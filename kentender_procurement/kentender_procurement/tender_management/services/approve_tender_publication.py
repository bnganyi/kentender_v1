# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §9.5 — approve tender publication (**TM2 Tender**).

Preconditions: status **Ready for Publication Review**; latest **TM2 Publication Readiness**
still **Ready** with outputs current and ``timeline_valid`` (same gate as §9.4 submit);
active binding matches that row; :func:`get_action_availability` for
``TND2_APPROVE_PUBLICATION``; **separation of duties** (doc 5 TM2-SOD-001 / tracker): approver
must not be the tender **creator** nor the **submitter for review**, unless
``context`` carries an explicit delegated override reason (see
``sod_delegated_override_reason``).

On success: ``status`` → **Approved for Publication**; ``approved_for_publication_by`` /
``approved_for_publication_at``; audit **Tender Approved for Publication**.

Tests: ``tender_management.tests.test_p4_05_approve_tender_publication``.
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
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	_OUTPUT_FLAG_DENIALS,
	_active_std_binding,
	_latest_publication_readiness,
	_resolve_tm2,
	_truthy,
)

_ACTION = "TND2_APPROVE_PUBLICATION"
_OBJECT_TYPE = "TM2 Tender"
_REQUIRED_STATUS = "Ready for Publication Review"


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _sod_override_reason(ctx: dict[str, Any]) -> str:
	for key in (
		"sod_delegated_override_reason",
		"sod_override_reason",
		"separation_of_duties_override_reason",
	):
		r = cstr(ctx.get(key) or "").strip()
		if r:
			return r[:500]
	return ""


def _separation_of_duties_denial(tm2: Document, actor: str, ctx: dict[str, Any]) -> dict[str, Any] | None:
	"""Return a deny dict if SoD fails, else ``None``."""
	ov = _sod_override_reason(ctx)
	if ov:
		return None
	act = cstr(actor).strip()
	creator = cstr(getattr(tm2, "created_by_user", None) or "").strip()
	if creator and creator == act:
		return _deny(
			DenialCode.AUTH_SOD_DENIED.value,
			_("Approver cannot be the tender creator without a delegated separation-of-duties override."),
			extra={"sod_rule": "TM2-SOD-001", "sod_dimension": "creator"},
		)
	submitter = cstr(
		frappe.db.get_value("TM2 Tender", tm2.name, "submitted_for_review_by") or ""
	).strip()
	if submitter and submitter == act:
		return _deny(
			DenialCode.AUTH_SOD_DENIED.value,
			_("Approver cannot be the same user who submitted this tender for publication review."),
			extra={"sod_rule": "TM2-SOD-001", "sod_dimension": "submitter"},
		)
	return None


def _readiness_still_valid_denial(tm2_name: str, bind: Document) -> dict[str, Any] | None:
	read_row = _latest_publication_readiness(tm2_name)
	if not read_row:
		return _deny(
			DenialCode.AUTH_STD_NOT_READY.value,
			_("No publication readiness run exists."),
		)
	if cstr(read_row.get("readiness_status")).strip() != "Ready":
		return _deny(
			DenialCode.AUTH_STD_NOT_READY.value,
			_("Latest publication readiness is not Ready."),
			extra={"tm2_publication_readiness": read_row.get("name"), "readiness_status": read_row.get("readiness_status")},
		)
	if cstr(read_row.get("tm2_tender_std_binding") or "").strip() != bind.name:
		return _deny(
			DenialCode.AUTH_STD_NOT_READY.value,
			_("Latest publication readiness does not match the active STD binding."),
			extra={"tm2_publication_readiness": read_row.get("name"), "active_binding": bind.name},
		)
	if not _truthy(read_row.get("timeline_valid")):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Timeline is not valid on the latest publication readiness run."),
			extra={"tm2_publication_readiness": read_row.get("name")},
		)
	for field, denial in _OUTPUT_FLAG_DENIALS:
		if not _truthy(read_row.get(field)):
			return _deny(
				denial.value,
				_("{0} is not current on the latest publication readiness run.").format(field.replace("_", " ").title()),
				extra={"tm2_publication_readiness": read_row.get("name"), "field": field},
			)
	return None  # gate passed


def approve_tender_publication(
	actor: str,
	tender_code: str,
	comments: str | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §9.5 — permission, SoD, readiness, then **Approved for Publication** + audit."""
	ctx = dict(context or ())
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st != _REQUIRED_STATUS:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender must be Ready for Publication Review to approve publication."),
			extra={"tender_status": st},
		)

	if not frappe.db.exists("TM2 Tender Access Rule", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("TM2 Tender Access Rule is required before approval."),
		)

	bind = _active_std_binding(tm2.name)
	if not bind:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("No active TM2 Tender STD Binding exists for this tender."),
		)

	rd = _readiness_still_valid_denial(tm2.name, bind)
	if rd:
		return rd

	sod = _separation_of_duties_denial(tm2, actor, ctx)
	if sod:
		return sod

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

	read_row = _latest_publication_readiness(tm2.name) or {}
	pr_name = cstr(read_row.get("name") or "").strip()
	pr_code = cstr(read_row.get("readiness_code") or "").strip()
	now = now_datetime()
	com = cstr(comments or "").strip() or None
	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		frappe.db.set_value(
			"TM2 Tender",
			tm2.name,
			{
				"status": "Approved for Publication",
				"approved_for_publication_by": actor if frappe.db.exists("User", actor) else None,
				"approved_for_publication_at": now,
			},
			update_modified=True,
		)
		audit_payload: dict[str, Any] = {
			"tm2_publication_readiness": pr_name,
			"readiness_code": pr_code,
			"prior_status": st,
		}
		if com:
			audit_payload["approval_comments"] = com
		sov = _sod_override_reason(ctx)
		if sov:
			audit_payload["sod_delegated_override_reason"] = sov
		append_tender_audit_event(
			tc,
			"Tender Approved for Publication",
			actor,
			audit_payload,
			related_object_type="TM2 Publication Readiness",
			related_object_code=pr_name,
			previous_state=st,
			new_state="Approved for Publication",
			enforce_section_13_2=False,
		)
		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"tm2_publication_readiness": pr_name,
			"readiness_code": pr_code,
			"status": "Approved for Publication",
		}
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def approveTenderPublication(
	actor: str,
	tender_code: str,
	comments: str | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`approve_tender_publication`."""
	return approve_tender_publication(actor, tender_code, comments=comments, context=context)
