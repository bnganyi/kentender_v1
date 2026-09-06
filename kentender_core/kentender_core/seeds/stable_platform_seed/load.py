# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Load stable platform seed — Works golden path + IT supplement + IT STD v1_1."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import (
	ensure_currency_kes,
	ensure_moh_entity_permission_aliases,
	ensure_procuring_entity,
)
from kentender_core.seeds.stable_platform_seed.clear import clear_stable_platform_seed
from kentender_core.seeds.stable_platform_seed.constants import (
	DEFAULT_PLANNING_CHECKPOINT,
	MASTER_SCENARIO_IT,
	MASTER_SCENARIO_WORKS,
	PACK_NAME,
	PACK_TITLE,
	PE_CODE,
	PE_DISPLAY,
	SUPPORTED_PLANNING_CHECKPOINTS,
)
from kentender_core.seeds.stable_platform_seed.it_budget import upsert_it_budget_supplement
from kentender_core.seeds.stable_platform_seed.it_strategy import upsert_it_strategy_supplement
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import (
	upsert_works_master_journey,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy


def load_stable_platform_seed(
	*,
	reset: bool = False,
	planning_checkpoint: str = DEFAULT_PLANNING_CHECKPOINT,
	import_it_std: bool = True,
	include_it_supplement: bool = True,
	purge_non_master: bool = False,
) -> dict[str, Any]:
	"""Regenerate the MOH stable platform seed pack.

	Order:
	1. Optional clear (when ``reset=True``)
	2. Core prerequisites (entity, users)
	3. Strategy (WORKS + IT supplement)
	4. Budget (WORKS + IT supplement)
	5. Journey (required for PP2 upstream)
	6. DIA / Demand (WORKS + IT supplement)
	7. Planning PP2 WORKS checkpoint
	8. Planning IT supplement (inclusion + package draft)
	9. IT STD v1_1 import

	:param reset: Clear existing stable pack rows before loading.
	:param planning_checkpoint: PP2 WORKS checkpoint (default ``READY_FOR_RELEASE``).
	:param import_it_std: Import KE-PPRA-IT-2022-04 v1_1 into STD Engine.
	:param include_it_supplement: Load IT strategy/budget/demand/planning supplement.
	:param purge_non_master: When resetting, purge smoke rows outside master registry.
	"""
	frappe.only_for(("System Manager", "Administrator"))
	frappe.set_user("Administrator")

	checkpoint = (planning_checkpoint or DEFAULT_PLANNING_CHECKPOINT).strip().upper()
	if checkpoint not in SUPPORTED_PLANNING_CHECKPOINTS:
		return {
			"ok": False,
			"error_code": "UNSUPPORTED_CHECKPOINT",
			"message": f"Supported checkpoints: {', '.join(SUPPORTED_PLANNING_CHECKPOINTS)}",
			"checkpoint": checkpoint,
		}

	warnings: list[str] = []
	stages: dict[str, Any] = {}

	if reset:
		stages["clear"] = clear_stable_platform_seed(
			purge_non_master=purge_non_master,
			clear_it_std=import_it_std,
			skip_guard=bool(frappe.in_test),
		)
		if not stages["clear"].get("ok"):
			return {**stages["clear"], "stage_failed": "clear", "warnings": warnings}

	ensure_currency_kes()
	ensure_procuring_entity(PE_CODE, PE_DISPLAY)
	for email, _full_name, _role, _dept in C.SEED_USERS:
		if frappe.db.exists("User", email):
			ensure_moh_entity_permission_aliases(email, C.ENTITY_MOH)
	stages["core"] = {"ok": True, "procuring_entity": PE_CODE}

	strategy = upsert_works_master_strategy_hierarchy()
	stages["strategy_works"] = strategy
	if not strategy.get("ok"):
		return {**strategy, "stage_failed": "strategy_works", "warnings": warnings}
	warnings.extend(strategy.get("warnings") or [])

	if include_it_supplement:
		it_strategy = upsert_it_strategy_supplement()
		stages["strategy_it"] = it_strategy
		if not it_strategy.get("ok"):
			return {**it_strategy, "stage_failed": "strategy_it", "warnings": warnings}

	budget = upsert_works_master_budget()
	stages["budget_works"] = budget
	if not budget.get("ok"):
		return {**budget, "stage_failed": "budget_works", "warnings": warnings}
	warnings.extend(budget.get("warnings") or [])

	if include_it_supplement:
		it_budget = upsert_it_budget_supplement()
		stages["budget_it"] = it_budget
		if not it_budget.get("ok"):
			return {**it_budget, "stage_failed": "budget_it", "warnings": warnings}

	journey = upsert_works_master_journey(reset=reset)
	stages["journey"] = journey
	if not journey.get("ok"):
		return {**journey, "stage_failed": "journey", "warnings": warnings}
	warnings.extend(journey.get("warnings") or [])

	# DIA Demand domain retired pending Demands MVP-1 rebuild.
	stages["demand_works"] = {
		"ok": True,
		"skipped": True,
		"reason": "DEMAND_MODULE_RETIRED",
	}
	if include_it_supplement:
		stages["demand_it"] = {
			"ok": True,
			"skipped": True,
			"reason": "DEMAND_MODULE_RETIRED",
		}
	warnings.append(
		"Demand Intake retired — WORKS/IT Demand seed skipped (Demands MVP-1 pending)."
	)

	stages["planning_works"] = {"ok": True, "skipped": True, "reason": "PP2_PLANNING_RETIRED"}
	if include_it_supplement:
		stages["planning_it"] = {"ok": True, "skipped": True, "reason": "PP2_PLANNING_RETIRED"}
	warnings.append("PP2 Planning retired — WORKS/IT planning seed skipped (Planning MVP-1 pending).")

	if import_it_std:
		stages["std_it"] = {"ok": True, "skipped": True, "reason": "STD_ENGINE_RETIRED"}
		warnings.append(
			"STD Engine retired — IT STD v1.1 package import skipped (no STD package registry)."
		)

	frappe.db.commit()

	return {
		"ok": True,
		"pack": PACK_NAME,
		"pack_title": PACK_TITLE,
		"planning_checkpoint": checkpoint,
		"scenarios": {
			"works": MASTER_SCENARIO_WORKS,
			"it": MASTER_SCENARIO_IT if include_it_supplement else None,
		},
		"stages": stages,
		"warnings": warnings,
		"status": "loaded",
	}
