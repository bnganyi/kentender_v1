# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §11.2 — ``start_bid_draft`` / ``save_bid_draft`` (supplier bid draft lifecycle).

Preconditions for **start** (enforced in order where applicable):

1. **TM2 Tender** status **Published**;
2. supplier eligible (:func:`~kentender_procurement.tender_management.services.check_supplier_tender_access.check_supplier_tender_access`);
3. submission window open (``TM2 Tender Timeline.submission_deadline_at`` in the future);
4. current **DSM** resolvable via :func:`~kentender_procurement.tender_management.services.tm2_std_adapter.get_current_dsm`;
5. required **addendum acknowledgements** satisfied for **Issued** addenda with
   ``requires_supplier_acknowledgement``.

**TM2-SMOKE-SEC-001 / doc 11.2** — successful responses return **metadata handles only**
(``draft_metadata_code``, ``dsm_output_code``, links). They must not include bid draft
body, ``validation_summary`` JSON, or other supplier-fillable content.

``save_bid_draft`` bumps **TM2 Bid Draft Metadata** ``last_saved_at`` / ``draft_status``
for an existing draft row using the same actor / portal context pattern as **start**.

Tests: ``tender_management.tests.test_p6_02_start_bid_draft``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
)
from kentender_procurement.tender_management.services.tm2_addendum_acknowledgement_checks import (
	missing_required_addendum_acknowledgements,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import get_current_dsm

_ACTION_START = "BID2_START_DRAFT"
_ACTION_SAVE = "BID2_SAVE_DRAFT"
_OBJECT_TYPE = "TM2 Tender"


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


def _public_metadata_response(
	*,
	bdm_name: str,
	tender_code: str,
	tm2_tender: str,
	supplier: str,
	idempotent: bool = False,
) -> dict[str, Any]:
	"""Safe envelope — no ``validation_summary`` or other draft body (doc 11.2)."""
	draft_metadata_code, dsm_output_code = frappe.db.get_value(
		"TM2 Bid Draft Metadata",
		bdm_name,
		["draft_metadata_code", "dsm_output_code"],
	) or (None, None)
	return {
		"ok": True,
		"tender_code": tender_code,
		"tm2_tender": tm2_tender,
		"supplier": supplier,
		"bid_draft_metadata": bdm_name,
		"draft_metadata_code": cstr(draft_metadata_code or "").strip(),
		"dsm_output_code": cstr(dsm_output_code or "").strip(),
		"idempotent": bool(idempotent),
	}


def _portal_gate_bid_draft(
	actor: str,
	tender_code: str,
	supplier_ref: str,
	context: dict[str, Any],
	*,
	action_code: str,
) -> dict[str, Any]:
	"""Return ``portal_ok`` payload or a deny-shaped dict (``ok`` false)."""
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
			_("Bid draft operations require the tender to be published."),
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
			_("You cannot manage a bid draft for a different supplier account."),
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
		return _deny(
			DenialCode.AUTH_DEADLINE_PASSED.value,
			_("The submission deadline has passed."),
			extra={"submission_deadline_at": str(deadline_at)},
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
			extra={
				"dsm_reason": dsm.get("reason"),
				"dsm_missing": dsm.get("missing"),
				"dsm_stale_or_invalid": dsm.get("stale_or_invalid"),
			},
		)

	avail = get_action_availability(
		action_code,
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

	return {
		"portal_ok": True,
		"tm2_name": tm2.name,
		"tc": tc,
		"supplier": supplier,
		"dsm_code": dsm_code,
	}


def start_bid_draft(
	actor: str,
	tender_code: str,
	supplier_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §11.2 — create **TM2 Bid Draft Metadata** when allowed (metadata-only response)."""
	ctx = dict(context or {})
	gate = _portal_gate_bid_draft(actor, tender_code, supplier_code, ctx, action_code=_ACTION_START)
	if not gate.get("portal_ok"):
		return {**gate, "actor": actor}

	tm2_name = str(gate.get("tm2_name") or "")
	tc = str(gate.get("tc") or "")
	supplier = str(gate.get("supplier") or "")
	dsm_code = str(gate.get("dsm_code") or "")

	existing = frappe.db.get_value(
		"TM2 Bid Draft Metadata",
		{"tm2_tender": tm2_name, "supplier": supplier},
		"name",
	)
	if existing:
		return {**_public_metadata_response(
			bdm_name=str(existing),
			tender_code=tc,
			tm2_tender=tm2_name,
			supplier=supplier,
			idempotent=True,
		), "actor": actor}

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		bdm = frappe.get_doc(
			{
				"doctype": "TM2 Bid Draft Metadata",
				"tm2_tender": tm2_name,
				"supplier": supplier,
				"dsm_output_code": dsm_code,
				"draft_status": "Draft",
				"completeness_status": "Unknown",
			}
		)
		bdm.insert(ignore_permissions=True)
		bdm.reload()
	finally:
		frappe.set_user(prev_user)

	part = frappe.db.get_value(
		"TM2 Supplier Participation",
		{"tm2_tender": tm2_name, "supplier": supplier},
		"name",
	)
	if part:
		existing_started = frappe.db.get_value("TM2 Supplier Participation", part, "bid_draft_started_at")
		patch: dict[str, Any] = {"current_status": "Bid Draft Started"}
		if not existing_started:
			patch["bid_draft_started_at"] = now_datetime()
		frappe.db.set_value("TM2 Supplier Participation", part, patch, update_modified=False)

	out = _public_metadata_response(
		bdm_name=bdm.name,
		tender_code=tc,
		tm2_tender=tm2_name,
		supplier=supplier,
		idempotent=False,
	)
	out["actor"] = actor
	return out


def save_bid_draft(
	actor: str,
	tender_code: str,
	supplier_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §11.2 — mark draft **Saved** (metadata-only response; no draft body in API)."""
	ctx = dict(context or {})
	gate = _portal_gate_bid_draft(actor, tender_code, supplier_code, ctx, action_code=_ACTION_SAVE)
	if not gate.get("portal_ok"):
		return {**gate, "actor": actor}

	tm2_name = str(gate.get("tm2_name") or "")
	tc = str(gate.get("tc") or "")
	supplier = str(gate.get("supplier") or "")

	bdm_name = frappe.db.get_value(
		"TM2 Bid Draft Metadata",
		{"tm2_tender": tm2_name, "supplier": supplier},
		"name",
	)
	if not bdm_name:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Start a bid draft before saving."),
		)

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		bdm = frappe.get_doc("TM2 Bid Draft Metadata", bdm_name)
		bdm.draft_status = "Saved"
		bdm.save(ignore_permissions=True)
	finally:
		frappe.set_user(prev_user)

	out = _public_metadata_response(
		bdm_name=str(bdm_name),
		tender_code=tc,
		tm2_tender=tm2_name,
		supplier=supplier,
		idempotent=True,
	)
	out["actor"] = actor
	return out


def startBidDraft(
	actor: str,
	tender_code: str,
	supplier_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`start_bid_draft`."""
	return start_bid_draft(actor, tender_code, supplier_code, context=context)


def saveBidDraft(
	actor: str,
	tender_code: str,
	supplier_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`save_bid_draft`."""
	return save_bid_draft(actor, tender_code, supplier_code, context=context)
