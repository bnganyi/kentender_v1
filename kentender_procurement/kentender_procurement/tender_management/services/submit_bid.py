# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §11.5 — ``submit_bid`` / ``submitBid`` (submit, seal, receipt).

Preconditions (service order):

1. **TM2 Tender** status **Published** (not **Suspended Pending Addendum** / other states);
2. supplier eligibility + participation + submission window + issued addendum acks (same portal
   gates as :mod:`start_bid_draft`);
3. :func:`get_action_availability` for **BID2_SUBMIT**;
4. :func:`~kentender_procurement.tender_management.services.validate_bid_submission_against_dsm.validate_bid_submission_against_dsm`;
5. active **TM2 Tender STD Binding** must carry ``publication_snapshot_code``;
6. no prior **Submitted** / **Sealed** (etc.) bid for the same tender + supplier.

On success:

1. Insert **TM2 Bid Submission** (``bid_status`` **Submitted**, ``submission_hash`` over a sealed
   metadata envelope — no raw binaries);
2. Append audit **Bid Submitted**;
3. Transition ``bid_status`` → **Sealed**; append audit **Bid Sealed**;
4. Insert **TM2 Bid Submission Component** rows for mandatory DSM requirements (incl. **BOQRateEntry**
   when enabled);
5. Insert **TM2 Bid Receipt** (``RCT-{bid_code}``, ``receipt_type`` **Submission**, TM2-RCT-002-safe
   ``receipt_payload`` + ``receipt_hash``).

If the submission deadline has passed (doc 9 §11.6), the portal gate records a **TM2 Late Submission
Attempt** and audit **Late Submission Rejected** via
:func:`~kentender_procurement.tender_management.services.record_late_submission_attempt.persist_tm2_late_submission_rejection`
— no **TM2 Bid Submission** is created; the service still returns ``AUTH_DEADLINE_PASSED``.

Tests: ``tender_management.tests.test_p6_05_submit_bid``, ``tender_management.tests.test_p6_06_record_late_submission_attempt``
(``test_EX_14_*`` — late path: **TM2 Late Submission Attempt**, not bid); ``tender_management.tests.test_p10_07_supplier_portal_submit_bid``
(``test_EX_07_*`` — no arithmetic correction at submission).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, get_datetime, now_datetime

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
)
from kentender_procurement.tender_management.services.record_late_submission_attempt import (
	persist_tm2_late_submission_rejection,
)
from kentender_procurement.tender_management.services.tm2_addendum_acknowledgement_checks import (
	missing_required_addendum_acknowledgements,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import get_current_dsm
from kentender_procurement.tender_management.services.validate_bid_submission_against_dsm import (
	validate_bid_submission_against_dsm,
)
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance

_ACTION = "BID2_SUBMIT"
_OBJECT_TYPE = "TM2 Tender"

_BLOCKING_PRIOR_BID_STATUSES: frozenset[str] = frozenset(
	{
		"Submitted",
		"Sealed",
		"Opened",
		"Excluded by System Rule",
		"Evaluation Locked",
	}
)


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


def _submission_deadline_row(tm2_name: str) -> tuple[str | None, Any]:
	tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2_name}, "name")
	if not tl_name:
		return None, None
	deadline = frappe.db.get_value("TM2 Tender Timeline", tl_name, "submission_deadline_at")
	return str(tl_name), deadline


def _active_std_instance(tm2_name: str) -> str | None:
	return frappe.db.get_value(
		"TM2 Tender STD Binding",
		{"tm2_tender": tm2_name, "is_active": 1},
		"tender_std_instance",
	)


def _binding_snapshot(tm2_name: str) -> tuple[str | None, str | None]:
	row = frappe.db.get_value(
		"TM2 Tender STD Binding",
		{"tm2_tender": tm2_name, "is_active": 1},
		["tender_std_instance", "publication_snapshot_code"],
		as_dict=True,
	)
	if not row:
		return None, None
	return cstr(row.get("tender_std_instance") or "").strip() or None, cstr(
		row.get("publication_snapshot_code") or ""
	).strip() or None


def _parse_dsm_json(dsm_output_name: str) -> dict[str, Any] | None:
	doc = frappe.get_doc("Tender STD Generated Output", dsm_output_name)
	raw = doc.get("content_json")
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			p = json.loads(raw)
			return p if isinstance(p, dict) else None
		except json.JSONDecodeError:
			return None
	return None


