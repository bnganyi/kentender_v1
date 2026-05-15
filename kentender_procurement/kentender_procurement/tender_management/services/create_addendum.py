# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §10.3 — create a **TM2 Addendum** in **Draft** (officer-initiated).

Required ``payload`` keys: ``title``, ``reason`` (non-whitespace), ``primary_impact_type`` (must match
``TM2 Addendum`` Select options).

Optional: ``tm2_source_clarification_request`` (``TM2 Clarification Request`` name on the **same**
tender); ``proposed_changes`` (JSON-serializable dict — stored on the **audit** ``event_payload`` only
until a dedicated DocType field exists); optional boolean impact flags in ``payload`` or ``context``
(``affects_deadline``, ``affects_submission_model``, …).

Preconditions: **TM2 Tender** status **Published**, **Addendum Pending**, or **Suspended Pending Addendum**
(TM2-ADD-001); :func:`get_action_availability` for ``ADD2_CREATE``.

On success: insert **TM2 Addendum** (**Draft**); audit **Addendum Created**.

Tests: ``tender_management.tests.test_p5_03_create_addendum``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)

_ACTION = "ADD2_CREATE"
_OBJECT_TYPE = "TM2 Tender"

_PRIMARY_IMPACT_OPTIONS: frozenset[str] = frozenset(
	{
		"No Structural Impact",
		"Parameter Change",
		"Deadline Change",
		"Works Requirement Change",
		"BOQ Change",
		"Submission Model Change",
		"Opening Model Change",
		"Evaluation Model Change",
		"Contract Carry-Forward Change",
		"Cancellation / Reissue Required",
	}
)

_ALLOWED_TENDER_STATUSES_FOR_NEW_ADDENDUM: frozenset[str] = frozenset(
	{"Published", "Addendum Pending", "Suspended Pending Addendum"}
)

_IMPACT_FLAGS: tuple[str, ...] = (
	"affects_deadline",
	"affects_submission_model",
	"affects_opening_model",
	"affects_evaluation_model",
	"affects_contract_model",
	"requires_supplier_acknowledgement",
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


def create_addendum(
	actor: str,
	tender_code: str,
	payload: dict[str, Any] | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §10.3 — gated **Draft** ``TM2 Addendum`` insert."""
	ctx = dict(context or ())
	raw = dict(payload or {})

	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	t_st = cstr(tm2.status or "").strip()
	if t_st not in _ALLOWED_TENDER_STATUSES_FOR_NEW_ADDENDUM:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Addenda can only be created when the tender is Published, Addendum Pending, or Suspended Pending Addendum."),
			extra={"tender_status": t_st},
		)

	title = cstr(raw.get("title") or "").strip()
	if not title:
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, _("Addendum title is required."))

	reason = cstr(raw.get("reason") or "").strip()
	if not reason:
		return _deny(DenialCode.AUTH_REASON_REQUIRED.value, _("Addendum reason is required."))

	pit = cstr(raw.get("primary_impact_type") or "").strip()
	if not pit or pit not in _PRIMARY_IMPACT_OPTIONS:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("payload[\"primary_impact_type\"] must be a valid TM2 Addendum primary impact type."),
			extra={"primary_impact_type": pit},
		)

	proposed = raw.get("proposed_changes")
	if proposed is not None and not isinstance(proposed, dict):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("proposed_changes must be a JSON object when provided."),
		)

	src_clr = cstr(raw.get("tm2_source_clarification_request") or "").strip()
	if src_clr:
		if not frappe.db.exists("TM2 Clarification Request", src_clr):
			return _deny(
				DenialCode.AUTH_CONTEXT_DENIED.value,
				_("Source clarification request was not found."),
			)
		clr_tender = frappe.db.get_value("TM2 Clarification Request", src_clr, "tm2_tender")
		if cstr(clr_tender or "").strip() != tm2.name:
			return _deny(
				DenialCode.AUTH_CONTEXT_DENIED.value,
				_("Source clarification request does not belong to this tender."),
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

	add_doc: dict[str, Any] = {
		"doctype": "TM2 Addendum",
		"tm2_tender": tm2.name,
		"title": title,
		"reason": reason,
		"status": "Draft",
		"primary_impact_type": pit,
	}
	if src_clr:
		add_doc["tm2_source_clarification_request"] = src_clr

	merged = {**raw, **ctx}
	for flag in _IMPACT_FLAGS:
		if flag in merged:
			try:
				add_doc[flag] = 1 if int(merged.get(flag) or 0) else 0
			except (TypeError, ValueError):
				add_doc[flag] = 0

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		add = frappe.get_doc(add_doc)
		add.insert(ignore_permissions=True)
		add.reload()
		add_code = cstr(add.addendum_code or "").strip()

		audit_payload: dict[str, Any] = {
			"addendum_code": add_code,
			"title": title,
			"primary_impact_type": pit,
		}
		if isinstance(proposed, dict):
			audit_payload["proposed_changes"] = proposed
		if src_clr:
			audit_payload["tm2_source_clarification_request"] = src_clr

		append_tender_audit_event(
			tc,
			"Addendum Created",
			actor,
			audit_payload,
			related_object_type="TM2 Addendum",
			related_object_code=add.name,
			enforce_section_13_2=False,
		)

		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"addendum": add.name,
			"addendum_code": add_code,
			"status": add.status,
		}
	except frappe.ValidationError as ex:
		msg = cstr(getattr(ex, "message", None) or str(ex)).strip() or _("Validation failed.")
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, msg)
	finally:
		frappe.set_user(prev_user)


def createAddendum(
	actor: str,
	tender_code: str,
	payload: dict[str, Any] | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`create_addendum`."""
	return create_addendum(actor, tender_code, payload=payload, context=context)
