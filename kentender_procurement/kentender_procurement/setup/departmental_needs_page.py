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

# §6/§10 — one Page ("departmental-needs") carries all eight NDS-UI routes, so
# its role list is the union of everyone §6 admits to any Departmental Needs
# surface. A role left out here is locked out of the whole module, not merely
# out of the one route it should not see.
#
# Until Phase 9 this file still described the pre-v1.1 world of six Pages with
# a role list each, and the survivor kept the narrow landing list — which left
# the Procurement Planner unable to open the Page at all, and so unable to
# reach the intake window §10 gives them a menu entry for (NDS-AC-043).
#
# Per-route authority is *not* expressed here. §17 puts it on the server: the
# Planner reaching this Page reads only accepted sources (`can_view`), holds no
# Need decision, and every command re-checks its own role. The §10 menu decides
# what each role is shown.
LANDING_ROLES: tuple[str, ...] = (
	"Administrator",
	"System Manager",
	"Departmental Author",
	"Head of User Department",
	"Procurement Planner",
	"Auditor",
)

PAGE_ROLES: dict[str, tuple[str, ...]] = {
	# The five per-screen Pages this map used to name were deleted in Phase 7
	# (patch nds_chg_001_v11_retire_legacy_pages); reconciling them recreated
	# nothing but did assert they existed.
	"departmental-needs": LANDING_ROLES,
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
