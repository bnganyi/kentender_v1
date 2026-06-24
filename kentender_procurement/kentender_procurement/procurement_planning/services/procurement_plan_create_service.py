# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-004 — Create procurement plan service."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import PLAN_DRAFT
from kentender_procurement.procurement_planning.services.procurement_plans_view_model import (
	_plan_row,
)


def _session_user(actor: str | None) -> str:
	return (actor or frappe.session.user or "").strip() or frappe.session.user


def _parse_fiscal_year(raw: Any) -> int | None:
	if raw is None:
		return None
	text = str(raw).strip()
	if not text:
		return None
	if "/" in text:
		text = text.split("/", 1)[0].strip()
	if not text.isdigit():
		return None
	return int(text)


def _entity_code(entity: str) -> str:
	code = (frappe.db.get_value("Procuring Entity", entity, "entity_code") or entity or "").strip()
	code = re.sub(r"[^A-Za-z0-9]", "", code).upper()
	return code[:12] or "PLAN"


def _generate_plan_code(procuring_entity: str, fiscal_year: int) -> str:
	base = f"PLAN-{_entity_code(procuring_entity)}-{fiscal_year}"
	if not frappe.db.exists("Procurement Plan", base):
		return base
	for _ in range(20):
		candidate = f"{base}-{frappe.generate_hash(length=4).upper()}"
		if not frappe.db.exists("Procurement Plan", candidate):
			return candidate
	frappe.throw(_("Could not generate a unique plan code."), title=_("Create plan failed"))


def create_procurement_plan(
	*,
	procuring_entity: str | None,
	fiscal_year: Any,
	plan_title: str | None,
	currency: str | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""Create a draft procurement plan (P4-004)."""
	user = _session_user(actor)
	role_key = resolve_pp_role_key(user) or "auditor"
	entity = (procuring_entity or "").strip()
	title = (plan_title or "").strip()
	cur = (currency or "KES").strip() or "KES"
	fy = _parse_fiscal_year(fiscal_year)
	if not entity:
		return {
			"ok": False,
			"error_code": "MISSING_ENTITY",
			"message": _("Procuring entity is required."),
			"role_key": role_key,
		}
	if fy is None:
		return {
			"ok": False,
			"error_code": "MISSING_FISCAL_YEAR",
			"message": _("Fiscal year is required."),
			"role_key": role_key,
		}
	if not title:
		return {
			"ok": False,
			"error_code": "MISSING_TITLE",
			"message": _("Plan title is required."),
			"role_key": role_key,
		}
	if not frappe.db.exists("Procuring Entity", entity):
		return {
			"ok": False,
			"error_code": "INVALID_ENTITY",
			"message": _("Procuring entity could not be found."),
			"role_key": role_key,
		}
	if not pp_scope.entity_in_user_scope(entity, user):
		return {
			"ok": False,
			"error_code": "PP_ACCESS_DENIED",
			"message": _("You do not have access to create plans for this entity."),
			"role_key": role_key,
		}
	if not frappe.has_permission("Procurement Plan", "create", user=user):
		return {
			"ok": False,
			"error_code": "PP_ACCESS_DENIED",
			"message": _("You do not have permission to create procurement plans."),
			"role_key": role_key,
		}
	plan_code = _generate_plan_code(entity, fy)
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			"plan_code": plan_code,
			"plan_name": title,
			"fiscal_year": fy,
			"procuring_entity": entity,
			"currency": cur,
			"status": PLAN_DRAFT,
			"is_active": 1,
			"created_by": user,
			"created_at": now_datetime(),
		}
	)
	doc.insert(ignore_permissions=True)
	row = _plan_row(
		{
			"name": doc.name,
			"plan_code": doc.plan_code,
			"plan_name": doc.plan_name,
			"fiscal_year": doc.fiscal_year,
			"status": doc.status,
			"is_active": doc.is_active,
		}
	)
	return {
		"ok": True,
		"role_key": role_key,
		"plan": row,
		"message": _("Procurement plan created."),
	}
