import frappe


PUBLIC_PAGE_ROUTES = (
	"home",
	"all-tenders",
	"contracts",
	"industry/donor",
	"industry/private",
	"industry/public",
)
OLD_TENDERS_HREF = 'href="/tenders"'
NEW_TENDERS_HREF = 'href="/all-tenders"'


def execute():
	old_page_names = frappe.get_all(
		"Web Page",
		filters={"route": "tenders"},
		pluck="name",
	)
	new_page_names = frappe.get_all(
		"Web Page",
		filters={"route": "all-tenders"},
		pluck="name",
	)
	if len(old_page_names) > 1 or len(new_page_names) > 1:
		frappe.throw("Expected a single Web Page for the old and new tender routes.")

	route_changed = False
	if old_page_names:
		old_page = frappe.get_doc("Web Page", old_page_names[0])
		if new_page_names:
			old_page.published = 0
		else:
			old_page.route = "all-tenders"
		old_page.save(ignore_permissions=True)
		route_changed = True

	page_names = frappe.get_all(
		"Web Page",
		filters={"route": ["in", PUBLIC_PAGE_ROUTES]},
		pluck="name",
	)
	changed = route_changed

	for page_name in page_names:
		page = frappe.get_doc("Web Page", page_name)
		content = page.main_section_html or ""
		updated_content = content.replace(OLD_TENDERS_HREF, NEW_TENDERS_HREF)
		if updated_content == content:
			continue

		page.main_section_html = updated_content
		page.save(ignore_permissions=True)
		changed = True

	if changed:
		frappe.clear_cache()