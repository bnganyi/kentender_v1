# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
	PKG_DESCRIPTION,
	PKG_FISCAL_YEAR,
	PKG_PREPARED_AT,
	PKG_PRIORITY,
	PKG_PROCUREMENT_CATEGORY,
	PKG_REQUIRED_STD_CATEGORY,
	PKG_REQUIRED_STD_TYPE,
	PKG_TITLE,
	PE_CODE,
	PLAN_CREATOR_USER_CODE,
	STD_VERSION_CODE,
)


def _user_by_code(user_code: str) -> str | None:
	return frappe.db.get_value("User", {"username": user_code}, "name")


def execute():
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		return
	updates: dict[str, object] = {
		"package_name": PKG_TITLE,
		"package_description": PKG_DESCRIPTION,
		"procurement_category": PKG_PROCUREMENT_CATEGORY,
		"required_std_category": PKG_REQUIRED_STD_CATEGORY,
		"required_std_type": PKG_REQUIRED_STD_TYPE,
		"required_std_template_version_code": STD_VERSION_CODE,
		"procuring_entity_code": PE_CODE,
		"fiscal_year": PKG_FISCAL_YEAR,
		"package_priority": PKG_PRIORITY,
		"prepared_at": PKG_PREPARED_AT,
		"is_master_seed": 1,
	}
	prepared_by = _user_by_code(PLAN_CREATOR_USER_CODE)
	if prepared_by:
		updates["created_by"] = prepared_by
	frappe.db.set_value("Procurement Package", PKG_CODE, updates, update_modified=False)
