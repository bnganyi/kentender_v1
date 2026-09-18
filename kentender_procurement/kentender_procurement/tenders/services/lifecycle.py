# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §5.1 / §7.2 — submission, return, approval and reopen.

Submission rebuilds and reviews the exact projection, requires zero Must
fix findings, freezes the Version (status, package digest, both generated
documents as immutable `Tender Document` rows) and assigns the Head of
Procurement Function (TPR08-AC-030/031). Return preserves the submitted
Version and creates one copied Draft at the affected task (AC-032).
Approval rechecks authority, segregation from the Version's own audit
columns (never a role label — §16(12)), compatibility, the review result
and the package digest, then commits the immutable decision and the
Accounting Officer task; it creates no channel confirmation, sets no
`published_at` and exposes nothing to suppliers (AC-033..035). Reopen is
possible only before publication authorisation (AC-036)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import clock, compatibility, documents, draft_commands, envelope, events, render_service, review, serializer
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import ROLE_ACCOUNTING_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION

TASK_HOPF_APPROVAL = "HOPF approval"
TASK_AO_AUTHORISATION = "AO publication authorisation"
AFFECTED_TASKS = ("Tender details", "Supplier and contract requirements", "Review and generated documents")
AFFECTED_TASK_KEYS = {"Tender details": "details", "Supplier and contract requirements": "requirements", "Review and generated documents": "review"}


# --------------------------------------------------------------------------
# tasks and decisions
# --------------------------------------------------------------------------


def new_task(root, version, *, task_type: str, business_role: str, subject_type: str = "", subject_id: str = "") -> Any:
	return envelope.insert(
		frappe.get_doc(
			{
				"doctype": "Tender Task", "tender": root.name, "tender_version": version.name if version else None, "task_type": task_type, "business_role": business_role,
				"subject_type": subject_type, "subject_id": subject_id, "status": "Open", "task_token": envelope.token(), "record_version": 0, "fixture_namespace": root.fixture_namespace,
			}
		)
	)


def open_task(root, *, task_type: str, subject_id: str = "") -> Any | None:
	filters = {"tender": root.name, "task_type": task_type, "status": "Open"}
	if subject_id:
		filters["subject_id"] = subject_id
	name = frappe.db.get_value("Tender Task", filters, "name")
	return frappe.get_doc("Tender Task", name) if name else None


def complete_task(task, decision_name: str) -> None:
	envelope.bump(task, status="Completed", decision=decision_name)


def cancel_open_tasks(root, *, task_types: tuple[str, ...] = ()) -> int:
	count = 0
	for name in frappe.get_all("Tender Task", filters={"tender": root.name, "status": "Open"}, pluck="name"):
		task = frappe.get_doc("Tender Task", name)
		if task_types and task.task_type not in task_types:
			continue
		envelope.bump(task, status="Cancelled")
		count += 1
	return count


def record_decision(root, version, *, decision: str, actor: str, business_role: str, assignment, idempotency_key: str, reason: str = "", affected_task: str = "", subject_type: str = "", subject_id: str = "") -> Any:
	return envelope.insert(
		frappe.get_doc(
			{
				"doctype": "Tender Decision", "tender": root.name, "tender_version": version.name if version else None, "decision": decision, "subject_type": subject_type,
				"subject_id": subject_id, "actor": actor, "business_role": business_role, "reason": reason, "affected_task": affected_task,
				"authority_snapshot": authz.authority_snapshot(assignment), "decided_at": clock.now(), "command_idempotency_key": idempotency_key, "fixture_namespace": root.fixture_namespace,
			}
		)
	)


