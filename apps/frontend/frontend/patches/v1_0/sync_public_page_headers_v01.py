import importlib

import frappe


DEFAULT_LOGO_URL = (
    "https://ik.imagekit.io/kltovsgah/kentender_logo.png"
)

PAGE_TEMPLATES = {
    "home": "frontend.patches.v1_0.create_homepage_v22",
    "about": "frontend.patches.v1_0.create_about_page_v06",
    "all-tenders": "frontend.patches.v1_0.create_all_tenders_page_v07",
    "contracts": "frontend.patches.v1_0.create_awarded_tenders_page_v07",
    "industry/donor": "frontend.patches.v1_0.create_donor_industry_page_v07",
    "industry/private": "frontend.patches.v1_0.create_private_industry_page_v07",
    "industry/public": "frontend.patches.v1_0.create_public_industry_page_v07",
}


def execute():
    website_settings = frappe.get_single("Website Settings")

    tenant_logo = (
        website_settings.app_logo
        or DEFAULT_LOGO_URL
    )

    for route, module_path in PAGE_TEMPLATES.items():

        page_names = frappe.get_all(
            "Web Page",
            filters={"route": route},
            pluck="name",
        )

        if len(page_names) != 1:
            frappe.throw(
                f"Expected one Web Page for route '{route}', "
                f"found {len(page_names)}"
            )

        template_module = importlib.import_module(module_path)

        page = frappe.get_doc("Web Page", page_names[0])

        page_html = template_module.PAGE_HTML.replace(
            DEFAULT_LOGO_URL,
            tenant_logo,
        )

        page.main_section_html = page_html
        page.save(ignore_permissions=True)

    frappe.clear_cache()
