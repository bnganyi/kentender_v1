# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-008 — Plan-level evidence view-model adapter."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT


def get_procurement_plan_evidence_view_model(
	*,
	plan_id: str | None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""Return PP3 plan-level evidence envelope (business labels only)."""
	user = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(user) or "auditor"
	code = (plan_id or "").strip()
	if not code or not frappe.db.exists("Procurement Plan", code):
		return {
			"ok": False,
			"error_code": "PLAN_NOT_FOUND",
			"message": "Procurement plan could not be found.",
			"role_key": role_key,
		}
	doc = frappe.get_doc("Procurement Plan", code)
	if not pp_scope.entity_in_user_scope(doc.procuring_entity, user):
		return {
			"ok": False,
			"error_code": "PP_ACCESS_DENIED",
			"message": "You do not have access to this procurement plan evidence.",
			"role_key": role_key,
		}
	title = (doc.plan_name or doc.plan_code or code).strip()
	timeline: list[dict[str, str]] = [{"label": "Procurement plan created", "status": "complete"}]
	status = (doc.status or "").strip()
	if status == PLAN_ACTIVE:
		timeline.append({"label": "Procurement plan activated", "status": "complete"})
	elif status == PLAN_DRAFT:
		timeline.append({"label": "Procurement plan awaiting activation", "status": "in_progress"})
	records = [{"label": "Procurement Plan", "type": "procurement_plan"}]
	return {
		"ok": True,
		"role_key": role_key,
		"title": title,
		"timeline": timeline,
		"records": records,
		"technical_details": {
			"visible_by_default": False,
			"requires_permission": True,
			"may_view_technical": bool(
				"Planning Authority" in frappe.get_roles(user)
				or "Administrator" in frappe.get_roles(user)
			),
			"codes": [code] if code else [],
		},
	}
