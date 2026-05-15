# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0310 — ``ApprovalDecisionService`` (record decisions; no silent content edits).

Cursor pack §9: preconditions (configuration snapshot, ``Locked for Approval``, actor permission,
no critical readiness blockers on snapshot); append-only ``Tender Publication Approval Decision``;
audit via ``kentender_core`` ``Audit Event``; **return** delegates to PUB-0320 ``ReturnToPreparationService``;
reject unlocks STD and supersedes snapshot.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	canonical_tm2_tender_code,
	resolve_tm2_tender_document,
)
from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.tender_publication.audit.publication_audit import (
	emit_publication_audit_event,
)
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_PUBLICATION_LOCK_APPLIED
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	invalidate_readiness_for_tender,
)
from kentender_procurement.tender_management.tender_publication.readiness.schema import is_critical_code
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)

APPROVAL_DECISION_PRECONDITION_FAILED = "APPROVAL_DECISION_PRECONDITION_FAILED"
APPROVAL_DECISION_READINESS_BLOCKERS_PRESENT = "APPROVAL_DECISION_READINESS_BLOCKERS_PRESENT"
APPROVAL_DECISION_PERMISSION_DENIED = "APPROVAL_DECISION_PERMISSION_DENIED"
APPROVAL_DECISION_ALREADY_APPROVED = "APPROVAL_DECISION_ALREADY_APPROVED"
APPROVAL_DECISION_STATE_CONFLICT = "APPROVAL_DECISION_STATE_CONFLICT"
APPROVAL_DECISION_PAYLOAD_INVALID = "APPROVAL_DECISION_PAYLOAD_INVALID"

DECISION_APPROVED = "Approved for Publication"
DECISION_RETURNED = "Returned for Correction"
DECISION_REJECTED = "Rejected"
DECISION_CLARIFICATION = "Clarification Requested"

_AUDIT_GRANTED = "TENDER_PUBLICATION_APPROVAL_GRANTED"
_AUDIT_RETURNED = "TENDER_PUBLICATION_APPROVAL_RETURNED"
_AUDIT_REJECTED = "TENDER_PUBLICATION_APPROVAL_REJECTED"
_AUDIT_CLARIFICATION = "TENDER_PUBLICATION_APPROVAL_CLARIFICATION_REQUESTED"

def _strip(value: str | None) -> str:
	return (value or "").strip()


def _effective_actor(actor: str | None) -> str:
	return _strip(actor) or _strip(frappe.session.user) or "Administrator"


def _assert_actor_can_decide(actor: str) -> None:
	from kentender_procurement.tender_management.tender_publication.authorization.publication_authorization import (
		PublicationAuthorizationService,
	)

	PublicationAuthorizationService.assertCanApproveForPublication(actor)


def _critical_codes_from_snapshot(snap: Document) -> list[str]:
	raw = _strip(getattr(snap, "readiness_summary_json", None))
	if not raw:
		return []
	try:
		obj = json.loads(raw)
	except Exception:
		return []
	if not isinstance(obj, dict):
		return []
	findings = list(obj.get("findings") or [])
	out: list[str] = []
	for row in findings:
		code = _strip((row or {}).get("code"))
		if code and is_critical_code(code):
			out.append(code)
	return out


def _latest_decision(tender_key: str) -> Document | None:
	tk = _strip(tender_key)
	if not tk:
		return None
	tm2 = resolve_tm2_tender_document(tk)
	if not tm2:
		return None
	filters: dict[str, str] = {"tm2_tender": tm2.name}
	rows = frappe.get_all(
		"Tender Publication Approval Decision",
		filters=filters,
		pluck="name",
		order_by="decided_at desc",
		limit=1,
	)
	if not rows:
		return None
	return frappe.get_doc("Tender Publication Approval Decision", rows[0])


def _assert_not_already_approved(tender_code: str) -> None:
	prev = _latest_decision(tender_code)
	if prev and (prev.decision or "").strip() == DECISION_APPROVED:
		frappe.throw(
			_("This tender is already marked Approved for Publication."),
			title=APPROVAL_DECISION_ALREADY_APPROVED,
			exc=frappe.ValidationError,
		)


def _assert_latest_not_approved_for_non_approve(tender_code: str) -> None:
	prev = _latest_decision(tender_code)
	if prev and (prev.decision or "").strip() == DECISION_APPROVED:
		frappe.throw(
			_("No further approval actions are allowed after Approved for Publication."),
			title=APPROVAL_DECISION_STATE_CONFLICT,
			exc=frappe.ValidationError,
		)


