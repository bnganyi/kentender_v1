import os
import json
import frappe
from frappe import _
from frappe.utils import cint

def initialize_tenant(company_name, country, administrator_name, email, password, abbr="KT"):
    """Called only on the newly provisioned tenant via bench execute."""
    frappe.flags.in_install = True
    email = (email or "").strip().lower()

    # Create the initial Company if ERPNext has not already created one.
    if not frappe.db.exists("Company", company_name):
        company = frappe.get_doc({
            "doctype": "Company",
            "company_name": company_name,
            "abbr": (abbr or "KT")[:5],
            "country": country,
            "default_currency": _currency_for_country(country),
        })
        company.insert(ignore_permissions=True)
        company_name = company.name

    # Configure defaults commonly used by ERPNext transactions.
    defaults = frappe.get_single("Global Defaults")
    defaults.default_company = company_name
    defaults.save(ignore_permissions=True)

    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": (administrator_name or "").strip(),
            "enabled": 1,
            "user_type": "System User",
            "send_welcome_email": 0,
        })
        user.append("roles", {"role": "System Manager"})
        user.insert(ignore_permissions=True)

    user.enabled = 1
    if not any(row.role == "System Manager" for row in user.roles):
        user.append("roles", {"role": "System Manager"})
    user.new_password = password
    user.save(ignore_permissions=True)

    # Ensure ERPNext setup wizard is marked complete where supported.
    try:
        frappe.db.set_single_value("System Settings", "setup_complete", 1)
    except Exception:
        pass

    frappe.db.commit()
    return {"company": company_name, "administrator": email}

def _currency_for_country(country):
    # Keep conservative; customize with your supported countries/currency mapping.
    mapping = {
        "Kenya": "KES",
        "Somalia": "SOS",
        "Uganda": "UGX",
        "Tanzania": "TZS",
        "Rwanda": "RWF",
        "United States": "USD",
        "United Kingdom": "GBP",
    }
    currency = mapping.get(country)
    if currency and frappe.db.exists("Currency", currency):
        return currency
    # Use system default if country is not mapped.
    return frappe.db.get_value("Global Defaults", None, "default_currency") or "KES"


def initialize_tenant_from_env():
    """Internal bench-execute entry point; payload is provided by the worker environment."""
    raw = os.environ.pop("KENTENDER_TENANT_PAYLOAD", None)
    if not raw:
        frappe.throw(_("Missing tenant initialization payload."))
    payload = json.loads(raw)
    return initialize_tenant(**payload)
