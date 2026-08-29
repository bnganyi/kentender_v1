"""Retire the four legacy Departmental Needs Desk pages.

NDS-CHG-001 v1.1 §10 gives the module one Page — `departmental-needs` — with
every NDS-UI route as a segment beneath it. The pre-v1.1 implementation used a
separate Page per screen (`-new`, `-edit`, `-review`, `-detail`), each a
jQuery controller built against the retired schema.

The Vue page that replaces them lands in the same change, so the records go
now rather than lingering as dead routes that still resolve (§17 forbids a
compatibility redirect, so they are removed outright rather than pointed at
the new page).

Runs post-model-sync: it edits Page records, not schema.
"""

import frappe

RETIRED_PAGES = (
	"departmental-needs-new",
	"departmental-needs-edit",
	"departmental-needs-review",
	"departmental-needs-detail",
	# Never part of §10; created by an earlier iteration of the page generator.
	"departmental-needs-intake-window",
)


def execute():
	removed = []
	for page in RETIRED_PAGES:
		if not frappe.db.exists("Page", page):
			continue
		frappe.delete_doc("Page", page, force=True, ignore_permissions=True, delete_permanently=True)
		removed.append(page)
	if removed:
		frappe.clear_cache()
		print(f"Retired legacy Departmental Needs pages: {removed}")
