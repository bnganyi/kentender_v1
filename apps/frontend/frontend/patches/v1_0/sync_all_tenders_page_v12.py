import frappe

from frontend.patches.v1_0 import create_all_tenders_page_v07


def execute():
	page_names = frappe.get_all(
		"Web Page",
		filters={"route": "all-tenders"},
		pluck="name",
	)
	if len(page_names) != 1:
		frappe.throw(f"Expected one Web Page for route 'all-tenders', found {len(page_names)}")

	page = frappe.get_doc("Web Page", page_names[0])
	if page.main_section_html != create_all_tenders_page_v07.PAGE_HTML:
		page.main_section_html = create_all_tenders_page_v07.PAGE_HTML
		page.save(ignore_permissions=True)
		frappe.clear_cache()
