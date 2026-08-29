"""Strip prohibited roles from the Departmental Needs Desk pages.

NDS-CHG-001 v1.1 §17 forbids a Planner, Budget Officer, Accounting Officer or
support dashboard in this module, and NDS-AC-023 requires that Budget Officer
and Accounting Officer receive no Departmental Needs workspace, task or special
action. The existing `departmental-needs-detail` page granted all three, and
the page generator referenced two roles §1.1 removed.

Runs post-model-sync because it edits Page records, not schema.
"""

import frappe

from kentender_procurement.setup.departmental_needs_page import generate

# Never permitted on a Departmental Needs surface (§6, §17, NDS-AC-023).
PROHIBITED_ROLES = (
	"Budget Officer",
	"Accounting Officer",
	"Departmental Need Requester",
	"Departmental Review Delegate",
	"Needs Configuration Manager",
)


def execute():
	changed = generate()
	# Belt and braces: catch any Departmental Needs page the generator does not
	# name, including one added by hand on an existing site.
	pages = frappe.get_all(
		"Page", filters={"name": ("like", "departmental-needs%")}, pluck="name"
	)
	for page in pages:
		stale = frappe.get_all(
			"Has Role",
			filters={
				"parent": page,
				"parenttype": "Page",
				"role": ("in", list(PROHIBITED_ROLES)),
			},
			pluck="name",
		)
		if not stale:
			continue
		frappe.db.delete("Has Role", {"name": ("in", stale)})
		changed.append(page)
	frappe.clear_cache()
	if changed:
		print(f"Departmental Needs page roles reconciled: {sorted(set(changed))}")
