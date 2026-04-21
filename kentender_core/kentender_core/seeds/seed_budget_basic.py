# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""seed_budget_basic — single FY2026 budget with two allocations."""

from __future__ import annotations

import frappe

from kentender_core.seeds._budget_seed_common import (
	BUDGET_2026_NAME,
	clear_budget_data,
	get_plan_name,
	get_program_name,
	upsert_budget,
	upsert_budget_allocation,
)
from kentender_core.seeds.seed_strategy_basic import run as run_strategy_basic


def run():
	frappe.only_for(("System Manager", "Administrator"))
	run_strategy_basic()

	# Deterministic scenario: keep only the records in this pack.
	clear_budget_data()
	out = _seed_basic()
	frappe.db.commit()
	return out


def _seed_basic():
	plan_name = get_plan_name()
	budget_name = upsert_budget(
		budget_name=BUDGET_2026_NAME,
		fiscal_year=2026,
		strategic_plan=plan_name,
		total_budget_amount=8_000_000,
		notes="Initial budget aligned to MOH strategic plan priorities",
	)

	healthcare_program = get_program_name(plan_name, "Healthcare Access")
	workforce_program = get_program_name(plan_name, "Workforce Development")

	a1 = upsert_budget_allocation(
		budget=budget_name,
		program=healthcare_program,
		amount=5_000_000,
		notes="Expansion of rural healthcare coverage and facilities",
		order_index=1,
	)
	a2 = upsert_budget_allocation(
		budget=budget_name,
		program=workforce_program,
		amount=3_000_000,
		notes="Workforce training and recruitment",
		order_index=2,
	)

	return {
		"plan": plan_name,
		"budgets": [budget_name],
		"allocations": [a1, a2],
	}

