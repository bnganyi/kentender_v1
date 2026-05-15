# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §9.3 — run publication readiness for a **TM2 Tender**.

Uses :func:`~kentender_procurement.tender_management.services.tm2_std_adapter.validate_tender_std_readiness`
and :func:`~kentender_procurement.tender_management.std_instance.tm2_publication_readiness_service.insert_tm2_publication_readiness_record`.

Tests: ``tender_management.tests.test_p4_03_run_publication_readiness``.
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
from kentender_procurement.tender_management.services.tm2_std_adapter import validate_tender_std_readiness
from kentender_procurement.tender_management.std_instance.tm2_publication_readiness_service import (
	insert_tm2_publication_readiness_record,
)

_ACTION = "TND2_RUN_READINESS"
_OBJECT_TYPE = "TM2 Tender"

_ALLOWED_TENDER_STATUSES = frozenset(
	{
		"Draft",
		"STD Instance Incomplete",
		"Returned for Correction",
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


def _tm2_readiness_summary_from_record(readiness_status: str) -> str:
	rs = (readiness_status or "").strip()
	if rs in ("Ready", "Ready With Warnings"):
		return rs
	if rs == "Blocked":
		return "Blocked"
	return "Not Ready"


def run_publication_readiness(
	actor: str,
	tender_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §9.3 — §7.3 ``TND2_RUN_READINESS``, active binding, adapter validate, immutable readiness row, audit."""
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
			DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED.value,
			_("Tender status does not allow running publication readiness."),
			extra={"tender_status": st},
		)

	bind = _active_std_binding(tm2.name)
	if not bind:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("No active TM2 Tender STD Binding exists for this tender."),
		)

	si_name = cstr(bind.tender_std_instance or "").strip()
	if not si_name:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("Active binding has no Tender STD Instance."),
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

	prev_user = frappe.session.user
	try:
		frappe.set_user(actor)
		v = validate_tender_std_readiness(si_name)
		if v.get("ok") is False:
			return _deny(
				DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
				_("Tender STD Instance readiness could not be evaluated."),
				extra={"validate_tender_std_readiness": v},
			)

		std_rs = cstr(
			frappe.db.get_value("Tender STD Instance", si_name, "readiness_status") or ""
		).strip()
		pub_status = "Ready" if v.get("status") == "Ready" else "Blocked"
		summary = _tm2_readiness_summary_from_record(pub_status)

		payload = {
			"evaluate": {
				"status": v.get("status"),
				"blockers": v.get("blockers") or [],
				"warnings": v.get("warnings") or [],
			},
			"adapter": "validate_tender_std_readiness",
		}
		for b in v.get("blockers") or []:
			if b.get("code") == "DEM_MISSING":
				payload.setdefault("doc9_pack_codes", []).append("DEM_MISSING_OR_STALE")

		bc = {str(b.get("code") or "") for b in (v.get("blockers") or [])}
		read_doc = insert_tm2_publication_readiness_record(
			tm2.name,
			bind.name,
			readiness_status=pub_status,
			std_readiness_status=std_rs or "Not Ready",
			validation_payload=payload,
			package_lineage_valid=True,
			template_version_active=True,
			std_instance_exists=True,
			parameters_complete="PARAMETERS_INCOMPLETE" not in bc,
			sections_complete="REQUIRED_ATTACHMENTS_INCOMPLETE" not in bc,
			bundle_current=bool(v.get("bundle_current")),
			dsm_current=bool(v.get("dsm_current")),
			dom_current=bool(v.get("dom_current")),
			dem_current=bool(v.get("dem_current")),
			dcm_current=bool(v.get("dcm_current")),
			timeline_valid=True,
			supplier_access_valid=True,
			unresolved_blocker_count=len(v.get("blockers") or []),
			warning_count=len(v.get("warnings") or []),
		)

		frappe.db.set_value(
			"TM2 Tender STD Binding",
			bind.name,
			{"readiness_status": summary},
			update_modified=False,
		)
		frappe.db.set_value(
			"TM2 Tender",
			tm2.name,
			{"std_readiness_status": summary},
			update_modified=False,
		)

		audit_payload = {
			"tm2_publication_readiness": read_doc.name,
			"readiness_code": read_doc.readiness_code,
			"readiness_status": pub_status,
			"primary_blocker_codes": [b.get("code") for b in (v.get("blockers") or []) if b.get("code")],
		}
		append_tender_audit_event(
			tc,
			"STD Readiness Validation Run",
			actor,
			audit_payload,
			related_object_type="TM2 Publication Readiness",
			related_object_code=read_doc.name,
			enforce_section_13_2=False,
		)

		return {
			"ok": True,
			"tender_code": tc,
			"tm2_tender": tm2.name,
			"tm2_publication_readiness": read_doc.name,
			"readiness_code": read_doc.readiness_code,
			"readiness_status": pub_status,
			"std_readiness_status": summary,
			"validate_tender_std_readiness": v,
		}
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.set_user(prev_user)


def runPublicationReadiness(actor: str, tender_code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
	"""CamelCase alias for :func:`run_publication_readiness`."""
	return run_publication_readiness(actor, tender_code, context=context)
