import re
import os
import base64
import binascii
import xml.etree.ElementTree as ET
import secrets
import hashlib
from datetime import datetime

import frappe
from frappe import _
from frappe.utils import cint, now_datetime, validate_email_address
from frappe.utils.file_manager import save_file


REGISTRATION_DOCTYPE = "Tenant Registration"
OTP_DOCTYPE = "Registration OTP Challenge"


# ---------------------------------------------------------------------
# NORMALIZATION
# ---------------------------------------------------------------------

def _normalize_email(value):
    return (value or "").strip().lower()


def _country_is_kenya(country):
    value = (country or "").strip().lower()
    return value in {"kenya", "ke", "ken"}


def _normalize_phone(value, country=None):
    """
    Normalize Kenyan phone numbers to E.164.

    Kenya examples:
      0711001122   -> +254711001122
      254711001122 -> +254711001122
      +254711001122 -> +254711001122
      711001122    -> +254711001122

    For other countries, preserve the supplied international country code.
    """
    raw = (value or "").strip()
    digits = re.sub(r"\D", "", raw)

    if not digits:
        return ""

    # Convert an international 00 prefix to its normal international form.
    if digits.startswith("00"):
        digits = digits[2:]

    if _country_is_kenya(country):
        if len(digits) == 10 and digits.startswith("0"):
            digits = "254" + digits[1:]
        elif len(digits) == 9 and digits.startswith(("7", "1")):
            digits = "254" + digits
        elif len(digits) == 12 and digits.startswith("254"):
            pass

    return "+" + digits


def _phone_digits(value):
    return re.sub(r"\D", "", value or "")


def _slugify(value):
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:50].strip("-")


def _get_site_name(slug):
    base_domain = (
        frappe.conf.get("tenant_registration_base_domain") or "midas.co.ke"
    ).strip(".").lower()
    return f"{slug}.{base_domain}"


def _phone_sql_expression(column_name):
    expression = column_name
    for character in (" ", "-", "(", ")", "+", ".", "/"):
        expression = f"REPLACE({expression}, '{character}', '')"
    return expression


# ---------------------------------------------------------------------
# DUPLICATE CHECKS
# ---------------------------------------------------------------------

def _phone_exists(phone, country=None):
    """
    Compare phone numbers across registrations and Contacts.

    For Kenya, compare E.164, local 0-prefixed, and national 9-digit
    representations so older records are still detected as duplicates.
    """
    digits = _phone_digits(_normalize_phone(phone, country))
    if not digits:
        return False

    candidates = {digits}

    if _country_is_kenya(country) and digits.startswith("254") and len(digits) == 12:
        national_number = digits[3:]
        candidates.add("0" + national_number)
        candidates.add(national_number)

    candidates = sorted(candidates)
    placeholders = ", ".join(["%s"] * len(candidates))

    registration_expr = _phone_sql_expression("phone")
    registration_match = frappe.db.sql(
        f"""
        SELECT name
          FROM `tab{REGISTRATION_DOCTYPE}`
         WHERE {registration_expr} IN ({placeholders})
         LIMIT 1
        """,
        tuple(candidates),
    )
    if registration_match:
        return True

    contact_expr = _phone_sql_expression("phone")
    contact_match = frappe.db.sql(
        f"""
        SELECT parent
          FROM `tabContact Phone`
         WHERE {contact_expr} IN ({placeholders})
         LIMIT 1
        """,
        tuple(candidates),
    )
    return bool(contact_match)


def _ensure_not_duplicate(company_name, email, phone, slug, country=None):
    checks = [
        ("email", email, "An account with this email already exists."),
        ("workspace_slug", slug, "This workspace address is already registered."),
    ]

    for field, value, message in checks:
        if value and frappe.db.exists(REGISTRATION_DOCTYPE, {field: value}):
            frappe.throw(_(message), title=_("Already registered"))

    existing = frappe.db.sql(
        """
        SELECT name
          FROM `tabTenant Registration`
         WHERE LOWER(company_name) = LOWER(%s)
         LIMIT 1
        """,
        (company_name,),
    )

    if existing or frappe.db.exists("Company", {"company_name": company_name}):
        frappe.throw(
            _("A workspace with this company name already exists."),
            title=_("Already registered"),
        )

    if frappe.db.exists("User", email):
        frappe.throw(
            _("A user with this email already exists in the main tenant."),
            title=_("Already registered"),
        )

    if _phone_exists(phone, country):
        frappe.throw(
            _("This phone number already exists."),
            title=_("Already registered"),
        )


