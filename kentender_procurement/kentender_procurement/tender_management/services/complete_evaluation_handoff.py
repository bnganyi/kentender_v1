# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §12.3 — ``complete_evaluation_handoff`` / ``completeEvaluationHandoff``.

Preconditions:

1. **TM2 Tender** status **Opening Completed**;
2. **TM2 Opening Readiness Record** exists (opening readiness gate);
3. ``opening_record_code`` is non-empty and, when set on the readiness row, matches the
   **Bid Opening** reference passed to this service;
4. **DEM** and **DSM** exist (consumable current outputs) and align with **publication snapshot V2**
   (active binding output refs vs :func:`get_tender_std_output_refs`);
5. At least one **opened** submission (``Opened`` / ``Evaluation Locked``) with a bid code;
6. :func:`~kentender_procurement.tender_management.security.action_availability.service.get_action_availability`
   for **EV2_PREPARE_EVALUATION_HANDOFF**.

On success:

1. Insert **TM2 Evaluation Handoff Record** (``EHR-{tender_code}``) with DEM/DSM refs, publication snapshot
   metadata in ``handoff_payload``, ``opened_submission_refs`` / ``addendum_history_refs`` (**refs only** —
   no evaluation criteria bodies; criteria remain in DEM / Evaluation module per TM2-EHR-003);
2. Set tender **Evaluation Ready**;
3. Audit **Evaluation Handoff Completed**.

Tests: ``tender_management.tests.test_p7_03_complete_evaluation_handoff``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
	is_known_denial_code,
)
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	get_current_dem,
	get_current_dsm,
	get_tender_std_output_refs,
)

_ACTION = "EV2_PREPARE_EVALUATION_HANDOFF"
_OBJECT_TYPE = "TM2 Tender"

_OPENED_BID_STATUSES: frozenset[str] = frozenset({"Opened", "Evaluation Locked"})


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _resolve_tm2(tender_code: str) -> Document | None:
	tc = (tender_code or "").strip()
	if not tc:
		return None
	name = frappe.db.get_value("TM2 Tender", {"tender_code": tc}, "name")
	if name and frappe.db.exists("TM2 Tender", name):
		return frappe.get_doc("TM2 Tender", name)
	if frappe.db.exists("TM2 Tender", tc):
		return frappe.get_doc("TM2 Tender", tc)
	return None


def _active_binding_row(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Tender STD Binding",
		filters={
			"tm2_tender": tm2_name,
			"is_active": 1,
			"binding_status": ["not in", ["Cancelled", "Superseded"]],
		},
		fields=[
			"name",
			"tender_std_instance",
			"publication_snapshot_code",
			"dsm_output_code",
			"dem_output_code",
		],
		limit=1,
	)
	return dict(rows[0]) if rows else None


def _opening_readiness_row(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Opening Readiness Record",
		filters={"tm2_tender": tm2_name},
		fields=["name", "opening_readiness_code", "opening_record_code"],
		limit=1,
	)
	return dict(rows[0]) if rows else None


def _issued_addendum_codes(tm2_name: str) -> list[str]:
	out: list[str] = []
	for row in frappe.get_all(
		"TM2 Addendum",
		filters={"tm2_tender": tm2_name, "status": "Issued"},
		fields=["name", "addendum_code"],
		order_by="creation asc",
	):
		code = cstr(row.get("addendum_code") or row.get("name") or "").strip()
		if code:
			out.append(code)
	return sorted(set(out))


def _opened_bid_codes(tm2_name: str) -> list[str]:
	codes: list[str] = []
	for row in frappe.get_all(
		"TM2 Bid Submission",
		filters={"tm2_tender": tm2_name},
		fields=["bid_code", "bid_status"],
		order_by="bid_code asc",
	):
		if cstr(row.bid_status).strip() not in _OPENED_BID_STATUSES:
			continue
		bc = cstr(row.bid_code).strip()
		if bc:
			codes.append(bc)
	return sorted(codes)


