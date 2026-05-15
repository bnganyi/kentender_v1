# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §12.2 — ``prepare_opening_readiness`` / ``prepareOpeningReadiness``.

Preconditions:

1. **TM2 Tender** status **Closed** (not **Closed - No Valid Submissions**);
2. **TM2 Tender Closing Record** exists;
3. Valid submissions exist and **remain Sealed** (same bid-status family as §12.1 counts,
   but each counted row must still be **Sealed**);
4. **DOM** exists (consumable current output) and aligns with **publication snapshot V2**
   (active binding ``publication_snapshot_code`` matches :func:`get_tender_std_output_refs`;
   live DOM ``output_code`` matches snapshot ``dom_output_code``);
5. :func:`~kentender_procurement.tender_management.security.action_availability.service.get_action_availability`
   for **OR2_PREPARE_OPENING_READINESS**.

On success:

1. Insert **TM2 Opening Readiness Record** (``ORR-{tender_code}``, refs-only handoff JSON);
2. Set tender **Opening Ready**;
3. Audit **Opening Readiness Created** (metadata only — no sealed bid bodies).

Tests: ``tender_management.tests.test_p7_02_prepare_opening_readiness``.
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
	get_current_dom,
	get_tender_std_output_refs,
)

_ACTION = "OR2_PREPARE_OPENING_READINESS"
_OBJECT_TYPE = "TM2 Tender"

_VALID_SUBMISSION_BID_STATUSES: frozenset[str] = frozenset(
	{
		"Submitted",
		"Sealed",
		"Opened",
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


def _active_binding_row(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Tender STD Binding",
		filters={
			"tm2_tender": tm2_name,
			"is_active": 1,
			"binding_status": ["not in", ["Cancelled", "Superseded"]],
		},
		fields=["name", "tender_std_instance", "publication_snapshot_code", "dom_output_code"],
		limit=1,
	)
	return dict(rows[0]) if rows else None


def _valid_sealed_bid_codes(tm2_name: str) -> tuple[list[str], str | None]:
	"""Bid codes for submissions counted as valid for closing, each must still be **Sealed**."""
	codes: list[str] = []
	for row in frappe.get_all(
		"TM2 Bid Submission",
		filters={"tm2_tender": tm2_name},
		fields=["bid_code", "bid_status"],
		order_by="bid_code asc",
	):
		st = cstr(row.bid_status).strip()
		if st not in _VALID_SUBMISSION_BID_STATUSES:
			continue
		if st != "Sealed":
			return [], "unsealed"
		bc = cstr(row.bid_code).strip()
		if bc:
			codes.append(bc)
	return sorted(codes), None


def prepare_opening_readiness(
	actor: str,
	tender_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""§12.2 — build **TM2 Opening Readiness Record** after closure; transition to **Opening Ready**."""
	ctx = dict(context or {})
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format(cstr(tender_code).strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()

	if frappe.db.exists("TM2 Opening Readiness Record", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Opening readiness has already been prepared for this tender."),
		)

	if st != "Closed":
		if st == "Closed - No Valid Submissions":
			return _deny(
				DenialCode.AUTH_STATE_DENIED.value,
				_("Opening readiness requires at least one valid sealed submission."),
				extra={"tender_status": st},
			)
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Opening readiness requires the tender to be closed with valid submissions."),
			extra={"tender_status": st},
		)

	cl_name = frappe.db.get_value("TM2 Tender Closing Record", {"tm2_tender": tm2.name}, "name")
	if not cl_name:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("TM2 Tender Closing Record is required."),
		)
	cl = frappe.get_doc("TM2 Tender Closing Record", cl_name)
	cl_valid = int(cl.valid_submission_count or 0)
	if cl_valid <= 0:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Opening readiness requires at least one valid submission on the closing record."),
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

	dom_live = get_current_dom(si)
	if not dom_live.get("ok"):
		return _deny(
			DenialCode.AUTH_DOM_MISSING_OR_STALE.value,
			str(dom_live.get("message") or _("DOM is missing or not consumable.")),
			extra={"dom_resolution": dom_live},
		)
	dom_code = cstr(dom_live.get("output_code") or "").strip()
	snap_dom = cstr(refs.get("dom_output_code") or "").strip()
	if not dom_code or dom_code != snap_dom:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("DOM output does not match the publication snapshot binding."),
			extra={"dom_output_code": dom_code, "snapshot_dom_output_code": snap_dom},
		)

	sealed_codes, seal_issue = _valid_sealed_bid_codes(tm2.name)
	if seal_issue == "unsealed":
		return _deny(
			DenialCode.AUTH_SEALED_BID_DENIED.value,
			_("All valid submissions must remain sealed before opening readiness can be prepared."),
		)
	if not sealed_codes:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("No sealed bid submissions were found for this tender."),
		)
	if len(sealed_codes) != cl_valid:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Live sealed submission count does not match the tender closing record."),
			extra={"closing_valid_submission_count": cl_valid, "live_sealed_count": len(sealed_codes)},
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

	now = now_datetime()
	orr = frappe.get_doc(
		{
			"doctype": "TM2 Opening Readiness Record",
			"tm2_tender": tm2.name,
			"tender_code": tc,
			"tm2_tender_closing_record": cl_name,
			"dom_output_code": dom_code,
			"tender_std_instance_code": si,
			"sealed_submission_refs": {"refs": sealed_codes},
			"valid_submission_count": len(sealed_codes),
			"readiness_status": "Ready",
			"prepared_by": actor,
			"prepared_at": now,
		}
	)
	orr.insert(ignore_permissions=True)
	orr.reload()

	frappe.db.set_value("TM2 Tender", tm2.name, {"status": "Opening Ready"}, update_modified=True)

	audit_payload = {
		"tender_code": tc,
		"opening_readiness_code": orr.opening_readiness_code,
		"tm2_opening_readiness_record": orr.name,
		"tm2_tender_closing_record": cl_name,
		"dom_output_code": dom_code,
		"publication_snapshot_code": snap_pub,
		"valid_submission_count": len(sealed_codes),
		"sealed_submission_ref_count": len(sealed_codes),
		"tender_std_instance_code": si,
	}
	append_tender_audit_event(
		tc,
		"Opening Readiness Created",
		actor,
		audit_payload,
		related_object_type="TM2 Opening Readiness Record",
		related_object_code=orr.name,
		previous_state="Closed",
		new_state="Opening Ready",
		enforce_section_13_2=False,
	)

	return {
		"ok": True,
		"actor": actor,
		"tender_code": tc,
		"tm2_tender": tm2.name,
		"tender_status": "Opening Ready",
		"tm2_opening_readiness_record": orr.name,
		"opening_readiness_code": orr.opening_readiness_code,
		"dom_output_code": dom_code,
		"publication_snapshot_code": snap_pub,
		"valid_submission_count": len(sealed_codes),
		"sealed_submission_refs": {"refs": sealed_codes},
	}


def prepareOpeningReadiness(
	actor: str,
	tender_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`prepare_opening_readiness`."""
	return prepare_opening_readiness(actor, tender_code, context=context)
