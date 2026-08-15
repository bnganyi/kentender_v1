"""Retire PLN-UI-10 and the Planning-owned publication projection."""

import frappe


def execute() -> None:
	if frappe.db.exists("DocType", "Publication Event"):
		filters = {}
		if frappe.db.has_column("Publication Event", "fixture_namespace"):
			filters = {"fixture_namespace": ["not in", ["KENTENDER_PLAYWRIGHT", "KENTENDER_SCENARIO", "KENTENDER_DESIGN"]]}
		persistent = frappe.get_all("Publication Event", filters=filters, pluck="name", limit_page_length=20)
		if persistent:
			frappe.throw(
				"Planning publication cleanup stopped: non-fixture audit evidence exists: " + ", ".join(persistent),
				title="PLN_PUBLICATION_HISTORY_REQUIRES_REVIEW",
			)
		for name in frappe.get_all("Publication Event", pluck="name"):
			frappe.delete_doc("Publication Event", name, force=1, ignore_permissions=True)
	if frappe.db.exists("Page", "procurement-plan-update"):
		frappe.delete_doc("Page", "procurement-plan-update", force=1, ignore_permissions=True)
