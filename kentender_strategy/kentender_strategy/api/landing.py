# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Strategy Management workspace — single payload for KPIs, plan list, and hierarchy counts."""

from typing import Dict, Tuple

import frappe
from frappe import _


def _counts_by_plan(plan_names: list) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
	"""Return three maps: strategic_plan -> count for Program / Objective / Target."""
	if not plan_names:
		return {}, {}, {}
	params = tuple(plan_names)
	prog: dict[str, int] = {}
	obj: dict[str, int] = {}
	tgt: dict[str, int] = {}
	for row in frappe.db.sql(
		"""
		SELECT strategic_plan, COUNT(*) AS c
		FROM `tabStrategy Program`
		WHERE strategic_plan IN %(plans)s
		GROUP BY strategic_plan
		""",
		{"plans": params},
		as_dict=True,
	):
		prog[row.strategic_plan] = int(row.c or 0)
	for row in frappe.db.sql(
		"""
		SELECT strategic_plan, COUNT(*) AS c
		FROM `tabStrategy Objective`
		WHERE strategic_plan IN %(plans)s
		GROUP BY strategic_plan
		""",
		{"plans": params},
		as_dict=True,
	):
		obj[row.strategic_plan] = int(row.c or 0)
	for row in frappe.db.sql(
		"""
		SELECT strategic_plan, COUNT(*) AS c
		FROM `tabStrategy Target`
		WHERE strategic_plan IN %(plans)s
		GROUP BY strategic_plan
		""",
		{"plans": params},
		as_dict=True,
	):
		tgt[row.strategic_plan] = int(row.c or 0)
	return prog, obj, tgt


@frappe.whitelist()
def get_strategy_landing_data():
	"""Portfolio KPIs + Strategic Plan rows with embedded hierarchy counts (current versions only)."""
	if not frappe.has_permission("Strategic Plan", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	plans = frappe.get_all(
		"Strategic Plan",
		filters={"is_current_version": 1},
		fields=[
			"name",
			"strategic_plan_name",
			"start_year",
			"end_year",
			"status",
			"modified",
			"owner",
			"procuring_entity",
		],
		order_by="modified desc",
		limit=2000,
	)

	session_user = frappe.session.user

	empty_portfolio = {
		"total_plans": 0,
		"draft_count": 0,
		"active_count": 0,
		"archived_count": 0,
		"my_drafts_count": 0,
		"total_programs": 0,
	}

	if not plans:
		return {"portfolio": empty_portfolio, "plans": []}

	names = [p.name for p in plans]
	prog_by, obj_by, tgt_by = _counts_by_plan(names)

	draft_count = sum(1 for p in plans if (p.get("status") or "").strip() == "Draft")
	active_count = sum(1 for p in plans if (p.get("status") or "").strip() == "Active")
	archived_count = sum(1 for p in plans if (p.get("status") or "").strip() == "Archived")
	my_drafts_count = sum(
		1
		for p in plans
		if (p.get("status") or "").strip() == "Draft" and p.get("owner") == session_user
	)
	total_programs = sum(prog_by.get(n, 0) for n in names)

	out_plans = []
	for p in plans:
		n = p.name
		pc = int(prog_by.get(n, 0))
		oc = int(obj_by.get(n, 0))
		tc = int(tgt_by.get(n, 0))
		out_plans.append(
			{
				**p,
				"program_count": pc,
				"objective_count": oc,
				"target_count": tc,
			}
		)

	return {
		"portfolio": {
			"total_plans": len(plans),
			"draft_count": draft_count,
			"active_count": active_count,
			"archived_count": archived_count,
			"my_drafts_count": my_drafts_count,
			"total_programs": total_programs,
		},
		"plans": out_plans,
	}