def copy_draft(root, source, *, actor: str, predecessor_fields: dict[str, Any] | None = None) -> Any:
	"""A copied Draft successor: same snapshot, officer values and evidence
	rows, next version number, predecessor link (§5.1 rows 3 and 5)."""
	number = int(frappe.db.sql("select coalesce(max(version_number), 0) from `tabTender Version` where tender=%s", root.name)[0][0]) + 1
	draft = frappe.get_doc(
		{
			"doctype": "Tender Version", "tender": root.name, "version_number": number, "status": "Draft", "predecessor_version": source.name,
			"requisition_handoff": source.requisition_handoff, "requisition_version": source.requisition_version, "template_release_id": source.template_release_id,
			"official_source_digest": source.official_source_digest, "bundle_digest": source.bundle_digest, "requisition_snapshot_digest": source.requisition_snapshot_digest,
			"requisition_snapshot_json": source.requisition_snapshot_json, "officer_payload_json": source.officer_payload_json, "prepared_by": actor, "prepared_at": clock.now(),
			"record_version": 0, "fixture_namespace": root.fixture_namespace, **(predecessor_fields or {}),
		}
	)
	for row in sorted(source.get("evidence_requirements") or [], key=lambda r: r.row_order or 0):
		draft.append("evidence_requirements", {"evidence_requirement_id": row.evidence_requirement_id, "label": row.label, "evidence_type": row.evidence_type, "linked_requirement_type": row.linked_requirement_type, "linked_requirement_id": row.linked_requirement_id, "mandatory": row.mandatory, "row_order": row.row_order})
	envelope.insert(draft)
	result = review.run(root, draft, with_renders=True)
	review.store(draft, result)
	envelope.bump(draft)
	return draft


def _freeze_documents(root, version, renders: dict[str, Any]) -> dict[str, str]:
	base = cstr(root.tender_reference).replace("/", "-") + f"-V{int(version.version_number)}"
	return {
		"invitation": documents.store(tender=root.name, tender_version=version.name, kind=documents.KIND_INVITATION, html=renders["invitation_html"], digest_value=renders["invitation_digest"], pdf=renders.get("invitation_pdf"), file_base=f"{base}-invitation", fixture_namespace=root.fixture_namespace),
		"complete_tender": documents.store(tender=root.name, tender_version=version.name, kind=documents.KIND_COMPLETE, html=renders["issued_tender_html"], digest_value=renders["issued_tender_digest"], pdf=renders.get("issued_tender_pdf"), file_base=f"{base}-tender", fixture_namespace=root.fixture_namespace),
	}


# --------------------------------------------------------------------------
# SubmitTenderForApproval
# --------------------------------------------------------------------------


