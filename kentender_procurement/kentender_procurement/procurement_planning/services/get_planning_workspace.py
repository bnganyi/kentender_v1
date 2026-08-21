# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-015 — bounded, authoritative Procurement Planning workspace."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, flt

from kentender_core.services.org_scope_access import descendant_org_units, user_scope_rows
from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ALLOC_EFFECTIVE,
	FINANCE_AWAITING,
	FINANCE_CONFIRMED,
	FINANCE_NOT_REQUESTED,
	FINANCE_RETURNED,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VALIDATION_BLOCKED,
	VALIDATION_NEEDS_ATTENTION,
	VALIDATION_NOT_RUN,
	VALIDATION_READY,
	VALIDATION_STALE,
	VERSION_IN_REVIEW,
	VERSION_RETURNED,
)
from kentender_procurement.procurement_planning.services._invariants import period_dates_for_financial_year
from kentender_procurement.procurement_planning.services.plan_item_field_issues import MILESTONE_FIELDS
from kentender_procurement.procurement_planning.services.plan_item_finance import effective_finance_status_from_values
from kentender_procurement.procurement_planning.services.planning_context import resolve_planning_context
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ADD_DEMAND_ROLES,
	CONFIRM_PLAN_FUNDING_ROLES,
	CREATE_PLAN_ROLES,
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	READ_PLAN_ROLES,
	actor_funding_roles,
	actor_planning_roles,
	is_planning_read_only,
	require_operational_roles,
)
from kentender_procurement.procurement_planning.services.validate_plan import (
	effective_validation_status_from_rows,
	flt_str,
)


WORKSPACE_NO_PLAN = "NO_PLAN"
WORKSPACE_INITIAL_DRAFT_EMPTY = "INITIAL_DRAFT_EMPTY"
WORKSPACE_APPROVED_ACTIONABLE = "APPROVED_WITH_ACTIONABLE_WORK"
WORKSPACE_DRAFT_ACTION = "DRAFT_WITH_PLANNER_ACTION"
WORKSPACE_DRAFT_FINANCE = "DRAFT_AWAITING_FINANCE"
WORKSPACE_REVIEW = "VERSION_AWAITING_PROFESSIONAL_REVIEW"
WORKSPACE_APPROVED_NO_WORK = "APPROVED_NO_WORK"

FILTER_OPTIONS = (
	{"value": "all", "label": "All work"},
	{"value": "approved_demands", "label": "Approved Demands"},
	{"value": "plan_items", "label": "Plan Items"},
	{"value": "returned_work", "label": "Returned work"},
)
FILTER_KEYS = frozenset(option["value"] for option in FILTER_OPTIONS)


def plan_canvas_routes(plan_doc: Any) -> dict[str, str]:
	approved = cstr(plan_doc.current_approved_version).strip()
	draft = cstr(plan_doc.open_draft_version).strip()
	return {
		"approved_route": f"/app/procurement-plan-approved?plan={plan_doc.name}" if approved else "",
		"update_route": f"/app/procurement-plan-builder?plan={plan_doc.name}" if draft else "",
		"builder_route": f"/app/procurement-plan-builder?plan={plan_doc.name}",
	}


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def _labels(doctype: str, names: set[str], label_field: str) -> dict[str, str]:
	if not names:
		return {}
	rows = frappe.get_all(
		doctype,
		filters={"name": ["in", sorted(names)]},
		fields=["name", label_field],
		limit_page_length=0,
	)
	return {row.name: cstr(row.get(label_field) or row.name) for row in rows}


def _entity_labels(names: set[str]) -> dict[str, str]:
	if not names:
		return {}
	meta = frappe.get_meta("Procuring Entity")
	label_field = "legal_name" if meta.has_field("legal_name") else (
		"entity_name" if meta.has_field("entity_name") else "procuring_entity_name"
	)
	rows = frappe.get_all(
		"Procuring Entity",
		filters={"name": ["in", sorted(names)]},
		fields=["name", label_field],
		limit_page_length=0,
	)
	return {row.name: cstr(row.get(label_field) or row.name) for row in rows}


