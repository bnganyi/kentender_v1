# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §10.2–§10.5 — the lifecycle commands. No submitted,
approved or handed-off Version is edited in place: return and reopen copy
a Draft successor; approval commits decision, approved Version, package,
files and handoff together or not at all (§10.5, TPR-AC-025/026/027); the
preparing or submitting officer can never approve the same Version,
checked from the Version's own audit columns (§10.3, TPR-AC-023); an
upstream correction stops the Version and releases the handoff (§10.4)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime, nowdate

from kentender_procurement.tender_preparation.services import controls, envelope, events, evidence, handoff_gateway, readiness, render_service, serializer
from kentender_procurement.tender_preparation.services import snapshot as snap
from kentender_procurement.tender_preparation.services import tender_authorization as authz
from kentender_procurement.tender_preparation.services.errors import fail
from kentender_procurement.tender_preparation.services.tender_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

REASON_MIN, REASON_MAX = 10, 1000


def _reason(reason: str) -> str:
	text = " ".join(cstr(reason).split())
	if not (REASON_MIN <= len(text) <= REASON_MAX):
		fail("TPR_CONTROL_INVALID", f"A reason of {REASON_MIN}–{REASON_MAX} characters is required.")
	return text


def _decision(*, task, root, version, actor: str, capacity: str, decision: str, reason: str, resulting_state: str, assignment, idempotency_key: str):
	return frappe.get_doc(
		{
			"doctype": "Tender Preparation Decision", "task": task.name if task is not None else None, "tender": root.name, "tender_version": version.name,
			"actor": actor, "legal_capacity": capacity, "decision": decision, "reason": reason, "resulting_state": resulting_state,
			"authority_snapshot": authz.authority_snapshot(assignment), "decided_at": now_datetime(), "command_idempotency_key": idempotency_key,
		}
	).insert(ignore_permissions=True)


def _copy_draft_successor(root, source_version, *, actor: str | None = None):
	"""A Draft copy of a returned/reopened Version: same immutable snapshot,
	same officer values and additional evidence rows, next version number."""
	snapshot = snap.load(source_version)
	values = {field: source_version.get(field) for field in controls.CATALOGUE}
	successor = frappe.get_doc(
		{
			"doctype": "Tender Preparation Version", "tender": root.name, "version_number": int(source_version.version_number) + 1,
			"based_on_version": source_version.name, "version_status": "Draft",
			"snapshot_json": source_version.snapshot_json, "snapshot_digest": source_version.snapshot_digest,
			"prepared_by": None, "record_version": 0, **values,
		}
	)
	for row in evidence.rows_as_dicts(source_version):
		if row["source"] == evidence.SOURCE_ADDITIONAL:
			successor.append("evidence_requirements", {k: v for k, v in row.items()})
	evidence.rebuild(successor, snapshot)
	successor.insert(ignore_permissions=True)
	successor.content_digest = serializer.content_digest(root, successor, snapshot)
	successor.save(ignore_permissions=True)
	return successor


def _cancel_open_tasks(root) -> None:
	for name in frappe.get_all("Tender Preparation Task", filters={"tender": root.name, "status": "Open"}, pluck="name"):
		task = frappe.get_doc("Tender Preparation Task", name)
		envelope.bump(task, status="Cancelled")


# --------------------------------------------------------------------------
# SubmitTenderForApproval
# --------------------------------------------------------------------------


def submit_tender_for_approval(*, tender: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"tender": tender}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	authz.require_officer(actor)
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = envelope.locked("Prepared Tender", tender)
	version = envelope.locked("Tender Preparation Version", root.current_version)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state != "Draft" or version.version_status != "Draft":
		fail("TPR_STALE_VERSION")
	snapshot = snap.load(version)
	evidence.rebuild(version, snapshot)
	version.content_digest = serializer.content_digest(root, version, snapshot)
	run = readiness.run(root, version)
	readiness.store(version, run)
	if run["blocking_count"]:
		envelope.bump(version)
		envelope.bump(root)
		fail("TPR_BLOCKING_FINDINGS", detail={"findings": [f for f in run["findings"] if f["severity"] == readiness.BLOCKING]})

	with envelope.atomic("submit_tender"):
		version.flags.kt_lifecycle = True
		if not version.prepared_by:
			version.prepared_by = actor
			version.prepared_at = now_datetime()
		envelope.bump(version, version_status="Submitted", submitted_by=actor, submitted_at=now_datetime())
		task = frappe.get_doc(
			{
				"doctype": "Tender Preparation Task", "tender": root.name, "tender_version": version.name,
				"business_role": ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "status": "Open", "task_token": envelope.token(), "record_version": 0,
			}
		).insert(ignore_permissions=True)
		envelope.bump(root, current_state="Submitted for approval")

	result = {"ok": True, "idempotent": False, "tender": root.name, "tender_version": version.name, "task": task.name, "record_version": root.record_version, "warning_count": run["warning_count"], "content_digest": version.content_digest}
	envelope.record_command(idempotency_key=idempotency_key, command="SubmitTenderForApproval", payload=payload, result=result, document_type="Prepared Tender", document_name=root.name, actor=actor)
	return result


