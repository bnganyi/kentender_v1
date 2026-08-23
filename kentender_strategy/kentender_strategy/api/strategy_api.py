# Copyright (c) 2026, KenTender and contributors
"""Thin whitelisted wrappers for Strategy MVP-1 services (REQ §16)."""

from __future__ import annotations

import json

import frappe

from kentender_strategy.services import strategy_contracts as contracts
from kentender_strategy.services import strategy_transitions as transitions
from kentender_strategy.services import strategy_writes as writes
from kentender_strategy.services.strategy_readiness import get_plan_readiness
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles


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


@frappe.whitelist()
def get_strategy_portfolio(procuring_entity: str | None = None):
	return contracts.get_strategy_portfolio(procuring_entity=procuring_entity or None)


@frappe.whitelist()
def list_strategy_plans(
	procuring_entity: str | None = None,
	status: str | None = None,
	plan_type: str | None = None,
	search: str | None = None,
	period: str | None = None,
):
	return contracts.list_strategy_plans(
		procuring_entity=procuring_entity or None,
		status=status or None,
		plan_type=plan_type or None,
		search=search or None,
		period=period or None,
	)


@frappe.whitelist()
def get_strategy_tree(plan_version: str | None = None, plan_code: str | None = None):
	return contracts.get_strategy_tree(plan_version=plan_version or None, plan_code=plan_code or None)


@frappe.whitelist()
def get_plan_overview(plan_version: str | None = None, plan_code: str | None = None):
	return contracts.get_plan_overview(plan_version=plan_version or None, plan_code=plan_code or None)


@frappe.whitelist()
def create_successor_version(plan_version: str):
	return writes.create_successor_version(plan_version)


@frappe.whitelist()
def get_strategy_usage(plan_version: str | None = None, plan_code: str | None = None):
	return contracts.get_strategy_usage(plan_version=plan_version or None, plan_code=plan_code or None)


@frappe.whitelist()
def list_active_targets(procuring_entity: str | None = None, plan_code: str | None = None):
	return contracts.list_active_targets(
		procuring_entity=procuring_entity or None, plan_code=plan_code or None
	)


@frappe.whitelist()
def validate_strategy_reference(reference=None):
	return contracts.validate_strategy_reference(_obj(reference) or {})


@frappe.whitelist()
def get_plan_readiness_api(plan_version: str | None = None, plan_code: str | None = None):
	if not plan_version and plan_code:
		plan_version = frappe.db.get_value(
			"Strategic Plan", {"plan_code": plan_code}, "name", order_by="version_number desc"
		)
	return get_plan_readiness(plan_version)


@frappe.whitelist()
def correct_strategy_reference(doctype: str, name: str, new_code: str, reason: str, plan_version: str | None = None):
	from kentender_strategy.services.strategy_reference import correct_reference

	return correct_reference(doctype, name, new_code, reason, plan_version=plan_version)


@frappe.whitelist()
def update_plan_identity(plan_version: str, payload=None):
	return writes.update_plan_identity(plan_version, _obj(payload) or {})


@frappe.whitelist()
def transition_plan(
	plan_version: str,
	action: str,
	reason: str | None = None,
	expected_version: str | None = None,
	correlation_id: str | None = None,
):
	return transitions.transition_plan_version(
		plan_version,
		action,
		reason=reason or None,
		expected_version=expected_version or None,
		correlation_id=correlation_id or None,
	)


@frappe.whitelist()
def upsert_structure_node(payload=None):
	return writes.upsert_structure_node(_obj(payload) or {})


@frappe.whitelist()
def reorder_structure_nodes(plan_version: str, ordered=None):
	return writes.reorder_structure_nodes(plan_version, _obj(ordered) or [])


@frappe.whitelist()
def delete_structure_node(node_type: str, name: str):
	return writes.delete_structure_node(node_type, name)


@frappe.whitelist()
def list_audit_events(plan_version: str | None = None, plan_code: str | None = None):
	return contracts.list_audit_events(plan_version=plan_version or None, plan_code=plan_code or None)


@frappe.whitelist()
def ensure_roles():
	ensure_strategy_roles()
	return {"ok": True}
