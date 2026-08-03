# Copyright (c) 2026, KenTender and contributors
"""REQ §11 state transitions (server authoritative)."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_strategy.services.strategy_audit import record_event
from kentender_strategy.services.strategy_permissions import (
	can_approve_plan,
	can_review_plan,
	can_submit_measurement,
	can_submit_plan,
	can_verify_measurement,
	require_any_role,
	ROLE_MANAGER,
	ROLE_PERF_OFFICER,
	ROLE_PERF_VERIFIER,
	ROLE_PLANNING,
	ROLE_REVIEWER,
)
from kentender_strategy.services.strategy_readiness import assert_plan_ready_for_submit


PLAN_TRANSITIONS = {
	("Draft", "Submit"): "Submitted",
	("Returned", "Resubmit"): "Submitted",
	("Submitted", "Return for correction"): "Returned",
	("Submitted", "Approve"): "Approved",
	("Approved", "Activate"): "Active",
	("Active", "Supersede"): "Superseded",
	("Active", "Archive"): "Archived",
	("Approved", "Withdraw approval"): "Draft",
}

PVO_TRANSITIONS = {
	("Draft", "Submit"): "Submitted",
	("Submitted", "Return"): "Returned",
	("Returned", "Submit"): "Submitted",
	("Submitted", "Approve"): "Approved",
	("Approved", "Activate"): "Active",
	("Active", "Supersede"): "Superseded",
	("Active", "Retire"): "Retired",
}

MEASUREMENT_TRANSITIONS = {
	("Draft", "Submit"): "Submitted",
	("Returned", "Resubmit"): "Submitted",
	("Submitted", "Return"): "Returned",
	("Submitted", "Verify"): "Verified",
	("Submitted", "Reject"): "Rejected",
}

CA_TRANSITIONS = {
	("Open", "Start"): "In progress",
	("In progress", "Submit completion"): "Submitted for verification",
	("Submitted for verification", "Return"): "In progress",
	("Submitted for verification", "Verify"): "Verified complete",
	("Open", "Cancel"): "Cancelled",
	("In progress", "Cancel"): "Cancelled",
}


def transition_plan(plan_name: str, action: str, reason: str | None = None) -> dict:
	doc = frappe.get_doc("Strategic Plan", plan_name)
	key = (doc.status, action)
	if key not in PLAN_TRANSITIONS:
		frappe.throw(_("Invalid plan transition: {0} / {1}").format(doc.status, action))
	next_status = PLAN_TRANSITIONS[key]

	if action in ("Submit", "Resubmit"):
		if not can_submit_plan():
			frappe.throw(_("Only Strategy Manager may submit plans"), frappe.PermissionError)
		assert_plan_ready_for_submit(plan_name)
		doc.submitted_by = frappe.session.user
		doc.submitted_at = frappe.utils.now_datetime()
		doc.return_reason = ""
	elif action == "Return for correction":
		if not can_review_plan():
			frappe.throw(_("Not permitted to return plans"), frappe.PermissionError)
		if not reason:
			frappe.throw(_("Return reason is required"))
		doc.return_reason = reason
	elif action == "Approve":
		if not can_approve_plan():
			frappe.throw(_("Only Planning Authority may approve"), frappe.PermissionError)
		if doc.submitted_by == frappe.session.user and frappe.session.user != "Administrator":
			frappe.throw(_("Approver must not be the submitter"))
		doc.approved_by = frappe.session.user
		doc.approved_at = frappe.utils.now_datetime()
	elif action == "Activate":
		if not can_approve_plan():
			frappe.throw(_("Only Planning Authority may activate"), frappe.PermissionError)
		_activate_plan(doc)
		next_status = "Active"
	elif action in ("Archive", "Withdraw approval", "Supersede"):
		if not can_approve_plan():
			frappe.throw(_("Only Planning Authority may perform this action"), frappe.PermissionError)
		if action != "Supersede" and not reason:
			frappe.throw(_("Reason is required"))

	prior = doc.status
	if action != "Activate":
		doc.status = next_status
		doc.save(ignore_permissions=True)
	record_event(
		entity_type="Strategic Plan",
		entity_name=doc.name,
		event_type=action,
		prior_state=prior,
		new_state=doc.status,
		reason=reason,
		plan_version=doc.name,
	)
	return {"name": doc.name, "status": doc.status, "plan_code": doc.plan_code}


def _activate_plan(doc) -> None:
	# Atomically supersede other Active version of same plan_code+entity
	others = frappe.get_all(
		"Strategic Plan",
		filters={
			"plan_code": doc.plan_code,
			"procuring_entity": doc.procuring_entity,
			"status": "Active",
			"name": ["!=", doc.name],
		},
		pluck="name",
	)
	for name in others:
		other = frappe.get_doc("Strategic Plan", name)
		other.status = "Superseded"
		other.save(ignore_permissions=True)
		record_event(
			entity_type="Strategic Plan",
			entity_name=other.name,
			event_type="Supersede",
			prior_state="Active",
			new_state="Superseded",
			plan_version=other.name,
			summary=f"Superseded by {doc.name}",
		)
	doc.status = "Active"
	doc.activated_by = frappe.session.user
	doc.activated_at = frappe.utils.now_datetime()
	doc.save(ignore_permissions=True)


def transition_pvo(name: str, action: str, reason: str | None = None) -> dict:
	doc = frappe.get_doc("Public Value Objective", name)
	key = (doc.status, action)
	if key not in PVO_TRANSITIONS:
		frappe.throw(_("Invalid PVO transition: {0} / {1}").format(doc.status, action))
	if action == "Submit":
		require_any_role(ROLE_MANAGER, "System Manager")
	elif action == "Return":
		require_any_role(ROLE_REVIEWER, ROLE_PLANNING, "System Manager")
		if not reason:
			frappe.throw(_("Return reason is required"))
	elif action in ("Approve", "Activate", "Retire", "Supersede"):
		require_any_role(ROLE_PLANNING, "System Manager")
		if action == "Approve" and doc.get("submitted_by") == frappe.session.user:
			pass  # PVO has no submitted_by field; segregation via roles
		if action == "Retire" and not reason:
			frappe.throw(_("Retirement reason is required"))
	prior = doc.status
	doc.status = PVO_TRANSITIONS[key]
	if action == "Activate":
		_activate_pvo(doc)
	else:
		doc.save(ignore_permissions=True)
	record_event(
		entity_type="Public Value Objective",
		entity_name=doc.name,
		event_type=action,
		prior_state=prior,
		new_state=doc.status,
		reason=reason,
	)
	return {"name": doc.name, "status": doc.status, "objective_code": doc.objective_code}


def _activate_pvo(doc) -> None:
	filters = {"objective_code": doc.objective_code, "status": "Active", "name": ["!=", doc.name]}
	if doc.procuring_entity:
		filters["procuring_entity"] = doc.procuring_entity
	for name in frappe.get_all("Public Value Objective", filters=filters, pluck="name"):
		other = frappe.get_doc("Public Value Objective", name)
		other.status = "Superseded"
		other.save(ignore_permissions=True)
	doc.status = "Active"
	doc.save(ignore_permissions=True)


def transition_measurement(
	name: str,
	action: str,
	reason: str | None = None,
	authorised_exception: bool | int | str | None = None,
	exception_reason: str | None = None,
) -> dict:
	from kentender_strategy.services.strategy_measurement import derive_measurement_result

	doc = frappe.get_doc("Performance Measurement", name)
	key = (doc.workflow_status, action)
	if key not in MEASUREMENT_TRANSITIONS:
		frappe.throw(_("Invalid measurement transition: {0} / {1}").format(doc.workflow_status, action))
	if action in ("Submit", "Resubmit"):
		if not can_submit_measurement():
			frappe.throw(_("Only Performance Officer may submit"), frappe.PermissionError)
		derive_measurement_result(doc)
		doc.submitted_by = frappe.session.user
		doc.submitted_at = frappe.utils.now_datetime()
	elif action in ("Return", "Verify", "Reject"):
		if not can_verify_measurement():
			frappe.throw(_("Only Performance Verifier may decide"), frappe.PermissionError)
		if doc.submitted_by == frappe.session.user and frappe.session.user != "Administrator":
			frappe.throw(_("Verifier must not be the submitter"), frappe.PermissionError)
		if action in ("Return", "Reject") and not reason:
			frappe.throw(_("Reason is required"))
		doc.verification_comment = reason or doc.verification_comment
		if action == "Verify":
			doc.verified_by = frappe.session.user
			doc.verified_at = frappe.utils.now_datetime()
			derive_measurement_result(doc)
			exc_flag = _as_bool(authorised_exception)
			exc_reason = (exception_reason or "").strip()
			if doc.result_status == "Off track":
				if exc_flag:
					if not exc_reason:
						frappe.throw(_("Exception reason is required for an authorised exception"))
					doc.authorised_exception = 1
					doc.exception_reason = exc_reason
				else:
					doc.authorised_exception = 0
					doc.exception_reason = None
					_ensure_corrective_or_exception(doc)
			else:
				doc.authorised_exception = 0
				doc.exception_reason = None
	prior = doc.workflow_status
	doc.workflow_status = MEASUREMENT_TRANSITIONS[key]
	doc.save(ignore_permissions=True)
	record_event(
		entity_type="Performance Measurement",
		entity_name=doc.name,
		event_type=action,
		prior_state=prior,
		new_state=doc.workflow_status,
		reason=reason,
		plan_version=doc.plan_version,
	)
	return {"name": doc.name, "workflow_status": doc.workflow_status, "result_status": doc.result_status}


def _as_bool(value) -> bool:
	if value in (True, 1, "1", "true", "True", "yes", "Yes"):
		return True
	return False


def _ensure_corrective_or_exception(doc) -> None:
	existing = frappe.db.exists(
		"Strategy Corrective Action",
		{"performance_measurement": doc.name, "status": ["not in", ["Cancelled"]]},
	)
	if existing:
		return
	# Auto-open corrective action shell when verifying Off track without authorised exception
	frappe.get_doc(
		{
			"doctype": "Strategy Corrective Action",
			"performance_measurement": doc.name,
			"performance_target": doc.performance_target,
			"plan_version": doc.plan_version,
			"action": "Address verified underperformance",
			"owner": doc.submitted_by or frappe.session.user,
			"due_date": frappe.utils.add_days(frappe.utils.today(), 30),
			"expected_result": "Return to On track performance",
			"status": "Open",
		}
	).insert(ignore_permissions=True)


def transition_corrective_action(name: str, action: str, reason: str | None = None) -> dict:
	doc = frappe.get_doc("Strategy Corrective Action", name)
	key = (doc.status, action)
	if key not in CA_TRANSITIONS:
		frappe.throw(_("Invalid corrective-action transition: {0} / {1}").format(doc.status, action))
	if action == "Cancel":
		require_any_role(ROLE_PLANNING, "System Manager")
		if not reason:
			frappe.throw(_("Cancellation reason is required"))
		doc.cancellation_reason = reason
		doc.cancelled_by = frappe.session.user
	elif action == "Verify":
		if not can_verify_measurement():
			frappe.throw(_("Only Performance Verifier may verify actions"), frappe.PermissionError)
		doc.verified_by = frappe.session.user
		doc.verified_at = frappe.utils.now_datetime()
	elif action in ("Start", "Submit completion"):
		require_any_role(ROLE_PERF_OFFICER, ROLE_MANAGER, "System Manager")
		if action == "Submit completion" and not doc.completion_evidence:
			frappe.throw(_("Completion evidence is required"))
	prior = doc.status
	doc.status = CA_TRANSITIONS[key]
	doc.save(ignore_permissions=True)
	record_event(
		entity_type="Strategy Corrective Action",
		entity_name=doc.name,
		event_type=action,
		prior_state=prior,
		new_state=doc.status,
		reason=reason,
		plan_version=doc.plan_version,
	)
	return {"name": doc.name, "status": doc.status}
