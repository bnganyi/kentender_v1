# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.utils import get_datetime

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	METHDEC_CODE,
	METHDEC_CONTRACT_TYPE,
	METHDEC_DECIDED_AT,
	METHDEC_METHOD_BASIS,
	METHDEC_RULE_PROFILE_CODE,
	METHDEC_TEMPLATE_CODE,
	METHDEC_THRESHOLD_RESULT,
	PKG_CODE,
	PKG_PROCUREMENT_CATEGORY,
	PKG_REQUIRED_STD_CATEGORY,
	PKG_REQUIRED_STD_TYPE,
	PLAN_CREATOR_USER_CODE,
)


def _user_by_code(user_code: str) -> str | None:
	return frappe.db.get_value("User", {"username": user_code}, "name")


def execute():
	if not frappe.db.exists("Package Method Decision", METHDEC_CODE):
		return
	decided_by = _user_by_code(PLAN_CREATOR_USER_CODE)
	updates: dict[str, object] = {
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
		"decided_at": get_datetime(METHDEC_DECIDED_AT),
		"approved_by": None,
		"approved_at": None,
		"is_current": 1,
		"is_master_seed": 1,
	}
	if decided_by:
		updates["decided_by"] = decided_by
	frappe.db.set_value("Package Method Decision", METHDEC_CODE, updates, update_modified=False)
