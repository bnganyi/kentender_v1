# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 4 — governed **cancel**, **mark retender required**, and **supersede** for TM2 Tender.

No ad-hoc ``status`` writes outside these services: availability via
:func:`get_action_availability`, mandatory ``reason``, ``TM2 Tender Access Rule``,
and append-only audit rows (**Tender Cancelled**, **Retender Required**, **Tender Superseded**).

Tests: ``tender_management.tests.test_p4_08_cancel_supersede_retender``.
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
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)

_OBJECT_TYPE = "TM2 Tender"

_ACTION_CANCEL = "TND2_CANCEL"
_ACTION_MARK_RETENDER = "TND2_MARK_RETENDER_REQUIRED"
_ACTION_SUPERSEDE = "TND2_SUPERSEDE"

_FORBIDDEN_CANCEL_STATUSES = frozenset({"Cancelled", "Superseded", "Archived"})
_MARK_RETENDER_ALLOWED_FROM = frozenset({"Closed - No Valid Submissions", "Cancelled"})
_SUPERSEDE_ALLOWED_FROM = frozenset(
	{
		"Published",
		"Addendum Pending",
		"Suspended Pending Addendum",
		"Cancelled",
	}
)
_REPLACEMENT_ALLOWED_STATUSES = frozenset({"Draft", "STD Instance Incomplete"})


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _norm_reason(reason: str) -> tuple[str | None, dict[str, Any] | None]:
	rs = cstr(reason or "").strip()
	if not rs:
		return None, _deny(DenialCode.AUTH_REASON_REQUIRED.value, _("A reason is required."))
	if len(rs) > 4000:
		rs = rs[:4000]
	return rs, None


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


