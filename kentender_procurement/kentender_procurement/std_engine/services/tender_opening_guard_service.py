from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event

DENIAL_CODE_MANUAL_OPENING_BLOCKED = "STD_TM_MANUAL_OPENING_BLOCKED"
DENIAL_CODE_DOM_REQUIRED = "STD_TM_DOM_REQUIRED"


def _std_engine_v2_enabled() -> bool:
	return bool(int(frappe.conf.get("std_engine_v2_enabled") or 0))


@frappe.whitelist()
def check_manual_opening_field_permission(tender_code: str, actor: str | None = None) -> dict[str, Any]:
	"""STD-CURSOR-0904: deny manual opening fields for STD-v2 bound tenders."""
	actor = actor or frappe.session.user
	if not _std_engine_v2_enabled():
		return {"allowed": True, "denial_code": None, "message": "Allowed"}
	binding = frappe.db.get_value(
		"STD Tender Binding",
		{"tender_code": tender_code},
		["std_instance_code", "std_dom_code"],
		as_dict=True,
	)
	if binding and binding.get("std_instance_code"):
		msg = "Manual opening fields are disabled for STD v2 tenders; opening register must come from DOM."
		record_std_audit_event(
			"PERMISSION_DENIED",
			"STD Tender Binding",
			tender_code,
			actor=actor,
			denial_code=DENIAL_CODE_MANUAL_OPENING_BLOCKED,
			reason=msg,
			metadata={
				"tender_code": tender_code,
				"std_instance_code": binding.get("std_instance_code"),
				"std_dom_code": binding.get("std_dom_code"),
			},
		)
		return {"allowed": False, "denial_code": DENIAL_CODE_MANUAL_OPENING_BLOCKED, "message": msg}
	return {"allowed": True, "denial_code": None, "message": "Allowed"}


@frappe.whitelist()
def create_manual_opening_field(
	tender_code: str, opening_field_payload: dict[str, Any] | None = None, actor: str | None = None
) -> dict[str, Any]:
	perm = check_manual_opening_field_permission(tender_code=tender_code, actor=actor)
	if not perm["allowed"]:
		frappe.throw(_(f"{perm['message']} ({perm['denial_code']})"), title=_("Manual opening field denied"))
	return {
		"created": True,
		"tender_code": tender_code,
		"source": "manual_opening_field",
		"opening_field_payload": opening_field_payload or {},
	}


@frappe.whitelist()
def validate_opening_can_proceed(tender_code: str, actor: str | None = None) -> dict[str, Any]:
	"""Enforce DOM presence before opening for STD-v2 bound tenders."""
	actor = actor or frappe.session.user
	if not _std_engine_v2_enabled():
		return {"allowed": True, "denial_code": None, "message": "Allowed"}
	binding = frappe.db.get_value(
		"STD Tender Binding",
		{"tender_code": tender_code},
		["std_instance_code", "std_dom_code"],
		as_dict=True,
	)
	if not binding or not binding.get("std_instance_code"):
		return {"allowed": True, "denial_code": None, "message": "Allowed"}
	if binding.get("std_dom_code"):
		return {"allowed": True, "denial_code": None, "message": "Allowed"}
	msg = "Opening cannot proceed without DOM for STD-bound tender."
	record_std_audit_event(
		"PERMISSION_DENIED",
		"STD Tender Binding",
		tender_code,
		actor=actor,
		denial_code=DENIAL_CODE_DOM_REQUIRED,
		reason=msg,
		metadata={"tender_code": tender_code, "std_instance_code": binding.get("std_instance_code")},
	)
	return {"allowed": False, "denial_code": DENIAL_CODE_DOM_REQUIRED, "message": msg}
