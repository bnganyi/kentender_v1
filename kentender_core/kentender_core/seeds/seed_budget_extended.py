# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""seed_budget_extended — FY2026 + FY2027 budgets; second budget partially allocated."""

from __future__ import annotations

import frappe

from kentender_core.seeds._budget_seed_common import (
	BUDGET_2026_NAME,
	BUDGET_2027_NAME,
	get_plan_name,
	get_program_name,
	set_budget_status_for_seed,
	upsert_budget,
	upsert_budget_allocation,
)
from kentender_core.seeds.seed_budget_basic import run as run_budget_basic


def run():
	frappe.only_for(("System Manager", "Administrator"))
	from kentender_core.seeds.seed_budget_line_dia import run as run_budget_line_dia

	# Extended must include everything from basic, then add second budget.
	basic = run_budget_basic()
	out = _add_budget_2027()
	lines = run_budget_line_dia(include_budget_extended=False)
	frappe.db.commit()
	return {"basic": basic, "extended": out, "budget_lines": lines}


def _add_budget_2027():
	plan_name = get_plan_name()
	budget_2027 = upsert_budget(
		budget_name=BUDGET_2027_NAME,
		fiscal_year=2027,
		strategic_plan=plan_name,
		total_budget_amount=9_000_000,
		notes="Adjusted allocations for following fiscal year",
	)

	healthcare_program = get_program_name(plan_name, "Healthcare Access")
	workforce_program = get_program_name(plan_name, "Workforce Development")

	alloc = upsert_budget_allocation(
		budget=budget_2027,
		program=healthcare_program,
		amount=6_000_000,
		notes="Increased infrastructure investment",
		order_index=1,
	)

	# Explicitly enforce spec: Workforce Development remains unallocated for FY2027.
	existing_workforce_alloc = frappe.db.get_value(
		"Budget Allocation",
		{"budget": budget_2027, "program": workforce_program},
		"name",
	)
	if existing_workforce_alloc:
		frappe.delete_doc(
			"Budget Allocation",
			existing_workforce_alloc,
			ignore_permissions=True,
			force=True,
		)

	# B5.6: FY2027 remains Draft in DB until allocations exist; then Submitted for approval-flow tests.
	set_budget_status_for_seed(budget_2027, "Submitted")

	return {
		"plan": plan_name,
		"budgets": [BUDGET_2026_NAME, budget_2027],
		"allocations_created_or_updated": [alloc],
	}

