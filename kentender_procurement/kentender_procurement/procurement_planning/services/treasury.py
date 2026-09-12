# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.2.2 / §5.5.2.3 / §7.2 — Treasury submission
evidence and the withdrawal-for-correction recovery route (plan D8,
PLN18-209).

Transmission to Treasury is external in this MVP: the Accounting Officer
records evidence of what was submitted, never a second approval. Evidence is
append-only — a correction supersedes rather than overwrites. Withdrawal
requires confirmed non-publication (no acknowledgement, no outstanding
attempt) and travels through the same statutory-capacity governance task
machinery §6/§7.2 already uses, so it inherits capacity resolution,
segregation and the decision journal rather than inventing a parallel
approval shape.
"""

from __future__ import annotations

from typing import Any

import json

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, plan_governance, publication_pipeline, references
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_ACCOUNTING_OFFICER, ROLE_PLAN_STATUTORY_APPROVER


def _approved_version(plan_version: str):
	version = envelope.locked("Annual Plan Version", plan_version)
	if not frappe.db.exists("Approved Plan Snapshot", {"plan_version": version.name}):
		fail("PLN_REVIEW_STALE", "Only an approved Plan Version takes Treasury submission evidence.")
	return version


def record_treasury_submission(
	*, plan_version: str, submitted_at, channel: str, destination: str, dispatch_reference: str,
	exact_document_confirmed, supporting_attachment: str = "", idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	"""§7.2 `RecordTreasurySubmission` — appends the first (or a fresh)
	Current evidence row for the exact approved Version; releases the
	`Approved — awaiting Treasury submission evidence` prerequisite."""
	actor = authz.actor(user)
	payload = {"plan_version": plan_version, "submitted_at": cstr(submitted_at), "channel": channel, "destination": destination, "dispatch_reference": dispatch_reference}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (exact_document_confirmed in (True, 1, "1", "true", "True")):
		fail("PLN_ENTRY_INCOMPLETE", "Confirm this is the exact document submitted to Treasury.", {"field": "exact_document_confirmed"})
	for field, value in (("channel", channel), ("destination", destination), ("dispatch_reference", dispatch_reference)):
		if not cstr(value).strip():
			fail("PLN_ENTRY_INCOMPLETE", detail={"field": field})
	version = _approved_version(plan_version)
	assignment = authz.require_site_role(ROLE_ACCOUNTING_OFFICER, actor)
	if frappe.db.exists("Treasury Submission Evidence", {"plan_version": version.name, "evidence_state": "Current"}):
		fail("PLN_ENTRY_INCOMPLETE", "Current Treasury submission evidence already exists; correct it instead of recording another.")
	snapshot = frappe.db.get_value("Approved Plan Snapshot", {"plan_version": version.name}, "content_digest")
	evidence = frappe.get_doc(
		{
			"doctype": "Treasury Submission Evidence", "plan_version": version.name, "document_hash": cstr(snapshot),
			"submitted_at": submitted_at, "channel": channel, "destination": destination, "dispatch_reference": dispatch_reference,
			"supporting_attachment": supporting_attachment or None, "exact_document_confirmed": 1, "actor": actor,
			"authority_snapshot": authz.authority_snapshot(assignment), "recorded_at": now_datetime(), "evidence_state": "Current",
			"fixture_namespace": cstr(version.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	result = {"ok": True, "idempotent": False, "action": "treasury_submission_recorded", "evidence": evidence.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RecordTreasurySubmission", payload=payload, result=result,
		document_type="Treasury Submission Evidence", document_name=evidence.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
	)
	return result


def correct_treasury_submission_evidence(*, prior_evidence: str, reason: str, idempotency_key: str, user: str | None = None, **new_fields) -> dict[str, Any]:
	"""§7.2 `CorrectTreasurySubmissionEvidence` — append a superseding record
	with a reason; the prior record is preserved, never overwritten. Any
	outstanding in-flight publication attempt is held pending reconciliation
	against the corrected evidence."""
	actor = authz.actor(user)
	reason = " ".join(cstr(reason).split())
	payload = {"prior_evidence": prior_evidence, "reason": reason, **{k: cstr(v) for k, v in new_fields.items()}}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (10 <= len(reason) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "State the reason for the correction (10–500 characters).", {"field": "reason"})
	if not prior_evidence or not frappe.db.exists("Treasury Submission Evidence", prior_evidence):
		authz.not_found()
	prior = frappe.get_doc("Treasury Submission Evidence", prior_evidence)
	if prior.evidence_state != "Current":
		fail("PLN_REVIEW_STALE", "Only the current evidence record can be corrected.")
	version = envelope.locked("Annual Plan Version", prior.plan_version)
	assignment = authz.require_site_role(ROLE_ACCOUNTING_OFFICER, actor)
	for field in ("submitted_at", "channel", "destination", "dispatch_reference"):
		if field not in new_fields or not cstr(new_fields.get(field)).strip():
			fail("PLN_ENTRY_INCOMPLETE", detail={"field": field})
	corrected = frappe.get_doc(
		{
			"doctype": "Treasury Submission Evidence", "plan_version": version.name, "document_hash": prior.document_hash,
			"submitted_at": new_fields["submitted_at"], "channel": new_fields["channel"], "destination": new_fields["destination"],
			"dispatch_reference": new_fields["dispatch_reference"], "supporting_attachment": new_fields.get("supporting_attachment") or None,
			"exact_document_confirmed": 1, "actor": actor, "authority_snapshot": authz.authority_snapshot(assignment), "recorded_at": now_datetime(),
			"evidence_state": "Current", "correction_reason": reason, "fixture_namespace": cstr(version.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value("Treasury Submission Evidence", prior.name, {"evidence_state": "Superseded", "superseded_by": corrected.name}, update_modified=False)
	held = None
	publication_name = frappe.db.get_value("Plan Publication", {"plan_version": version.name}, "name")
	if publication_name and frappe.db.get_value("Publication Attempt", {"publication": publication_name, "result": ("in", ("Pending", "Indeterminate"))}, "name"):
		held = publication_pipeline.hold_plan_publication(
			plan_version=version.name, reason=f"Treasury submission evidence corrected: {reason}",
			hold_kind="Accounting Officer correction request", idempotency_key=f"{idempotency_key}:hold", user=actor,
		)["hold"]
	result = {"ok": True, "idempotent": False, "action": "treasury_evidence_corrected", "evidence": corrected.name, "supersedes": prior.name, "hold": held}
	envelope.record_command(
		idempotency_key=idempotency_key, command="CorrectTreasurySubmissionEvidence", payload=payload, result=result,
		document_type="Treasury Submission Evidence", document_name=corrected.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
	)
	return result


def _confirmed_unpublished(version) -> bool:
	publication_name = frappe.db.get_value("Plan Publication", {"plan_version": version.name}, "name")
	if not publication_name:
		return True
	if frappe.db.exists("Publication Acknowledgement", {"publication": publication_name, "matched": 1}):
		return False
	if frappe.db.exists("Publication Attempt", {"publication": publication_name, "result": ("in", ("Pending", "Indeterminate"))}):
		return False
	return True


def request_plan_withdrawal(*, plan_version: str, reason: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `RequestPlanWithdrawal` — the Accounting Officer's request to the
	configured statutory authority; requires confirmed-unpublished content
	and no outstanding transmission. Content stays locked throughout."""
	actor = authz.actor(user)
	reason = " ".join(cstr(reason).split())
	payload = {"plan_version": plan_version, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (10 <= len(reason) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "State the reason for the withdrawal request (10–500 characters).", {"field": "reason"})
	version = envelope.locked("Annual Plan Version", plan_version)
	assignment = authz.require_site_role(ROLE_ACCOUNTING_OFFICER, actor)
	if version.version_status not in ("Approved — publication pending", "Publication failed"):
		fail("PLN_WITHDRAWAL_NOT_PERMITTED")
	if not _confirmed_unpublished(version):
		fail("PLN_WITHDRAWAL_NOT_PERMITTED")
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	hold = publication_pipeline.hold_plan_publication(
		plan_version=version.name, reason=reason, hold_kind="Withdrawal request", idempotency_key=f"{idempotency_key}:hold", user=actor,
	)["hold"]
	capacity = plan_governance.capacity_for_site()
	task = frappe.get_doc(
		{
			"doctype": "Plan Governance Task", "task_reference": f"SAT-WD-{version.name}",
			"annual_plan": plan.name, "plan_version": version.name, "stage": "Statutory approval", "capacity": capacity,
			"status": "Open", "task_token": envelope.token(), "record_version": 0, "fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	result = {"ok": True, "idempotent": False, "action": "withdrawal_requested", "hold": hold, "task": task.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RequestPlanWithdrawal", payload=payload, result=result,
		document_type="Plan Governance Task", document_name=task.name, actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def withdraw_approved_plan_for_correction(*, task: str, task_token: str, collective_resolution_reference: str = "", idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `WithdrawApprovedPlanForCorrection` — the configured statutory
	authority confirms the content is still unpublished with no outstanding
	transmission, then preserves the approved evidence as **Withdrawn for
	correction** and creates one copied Draft correction."""
	actor = authz.actor(user)
	payload = {"task": task, "collective_resolution_reference": cstr(collective_resolution_reference).strip()}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not task or not frappe.db.exists("Plan Governance Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Plan Governance Task", task)
	if task_doc.stage != "Statutory approval" or task_doc.status != "Open":
		fail("PLN_REVIEW_STALE")
	assignment = authz.require_site_role(ROLE_PLAN_STATUTORY_APPROVER, actor)
	envelope.assert_task_token(task_doc, task_token)
	resolution_reference = cstr(collective_resolution_reference).strip()
	if plan_governance.is_collective_capacity(task_doc.capacity) and not resolution_reference:
		fail("PLN_COLLECTIVE_RESOLUTION_REQUIRED", detail={"field": "collective_resolution_reference"})
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	if version.version_status not in ("Approved — publication pending", "Publication failed"):
		fail("PLN_WITHDRAWAL_NOT_PERMITTED")
	hold_name = publication_pipeline._active_hold(version.name)
	if not hold_name or frappe.db.get_value("Plan Publication Hold", hold_name, "hold_kind") != "Withdrawal request":
		fail("PLN_WITHDRAWAL_NOT_PERMITTED", "No valid Accounting Officer withdrawal request is open for this Plan Version.")
	if not _confirmed_unpublished(version):
		fail("PLN_WITHDRAWAL_NOT_PERMITTED")
	plan = envelope.locked("Annual Plan", version.annual_plan)

	decision = frappe.get_doc(
		{
			"doctype": "Plan Governance Decision", "decision_reference": f"APP-WD-{version.name}",
			"task": task_doc.name, "plan_version": version.name, "stage": task_doc.stage, "decision": "Withdraw for correction",
			"capacity": task_doc.capacity, "collective_resolution_reference": resolution_reference or None, "actor": actor,
			"authority_snapshot": authz.authority_snapshot(assignment), "decided_at": now_datetime(), "command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task_doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, version_status="Withdrawn for correction")
	frappe.db.set_value("Plan Publication Hold", hold_name, {"hold_state": "Released", "released_at": now_datetime(), "withdrawal_decision": decision.name, "reconciliation_outcome": "Confirmed unpublished"}, update_modified=False)

	number = plan_governance._next_plan_version_number(plan.name)
	correction = frappe.get_doc(
		{
			"doctype": "Annual Plan Version", "version_reference": f"{plan.plan_reference}-V{number}", "annual_plan": plan.name,
			"version_number": number, "based_on_version": version.based_on_version or None, "correction_of_plan_version": version.name,
			"version_status": "Draft", "funding_state": "Confirmed" if version.funding_state == "Confirmed" else "Not requested",
			"funding_line_totals_hash": version.funding_line_totals_hash if version.funding_state == "Confirmed" else None,
			"source_cohort": version.source_cohort or json.dumps(plan_governance.source_cohort(version.name)),
			"project_name": version.project_name, "record_version": 0, "fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	plan_governance._copy_version_content(version.name, correction, cstr(plan.fixture_namespace))
	frappe.db.set_value("Annual Plan", plan.name, "open_successor_version", correction.name, update_modified=False)

	result = {"ok": True, "idempotent": False, "action": "withdrawn_for_correction", "correction_version": correction.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="WithdrawApprovedPlanForCorrection", payload=payload, result=result,
		document_type="Plan Governance Decision", document_name=decision.name, actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result