def submit_tender_for_approval(*, tender: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_officer(actor)
	payload = {"tender": tender}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version = draft_commands.load(tender)
	draft_commands.require_editable(root, version)
	envelope.check_record_version(root, expected_record_version)
	snapshot = snap.load(version)
	compatibility.require_supported(snapshot)
	result = review.run(root, version, with_renders=True)
	if result["must_fix_count"]:
		review.store(version, result)
		envelope.bump(version)
		envelope.bump(root)
		fail("TND_MUST_FIX", detail={"findings": [f for f in result["findings"] if f["severity"] == review.MUST_FIX]})
	renders = render_service.render(root, version, snapshot, with_pdf=True)
	with envelope.atomic("submit"):
		review.store(version, result)
		version.invitation_digest = renders["invitation_digest"]
		version.issued_tender_digest = renders["issued_tender_digest"]
		version.package_digest = serializer.package_digest(root, version, snapshot, renders=renders)
		stored = _freeze_documents(root, version, renders)
		envelope.bump(version, status="Submitted", submitted_by=actor, submitted_at=clock.now())
		decision = record_decision(root, version, decision="Submit for approval", actor=actor, business_role="Procurement Officer", assignment=assignment, idempotency_key=idempotency_key)
		task = new_task(root, version, task_type=TASK_HOPF_APPROVAL, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
		envelope.bump(root, overall_status="Awaiting procurement approval", submission_deadline=serializer.officer_state(version).get("submission_deadline"), clarification_deadline=serializer.officer_state(version).get("clarification_deadline"))
		events.emit(
			tender=root.name, event_type="TenderSubmitted", command="SubmitTenderForApproval", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Draft", resulting_status="Awaiting procurement approval", record_version=root.record_version, subject_type="Tender Version", subject_id=version.name,
			payload={"package_digest": version.package_digest, "invitation_digest": version.invitation_digest, "issued_tender_digest": version.issued_tender_digest, "documents": stored, "compatibility": [c.as_dict() for c in compatibility.evaluate(snapshot)], "decision": decision.name, "task": task.name},
			fixture_namespace=root.fixture_namespace,
		)
	out = {"ok": True, "idempotent": False, "action": "submitted", "tender": root.name, "record_version": root.record_version, "version": draft_commands.version_dict(version), "task": task.name, "package_digest": version.package_digest}
	envelope.record_command(idempotency_key=idempotency_key, command="SubmitTenderForApproval", payload=payload, result=out, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return out


# --------------------------------------------------------------------------
# ReturnTenderForCorrection
# --------------------------------------------------------------------------


def return_tender_for_correction(*, tender: str, reason: str, affected_task: str, expected_record_version, idempotency_key: str, user: str | None = None, task: str = "", task_token: str = "") -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_hopf(actor)
	payload = {"tender": tender, "reason": reason, "affected_task": affected_task}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = " ".join(cstr(reason).split())
	if not (3 <= len(reason) <= 1000):
		fail("TND_CONTROL_INVALID", "A plain-language correction comment is required.", {"fields": {"reason": "Enter what must be corrected."}})
	if affected_task not in AFFECTED_TASKS:
		fail("TND_CONTROL_INVALID", "Choose the affected task.", {"fields": {"affected_task": "Choose one of: " + ", ".join(AFFECTED_TASKS) + "."}})
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if version.status != "Submitted" or root.overall_status != "Awaiting procurement approval":
		fail("TND_STALE_VERSION", "This Tender is not awaiting procurement approval.")
	open_approval = open_task(root, task_type=TASK_HOPF_APPROVAL)
	if task and open_approval and open_approval.name != task:
		fail("TND_STALE_VERSION", "This task has already changed. Reload to see the current decision.")
	if task_token and open_approval:
		envelope.assert_task_token(open_approval, task_token)
	with envelope.atomic("return"):
		decision = record_decision(root, version, decision="Return for correction", actor=actor, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, assignment=assignment, idempotency_key=idempotency_key, reason=reason, affected_task=affected_task)
		envelope.bump(version, status="Returned", returned_by=actor, returned_at=clock.now(), return_reason=reason, return_affected_task=affected_task)
		draft = copy_draft(root, version, actor=cstr(version.prepared_by) or actor)
		if open_approval:
			complete_task(open_approval, decision.name)
		envelope.bump(root, overall_status="Draft", current_version=draft.name)
		events.emit(
			tender=root.name, event_type="TenderReturned", command="ReturnTenderForCorrection", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Awaiting procurement approval", resulting_status="Draft", record_version=root.record_version, subject_type="Tender Version", subject_id=version.name, reason=reason,
			payload={"affected_task": affected_task, "copied_draft": draft.name, "decision": decision.name}, fixture_namespace=root.fixture_namespace,
		)
	out = {"ok": True, "idempotent": False, "action": "returned", "tender": root.name, "record_version": root.record_version, "returned_version": version.name, "copied_draft": draft.name, "affected_task": AFFECTED_TASK_KEYS[affected_task]}
	envelope.record_command(idempotency_key=idempotency_key, command="ReturnTenderForCorrection", payload=payload, result=out, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return out


# --------------------------------------------------------------------------
# ApproveTenderPackage
# --------------------------------------------------------------------------


def require_segregation(version, actor: str, *, blocked_columns: tuple[str, ...]) -> None:
	"""§6: the person who prepared or submitted a Version cannot approve it;
	the person who prepared, submitted or approved cannot authorise its
	publication. Decided from the immutable Version columns."""
	for column in blocked_columns:
		if cstr(version.get(column)) == actor:
			fail("TND_SOD_BLOCKED", detail={"conflicting_action": column, "version": version.name})


def approve_tender_package(*, tender: str, expected_record_version, idempotency_key: str, user: str | None = None, task: str = "", task_token: str = "") -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_hopf(actor)
	payload = {"tender": tender}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if version.status != "Submitted" or root.overall_status != "Awaiting procurement approval":
		fail("TND_STALE_VERSION", "This Tender is not awaiting procurement approval.")
	require_segregation(version, actor, blocked_columns=("prepared_by", "submitted_by"))
	open_approval = open_task(root, task_type=TASK_HOPF_APPROVAL)
	if task and open_approval and open_approval.name != task:
		fail("TND_STALE_VERSION", "This task has already changed. Reload to see the current decision.")
	if task_token and open_approval:
		envelope.assert_task_token(open_approval, task_token)
	snapshot = snap.load(version)
	compatibility.require_supported(snapshot)
	submitted_package_digest = cstr(version.package_digest)
	check = review.run(root, version, with_renders=True)
	if check["must_fix_count"]:
		fail("TND_MUST_FIX", detail={"findings": [f for f in check["findings"] if f["severity"] == review.MUST_FIX]})
	if serializer.package_digest(root, version, snapshot) != submitted_package_digest:
		fail("TND_STALE_VERSION", "The submitted package no longer matches its digest.")
	approved_at = clock.now()
	approval = {
		"official_name": cstr(frappe.db.get_value("User", actor, "full_name") or actor), "official_title": ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
		"approved_date": serializer.fmt_date(approved_at), "reference": f"{root.tender_reference}-V{int(version.version_number)}",
	}
	renders = render_service.render(root, version, snapshot, approval=approval, with_pdf=True)
	with envelope.atomic("approve"):
		version.invitation_digest = renders["invitation_digest"]
		version.issued_tender_digest = renders["issued_tender_digest"]
		version.package_digest = serializer.package_digest(root, version, snapshot, renders=renders)
		stored = _freeze_documents(root, version, renders)
		envelope.bump(version, status="Approved", approved_by=actor, approved_at=approved_at)
		decision = record_decision(root, version, decision="Approve Tender package", actor=actor, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, assignment=assignment, idempotency_key=idempotency_key)
		if open_approval:
			complete_task(open_approval, decision.name)
		ao_task = new_task(root, version, task_type=TASK_AO_AUTHORISATION, business_role=ROLE_ACCOUNTING_OFFICER)
		envelope.bump(root, overall_status="Approved", approved_version=version.name)
		events.emit(
			tender=root.name, event_type="TenderApproved", command="ApproveTenderPackage", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Awaiting procurement approval", resulting_status="Approved", record_version=root.record_version, subject_type="Tender Version", subject_id=version.name,
			payload={"submitted_package_digest": submitted_package_digest, "approved_package_digest": version.package_digest, "invitation_digest": version.invitation_digest, "issued_tender_digest": version.issued_tender_digest, "documents": stored, "decision": decision.name, "task": ao_task.name},
			fixture_namespace=root.fixture_namespace,
		)
	out = {"ok": True, "idempotent": False, "action": "approved", "tender": root.name, "record_version": root.record_version, "version": draft_commands.version_dict(version), "task": ao_task.name, "package_digest": version.package_digest}
	envelope.record_command(idempotency_key=idempotency_key, command="ApproveTenderPackage", payload=payload, result=out, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return out


# --------------------------------------------------------------------------
# ReopenApprovedTender
# --------------------------------------------------------------------------


def reopen_approved_tender(*, tender: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_hopf(actor)
	payload = {"tender": tender, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = " ".join(cstr(reason).split())
	if not (3 <= len(reason) <= 1000):
		fail("TND_CONTROL_INVALID", "A reason is required to reopen an approved Tender.", {"fields": {"reason": "Enter the reason."}})
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if root.publication or root.overall_status in ("Publication authorised", "Published — open", "Submission period ended"):
		fail("TND_PUBLICATION_STARTED")
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	if version.status != "Approved" or root.overall_status != "Approved":
		fail("TND_STALE_VERSION", "This Tender is not approved.")
	with envelope.atomic("reopen"):
		decision = record_decision(root, version, decision="Reopen Tender", actor=actor, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, assignment=assignment, idempotency_key=idempotency_key, reason=reason)
		draft = copy_draft(root, version, actor=cstr(version.prepared_by) or actor, predecessor_fields={"reopen_reason": reason})
		cancel_open_tasks(root, task_types=(TASK_AO_AUTHORISATION,))
		envelope.bump(root, overall_status="Draft", current_version=draft.name, approved_version=None)
		events.emit(
			tender=root.name, event_type="TenderReopened", command="ReopenApprovedTender", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Approved", resulting_status="Draft", record_version=root.record_version, subject_type="Tender Version", subject_id=version.name, reason=reason,
			payload={"copied_draft": draft.name, "decision": decision.name}, fixture_namespace=root.fixture_namespace,
		)
	out = {"ok": True, "idempotent": False, "action": "reopened", "tender": root.name, "record_version": root.record_version, "approved_version": version.name, "copied_draft": draft.name}
	envelope.record_command(idempotency_key=idempotency_key, command="ReopenApprovedTender", payload=payload, result=out, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return out