# --------------------------------------------------------------------------
# ReturnTenderForCorrection
# --------------------------------------------------------------------------


def _open_task(task: str, actor: str):
	if not task or not frappe.db.exists("Tender Preparation Task", task):
		authz.not_found()
	task_doc = envelope.locked("Tender Preparation Task", task)
	root = envelope.locked("Prepared Tender", task_doc.tender)
	assignment = authz.require_hopf(actor)
	if task_doc.status != "Open" or root.current_state != "Submitted for approval":
		fail("TPR_STALE_VERSION")
	version = frappe.get_doc("Tender Preparation Version", task_doc.tender_version)
	if version.version_status != "Submitted" or root.current_version != version.name:
		fail("TPR_STALE_VERSION")
	return task_doc, root, version, assignment


def return_tender_for_correction(*, task: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"task": task, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = _reason(reason)
	task_doc, root, version, assignment = _open_task(task, actor)
	envelope.check_record_version(root, expected_record_version)

	with envelope.atomic("return_tender"):
		version.flags.kt_lifecycle = True
		envelope.bump(version, version_status="Returned", decided_by=actor, decided_at=now_datetime())
		decision = _decision(task=task_doc, root=root, version=version, actor=actor, capacity=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, decision="Return for correction", reason=reason, resulting_state="Draft", assignment=assignment, idempotency_key=idempotency_key)
		envelope.bump(task_doc, status="Completed", decision=decision.name)
		successor = _copy_draft_successor(root, version)
		envelope.bump(root, current_state="Draft", current_version=successor.name)

	result = {"ok": True, "idempotent": False, "action": "returned", "tender": root.name, "returned_version": version.name, "tender_version": successor.name, "decision": decision.name, "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="ReturnTenderForCorrection", payload=payload, result=result, document_type="Prepared Tender", document_name=root.name, actor=actor)
	return result


# --------------------------------------------------------------------------
# ApproveTenderForPublication (atomic)
# --------------------------------------------------------------------------


def _approval_block(actor: str, version) -> dict[str, str]:
	return {
		"official_name": cstr(frappe.db.get_value("User", actor, "full_name") or actor),
		"official_title": ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
		"approved_date": serializer.fmt_date(nowdate()),
		"reference": f"{frappe.db.get_value('Prepared Tender', version.tender, 'tender_reference')}-V{int(version.version_number)}",
	}


# Test seam for TPR-AC-026: a test may make this raise after the decision is
# inserted to prove nothing survives; production never sets it.
_after_decision_hook = None


def approve_tender_for_publication(*, task: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"task": task}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	task_doc, root, version, assignment = _open_task(task, actor)
	envelope.check_record_version(root, expected_record_version)

	# §10.3 — segregation from the Version's own preparation audit event.
	if actor in {cstr(version.prepared_by), cstr(version.submitted_by)}:
		fail("TPR_SOD_BLOCKED")

	snapshot = snap.load(version)
	if serializer.content_digest(root, version, snapshot) != version.content_digest:
		fail("TPR_BLOCKING_FINDINGS", "The submitted Version's content digest no longer matches.", {"findings": [{"finding_code": "DIGEST_FAILED"}]})
	approval = _approval_block(actor, version)
	run = readiness.run(root, version, approval=approval)
	if run["blocking_count"] or not run.get("renders"):
		fail("TPR_BLOCKING_FINDINGS", detail={"findings": [f for f in run["findings"] if f["severity"] == readiness.BLOCKING]})

	with envelope.atomic("approve_tender"):
		decision = _decision(task=task_doc, root=root, version=version, actor=actor, capacity=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, decision="Approve for publication", reason="", resulting_state="Approved for publication", assignment=assignment, idempotency_key=idempotency_key)
		if _after_decision_hook:
			_after_decision_hook()
		renders = render_service.render(root, version, snapshot, approval=approval, with_pdf=True)
		if renders["problems"]:
			fail("TPR_BLOCKING_FINDINGS", detail={"findings": [{"finding_code": "RENDER_PROBLEM", "message": p} for p in renders["problems"]]})
		decision_view = {"decision": decision.name, "actor": actor, "official_name": approval["official_name"], "capacity": ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "decided_at": cstr(decision.decided_at), "reference": approval["reference"]}
		readiness.store(version, run)
		body, package_digest = serializer.package(root, version, snapshot, renders=renders, readiness=run, decision=decision_view)
		handoff = frappe.get_doc(
			{
				"doctype": "Tender Publication Handoff", "tender": root.name, "tender_version": version.name, "handoff_version": "1.1",
				"package_json": serializer.digest.canonical_json(body), "package_digest": package_digest,
				"invitation_digest": renders["invitation_digest"], "issued_tender_digest": renders["issued_tender_digest"],
				"status": "Ready", "generated_at": now_datetime(),
			}
		).insert(ignore_permissions=True)
		files = render_service.store_files(handoff_name=handoff.name, tender_reference=root.tender_reference, renders=renders)
		for field, file_name in files.items():
			frappe.db.set_value("Tender Publication Handoff", handoff.name, field, file_name, update_modified=False)
		version.flags.kt_lifecycle = True
		envelope.bump(version, version_status="Approved", decided_by=actor, decided_at=now_datetime())
		envelope.bump(task_doc, status="Completed", decision=decision.name)
		envelope.bump(root, current_state="Approved for publication", approved_version=version.name, publication_handoff=handoff.name)
		events.emit(event_type=events.EVENT_HANDOFF_READY, tender=root.name, tender_version=version.name, payload={"publication_handoff": handoff.name, "package_digest": package_digest}, correlation_id=idempotency_key)

	result = {
		"ok": True, "idempotent": False, "action": "approved", "tender": root.name, "tender_version": version.name, "decision": decision.name,
		"publication_handoff": handoff.name, "package_digest": package_digest, "invitation_digest": renders["invitation_digest"],
		"issued_tender_digest": renders["issued_tender_digest"], "files": files, "record_version": root.record_version,
	}
	envelope.record_command(idempotency_key=idempotency_key, command="ApproveTenderForPublication", payload=payload, result=result, document_type="Prepared Tender", document_name=root.name, actor=actor)
	return result


# --------------------------------------------------------------------------
# ReopenApprovedTender
# --------------------------------------------------------------------------


def reopen_approved_tender(*, tender: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"tender": tender, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = _reason(reason)
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = envelope.locked("Prepared Tender", tender)
	assignment = authz.require_hopf(actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state != "Approved for publication" or not root.publication_handoff:
		fail("TPR_STALE_VERSION")
	handoff = envelope.locked("Tender Publication Handoff", root.publication_handoff)
	if handoff.status != "Ready" or handoff.consumed_at or root.publication_consumed_at:
		fail("TPR_PUBLICATION_CONSUMED")
	version = frappe.get_doc("Tender Preparation Version", root.approved_version)

	with envelope.atomic("reopen_tender"):
		decision = _decision(task=None, root=root, version=version, actor=actor, capacity=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, decision="Reopen before publication", reason=reason, resulting_state="Draft", assignment=assignment, idempotency_key=idempotency_key)
		handoff.status = "Cancelled"
		handoff.save(ignore_permissions=True)
		version.flags.kt_lifecycle = True
		envelope.bump(version, version_status="Reopened")
		successor = _copy_draft_successor(root, version)
		envelope.bump(root, current_state="Draft", current_version=successor.name, approved_version=None, publication_handoff=None)

	result = {"ok": True, "idempotent": False, "action": "reopened", "tender": root.name, "reopened_version": version.name, "tender_version": successor.name, "decision": decision.name, "cancelled_handoff": handoff.name, "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="ReopenApprovedTender", payload=payload, result=result, document_type="Prepared Tender", document_name=root.name, actor=actor)
	return result


# --------------------------------------------------------------------------
# RequestTenderUpstreamCorrection (§10.4)
# --------------------------------------------------------------------------


def request_tender_upstream_correction(*, tender: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"tender": tender, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = _reason(reason)
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = envelope.locked("Prepared Tender", tender)
	assignment = authz.require_officer_or_hopf(actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state not in ("Draft", "Submitted for approval"):
		fail("TPR_STALE_VERSION", "Only a Draft or submitted Tender can request an upstream correction; an approved Tender is reopened first.")
	version = frappe.get_doc("Tender Preparation Version", root.current_version)
	capacity = ROLE_PROCUREMENT_OFFICER if authz.has_site_role(ROLE_PROCUREMENT_OFFICER, actor) else ROLE_HEAD_OF_PROCUREMENT_FUNCTION

	with envelope.atomic("upstream_correction"):
		decision = _decision(task=None, root=root, version=version, actor=actor, capacity=capacity, decision="Request upstream correction", reason=reason, resulting_state="Upstream correction required", assignment=assignment, idempotency_key=idempotency_key)
		_cancel_open_tasks(root)
		version.flags.kt_lifecycle = True
		envelope.bump(version, version_status="Upstream correction required", decided_by=actor, decided_at=now_datetime())
		envelope.bump(root, current_state="Upstream correction required")
		release = handoff_gateway.release_consumption(handoff=root.requisition_handoff, tender=root.name, reason=reason, idempotency_key=f"{idempotency_key}:release", user=actor)

	result = {"ok": True, "idempotent": False, "action": "upstream_correction_required", "tender": root.name, "tender_version": version.name, "decision": decision.name, "handoff_release": release.get("action"), "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="RequestTenderUpstreamCorrection", payload=payload, result=result, document_type="Prepared Tender", document_name=root.name, actor=actor)
	return result
