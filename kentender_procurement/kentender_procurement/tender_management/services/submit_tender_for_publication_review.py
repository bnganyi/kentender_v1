# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §9.4 — submit tender for publication review (**TM2 Tender**).

Preconditions: tender in an editable pre-review state (**Draft**, **STD Instance Incomplete**,
same set as §9.3 ``run_publication_readiness``, or **Returned for Correction**); latest **TM2 Publication
Readiness** row is **Ready** with bundle/DSM/DOM/DEM/DCM current and ``timeline_valid`` on that row;
**TM2 Tender Access Rule** exists; active STD binding matches the readiness row;
:func:`get_action_availability` for
``TND2_SUBMIT_PUBLICATION_REVIEW``.

On success: ``status`` → **Ready for Publication Review**; audit **Tender Submitted for
Publication Review**.

Tests: ``tender_management.tests.test_p4_04_submit_tender_for_publication_review``;
``tender_management.tests.test_o01_tm2_smoke_read_001_block_publication_review_when_dem_missing`` (doc 8 TM2-SMOKE-READ-001 / O-01);
``tender_management.tests.test_o02_tm2_smoke_read_002_allow_publication_review_after_readiness_passes`` (doc 8 TM2-SMOKE-READ-002 / O-02).
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

_ACTION = "TND2_SUBMIT_PUBLICATION_REVIEW"
_OBJECT_TYPE = "TM2 Tender"

# Align with ``run_publication_readiness`` — after P4-02 bind, status is often **STD Instance Incomplete**.
_ALLOWED_TENDER_STATUSES = frozenset({"Draft", "STD Instance Incomplete", "Returned for Correction"})

_OUTPUT_FLAG_DENIALS: tuple[tuple[str, DenialCode], ...] = (
	("bundle_current", DenialCode.AUTH_BUNDLE_MISSING_OR_STALE),
	("dsm_current", DenialCode.AUTH_DSM_MISSING_OR_STALE),
	("dom_current", DenialCode.AUTH_DOM_MISSING_OR_STALE),
	("dem_current", DenialCode.AUTH_DEM_MISSING_OR_STALE),
	("dcm_current", DenialCode.AUTH_DCM_MISSING_OR_STALE),
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


def _active_std_binding(tm2_name: str) -> Document | None:
	rows = frappe.get_all(
		"TM2 Tender STD Binding",
		filters={
			"tm2_tender": tm2_name,
			"is_active": 1,
			"binding_status": ["not in", ["Cancelled", "Superseded"]],
		},
		pluck="name",
		limit=1,
	)
	if not rows:
		return None
	return frappe.get_doc("TM2 Tender STD Binding", rows[0])


def _latest_publication_readiness(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Publication Readiness",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"readiness_code",
			"readiness_status",
			"tm2_tender_std_binding",
			"bundle_current",
			"dsm_current",
			"dom_current",
			"dem_current",
			"dcm_current",
			"timeline_valid",
		],
		order_by="validation_run_number desc",
		limit=1,
	)
	return rows[0] if rows else None


def _truthy(v: Any) -> bool:
	if v is None:
		return False
	if isinstance(v, (int, float)):
		return bool(int(v))
	return bool(v)


def submit_tender_for_publication_review(
	actor: str,
	tender_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §9.4 — gate on latest readiness **Ready**, outputs current, access/timeline, then transition + audit."""
	ctx = dict(context or ())
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format((tender_code or "").strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st not in _ALLOWED_TENDER_STATUSES:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Tender status does not allow submit for publication review."),
			extra={"tender_status": st},
		)

	if not frappe.db.exists("TM2 Tender Access Rule", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("TM2 Tender Access Rule is required before submission."),
		)

	bind = _active_std_binding(tm2.name)
	if not bind:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("No active TM2 Tender STD Binding exists for this tender."),
		)

	read_row = _latest_publication_readiness(tm2.name)
	if not read_row:
		return _deny(
			DenialCode.AUTH_STD_NOT_READY.value,
			_("Run publication readiness before submitting for publication review."),
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

	pr_name = cstr(read_row.get("name") or "").strip()
	pr_code = cstr(read_row.get("readiness_code") or "").strip()
	now = now_datetime()
	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		frappe.db.set_value(
			"TM2 Tender",
			tm2.name,
			{
				"status": "Ready for Publication Review",
				"submitted_for_review_by": actor if frappe.db.exists("User", actor) else None,
				"submitted_for_review_at": now,
			},
			update_modified=True,
		)
		audit_payload = {
			"tm2_publication_readiness": pr_name,
			"readiness_code": pr_code,
			"prior_status": st,
		}
		append_tender_audit_event(
			tc,
			"Tender Submitted for Publication Review",
			actor,
			audit_payload,
			related_object_type="TM2 Publication Readiness",
			related_object_code=pr_name,
			previous_state=st,
			new_state="Ready for Publication Review",
			enforce_section_13_2=False,
		)
		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"tm2_publication_readiness": pr_name,
			"readiness_code": pr_code,
			"status": "Ready for Publication Review",
		}
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def submitTenderForPublicationReview(
	actor: str, tender_code: str, context: dict[str, Any] | None = None
) -> dict[str, Any]:
	"""CamelCase alias for :func:`submit_tender_for_publication_review`."""
	return submit_tender_for_publication_review(actor, tender_code, context=context)