def _scope_index(actor: str) -> tuple[list[dict[str, str]], dict[str, set[str] | None]]:
	rows = [
		row
		for row in user_scope_rows(actor)
		if cstr(row.get("role")) in (READ_PLAN_ROLES | CONFIRM_PLAN_FUNDING_ROLES) and cstr(row.get("procuring_entity"))
	]
	pes = {cstr(row.get("procuring_entity")) for row in rows}
	labels = _entity_labels(pes)
	entities = [
		{"id": pe, "code": pe, "name": labels.get(pe, pe), "label": labels.get(pe, pe)}
		for pe in sorted(pes)
	]
	scope: dict[str, set[str] | None] = {}
	for pe in pes:
		pe_rows = [row for row in rows if cstr(row.get("procuring_entity")) == pe]
		if any(not cstr(row.get("organisation_unit")) for row in pe_rows):
			scope[pe] = None
			continue
		units: set[str] = set()
		for row in pe_rows:
			unit = cstr(row.get("organisation_unit"))
			if unit:
				units |= descendant_org_units(unit) if int(row.get("include_descendants") or 0) else {unit}
		scope[pe] = units
	return entities, scope


def _in_scope(scope: dict[str, set[str] | None], pe: str, org_unit: str | None) -> bool:
	if pe not in scope:
		return False
	units = scope[pe]
	return units is None or not org_unit or org_unit in units


def _base_payload(
	*, mode: str, entities: list[dict[str, str]], pe: str | None, pe_label: str,
	fy: str, read_only: bool, helper: str,
) -> dict[str, Any]:
	return {
		"ok": True,
		"selection_mode": mode,
		"workspace_state": None,
		"procuring_entities": entities,
		"procuring_entity": pe,
		"procuring_entity_label": pe_label,
		"financial_years": [],
		"financial_year": fy,
		"read_only": read_only,
		"helper_text": helper,
		"error_id": None,
		"blocked_reason": None,
		"current_plan": None,
		"primary_action": None,
		"filter_options": list(FILTER_OPTIONS),
		"show_work_controls": False,
		"work_requiring_action": [],
		"waiting_on_others": [],
		"work_queue": [],
		"counts": {"work_requiring_action": 0, "waiting_on_others": 0},
		"filtered_counts": {"work_requiring_action": 0, "waiting_on_others": 0},
		"empty_states": {
			"work_requiring_action": "No planning work currently needs your action.",
			"waiting_on_others": "Nothing is currently waiting on another reviewer.",
		},
		"can_create_plan": False,
		"eligible_demand_count": 0,
		"register_route": "/app/procurement-plan-register",
		"workspace_route": "/app/planning-workspace",
		"as_at": None,
		"as_at_display": "",
		"projection_token": "",
		"planning_context": None,
	}


def _action(code: str, label: str, route: str) -> dict[str, str]:
	return {"code": code, "label": label, "route": route}


def _version_rows(names: set[str]) -> dict[str, Any]:
	if not names:
		return {}
	rows = frappe.get_all(
		"Procurement Plan Version",
		filters={"name": ["in", sorted(names)]},
		fields=[
			"name", "version_code", "version_number", "status", "validation_projection",
			"concurrency_token", "version_reason", "review_task_id", "review_task_state",
			"review_task_assignee", "submitted_by", "submitted_at", "creation", "modified",
		],
		limit_page_length=0,
	)
	return {row.name: row for row in rows}


def _validation_inputs(ivs: list[Any]) -> list[dict[str, Any]]:
	inputs = []
	for iv in ivs:
		if int(iv.proposed_removal or 0):
			continue
		row = {
			"item": iv.plan_item,
			"estimate": flt_str(iv.confirmed_estimate),
			"method": cstr(iv.procurement_method or ""),
			"arrangement": cstr(iv.arrangement or ""),
			"lotting": cstr(iv.lotting_decision or ""),
			"lot_basis": cstr(iv.lot_basis or ""),
			"lot_count": cstr(iv.expected_lot_count or ""),
		}
		for field in MILESTONE_FIELDS:
			row[field] = cstr(iv.get(field) or "")
		inputs.append(row)
	return inputs