# ---------------------------------------------------------------------
# PRE-OTP VALIDATION
# ---------------------------------------------------------------------

@frappe.whitelist(allow_guest=True, methods=["POST"])
def validate_registration(company_name, workspace_name, email, phone, country=None):
    """
    Check registration details before sending OTPs.
    Does not create a registration record or send an OTP.
    """

    errors = {}

    company_name = (company_name or "").strip()
    workspace_name = (workspace_name or "").strip().lower()
    email = _normalize_email(email)
    phone = _normalize_phone(phone, country)

    if not company_name:
        errors["company_name"] = _("Company name is required.")
    elif len(company_name) < 2 or len(company_name) > 140:
        errors["company_name"] = _(
            "Company name must be between 2 and 140 characters."
        )

    if not workspace_name:
        errors["workspace_name"] = _("Workspace name is required.")

    if not email:
        errors["email"] = _("Email address is required.")
    elif not validate_email_address(email, throw=False):
        errors["email"] = _("Enter a valid email address.")

    digits = _phone_digits(phone)
    if not phone:
        errors["phone"] = _("Phone number is required.")
    elif _country_is_kenya(country) and not (
        len(digits) == 12 and digits.startswith("254")
    ):
        errors["phone"] = _(
            "Enter a valid Kenyan mobile number, for example 0711001122."
        )
    elif len(digits) < 8 or len(digits) > 16:
        errors["phone"] = _("Enter a valid phone number.")

    if errors:
        return {
            "available": False,
            "errors": errors,
            "message": _("Please correct the highlighted fields."),
        }

    slug = _slugify(workspace_name)
    if len(slug) < 3:
        errors["workspace_name"] = _(
            "Workspace name must contain at least three letters or numbers."
        )
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        errors["workspace_name"] = _(
            "Use lowercase letters, numbers and single hyphens in the workspace name."
        )

    if errors:
        return {
            "available": False,
            "errors": errors,
            "message": _("Please correct the highlighted fields."),
        }

    site_name = _get_site_name(slug)

    if site_name.lower() == (frappe.local.site or "").lower():
        errors["workspace_name"] = _("This workspace name is reserved.")

    if frappe.db.exists("User", email):
        errors["email"] = _(
            "A user with this email already exists in the main tenant."
        )
    elif frappe.db.exists(REGISTRATION_DOCTYPE, {"email": email}):
        errors["email"] = _("This email is already registered.")

    if _phone_exists(phone, country):
        errors["phone"] = _("This phone number is already registered.")

    existing_company = frappe.db.sql(
        """
        SELECT name
          FROM `tabTenant Registration`
         WHERE LOWER(company_name) = LOWER(%s)
         LIMIT 1
        """,
        (company_name,),
    )
    if existing_company or frappe.db.exists("Company", {"company_name": company_name}):
        errors["company_name"] = _("This company name is already registered.")

    if frappe.db.exists(REGISTRATION_DOCTYPE, {"workspace_slug": slug}):
        errors["workspace_name"] = _("This workspace address is already taken.")

    if frappe.db.exists(REGISTRATION_DOCTYPE, {"tenant_site": site_name}):
        errors["workspace_name"] = _("This workspace address is already registered.")

    return {
        "available": not bool(errors),
        "errors": errors,
        "workspace_url": site_name if not errors else None,
        "message": (
            _("Registration details are available.")
            if not errors
            else _("Please correct the highlighted fields.")
        ),
    }


# ---------------------------------------------------------------------
# TENANT LOGO UPLOAD
# ---------------------------------------------------------------------