def _sha256_hex(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def _canonical_json(obj: Any) -> bytes:
	return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _seal_envelope(bid_payload: dict[str, Any]) -> bytes:
	"""Hashing envelope — metadata/refs only (no binary bodies)."""
	req = bid_payload.get("requirements")
	if not isinstance(req, dict):
		req = {}
	boq = bid_payload.get("boq")
	if not isinstance(boq, list):
		boq = []
	acks = bid_payload.get("addendum_acknowledgements")
	if not isinstance(acks, dict):
		acks = {}
	env = {
		"addendum_acknowledgements": acks,
		"boq": boq,
		"requirements": req,
	}
	return _canonical_json(env)


def _compute_total_and_currency(si: str, bid_payload: dict[str, Any], dsm: dict[str, Any]) -> tuple[float, str]:
	boq_doc = get_boq_for_instance(si)
	curr = "KES"
	if boq_doc:
		curr = cstr(boq_doc.currency or "KES").strip() or "KES"
	bqe = dsm.get("boq_rate_entry")
	if not (isinstance(bqe, dict) and bqe.get("enabled")):
		return 0.0, curr
	bid_boq = bid_payload.get("boq")
	if not isinstance(bid_boq, list) or not boq_doc:
		return 0.0, curr
	by_item: dict[str, dict[str, Any]] = {}
	for raw in bid_boq:
		if isinstance(raw, dict):
			num = cstr(raw.get("item_number") or "").strip()
			if num:
				by_item[num] = raw
	total = 0.0
	for row in boq_doc.get("boq_items") or []:
		st = cstr(getattr(row, "status", None) or "").strip()
		if st and st not in ("Published", "Current"):
			continue
		item_number = cstr(getattr(row, "item_number", None) or "").strip()
		if not item_number:
			continue
		pe_qty = flt(getattr(row, "quantity", None))
		rate_req = cint(getattr(row, "rate_required_from_supplier", 0))
		item_type = cstr(getattr(row, "item_type", None) or "").strip()
		sup_mode = cstr(getattr(row, "supplier_input_mode", None) or "").strip()
		fixed_amount = flt(getattr(row, "fixed_amount", None))
		ps_amt = flt(getattr(row, "provisional_sum_amount", None))
		bid_row = by_item.get(item_number)
		if rate_req and bid_row is not None:
			total += pe_qty * flt(bid_row.get("rate"))
		elif not rate_req:
			lock_val = fixed_amount or ps_amt
			if lock_val:
				total += flt(lock_val)
	return total, curr


def _component_type_for_requirement(requirement_type: str, entry: Any) -> str:
	rt = (requirement_type or "").strip()
	if rt == "BOQRateEntry":
		return "OTHER"
	if rt in ("Document", "TechnicalProposal"):
		if isinstance(entry, dict) and cstr(
			entry.get("file_url") or entry.get("attachment_url") or ""
		).strip():
			return "FILE_SET"
		return "STRUCTURED_TEXT"
	return "STRUCTURED_TEXT"


def _portal_gate_submit(
	actor: str,
	tender_code: str,
	supplier_ref: str,
	context: dict[str, Any],
	bid_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
	ctx = dict(context or {})
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format(cstr(tender_code).strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st != "Published":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Bid submission requires the tender to be published."),
			extra={"tender_status": st},
		)

	elig = check_supplier_tender_access(actor, tc, supplier_ref, context=ctx)
	if not elig.get("ok"):
		return {
			"ok": False,
			"denial_code": cstr(elig.get("denial_code") or DenialCode.AUTH_SUPPLIER_INELIGIBLE.value).strip(),
			"message": cstr(elig.get("message") or _("Supplier is not eligible for this tender.")).strip(),
			"actor": actor,
		}

	supplier = cstr(elig.get("supplier") or "").strip()
	if not supplier:
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, _("Supplier could not be resolved for this tender."))

	acting = cstr(ctx.get("acting_supplier") or "").strip()
	if acting and acting != supplier:
		return _deny(
			DenialCode.AUTH_SUPPLIER_INELIGIBLE.value,
			_("You cannot submit a bid for a different supplier account."),
		)

	if not frappe.db.exists("TM2 Supplier Participation", {"tm2_tender": tm2.name, "supplier": supplier}):
		return _deny(
			DenialCode.AUTH_SUPPLIER_INELIGIBLE.value,
			_("This supplier is not registered as a participant on this tender."),
		)

	_tl, deadline_at = _submission_deadline_row(tm2.name)
	if not deadline_at:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Submission deadline is not configured for this tender."),
		)
	if get_datetime(now_datetime()) > get_datetime(deadline_at):
		late_extra = persist_tm2_late_submission_rejection(
			actor,
			tm2_name=tm2.name,
			tender_code=tc,
			supplier=supplier,
			submission_deadline_at=deadline_at,
			bid_payload=bid_payload,
		)
		return _deny(
			DenialCode.AUTH_DEADLINE_PASSED.value,
			_("The submission deadline has passed."),
			extra={"submission_deadline_at": str(deadline_at), **late_extra},
		)

	pending = missing_required_addendum_acknowledgements(tm2.name, supplier)
	if pending:
		return _deny(
			DenialCode.AUTH_ADDENDUM_ACK_REQUIRED.value,
			_("Required addendum acknowledgement is missing for: {0}").format(", ".join(pending)),
			extra={"pending_addendum_codes": pending},
		)

	si = _active_std_instance(tm2.name)
	if not si:
		return _deny(
			DenialCode.AUTH_STD_NOT_READY.value,
			_("No active Tender STD binding is available for this tender."),
		)

	dsm = get_current_dsm(si)
	if not dsm.get("ok"):
		return _deny(
			DenialCode.AUTH_DSM_MISSING_OR_STALE.value,
			cstr(dsm.get("message") or _("Current DSM output is missing or not consumable.")).strip()
			or _("Current DSM output is missing or not consumable."),
			extra={
				"dsm_reason": dsm.get("reason"),
				"dsm_missing": dsm.get("missing"),
				"dsm_stale_or_invalid": dsm.get("stale_or_invalid"),
			},
		)

	dsm_code = cstr(dsm.get("output_code") or "").strip()
	if not dsm_code:
		return _deny(
			DenialCode.AUTH_DSM_MISSING_OR_STALE.value,
			_("Current DSM output code is not available."),
		)

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

	_bind_si, snap = _binding_snapshot(tm2.name)
	if not snap:
		return _deny(
			DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			_("Publication snapshot is not bound for this tender."),
		)

	for nm in frappe.get_all(
		"TM2 Bid Submission",
		filters={"tm2_tender": tm2.name, "supplier": supplier},
		pluck="name",
	):
		st = cstr(frappe.db.get_value("TM2 Bid Submission", nm, "bid_status") or "").strip()
		if st in _BLOCKING_PRIOR_BID_STATUSES:
			return _deny(
				DenialCode.AUTH_CONTEXT_DENIED.value,
				_("A bid submission already exists for this supplier on this tender."),
				extra={"existing_bid_submission": nm, "existing_bid_status": st},
			)

	return {
		"portal_ok": True,
		"tm2_name": tm2.name,
		"tc": tc,
		"supplier": supplier,
		"dsm_code": dsm_code,
		"si": si,
		"publication_snapshot_code": snap,
	}


