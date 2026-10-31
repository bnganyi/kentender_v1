"""Initialize the ERPNext tenant after apps are installed."""

import json
import os
from datetime import date, timedelta
from pathlib import Path

import frappe
from frappe import _
from dateutil.relativedelta import relativedelta


def initialize_tenant(
    company_name,
    country,
    administrator_name,
    email,
    password,
    phone=None,
    currency=None,
    financial_year_start="07-01",
    abbr="KT",
):
    """Create the tenant company and named System Manager user."""
    email = (email or "").strip().lower()
    company_name = (company_name or "").strip()
    if not company_name or not email or not password:
        frappe.throw(_("Company, email and password are required for tenant initialization."))

    if not frappe.db.exists("Company", {"company_name": company_name}):
        company = frappe.get_doc({
            "doctype": "Company",
            "company_name": company_name,
            "abbr": (abbr or "KT")[:5],
            "country": country,
            "default_currency": currency or _currency_for_country(country),
        })
        company.insert(ignore_permissions=True)
        company_name = company.name
    else:
        company_name = frappe.db.get_value("Company", {"company_name": company_name}, "name")

    selected_currency = currency or _currency_for_country(country)
    company = frappe.get_doc("Company", company_name)
    if company.default_currency != selected_currency:
        company.default_currency = selected_currency
        company.save(ignore_permissions=True)

    defaults = frappe.get_single("Global Defaults")
    defaults.default_company = company_name
    defaults.default_currency = selected_currency
    defaults.save(ignore_permissions=True)

    _ensure_fiscal_year(company_name, financial_year_start)

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
        user.insert(ignore_permissions=True)

    user.enabled = 1
    user.user_type = "System User"
    if not any(row.role == "System Manager" for row in user.roles):
        user.append("roles", {"role": "System Manager"})
    user.new_password = password
    user.save(ignore_permissions=True)

    # Store the supplied phone as a Contact for the administrator where possible.
    linked_contact = frappe.db.sql(
        """select parent from `tabDynamic Link`
           where link_doctype = 'User' and link_name = %s and parenttype = 'Contact'
           limit 1""",
        (email,),
    )
    if phone and not linked_contact:
        contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": (administrator_name or "Administrator").strip() or "Administrator",
            "email_ids": [{"email_id": email, "is_primary": 1}],
            "phone_nos": [{"phone": phone, "is_primary_phone": 1}],
            "links": [{"link_doctype": "User", "link_name": email}],
        })
        contact.insert(ignore_permissions=True)

    try:
        frappe.db.set_single_value("System Settings", "setup_complete", 1)
    except Exception:
        # This field can vary by ERPNext version/setup; company and user creation
        # are the essential onboarding operations.
        pass

    frappe.db.commit()
    return {"company": company_name, "administrator": email}


def _ensure_fiscal_year(company_name, start_value):
    try:
        month, day = (int(part) for part in (start_value or "07-01").split("-", 1))
        today = date.today()
        start = date(today.year, month, day)
        if start > today:
            start = date(today.year - 1, month, day)
    except (TypeError, ValueError):
        frappe.throw(_("The financial year start date is invalid."))

    end = start + relativedelta(years=1) - timedelta(days=1)
    fiscal_year_name = frappe.db.get_value(
        "Fiscal Year",
        {"year_start_date": start, "year_end_date": end},
        "name",
    )
    if fiscal_year_name:
        fiscal_year = frappe.get_doc("Fiscal Year", fiscal_year_name)
        if company_name not in {row.company for row in fiscal_year.companies}:
            fiscal_year.append("companies", {"company": company_name})
            fiscal_year.save(ignore_permissions=True)
        return

    start_year = str(start.year)
    end_year = str(end.year)
    base_name = start_year if start_year == end_year else f"{start_year}-{end_year}"
    fiscal_year = frappe.new_doc("Fiscal Year")
    fiscal_year.year = base_name
    if frappe.db.exists("Fiscal Year", base_name):
        fiscal_year.year = f"{base_name} ({month:02d}-{day:02d})"
    fiscal_year.year_start_date = start
    fiscal_year.year_end_date = end
    fiscal_year.append("companies", {"company": company_name})
    fiscal_year.insert(ignore_permissions=True)


def _currency_for_country(country):
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
    return frappe.db.get_value("Global Defaults", None, "default_currency") or "KES"


def initialize_tenant_from_file():
    """Internal bench-execute entry point; payload file is short-lived and owner-only."""
    file_name = os.environ.get("KENTENDER_TENANT_PAYLOAD_FILE")
    if not file_name:
        frappe.throw(_("Missing tenant initialization payload file."))
    path = Path(file_name).resolve()
    sites_dir = Path(frappe.get_site_path()).parent.resolve()
    # Only allow the temporary payload directly under this Bench's sites directory.
    if path.parent != sites_dir or not path.name.startswith(".tenant-onboarding-") or path.suffix != ".json":
        frappe.throw(_("Invalid tenant initialization payload path."))
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    return initialize_tenant(**payload)
