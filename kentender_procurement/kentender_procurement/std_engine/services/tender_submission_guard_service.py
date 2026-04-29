from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event

DENIAL_CODE_MANUAL_SUBMISSION_BLOCKED = "STD_TM_MANUAL_SUBMISSION_BLOCKED"


def _std_engine_v2_enabled() -> bool:
	return bool(int(frappe.conf.get("std_engine_v2_enabled") or 0))


@frappe.whitelist()
def check_manual_submission_requirement_permission(tender_code: str, actor: str | None = None) -> dict[str, Any]:
	"""STD-CURSOR-0902: deny manual submission checklist for STD-v2 bound tenders."""
	actor = actor or frappe.session.user
	if not _std_engine_v2_enabled():
		return {"allowed": True, "denial_code": None, "message": "Allowed"}
	binding = frappe.db.get_value(
		"STD Tender Binding",
		{"tender_code": tender_code},
		["name", "std_instance_code"],
		as_dict=True,
	)
	if binding and binding.get("std_instance_code"):
		msg = "Manual submission requirements are disabled for STD v2 tenders; use DSM-derived checklist."
		record_std_audit_event(
			"PERMISSION_DENIED",
			"STD Tender Binding",
			tender_code,
			actor=actor,
			denial_code=DENIAL_CODE_MANUAL_SUBMISSION_BLOCKED,
			reason=msg,
			metadata={"tender_code": tender_code, "std_instance_code": binding.get("std_instance_code")},
		)
		return {"allowed": False, "denial_code": DENIAL_CODE_MANUAL_SUBMISSION_BLOCKED, "message": msg}
	return {"allowed": True, "denial_code": None, "message": "Allowed"}


@frappe.whitelist()
def create_manual_submission_requirement(
	tender_code: str, requirement_payload: dict[str, Any] | None = None, actor: str | None = None
) -> dict[str, Any]:
	"""Guarded API surface; blocks bypass when STD v2 + binding are active."""
	perm = check_manual_submission_requirement_permission(tender_code=tender_code, actor=actor)
	if not perm["allowed"]:
		frappe.throw(_(f"{perm['message']} ({perm['denial_code']})"), title=_("Manual checklist denied"))
	return {
		"created": True,
		"tender_code": tender_code,
		"source": "manual_submission_requirement",
		"requirement_payload": requirement_payload or {},
	}
