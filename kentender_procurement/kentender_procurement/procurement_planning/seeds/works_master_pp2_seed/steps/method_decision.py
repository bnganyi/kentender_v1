# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Record METHDEC-PKG-MOH-2026-001 (spec §11)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_CONSUMED,
	PKG_EDITABLE_STATUSES,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	JOURNEY_CODE,
	METHDEC_APPROVED_AT,
	METHDEC_CODE,
	METHDEC_CONTRACT_TYPE,
	METHDEC_DECIDED_AT,
	METHDEC_METHOD_BASIS,
	METHDEC_REVIEWER_EMAIL,
	METHDEC_REVIEWER_USER_CODE,
	METHDEC_RULE_PROFILE_CODE,
	METHDEC_TEMPLATE_CODE,
	METHDEC_THRESHOLD_RESULT,
	PKG_CODE,
	PKG_PROCUREMENT_CATEGORY,
	PKG_REQUIRED_STD_CATEGORY,
	PKG_REQUIRED_STD_TYPE,
	PLAN_CREATOR_EMAIL,
	PLAN_CREATOR_USER_CODE,
	SEED_ACTOR,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	_ensure_seed_user,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	_sync_package_from_decision,
)

_REPAIRABLE_METHOD_DECISION_FIELDS = (
	"method_decision_code",
	"package_code",
	"procurement_category",
	"procurement_method",
	"contract_type_expectation",
	"required_std_category",
	"required_std_type",
	"method_basis",
	"threshold_check_result",
	"template_code",
	"rule_profile_code",
	"override_flag",
	"override_reason",
	"decided_by",
	"decided_at",
	"approved_by",
	"approved_at",
	"is_current",
	"is_master_seed",
)

_APPROVED_PACKAGE_STATUSES = frozenset(
	(PKG_APPROVED, PKG_READY_FOR_RELEASE, PKG_RELEASED, PKG_CONSUMED)
)


def _strict_method_decision_values(
	*,
	decided_by: str,
	approved_by: str | None = None,
) -> dict[str, Any]:
	values: dict[str, Any] = {
		"method_decision_code": METHDEC_CODE,
		"package_code": PKG_CODE,
		"procurement_category": PKG_PROCUREMENT_CATEGORY,
		"procurement_method": "Open Tender",
		"contract_type_expectation": METHDEC_CONTRACT_TYPE,
		"required_std_category": PKG_REQUIRED_STD_CATEGORY,
		"required_std_type": PKG_REQUIRED_STD_TYPE,
		"method_basis": METHDEC_METHOD_BASIS,
		"threshold_check_result": METHDEC_THRESHOLD_RESULT,
		"template_code": METHDEC_TEMPLATE_CODE,
		"rule_profile_code": METHDEC_RULE_PROFILE_CODE,
		"override_flag": 0,
		"override_reason": None,
		"decided_by": decided_by,
		"decided_at": get_datetime(METHDEC_DECIDED_AT),
		"approved_by": approved_by,
		"approved_at": get_datetime(METHDEC_APPROVED_AT) if approved_by else None,
		"is_current": 1,
		"is_master_seed": 1,
	}
	if not approved_by:
		values["approved_by"] = None
		values["approved_at"] = None
	return values


def _normalize_for_sync(values: dict[str, Any]) -> dict[str, Any]:
	return {
		"procurement_category": values.get("procurement_category"),
		"procurement_method": values.get("procurement_method"),
		"required_std_category": values.get("required_std_category"),
		"required_std_type": values.get("required_std_type"),
		"contract_type_expectation": values.get("contract_type_expectation"),
		"method_basis": values.get("method_basis"),
		"threshold_check_result": values.get("threshold_check_result"),
		"template_code": values.get("template_code"),
		"rule_profile_code": values.get("rule_profile_code"),
		"override_flag": bool(values.get("override_flag")),
		"override_reason": values.get("override_reason"),
	}


def _method_decision_repair_allowed(*, package_status: str) -> bool:
	return (package_status or "").strip() in PKG_EDITABLE_STATUSES


def _demote_other_current_decisions() -> None:
	frappe.db.sql(
		"""
		UPDATE `tabPackage Method Decision`
		SET is_current = 0
		WHERE package_code = %s AND is_current = 1 AND method_decision_code != %s
		""",
		(PKG_CODE, METHDEC_CODE),
	)


def _ensure_package_method_decision() -> dict[str, Any]:
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		frappe.throw("Procurement Package not found.", title="MISSING_PACKAGE")

	decided_by = _ensure_seed_user(
		email=PLAN_CREATOR_EMAIL,
		user_code=PLAN_CREATOR_USER_CODE,
		full_name="Procurement Planner MOH",
	)
	values = _strict_method_decision_values(decided_by=decided_by)
	package_status = frappe.db.get_value("Procurement Package", PKG_CODE, "status") or ""
	existed = bool(frappe.db.exists("Package Method Decision", METHDEC_CODE))

	if existed:
		if _method_decision_repair_allowed(package_status=package_status):
			doc = frappe.get_doc("Package Method Decision", METHDEC_CODE)
			for fieldname in _REPAIRABLE_METHOD_DECISION_FIELDS:
				doc.set(fieldname, values[fieldname])
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)
			action = "repaired"
		else:
			action = "existing"
	else:
		doc = frappe.get_doc({"doctype": "Package Method Decision", **values})
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		action = "created"

	_demote_other_current_decisions()
	frappe.db.set_value(
		"Package Method Decision",
		METHDEC_CODE,
		{"is_current": 1},
		update_modified=False,
	)
	_sync_package_from_decision(PKG_CODE, _normalize_for_sync(values))

	return {
		"action": action,
		"method_decision_code": METHDEC_CODE,
	}


def sync_master_method_decision_approval() -> dict[str, Any]:
	if not frappe.db.exists("Package Method Decision", METHDEC_CODE):
		return {"action": "missing", "method_decision_code": METHDEC_CODE}

	package_status = frappe.db.get_value("Procurement Package", PKG_CODE, "status") or ""
	if package_status not in _APPROVED_PACKAGE_STATUSES:
		return {
			"action": "skipped",
			"method_decision_code": METHDEC_CODE,
			"reason": "package_not_approved",
		}

	approved_by = _ensure_seed_user(
		email=METHDEC_REVIEWER_EMAIL,
		user_code=METHDEC_REVIEWER_USER_CODE,
		full_name="Planning Reviewer MOH",
	)
	current_approved_by, current_approved_at = frappe.db.get_value(
		"Package Method Decision",
		METHDEC_CODE,
		("approved_by", "approved_at"),
	)
	if (
		(current_approved_by or "").strip() == approved_by
		and str(current_approved_at or "").split(".")[0] == METHDEC_APPROVED_AT
	):
		return {"action": "existing", "method_decision_code": METHDEC_CODE}

	frappe.db.set_value(
		"Package Method Decision",
		METHDEC_CODE,
		{
			"approved_by": approved_by,
			"approved_at": get_datetime(METHDEC_APPROVED_AT),
			"is_master_seed": 1,
		},
		update_modified=False,
	)
	return {"action": "synced", "method_decision_code": METHDEC_CODE}


def ensure_method_decision(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	del actor
	return _ensure_package_method_decision()
