import re
import secrets
import hashlib
from datetime import datetime
import frappe
from frappe import _
from frappe.utils import cint, now_datetime, validate_email_address

REGISTRATION_DOCTYPE = "Tenant Registration"

def _normalize_email(value):
    return (value or "").strip().lower()

def _normalize_phone(value):
    # Keep a leading + and digits only. For production, consider phonenumbers
    # to validate country-specific numbering plans.
    value = (value or "").strip()
    return ("+" if value.startswith("+") else "") + re.sub(r"\D", "", value)

def _slugify(value):
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:50].strip("-")

def _ensure_not_duplicate(company_name, email, phone, slug):
    # Use database queries rather than trusting client-side validation.
    checks = [
        ("email", email, "An account with this email already exists."),
        ("phone", phone, "An account with this phone number already exists."),
        ("workspace_slug", slug, "This workspace address is already registered."),
    ]
    for field, value, message in checks:
        if value and frappe.db.exists(REGISTRATION_DOCTYPE, {field: value}):
            frappe.throw(_(message), title=_("Already registered"))

    # Check the central registry and the main ERPNext site's own records.
    existing = frappe.db.sql(
        """select name from `tabTenant Registration`
           where lower(company_name) = lower(%s) limit 1""",
        (company_name,),
    )
    if existing or frappe.db.exists("Company", {"company_name": company_name}):
        frappe.throw(_("A workspace with this company name already exists."),
                     title=_("Already registered"))

    if frappe.db.exists("User", email):
        frappe.throw(_("A user with this email already exists in the main tenant."),
                     title=_("Already registered"))

    # Check phone numbers recorded against Contacts in the main tenant.
    phone_exists = frappe.db.sql(
        """select parent from `tabContact Phone`
           where replace(replace(replace(replace(phone, ' ', ''), '-', ''), '(', ''), ')', '') = %s
           limit 1""",
        (phone,),
    )
    if phone_exists:
        frappe.throw(_("This phone number already exists in the main tenant."),
                     title=_("Already registered"))

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
):
    """Save a registration centrally and queue provisioning."""
    ip = frappe.local.request_ip or "unknown"
    if not all([company_name, workspace_name, country, phone, administrator_name, email, password]):
        frappe.throw(_("All fields are required."))
    if not cint(terms_accepted):
        frappe.throw(_("Accept the Terms of Service and Privacy Policy to continue."))

    company_name = (company_name or "").strip()
    workspace_name = (workspace_name or "").strip().lower()
    country = (country or "").strip()
    administrator_name = (administrator_name or "").strip()
    email = _normalize_email(email)
    phone = _normalize_phone(phone)

    if len(company_name) < 2 or len(company_name) > 140:
        frappe.throw(_("Company/workspace name must be between 2 and 140 characters."))
    if len(administrator_name) < 2 or len(administrator_name) > 140:
        frappe.throw(_("Enter the administrator's full name."))
    if len(password) < 12 or len(password) > 256:
        frappe.throw(_("Use a password between 12 and 256 characters."))
    if not validate_email_address(email, throw=False):
        frappe.throw(_("Enter a valid email address."))
    if len(phone) < 8 or len(phone) > 16:
        frappe.throw(_("Enter a valid phone number, including country code where possible."))

    slug = _slugify(workspace_name)
    if len(slug) < 3:
        frappe.throw(_("Workspace name must contain at least three letters or numbers."))
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        frappe.throw(_("Use lowercase letters, numbers, and single hyphens in the workspace name."))

    financial_year_start = (financial_year_start or "07-01").strip()
    try:
        datetime.strptime(financial_year_start, "%m-%d")
    except ValueError:
        frappe.throw(_("Choose a valid financial year start date."))
    currency = (currency or "").strip().upper()
    if currency and not frappe.db.exists("Currency", currency):
        frappe.throw(_("Choose a supported currency."))

    base_domain = (frappe.conf.get("tenant_registration_base_domain") or "midas.co.ke").strip(".").lower()
    site_name = f"{slug}.{base_domain}"
    if site_name.lower() == frappe.local.site.lower() or site_name.lower() == base_domain:
        frappe.throw(_("This workspace name is reserved."))

    # Require both channels to be verified against the exact submitted identities.
    challenge_name = frappe.db.get_value(
        "Registration OTP Challenge",
        {"verification_token": verification_token},
        "name",
    )
    if not challenge_name:
        frappe.throw(_("Verify your email and phone before registering."))
    challenge = frappe.get_doc("Registration OTP Challenge", challenge_name)
    if challenge.expires_at < frappe.utils.now_datetime():
        frappe.throw(_("Your verification session expired. Please verify again."))
    if challenge.email != email or challenge.phone != phone:
        frappe.throw(_("The verified email and phone must match the registration details."))
    if not challenge.email_verified or not challenge.sms_verified:
        frappe.throw(_("Verify both your email address and phone number before registering."))

    # Acquire identity locks in stable order so simultaneous requests cannot
    # both pass the duplicate checks for the same email, phone, or workspace.
    lock_keys = sorted({
        "tenant-reg:" + hashlib.sha256(f"email:{email}".encode()).hexdigest()[:48],
        "tenant-reg:" + hashlib.sha256(f"phone:{phone}".encode()).hexdigest()[:48],
        "tenant-reg:" + hashlib.sha256(f"slug:{slug}".encode()).hexdigest()[:48],
        "tenant-reg:" + hashlib.sha256(f"company:{company_name.casefold()}".encode()).hexdigest()[:48],
    })
    acquired = []
    try:
        for lock_key in lock_keys:
            lock_result = frappe.db.sql("select get_lock(%s, 5)", (lock_key,))
            if not lock_result or lock_result[0][0] != 1:
                frappe.throw(_("Registration is busy. Please try again in a moment."))
            acquired.append(lock_key)

        _ensure_not_duplicate(company_name, email, phone, slug)
        if frappe.db.exists(REGISTRATION_DOCTYPE, {"tenant_site": site_name}):
            frappe.throw(_("This workspace address is already registered."), title=_("Already registered"))

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
            "terms_accepted": 1,
            "terms_accepted_at": now_datetime(),
            "status_token": secrets.token_urlsafe(32),
            "status": "Pending",
            "admin_password": password,
            "request_ip": ip[:140],
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        # Consume the verification token so it cannot be reused.
        frappe.delete_doc("Registration OTP Challenge", challenge.name, ignore_permissions=True, force=True)
        frappe.db.commit()

        frappe.enqueue(
            "frontend.services.tenant_provisioner.provision_registration",
            queue="long",
            timeout=14400,
            job_name=f"tenant-provision-{doc.name}",
            registration_name=doc.name,
        )
        return {
            "ok": True,
            "registration_id": doc.name,
            "status_token": doc.status_token,
            "status": "Pending",
            "message": _("Registration received. Your workspace is being prepared."),
        }
    finally:
        for lock_key in reversed(acquired):
            frappe.db.sql("select release_lock(%s)", (lock_key,))

@frappe.whitelist(allow_guest=True, methods=["POST"])
def registration_status(status_token):
    """Return minimal status data; token is random and not a sequential record ID."""
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
        "login_url": f"https://{doc.tenant_site}" if doc.status == "Active" else None,
        "message": {
            "Pending": _("Your registration is queued."),
            "Provisioning": _("Your workspace is being created."),
            "Active": _("Your workspace is ready."),
            "Failed": _("Workspace creation failed. Please contact support with your registration reference."),
        }.get(doc.status, _("Registration status updated.")),
    }
