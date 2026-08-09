# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Plan builder projection for PLN-UI-03 (empty Draft / Draft items list shell)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import (
	ITEM_ACTIVE,
	ITEM_PROPOSED,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	READ_PLAN_ROLES,
	assert_planning_scope,
	require_operational_roles,
)


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def get_plan_builder(*, plan: str, user: str | None = None) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(
			frappe._("Login required."),
			frappe.PermissionError,
			title="PLN_LOGIN_REQUIRED",
		)
	require_operational_roles(*READ_PLAN_ROLES, user=actor)

	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(frappe._("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
		user=actor,
		require_write=False,
	)

	draft = cstr(plan_doc.open_draft_version or "").strip()
	approved = cstr(plan_doc.current_approved_version or "").strip()
	focus = draft or approved
	version = None
	if focus and frappe.db.exists("Procurement Plan Version", focus):
		version = frappe.db.get_value(
			"Procurement Plan Version",
			focus,
			["name", "version_code", "version_number", "status", "validation_projection"],
			as_dict=True,
		)

	items_out: list[dict[str, Any]] = []
	planned_total = 0.0
	item_names = frappe.get_all(
		"Procurement Plan Item",
		filters={
			"plan": plan_name,
			"baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]],
		},
		fields=["name", "plan_item_code", "baseline_state", "owner_org_unit"],
		order_by="creation asc",
	)
	for it in item_names:
		iv_name = None
		if focus:
			iv_name = frappe.db.get_value(
				"Procurement Plan Item Version",
				{"plan_item": it.name, "plan_version": focus},
				"name",
			)
		if not iv_name:
			iv_name = frappe.db.get_value(
				"Procurement Plan Item", it.name, "current_approved_item_version"
			) or frappe.db.get_value(
				"Procurement Plan Item", it.name, "draft_item_version"
			)
		title = ""
		amount = 0.0
		category = ""
		if iv_name:
			iv = frappe.db.get_value(
				"Procurement Plan Item Version",
				iv_name,
				["requirement_title", "confirmed_estimate", "procurement_category"],
				as_dict=True,
			)
			if iv:
				title = iv.requirement_title or ""
				amount = flt(iv.confirmed_estimate)
				category = iv.procurement_category or ""
		planned_total += amount
		items_out.append(
			{
				"plan_item": it.name,
				"plan_item_code": it.plan_item_code,
				"baseline_state": it.baseline_state,
				"title": title,
				"owner_org_unit": it.owner_org_unit,
				"amount": amount,
				"amount_display": _money(amount, plan_doc.currency or "KES"),
				"category": category,
			}
		)

	empty = len(items_out) == 0
	pe_label = (
		frappe.db.get_value("Procuring Entity", plan_doc.procuring_entity, "entity_name")
		or plan_doc.procuring_entity
	)

	return {
		"ok": True,
		"plan": plan_doc.name,
		"plan_code": plan_doc.plan_code,
		"title": plan_doc.title,
		"procuring_entity": plan_doc.procuring_entity,
		"procuring_entity_label": pe_label,
		"financial_year": plan_doc.financial_year,
		"lifecycle_state": plan_doc.lifecycle_state,
		"period_start": str(plan_doc.period_start or ""),
		"period_end": str(plan_doc.period_end or ""),
		"currency": plan_doc.currency or "KES",
		"version": version,
		"version_label": (
			f"{version.status} Version {int(version.version_number)}" if version else "—"
		),
		"item_count": len(items_out),
		"planned_total": planned_total,
		"planned_total_display": _money(planned_total, plan_doc.currency or "KES"),
		"validation_projection": (version.validation_projection if version else "Not run")
		or "Not run",
		"departmental_contributions_label": "0 submitted",
		"items": items_out,
		"empty": empty,
		"can_add_demand": empty or bool(draft),
		"add_demand_pending_gate": True,
		"workspace_route": "/app/planning-workspace",
	}