def _sanitize_tenant_svg(content):
    """Remove active content and external references from an SVG image."""

    try:
        svg_text = content.decode("utf-8-sig")
        if re.search(r"<!DOCTYPE|<!ENTITY", svg_text, re.IGNORECASE):
            frappe.throw(_("SVG files containing DTD or entity declarations are not allowed."))
        root = ET.fromstring(svg_text)
    except (UnicodeDecodeError, ET.ParseError):
        frappe.throw(_("The uploaded SVG file is invalid."))

    def local_name(value):
        return value.rsplit("}", 1)[-1].lower()

    if local_name(root.tag) != "svg":
        frappe.throw(_("The uploaded file is not a valid SVG image."))

    forbidden_elements = {
        "script", "foreignobject", "iframe", "object", "embed",
        "audio", "video", "style", "animate", "animatetransform",
        "animatemotion", "set",
    }

    # Remove unsafe elements from the SVG tree.
    for parent in root.iter():
        for child in list(parent):
            if local_name(child.tag) in forbidden_elements:
                parent.remove(child)

    # Remove event handlers, CSS and external resource references.
    for element in root.iter():
        for attribute, value in list(element.attrib.items()):
            attr_name = local_name(attribute)
            attr_value = str(value).strip()
            lower_value = attr_value.lower()

            if attr_name.startswith("on") or attr_name in {"style", "xml:base", "base"}:
                del element.attrib[attribute]
                continue

            if attr_name in {"href", "src"}:
                if attr_value and not attr_value.startswith("#"):
                    del element.attrib[attribute]
                continue

            if "expression(" in lower_value or "javascript:" in lower_value:
                del element.attrib[attribute]
                continue

            if "url(" in lower_value:
                references = re.findall(r"url\((.*?)\)", attr_value, flags=re.IGNORECASE)
                if any(
                    not reference.strip(" \t\r\n'\"").startswith("#")
                    for reference in references
                ):
                    del element.attrib[attribute]

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def upload_tenant_logo(verification_token, filename, content):
    """Upload a tenant logo after both email and phone OTPs are verified.

    Accepted formats: PNG, JPG, JPEG, WebP and SVG.
    Maximum decoded file size: 2 MB.
    The temporary File record is attached to the OTP challenge and is
    transferred to Tenant Registration when registration is submitted.
    """

    if not verification_token:
        frappe.throw(_("Verification token is required."))

    challenge_name = frappe.db.get_value(
        OTP_DOCTYPE,
        {"verification_token": verification_token},
        "name",
    )
    if not challenge_name:
        frappe.throw(_("Verify your email and phone before uploading a logo."))

    challenge = frappe.get_doc(OTP_DOCTYPE, challenge_name)
    if not challenge.expires_at or challenge.expires_at < now_datetime():
        frappe.throw(_("Your verification session expired. Please verify again."))
    if not challenge.email_verified or not challenge.sms_verified:
        frappe.throw(_("Verify both email and phone before uploading a logo."))

    if not isinstance(filename, str) or not filename.strip():
        frappe.throw(_("A valid image filename is required."))
    if not isinstance(content, str):
        frappe.throw(_("Invalid image content."))

    # Strip any client-supplied path and normalize the extension.
    filename = filename.strip().replace("\\", "/").split("/")[-1]
    file_stem, extension = os.path.splitext(filename)
    extension = extension.lower()

    allowed_formats = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    if extension not in allowed_formats:
        frappe.throw(_("Unsupported image format. Upload PNG, JPG, JPEG, WEBP or SVG only."))

    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", file_stem).strip("-_") or "tenant-logo"
    filename = f"{safe_stem[:120]}{extension}"

    # Reject oversized data URLs before decoding to limit memory use.
    if len(content) > 4_000_000:
        frappe.throw(_("The tenant logo must be 2 MB or smaller."))

    try:
        header, encoded = content.split(",", 1)
        header_parts = header.split(";")
        if (
            not header_parts[0].lower().startswith("data:")
            or "base64" not in [part.lower() for part in header_parts[1:]]
        ):
            frappe.throw(_("Invalid image data URL."))

        mime_type = header_parts[0][5:].strip().lower()
        decoded_content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        frappe.throw(_("The tenant logo contains invalid image data."))

    if mime_type != allowed_formats[extension]:
        frappe.throw(_("The image content does not match its file extension."))

    if not decoded_content:
        frappe.throw(_("The uploaded image is empty."))
    if len(decoded_content) > 2 * 1024 * 1024:
        frappe.throw(_("The tenant logo must be 2 MB or smaller."))

    # Verify the actual file signature; do not trust extension or MIME alone.
    if extension == ".png":
        if not decoded_content.startswith(b"\x89PNG\r\n\x1a\n"):
            frappe.throw(_("The uploaded file is not a valid PNG image."))

    elif extension in {".jpg", ".jpeg"}:
        if not decoded_content.startswith(b"\xff\xd8\xff"):
            frappe.throw(_("The uploaded file is not a valid JPEG image."))

    elif extension == ".webp":
        if (
            len(decoded_content) < 12
            or decoded_content[0:4] != b"RIFF"
            or decoded_content[8:12] != b"WEBP"
        ):
            frappe.throw(_("The uploaded file is not a valid WebP image."))

    elif extension == ".svg":
        decoded_content = _sanitize_tenant_svg(decoded_content)
        if len(decoded_content) > 2 * 1024 * 1024:
            frappe.throw(_("The sanitized SVG exceeds the 2 MB limit."))

    # Attach to the verified OTP challenge, not to a missing Registration name.
    attachment = save_file(
        filename,
        decoded_content,
        OTP_DOCTYPE,
        str(challenge.name),
        is_private=0,
    )

    return {
        "success": True,
        "file_url": attachment.file_url,
        "filename": attachment.file_name,
        "file_type": mime_type,
        "file_size": len(decoded_content),
    }


