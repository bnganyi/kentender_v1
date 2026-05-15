# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §10.2 — convert a **TM2 Clarification Request** to a **TM2 Addendum** (material path).

Governance (doc 4 §11.2 / TM2-CLR-GOV-006): use when the clarification **materially** changes the
tender (BOQ, deadlines, submission/opening/evaluation/contract model, scope / Works requirements).

**Material path (tracker P5-02):**

- ``context["primary_impact_type"]`` is **required** and must **not** be *No Structural Impact*
  (must match ``TM2 Addendum`` primary impact Select values).
- Clarification ``status`` must be **Under Review** or **Response Drafted**, **or** **Submitted**
  with ``requires_addendum`` set (officer pre-flag).

Preconditions: parent **TM2 Tender** in a state that allows new addenda (**Published**,
**Addendum Pending**, **Suspended Pending Addendum** per TM2-ADD-001); clarification not already
**Converted to Addendum**; non-empty ``reason`` (conversion / audit justification);
:func:`get_action_availability` for ``CLR2_CONVERT_TO_ADDENDUM``.

Optional ``context["title"]`` — defaults to a short title derived from the clarification code.

On success: insert **TM2 Addendum** (**Draft**, linked via ``tm2_source_clarification_request``);
set clarification **Converted to Addendum** and ``tm2_converted_addendum``; audit
**Clarification Converted to Addendum**.

Tests: ``tender_management.tests.test_p5_02_convert_clarification_to_addendum``.
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

_ACTION = "CLR2_CONVERT_TO_ADDENDUM"
_OBJECT_TYPE = "TM2 Tender"

# Must match ``TM2 Addendum`` Select (doc 3 / P1-11) — structural = anything except "No Structural Impact".
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

_ALLOWED_CLARIFICATION_STATUSES: frozenset[str] = frozenset({"Under Review", "Response Drafted"})

_TERMINAL_CLARIFICATION_STATUSES: frozenset[str] = frozenset(
	{"Rejected", "Converted to Addendum", "Withdrawn", "Published"}
)

_ALLOWED_TENDER_STATUSES_FOR_ADDENDUM: frozenset[str] = frozenset(
	{"Published", "Addendum Pending", "Suspended Pending Addendum"}
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


def _resolve_clarification(clarification_code: str) -> Document | None:
	cc = (clarification_code or "").strip()
	if not cc:
		return None
	name = frappe.db.get_value("TM2 Clarification Request", {"clarification_code": cc}, "name")
	if name and frappe.db.exists("TM2 Clarification Request", name):
		return frappe.get_doc("TM2 Clarification Request", name)
	if frappe.db.exists("TM2 Clarification Request", cc):
		return frappe.get_doc("TM2 Clarification Request", cc)
	return None


def convert_clarification_to_addendum(
	actor: str,
	clarification_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §10.2 — material clarification → **TM2 Addendum** draft + clarification terminal state."""
	ctx = dict(context or ())
	reason_s = cstr(reason or "").strip()
	if not reason_s:
		return _deny(
			DenialCode.AUTH_REASON_REQUIRED.value,
			_("A conversion reason is required."),
		)

	clr = _resolve_clarification(clarification_code)
	if not clr:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("Clarification {0} was not found.").format(frappe.bold((clarification_code or "").strip())),
		)

	ccode = cstr(clr.clarification_code or "").strip()
	st = cstr(clr.status or "").strip()
	if st in _TERMINAL_CLARIFICATION_STATUSES:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("This clarification cannot be converted in its current status."),
			extra={"clarification_status": st},
		)

	req_add = bool(int(clr.get("requires_addendum") or 0))
	if st not in _ALLOWED_CLARIFICATION_STATUSES and not (st == "Submitted" and req_add):
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_(
				"Conversion is only allowed for clarifications in Under Review or Response Drafted, "
				"or Submitted clarifications flagged as requiring an addendum (material path)."
			),
			extra={"clarification_status": st, "requires_addendum": int(req_add)},
		)

	if cstr(clr.tm2_converted_addendum or "").strip():
		return _deny(
			DenialCode.AUTH_LOCKED_RECORD.value,
			_("This clarification is already linked to an addendum."),
		)

	pit = cstr(ctx.get("primary_impact_type") or "").strip()
	if not pit or pit not in _PRIMARY_IMPACT_OPTIONS:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("context[\"primary_impact_type\"] must be a valid TM2 Addendum primary impact type."),
			extra={"primary_impact_type": pit},
		)
	if pit == "No Structural Impact":
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Material addendum path requires a structural primary_impact_type (not No Structural Impact)."),
		)

	tm2_name = cstr(clr.tm2_tender or "").strip()
	if not tm2_name or not frappe.db.exists("TM2 Tender", tm2_name):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Clarification is not linked to a TM2 Tender."),
		)

	tc = cstr(clr.tender_code or "").strip() or (
		frappe.db.get_value("TM2 Tender", tm2_name, "tender_code") or tm2_name
	)

	t_st = cstr(frappe.db.get_value("TM2 Tender", tm2_name, "status") or "").strip()
	if t_st not in _ALLOWED_TENDER_STATUSES_FOR_ADDENDUM:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Addendum conversion is not allowed for this tender status."),
			extra={"tender_status": t_st},
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

	title = cstr(ctx.get("title") or "").strip()
	if not title:
		title = _("Addendum from clarification {0}").format(ccode)

	add_doc: dict[str, Any] = {
		"doctype": "TM2 Addendum",
		"tm2_tender": tm2_name,
		"title": title,
		"reason": reason_s,
		"status": "Draft",
		"primary_impact_type": pit,
		"tm2_source_clarification_request": clr.name,
	}
	for flag in (
		"affects_deadline",
		"affects_submission_model",
		"affects_opening_model",
		"affects_evaluation_model",
		"affects_contract_model",
		"requires_supplier_acknowledgement",
	):
		if flag in ctx:
			try:
				add_doc[flag] = 1 if int(ctx.get(flag) or 0) else 0
			except (TypeError, ValueError):
				add_doc[flag] = 0

	prev_user = frappe.session.user
	add_name: str | None = None
	try:
		frappe.set_user(actor)
		add = frappe.get_doc(add_doc)
		add.insert(ignore_permissions=True)
		add_name = add.name
		add_code = cstr(add.addendum_code or "").strip()

		clr.reload()
		clr.status = "Converted to Addendum"
		clr.tm2_converted_addendum = add.name
		clr.save(ignore_permissions=True)

		append_tender_audit_event(
			tc,
			"Clarification Converted to Addendum",
			actor,
			{
				"clarification_code": ccode,
				"addendum_code": add_code,
				"conversion_reason": reason_s[:2000],
			},
			related_object_type="TM2 Clarification Request",
			related_object_code=clr.name,
			reason=reason_s,
			enforce_section_13_2=False,
		)

		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2_name,
			"clarification_code": ccode,
			"addendum": add.name,
			"addendum_code": add_code,
			"clarification_status": "Converted to Addendum",
		}
	except frappe.ValidationError as ex:
		msg = cstr(getattr(ex, "message", None) or str(ex)).strip() or _("Validation failed.")
		if add_name and frappe.db.exists("TM2 Addendum", add_name):
			frappe.delete_doc("TM2 Addendum", add_name, force=True, ignore_permissions=True)
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, msg)
	finally:
		frappe.set_user(prev_user)


def convertClarificationToAddendum(
	actor: str,
	clarification_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`convert_clarification_to_addendum`."""
	return convert_clarification_to_addendum(actor, clarification_code, reason, context=context)
