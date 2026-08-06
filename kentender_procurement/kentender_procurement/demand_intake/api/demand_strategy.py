# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Create Demand / DIA Strategy helpers (XMOD-STR-002 / 003)."""

from __future__ import annotations

import frappe

from kentender_procurement.demand_intake.api.dia_access import require_dia_workspace_user
from kentender_procurement.demand_intake.services.demand_strategy_value import list_demand_applicable_pvcs


@frappe.whitelist()
def list_active_targets_for_demand(procuring_entity: str | None = None) -> list[dict]:
	"""Whitelist wrapper for create-demand Active target picker."""
	require_dia_workspace_user()
	from kentender_strategy.services.strategy_consumer import active_target_options

	return active_target_options(procuring_entity=procuring_entity or None)


@frappe.whitelist()
def list_applicable_pvcs_for_demand(demand_name: str | None = None) -> list[dict]:
	"""Return applicable PVCs for an existing Demand (Review step)."""
	require_dia_workspace_user()
	name = (demand_name or "").strip()
	if not name or not frappe.db.exists("Demand", name):
		return []
	doc = frappe.get_doc("Demand", name)
	rows = list_demand_applicable_pvcs(doc)
	out = []
	for r in rows:
		obj = r.get("objective") or {}
		out.append(
			{
				"pvc_id": r.get("id"),
				"pvc_code": obj.get("code") or "",
				"pvc_name": obj.get("name") or "",
				"requirement_level": r.get("consideration_level") or "",
				"pillar": r.get("pillar") or "",
				"rationale": r.get("rationale") or "",
			}
		)
	return out
