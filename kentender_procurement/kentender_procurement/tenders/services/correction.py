# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §5.1 (last two rows) / §7.2 / §10.14 — the
Requisition-owned correction route (TPR08-AC-010).

`RequestRequisitionCorrection` stops the current pre-publication Version
(immutable, `Stopped for requisition correction`), never edits inherited
content, and hands the correction to the Requisition's Departmental Author
(§5.11: **Correct Requisition …** with the reason, and the requester's
**Waiting for … to correct the requisition**). Requisitions owns how a
corrected successor is authorised; REQ-CHG-001 v1.11 removed handoff
release (REQ FOLLOW_UPS FU-30), so Tenders no longer calls it. Work
continues only from a newly authorised successor handoff on the same Plan
Item: `StartCorrectedTenderVersion` consumes it and creates a linked Draft
with a regenerated snapshot while the stopped history stays untouched."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import clock, compatibility, controls, draft_commands, envelope, events, handoff_gateway, handoffs, lifecycle, review, serializer, template_binding
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

STOPPABLE_VERSION_STATUSES = ("Draft", "Returned", "Submitted", "Approved")
STOPPABLE_TENDER_STATUSES = ("Draft", "Awaiting procurement approval", "Approved")
STOPPED = "Stopped for requisition correction"
CORRECTION_REQUESTED = "Requisition correction requested"


