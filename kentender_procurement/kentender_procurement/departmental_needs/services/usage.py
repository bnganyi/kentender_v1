"""Planning usage projection (NDS-CHG-001 v1.1 §4.7).

The projection is only `Not included` or `Fully included`. `Partially included`
is removed by §1.1 and forbidden by §17, along with any partial Need allocation
or Planning quantity override (NDS-AC-014, NDS-AC-015).

Phase 5 replaces these direct reads of Planning's allocation table with the
`NeedPlanningUsageChanged.v1` event required by §3 and §7.2.
"""

from __future__ import annotations

import frappe
from frappe.utils import flt

from kentender_procurement.departmental_needs.constants import USAGE_FULL, USAGE_NOT_INCLUDED


def planning_usage(need: str) -> str:
	"""A Need is included only when its full accepted quantity is represented."""
	accepted_version = frappe.db.get_value(
		"Departmental Need", need, "current_accepted_version"
	)
	if not accepted_version:
		return USAGE_NOT_INCLUDED
	required = flt(
		frappe.db.get_value("Departmental Need Version", accepted_version, "indicative_quantity")
	)
	if required <= 0:
		return USAGE_NOT_INCLUDED
	allocated = flt(
		frappe.db.sql(
			"""
			select coalesce(sum(allocated_quantity), 0)
			from `tabPlan Need Allocation`
			where departmental_need = %s and status = 'Effective'
			""",
			need,
		)[0][0]
	)
	return USAGE_FULL if allocated >= required else USAGE_NOT_INCLUDED


def effective_allocation_count(need: str) -> int:
	return frappe.db.count("Plan Need Allocation", {"departmental_need": need, "status": "Effective"})


def draft_allocation_count(need: str) -> int:
	return frappe.db.count("Plan Need Allocation", {"departmental_need": need, "status": "Draft"})