def complete_evaluation_handoff(
	actor: str,
	tender_code: str,
	opening_record_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""§12.3 — persist **TM2 Evaluation Handoff Record** after opening; transition to **Evaluation Ready**."""
	ctx = dict(context or {})
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format(cstr(tender_code).strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()

	if frappe.db.exists("TM2 Evaluation Handoff Record", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Evaluation handoff has already been completed for this tender."),
		)

	if st != "Opening Completed":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Evaluation handoff requires the tender to be in Opening Completed state."),
			extra={"tender_status": st},
		)

	orr = _opening_readiness_row(tm2.name)
	if not orr:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("TM2 Opening Readiness Record is required before evaluation handoff."),
		)

	opn_req = cstr(opening_record_code or "").strip()
	if not opn_req:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Opening record code is required."),
		)
	orr_opn = cstr(orr.get("opening_record_code") or "").strip()
	if not orr_opn:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Opening readiness record must reference a completed opening record."),
		)
	if orr_opn != opn_req:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Opening record code does not match the opening readiness record."),
			extra={"expected_opening_record_code": orr_opn, "provided_opening_record_code": opn_req},
		)

	bind = _active_binding_row(tm2.name)
	if not bind or not cstr(bind.get("tender_std_instance")).strip():
		return _deny(
			DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			_("No active TM2 Tender STD Binding with a Tender STD Instance."),
		)
	si = cstr(bind["tender_std_instance"]).strip()

	refs = get_tender_std_output_refs(tc)
	if not refs.get("ok"):
		dc = cstr(refs.get("denial_code") or DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value).strip()
		if not dc or not is_known_denial_code(dc):
			dc = DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value
		return _deny(
			dc,
			str(refs.get("message") or _("Publication snapshot could not be resolved.")),
			extra={"snapshot": {k: refs.get(k) for k in ("denial_code", "message", "missing_fields") if k in refs}},
		)

	bind_pub = cstr(bind.get("publication_snapshot_code") or "").strip()
	snap_pub = cstr(refs.get("publication_snapshot_code") or "").strip()
	if not bind_pub:
		return _deny(
			DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			_("Active binding is missing a publication snapshot reference."),
		)
	if bind_pub != snap_pub:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Active binding publication snapshot does not match the current STD publication snapshot."),
			extra={"binding_publication_snapshot_code": bind_pub, "resolved_publication_snapshot_code": snap_pub},
		)

	bind_dsm = cstr(bind.get("dsm_output_code") or "").strip()
	bind_dem = cstr(bind.get("dem_output_code") or "").strip()
	ref_dsm = cstr(refs.get("dsm_output_code") or "").strip()
	ref_dem = cstr(refs.get("dem_output_code") or "").strip()
	if bind_dsm and ref_dsm and bind_dsm != ref_dsm:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("DSM output on the binding does not match the publication snapshot."),
		)
	if bind_dem and ref_dem and bind_dem != ref_dem:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("DEM output on the binding does not match the publication snapshot."),
		)

	dsm_live = get_current_dsm(si)
	if not dsm_live.get("ok"):
		return _deny(
			DenialCode.AUTH_DSM_MISSING_OR_STALE.value,
			str(dsm_live.get("message") or _("DSM is missing or not consumable.")),
			extra={"dsm_resolution": dsm_live},
		)
	dsm_code = cstr(dsm_live.get("output_code") or "").strip()
	if not dsm_code or dsm_code != ref_dsm:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("DSM output does not match the publication snapshot binding."),
			extra={"dsm_output_code": dsm_code, "snapshot_dsm_output_code": ref_dsm},
		)

	dem_live = get_current_dem(si)
	if not dem_live.get("ok"):
		return _deny(
			DenialCode.AUTH_DEM_MISSING_OR_STALE.value,
			str(dem_live.get("message") or _("DEM is missing or not consumable.")),
			extra={"dem_resolution": dem_live},
		)
	dem_code = cstr(dem_live.get("output_code") or "").strip()
	if not dem_code or dem_code != ref_dem:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("DEM output does not match the publication snapshot binding."),
			extra={"dem_output_code": dem_code, "snapshot_dem_output_code": ref_dem},
		)

	opened_codes = _opened_bid_codes(tm2.name)
	if not opened_codes:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("At least one opened submission (bid code) is required for evaluation handoff."),
		)

	addendum_codes = _issued_addendum_codes(tm2.name)

	avail = get_action_availability(
		_ACTION,
		_OBJECT_TYPE,
		tc,
		actor,
		context={**ctx, "object_exists": True},
	)
	if not avail.get("allowed"):
		dc = _map_auth_denial(str(avail.get("denial_code") or ""))
		return _deny(
			dc,
			str(avail.get("user_message") or avail.get("message") or dc),
			extra={"availability": avail},
		)

	now = now_datetime()
	handoff_payload: dict[str, Any] = {
		"tender_code": tc,
		"publication_snapshot_code": snap_pub,
		"snapshot_hash": cstr(refs.get("snapshot_hash") or ""),
		"bundle_output_code": cstr(refs.get("bundle_output_code") or ""),
		"dsm_output_code": dsm_code,
		"dem_output_code": dem_code,
		"dcm_output_code": cstr(refs.get("dcm_output_code") or ""),
		"opened_submission_count": len(opened_codes),
		"addendum_history_count": len(addendum_codes),
		"opening_record_code": opn_req,
	}

	addendum_refs: dict[str, list[str]] | None = {"refs": addendum_codes} if addendum_codes else None

	ehr = frappe.get_doc(
		{
			"doctype": "TM2 Evaluation Handoff Record",
			"tm2_tender": tm2.name,
			"tender_code": tc,
			"opening_record_code": opn_req,
			"dem_output_code": dem_code,
			"dsm_output_code": dsm_code,
			"tender_std_instance_code": si,
			"opened_submission_refs": {"refs": opened_codes},
			"addendum_history_refs": addendum_refs,
			"handoff_payload": handoff_payload,
			"handoff_status": "Ready",
			"sent_by": actor,
			"sent_at": now,
		}
	)
	ehr.insert(ignore_permissions=True)
	ehr.reload()

	frappe.db.set_value("TM2 Tender", tm2.name, {"status": "Evaluation Ready"}, update_modified=True)

	audit_payload = {
		"tender_code": tc,
		"evaluation_handoff_code": ehr.evaluation_handoff_code,
		"tm2_evaluation_handoff_record": ehr.name,
		"opening_record_code": opn_req,
		"tm2_opening_readiness_record": cstr(orr.get("name") or ""),
		"dem_output_code": dem_code,
		"dsm_output_code": dsm_code,
		"publication_snapshot_code": snap_pub,
		"opened_submission_count": len(opened_codes),
		"addendum_history_count": len(addendum_codes),
		"tender_std_instance_code": si,
	}
	append_tender_audit_event(
		tc,
		"Evaluation Handoff Completed",
		actor,
		audit_payload,
		related_object_type="TM2 Evaluation Handoff Record",
		related_object_code=ehr.name,
		previous_state="Opening Completed",
		new_state="Evaluation Ready",
		enforce_section_13_2=False,
	)

	return {
		"ok": True,
		"actor": actor,
		"tender_code": tc,
		"tm2_tender": tm2.name,
		"tender_status": "Evaluation Ready",
		"tm2_evaluation_handoff_record": ehr.name,
		"evaluation_handoff_code": ehr.evaluation_handoff_code,
		"dem_output_code": dem_code,
		"dsm_output_code": dsm_code,
		"publication_snapshot_code": snap_pub,
		"opened_submission_refs": {"refs": opened_codes},
		"addendum_history_refs": addendum_refs or {"refs": []},
		"handoff_payload": handoff_payload,
	}


def completeEvaluationHandoff(
	actor: str,
	tender_code: str,
	opening_record_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`complete_evaluation_handoff`."""
	return complete_evaluation_handoff(actor, tender_code, opening_record_code, context=context)