def _insert_components_for_bid(
	bid_docname: str,
	dsm_json: dict[str, Any],
	bid_payload: dict[str, Any],
) -> None:
	reqs = dsm_json.get("requirements")
	if not isinstance(reqs, list):
		return
	allowed = frozenset(
		cstr(r.get("requirement_code") or "").strip()
		for r in reqs
		if isinstance(r, dict) and cstr(r.get("requirement_code") or "").strip()
	)
	bid_req = bid_payload.get("requirements")
	if not isinstance(bid_req, dict):
		bid_req = {}
	boq_lines = bid_payload.get("boq")
	if not isinstance(boq_lines, list):
		boq_lines = []

	for row in reqs:
		if not isinstance(row, dict) or not row.get("mandatory"):
			continue
		code = cstr(row.get("requirement_code") or "").strip()
		rt = cstr(row.get("requirement_type") or "").strip()
		if not code or rt in ("System",):
			continue
		if rt == "BOQRateEntry":
			entry = boq_lines
		else:
			entry = bid_req.get(code)
			if entry is None:
				continue
		ct = _component_type_for_requirement(rt, entry)
		submitted = 1
		file_ref = ""
		struct_ref = ""
		val_payload: dict[str, Any] = {"requirement_code": code, "requirement_type": rt}
		if rt == "BOQRateEntry":
			val_payload["boq_line_count"] = len(boq_lines)
			struct_ref = _sha256_hex(_canonical_json(boq_lines))[:120]
		elif isinstance(entry, dict):
			val_payload["keys"] = sorted(k for k in entry.keys())
			struct_ref = _sha256_hex(_canonical_json(entry))[:120]
			if ct == "FILE_SET":
				file_ref = cstr(entry.get("file_url") or entry.get("attachment_url") or "").strip()
		else:
			struct_ref = _sha256_hex(_canonical_json(entry))[:120]

		comp = frappe.get_doc(
			{
				"doctype": "TM2 Bid Submission Component",
				"tm2_bid_submission": bid_docname,
				"std_submission_requirement_code": code,
				"component_type": ct,
				"component_label": cstr(row.get("label") or code).strip() or code,
				"required": 1,
				"submitted": submitted,
				"file_ref": file_ref,
				"structured_payload_ref": struct_ref,
				"validation_status": "Passed",
				"validation_payload": val_payload,
			}
		)
		comp.flags.tm2_bsc_allowed_requirement_codes = allowed
		comp.insert(ignore_permissions=True)


