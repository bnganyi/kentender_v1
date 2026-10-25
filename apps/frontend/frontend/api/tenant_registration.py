import re
import frappe
from frappe import _
from frappe.utils import validate_email_address
from frappe.utils.password import encrypt

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
def register_tenant(company_name, country, phone, administrator_name, email, password):
    """Create a central registration and queue site provisioning."""
    # Basic abuse guard; also apply reverse-proxy rate limiting/CAPTCHA.
    ip = frappe.local.request_ip or "unknown"
    if not all([company_name, country, phone, administrator_name, email, password]):
        frappe.throw(_("All fields are required."))

    company_name = (company_name or "").strip()
    country = (country or "").strip()
    administrator_name = (administrator_name or "").strip()
    email = _normalize_email(email)
    phone = _normalize_phone(phone)

    if len(company_name) < 2 or len(company_name) > 140:
        frappe.throw(_("Company/workspace name must be between 2 and 140 characters."))
    if len(administrator_name) < 2 or len(administrator_name) > 140:
        frappe.throw(_("Enter the administrator's full name."))
    if len(password) < 12:
        frappe.throw(_("Use a password with at least 12 characters."))
    if len(password) > 256:
        frappe.throw(_("Password is too long."))
    if not validate_email_address(email, throw=False):
        frappe.throw(_("Enter a valid email address."))
    if len(phone) < 8 or len(phone) > 16:
        frappe.throw(_("Enter a valid phone number, including country code where possible."))

    slug = _slugify(company_name)
    if not slug:
        frappe.throw(_("Company name cannot be converted into a workspace address."))

    base_domain = frappe.conf.get("tenant_registration_base_domain", "midas.co.ke").strip(".")
    site_name = f"{slug}.{base_domain}"

    # Avoid creating a hostname that collides with the central site.
    if site_name.lower() == frappe.local.site.lower():
        frappe.throw(_("This workspace name is reserved."))

    # A transaction lock reduces races on concurrent submissions. Database unique
    # indexes are still recommended for email, phone, and workspace_slug.
    frappe.db.sql("select get_lock(%s, 5)", (f"tenant-reg:{email}",))
    try:
        _ensure_not_duplicate(company_name, email, phone, slug)
        if frappe.db.exists(REGISTRATION_DOCTYPE, {"tenant_site": site_name}):
            frappe.throw(_("This workspace address is already registered."))

        doc = frappe.get_doc({
            "doctype": REGISTRATION_DOCTYPE,
            "company_name": company_name,
            "country": country,
            "phone": phone,
            "administrator_name": administrator_name,
            "email": email,
            "workspace_slug": slug,
            "tenant_site": site_name,
            "status": "Pending",
            # Password field is stored through Frappe's password mechanism.
            "admin_password": password,
            "request_ip": ip[:140],
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.enqueue(
            "kentender_core.services.tenant_provisioner.provision_registration",
            queue="long",
            timeout=7200,
            job_name=f"tenant-provision-{doc.name}",
            registration_name=doc.name,
        )
        return {
            "ok": True,
            "registration_id": doc.name,
            "status": "Pending",
            "message": _("Registration received. Your workspace is being prepared."),
        }
    finally:
        frappe.db.sql("select release_lock(%s)", (f"tenant-reg:{email}",))

@frappe.whitelist(allow_guest=True, methods=["POST"])
def registration_status(registration_id):
    """Return limited status data; never expose passwords, errors, or PII."""
    if not registration_id:
        frappe.throw(_("Registration reference is required."))
    doc = frappe.db.get_value(
        REGISTRATION_DOCTYPE,
        registration_id,
        ["status", "tenant_site"],
        as_dict=True,
    )
    if not doc:
        frappe.throw(_("Registration not found."), frappe.DoesNotExistError)

    scheme = frappe.conf.get("tenant_registration_scheme", "https")
    return {
        "registration_id": registration_id,
        "status": doc.status,
        "login_url": f"{scheme}://{doc.tenant_site}" if doc.status == "Active" else None,
        "message": {
            "Pending": _("Your registration is queued."),
            "Provisioning": _("Your workspace is being created."),
            "Active": _("Your workspace is ready."),
            "Failed": _("Workspace creation failed. Please contact support with your registration reference."),
        }.get(doc.status, _("Registration status updated.")),
    }
