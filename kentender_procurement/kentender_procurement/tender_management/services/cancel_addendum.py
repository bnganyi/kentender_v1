# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 4 §12 / pack **P5-06** — governed **cancel** of a **TM2 Addendum** (not issued).

1. :func:`get_action_availability` for ``ADD2_CANCEL``;
2. addendum must exist and **not** be in a terminal workflow state (**Issued**, **Cancelled**,
   **Superseded**, **Withdrawn**);
3. non-whitespace ``cancellation_reason`` (``payload[\"cancellation_reason\"]`` or
   ``payload[\"reason\"]``);
4. set **TM2 Addendum** **Cancelled** + ``cancellation_reason`` (controller stamps
   ``cancelled_by`` / ``cancelled_at``);
5. audit **Addendum Cancelled** on **TM2 Tender Audit Event**.

Tests: ``tender_management.tests.test_p5_06_cancel_addendum``.
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

_ACTION = "ADD2_CANCEL"
_OBJECT_TYPE = "TM2 Tender"

_NO_CANCEL_FROM: frozenset[str] = frozenset({"Issued", "Cancelled", "Superseded", "Withdrawn"})


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _resolve_addendum(addendum_code: str) -> Document | None:
	ac = (addendum_code or "").strip()
	if not ac:
		return None
	name = frappe.db.get_value("TM2 Addendum", {"addendum_code": ac}, "name")
	if name and frappe.db.exists("TM2 Addendum", name):
		return frappe.get_doc("TM2 Addendum", name)
	if frappe.db.exists("TM2 Addendum", ac):
		return frappe.get_doc("TM2 Addendum", ac)
	return None


def _cancellation_reason(payload: dict[str, Any] | None) -> str:
	raw = dict(payload or "")
	return cstr(raw.get("cancellation_reason") or raw.get("reason") or "").strip()


def cancel_addendum(
	actor: str,
	addendum_code: str,
	payload: dict[str, Any] | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Governed cancel of a **TM2 Addendum** that has **not** been issued."""
	ctx = dict(context or {})
	ad = _resolve_addendum(addendum_code)
	if not ad:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Addendum {0} was not found.").format((addendum_code or "").strip()),
		)

	ac = cstr(ad.addendum_code or "").strip()
	st = cstr(ad.status or "").strip()
	if st in _NO_CANCEL_FROM:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("This addendum cannot be cancelled from its current status."),
			extra={"addendum_status": st},
		)

	reason = _cancellation_reason(payload)
	if not reason:
		return _deny(
			DenialCode.AUTH_REASON_REQUIRED.value,
			_("A cancellation reason is required."),
		)

	tc = cstr(ad.tender_code or "").strip()
	if not tc:
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, _("Addendum is missing tender_code."))

	tm2_name = cstr(ad.tm2_tender or "").strip()
	if not tm2_name:
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, _("Addendum is missing tm2_tender."))

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

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		adc = frappe.get_doc("TM2 Addendum", ad.name)
		adc.status = "Cancelled"
		adc.cancellation_reason = reason
		adc.save(ignore_permissions=True)

		append_tender_audit_event(
			tc,
			"Addendum Cancelled",
			actor,
			{"addendum_code": ac, "cancellation_reason": reason},
			related_object_type="TM2 Addendum",
			related_object_code=adc.name,
			reason=reason,
			enforce_section_13_2=False,
		)

		return {
			"ok": True,
			"addendum_code": ac,
			"tm2_addendum": adc.name,
			"tender_code": tc,
			"addendum_status": "Cancelled",
		}
	except frappe.ValidationError as ex:
		msg = cstr(getattr(ex, "message", None) or str(ex)).strip() or _("Validation failed.")
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, msg)
	finally:
		frappe.set_user(prev_user)


def cancelAddendum(
	actor: str,
	addendum_code: str,
	payload: dict[str, Any] | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`cancel_addendum`."""
	return cancel_addendum(actor, addendum_code, payload=payload, context=context)