def _load_graph(plan: Any) -> dict[str, Any]:
	version_names = {
		name for name in (cstr(plan.current_approved_version), cstr(plan.open_draft_version)) if name
	}
	versions = _version_rows(version_names)
	items = frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan.name, "baseline_state": ["in", [ITEM_ACTIVE, ITEM_PROPOSED]]},
		fields=["name", "plan_item_code", "baseline_state", "owner_org_unit", "modified"],
		order_by="creation asc",
		limit_page_length=0,
	)
	item_names = [item.name for item in items]
	iv_fields = [
		"name", "plan_item", "plan_version", "requirement_title", "confirmed_estimate",
		"currency", "finance_status", "finance_snapshot_amount", "finance_snapshot_budget_line",
		"finance_task_id", "finance_task_state", "finance_task_assignee",
		"validation_projection", "procurement_method", "arrangement", "lotting_decision",
		"lot_basis", "expected_lot_count", "proposed_removal", "carry_forward_unchanged",
		"draft_change_label", "requirement_description", "procurement_category", "modified",
		*MILESTONE_FIELDS,
	]
	ivs = (
		frappe.get_all(
			"Procurement Plan Item Version",
			filters={"plan_item": ["in", item_names], "plan_version": ["in", sorted(version_names)]},
			fields=iv_fields,
			limit_page_length=0,
		)
		if item_names and version_names else []
	)
	allocations = (
		frappe.get_all(
			"Plan Demand Allocation",
			filters={"plan_item": ["in", item_names], "status": ["in", [ALLOC_DRAFT, ALLOC_EFFECTIVE]]},
			fields=["plan_item", "demand", "status", "allocated_amount", "modified"],
			limit_page_length=0,
		)
		if item_names else []
	)
	demand_names = {cstr(row.demand) for row in allocations if row.demand}
	dfas = (
		frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": ["in", sorted(demand_names)]},
			fields=["demand", "budget_line"],
			limit_page_length=0,
		)
		if demand_names and frappe.db.exists("DocType", "Demand Funding Allocation") else []
	)
	line_by_demand = {row.demand: cstr(row.budget_line) for row in dfas}
	demand_by_item: dict[str, str] = {}
	for row in allocations:
		demand_by_item.setdefault(row.plan_item, cstr(row.demand))
	for iv in ivs:
		iv.effective_finance_status = effective_finance_status_from_values(
			status=iv.finance_status,
			snapshot_amount=iv.finance_snapshot_amount,
			snapshot_budget_line=iv.finance_snapshot_budget_line,
			live_amount=iv.confirmed_estimate,
			live_budget_line=line_by_demand.get(demand_by_item.get(iv.plan_item, ""), ""),
		)
	iv_by_version: dict[str, list[Any]] = defaultdict(list)
	for iv in ivs:
		iv_by_version[iv.plan_version].append(iv)
	return {"versions": versions, "items": items, "iv_by_version": iv_by_version, "allocations": allocations}


def _is_incomplete(iv: Any) -> bool:
	required = (
		"requirement_description", "procurement_category", "procurement_method",
		"arrangement", "lotting_decision", *MILESTONE_FIELDS,
	)
	return any(not cstr(iv.get(field) or "").strip() for field in required)


def _version_projection(version: Any | None, ivs: list[Any], currency: str) -> dict[str, Any] | None:
	if not version:
		return None
	included = [iv for iv in ivs if not int(iv.proposed_removal or 0)]
	confirmed = sum(iv.effective_finance_status == FINANCE_CONFIRMED for iv in included)
	planning_complete = sum(not _is_incomplete(iv) for iv in included)
	validation = effective_validation_status_from_rows(
		version=version.name,
		stored=version.validation_projection,
		rows=_validation_inputs(included),
	)
	total = sum(flt(iv.confirmed_estimate) for iv in included)
	return {
		"version": version.name,
		"version_code": cstr(version.version_code or version.name),
		"version_number": int(version.version_number or 0),
		"status": cstr(version.status),
		"item_count": len(included),
		"planned_total": total,
		"planned_total_display": _money(total, currency),
		"planning_complete_count": planning_complete,
		"planning_complete_label": f"{planning_complete} of {len(included)}",
		"finance_confirmed_count": confirmed,
		"finance_item_count": len(included),
		"finance_confirmed_label": f"{confirmed} of {len(included)}",
		"validation_projection": validation,
		"concurrency_token": cstr(version.concurrency_token),
		"submitted_by": cstr(version.submitted_by),
		"submitted_at": str(version.submitted_at or ""),
		"modified": str(version.modified or ""),
	}


def _has_effective_changes(items: list[Any], draft_ivs: list[Any]) -> bool:
	state = {item.name: item.baseline_state for item in items}
	return any(
		state.get(iv.plan_item) == ITEM_PROPOSED
		or int(iv.proposed_removal or 0)
		or not int(iv.carry_forward_unchanged or 0)
		for iv in draft_ivs
	)


def _work_row(
	*, resource_key: str, reference: str, title: str, work_type: str,
	org_unit: str, org_label: str, amount: float, currency: str, reason: str,
	status: str, filter_key: str, priority: int, action: dict[str, str],
) -> dict[str, Any]:
	return {
		"resource_key": resource_key,
		"reference": reference,
		"title": title,
		"work_type": work_type,
		"organisation_unit": org_unit,
		"organisation_unit_label": org_label or org_unit,
		"amount": flt(amount),
		"amount_display": _money(amount, currency),
		"reason": reason,
		"status": status,
		"filter_key": filter_key,
		"priority": priority,
		"action": action,
	}


