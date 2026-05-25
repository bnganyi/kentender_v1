# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PLAN_APPROVED_AT,
	PLAN_APPROVER_USER_CODE,
	PLAN_CODE,
	PLAN_CREATED_AT,
	PLAN_CREATOR_USER_CODE,
	PLAN_DESCRIPTION,
	PLAN_PLANNING_CYCLE_CODE,
)


def _user_by_code(user_code: str) -> str | None:
	return frappe.db.get_value("User", {"username": user_code}, "name")


def execute():
	if not frappe.db.exists("Procurement Plan", PLAN_CODE):
		return
	updates: dict[str, object] = {
		"status": PLAN_ACTIVE,
		"is_active": 1,
		"is_master_seed": 1,
		"plan_description": PLAN_DESCRIPTION,
		"planning_cycle_code": PLAN_PLANNING_CYCLE_CODE,
		"created_at": PLAN_CREATED_AT,
		"approved_at": PLAN_APPROVED_AT,
	}
	creator = _user_by_code(PLAN_CREATOR_USER_CODE)
	if creator:
		updates["created_by"] = creator
	approver = _user_by_code(PLAN_APPROVER_USER_CODE)
	if approver:
		updates["approved_by"] = approver
	frappe.db.set_value("Procurement Plan", PLAN_CODE, updates, update_modified=False)
