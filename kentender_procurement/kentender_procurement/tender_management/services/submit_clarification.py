# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §10.1 — supplier submits a **TM2 Clarification Request**.

Preconditions: **TM2 Tender** status **Published**; **TM2 Tender Timeline** exists with a
``clarification_deadline_at`` and current time is on/before that deadline; **TM2 Supplier
Participation** for ``(tm2_tender, supplier)``; **TM2 Tender Access Rule** present;
:func:`get_action_availability` for ``CLR2_SUBMIT``.

Supplier **eligibility** (doc 9 §11.1) is enforced via
:func:`~kentender_procurement.tender_management.services.check_supplier_tender_access.check_supplier_tender_access`
(Supplier Management adapter); failures surface as ``AUTH_SUPPLIER_INELIGIBLE``.

``payload`` must include ``supplier`` (``Supplier`` name) and ``question_text``. Optional:
``related_std_section_code``, ``related_std_clause_ref``, ``related_boq_item_code``,
``attachment_refs`` (JSON-serializable dict).

When ``context["acting_supplier"]`` is set (portal gateway), it must equal ``payload["supplier"]``
or the call is denied with ``AUTH_SUPPLIER_INELIGIBLE``.

On success: insert **TM2 Clarification Request** (status **Submitted**); audit **Clarification Submitted**.

Tests: ``tender_management.tests.test_p5_01_submit_clarification``.
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
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
)

_ACTION = "CLR2_SUBMIT"
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


def _clarification_deadline_row(tm2_name: str) -> tuple[str | None, Any]:
	tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2_name}, "name")
	if not tl_name:
		return None, None
	deadline = frappe.db.get_value("TM2 Tender Timeline", tl_name, "clarification_deadline_at")
	return str(tl_name), deadline


def submit_clarification(
	actor: str,
	tender_code: str,
	payload: dict[str, Any] | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §10.1 — gated supplier clarification submission."""
	ctx = dict(context or ())
	raw = dict(payload or {})

	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st != "Published":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Clarifications can only be submitted while the tender is published."),
			extra={"tender_status": st},
		)

	if not frappe.db.exists("TM2 Tender Access Rule", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("TM2 Tender Access Rule is required before suppliers can submit clarifications."),
		)

	tl_name, deadline_at = _clarification_deadline_row(tm2.name)
	if not tl_name or not deadline_at:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Clarification deadline is not configured for this tender."),
		)
	if get_datetime(now_datetime()) > get_datetime(deadline_at):
		return _deny(
			DenialCode.AUTH_DEADLINE_PASSED.value,
			_("The clarification deadline has passed."),
			extra={"clarification_deadline_at": str(deadline_at)},
		)

	supplier = cstr(raw.get("supplier") or "").strip()
	if not supplier or not frappe.db.exists("Supplier", supplier):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("A valid supplier is required to submit a clarification."),
		)

	elig = check_supplier_tender_access(actor, tc, supplier, context=ctx)
	if not elig.get("ok"):
		return _deny(
			cstr(elig.get("denial_code") or DenialCode.AUTH_SUPPLIER_INELIGIBLE.value).strip()
			or DenialCode.AUTH_SUPPLIER_INELIGIBLE.value,
			cstr(elig.get("message") or _("Supplier is not eligible for this tender.")).strip()
			or _("Supplier is not eligible for this tender."),
			extra={"supplier_eligibility": elig.get("eligibility")},
		)

	acting = cstr(ctx.get("acting_supplier") or "").strip()
	if acting and acting != supplier:
		return _deny(
			DenialCode.AUTH_SUPPLIER_INELIGIBLE.value,
			_("You cannot submit a clarification for a different supplier account."),
		)

	if not frappe.db.exists("TM2 Supplier Participation", {"tm2_tender": tm2.name, "supplier": supplier}):
		return _deny(
			DenialCode.AUTH_SUPPLIER_INELIGIBLE.value,
			_("This supplier is not registered as a participant on this tender."),
		)

	question = cstr(raw.get("question_text") or "").strip()
	if not question:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Question text is required."),
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

	attachment_refs = raw.get("attachment_refs")
	if attachment_refs is not None and not isinstance(attachment_refs, dict):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("attachment_refs must be a JSON object when provided."),
		)

	doc_dict: dict[str, Any] = {
		"doctype": "TM2 Clarification Request",
		"tm2_tender": tm2.name,
		"supplier": supplier,
		"question_text": question,
		"status": "Submitted",
		"requires_addendum": 0,
	}
	for key in ("related_std_section_code", "related_std_clause_ref", "related_boq_item_code"):
		val = cstr(raw.get(key) or "").strip()
		if val:
			doc_dict[key] = val
	if isinstance(attachment_refs, dict):
		doc_dict["attachment_refs"] = attachment_refs

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		clr = frappe.get_doc(doc_dict)
		clr.insert(ignore_permissions=True)
		clr.reload()

		audit_payload = {
			"clarification_code": clr.clarification_code,
			"supplier": supplier,
			"supplier_code": cstr(clr.supplier_code or "").strip(),
			"question_preview": question[:500],
		}
		append_tender_audit_event(
			tc,
			"Clarification Submitted",
			actor,
			audit_payload,
			related_object_type="TM2 Clarification Request",
			related_object_code=clr.name,
			enforce_section_13_2=False,
		)

		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"clarification_request": clr.name,
			"clarification_code": clr.clarification_code,
			"status": clr.status,
		}
	except frappe.ValidationError as ex:
		msg = cstr(getattr(ex, "message", None) or str(ex)).strip() or _("Validation failed.")
		if "deadline" in msg.lower() or "tm2-clr-001" in msg.lower():
			return _deny(DenialCode.AUTH_DEADLINE_PASSED.value, msg)
		if "participation" in msg.lower() or "tm2-clr-002" in msg.lower():
			return _deny(DenialCode.AUTH_SUPPLIER_INELIGIBLE.value, msg)
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, msg)
	finally:
		frappe.set_user(prev_user)


def submitClarification(
	actor: str,
	tender_code: str,
	payload: dict[str, Any] | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`submit_clarification`."""
	return submit_clarification(actor, tender_code, payload=payload, context=context)
