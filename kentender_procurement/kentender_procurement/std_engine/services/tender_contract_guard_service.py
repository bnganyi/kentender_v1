from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event

DENIAL_CODE_DCM_REQUIRED = "STD_TM_DCM_REQUIRED"
DENIAL_CODE_CONTRACT_SOURCE_MISMATCH = "STD_TM_CONTRACT_SOURCE_MISMATCH"

WORKS_REQUIRED_CONTRACT_PRICE_SOURCE = "corrected evaluated BOQ total from Evaluation/Award"


def _std_engine_v2_enabled() -> bool:
	return bool(int(frappe.conf.get("std_engine_v2_enabled") or 0))


def _is_works_instance(std_instance_code: str) -> bool:
	row = frappe.db.get_value("STD Instance", {"instance_code": std_instance_code}, ["profile_code"], as_dict=True)
	if not row or not row.get("profile_code"):
		return False
	category = frappe.db.get_value(
		"STD Applicability Profile",
		{"profile_code": row["profile_code"]},
		"procurement_category",
	)
	return (category or "").strip().lower() == "works"


@frappe.whitelist()
def validate_contract_creation_inputs(
	tender_code: str, contract_payload: dict[str, Any] | None = None, actor: str | None = None
) -> dict[str, Any]:
	"""STD-CURSOR-0905: require DCM and enforce works contract source rule."""
	actor = actor or frappe.session.user
	contract_payload = contract_payload or {}
	if not _std_engine_v2_enabled():
		return {"allowed": True, "denial_code": None, "message": "Allowed"}
	binding = frappe.db.get_value(
		"STD Tender Binding",
		{"tender_code": tender_code},
		["std_instance_code", "std_dcm_code"],
		as_dict=True,
	)
	if not binding or not binding.get("std_instance_code"):
		return {"allowed": True, "denial_code": None, "message": "Allowed"}
	if not binding.get("std_dcm_code"):
		msg = "Contract creation cannot proceed without DCM for STD-bound tender."
		record_std_audit_event(
			"PERMISSION_DENIED",
			"STD Tender Binding",
			tender_code,
			actor=actor,
			denial_code=DENIAL_CODE_DCM_REQUIRED,
			reason=msg,
			metadata={"tender_code": tender_code, "std_instance_code": binding.get("std_instance_code")},
		)
		return {"allowed": False, "denial_code": DENIAL_CODE_DCM_REQUIRED, "message": msg}

	if _is_works_instance(binding["std_instance_code"]):
		source = (contract_payload.get("contract_price_source") or "").strip()
		if source and source != WORKS_REQUIRED_CONTRACT_PRICE_SOURCE:
			msg = "Works contract price source must be corrected evaluated BOQ total from Evaluation/Award."
			record_std_audit_event(
				"PERMISSION_DENIED",
				"STD Tender Binding",
				tender_code,
				actor=actor,
				denial_code=DENIAL_CODE_CONTRACT_SOURCE_MISMATCH,
				reason=msg,
				metadata={"tender_code": tender_code, "supplied_source": source},
			)
			return {"allowed": False, "denial_code": DENIAL_CODE_CONTRACT_SOURCE_MISMATCH, "message": msg}
	return {"allowed": True, "denial_code": None, "message": "Allowed"}


@frappe.whitelist()
def create_contract_from_std(
	tender_code: str, contract_payload: dict[str, Any] | None = None, actor: str | None = None
) -> dict[str, Any]:
	perm = validate_contract_creation_inputs(tender_code=tender_code, contract_payload=contract_payload, actor=actor)
	if not perm["allowed"]:
		frappe.throw(_(f"{perm['message']} ({perm['denial_code']})"), title=_("Contract creation denied"))
	return {
		"created": True,
		"tender_code": tender_code,
		"source": "dcm_contract_binding",
		"contract_payload": contract_payload or {},
	}
