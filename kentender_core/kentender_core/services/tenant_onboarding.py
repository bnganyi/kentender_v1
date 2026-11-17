
"""Initialize a newly provisioned Kentender ERPNext tenant."""
import json
import os
from datetime import date, timedelta
from pathlib import Path

import frappe
from frappe import _
from dateutil.relativedelta import relativedelta


def _ensure_required_warehouse_types():
    required = {"Transit": "Warehouse used for goods in transit"}
    for name, description in required.items():
        if not frappe.db.exists("Warehouse Type", name):
            frappe.get_doc({
                "doctype": "Warehouse Type",
                "name": name,
                "description": description,
            }).insert(ignore_permissions=True)


def _financial_year_dates(start_value):
    try:
        month, day = (int(part) for part in (start_value or "07-01").split("-", 1))
        today = date.today()
        start = date(today.year, month, day)
        if start > today:
            start = date(today.year - 1, month, day)
    except (TypeError, ValueError):
        frappe.throw(_("The financial year start date is invalid."))
    return start, start + relativedelta(years=1) - timedelta(days=1)


def _ensure_fiscal_year(company_name, start_value):
    start, end = _financial_year_dates(start_value)
    name = frappe.db.get_value(
        "Fiscal Year",
        {"year_start_date": start, "year_end_date": end},
        "name",
    )
    if name:
        fy = frappe.get_doc("Fiscal Year", name)
        if company_name not in {row.company for row in fy.companies}:
            fy.append("companies", {"company": company_name})
            fy.save(ignore_permissions=True)
        return name

    base = str(start.year) if start.year == end.year else f"{start.year}-{end.year}"
    fy = frappe.new_doc("Fiscal Year")
    fy.year = base if not frappe.db.exists("Fiscal Year", base) else f"{base} ({start:%m-%d})"
    fy.year_start_date = start
    fy.year_end_date = end
    fy.append("companies", {"company": company_name})
    fy.insert(ignore_permissions=True)
    return fy.name


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


def _run_native_setup(
    company_name,
    country,
    administrator_name,
    email,
    password,
    currency,
    financial_year_start,
    abbr,
):
    from frappe.desk.page.setup_wizard.setup_wizard import (
        get_setup_stages,
        process_setup_stages,
    )

    selected_currency = currency or _currency_for_country(country)
    if not frappe.db.exists("Currency", selected_currency):
        frappe.throw(_("Currency {0} does not exist.").format(selected_currency))

    fy_start, fy_end = _financial_year_dates(financial_year_start)
    existing_company = frappe.db.get_value(
        "Company", {"company_name": company_name}, "name"
    )

    # ERPNext v16 stores chart definitions as Python/JSON templates,
    # not as a "Chart of Accounts Template" DocType.
    from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
        get_charts_for_country,
    )

    chart_templates = get_charts_for_country(country, with_standard=True) or []
    if not chart_templates:
        frappe.throw(
            _("ERPNext has no available Chart of Accounts for country {0}.").format(country)
        )

    # Prefer a country-specific chart when available.
    # Kenya currently returns Standard and Standard with Numbers.
    chart_template = (
        chart_templates[0]
        if chart_templates[0] not in ("Standard", "Standard with Numbers")
        else ("Standard" if "Standard" in chart_templates else chart_templates[0])
    )

    # Do not assign an arbitrary domain to a tenant.
    selected_domain = None

    args = frappe._dict({
        "country": country,
        "currency": selected_currency,
        "company_name": company_name,
        "company_abbr": (abbr or "KT")[:5],
        "email": email,
        "full_name": administrator_name,
        "password": password,
        "fy_start_date": fy_start,
        "fy_end_date": fy_end,
        "chart_of_accounts": chart_template,
        "domain": selected_domain,
        "language": "English",
        "timezone": (
            frappe.db.get_single_value("System Settings", "time_zone")
            or "Africa/Nairobi"
        ),
        "setup_demo": 0,
        "enable_telemetry": 0,
    })

    _ensure_required_warehouse_types()
    stages = get_setup_stages(args)

    if existing_company:
        _ensure_fiscal_year(existing_company, financial_year_start)

        # Preserve an existing Company and avoid creating it twice.
        for stage in stages:
            for task in stage.get("tasks", []):
                if getattr(task.get("fn"), "__name__", "") == "setup_company":
                    task["fn"] = lambda _args: None

    result = process_setup_stages(stages, args)

    company = frappe.db.get_value(
        "Company", {"company_name": company_name}, "name"
    )
    if not company:
        frappe.throw(
            _("Native ERPNext setup did not create Company {0}.").format(company_name)
        )

    company_doc = frappe.get_doc("Company", company)
    company_doc.country = country
    company_doc.default_currency = selected_currency
    company_doc.save(ignore_permissions=True)

    defaults = frappe.get_single("Global Defaults")
    defaults.default_company = company
    defaults.default_currency = selected_currency
    defaults.save(ignore_permissions=True)

    return {"company": company, "setup_result": result}