def _waiting_row(*, resource_key: str, reference: str, title: str, stage: str, status: str, with_role: str) -> dict[str, str]:
	return {
		"resource_key": resource_key,
		"reference": reference,
		"title": title,
		"stage": stage,
		"status": status,
		"with_role": with_role,
	}


def _matches(row: dict[str, Any], work_filter: str, search: str) -> bool:
	if work_filter != "all" and row["filter_key"] != work_filter:
		return False
	if not search:
		return True
	haystack = " ".join(
		cstr(row.get(key))
		for key in ("reference", "title", "work_type", "organisation_unit_label", "reason", "status")
	).lower()
	return search.lower() in haystack


def _metric(label: str, value: str, kind: str = "text", status: str = "") -> dict[str, str]:
	return {"label": label, "value": value, "kind": kind, "status": status}


def _as_at(values: list[Any]) -> tuple[str | None, str]:
	candidates: list[datetime] = []
	for value in values:
		if not value:
			continue
		try:
			candidates.append(frappe.utils.get_datetime(value))
		except Exception:
			continue
	if not candidates:
		return None, ""
	value = max(candidates)
	return str(value), f"{value.day} {value.strftime('%B %Y, %H:%M')} EAT"


def _projection_token(payload: dict[str, Any], evidence: list[Any]) -> str:
	canonical = {
		"pe": payload.get("procuring_entity"),
		"fy": payload.get("financial_year"),
		"state": payload.get("workspace_state"),
		"evidence": [cstr(value) for value in evidence if value],
		"work": [row.get("resource_key") for row in payload.get("work_requiring_action") or []],
		"waiting": [row.get("resource_key") for row in payload.get("waiting_on_others") or []],
	}
	return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()[:24]


def _eligible_source_rows(*, plan: Any, actor: str, actor_roles: set[str]) -> list[dict[str, Any]]:
	if not actor_roles.intersection(ADD_DEMAND_ROLES):
		return []
	from kentender_procurement.procurement_planning.services.list_eligible_demands import list_eligible_demands
	return list_eligible_demands(plan=plan.name, user=actor)["demands"]


def _eligible_context_rows(*, pe: str, fy: str, actor: str, actor_roles: set[str]) -> list[dict[str, Any]]:
	if not actor_roles.intersection(ADD_DEMAND_ROLES):
		return []
	from kentender_procurement.procurement_planning.services.list_eligible_demands import project_eligible_demands_for_context
	start, end = period_dates_for_financial_year(fy)
	currency = cstr(frappe.db.get_value("Procuring Entity", pe, "reporting_currency") or "KES")
	return project_eligible_demands_for_context(
		procuring_entity=pe, financial_year=fy, period_start=start, period_end=end,
		currency=currency, user=actor,
	)


