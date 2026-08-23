# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §6.1 plan-version lifecycle — table-driven, modeled on
kentender_core.services.reference_data_transitions.py's pattern (CFG-CHG-002).

Governs Strategic Plan Version only. Strategy Node/Performance Indicator/
Performance Target inherit their plan version's status (§6.1: "There is no
separate lifecycle for hierarchy, indicator or target records") and are
gated directly by strategy_domain_guards._assert_version_editable, not by
anything in this module.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_strategy.services.strategy_audit import record_event
from kentender_strategy.services.strategy_authorization import (
	CAP_APPROVE,
	CAP_AUTHOR,
	CAP_REVIEW,
	has_plan_version_capability,
	require_plan_version_capability,
)
from kentender_strategy.services.strategy_readiness import assert_version_ready_for_submit

# (status, action) -> (next_status, capability). Matches the 9-row §6.1 table
# exactly except "Activate successor" (system-driven, inside _activate below,
# not a user-invoked action key).
TRANSITIONS: dict[tuple[str, str], tuple[str, str]] = {
	("Draft", "Submit for review"): ("In Review", CAP_AUTHOR),
	("Returned", "Revise"): ("Draft", CAP_AUTHOR),
	("In Review", "Return"): ("Returned", CAP_REVIEW),
	("In Review", "Recommend for approval"): ("Awaiting Approval", CAP_REVIEW),
	("Awaiting Approval", "Return"): ("Returned", CAP_APPROVE),
	("Awaiting Approval", "Approve"): ("Approved", CAP_APPROVE),
	("Approved", "Activate"): ("Active", CAP_APPROVE),
	("Superseded", "Archive"): ("Archived", CAP_APPROVE),
}

# status -> [(action, capability), ...] — the same table, read the other way,
# for server-computed available_actions (AGENTS.md §5: "server-computed
# action order is part of the contract").
_ACTIONS_BY_STATUS: dict[str, list[tuple[str, str]]] = {}
for (_status, _action), (_next, _cap) in TRANSITIONS.items():
	_ACTIONS_BY_STATUS.setdefault(_status, []).append((_action, _cap))

RETURN_REASON_MIN = 10
RETURN_REASON_MAX = 500


def _check_expected_version(doc, expected_version: str | None) -> None:
	"""BR-016 optimistic concurrency, using `modified` as the version token —
	same mechanism as reference_data_transitions.py."""
	if expected_version is None:
		return
	if str(doc.modified) != str(expected_version):
		frappe.throw(
			_("This plan version has changed since it was loaded."),
			frappe.ValidationError,
			title="STRATEGY_STALE_WRITE",
		)


def available_actions(version, user: str | None = None) -> list[str]:
	if isinstance(version, str):
		version = frappe.get_doc("Strategic Plan Version", version)
	user = user or frappe.session.user
	return [
		action
		for action, capability in _ACTIONS_BY_STATUS.get(version.status, [])
		if has_plan_version_capability(user, capability, version)
	]


def _version_payload(doc) -> dict:
	return {
		"name": doc.name,
		"plan_version_id": doc.plan_version_id,
		"plan_id": doc.plan_id,
		"status": doc.status,
		"expected_version": str(doc.modified),
		"allowed_actions": available_actions(doc),
	}


def _overlaps(start_a, end_a, start_b, end_b) -> bool:
	if not start_a or not end_a or not start_b or not end_b:
		return False
	return (
		frappe.utils.getdate(start_a) <= frappe.utils.getdate(end_b)
		and frappe.utils.getdate(start_b) <= frappe.utils.getdate(end_a)
	)


def _assert_no_primary_overlap(doc) -> None:
	"""STR-BR-004: two Primary plans for the same PE/OU shall not both be
	Active for overlapping dates."""
	plan = frappe.get_doc("Strategic Plan", doc.plan_id)
	if plan.plan_role != "Primary":
		return
	other_plans = frappe.get_all(
		"Strategic Plan",
		filters={
			"procuring_entity_id": plan.procuring_entity_id,
			"plan_role": "Primary",
			"name": ["!=", plan.name],
		},
		fields=["name", "owner_org_unit_id"],
	)
	for other_plan in other_plans:
		# PE-wide (no OU) and a specific-OU plan are treated as non-overlapping
		# scopes unless both are PE-wide or both name the same OU.
		if (plan.owner_org_unit_id or other_plan.owner_org_unit_id) and (
			plan.owner_org_unit_id != other_plan.owner_org_unit_id
		):
			continue
		active_versions = frappe.get_all(
			"Strategic Plan Version",
			filters={"plan_id": other_plan.name, "status": "Active"},
			fields=["name", "effective_from", "effective_to"],
		)
		for v in active_versions:
			if _overlaps(doc.effective_from, doc.effective_to, v.effective_from, v.effective_to):
				frappe.throw(
					_("Activation would create overlapping Active Primary authority"),
					frappe.ValidationError,
					title="STRATEGY_OVERLAP",
				)


def _activate(doc) -> None:
	"""Revalidates and atomically activates: supersedes the plan's own
	previous Active version (successor case) and rejects cross-plan Primary
	overlap (STR-BR-004), inside the request's own DB transaction."""
	_assert_no_primary_overlap(doc)

	current_active = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": doc.plan_id, "status": "Active", "name": ["!=", doc.name]},
		pluck="name",
	)
	for name in current_active:
		other = frappe.get_doc("Strategic Plan Version", name)
		other.status = "Superseded"
		other.save(ignore_permissions=True)
		record_event(
			entity_type="Strategic Plan Version",
			entity_name=other.name,
			event_type="Activate successor",
			prior_state="Active",
			new_state="Superseded",
			plan_version=other.name,
			summary=f"Superseded by {doc.name}",
		)

	doc.status = "Active"
	doc.save(ignore_permissions=True)


def transition_plan_version(
	plan_version_id: str,
	action: str,
	*,
	reason: str | None = None,
	expected_version: str | None = None,
	correlation_id: str | None = None,
) -> dict:
	doc = frappe.get_doc("Strategic Plan Version", plan_version_id)
	_check_expected_version(doc, expected_version)

	key = (doc.status, action)
	if key not in TRANSITIONS:
		frappe.throw(
			_("Invalid transition: {0} / {1}").format(doc.status, action),
			frappe.ValidationError,
			title="STRATEGY_INVALID_STATE",
		)
	next_status, capability = TRANSITIONS[key]

	require_plan_version_capability(
		frappe.session.user, capability, doc, correlation_id=correlation_id or ""
	)

	if action == "Submit for review":
		assert_version_ready_for_submit(doc.name)

	if action == "Return":
		reason = (reason or "").strip()
		if not (RETURN_REASON_MIN <= len(reason) <= RETURN_REASON_MAX):
			frappe.throw(
				_("Return reason must be {0}-{1} characters").format(RETURN_REASON_MIN, RETURN_REASON_MAX),
				frappe.ValidationError,
				title="STRATEGY_NOT_READY",
			)
		doc.return_reason = reason

	prior_status = doc.status
	if action == "Activate":
		_activate(doc)
	else:
		doc.status = next_status
		if action == "Revise":
			doc.return_reason = ""
		doc.save(ignore_permissions=True)

	record_event(
		entity_type="Strategic Plan Version",
		entity_name=doc.name,
		event_type=action,
		prior_state=prior_status,
		new_state=doc.status,
		reason=reason,
		plan_version=doc.name,
		correlation_id=correlation_id,
		capability=capability,
	)
	return _version_payload(doc)