def _ensure_administrator(email, password):
    user = frappe.get_doc("User", email)
    user.enabled = 1
    user.user_type = "System User"

    if not any(row.role == "System Manager" for row in user.roles):
        user.append("roles", {"role": "System Manager"})

    user.new_password = password
    user.save(ignore_permissions=True)


def _ensure_administrator_contact(email, administrator_name, phone):
    if not phone:
        return None

    linked = frappe.db.sql("""
        SELECT parent FROM `tabDynamic Link`
        WHERE link_doctype = 'User' AND link_name = %s
          AND parenttype = 'Contact' LIMIT 1
    """, (email,))

    if linked:
        contact = frappe.get_doc("Contact", linked[0][0])

        if not any(row.phone == phone for row in contact.phone_nos):
            contact.append("phone_nos", {
                "phone": phone,
                "is_primary_phone": not bool(contact.phone_nos),
            })
            contact.save(ignore_permissions=True)

        return contact.name

    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": administrator_name or "Administrator",
        "email_ids": [{"email_id": email, "is_primary": 1}],
        "phone_nos": [{"phone": phone, "is_primary_phone": 1}],
        "links": [{"link_doctype": "User", "link_name": email}],
    })

    contact.insert(ignore_permissions=True)
    return contact.name



def _ensure_procurement_onboarding():
    """Install the Procurement onboarding checklist for this tenant."""

    onboarding_name = "KenTender Procurement Setup"
    module_name = "Kentender Procurement"

    steps = [
        {
            "name": "KT Procurement - System Setup",
            "title": "Configure System Setup",
            "description": (
                "Review and configure the core procurement system "
                "settings for your institution."
            ),
            "action_label": "Configure System Setup",
            "path": "system-setup",
        },
        {
            "name": "KT Procurement - Strategy Alignment",
            "title": "Configure Strategy Alignment",
            "description": (
                "Review institutional strategy and align procurement "
                "priorities with organisational objectives."
            ),
            "action_label": "Open Strategy Alignment",
            "path": "strategy",
        },
        {
            "name": "KT Procurement - Budget Funding",
            "title": "Configure Budget and Funding",
            "description": (
                "Review available budgets and funding allocations "
                "for procurement activities."
            ),
            "action_label": "Configure Budget and Funding",
            "path": "budget-funding",
        },
        {
            "name": "KT Procurement - Departmental Needs",
            "title": "Configure Departmental Needs",
            "description": (
                "Review departmental requirements and consolidate "
                "institutional procurement needs."
            ),
            "action_label": "Review Departmental Needs",
            "path": "departmental-needs",
        },
        {
            "name": "KT Procurement - Procurement Planning",
            "title": "Prepare Procurement Plan",
            "description": (
                "Prepare and review the institution's procurement plan."
            ),
            "action_label": "Open Procurement Planning",
            "path": "procurement-planning",
        },
        {
            "name": "KT Procurement - Requisitions",
            "title": "Configure Procurement Requisitions",
            "description": (
                "Review the procurement requisition process "
                "and its configuration."
            ),
            "action_label": "Open Procurement Requisitions",
            "path": "procurement-requisitions",
        },
    ]

    if not frappe.db.exists("Module Def", module_name):
        frappe.throw(
            _("Procurement module is not installed: {0}").format(
                module_name
            )
        )

    if not frappe.db.exists("Role", "System Manager"):
        frappe.throw(_("System Manager role does not exist."))

    # Create missing steps. Preserve existing completion state.
    for step_data in steps:
        step_name = step_data["name"]

        if not frappe.db.exists("Onboarding Step", step_name):
            frappe.get_doc({
                "doctype": "Onboarding Step",
                "name": step_name,
                "title": step_data["title"],
                "is_complete": 0,
                "is_skipped": 0,
                "description": step_data["description"],
                "action": "Go to Page",
                "action_label": step_data["action_label"],
                "path": step_data["path"],
                "validate_action": 1,
            }).insert(ignore_permissions=True)

    # Create or update the Module Onboarding record.
    if frappe.db.exists("Module Onboarding", onboarding_name):
        onboarding = frappe.get_doc(
            "Module Onboarding", onboarding_name
        )
    else:
        onboarding = frappe.new_doc("Module Onboarding")
        onboarding.name = onboarding_name

    onboarding.title = onboarding_name
    onboarding.module = module_name

    # Restrict the checklist to System Manager.
    onboarding.set("allow_roles", [])
    onboarding.append("allow_roles", {"role": "System Manager"})

    # Add only missing steps, preserving existing checklist rows.
    existing_steps = {
        row.step for row in onboarding.steps
    }

    for step_data in steps:
        step_name = step_data["name"]
        if step_name not in existing_steps:
            onboarding.append("steps", {"step": step_name})

    if onboarding.is_new():
        onboarding.insert(ignore_permissions=True)
    else:
        onboarding.save(ignore_permissions=True)

    # Attach the onboarding checklist to the Procurement workspace.
    if frappe.db.exists("Workspace Sidebar", "Procurement"):
        workspace_module = frappe.db.get_value(
            "Workspace Sidebar",
            "Procurement",
            "module",
        )

        if workspace_module != module_name:
            frappe.throw(
                _("Procurement workspace belongs to an unexpected module.")
            )

        frappe.db.set_value(
            "Workspace Sidebar",
            "Procurement",
            "module_onboarding",
            onboarding_name,
            update_modified=False,
        )
    else:
        frappe.throw(_("Procurement workspace does not exist."))

    frappe.clear_cache()

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
    """Run native Frappe/ERPNext setup, then Kentender-specific initialization."""
    email = (email or "").strip().lower()
    company_name = (company_name or "").strip()
    country = (country or "").strip()
    administrator_name = (administrator_name or "").strip()

    if not company_name or not country or not email or not password:
        frappe.throw(
            _("Company, country, administrator email and password are required.")
        )

    # Password strength is validated centrally before provisioning begins.
    setup = _run_native_setup(
        company_name,
        country,
        administrator_name,
        email,
        password,
        currency,
        financial_year_start,
        abbr,
    )

    _ensure_administrator(email, password)
    contact = _ensure_administrator_contact(
        email, administrator_name, phone
    )

    frappe.clear_cache()
    frappe.db.commit()

    if not frappe.is_setup_complete():
        states = frappe.get_all(
            "Installed Application",
            filters={"app_name": ["in", ["frappe", "erpnext"]]},
            fields=["app_name", "has_setup_wizard", "is_setup_complete"],
        )
        frappe.throw(
            _("Setup did not complete. App status: {0}").format(
                json.dumps(states, default=str)
            )
        )

    # Install the Procurement onboarding checklist for this tenant.
    _ensure_procurement_onboarding()
    frappe.db.commit()

    return {
        "company": setup["company"],
        "administrator": email,
        "contact": contact,
        "setup_complete": True,
    }


def initialize_tenant_from_file():
    """Bench-execute entry point reading the short-lived protected payload."""
    file_name = os.environ.get("KENTENDER_TENANT_PAYLOAD_FILE")

    if not file_name:
        frappe.throw(_("Missing tenant initialization payload file."))

    path = Path(file_name).resolve()
    sites_dir = Path(frappe.get_site_path()).parent.resolve()

    if (
        path.parent != sites_dir
        or not path.name.startswith(".tenant-onboarding-")
        or path.suffix != ".json"
    ):
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

