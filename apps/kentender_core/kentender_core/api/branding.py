import frappe


@frappe.whitelist(allow_guest=True)
def get_tenant_branding():
    """
    Retrieve branding dynamically from the current tenant's
    Website Settings.

    Each tenant returns its own branding based on the site
    handling the request.
    """

    try:
        settings = frappe.get_single("Website Settings")

        # Get the default company configured for this tenant.
        company = frappe.db.get_single_value(
            "Global Defaults",
            "default_company"
        )

        company_name = None

        if company:
            company_name = frappe.db.get_value(
                "Company",
                company,
                "company_name"
            )

        return {
            "success": True,
            "branding": {
                "app_name": settings.get("app_name"),
                "app_logo": settings.get("app_logo"),
                "title_prefix": settings.get("title_prefix"),
                "organization_name": company_name
            }
        }

    except Exception:
        frappe.log_error(
            title="Tenant Branding Retrieval Failed",
            message=frappe.get_traceback()
        )

        return {
            "success": False,
            "message": "Unable to retrieve tenant branding."
        }
