# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.5 §6.1 plan-version lifecycle — table-driven, modeled on
kentender_core.services.reference_data_transitions.py's pattern (CFG-CHG-002).

Governs Strategic Plan Version only. Strategy Node/Performance Indicator/
Performance Target inherit their plan version's status (§6.1: "There is no
separate lifecycle for hierarchy, indicator or target records") and are
gated directly by strategy_domain_guards._assert_version_editable, not by
anything in this module.

v1.5 collapses the previous 8-status/9-transition table onto 4 statuses and
3 user-invoked actions: Submit for approval, Return and Approve. Approve
both activates the submitted version and (inside the same transaction,
still driven off "Approve" rather than a separate user action) supersedes
the plan's previous Active version — see `_activate` below.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_strategy.services.strategy_audit import record_event
from kentender_strategy.services.strategy_authorization import (
	CAP_APPROVE,
	CAP_AUTHOR,
	assignment_id,
	business_role_for_capability,
	has_plan_version_capability,
	require_plan_version_capability,
)
from kentender_strategy.services.strategy_domain_guards import assert_no_primary_overlap
from kentender_strategy.services.strategy_readiness import (
	assert_version_ready_for_approval,
	assert_version_ready_for_submit,
)
from kentender_strategy.services.strategy_reference import resolve_version_name

# (status, action) -> (next_status, capability). Matches the 4-row §6.1
# table exactly: Activate/supersede-previous-Active happens inside the
# "Approve" branch of transition_plan_version below (§6.1's own 4th row is
# system-driven "as part of the successor approval transaction", not a
# separate user-invoked action key).
TRANSITIONS: dict[tuple[str, str], tuple[str, str]] = {
	("Draft", "Submit for approval"): ("Submitted for approval", CAP_AUTHOR),
	("Submitted for approval", "Return"): ("Draft", CAP_APPROVE),
	("Submitted for approval", "Approve"): ("Active", CAP_APPROVE),
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
		version = frappe.get_doc("Strategic Plan Version", resolve_version_name(version) or version)
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
		"plan_reference": frappe.db.get_value("Strategic Plan", doc.plan_id, "plan_id"),
		"version_number": doc.version_number,
		"status": doc.status,
		"effective_from": str(doc.effective_from) if doc.effective_from else None,
		"effective_to": str(doc.effective_to) if doc.effective_to else None,
		"expected_version": str(doc.modified),
		"allowed_actions": available_actions(doc),
	}


def _assert_no_primary_overlap(doc) -> None:
	"""STR-BR-004 — delegated to the domain guard so the same locking check
	runs here (command layer) and in the doctype's own validate (bypass)."""
	assert_no_primary_overlap(doc)


def _activate(doc) -> None:
	"""STR-BR-015: revalidates and atomically activates: supersedes the
	plan's own previous Active version (successor case) and rejects
	cross-plan Primary overlap (STR-BR-004), inside the request's own DB
	transaction. Fires directly off "Approve" (§5.1: "Approval ... activates
	within one transaction") — there is no separate Activate action.

	Predecessor closure (v1.8 plan D8 / STR18-XD-002): the superseded
	version's applicability interval is closed to the day before the
	successor starts when the successor starts after the predecessor did;
	otherwise the predecessor keeps its stored dates. Date semantics are
	whole site dates — a successor effective on day D is current from D and
	the predecessor's last applicable day is D-1."""
	_assert_no_primary_overlap(doc)

	current_active = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": doc.plan_id, "status": "Active", "name": ["!=", doc.name]},
		pluck="name",
	)
	for name in current_active:
		other = frappe.get_doc("Strategic Plan Version", name)
		other.status = "Superseded"
		if (
			doc.effective_from
			and other.effective_from
			and frappe.utils.getdate(doc.effective_from) > frappe.utils.getdate(other.effective_from)
		):
			other.effective_to = frappe.utils.add_days(frappe.utils.getdate(doc.effective_from), -1)
		other.save(ignore_permissions=True)
		record_event(
			entity_type="Strategic Plan Version",
			entity_name=other.name,
			event_type="Approve successor",
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
	doc = frappe.get_doc("Strategic Plan Version", resolve_version_name(plan_version_id) or plan_version_id)
	_check_expected_version(doc, expected_version)

	key = (doc.status, action)
	if key not in TRANSITIONS:
		frappe.throw(
			_("Invalid transition: {0} / {1}").format(doc.status, action),
			frappe.ValidationError,
			title="STRATEGY_INVALID_STATE",
		)
	next_status, capability = TRANSITIONS[key]

	exercised = require_plan_version_capability(
		frappe.session.user, capability, doc, correlation_id=correlation_id or ""
	)

	if action == "Submit for approval":
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
	if action == "Approve":
		# STR-BR-015: readiness, immediate applicability (§5.1) and overlap
		# are revalidated and the version activated atomically — no separate
		# Awaiting Approval/Approved stopover, no scheduled activation.
		assert_version_ready_for_approval(doc)
		_activate(doc)
	else:
		doc.status = next_status
		if action == "Submit for approval":
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
		business_role=business_role_for_capability(capability),
		assignment=assignment_id(exercised),
	)
	return _version_payload(doc)
