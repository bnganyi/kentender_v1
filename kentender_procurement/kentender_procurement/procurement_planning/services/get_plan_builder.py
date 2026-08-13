# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Plan builder projection for PLN-UI-03 / PLN-UI-05."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, getdate

from kentender_procurement.procurement_planning.mvp1_constants import (
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VALIDATION_READY,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	READ_PLAN_ROLES,
	assert_planning_scope,
	has_any_operational_role,
	has_finance_task_capability,
	is_planning_read_only,
	require_operational_roles,
)
from kentender_procurement.procurement_planning.services.plan_item_finance import (
	finance_status_label,
)
from kentender_procurement.procurement_planning.services.preference_reservation import (
	plan_coverage,
	scheme_is_assigned,
)
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	draft_has_effective_changes,
	removal_capabilities_for_item,
)


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def _ou_label(ou: str) -> str:
	if not ou:
		return ""
	return cstr(
		frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou
	)


def _builder_next_step(
	*,
	empty: bool,
	issue_count: int,
	items_ready: bool,
	can_submit_for_review: bool,
) -> dict[str, str]:
	"""Guidance for the builder when the issue strip is not the primary cue."""
	if empty:
		return {"kind": "", "message": ""}
	if issue_count > 0:
		return {"kind": "attention", "message": ""}
	if not items_ready:
		return {"kind": "", "message": ""}
	if can_submit_for_review:
		return {
			"kind": "submit_review",
			"message": (
				"Plan Items are ready. Submit the consolidated plan for professional review."
			),
		}
	return {"kind": "", "message": ""}