# ---------------------------------------------------------------------
# FINAL REGISTRATION
# ---------------------------------------------------------------------

@frappe.whitelist(allow_guest=True, methods=["POST"])
def register_tenant(
    company_name,
    workspace_name,
    country,
    phone,
    administrator_name,
    email,
    password,
    verification_token,
    terms_accepted=0,
    industry=None,
    organization_size=None,
    financial_year_start="07-01",
    currency=None,
    logo_url=None,
):
    """Save registration centrally and queue tenant provisioning."""

    ip = frappe.local.request_ip or "unknown"

    if not all([
        company_name, workspace_name, country, phone,
        administrator_name, email, password,
    ]):
        frappe.throw(_("All fields are required."))

    if not cint(terms_accepted):
        frappe.throw(
            _("Accept the Terms of Service and Privacy Policy to continue.")
        )

    company_name = (company_name or "").strip()
    workspace_name = (workspace_name or "").strip().lower()
    country = (country or "").strip()
    administrator_name = (administrator_name or "").strip()
    email = _normalize_email(email)
    phone = _normalize_phone(phone, country)

    if len(company_name) < 2 or len(company_name) > 140:
        frappe.throw(
            _("Company/workspace name must be between 2 and 140 characters.")
        )

    if len(administrator_name) < 2 or len(administrator_name) > 140:
        frappe.throw(_("Enter the administrator's full name."))

    if len(password) < 12 or len(password) > 256:
        frappe.throw(_("Use a password between 12 and 256 characters."))

    if not validate_email_address(email, throw=False):
        frappe.throw(_("Enter a valid email address."))

    phone_digits = _phone_digits(phone)
    if _country_is_kenya(country) and not (
        len(phone_digits) == 12 and phone_digits.startswith("254")
    ):
        frappe.throw(
            _("Enter a valid Kenyan mobile number, for example 0711001122.")
        )
    if len(phone_digits) < 8 or len(phone_digits) > 16:
        frappe.throw(
            _("Enter a valid phone number, including country code where possible.")
        )

    slug = _slugify(workspace_name)
    if len(slug) < 3:
        frappe.throw(
            _("Workspace name must contain at least three letters or numbers.")
        )

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        frappe.throw(
            _("Use lowercase letters, numbers, and single hyphens in the workspace name.")
        )

    financial_year_start = (financial_year_start or "07-01").strip()
    try:
        datetime.strptime(financial_year_start, "%m-%d")
    except ValueError:
        frappe.throw(_("Choose a valid financial year start date."))

    currency = (currency or "").strip().upper()
    if currency and not frappe.db.exists("Currency", currency):
        frappe.throw(_("Choose a supported currency."))

    site_name = _get_site_name(slug)
    if site_name.lower() == (frappe.local.site or "").lower():
        frappe.throw(_("This workspace name is reserved."))

    # Verify OTPs against the exact email and phone being registered.
    challenge_name = frappe.db.get_value(
        OTP_DOCTYPE,
        {"verification_token": verification_token},
        "name",
    )
    if not challenge_name:
        frappe.throw(_("Verify your email and phone before registering."))

    challenge = frappe.get_doc(OTP_DOCTYPE, challenge_name)

    if not challenge.expires_at or challenge.expires_at < now_datetime():
        frappe.throw(_("Your verification session expired. Please verify again."))

    if (
        _normalize_email(challenge.email) != email
        or _phone_digits(_normalize_phone(challenge.phone, country)) != phone_digits
    ):
        frappe.throw(
            _("The verified email and phone must match the registration details.")
        )

    if not challenge.email_verified or not challenge.sms_verified:
        frappe.throw(
            _("Verify both your email address and phone number before registering.")
        )

    # A supplied logo must be the file uploaded against this exact OTP challenge.
    logo_file_name = None
    logo_url = (logo_url or "").strip()
    if logo_url:
        logo_file_name = frappe.db.get_value(
            "File",
            {
                "file_url": logo_url,
                "attached_to_doctype": OTP_DOCTYPE,
                "attached_to_name": challenge.name,
            },
            "name",
        )
        if not logo_file_name:
            frappe.throw(_("The uploaded logo is invalid or belongs to another verification session."))

    # Stable lock ordering prevents concurrent submissions racing each other.
    lock_keys = sorted({
        "tenant-reg:" + hashlib.sha256(
            f"email:{email}".encode()
        ).hexdigest()[:48],
        "tenant-reg:" + hashlib.sha256(
            f"phone:{phone_digits}".encode()
        ).hexdigest()[:48],
        "tenant-reg:" + hashlib.sha256(
            f"slug:{slug}".encode()
        ).hexdigest()[:48],
        "tenant-reg:" + hashlib.sha256(
            f"company:{company_name.casefold()}".encode()
        ).hexdigest()[:48],
    })

    acquired = []
    try:
        for lock_key in lock_keys:
            result = frappe.db.sql(
                "SELECT GET_LOCK(%s, 5)",
                (lock_key,),
            )
            if not result or result[0][0] != 1:
                frappe.throw(
                    _("Registration is busy. Please try again in a moment.")
                )
            acquired.append(lock_key)

        # Repeat all uniqueness checks at final submission.
        _ensure_not_duplicate(company_name, email, phone, slug, country)

        if frappe.db.exists(REGISTRATION_DOCTYPE, {"tenant_site": site_name}):
            frappe.throw(
                _("This workspace address is already registered."),
                title=_("Already registered"),
            )

        doc = frappe.get_doc({
            "doctype": REGISTRATION_DOCTYPE,
            "company_name": company_name,
            "country": country,
            "phone": phone,
            "administrator_name": administrator_name,
            "email": email,
            "workspace_slug": slug,
            "tenant_site": site_name,
            "industry": (industry or "").strip() or None,
            "organization_size": (organization_size or "").strip() or None,
            "financial_year_start": financial_year_start,
            "currency": currency or None,
            "logo_url": logo_url or None,
            "terms_accepted": 1,
            "terms_accepted_at": now_datetime(),
            "status_token": secrets.token_urlsafe(32),
            "status": "Pending",
            "admin_password": password,
            "request_ip": ip[:140],
        })

        doc.insert(ignore_permissions=True)

        # Move the File attachment onto the new registration before deleting
        # the temporary OTP challenge that originally owned it.
        if logo_file_name:
            frappe.db.set_value(
                "File",
                logo_file_name,
                {
                    "attached_to_doctype": REGISTRATION_DOCTYPE,
                    "attached_to_name": str(doc.name),
                    "attached_to_field": "logo_url",
                },
                update_modified=False,
            )

        frappe.db.commit()

        # Consume the OTP challenge after the registration is saved.
        frappe.delete_doc(
            OTP_DOCTYPE,
            challenge.name,
            ignore_permissions=True,
            force=True,
        )
        frappe.db.commit()

        try:
            frappe.enqueue(
                "frontend.services.tenant_provisioner.provision_registration",
                queue="long",
                timeout=14400,
                job_name=f"tenant-provision-{doc.name}",
                registration_name=doc.name,
            )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "Tenant Provisioning Queue Error",
            )
            frappe.db.set_value(
                REGISTRATION_DOCTYPE,
                doc.name,
                "status",
                "Failed",
            )
            frappe.db.commit()
            frappe.throw(
                _(
                    "Registration was saved but provisioning could not be queued. "
                    "Please contact support with your registration reference."
                )
            )

        return {
            "ok": True,
            "registration_id": doc.name,
            "status_token": doc.status_token,
            "status": "Pending",
            "message": _(
                "Registration received. Your workspace is being prepared."
            ),
        }

    finally:
        for lock_key in reversed(acquired):
            frappe.db.sql("SELECT RELEASE_LOCK(%s)", (lock_key,))


# ---------------------------------------------------------------------
# REGISTRATION STATUS
# ---------------------------------------------------------------------

@frappe.whitelist(allow_guest=True, methods=["POST"])
def registration_status(status_token):
    """Return minimal registration status using its random status token."""

    if not status_token or len(status_token) > 100:
        frappe.throw(_("Registration status token is required."))

    doc = frappe.db.get_value(
        REGISTRATION_DOCTYPE,
        {"status_token": status_token},
        ["status", "tenant_site"],
        as_dict=True,
    )

    if not doc:
        frappe.throw(_("Registration not found."), frappe.DoesNotExistError)

    return {
        "status": doc.status,
        "login_url": (
            f"https://{doc.tenant_site}"
            if doc.status == "Active"
            else None
        ),
        "message": {
            "Pending": _("Your registration is queued."),
            "Provisioning": _("Your workspace is being created."),
            "Active": _("Your workspace is ready."),
            "Failed": _(
                "Workspace creation failed. Please contact support with your registration reference."
            ),
        }.get(doc.status, _("Registration status updated.")),
    }

