"""Departmental Needs Desk page roles (NDS-CHG-001 v1.1 §6, §10).

§10 gives the module exactly three menu entries: **Departmental Needs**,
**Review tasks** (effective Head of User Department only) and **Intake window**
(effective Procurement Planner only). Procurement Planners use the Procurement
Planning workspace and reach an accepted Need through a read-only deep link;
they do not receive a landing page, and §17 forbids a Planner, Budget Officer,
Accounting Officer or support dashboard in this module (NDS-AC-023).

`generate()` reconciles the role list on every run rather than skipping when the
Page already exists, so a role removed by §1.1 cannot survive in an existing
environment.

The pages themselves are the legacy jQuery surfaces and are non-functional
against the v1.1 schema. Phase 7 replaces them with the Vue-in-Desk routes in
§10 and deletes these records; until then this module only guarantees that no
prohibited role can reach them.
"""

from __future__ import annotations

import frappe

# Roles that may open a Departmental Needs surface at all (§6).
LANDING_ROLES: tuple[str, ...] = (
	"Administrator",
	"System Manager",
	"Departmental Author",
	"Head of User Department",
	"Auditor",
)

# §10 — the departmental decision queue is not visible outside the department.
REVIEW_ROLES: tuple[str, ...] = (
	"Administrator",
	"System Manager",
	"Head of User Department",
)

# §10 / NDS-AC-043 — the Planner maintains the window and nothing else here.
INTAKE_WINDOW_ROLES: tuple[str, ...] = (
	"Administrator",
	"System Manager",
	"Procurement Planner",
)

PAGE_ROLES: dict[str, tuple[str, ...]] = {
	"departmental-needs": LANDING_ROLES,
	"departmental-needs-new": LANDING_ROLES,
	"departmental-needs-edit": LANDING_ROLES,
	"departmental-needs-detail": LANDING_ROLES,
	"departmental-needs-review": REVIEW_ROLES,
	"departmental-needs-intake-window": INTAKE_WINDOW_ROLES,
}


def _reconcile(page_name: str, roles: tuple[str, ...]) -> bool:
	"""Make the Page's role list exactly `roles`. Returns True when it changed."""
	page = frappe.get_doc("Page", page_name)
	current = sorted({row.role for row in page.roles})
	wanted = sorted(set(roles))
	if current == wanted:
		return False
	page.set("roles", [{"role": role} for role in wanted])
	page.save(ignore_permissions=True)
	return True


def generate() -> list[str]:
	"""Create the landing Page if absent, then reconcile every page's roles."""
	frappe.flags.allow_doctype_export = True
	changed: list[str] = []
	if not frappe.db.exists("Page", "departmental-needs"):
		frappe.get_doc(
			{
				"doctype": "Page",
				"page_name": "departmental-needs",
				"title": "Departmental Needs",
				"module": "Departmental Needs",
				"standard": "Yes",
				"system_page": 0,
				"roles": [{"role": role} for role in LANDING_ROLES],
			}
		).insert(ignore_permissions=True)
		changed.append("departmental-needs")
	for page_name, roles in PAGE_ROLES.items():
		if page_name in changed or not frappe.db.exists("Page", page_name):
			continue
		if _reconcile(page_name, roles):
			changed.append(page_name)
	frappe.db.commit()
	return changed