def submit_bid(
	actor: str,
	tender_code: str,
	supplier_code: str,
	bid_payload: dict[str, Any] | None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §11.5 — validate, persist sealed **TM2 Bid Submission**, components, and receipt."""
	ctx = dict(context or {})
	raw_payload: dict[str, Any] = dict(bid_payload or {})

	gate = _portal_gate_submit(actor, tender_code, supplier_code, ctx, bid_payload=raw_payload)
	if not gate.get("portal_ok"):
		return {**gate, "actor": actor}

	tm2_name = str(gate["tm2_name"])
	tc = str(gate["tc"])
	supplier = str(gate["supplier"])
	dsm_code = str(gate["dsm_code"])
	si = str(gate["si"])
	pub_snap = str(gate["publication_snapshot_code"])

	val = validate_bid_submission_against_dsm(tc, supplier_code, raw_payload)
	if not val.get("ok"):
		return {**val, "actor": actor}

	dsm_json = _parse_dsm_json(dsm_code)
	if not dsm_json:
		return _deny(
			DenialCode.AUTH_DSM_MISSING_OR_STALE.value,
			_("Could not load DSM content for sealing."),
			extra={"actor": actor},
		)

	total, currency = _compute_total_and_currency(si, raw_payload, dsm_json)
	seal_bytes = _seal_envelope(raw_payload)
	submission_hash = _sha256_hex(seal_bytes)

	ack_snap = raw_payload.get("addendum_acknowledgements")
	if not isinstance(ack_snap, dict):
		ack_snap = {}

	bid = None
	rc = None
	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		bid = frappe.get_doc(
			{
				"doctype": "TM2 Bid Submission",
				"tm2_tender": tm2_name,
				"supplier": supplier,
				"dsm_output_code": dsm_code,
				"tender_std_instance_code": si,
				"publication_snapshot_code": pub_snap,
				"addendum_acknowledgement_snapshot": ack_snap,
				"bid_status": "Submitted",
				"submission_hash": submission_hash,
				"total_submitted_price": total,
				"currency": currency,
			}
		)
		bid.insert(ignore_permissions=True)
		bid.reload()
		append_tender_audit_event(
			tc,
			"Bid Submitted",
			actor,
			{
				"bid_code": bid.bid_code,
				"submission_hash": submission_hash,
				"total_submitted_price": total,
				"currency": currency,
			},
			related_object_type="TM2 Bid Submission",
			related_object_code=bid.name,
			enforce_section_13_2=False,
		)

		frappe.db.set_value("TM2 Bid Submission", bid.name, "bid_status", "Sealed", update_modified=False)
		append_tender_audit_event(
			tc,
			"Bid Sealed",
			actor,
			{"bid_code": bid.bid_code, "submission_hash": submission_hash},
			related_object_type="TM2 Bid Submission",
			related_object_code=bid.name,
			enforce_section_13_2=False,
		)

		_insert_components_for_bid(bid.name, dsm_json, raw_payload)

		rc_payload = {
			"tender_code": tc,
			"bid_code": bid.bid_code,
			"supplier": supplier,
			"dsm_output_code": dsm_code,
			"publication_snapshot_code": pub_snap,
			"submission_hash": submission_hash,
			"total_submitted_price": total,
			"currency": currency,
		}
		rc_hash = _sha256_hex(_canonical_json(rc_payload))
		rc = frappe.get_doc(
			{
				"doctype": "TM2 Bid Receipt",
				"tm2_bid_submission": bid.name,
				"receipt_type": "Submission",
				"receipt_payload": rc_payload,
				"receipt_hash": rc_hash,
			}
		)
		rc.insert(ignore_permissions=True)
	finally:
		frappe.set_user(prev_user)

	if not bid or not rc:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Bid submission could not be completed."),
			extra={"actor": actor},
		)

	return {
		"ok": True,
		"actor": actor,
		"tender_code": tc,
		"tm2_tender": tm2_name,
		"supplier": supplier,
		"bid_submission": bid.name,
		"bid_code": bid.bid_code,
		"bid_status": "Sealed",
		"receipt": rc.name,
		"receipt_code": rc.receipt_code,
		"submission_hash": submission_hash,
		"total_submitted_price": total,
		"currency": currency,
	}


def submitBid(
	actor: str,
	tender_code: str,
	supplier_code: str,
	bid_payload: dict[str, Any] | None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`submit_bid`."""
	return submit_bid(actor, tender_code, supplier_code, bid_payload, context=context)
