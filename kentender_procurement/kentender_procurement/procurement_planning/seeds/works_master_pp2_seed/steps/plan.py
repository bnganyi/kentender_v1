# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure PLAN-MOH-2026 exists (spec §7)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime

from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	CURRENCY,
	FISCAL_YEAR,
	PLAN_APPROVED_AT,
	PLAN_APPROVER_EMAIL,
	PLAN_APPROVER_USER_CODE,
	PLAN_CODE,
	PLAN_CREATED_AT,
	PLAN_CREATOR_EMAIL,
	PLAN_CREATOR_USER_CODE,
	PLAN_DESCRIPTION,
	PLAN_NAME,
	PLAN_PLANNING_CYCLE_CODE,
	SEED_ACTOR,
)


def _resolve_entity() -> str:
	entity = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name")
	if entity:
		return entity
	entity = frappe.db.get_value("Procuring Entity", {"entity_code": "MOH"}, "name")
	if entity:
		return entity
	frappe.throw("Procuring Entity PE-MOH not found.", title="MISSING_PROCURING_ENTITY")


def _ensure_seed_user(*, email: str, user_code: str, full_name: str) -> str:
	"""Resolve a User link for strict seed actor codes."""
	if frappe.db.exists("User", user_code):
		return user_code
	by_username = frappe.db.get_value("User", {"username": user_code}, "name")
	if by_username:
		return by_username
	if frappe.db.exists("User", email):
		frappe.db.set_value("User", email, {"enabled": 1, "username": user_code}, update_modified=False)
		return email
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"username": user_code,
			"first_name": full_name,
			"full_name": full_name,
			"enabled": 1,
			"user_type": "System User",
			"send_welcome_email": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _strict_plan_values(*, entity: str) -> dict[str, Any]:
	created_by = _ensure_seed_user(
		email=PLAN_CREATOR_EMAIL,
		user_code=PLAN_CREATOR_USER_CODE,
		full_name="Procurement Planner MOH",
	)
	approved_by = _ensure_seed_user(
		email=PLAN_APPROVER_EMAIL,
		user_code=PLAN_APPROVER_USER_CODE,
		full_name="Planning Authority MOH",
	)
	return {
		"plan_code": PLAN_CODE,
		"plan_name": PLAN_NAME,
		"plan_description": PLAN_DESCRIPTION,
		"fiscal_year": FISCAL_YEAR,
		"planning_cycle_code": PLAN_PLANNING_CYCLE_CODE,
		"procuring_entity": entity,
		"currency": CURRENCY,
		"status": PLAN_ACTIVE,
		"is_active": 1,
		"is_master_seed": 1,
		"created_by": created_by,
		"created_at": get_datetime(PLAN_CREATED_AT),
		"approved_by": approved_by,
		"approved_at": get_datetime(PLAN_APPROVED_AT),
	}


def ensure_procurement_plan(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	entity = _resolve_entity()
	values = _strict_plan_values(entity=entity)
	if frappe.db.exists("Procurement Plan", PLAN_CODE):
		doc = frappe.get_doc("Procurement Plan", PLAN_CODE)
		doc.flags.ignore_validate_update_after_submit = True
		for fieldname, value in values.items():
			doc.set(fieldname, value)
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)
		return {"action": "repaired", "plan_code": PLAN_CODE, "status": doc.status}

	doc = frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			**values,
		}
	)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return {"action": "created", "plan_code": PLAN_CODE, "status": PLAN_ACTIVE}
