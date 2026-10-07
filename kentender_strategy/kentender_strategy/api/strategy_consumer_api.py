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
from kentender_strategy.services.strategy_authorization import require_downstream_read, require_plan_create_capability
from kentender_strategy.services import strategy_transitions as transitions
from kentender_strategy.services import strategy_writes as writes
from kentender_strategy.services.strategy_idempotency import require_command_inputs, run_idempotent


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
	require_downstream_read()
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
	require_downstream_read()
	return consumer.list_strategy_objectives(
		plan_version_id,
		parent_node_id=parent_node_id or None,
		search=search or None,
		limit_start=int(limit_start or 0),
		limit_page_length=int(limit_page_length or 20),
	)


@frappe.whitelist()
def get_strategy_lineage(node_id: str):
	require_downstream_read()
	return consumer.get_strategy_lineage(node_id)


@frappe.whitelist()
def list_active_targets(plan_code: str | None = None):
	"""Relocated from the retired `strategy_api.py` (STR-CHG-001 v1.6 cleanup)
	— the Budget Line "primary target" picker's live dropdown source
	(`kentender_budget`'s `budget_live_bind.js::loadTargetOptions`)."""
	require_downstream_read()
	return consumer.active_target_options(plan_code=plan_code or None)


def create_strategy_snapshot(plan_version_id: str, objective_id: str, correlation_key: str):
	"""Not an endpoint (RG-34): it writes an audit event and a journal row, and the only gate was the read
	gate every internal user passes. Planning freezes lineage by calling the service in-process
	(`procurement_planning.services.strategy_gateway`); the function stays here for that contract and
	refuses portal and other external accounts."""
	require_downstream_read()
	return run_idempotent(
		correlation_key,
		"Strategy Node",
		objective_id,
		"Strategy Snapshot Created",
		lambda: consumer.create_strategy_snapshot(
			plan_version_id=plan_version_id, objective_id=objective_id, correlation_key=correlation_key
		),
		payload={"plan_version_id": plan_version_id, "objective_id": objective_id},
		authorise=require_downstream_read,
	)


# --- §8/§8.2 command contracts ---------------------------------------------------
#
# Every write command is retriable and carries its attempt's `idempotency_key`
# (KT-STD-001 §11: "every retriable command carries an idempotency key"); one
# on an existing version also carries `expected_version` (STR §8: "every write
# command requires the expected record version"). The client captures one key
# per attempt and reuses it on retry and after a lost response. The journal
# (`strategy_idempotency`) binds the key to the actor, the command and its
# payload, answers only after authorisation, and returns the original
# committed result on replay, so no attempt ever creates a second plan,
# version, submission or decision. The key's payload is the command's own
# inputs, so the same key with other inputs is `STRATEGY_IDEMPOTENCY_CONFLICT`.


def _authorise_author() -> None:
	"""Strategy Author, Site-wide (STR §7). State-independent, so a replay
	after the command has taken effect is still answered only to an author."""
	require_plan_create_capability(frappe.session.user)


@frappe.whitelist()
def save_strategy_plan_draft(payload=None, expected_version: str | None = None, idempotency_key: str | None = None):
	data = _obj(payload) or {}
	updating = bool(data.get("plan_id"))
	key, token = require_command_inputs(idempotency_key, expected_version, version_required=updating)
	return run_idempotent(
		key,
		"Strategic Plan",
		str(data.get("plan_id") or "new"),
		"save_strategy_plan_draft",
		lambda: writes.save_strategy_plan_draft(data, expected_version=token),
		payload={"payload": data, "expected_version": token},
		authorise=_authorise_author,
	)


@frappe.whitelist()
def create_strategy_successor_version(plan_id: str, idempotency_key: str | None = None):
	key, _token = require_command_inputs(idempotency_key)
	return run_idempotent(
		key,
		"Strategic Plan",
		plan_id,
		"create_strategy_successor_version",
		lambda: writes.create_strategy_successor_version(plan_id),
		payload={"plan_id": plan_id},
		authorise=_authorise_author,
	)


@frappe.whitelist()
def save_strategy_structure_draft(
	plan_version_id: str,
	nodes=None,
	indicators=None,
	targets=None,
	deletes=None,
	expected_version: str | None = None,
	idempotency_key: str | None = None,
):
	key, token = require_command_inputs(idempotency_key, expected_version, version_required=True)
	change_set = {
		"nodes": _obj(nodes) or [],
		"indicators": _obj(indicators) or [],
		"targets": _obj(targets) or [],
		"deletes": _obj(deletes) or [],
	}
	return run_idempotent(
		key,
		"Strategic Plan Version",
		plan_version_id,
		"save_strategy_structure_draft",
		lambda: writes.save_strategy_structure_draft(plan_version_id, **change_set, expected_version=token),
		payload={"plan_version_id": plan_version_id, **change_set, "expected_version": token},
		authorise=_authorise_author,
	)


@frappe.whitelist()
def discard_strategy_plan_draft(
	plan_version_id: str,
	expected_version: str | None = None,
	idempotency_key: str | None = None,
):
	"""discard_strategy_plan_draft — Strategy Author only, Draft and never
	submitted only. Permanently removes the version (and, for a plan's only
	version, the plan itself)."""
	key, token = require_command_inputs(idempotency_key, expected_version, version_required=True)
	return run_idempotent(
		key,
		"Strategic Plan Version",
		plan_version_id,
		"discard_strategy_plan_draft",
		lambda: writes.discard_strategy_plan_draft(plan_version_id, expected_version=token),
		payload={"plan_version_id": plan_version_id, "expected_version": token},
		authorise=_authorise_author,
	)


def _transition(action: str, command: str, plan_version_id: str, expected_version, correlation_id, idempotency_key, *, reason: str | None = None) -> dict:
	key, token = require_command_inputs(idempotency_key, expected_version, version_required=True)
	return run_idempotent(
		key,
		"Strategic Plan Version",
		plan_version_id,
		command,
		lambda: transitions.transition_plan_version(
			plan_version_id,
			action,
			reason=reason,
			expected_version=token,
			correlation_id=correlation_id or key,
		),
		payload={"plan_version_id": plan_version_id, "reason": reason, "expected_version": token, "correlation_id": correlation_id or None},
		authorise=lambda: transitions.authorise_action(plan_version_id, action),
	)


@frappe.whitelist()
def submit_strategy_version(
	plan_version_id: str,
	expected_version: str | None = None,
	correlation_id: str | None = None,
	idempotency_key: str | None = None,
):
	return _transition("Submit for approval", "submit_strategy_version", plan_version_id, expected_version, correlation_id, idempotency_key)


@frappe.whitelist()
def return_strategy_version(
	plan_version_id: str,
	reason: str,
	expected_version: str | None = None,
	correlation_id: str | None = None,
	idempotency_key: str | None = None,
):
	"""§8 return_strategy_version — Strategy Approver only, Submitted for
	approval only. Requires a 10-500 character correction reason."""
	return _transition("Return", "return_strategy_version", plan_version_id, expected_version, correlation_id, idempotency_key, reason=reason)


@frappe.whitelist()
def approve_strategy_version(
	plan_version_id: str,
	expected_version: str | None = None,
	correlation_id: str | None = None,
	idempotency_key: str | None = None,
):
	"""§8 approve_strategy_version — Strategy Approver only, Submitted for
	approval only. Revalidates readiness, immediate applicability and
	overlap and activates the version, atomically superseding the plan's
	previous Active version in the same transaction."""
	return _transition("Approve", "approve_strategy_version", plan_version_id, expected_version, correlation_id, idempotency_key)