def _require_access_rule(tm2_name: str) -> dict[str, Any] | None:
	if not frappe.db.exists("TM2 Tender Access Rule", {"tm2_tender": tm2_name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("TM2 Tender Access Rule is required."),
		)
	return None


def _auth_gate(
	action: str,
	tender_code: str,
	actor: str,
	ctx: dict[str, Any],
) -> dict[str, Any] | None:
	avail = get_action_availability(
		action,
		_OBJECT_TYPE,
		tender_code,
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
	return None


def cancel_tender(
	actor: str,
	tender_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Transition TM2 Tender to **Cancelled** with audit and cancellation lineage fields."""
	ctx = dict(context or ())
	rs, err = _norm_reason(reason)
	if err:
		return err

	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st in _FORBIDDEN_CANCEL_STATUSES:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender status does not allow cancellation."),
			extra={"tender_status": st},
		)

	if gate := _require_access_rule(tm2.name):
		return gate
	if gate := _auth_gate(_ACTION_CANCEL, tc, actor, ctx):
		return gate

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		frappe.db.set_value(
			"TM2 Tender",
			tm2.name,
			{
				"status": "Cancelled",
				"is_active": 0,
				"cancelled_by": actor if frappe.db.exists("User", actor) else None,
				"cancelled_at": now_datetime(),
				"cancellation_reason": rs,
			},
			update_modified=True,
		)
		append_tender_audit_event(
			tc,
			"Tender Cancelled",
			actor,
			{"cancellation_reason": rs, "prior_status": st},
			previous_state=st,
			new_state="Cancelled",
			reason=rs,
			enforce_section_13_2=False,
		)
		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"status": "Cancelled",
			"reason": rs,
		}
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def mark_retender_required(
	actor: str,
	tender_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Mark tender **Retender Required** from closed-no-bids or cancelled (doc 4 matrix)."""
	ctx = dict(context or ())
	rs, err = _norm_reason(reason)
	if err:
		return err

	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st == "Retender Required":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender is already marked retender required."),
			extra={"tender_status": st},
		)
	if st not in _MARK_RETENDER_ALLOWED_FROM:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender status does not allow marking retender required."),
			extra={"tender_status": st},
		)

	if gate := _require_access_rule(tm2.name):
		return gate
	if gate := _auth_gate(_ACTION_MARK_RETENDER, tc, actor, ctx):
		return gate

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		frappe.db.set_value(
			"TM2 Tender",
			tm2.name,
			{"status": "Retender Required", "is_active": 0},
			update_modified=True,
		)
		append_tender_audit_event(
			tc,
			"Retender Required",
			actor,
			{"retender_reason": rs, "prior_status": st},
			previous_state=st,
			new_state="Retender Required",
			reason=rs,
			enforce_section_13_2=False,
		)
		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"status": "Retender Required",
			"reason": rs,
		}
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def supersede_tender(
	actor: str,
	tender_code: str,
	replacement_tender_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Mark the subject tender **Superseded**; replacement must be same package (draft path)."""
	ctx = dict(context or ())
	rs, err = _norm_reason(reason)
	if err:
		return err

	rep_code_in = cstr(replacement_tender_code or "").strip()
	if not rep_code_in:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Replacement tender code is required."),
		)

	old = _resolve_tm2(tender_code)
	if not old:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	repl = _resolve_tm2(rep_code_in)
	if not repl:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("Replacement TM2 Tender {0} was not found.").format(rep_code_in),
		)

	old_tc = cstr(old.tender_code).strip() or old.name
	rep_tc = cstr(repl.tender_code).strip() or repl.name
	if old_tc == rep_tc:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("A tender cannot supersede itself."),
		)

	old_st = cstr(old.status).strip()
	if old_st in {"Superseded", "Archived"}:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender status does not allow supersede."),
			extra={"tender_status": old_st},
		)
	if old_st not in _SUPERSEDE_ALLOWED_FROM:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender status does not allow supersede."),
			extra={"tender_status": old_st},
		)

	rep_st = cstr(repl.status).strip()
	if rep_st not in _REPLACEMENT_ALLOWED_STATUSES:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Replacement tender must be in Draft or STD Instance Incomplete."),
			extra={"replacement_status": rep_st},
		)

	pkg_old = cstr(old.procurement_package or "").strip()
	pkg_rep = cstr(repl.procurement_package or "").strip()
	if not pkg_old or pkg_old != pkg_rep:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Replacement tender must belong to the same procurement package."),
		)

	existing_sup = cstr(repl.supersedes_tender_code or "").strip()
	if existing_sup and existing_sup != old_tc:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Replacement tender supersedes a different prior tender."),
		)

	if gate := _require_access_rule(old.name):
		return gate
	if gate := _require_access_rule(repl.name):
		return gate
	if gate := _auth_gate(_ACTION_SUPERSEDE, old_tc, actor, ctx):
		return gate

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		frappe.db.set_value(
			"TM2 Tender",
			old.name,
			{"status": "Superseded", "is_active": 0},
			update_modified=True,
		)
		if not existing_sup:
			frappe.db.set_value(
				"TM2 Tender",
				repl.name,
				{"supersedes_tender_code": old_tc},
				update_modified=True,
			)
		append_tender_audit_event(
			old_tc,
			"Tender Superseded",
			actor,
			{
				"supersede_reason": rs,
				"prior_status": old_st,
				"superseded_tender_code": old_tc,
				"replacement_tender_code": rep_tc,
			},
			previous_state=old_st,
			new_state="Superseded",
			reason=rs,
			enforce_section_13_2=False,
		)
		return {
			"ok": True,
			"tender_code": old_tc,
			"tm2_tender": old.name,
			"status": "Superseded",
			"replacement_tender_code": rep_tc,
			"reason": rs,
		}
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def cancelTender(
	actor: str,
	tender_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`cancel_tender`."""
	return cancel_tender(actor, tender_code, reason, context=context)


def markRetenderRequired(
	actor: str,
	tender_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`mark_retender_required`."""
	return mark_retender_required(actor, tender_code, reason, context=context)


def supersedeTender(
	actor: str,
	tender_code: str,
	replacement_tender_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`supersede_tender`."""
	return supersede_tender(actor, tender_code, replacement_tender_code, reason, context=context)