def get_planning_workspace(
	*, procuring_entity: str | None = None, financial_year: str | None = None,
	work_filter: str | None = "all", search: str | None = None, user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user).strip()
	if not actor or actor == "Guest":
		frappe.throw(frappe._("Login required."), frappe.PermissionError, title="PLN_LOGIN_REQUIRED")
	actor_roles = actor_planning_roles(actor)
	finance_roles = actor_funding_roles(actor)
	finance_actor = bool(finance_roles.intersection(CONFIRM_PLAN_FUNDING_ROLES))
	if finance_actor and not actor_roles:
		frappe.throw(
			frappe._("Finance decision work is available from My work, not the Procurement Planning workspace."),
			frappe.PermissionError,
			title="PLN_USE_MY_WORK",
		)
	# A combined-role actor may use the Planner workspace, but task decisions remain
	# available only from the shared My work projection and protected task loader.
	finance_actor = False
	if not finance_actor:
		require_operational_roles(*READ_PLAN_ROLES, user=actor)
	read_only = True if finance_actor and not actor_roles else is_planning_read_only(actor)
	entities, scope = _scope_index(actor)
	finance_pe = cstr(procuring_entity).strip()
	finance_fy = cstr(financial_year).strip()
	if finance_actor and (not finance_pe or not finance_fy):
		assigned_version = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"finance_task_assignee": actor, "finance_task_state": "Open"},
			"plan_version",
		)
		assigned_plan = (
			frappe.db.get_value(
				"Procurement Plan",
				{"open_draft_version": assigned_version},
				["procuring_entity", "financial_year"],
				as_dict=True,
			)
			if assigned_version else None
		)
		if assigned_plan:
			finance_pe = finance_pe or cstr(assigned_plan.procuring_entity)
			finance_fy = finance_fy or cstr(assigned_plan.financial_year)
	context = resolve_planning_context(
		procuring_entity=finance_pe if finance_actor else procuring_entity,
		financial_year=finance_fy if finance_actor else financial_year,
		user=actor,
	)
	if finance_actor and finance_pe in scope:
		context.update({
			"procuring_entity": finance_pe,
			"financial_year": finance_fy,
			"procuring_entities": entities,
			"selection_source": "selected" if procuring_entity else "assigned_finance_task",
			"selection_required": False,
			"no_scope": False,
		})
	fy = cstr(context.get("financial_year"))
	helper = (
		"Read-only support view. These controls filter visibility; they do not grant ownership or operational Planning authority."
		if read_only else "These controls define the workspace view; they do not change record ownership."
	)
	labels = {entity["id"]: entity["name"] for entity in entities}
	if not entities:
		payload = _base_payload(mode=MODE_BLOCKED, entities=[], pe=None, pe_label="", fy=fy, read_only=True, helper=helper)
		payload["planning_context"] = context
		payload["blocked_reason"] = "No operational Planning assignment exists."
		return payload
	pe = cstr(context.get("procuring_entity")).strip()
	mode = MODE_SINGLE if len(entities) == 1 else MODE_MULTI
	if not pe or context.get("selection_required"):
		payload = _base_payload(mode=MODE_MULTI, entities=entities, pe=None, pe_label="", fy=fy, read_only=read_only, helper=helper)
		payload["planning_context"] = context
		payload["financial_years"] = context.get("financial_years") or []
		return payload
	payload = _base_payload(mode=mode, entities=entities, pe=pe, pe_label=labels[pe], fy=fy, read_only=read_only, helper=helper)
	payload["planning_context"] = context
	payload["procuring_entities"] = context["procuring_entities"]
	payload["financial_years"] = context["financial_years"]
	can_create = not read_only and bool(actor_roles.intersection(CREATE_PLAN_ROLES))
	payload["can_create_plan"] = can_create
	plan_row = frappe.db.get_value(
		"Procurement Plan", {"procuring_entity": pe, "financial_year": fy},
		["name", "plan_code", "title", "lifecycle_state", "currency", "current_approved_version", "open_draft_version", "financial_year", "period_start", "period_end", "modified"],
		as_dict=True,
	)
	if not plan_row:
		eligible = _eligible_context_rows(pe=pe, fy=fy, actor=actor, actor_roles=actor_roles)
		payload["workspace_state"] = WORKSPACE_NO_PLAN
		payload["eligible_demand_count"] = len(eligible)
		payload["empty_states"].update({
			"current_plan_heading": "No annual Procurement Plan",
			"current_plan": f"No Procurement Plan has been registered for {labels[pe]} for FY {fy}.",
			"current_plan_supporting": f"Create the annual Plan before adding the {len(eligible)} Approved Demands ready for Planning.",
			"work_requiring_action": "Create the annual Plan to begin Planning approved requirements.",
		})
		if can_create:
			payload["primary_action"] = _action("create_plan", "Create annual plan", f"/app/procurement-plan-register?procuring_entity={quote(pe)}&financial_year={quote(fy)}")
		payload["projection_token"] = _projection_token(payload, [pe, fy, len(eligible)])
		return payload

	plan = frappe.get_doc("Procurement Plan", plan_row.name)
	plan.reload()
	graph = _load_graph(plan)
	approved_version = graph["versions"].get(cstr(plan.current_approved_version))
	draft_version = graph["versions"].get(cstr(plan.open_draft_version))
	approved_ivs = graph["iv_by_version"].get(cstr(plan.current_approved_version), [])
	draft_ivs = graph["iv_by_version"].get(cstr(plan.open_draft_version), [])
	approved = _version_projection(approved_version, approved_ivs, plan.currency or "KES")
	draft = _version_projection(draft_version, draft_ivs, plan.currency or "KES")
	routes = plan_canvas_routes(plan)
	has_changes = bool(draft and approved and _has_effective_changes(graph["items"], draft_ivs))
	eligible_sources = _eligible_source_rows(plan=plan, actor=actor, actor_roles=actor_roles)
	payload["eligible_demand_count"] = len(eligible_sources)

	all_ous = {cstr(item.owner_org_unit) for item in graph["items"] if item.owner_org_unit}
	all_ous |= {cstr(row.get("organisation_unit")) for row in eligible_sources if row.get("organisation_unit")}
	ou_labels = _labels("Organisation Unit", all_ous, "unit_name")
	item_by_name = {item.name: item for item in graph["items"]}
	work: list[dict[str, Any]] = []
	waiting: list[dict[str, str]] = []
	if draft and (not read_only or finance_actor):
		if not read_only and actor_roles.intersection(ADD_DEMAND_ROLES) and cstr(draft_version.status) == VERSION_RETURNED:
			work.append(_work_row(resource_key=f"plan:{plan.name}", reference=cstr(draft["version_code"]), title=plan.title, work_type="Plan update", org_unit="", org_label=labels[pe], amount=draft["planned_total"], currency=plan.currency, reason="The plan update was returned by the Head of Procurement for correction.", status="Returned by Head of Procurement", filter_key="returned_work", priority=10, action=_action("address_return", "Address return", routes["update_route"])))
		elif not read_only and actor_roles.intersection(ADD_DEMAND_ROLES) and approved and not has_changes:
			work.append(_work_row(resource_key=f"plan:{plan.name}", reference=cstr(draft["version_code"]), title=plan.title, work_type="Plan update", org_unit="", org_label=labels[pe], amount=draft["planned_total"], currency=plan.currency, reason=f"No effective changes remain in Draft Version {draft['version_number']}.", status="No changes", filter_key="plan_items", priority=30, action=_action("cancel_update", "Cancel update", routes["update_route"])))
		for iv in draft_ivs:
			if int(iv.proposed_removal or 0):
				continue
			item = item_by_name.get(iv.plan_item)
			if not item or not _in_scope(scope, pe, item.owner_org_unit):
				continue
			base = {"resource_key": f"item:{item.name}", "reference": cstr(item.plan_item_code or item.name), "title": cstr(iv.requirement_title or item.plan_item_code), "work_type": "Plan Item", "org_unit": cstr(item.owner_org_unit), "org_label": ou_labels.get(cstr(item.owner_org_unit), cstr(item.owner_org_unit)), "amount": flt(iv.confirmed_estimate), "currency": cstr(iv.currency or plan.currency or "KES")}
			if finance_actor:
				if cstr(iv.finance_task_state) == "Open" and cstr(iv.finance_task_assignee) == actor and cstr(iv.finance_task_id):
					work.append(_work_row(**base, reason="Confirm that the full source-approved value is available for reservation.", status="Awaiting confirmation", filter_key="plan_items", priority=5, action=_action("review_funding", "Review funding", f"/app/procurement-plan-builder?plan={plan.name}&finance_task={cstr(iv.finance_task_id)}")))
				continue
			item_route = f"/app/procurement-plan-item-editor?plan_item={item.name}"
			finance = cstr(iv.effective_finance_status or FINANCE_NOT_REQUESTED)
			validation = cstr(iv.validation_projection or VALIDATION_NOT_RUN)
			if finance == FINANCE_RETURNED:
				work.append(_work_row(**base, reason="Finance returned this item for correction.", status="Returned by Finance", filter_key="returned_work", priority=10, action=_action("correct_item", "Correct item", item_route)))
			elif validation in (VALIDATION_BLOCKED, VALIDATION_STALE):
				work.append(_work_row(**base, reason="Blocking or stale validation must be resolved.", status=validation, filter_key="plan_items", priority=20, action=_action("resolve_issues", "Resolve issues", item_route)))
			elif item.baseline_state == ITEM_PROPOSED and _is_incomplete(iv):
				work.append(_work_row(**base, reason="Complete the procurement method and schedule before requesting Finance confirmation.", status="Planning incomplete", filter_key="plan_items", priority=30, action=_action("complete_item", "Complete item", item_route)))
			elif validation == VALIDATION_NEEDS_ATTENTION and finance != FINANCE_AWAITING:
				work.append(_work_row(**base, reason="Planning validation needs attention.", status="Needs attention", filter_key="plan_items", priority=20, action=_action("resolve_issues", "Resolve issues", item_route)))
			elif finance == FINANCE_AWAITING and cstr(iv.finance_task_state) == "Open":
				task_owner = frappe.db.get_value("Workflow Task", cstr(iv.finance_task_id), ["assigned_user_id", "queue_id"], as_dict=True)
				with_actor = cstr((task_owner or {}).get("assigned_user_id") or (task_owner or {}).get("queue_id") or "Routing unavailable")
				waiting.append(_waiting_row(resource_key=f"item:{item.name}", reference=cstr(item.plan_item_code or item.name), title=cstr(iv.requirement_title or item.plan_item_code), stage="Finance confirmation", status="Awaiting confirmation", with_role=with_actor))
			elif finance == FINANCE_AWAITING:
				work.append(_work_row(**base, reason="Finance confirmation evidence is incomplete; reopen the item to resolve it.", status="Needs attention", filter_key="plan_items", priority=20, action=_action("resolve_issues", "Resolve issues", item_route)))

	open_review = bool(draft_version and cstr(draft_version.status) == VERSION_IN_REVIEW and cstr(draft_version.review_task_id) and cstr(draft_version.review_task_state) == "Open")
	if open_review:
		work = []
		task_owner = frappe.db.get_value("Workflow Task", cstr(draft_version.review_task_id), ["assigned_user_id", "queue_id"], as_dict=True)
		with_actor = cstr((task_owner or {}).get("assigned_user_id") or (task_owner or {}).get("queue_id") or "Routing unavailable")
		waiting = [_waiting_row(resource_key=f"review:{draft_version.name}", reference=cstr(draft_version.version_code or draft_version.name), title=f"{plan.title} — Version {int(draft_version.version_number or 0)}", stage="Professional review", status="Awaiting review", with_role=with_actor)]
	if finance_actor:
		work = [row for row in work if cstr((row.get("action") or {}).get("code")) == "review_funding"]
		waiting = []
	if draft and approved and has_changes and not work and not waiting and not open_review and not read_only:
		work.append(_work_row(resource_key=f"plan:{plan.name}", reference=cstr(draft["version_code"]), title=plan.title, work_type="Plan update", org_unit="", org_label=labels[pe], amount=draft["planned_total"], currency=plan.currency, reason="This Draft update is ready for the next Planning action.", status="Needs attention", filter_key="plan_items", priority=30, action=_action("continue_update", "Continue update", routes["update_route"])))

	if draft and not approved and draft["item_count"] == 0:
		workspace_state = WORKSPACE_INITIAL_DRAFT_EMPTY
	elif open_review:
		workspace_state = WORKSPACE_REVIEW
	elif draft and work:
		workspace_state = WORKSPACE_DRAFT_ACTION
	elif draft and waiting:
		workspace_state = WORKSPACE_DRAFT_FINANCE
	elif approved and not draft and eligible_sources and not read_only:
		workspace_state = WORKSPACE_APPROVED_ACTIONABLE
	elif draft:
		workspace_state = WORKSPACE_DRAFT_ACTION
	else:
		workspace_state = WORKSPACE_APPROVED_NO_WORK

	if workspace_state in (WORKSPACE_INITIAL_DRAFT_EMPTY, WORKSPACE_APPROVED_ACTIONABLE):
		for demand in eligible_sources:
			reason = f"Approved Demand is ready to add to the FY {fy} Plan." if workspace_state == WORKSPACE_INITIAL_DRAFT_EMPTY else f"HoD-approved Demand is ready to add to the FY {fy} Plan."
			route = routes["approved_route"] if approved else routes["builder_route"]
			row = _work_row(resource_key=f"demand:{demand['demand']}", reference=cstr(demand["demand_code"] or demand["demand"]), title=cstr(demand["title"] or demand["demand"]), work_type="Approved Demand", org_unit=cstr(demand["organisation_unit"]), org_label=cstr(demand["organisation_unit_label"]), amount=flt(demand["available_to_plan"]), currency=cstr(demand["currency"] or plan.currency or "KES"), reason=reason, status="Ready for planning", filter_key="approved_demands", priority=40, action=_action("add_to_plan", "Add to plan", f"{route}{'&' if '?' in route else '?'}add_demand={quote(demand['demand'])}"))
			row["demand"] = demand["demand"]
			work.append(row)

	deduped: dict[str, dict[str, Any]] = {}
	for row in sorted(work, key=lambda value: (value["priority"], value["reference"])):
		deduped.setdefault(row["resource_key"], row)
	unfiltered_work = list(deduped.values())
	selected_filter = cstr(work_filter or "all").strip() or "all"
	if selected_filter not in FILTER_KEYS:
		selected_filter = "all"
	needle = cstr(search).strip()
	filtered_work = [row for row in unfiltered_work if _matches(row, selected_filter, needle)][:50]
	payload["workspace_state"] = workspace_state
	payload["show_work_controls"] = workspace_state == WORKSPACE_APPROVED_ACTIONABLE
	payload["work_requiring_action"] = filtered_work
	payload["waiting_on_others"] = waiting[:50]
	payload["work_queue"] = filtered_work
	payload["counts"] = {"work_requiring_action": len(unfiltered_work), "waiting_on_others": len(waiting)}
	payload["filtered_counts"] = {"work_requiring_action": len(filtered_work), "waiting_on_others": len(waiting)}

	status_parts = [f"{plan.lifecycle_state} Plan"]
	if approved:
		status_parts.append(f"Approved Version {approved['version_number']}")
	if draft:
		status_parts.append(f"Version {draft['version_number']} in review" if workspace_state == WORKSPACE_REVIEW else f"Draft Version {draft['version_number']}")
	metrics: list[dict[str, str]] = []
	if workspace_state == WORKSPACE_INITIAL_DRAFT_EMPTY:
		supporting = "The annual Plan is ready for its first Approved Demands."
		metrics = [_metric("Plan Items", "0"), _metric("Draft planned value", _money(0, plan.currency), "money"), _metric("Approved Demands available", str(len(eligible_sources))), _metric("Validation", "Not run", "validation", "Not run")]
		payload["primary_action"] = None if read_only else _action("continue_planning", "Continue planning", routes["builder_route"])
	elif workspace_state == WORKSPACE_DRAFT_ACTION:
		supporting = f"No changes remain in Draft Version {draft['version_number']}." if approved and not has_changes else (f"Approved Version {approved['version_number']} remains active while Draft Version {draft['version_number']} is prepared." if approved else "The initial Draft is being prepared.")
		if approved:
			delta = draft["planned_total"] - approved["planned_total"]
			metrics.extend([_metric("Approved value", approved["planned_total_display"], "money"), _metric("Draft value", draft["planned_total_display"], "money"), _metric("Net change", f"{_money(abs(delta), plan.currency)} {'added' if delta >= 0 else 'removed'}", "money")])
		metrics.extend([_metric("Planning complete", draft["planning_complete_label"]), _metric("Finance confirmed", draft["finance_confirmed_label"], "finance"), _metric("Validation", VALIDATION_NEEDS_ATTENTION if work else draft["validation_projection"], "validation", VALIDATION_NEEDS_ATTENTION if work else draft["validation_projection"])])
		payload["primary_action"] = None if read_only else _action("continue_plan_update", "Continue plan update", routes["update_route"])
	elif workspace_state == WORKSPACE_DRAFT_FINANCE:
		supporting = f"Approved Version {approved['version_number']} remains active while Finance reviews the added Plan Item."
		delta = draft["planned_total"] - approved["planned_total"]
		metrics = [_metric("Draft Plan Items", str(draft["item_count"])), _metric("Draft planned value", draft["planned_total_display"], "money"), _metric("Net change", f"{_money(abs(delta), plan.currency)} {'added' if delta >= 0 else 'removed'}", "money"), _metric("Planning complete", draft["planning_complete_label"]), _metric("Finance confirmed", draft["finance_confirmed_label"], "finance"), _metric("Validation", VALIDATION_NEEDS_ATTENTION, "validation", VALIDATION_NEEDS_ATTENTION)]
		payload["primary_action"] = None if read_only else _action("view_plan_update", "View plan update", routes["update_route"])
	elif workspace_state == WORKSPACE_REVIEW:
		supporting = f"Approved Version {approved['version_number']} remains active while Version {draft['version_number']} awaits Head-of-Procurement review."
		delta = draft["planned_total"] - approved["planned_total"]
		metrics = [_metric("Submitted value", draft["planned_total_display"], "money"), _metric("Net change", f"{_money(abs(delta), plan.currency)} {'added' if delta >= 0 else 'removed'}", "money"), _metric("Finance confirmed", draft["finance_confirmed_label"], "finance"), _metric("Validation", VALIDATION_READY, "validation", VALIDATION_READY)]
		payload["primary_action"] = _action("view_approved_plan", "View approved plan", routes["approved_route"])
	else:
		supporting = "No plan update is currently in progress."
		metrics = [_metric("Plan Items", f"{approved['item_count']} active"), _metric("Approved value", approved["planned_total_display"], "money"), _metric("Finance confirmed", approved["finance_confirmed_label"], "finance"), _metric("Validation", approved["validation_projection"], "validation", approved["validation_projection"])]
		payload["primary_action"] = _action("view_approved_plan", "View approved plan", routes["approved_route"])

	payload["current_plan"] = {
		"plan": plan.name, "plan_code": plan.plan_code, "title": plan.title,
		"lifecycle_state": plan.lifecycle_state, "currency": plan.currency or "KES",
		"current_approved_version": plan.current_approved_version, "open_draft_version": plan.open_draft_version,
		"approved": approved, "draft": draft, "status_line": " · ".join(status_parts),
		"status_parts": status_parts, "supporting_text": supporting, "summary_metrics": metrics, **routes,
	}
	evidence = [plan.modified]
	for version in (approved_version, draft_version):
		if version:
			evidence.extend([version.modified, version.concurrency_token, version.review_task_state, version.submitted_at])
	for iv in approved_ivs + draft_ivs:
		evidence.extend([iv.modified, iv.finance_task_state])
	payload["as_at"], payload["as_at_display"] = _as_at(evidence)
	payload["projection_token"] = _projection_token(payload, evidence)
	return payload