def _load_snapshot_and_instance(tender_code: str) -> tuple[Document, Document]:
	cur = ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tender_code)
	if not cur:
		frappe.throw(
			_("A Final configuration snapshot is required."),
			title=APPROVAL_DECISION_PRECONDITION_FAILED,
			exc=frappe.ValidationError,
		)
	snap = frappe.get_doc("Tender STD Instance Snapshot", cur["snapshot_code"])
	if (snap.snapshot_type or "").strip() != "Configuration" or (snap.snapshot_status or "").strip() != "Final":
		frappe.throw(
			_("Configuration snapshot is not in a valid state for decisions."),
			title=APPROVAL_DECISION_PRECONDITION_FAILED,
			exc=frappe.ValidationError,
		)
	inst = frappe.get_doc("Tender STD Instance", snap.tender_std_instance)
	if (inst.instance_status or "").strip() != "Locked for Approval":
		frappe.throw(
			_("STD Instance must be Locked for Approval (current: {0}).").format(inst.instance_status),
			title=APPROVAL_DECISION_PRECONDITION_FAILED,
			exc=frappe.ValidationError,
		)
	return snap, inst


def _assert_no_critical_readiness(snap: Document) -> None:
	codes = _critical_codes_from_snapshot(snap)
	if codes:
		frappe.throw(
			_("Snapshot readiness contains critical blockers: {0}").format(", ".join(codes)),
			title=APPROVAL_DECISION_READINESS_BLOCKERS_PRESENT,
			exc=frappe.ValidationError,
		)


def _emit_publication_audit(
	*,
	event_type: str,
	tender_code: str,
	instance_name: str,
	snapshot_code: str,
	decision_code: str,
	decision: str,
	actor: str,
	extra: dict[str, Any] | None = None,
) -> None:
	details: dict[str, Any] = {
		"decision_code": decision_code,
		"decision": decision,
	}
	if extra:
		details.update(extra)
	emit_publication_audit_event(
		event_type=event_type,
		tender_code=tender_code,
		action="publication_approval_decision",
		performed_by=actor,
		instance_code=instance_name,
		configuration_snapshot_code=snapshot_code,
		details=details,
		timestamp=now_datetime(),
	)


def _record_decision_row(
	*,
	tm2_tender: str,
	instance_name: str,
	snapshot_name: str,
	decision: str,
	decision_note: str | None,
	payload: dict[str, Any] | None,
	actor: str,
) -> Document:
	if not tm2_tender:
		frappe.throw(
			_("Internal error: tm2_tender is required on approval decision."),
			exc=frappe.ValidationError,
		)
	doc = frappe.new_doc("Tender Publication Approval Decision")
	doc.tm2_tender = tm2_tender
	doc.tender_std_instance = instance_name
	doc.configuration_snapshot = snapshot_name
	doc.decision = decision
	doc.decision_note = _strip(decision_note) or None
	doc.decided_by = actor
	doc.decided_at = now_datetime()
	doc.payload_json = payload or {}
	doc.insert(ignore_permissions=True)
	return doc


def _unlock_instance_from_approval_lock(instance_name: str, *, actor: str) -> None:
	StdInstanceStateService.apply_transition(
		instance_name,
		"In Configuration",
		ignore_permissions=True,
	)
	inst = frappe.get_doc("Tender STD Instance", instance_name)
	inst.locked_for_approval_at = None
	inst.locked_for_approval_by = None
	inst.save(ignore_permissions=True)
	emit_std_instance_event(
		EVT_STDINST_PUBLICATION_LOCK_APPLIED,
		instance_code=instance_name,
		details={"lock_type": "approval_release", "released_by": actor},
	)


