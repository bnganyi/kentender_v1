# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §11.6 — late submission rejection (``record_late_submission_attempt`` / ``recordLateSubmissionAttempt``).

When server time is after the submission deadline:

1. Do **not** create **TM2 Bid Submission**;
2. Create **TM2 Late Submission Attempt** (TM2-LATE-001/002/003);
3. Append audit **Late Submission Rejected** (``denial_code`` = ``AUTH_DEADLINE_PASSED``);
4. Callers (e.g. :func:`submit_bid`) return denial ``AUTH_DEADLINE_PASSED`` to the client.

The public API repeats the same **Published** + eligibility + participation + timeline gates as
:func:`~kentender_procurement.tender_management.services.submit_bid.submit_bid` up to the deadline
check, but does **not** require DSM, addendum acks, or **BID2_SUBMIT** — those apply only to on-time
submissions.

Tests: ``tender_management.tests.test_p6_06_record_late_submission_attempt`` (incl. doc 9 §25 **EX-14** ``test_EX_14_*``).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
)


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


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


def _safe_attempt_metadata(payload: dict[str, Any] | None) -> dict[str, Any]:
	if not isinstance(payload, dict) or not payload:
		return {}
	out: dict[str, Any] = {}
	for key in ("tender_std_instance_code", "dsm_output_code", "supplier"):
		v = payload.get(key)
		if v is not None and not isinstance(v, (dict, list)):
			s = cstr(v).strip()
			if s:
				out[key] = s
	req = payload.get("requirements")
	if isinstance(req, dict):
		out["requirement_codes_submitted"] = sorted(str(k) for k in req.keys())
	boq = payload.get("boq")
	if isinstance(boq, list):
		out["boq_line_count"] = len(boq)
	return out


def persist_tm2_late_submission_rejection(
	actor: str,
	*,
	tm2_name: str,
	tender_code: str,
	supplier: str,
	submission_deadline_at: Any,
	bid_payload: dict[str, Any] | None,
) -> dict[str, str]:
	"""Insert **TM2 Late Submission Attempt** + **Late Submission Rejected** audit (caller gates deadline)."""
	meta = _safe_attempt_metadata(bid_payload)
	reason = f"{DenialCode.AUTH_DEADLINE_PASSED.value}: submission deadline has passed."
	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		doc = frappe.get_doc(
			{
				"doctype": "TM2 Late Submission Attempt",
				"tm2_tender": tm2_name,
				"supplier": supplier,
				"submission_deadline_at": submission_deadline_at,
				"rejection_reason": reason,
				"attempted_payload_metadata": meta,
			}
		)
		doc.insert(ignore_permissions=True)
		doc.reload()
		append_tender_audit_event(
			tender_code,
			"Late Submission Rejected",
			actor,
			{
				"late_attempt_code": cstr(doc.late_attempt_code).strip(),
				"submission_deadline_at": str(submission_deadline_at),
			},
			related_object_type="TM2 Late Submission Attempt",
			related_object_code=doc.name,
			denial_code=DenialCode.AUTH_DEADLINE_PASSED.value,
			enforce_section_13_2=False,
		)
		return {"late_attempt": doc.name, "late_attempt_code": cstr(doc.late_attempt_code).strip()}
	finally:
		frappe.set_user(prev_user)


def record_late_submission_attempt(
	actor: str,
	tender_code: str,
	supplier_ref: str,
	context: dict[str, Any] | None = None,
	*,
	bid_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""§11.6 — record a late attempt when (and only when) server time is after the submission deadline."""
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
			_("Late submission recording requires a published tender."),
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
			_("You cannot record a late attempt for a different supplier account."),
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

	if get_datetime(now_datetime()) <= get_datetime(deadline_at):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("A late submission attempt can only be recorded after the submission deadline has passed."),
			extra={"submission_deadline_at": str(deadline_at)},
		)

	extra = persist_tm2_late_submission_rejection(
		actor,
		tm2_name=tm2.name,
		tender_code=tc,
		supplier=supplier,
		submission_deadline_at=deadline_at,
		bid_payload=bid_payload,
	)
	return {
		"ok": True,
		"recorded": True,
		"actor": actor,
		"tender_code": tc,
		"tm2_tender": tm2.name,
		"supplier": supplier,
		"denial_code": DenialCode.AUTH_DEADLINE_PASSED.value,
		"message": _("The submission deadline has passed."),
		**extra,
	}


def recordLateSubmissionAttempt(
	actor: str,
	tender_code: str,
	supplier_ref: str,
	context: dict[str, Any] | None = None,
	*,
	bid_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`record_late_submission_attempt`."""
	return record_late_submission_attempt(actor, tender_code, supplier_ref, context, bid_payload=bid_payload)
