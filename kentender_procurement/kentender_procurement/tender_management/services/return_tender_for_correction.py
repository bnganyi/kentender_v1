# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 4 §23 / pack — return **TM2 Tender** for correction.

Governed transition (no ad-hoc ``status`` writes): tender must be **Ready for Publication Review**
or **Approved for Publication** (pre-publish review path); non-empty ``reason``; access rule exists;
:func:`get_action_availability` for ``TND2_RETURN_CORRECTION``.

On success: ``status`` → **Returned for Correction**; clears publication-review fields
(``submitted_for_review_*``; ``approved_for_publication_*`` when returning from **Approved for Publication**);
audit **Tender Returned for Correction** with ``reason`` + ``previous_state`` / ``new_state``.

Tests: ``tender_management.tests.test_p4_07_return_tender_for_correction``.
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

_ACTION = "TND2_RETURN_CORRECTION"
_OBJECT_TYPE = "TM2 Tender"

_ALLOWED_STATUSES = frozenset({"Ready for Publication Review", "Approved for Publication"})


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


def return_tender_for_correction(
	actor: str,
	tender_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Return tender for correction with mandatory reviewer ``reason`` (doc 4 governance)."""
	ctx = dict(context or ())
	rs = cstr(reason or "").strip()
	if not rs:
		return _deny(
			DenialCode.AUTH_REASON_REQUIRED.value,
			_("A return reason is required."),
		)
	if len(rs) > 4000:
		rs = rs[:4000]

	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st == "Returned for Correction":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender is already returned for correction."),
			extra={"tender_status": st},
		)
	if st not in _ALLOWED_STATUSES:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender status does not allow return for correction."),
			extra={"tender_status": st},
		)

	if not frappe.db.exists("TM2 Tender Access Rule", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("TM2 Tender Access Rule is required."),
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

	updates: dict[str, Any] = {
		"status": "Returned for Correction",
		"submitted_for_review_by": None,
		"submitted_for_review_at": None,
	}
	if st == "Approved for Publication":
		updates["approved_for_publication_by"] = None
		updates["approved_for_publication_at"] = None

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		frappe.db.set_value("TM2 Tender", tm2.name, updates, update_modified=True)
		reason_trim = rs.strip()
		append_tender_audit_event(
			tc,
			"Tender Returned for Correction",
			actor,
			{"return_reason": reason_trim, "prior_status": st},
			previous_state=st,
			new_state="Returned for Correction",
			reason=reason_trim,
			enforce_section_13_2=False,
		)
		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"status": "Returned for Correction",
			"reason": rs,
		}
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def returnTenderForCorrection(
	actor: str,
	tender_code: str,
	reason: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`return_tender_for_correction`."""
	return return_tender_for_correction(actor, tender_code, reason, context=context)