def get_plan_builder(*, plan: str, user: str | None = None) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(
			frappe._("Login required."),
			frappe.PermissionError,
			title="PLN_LOGIN_REQUIRED",
		)
	if not (
		has_any_operational_role(*READ_PLAN_ROLES, user=actor)
		or has_finance_task_capability(actor)
	):
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
			[
				"name",
				"version_code",
				"version_number",
				"status",
				"validation_projection",
				"concurrency_token",
			],
			as_dict=True,
		)

	items_out: list[dict[str, Any]] = []
	planned_total = 0.0
	designation_values: list[float] = []
	ous: set[str] = set()
	read_only = is_planning_read_only(actor)
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
		method = ""
		schedule = ""
		validation = "Not run"
		iv = None
		if iv_name:
			iv = frappe.db.get_value(
				"Procurement Plan Item Version",
				iv_name,
				[
					"requirement_title",
					"confirmed_estimate",
					"procurement_category",
					"procurement_method",
					"ms_delivery_completion",
					"validation_projection",
					"preference_reservation_scheme",
					"planned_reserved_value",
					"finance_status",
					"finance_snapshot_amount",
					"finance_snapshot_budget_line",
					"plan_item",
				],
				as_dict=True,
			)
			if iv:
				title = iv.requirement_title or ""
				amount = flt(iv.confirmed_estimate)
				category = iv.procurement_category or ""
				method = iv.procurement_method or ""
				# Stitch PLN-UI-05: "By 31 Mar 2028"
				schedule = (
					f"By {getdate(iv.ms_delivery_completion).strftime('%d %b %Y')}"
					if iv.ms_delivery_completion
					else ""
				)
				validation = iv.validation_projection or "Not run"
				if scheme_is_assigned(iv.preference_reservation_scheme):
					designation_values.append(flt(iv.planned_reserved_value))
		planned_total += amount
		if it.owner_org_unit:
			ous.add(it.owner_org_unit)
		finance_label = "Not requested"
		if iv:
			finance_label = finance_status_label(iv)
		caps = removal_capabilities_for_item(
			plan_item=it.name,
			baseline_state=it.baseline_state,
			draft_version=draft or None,
			read_only=read_only,
		)
		items_out.append(
			{
				"plan_item": it.name,
				"plan_item_code": it.plan_item_code,
				"baseline_state": it.baseline_state,
				"title": title,
				"owner_org_unit": it.owner_org_unit,
				"owner_org_unit_label": _ou_label(it.owner_org_unit or ""),
				"amount": amount,
				"amount_display": _money(amount, plan_doc.currency or "KES"),
				"category": category,
				"method": method,
				"schedule": schedule,
				"validation_projection": validation,
				"finance_status_label": finance_label,
				"can_open_finance_task": has_finance_task_capability(actor)
				and finance_label
				in ("Awaiting confirmation", "Stale", "Returned"),
				"editor_route": f"/app/procurement-plan-item-editor?plan_item={it.name}",
				"can_remove_from_draft": caps["can_remove_from_draft"],
				"can_propose_removal": caps["can_propose_removal"],
				"removal_variant": caps["removal_variant"],
				"finance_effect_kind": caps["finance_effect_kind"],
				"finance_effect_copy": caps["finance_effect_copy"],
				"sources_label": caps["sources_label"],
			}
		)

	empty = len(items_out) == 0
	pe_label = (
		frappe.db.get_value("Procuring Entity", plan_doc.procuring_entity, "entity_name")
		or plan_doc.procuring_entity
	)
	validation = (version.validation_projection if version else "Not run") or "Not run"
	issue_count = sum(
		1
		for i in items_out
		if cstr(i.get("validation_projection")) in ("Needs attention", "Blocked")
	)
	currency = plan_doc.currency or "KES"
	coverage = plan_coverage(
		planned_total=planned_total,
		designation_values=designation_values,
		currency=currency,
	)

	items_ready = (not empty) and issue_count == 0 and all(
		cstr(i.get("validation_projection")) == VALIDATION_READY for i in items_out
	)
	has_successor = bool(draft) and bool(approved)
	no_changes_remain = has_successor and (not draft_has_effective_changes(plan=plan_name, version=draft))
	can_cancel_update = (not read_only) and no_changes_remain
	can_submit_for_review = (
		(not read_only)
		and bool(draft)
		and items_ready
		and (not no_changes_remain)
		and cstr(version.status if version else "") in ("Draft", "Returned")
	)

	# PLN-UI-03 Finance Confirmed projection.
	finance_confirmed_count = sum(
		1 for i in items_out if cstr(i.get("finance_status_label")) == "Confirmed"
	)
	finance_confirmed_total = len(items_out)

	next_step = _builder_next_step(
		empty=empty,
		issue_count=issue_count,
		items_ready=items_ready,
		can_submit_for_review=can_submit_for_review,
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
		# Stitch PLN-UI-03/05 header: Open Plan pill + Draft Version N.
		"version_status": cstr(version.status if version else "Draft") or "Draft",
		"version_number_label": (
			f"Draft Version {int(version.version_number)}" if version else "Draft Version 1"
		),
		"version_label": (
			f"{version.status} Version {int(version.version_number)}" if version else "—"
		),
		"item_count": len(items_out),
		"planned_total": planned_total,
		"planned_total_display": _money(planned_total, plan_doc.currency or "KES"),
		"organisation_unit_count": len(ous),
		"finance_confirmed_count": finance_confirmed_count,
		"finance_confirmed_total": finance_confirmed_total,
		"finance_confirmed_display": (
			f"{finance_confirmed_count} of {finance_confirmed_total}"
		),
		"validation_projection": validation,
		"issue_count": issue_count,
		"issue_summary": (
			"Complete the Plan Item before requesting Finance confirmation."
			if (not empty and not can_submit_for_review)
			else (
				f"{issue_count} item needs attention before submit for review."
				if issue_count == 1
				else (
					f"{issue_count} items need attention before submit for review."
					if issue_count
					else ""
				)
			)
		),
		"next_step_kind": next_step["kind"],
		"next_step_message": next_step["message"],
		"preference_reservation_coverage": coverage,
		"preference_reservation_coverage_display": coverage["display"],
		"items": items_out,
		"empty": empty,
		# Add Demand may open a Draft successor when only Approved Vn exists (PLN-FR-018).
		"can_add_demand": (not read_only)
		and cstr(plan_doc.lifecycle_state) == "Open"
		and (bool(draft) or bool(approved)),
		"add_demand_pending_gate": False,
		"read_only": read_only,
		"can_submit_for_review": can_submit_for_review,
		"no_changes_remain": no_changes_remain,
		"can_cancel_update": can_cancel_update,
		"review_route": f"/app/procurement-plan-review?plan={plan_name}",
		"current_approved_version": approved,
		"open_draft_version": draft,
		"update_route": (
			f"/app/procurement-plan-update?plan={plan_name}" if has_successor else ""
		),
		"concurrency_token": cstr(version.concurrency_token if version else "") or "",
		"workspace_route": "/app/planning-workspace",
	}