def request_requisition_correction(*, tender: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment, role = authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	payload = {"tender": tender, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload, command="RequestRequisitionCorrection", actor=actor)
	if replay:
		return replay
	reason = " ".join(cstr(reason).split())
	if not (20 <= len(reason) <= 1000):
		fail("TND_CONTROL_INVALID", "A reason of 20–1,000 characters is required.", {"fields": {"reason": "Enter a reason of 20–1,000 characters."}})
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	if root.publication or root.overall_status not in STOPPABLE_TENDER_STATUSES or version.status not in STOPPABLE_VERSION_STATUSES:
		fail("TND_PUBLICATION_STARTED" if root.publication else "TND_STALE_VERSION")
	with envelope.atomic("request-correction"):
		decision = lifecycle.record_decision(root, version, decision="Request requisition correction", actor=actor, business_role=role, assignment=assignment, idempotency_key=idempotency_key, reason=reason)
		envelope.bump(version, status=STOPPED, stopped_by=actor, stopped_at=clock.now(), stop_reason=reason)
		lifecycle.cancel_open_tasks(root)
		previous = root.overall_status
		envelope.bump(root, overall_status=CORRECTION_REQUESTED, approved_version=None)
		author = requisition_author(root)
		handoffs.open_task(root, version, task_type=handoffs.REQUISITION_CORRECTION, subject_type="Procurement Requisition", subject_id=cstr(root.requisition), holder=author, sender=actor, comment=reason)
		events.emit(
			tender=root.name, event_type="TenderRequisitionCorrectionRequested", command="RequestRequisitionCorrection", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status=previous, resulting_status=CORRECTION_REQUESTED, record_version=root.record_version, subject_type="Tender Version", subject_id=version.name, reason=reason,
			payload={"requisition_handoff": root.requisition_handoff, "requisition_author": author, "decision": decision.name}, fixture_namespace=root.fixture_namespace,
		)
	out = {"ok": True, "idempotent": False, "action": "correction_requested", "tender": root.name, "record_version": root.record_version, "stopped_version": version.name, "requisition": root.requisition, "requisition_reference": root.requisition_reference}
	envelope.record_command(idempotency_key=idempotency_key, command="RequestRequisitionCorrection", payload=payload, result=out, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return out


def requisition_author(root) -> str:
	"""The Departmental Author who prepared the authorised Requisition Version
	(§5.11: the correction's holder)."""
	return cstr(frappe.db.get_value("Requisition Version", cstr(root.requisition_version), "prepared_by"))


def correction_state(root, *, user: str | None = None) -> dict[str, Any]:
	"""§10.14 — the stopped Version's request facts, the Requisition's
	current state and owner, and any authorised successor handoff."""
	version = frappe.get_doc("Tender Version", root.current_version) if root.current_version else None
	requisition = frappe.db.get_value("Procurement Requisition", root.requisition, ["current_state", "lead_org_unit_id", "authorised_version", "handoff", "requisition_reference"], as_dict=True) or {}
	successors = handoff_gateway.successors(plan_item_id=cstr(root.plan_item_id), user=user) if root.overall_status == CORRECTION_REQUESTED else []
	successor = successors[0] if successors else None
	# §10.14: the current owner is the correction hand-off's holder (§5.11),
	# named with the responsibility they hold for it
	from kentender_procurement.tenders.services import handoffs

	holder = frappe.db.get_value("Tender Task", {"tender": root.name, "task_type": handoffs.REQUISITION_CORRECTION, "status": "Open"}, "holder") if root.overall_status == CORRECTION_REQUESTED else None
	basis = frappe.db.get_value("Requisition Version", version.requisition_version, "version_number") if version is not None and version.get("requisition_version") else None
	successor_number = frappe.db.get_value("Requisition Version", successor["requisition_version"], "version_number") if successor and successor.get("requisition_version") else None
	return {
		"stopped_version": version.name if version else "", "version_number": int(version.version_number) if version else None,
		"requested_by": cstr(version.stopped_by) if version else "", "requested_by_name": cstr(frappe.db.get_value("User", version.stopped_by, "full_name") or version.stopped_by) if version and version.stopped_by else "",
		"requested_at": cstr(version.stopped_at) if version else "", "requested_at_label": serializer.fmt_datetime_short(version.stopped_at) if version and version.stopped_at else "",
		"reason": cstr(version.stop_reason) if version else "",
		"requisition": {"name": root.requisition, "reference": requisition.get("requisition_reference") or root.requisition_reference, "state": requisition.get("current_state", ""), "lead_org_unit": requisition.get("lead_org_unit_id", ""), "owner_label": cstr(frappe.db.get_value("Organisation Unit", requisition.get("lead_org_unit_id"), "unit_name") or "") if requisition.get("lead_org_unit_id") and frappe.db.has_column("Organisation Unit", "unit_name") else cstr(requisition.get("lead_org_unit_id") or "")},
		"owner_label": f"{cstr(frappe.db.get_value('User', holder, 'full_name') or holder)}, Departmental Author" if holder else "",
		"basis_requisition_version_number": int(basis) if basis else None,
		"successor": {
			"handoff": successor["handoff"], "requisition_reference": successor["requisition_reference"], "requisition_version": successor["requisition_version"], "authorised_at": successor.get("authorised_at", ""),
			"requisition_version_number": int(successor_number) if successor_number else None, "authorised_at_label": serializer.fmt_datetime_short(successor["authorised_at"]) if successor.get("authorised_at") else "",
		} if successor else None,
	}


def start_corrected_tender_version(*, tender: str, handoff: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_officer(actor)
	payload = {"tender": tender, "handoff": handoff}
	replay = envelope.replay_or_none(idempotency_key, payload, command="StartCorrectedTenderVersion", actor=actor)
	if replay:
		return replay
	root, stopped = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if root.overall_status != CORRECTION_REQUESTED or stopped.status != STOPPED:
		fail("TND_STALE_VERSION", "This Tender is not waiting for a corrected requisition.")
	handoff_doc = handoff_gateway.load(handoff)
	handoff_gateway.require_startable(handoff_doc)
	if handoff_doc.consumed_at:
		fail("TND_HANDOFF_CONFLICT", detail={"handoff": handoff_doc.name, "tender": cstr(handoff_doc.tender)})
	snapshot, snapshot_digest = snap.build(handoff_doc)
	if cstr(snapshot.get("plan_item_id")) != cstr(root.plan_item_id):
		fail("TND_HANDOFF_INVALID", "The corrected requisition belongs to a different Plan Item.")
	# TPR-CHG-001 v0.11 §5.3: a corrected Version keeps the release this
	# Tender bound (never rebinds); it may be Available or Superseded.
	binding = template_binding.require_bound(root, "continue")
	compatibility.require_supported(snapshot, binding)
	previous_state = serializer.officer_state(stopped)
	with envelope.atomic("start-corrected"):
		number = int(stopped.version_number) + 1
		draft = frappe.get_doc(
			{
				"doctype": "Tender Version", "tender": root.name, "version_number": number, "status": "Draft", "predecessor_version": stopped.name,
				"requisition_handoff": handoff_doc.name, "requisition_version": handoff_doc.requisition_version, **template_binding.bound_fields(binding),
				"requisition_snapshot_digest": snapshot_digest,
				"requisition_snapshot_json": json.dumps(snapshot, sort_keys=True, default=str),
				# Officer values carry over (§5.1: "linked Draft"), with the title defaulted afresh from the corrected requirement.
				"officer_payload_json": json.dumps(controls.normalise({**previous_state, "tender_title": previous_state.get("tender_title") or controls.defaults(snapshot)["tender_title"]}), sort_keys=True, default=str),
				"prepared_by": actor, "prepared_at": clock.now(), "record_version": 0, "fixture_namespace": root.fixture_namespace,
			}
		)
		envelope.insert(draft)
		result = review.run(root, draft, with_renders=True)
		review.store(draft, result)
		envelope.bump(draft)
		handoffs.close_open(root, task_types=(handoffs.REQUISITION_CORRECTION,))
		envelope.bump(
			root, overall_status="Draft", current_version=draft.name, requisition_handoff=handoff_doc.name, requisition=handoff_doc.requisition,
			requisition_reference=snapshot.get("requisition_reference"), requisition_version=handoff_doc.requisition_version, requirement_title=snapshot.get("requirement_title"),
		)
		handoff_gateway.consume(handoff=handoff_doc.name, tender=root.name, tender_version=draft.name, template_key=binding["template_key"], template_version=binding["template_release"], idempotency_key=f"{idempotency_key}:consume")
		events.emit(
			tender=root.name, event_type="TenderCorrectedVersionStarted", command="StartCorrectedTenderVersion", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status=CORRECTION_REQUESTED, resulting_status="Draft", record_version=root.record_version, subject_type="Tender Version", subject_id=draft.name,
			payload={"stopped_version": stopped.name, "requisition_handoff": handoff_doc.name, "handoff_digest": handoff_doc.handoff_digest, "requisition_snapshot_digest": snapshot_digest}, fixture_namespace=root.fixture_namespace,
		)
	out = {"ok": True, "idempotent": False, "action": "corrected_version_started", "tender": root.name, "record_version": root.record_version, "version": draft_commands.version_dict(draft), "stopped_version": stopped.name}
	envelope.record_command(idempotency_key=idempotency_key, command="StartCorrectedTenderVersion", payload=payload, result=out, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return out
