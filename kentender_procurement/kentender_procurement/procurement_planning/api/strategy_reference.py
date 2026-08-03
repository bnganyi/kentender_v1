# Copyright (c) 2026, KenTender and contributors
"""Planning consumer adapter for Strategy Reference DTO (§16.1)."""

from __future__ import annotations

import frappe


@frappe.whitelist()
def list_active_strategy_targets(procuring_entity: str | None = None, plan_code: str | None = None):
	from kentender_strategy.services.strategy_consumer import active_target_options

	return active_target_options(procuring_entity=procuring_entity or None, plan_code=plan_code or None)


@frappe.whitelist()
def validate_planning_strategy_reference(reference=None):
	from kentender_strategy.api.strategy_api import validate_strategy_reference

	return validate_strategy_reference(reference=reference)