class ApprovalDecisionService:
	"""Publication approval decisions (PUB-0310). Does **not** mutate TDS/SCC/BOQ/outputs."""

	@staticmethod
	def approveForPublication(
		tender_code: str,
		decision_payload: dict[str, Any] | None,
		actor: str | None = None,
	) -> dict[str, Any]:
		"""Record **Approved for Publication**; STD remains ``Locked for Approval`` until publish (PUB-0600)."""
		raw = _strip(tender_code)
		act = _effective_actor(actor)
		tm2 = resolve_tm2_tender_document(raw)
		if not tm2:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(raw),
				frappe.DoesNotExistError,
			)
		canon = canonical_tm2_tender_code(tm2)
		enforce_sec_authorization(
			action_code="APPROVE_TENDER_PUBLICATION",
			actor=act,
			object_type="TM2 Tender",
			object_code=canon,
			context={"object_exists": True},
			fallback_message="Not authorized to approve tender publication.",
		)
		_assert_actor_can_decide(act)
		snap, inst = _load_snapshot_and_instance(raw)
		_assert_no_critical_readiness(snap)
		_assert_not_already_approved(raw)

		note = _strip((decision_payload or {}).get("decision_note"))
		row = _record_decision_row(
			tm2_tender=tm2.name,
			instance_name=inst.name,
			snapshot_name=snap.name,
			decision=DECISION_APPROVED,
			decision_note=note or None,
			payload=decision_payload,
			actor=act,
		)
		_emit_publication_audit(
			event_type=_AUDIT_GRANTED,
			tender_code=canon,
			instance_name=inst.name,
			snapshot_code=snap.name,
			decision_code=row.name,
			decision=DECISION_APPROVED,
			actor=act,
		)
		return {
			"ok": True,
			"decision_code": row.name,
			"decision": DECISION_APPROVED,
			"configuration_snapshot_code": snap.name,
			"tender_std_instance": inst.name,
			"instance_status": (frappe.db.get_value("Tender STD Instance", inst.name, "instance_status") or "").strip(),
		}

	@staticmethod
	def returnForCorrection(
		tender_code: str,
		return_payload: dict[str, Any] | None,
		actor: str | None = None,
	) -> dict[str, Any]:
		"""Delegate to PUB-0320 ``ReturnToPreparationService`` (normalizes legacy payloads)."""
		from kentender_procurement.tender_management.tender_publication.approval.return_to_preparation import (
			ReturnToPreparationService,
		)

		normalized = ReturnToPreparationService.normalize_return_payload_from_decision_service(return_payload)
		return ReturnToPreparationService.returnToPreparation(tender_code, normalized, actor)

	@staticmethod
	def rejectPublication(
		tender_code: str,
		decision_payload: dict[str, Any] | None,
		actor: str | None = None,
	) -> dict[str, Any]:
		"""Record **Rejected**; same side-effects as return (unlock + supersede snapshot + invalidate readiness)."""
		raw = _strip(tender_code)
		act = _effective_actor(actor)
		tm2 = resolve_tm2_tender_document(raw)
		if not tm2:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(raw),
				frappe.DoesNotExistError,
			)
		canon = canonical_tm2_tender_code(tm2)
		_assert_actor_can_decide(act)
		snap, inst = _load_snapshot_and_instance(raw)
		_assert_no_critical_readiness(snap)
		_assert_latest_not_approved_for_non_approve(raw)

		payload = dict(decision_payload or {})
		note = _strip(payload.get("decision_note")) or _strip(payload.get("reject_reason"))
		if not note:
			frappe.throw(
				_("decision_note (or reject_reason) is required for a rejection."),
				title=APPROVAL_DECISION_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)

		row = _record_decision_row(
			tm2_tender=tm2.name,
			instance_name=inst.name,
			snapshot_name=snap.name,
			decision=DECISION_REJECTED,
			decision_note=note,
			payload=payload,
			actor=act,
		)
		ConfigurationSnapshotService.invalidateConfigurationSnapshot(snap.name, note, actor=act)
		_unlock_instance_from_approval_lock(inst.name, actor=act)
		invalidate_readiness_for_tender(raw, actor=act)

		_emit_publication_audit(
			event_type=_AUDIT_REJECTED,
			tender_code=canon,
			instance_name=inst.name,
			snapshot_code=snap.name,
			decision_code=row.name,
			decision=DECISION_REJECTED,
			actor=act,
		)
		return {
			"ok": True,
			"decision_code": row.name,
			"decision": DECISION_REJECTED,
			"configuration_snapshot_code": snap.name,
			"tender_std_instance": inst.name,
			"instance_status": (frappe.db.get_value("Tender STD Instance", inst.name, "instance_status") or "").strip(),
		}

	@staticmethod
	def requestClarification(
		tender_code: str,
		clarification_payload: dict[str, Any] | None,
		actor: str | None = None,
	) -> dict[str, Any]:
		"""Record **Clarification Requested**; leaves STD ``Locked for Approval`` and snapshot **Final**."""
		raw = _strip(tender_code)
		act = _effective_actor(actor)
		tm2 = resolve_tm2_tender_document(raw)
		if not tm2:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(raw),
				frappe.DoesNotExistError,
			)
		canon = canonical_tm2_tender_code(tm2)
		_assert_actor_can_decide(act)
		snap, inst = _load_snapshot_and_instance(raw)
		_assert_no_critical_readiness(snap)
		_assert_latest_not_approved_for_non_approve(raw)

		payload = dict(clarification_payload or {})
		note = (
			_strip(payload.get("clarification_summary"))
			or _strip(payload.get("clarification_note"))
			or _strip(payload.get("decision_note"))
		)
		if not note:
			frappe.throw(
				_("clarification_summary, clarification_note, or decision_note is required."),
				title=APPROVAL_DECISION_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)

		row = _record_decision_row(
			tm2_tender=tm2.name,
			instance_name=inst.name,
			snapshot_name=snap.name,
			decision=DECISION_CLARIFICATION,
			decision_note=note,
			payload=payload,
			actor=act,
		)
		_emit_publication_audit(
			event_type=_AUDIT_CLARIFICATION,
			tender_code=canon,
			instance_name=inst.name,
			snapshot_code=snap.name,
			decision_code=row.name,
			decision=DECISION_CLARIFICATION,
			actor=act,
		)
		return {
			"ok": True,
			"decision_code": row.name,
			"decision": DECISION_CLARIFICATION,
			"configuration_snapshot_code": snap.name,
			"tender_std_instance": inst.name,
			"instance_status": (frappe.db.get_value("Tender STD Instance", inst.name, "instance_status") or "").strip(),
		}
