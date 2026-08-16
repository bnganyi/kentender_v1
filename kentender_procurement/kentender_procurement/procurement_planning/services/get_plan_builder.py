"""Ordinary Plan builder projection for PLN-UI-03 and every PLN-UI-05 Draft."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.services.list_eligible_demands import list_eligible_demands
from kentender_procurement.procurement_planning.services.plan_item_finance import effective_finance_status_from_values
from kentender_procurement.procurement_planning.services.planning_permissions import READ_PLAN_ROLES, assert_planning_scope, has_any_operational_role, is_planning_read_only, require_operational_roles
from kentender_procurement.procurement_planning.services.validate_plan import effective_validation_status_from_rows


def _money(value: float, currency: str) -> str:
	return f"{currency} {flt(value):,.2f}"


def _row_state(iv: Any, finance: str | None = None) -> tuple[str, str, str]:
	finance = cstr(finance or iv.finance_status or "Not requested")
	validation = cstr(iv.validation_projection or "Not run")
	if finance == "Returned":
		return "Finance returned", "Correct item", "correct_item"
	if validation in ("Blocked", "Stale", "Needs attention"):
		return validation, "Resolve issues", "resolve_issues"
	if validation != "Ready":
		return "Incomplete", "Complete item", "complete_item"
	if finance == "Awaiting confirmation":
		return "Awaiting Finance", "View item", "view_item"
	return "Complete", "View item", "view_item"


def get_plan_builder(
	*, plan: str, organisation_unit: str | None = None, status: str | None = None,
	search: str | None = None, user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(frappe._("Login required."), frappe.PermissionError, title="PLN_LOGIN_REQUIRED")
	if not has_any_operational_role(*READ_PLAN_ROLES, user=actor):
		require_operational_roles(*READ_PLAN_ROLES, user=actor)
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(frappe._("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")
	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(procuring_entity=plan_doc.procuring_entity, user=actor, require_write=False)
	draft = cstr(plan_doc.open_draft_version).strip()
	approved = cstr(plan_doc.current_approved_version).strip()
	if approved and draft:
		from kentender_procurement.procurement_planning.services.plan_builder_successor import get_successor_builder

		return get_successor_builder(
			plan_doc=plan_doc,
			actor=actor,
			organisation_unit=organisation_unit,
			status=status,
			search=search,
		)
	if approved:
		return {
			"ok": True, "redirect": True,
			"route": f"/app/procurement-plan-approved?plan={plan_name}",
			"reason": "Approved Plans use the approved Plan surface.",
		}
	if not draft or not frappe.db.exists("Procurement Plan Version", draft):
		frappe.throw(frappe._("The Plan has no initial Draft Version."), title="PLN_NO_OPEN_DRAFT")
	version = frappe.db.get_value(
		"Procurement Plan Version", draft,
		["name", "version_code", "version_number", "status", "validation_projection", "concurrency_token", "modified"], as_dict=True,
	)
	items = frappe.get_all(
		"Procurement Plan Item", filters={"plan": plan_name, "baseline_state": "Proposed"},
		fields=["name", "plan_item_code", "owner_org_unit", "draft_item_version", "baseline_state", "tender_takeup_projection"], order_by="creation asc", limit_page_length=500,
	)
	iv_ids = [row.draft_item_version for row in items if row.draft_item_version]
	fingerprint_fields = [
		"procurement_method", "arrangement", "lotting_decision", "lot_basis",
		"expected_lot_count", "proposed_removal", "ms_invitation_published",
		"ms_tender_opening", "ms_evaluation_completed", "ms_award_approval",
		"ms_notification_of_award",
		"ms_contract_signature", "ms_delivery_completion",
	]
	versions = frappe.get_all(
		"Procurement Plan Item Version", filters={"name": ["in", iv_ids]},
		fields=[
			"name", "plan_item", "requirement_title", "confirmed_estimate", "currency",
			"validation_projection", "finance_status", "finance_snapshot_amount",
			"finance_snapshot_budget_line", "modified", *fingerprint_fields,
		],
		limit_page_length=500,
	) if iv_ids else []
	iv_by_item = {row.plan_item: row for row in versions}
	ou_ids = [row.owner_org_unit for row in items if row.owner_org_unit]
	ou_labels = dict(frappe.get_all(
		"Organisation Unit", filters={"name": ["in", ou_ids]}, fields=["name", "unit_name"], as_list=True,
	)) if ou_ids else {}
	alloc_counts: dict[str, int] = defaultdict(int)
	item_demand_sets: dict[str, set[str]] = defaultdict(set)
	item_demands: dict[str, str] = {}
	if items:
		for row in frappe.get_all(
			"Plan Demand Allocation",
			filters={"plan_item": ["in", [r.name for r in items]], "status": "Draft"},
			fields=["plan_item", "demand"], limit_page_length=2000,
		):
			alloc_counts[row.plan_item] += 1
			item_demand_sets[row.plan_item].add(cstr(row.demand))
			item_demands.setdefault(row.plan_item, row.demand)
	item_names = [row.name for row in items]
	handoff_items = set()
	if item_names and frappe.db.exists("DocType", "Planning Handoff Snapshot"):
		handoff_items = set(
			frappe.get_all(
				"Planning Handoff Snapshot",
				filters={"plan_item": ["in", item_names]},
				pluck="plan_item",
			)
		)
	demand_ids = list(dict.fromkeys(item_demands.values()))
	demand_lines = {
		row.demand: cstr(row.budget_line)
		for row in (
			frappe.get_all(
				"Demand Funding Allocation",
				filters={"demand": ["in", demand_ids]}, fields=["demand", "budget_line"],
			)
			if demand_ids else []
		)
	}
	rows: list[dict[str, Any]] = []
	total = 0.0
	planning_complete = 0
	finance_confirmed = 0
	for item in items:
		iv = iv_by_item.get(item.name)
		if not iv:
			continue
		amount = flt(iv.confirmed_estimate)
		total += amount
		finance_status = effective_finance_status_from_values(
			status=iv.finance_status,
			snapshot_amount=iv.finance_snapshot_amount,
			snapshot_budget_line=iv.finance_snapshot_budget_line,
			live_amount=iv.confirmed_estimate,
			live_budget_line=demand_lines.get(item_demands.get(item.name, ""), ""),
		)
		state, action_label, action = _row_state(iv, finance_status)
		if cstr(iv.validation_projection) == "Ready":
			planning_complete += 1
		if finance_status == "Confirmed":
			finance_confirmed += 1
		blocked = item.name in handoff_items or (
			cstr(item.tender_takeup_projection).strip()
			and cstr(item.tender_takeup_projection).strip() != "Not taken up"
		)
		can_remove = bool(
			not is_planning_read_only(actor)
			and cstr(plan_doc.lifecycle_state) == "Open"
			and cstr(version.status) in ("Draft", "Returned")
			and not blocked
		)
		demand_count = len(item_demand_sets.get(item.name, set()))
		need_count = alloc_counts.get(item.name, 0)
		removal = {
			"can_remove_from_draft": can_remove,
			"can_propose_removal": False,
			"removal_variant": "draft" if can_remove else None,
			"finance_effect_kind": "reservation" if finance_status == "Confirmed" else ("awaiting" if finance_status == "Awaiting confirmation" else "none"),
			"finance_effect_copy": "Finance confirmation and its reservation will be reversed" if finance_status == "Confirmed" else ("The awaiting Finance task will be cancelled" if finance_status == "Awaiting confirmation" else "No funding confirmed; no reservation to release"),
			"sources_label": f"{demand_count} {'Demand' if demand_count == 1 else 'Demands'} · {need_count} {'Need Item' if need_count == 1 else 'Need Items'}",
		}
		rows.append({
			"plan_item": item.name, "plan_item_code": item.plan_item_code,
			"title": cstr(iv.requirement_title), "owner_org_unit": item.owner_org_unit,
			"owner_org_unit_label": cstr(ou_labels.get(item.owner_org_unit) or "Procuring Entity level"),
			"planned_value": amount, "planned_value_display": _money(amount, cstr(iv.currency or plan_doc.currency)),
			"planning_status": state,
			"planning_status_label": state,
			"finance_status": finance_status,
			"finance_status_label": finance_status,
			"validation_status": cstr(iv.validation_projection or "Not run"),
			"validation_status_label": cstr(iv.validation_projection or "Not run"),
			"source_count": alloc_counts.get(item.name, 0), "action": action, "action_label": action_label,
			"route": f"/app/procurement-plan-item-editor/{item.name}",
			"can_remove": can_remove,
			**removal,
		})
	all_rows = list(rows)
	ou_filter = cstr(organisation_unit).strip()
	status_filter = cstr(status).strip()
	query = cstr(search).strip().lower()
	if ou_filter and ou_filter not in ("all", "__all__"):
		rows = [row for row in rows if row["owner_org_unit"] == ou_filter]
	if status_filter and status_filter not in ("all", "__all__"):
		rows = [row for row in rows if row["planning_status"].lower().replace(" ", "_") == status_filter.lower().replace(" ", "_")]
	if query:
		rows = [row for row in rows if query in f"{row['plan_item_code']} {row['title']} {row['owner_org_unit_label']}".lower()]
	fingerprint_rows = []
	for row in versions:
		if int(row.proposed_removal or 0):
			continue
		fingerprint_rows.append({
			"item": row.plan_item,
			"estimate": f"{flt(row.confirmed_estimate):.2f}",
			"method": cstr(row.procurement_method or ""),
			"arrangement": cstr(row.arrangement or ""),
			"lotting": cstr(row.lotting_decision or ""),
			"lot_basis": cstr(row.lot_basis or ""),
			"lot_count": cstr(row.expected_lot_count or ""),
			**{field: cstr(row.get(field) or "") for field in fingerprint_fields if field.startswith("ms_")},
		})
	validation = effective_validation_status_from_rows(
		version=version.name, stored=cstr(version.validation_projection), rows=fingerprint_rows,
	)
	eligible = list_eligible_demands(plan=plan_name, user=actor)
	item_count = len(all_rows)
	read_only = is_planning_read_only(actor)
	all_complete = bool(item_count) and planning_complete == item_count
	all_finance = bool(item_count) and finance_confirmed == item_count
	return {
		"ok": True, "redirect": False, "state_id": "PLN-UI-03" if item_count == 0 else "PLN-UI-05",
		"plan": plan_name, "plan_code": plan_doc.plan_code, "title": plan_doc.title,
		"procuring_entity": plan_doc.procuring_entity,
		"procuring_entity_label": frappe.db.get_value("Procuring Entity", plan_doc.procuring_entity, "legal_name") or plan_doc.procuring_entity,
		"financial_year": plan_doc.financial_year, "period_start": str(plan_doc.period_start), "period_end": str(plan_doc.period_end),
		"currency": plan_doc.currency, "lifecycle_state": plan_doc.lifecycle_state,
		"version": version, "version_status": version.status, "version_number_label": f"Draft Version {int(version.version_number)}",
		"item_count": item_count, "planned_total": total, "planned_total_display": _money(total, plan_doc.currency),
		"planning_complete_count": planning_complete, "planning_complete_display": f"{planning_complete} of {item_count}",
		"finance_confirmed_count": finance_confirmed, "finance_confirmed_total": item_count,
		"finance_confirmed_display": f"{finance_confirmed} of {item_count}", "validation_projection": validation,
		"outstanding_count": sum(1 for row in all_rows if row["planning_status"] not in ("Complete", "Awaiting Finance")),
		"items": rows, "unfiltered_item_count": item_count, "empty": item_count == 0,
		"eligible_demand_count": eligible["eligible_demand_count"],
		"can_add_demand": not read_only and eligible["eligible_demand_count"] > 0,
		"can_save": False,
		"can_submit": bool(not read_only and all_complete and all_finance and validation == "Ready"),
		"read_only": read_only, "concurrency_token": cstr(version.concurrency_token),
		"organisation_unit_options": [{"id": key, "label": label} for key, label in sorted({(r["owner_org_unit"] or "__pe__", r["owner_org_unit_label"]) for r in all_rows}, key=lambda pair: pair[1])],
		"status_options": [{"id": key.lower().replace(" ", "_"), "label": key} for key in sorted({r["planning_status"] for r in all_rows})],
		"workspace_route": f"/app/planning-workspace?procuring_entity={plan_doc.procuring_entity}&financial_year={plan_doc.financial_year}",
	}
