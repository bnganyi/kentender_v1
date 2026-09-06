# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.5 §10/§10.1 — the 4 downstream read/action contracts and
the 6 plan-version command contracts, as thin whitelisted wrappers.

Every state-changing command here returns the same refreshed-state shape
as kentender_strategy.services.strategy_transitions._version_payload:
{name, plan_version_id, plan_id, status, expected_version, allowed_actions}
(AGENTS.md §5 — server-computed action order is part of the contract).
"""

from __future__ import annotations

import json

import frappe

from kentender_strategy.services import strategy_consumer as consumer
from kentender_strategy.services import strategy_transitions as transitions
from kentender_strategy.services import strategy_writes as writes
from kentender_strategy.services.strategy_idempotency import run_idempotent


def _obj(value):
	if value is None or value == "":
		return None
	if isinstance(value, (dict, list)):
		return value
	if isinstance(value, str):
		try:
			return json.loads(value)
		except (TypeError, ValueError):
			return value
	return value


# --- §10 read/action contracts -------------------------------------------------


@frappe.whitelist()
def resolve_strategy_context(
	as_of_date: str | None = None,
	fiscal_year: str | None = None,
	include_supporting: bool | str | int = False,
):
	"""STR-CHG-001 v1.7 §7/§8 — exactly one of `as_of_date` or `fiscal_year`;
	no Procuring Entity or organisation-unit input exists."""
	return consumer.resolve_strategy_context(
		as_of_date=as_of_date or None,
		fiscal_year=fiscal_year or None,
		include_supporting=str(include_supporting).lower() in ("1", "true", "yes"),
	)


@frappe.whitelist()
def list_strategy_objectives(
	plan_version_id: str,
	parent_node_id: str | None = None,
	search: str | None = None,
	limit_start: int = 0,
	limit_page_length: int = 20,
):
	return consumer.list_strategy_objectives(
		plan_version_id,
		parent_node_id=parent_node_id or None,
		search=search or None,
		limit_start=int(limit_start or 0),
		limit_page_length=int(limit_page_length or 20),
	)


@frappe.whitelist()
def get_strategy_lineage(node_id: str):
	return consumer.get_strategy_lineage(node_id)


@frappe.whitelist()
def list_active_targets(plan_code: str | None = None):
	"""Relocated from the retired `strategy_api.py` (STR-CHG-001 v1.6 cleanup)
	— the Budget Line "primary target" picker's live dropdown source
	(`kentender_budget`'s `budget_live_bind.js::loadTargetOptions`)."""
	return consumer.active_target_options(plan_code=plan_code or None)


@frappe.whitelist()
def create_strategy_snapshot(plan_version_id: str, objective_id: str, correlation_key: str):
	return run_idempotent(
		correlation_key,
		"Strategy Node",
		objective_id,
		"Strategy Snapshot Created",
		lambda: consumer.create_strategy_snapshot(
			plan_version_id=plan_version_id, objective_id=objective_id, correlation_key=correlation_key
		),
	)


# --- §10.1 command contracts ----------------------------------------------------


@frappe.whitelist()
def save_strategy_plan_draft(payload=None, expected_version: str | None = None):
	return writes.save_strategy_plan_draft(_obj(payload) or {}, expected_version=expected_version or None)


@frappe.whitelist()
def create_strategy_successor_version(plan_id: str):
	return writes.create_strategy_successor_version(plan_id)


@frappe.whitelist()
def save_strategy_structure_draft(
	plan_version_id: str,
	nodes=None,
	indicators=None,
	targets=None,
	deletes=None,
	expected_version: str | None = None,
):
	return writes.save_strategy_structure_draft(
		plan_version_id,
		nodes=_obj(nodes) or [],
		indicators=_obj(indicators) or [],
		targets=_obj(targets) or [],
		deletes=_obj(deletes) or [],
		expected_version=expected_version or None,
	)


@frappe.whitelist()
def submit_strategy_version(
	plan_version_id: str, expected_version: str | None = None, correlation_id: str | None = None
):
	return transitions.transition_plan_version(
		plan_version_id,
		"Submit for approval",
		expected_version=expected_version or None,
		correlation_id=correlation_id or None,
	)


@frappe.whitelist()
def return_strategy_version(
	plan_version_id: str,
	reason: str,
	expected_version: str | None = None,
	correlation_id: str | None = None,
):
	"""§10.1 return_strategy_version — Strategy Approver only, Submitted for
	approval only. Requires a 10-500 character correction reason."""
	return transitions.transition_plan_version(
		plan_version_id,
		"Return",
		reason=reason,
		expected_version=expected_version or None,
		correlation_id=correlation_id or None,
	)


@frappe.whitelist()
def approve_strategy_version(
	plan_version_id: str, expected_version: str | None = None, correlation_id: str | None = None
):
	"""§10.1 approve_strategy_version — Strategy Approver only, Submitted for
	approval only. Revalidates readiness/overlap and activates the version,
	atomically superseding the plan's previous Active version in the same
	transaction — there is no separate Activate action any more."""
	return transitions.transition_plan_version(
		plan_version_id,
		"Approve",
		expected_version=expected_version or None,
		correlation_id=correlation_id or None,
	)
