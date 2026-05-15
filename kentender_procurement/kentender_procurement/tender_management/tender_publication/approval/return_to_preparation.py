# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0320 — ``ReturnToPreparationService`` (std engine §9 / Cursor pack §10).

Canonical return-for-correction path: validated ``return_payload``, decision row, configuration
snapshot superseded, STD unlocked (optional second hop to **Validation Blocked**), readiness
**Invalidated**, audits.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_TENDER_PUBLICATION_RETURN_TO_PREPARATION,
)
from kentender_procurement.tender_management.tender_publication.audit.publication_audit import (
	emit_publication_audit_event,
)
from kentender_procurement.tender_management.tender_publication.approval.approval_decision import (
	_AUDIT_RETURNED,
	DECISION_RETURNED,
	_assert_actor_can_decide,
	_assert_latest_not_approved_for_non_approve,
	_assert_no_critical_readiness,
	_effective_actor,
	_emit_publication_audit,
	_load_snapshot_and_instance,
	_record_decision_row,
	_unlock_instance_from_approval_lock,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	invalidate_readiness_for_tender,
)
from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	resolve_tm2_tender_document,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)

RETURN_TO_PREPARATION_PAYLOAD_INVALID = "RETURN_TO_PREPARATION_PAYLOAD_INVALID"

_CRITICALITY_VALUES: frozenset[str] = frozenset({"Low", "Medium", "High", "Critical"})

_TARGET_INSTANCE_STATUSES: frozenset[str] = frozenset({"In Configuration", "Validation Blocked"})


def _strip(value: str | None) -> str:
	return (value or "").strip()


def _validate_return_payload(payload: dict[str, Any]) -> None:
	missing: list[str] = []
	for key in ("return_reason_code", "return_comment", "affected_area", "criticality"):
		if not _strip(payload.get(key)):
			missing.append(key)
	if missing:
		frappe.throw(
			_("Return payload is missing required fields: {0}").format(", ".join(missing)),
			title=RETURN_TO_PREPARATION_PAYLOAD_INVALID,
			exc=frappe.ValidationError,
		)
	crit = _strip(payload.get("criticality"))
	if crit not in _CRITICALITY_VALUES:
		frappe.throw(
			_("criticality must be one of: {0}").format(", ".join(sorted(_CRITICALITY_VALUES))),
			title=RETURN_TO_PREPARATION_PAYLOAD_INVALID,
			exc=frappe.ValidationError,
		)
	tgt = _strip(payload.get("target_instance_status"))
	if tgt and tgt not in _TARGET_INSTANCE_STATUSES:
		frappe.throw(
			_("target_instance_status must be In Configuration or Validation Blocked."),
			title=RETURN_TO_PREPARATION_PAYLOAD_INVALID,
			exc=frappe.ValidationError,
		)


def _unlock_with_optional_validation_blocked(
	instance_name: str,
	*,
	actor: str,
	target_instance_status: str | None,
) -> str:
	"""Always leave ``Locked for Approval`` via **In Configuration**; optionally move to **Validation Blocked**."""
	_unlock_instance_from_approval_lock(instance_name, actor=actor)
	final = "In Configuration"
	tgt = _strip(target_instance_status)
	if tgt == "Validation Blocked":
		StdInstanceStateService.apply_transition(
			instance_name,
			"Validation Blocked",
			ignore_permissions=True,
		)
		final = "Validation Blocked"
	return final


def _maybe_reset_tender_preparation_status(tender_code: str) -> None:
	"""Soft signal: tender back in preparation (TM2 ``status`` vocabulary)."""
	try:
		tm2 = resolve_tm2_tender_document(tender_code)
		if not tm2:
			return
		st = (frappe.db.get_value("TM2 Tender", tm2.name, "status") or "").strip()
		if st and st != "Cancelled":
			frappe.db.set_value(
				"TM2 Tender",
				tm2.name,
				"status",
				"Returned for Correction",
				update_modified=False,
			)
	except Exception:
		pass


class ReturnToPreparationService:
	"""Pack §10 / std §9 — safe return from approval lock to preparation."""

	@staticmethod
	def normalize_return_payload_from_decision_service(return_payload: dict[str, Any] | None) -> dict[str, Any]:
		"""Map PUB-0310 ``returnForCorrection`` payloads onto PUB-0320 required shape (defaults for pack fields)."""
		p = dict(return_payload or {})
		comment = _strip(p.get("return_comment")) or _strip(p.get("decision_note"))
		if not comment:
			frappe.throw(
				_("return_comment (or decision_note) is required."),
				title=RETURN_TO_PREPARATION_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)
		p["return_comment"] = comment
		if not _strip(p.get("return_reason_code")):
			p["return_reason_code"] = "RETURN_FOR_CORRECTION_UNSPECIFIED"
		if not _strip(p.get("affected_area")):
			p["affected_area"] = "General"
		if not _strip(p.get("criticality")):
			p["criticality"] = "Medium"
		return p

	@staticmethod
	def returnToPreparation(tender_code: str, return_payload: dict[str, Any] | None, actor: str | None = None) -> dict[str, Any]:
		"""Execute return-to-preparation (effects 1–5, pack §10 / std §9.2–9.4)."""
		tc = _strip(tender_code)
		if not tc:
			frappe.throw(_("Tender code is required."), exc=frappe.ValidationError)

		payload = dict(return_payload or {})
		_validate_return_payload(payload)

		act = _effective_actor(actor)
		_assert_actor_can_decide(act)
		tm2 = resolve_tm2_tender_document(tc)
		if not tm2:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(tc),
				frappe.DoesNotExistError,
			)
		snap, inst = _load_snapshot_and_instance(tc)
		_assert_no_critical_readiness(snap)
		_assert_latest_not_approved_for_non_approve(tc)

		decision_note = _strip(
			"[{0}] {1}".format(_strip(payload.get("return_reason_code")), _strip(payload.get("return_comment"))),
		)

		row = _record_decision_row(
			tm2_tender=tm2.name,
			instance_name=inst.name,
			snapshot_name=snap.name,
			decision=DECISION_RETURNED,
			decision_note=decision_note,
			payload=payload,
			actor=act,
		)

		ConfigurationSnapshotService.invalidateConfigurationSnapshot(
			snap.name,
			_strip(payload.get("return_comment")),
			actor=act,
		)

		final_status = _unlock_with_optional_validation_blocked(
			inst.name,
			actor=act,
			target_instance_status=_strip(payload.get("target_instance_status")) or None,
		)
		invalidate_readiness_for_tender(tc, actor=act)
		_maybe_reset_tender_preparation_status(tc)

		_emit_publication_audit(
			event_type=_AUDIT_RETURNED,
			tender_code=tc,
			instance_name=inst.name,
			snapshot_code=snap.name,
			decision_code=row.name,
			decision=DECISION_RETURNED,
			actor=act,
			extra={"return_payload": payload},
		)
		emit_publication_audit_event(
			event_type=AUDIT_TENDER_PUBLICATION_RETURN_TO_PREPARATION,
			tender_code=tc,
			action="return_to_preparation",
			performed_by=act,
			timestamp=now_datetime(),
			instance_code=inst.name,
			configuration_snapshot_code=snap.name,
			details={
				"decision_code": row.name,
				"return_payload": payload,
				"instance_status_after": final_status,
			},
		)

		return {
			"ok": True,
			"decision_code": row.name,
			"decision": DECISION_RETURNED,
			"configuration_snapshot_code": snap.name,
			"tender_std_instance": inst.name,
			"instance_status": final_status,
			"return_payload": payload,
		}
