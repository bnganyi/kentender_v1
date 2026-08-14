# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-001 — bounded, server-scoped Planning workspace projection."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, flt, getdate

from kentender_core.services.org_scope_access import descendant_org_units, user_scope_rows
from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ALLOC_EFFECTIVE,
	FINANCE_AWAITING,
	FINANCE_CONFIRMED,
	FINANCE_NOT_REQUESTED,
	FINANCE_RETURNED,
	FINANCE_STALE,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VALIDATION_BLOCKED,
	VALIDATION_NEEDS_ATTENTION,
	VALIDATION_NOT_RUN,
	VALIDATION_READY,
	VALIDATION_STALE,
	VERSION_DRAFT,
	VERSION_IN_REVIEW,
	VERSION_RETURNED,
)
from kentender_procurement.procurement_planning.services._invariants import (
	period_dates_for_financial_year,
)
from kentender_procurement.procurement_planning.services.get_plan_update import (
	plan_canvas_routes,
)
from kentender_procurement.procurement_planning.services.plan_item_field_issues import (
	MILESTONE_FIELDS,
)
from kentender_procurement.procurement_planning.services.plan_item_finance import (
	effective_finance_status_from_values,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ADD_DEMAND_ROLES,
	CREATE_PLAN_ROLES,
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	READ_PLAN_ROLES,
	actor_planning_roles,
	is_planning_read_only,
	require_operational_roles,
)
from kentender_procurement.procurement_planning.services.validate_plan import (
	effective_validation_status_from_rows,
	flt_str,
)


FILTER_OPTIONS = (
	{"value": "all", "label": "All work"},
	{"value": "approved_demands", "label": "Approved Demands"},
	{"value": "plan_items", "label": "Plan Items"},
	{"value": "returned_work", "label": "Returned work"},
)
FILTER_KEYS = frozenset(option["value"] for option in FILTER_OPTIONS)

STATE_BLOCKED = "blocked_no_scope"
STATE_SELECTION = "selection_required"
STATE_NO_PLAN = "no_plan"
STATE_INITIAL_DRAFT = "initial_draft"
STATE_APPROVED = "approved_only"
STATE_UPDATE = "approved_with_draft"
STATE_NO_CHANGES = "no_effective_changes"


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def _fy_options(selected: str) -> list[dict[str, str]]:
	values = ["2027/28", "2028/29", "2029/30"]
	if selected and selected not in values:
		values.append(selected)
	return [{"id": value, "label": value} for value in values]


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
	fields = ["name"]
	meta = frappe.get_meta("Procuring Entity")
	label_field = "entity_name" if meta.has_field("entity_name") else "procuring_entity_name"
	fields.append(label_field)
	rows = frappe.get_all(
		"Procuring Entity",
		filters={"name": ["in", sorted(names)]},
		fields=fields,
		limit_page_length=0,
	)
	return {row.name: cstr(row.get(label_field) or row.name) for row in rows}


def _scope_index(actor: str) -> tuple[list[dict[str, str]], dict[str, set[str] | None]]:
	"""Resolve Planning USA rows once; Administrator receives no implicit authority."""
	rows = [
		row
		for row in user_scope_rows(actor)
		if cstr(row.get("role")) in READ_PLAN_ROLES and cstr(row.get("procuring_entity"))
	]
	pes = {cstr(row.get("procuring_entity")) for row in rows}
	pe_labels = _entity_labels(pes)
	entities = [
		{"id": pe, "code": pe, "name": pe_labels.get(pe, pe), "label": pe_labels.get(pe, pe)}
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
			if not unit:
				continue
			units |= descendant_org_units(unit) if int(row.get("include_descendants") or 0) else {unit}
		scope[pe] = units
	return entities, scope


def _in_scope(scope: dict[str, set[str] | None], pe: str, org_unit: str | None) -> bool:
	if pe not in scope:
		return False
	units = scope[pe]
	return units is None or not org_unit or org_unit in units


def _base_payload(
	*,
	mode: str,
	entities: list[dict[str, str]],
	pe: str | None,
	pe_label: str,
	fy: str,
	read_only: bool,
	state_id: str,
	helper: str,
) -> dict[str, Any]:
	return {
		"ok": True,
		"selection_mode": mode,
		"procuring_entities": entities,
		"procuring_entity": pe,
		"procuring_entity_label": pe_label,
		"financial_years": _fy_options(fy),
		"financial_year": fy,
		"read_only": read_only,
		"helper_text": helper,
		"state_id": state_id,
		"error_id": None,
		"blocked_reason": None,
		"current_plan": None,
		"primary_action": None,
		"filter_options": list(FILTER_OPTIONS),
		"work_requiring_action": [],
		"waiting_on_others": [],
		"work_queue": [],
		"counts": {"work_requiring_action": 0, "waiting_on_others": 0},
		"empty_states": {
			"work_requiring_action": "Nothing currently requires your planning action.",
			"waiting_on_others": "Nothing is currently waiting on another reviewer.",
		},
		"can_create_plan": False,
		"register_route": "/app/procurement-plan-register",
		"workspace_route": "/app/planning-workspace",
	}


def _action(code: str, label: str, route: str) -> dict[str, str]:
	return {"code": code, "label": label, "route": route}


def _version_rows(names: set[str]) -> dict[str, Any]:
	if not names:
		return {}
	rows = frappe.get_all(
		"Procurement Plan Version",
		filters={"name": ["in", sorted(names)]},
		fields=["name", "version_number", "status", "validation_projection"],
		limit_page_length=0,
	)
	return {row.name: row for row in rows}


def _validation_inputs(iv_rows: list[Any]) -> list[dict[str, Any]]:
	inputs = []
	for iv in iv_rows:
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
		name
		for name in (cstr(plan.current_approved_version), cstr(plan.open_draft_version))
		if name
	}
	versions = _version_rows(version_names)
	items = frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan.name, "baseline_state": ["in", [ITEM_ACTIVE, ITEM_PROPOSED]]},
		fields=["name", "plan_item_code", "baseline_state", "owner_org_unit"],
		order_by="creation asc",
		limit_page_length=0,
	)
	item_names = [item.name for item in items]
	iv_fields = [
		"name", "plan_item", "plan_version", "requirement_title", "confirmed_estimate",
		"currency", "finance_status", "finance_snapshot_amount", "finance_snapshot_budget_line",
		"validation_projection", "procurement_method", "arrangement", "lotting_decision",
		"lot_basis", "expected_lot_count", "proposed_removal", "carry_forward_unchanged",
		"draft_change_label", "requirement_description", "procurement_category",
		*MILESTONE_FIELDS,
	]
	ivs = (
		frappe.get_all(
			"Procurement Plan Item Version",
			filters={"plan_item": ["in", item_names], "plan_version": ["in", sorted(version_names)]},
			fields=iv_fields,
			limit_page_length=0,
		)
		if item_names and version_names
		else []
	)
	allocations = (
		frappe.get_all(
			"Plan Demand Allocation",
			filters={"plan_item": ["in", item_names], "status": ["in", [ALLOC_DRAFT, ALLOC_EFFECTIVE]]},
			fields=["plan_item", "demand", "status", "allocated_amount"],
			limit_page_length=0,
		)
		if item_names
		else []
	)
	demand_names = {cstr(row.demand) for row in allocations if row.demand}
	dfas = (
		frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": ["in", sorted(demand_names)]},
			fields=["demand", "budget_line"],
			limit_page_length=0,
		)
		if demand_names and frappe.db.exists("DocType", "Demand Funding Allocation")
		else []
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
	iv_by_key: dict[tuple[str, str], Any] = {}
	for iv in ivs:
		iv_by_version[iv.plan_version].append(iv)
		iv_by_key[(iv.plan_item, iv.plan_version)] = iv
	return {
		"versions": versions,
		"items": items,
		"iv_by_version": iv_by_version,
		"iv_by_key": iv_by_key,
		"allocations": allocations,
	}


def _version_projection(version: Any | None, ivs: list[Any], currency: str) -> dict[str, Any] | None:
	if not version:
		return None
	included = [iv for iv in ivs if not int(iv.proposed_removal or 0)]
	confirmed = sum(iv.effective_finance_status == FINANCE_CONFIRMED for iv in included)
	validation = effective_validation_status_from_rows(
		version=version.name,
		stored=version.validation_projection,
		rows=_validation_inputs(included),
	)
	total = sum(flt(iv.confirmed_estimate) for iv in included)
	return {
		"version": version.name,
		"version_number": int(version.version_number or 0),
		"status": cstr(version.status),
		"item_count": len(included),
		"planned_total": total,
		"planned_total_display": _money(total, currency),
		"finance_confirmed_count": confirmed,
		"finance_item_count": len(included),
		"finance_confirmed_label": f"{confirmed} of {len(included)}",
		"validation_projection": validation,
	}


def _has_effective_changes(items: list[Any], draft_ivs: list[Any]) -> bool:
	state = {item.name: item.baseline_state for item in items}
	return any(
		state.get(iv.plan_item) == ITEM_PROPOSED
		or int(iv.proposed_removal or 0)
		or not int(iv.carry_forward_unchanged or 0)
		for iv in draft_ivs
	)


def _is_incomplete(iv: Any) -> bool:
	required = (
		"requirement_description", "procurement_category", "procurement_method",
		"arrangement", "lotting_decision", *MILESTONE_FIELDS,
	)
	return any(not cstr(iv.get(field) or "").strip() for field in required)


def _row(
	*, resource_key: str, reference: str, title: str, work_type: str, org_unit: str,
	org_label: str, amount: float, currency: str, reason: str, status: str,
	filter_key: str, priority: int, action: dict[str, str],
) -> dict[str, Any]:
	return {
		"resource_key": resource_key,
		"reference": reference,
		"demand_code": reference,
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
		"action_label": action["label"],
	}


def _eligible_demands(
	*, plan: Any, financial_year: str | None = None, scope: dict[str, set[str] | None], actor_roles: set[str], ou_labels: dict[str, str]
) -> list[dict[str, Any]]:
	if not actor_roles.intersection(ADD_DEMAND_ROLES) or not frappe.db.exists("DocType", "Demand"):
		return []
	pe = cstr(plan.get("procuring_entity") if isinstance(plan, dict) else plan.procuring_entity)
	fy = cstr(financial_year or (plan.get("financial_year") if isinstance(plan, dict) else plan.financial_year))
	start, end = period_dates_for_financial_year(fy)
	rows = frappe.get_all(
		"Demand",
		filters={
			"procuring_entity": pe,
			"status": "Approved",
			"planning_ready": 1,
		},
		fields=[
			"name", "demand_code", "title", "owner_org_unit", "confirmed_estimate",
			"requester_estimate", "currency", "planning_usage", "required_by_date",
		],
		order_by="modified desc",
		limit_page_length=0,
	)
	rows = [
		row for row in rows
		if row.required_by_date
		and getdate(start) <= getdate(row.required_by_date) <= getdate(end)
		and _in_scope(scope, pe, row.owner_org_unit)
	]
	if not rows:
		return []
	allocations = frappe.get_all(
		"Plan Demand Allocation",
		filters={"demand": ["in", [row.name for row in rows]], "status": ["in", [ALLOC_DRAFT, ALLOC_EFFECTIVE]]},
		fields=["demand", "allocated_amount"],
		limit_page_length=0,
	)
	allocated: dict[str, float] = defaultdict(float)
	for allocation in allocations:
		allocated[allocation.demand] += flt(allocation.allocated_amount)
	route = plan_canvas_routes(plan)["builder_route"]
	out = []
	for demand in rows:
		amount = flt(demand.confirmed_estimate or demand.requester_estimate)
		if cstr(demand.planning_usage) == "Fully planned" or allocated[demand.name] + 0.005 >= amount:
			continue
		row = _row(
				resource_key=f"demand:{demand.name}",
				reference=cstr(demand.demand_code or demand.name),
				title=cstr(demand.title or demand.name),
				work_type="Approved Demand",
				org_unit=cstr(demand.owner_org_unit),
				org_label=ou_labels.get(cstr(demand.owner_org_unit), cstr(demand.owner_org_unit)),
				amount=amount - allocated[demand.name],
				currency=cstr(demand.currency or plan.currency or "KES"),
				reason=f"HoD-approved Demand is ready to add to the FY {fy} Plan.",
				status="Ready for planning",
				filter_key="approved_demands",
				priority=40,
				action=_action("add_to_plan", "Add to plan", f"{route}&add_demand={quote(demand.name)}"),
			)
		row["demand"] = demand.name
		row["builder_route"] = route
		out.append(row)
	return out


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


def get_planning_workspace(
	*,
	procuring_entity: str | None = None,
	financial_year: str | None = "2027/28",
	work_filter: str | None = "all",
	search: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user).strip()
	if not actor or actor == "Guest":
		frappe.throw(frappe._("Login required."), frappe.PermissionError, title="PLN_LOGIN_REQUIRED")
	require_operational_roles(*READ_PLAN_ROLES, user=actor)
	actor_roles = actor_planning_roles(actor)
	read_only = is_planning_read_only(actor)
	entities, scope = _scope_index(actor)
	fy = cstr(financial_year or "2027/28").strip() or "2027/28"
	helper = (
		"Read-only support view. These controls filter visibility; they do not grant ownership or operational Planning authority."
		if read_only
		else "These controls define the workspace view; they do not change record ownership."
	)
	labels = {entity["id"]: entity["name"] for entity in entities}
	if not entities:
		payload = _base_payload(
			mode=MODE_BLOCKED, entities=[], pe=None, pe_label="", fy=fy,
			read_only=True, state_id=STATE_BLOCKED, helper=helper,
		)
		payload["blocked_reason"] = "No operational Planning assignment exists."
		return payload
	requested = cstr(procuring_entity).strip()
	if len(entities) == 1:
		pe = entities[0]["id"]
		mode = MODE_SINGLE
	elif not requested:
		return _base_payload(
			mode=MODE_MULTI, entities=entities, pe=None, pe_label="", fy=fy,
			read_only=read_only, state_id=STATE_SELECTION, helper=helper,
		)
	elif requested not in labels:
		frappe.throw(
			frappe._("Selected Procuring Entity is not in your Planning scope."),
			frappe.PermissionError,
			title="PLN_SCOPE_DENIED",
		)
	else:
		pe = requested
		mode = MODE_MULTI
	payload = _base_payload(
		mode=mode, entities=entities, pe=pe, pe_label=labels[pe], fy=fy,
		read_only=read_only, state_id=STATE_NO_PLAN, helper=helper,
	)
	can_create = (not read_only) and bool(actor_roles.intersection(CREATE_PLAN_ROLES))
	payload["can_create_plan"] = can_create
	plan = frappe.db.get_value(
		"Procurement Plan",
		{"procuring_entity": pe, "financial_year": fy},
		[
			"name", "plan_code", "title", "lifecycle_state", "currency",
			"current_approved_version", "open_draft_version", "coordinating_org_unit",
			"financial_year", "period_start", "period_end",
		],
		as_dict=True,
	)
	if not plan:
		payload["empty_states"]["current_plan"] = "No annual Procurement Plan exists for this context."
		if can_create:
			payload["primary_action"] = _action("create_plan", "Create annual plan", "/app/procurement-plan-register")
		return payload
	plan = frappe.get_doc("Procurement Plan", plan.name)
	# Scenario/UI fixtures may mutate the logical header earlier in the same request.
	# Reload so the projection never reuses a stale document from frappe.local.
	plan.reload()
	eligible_rows = _eligible_demands(
		plan=plan, financial_year=fy, scope=scope, actor_roles=actor_roles, ou_labels={}
	)
	graph = _load_graph(plan)
	approved_version = graph["versions"].get(cstr(plan.current_approved_version))
	draft_version = graph["versions"].get(cstr(plan.open_draft_version))
	approved_ivs = graph["iv_by_version"].get(cstr(plan.current_approved_version), [])
	draft_ivs = graph["iv_by_version"].get(cstr(plan.open_draft_version), [])
	approved = _version_projection(approved_version, approved_ivs, plan.currency or "KES")
	draft = _version_projection(draft_version, draft_ivs, plan.currency or "KES")
	routes = plan_canvas_routes(plan)
	has_changes = bool(draft and approved and _has_effective_changes(graph["items"], draft_ivs))
	if approved and draft:
		state_id = STATE_UPDATE if has_changes else STATE_NO_CHANGES
		supporting = "A Draft plan update is in progress." if has_changes else "No effective changes remain in this plan update."
	elif draft:
		state_id = STATE_INITIAL_DRAFT
		supporting = "Complete the initial Draft before professional review."
	else:
		state_id = STATE_APPROVED
		supporting = "No plan update is currently in progress."
	status_parts = [f"{plan.lifecycle_state} Plan"]
	if approved:
		status_parts.append(f"Approved Version {approved['version_number']}")
	if draft:
		status_parts.append(f"Draft Version {draft['version_number']}")
	focus = draft or approved or {
		"item_count": 0, "planned_total": 0, "planned_total_display": _money(0, plan.currency),
		"finance_confirmed_label": "0 of 0", "validation_projection": VALIDATION_NOT_RUN,
	}
	payload["state_id"] = state_id
	payload["current_plan"] = {
		"plan": plan.name,
		"plan_code": plan.plan_code,
		"title": plan.title,
		"lifecycle_state": plan.lifecycle_state,
		"currency": plan.currency or "KES",
		"current_approved_version": plan.current_approved_version,
		"open_draft_version": plan.open_draft_version,
		"approved": approved,
		"draft": draft,
		"status_line": " · ".join(status_parts),
		"supporting_text": supporting,
		"item_count": focus["item_count"],
		"planned_total": focus["planned_total"],
		"planned_total_display": focus["planned_total_display"],
		"finance_confirmed_label": focus["finance_confirmed_label"],
		"validation_projection": focus["validation_projection"],
		"routes": routes,
		**routes,
	}
	if approved and draft and cstr(draft_version.status) == VERSION_IN_REVIEW:
		payload["primary_action"] = _action("view_approved_plan", "View approved plan", routes["approved_route"])
	elif approved and draft:
		payload["primary_action"] = _action("continue_plan_update", "Continue plan update", routes["update_route"])
	elif draft:
		payload["primary_action"] = _action("continue_planning", "Continue planning", routes["builder_route"])
	elif approved:
		payload["primary_action"] = _action("view_approved_plan", "View approved plan", routes["approved_route"])
	if read_only:
		payload["primary_action"] = (
			_action("view_approved_plan", "View approved plan", routes["approved_route"])
			if approved else None
		)
		return payload
	all_ous = {cstr(item.owner_org_unit) for item in graph["items"] if item.owner_org_unit}
	if frappe.db.exists("DocType", "Demand"):
		all_ous |= {
			cstr(value)
			for value in frappe.get_all("Demand", filters={"procuring_entity": pe}, pluck="owner_org_unit", limit_page_length=0)
			if value
		}
	ou_labels = _labels("Organisation Unit", all_ous, "unit_name")
	work: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []
	if draft and actor_roles.intersection(ADD_DEMAND_ROLES):
		item_by_name = {item.name: item for item in graph["items"]}
		if cstr(draft_version.status) == VERSION_RETURNED:
			work.append(
				_row(
					resource_key=f"plan:{plan.name}", reference=plan.plan_code, title=plan.title,
					work_type="Plan update", org_unit=cstr(plan.coordinating_org_unit),
					org_label=ou_labels.get(cstr(plan.coordinating_org_unit), cstr(plan.coordinating_org_unit)),
					amount=draft["planned_total"], currency=plan.currency, reason="The plan update was returned for correction.",
					status="Returned", filter_key="returned_work", priority=10,
					action=_action("address_return", "Address return", routes["update_route"]),
				)
			)
		elif approved and not has_changes:
			work.append(
				_row(
					resource_key=f"plan:{plan.name}", reference=plan.plan_code, title=plan.title,
					work_type="Plan update", org_unit=cstr(plan.coordinating_org_unit),
					org_label=ou_labels.get(cstr(plan.coordinating_org_unit), cstr(plan.coordinating_org_unit)),
					amount=draft["planned_total"], currency=plan.currency,
					reason="No effective changes remain; the update cannot be submitted.", status="No changes",
					filter_key="plan_items", priority=30,
					action=_action("cancel_update", "Cancel update", routes["update_route"]),
				)
			)
		for iv in draft_ivs:
			if int(iv.proposed_removal or 0):
				continue
			item = item_by_name.get(iv.plan_item)
			if not item or not _in_scope(scope, pe, item.owner_org_unit):
				continue
			base = dict(
				resource_key=f"item:{item.name}", reference=cstr(item.plan_item_code or item.name),
				title=cstr(iv.requirement_title or item.plan_item_code), work_type="Plan Item",
				org_unit=cstr(item.owner_org_unit), org_label=ou_labels.get(cstr(item.owner_org_unit), cstr(item.owner_org_unit)),
				amount=flt(iv.confirmed_estimate), currency=cstr(iv.currency or plan.currency or "KES"),
			)
			item_route = f"/app/procurement-plan-item-editor?plan_item={item.name}"
			finance = cstr(iv.effective_finance_status or FINANCE_NOT_REQUESTED)
			validation = cstr(iv.validation_projection or VALIDATION_NOT_RUN)
			if finance == FINANCE_RETURNED:
				work.append(_row(**base, reason="Finance returned this item for correction.", status="Returned by Finance", filter_key="returned_work", priority=10, action=_action("correct_item", "Correct item", item_route)))
			elif validation in (VALIDATION_BLOCKED, VALIDATION_STALE):
				work.append(_row(**base, reason="Blocking or stale validation must be resolved.", status=validation, filter_key="plan_items", priority=20, action=_action("resolve_issues", "Resolve issues", item_route)))
			elif item.baseline_state == ITEM_PROPOSED and _is_incomplete(iv):
				work.append(_row(**base, reason="Complete the Plan Item before requesting Finance confirmation.", status="Incomplete", filter_key="plan_items", priority=30, action=_action("complete_item", "Complete item", item_route)))
			elif validation == VALIDATION_NEEDS_ATTENTION:
				work.append(_row(**base, reason="Planning validation needs attention.", status=validation, filter_key="plan_items", priority=20, action=_action("resolve_issues", "Resolve issues", item_route)))
			elif finance == FINANCE_AWAITING:
				waiting.append(_row(**base, reason="Awaiting Finance confirmation.", status="Awaiting Finance", filter_key="plan_items", priority=30, action=_action("view_item", "View item", item_route)))
		if cstr(draft_version.status) == VERSION_IN_REVIEW:
			waiting = [
				_row(
					resource_key=f"review:{plan.name}", reference=plan.plan_code, title=plan.title,
					work_type="Plan update", org_unit=cstr(plan.coordinating_org_unit),
					org_label=ou_labels.get(cstr(plan.coordinating_org_unit), cstr(plan.coordinating_org_unit)),
					amount=draft["planned_total"], currency=plan.currency,
					reason="Awaiting Head-of-Procurement review.", status="In professional review",
					filter_key="plan_items", priority=30,
					action=_action("view_update", "View update", routes["update_route"]),
				)
			]
		elif approved and has_changes and not work and not waiting:
			work.append(
				_row(
					resource_key=f"plan:{plan.name}", reference=plan.plan_code, title=plan.title,
					work_type="Plan update", org_unit=cstr(plan.coordinating_org_unit),
					org_label=ou_labels.get(cstr(plan.coordinating_org_unit), cstr(plan.coordinating_org_unit)),
					amount=draft["planned_total"], currency=plan.currency,
					reason="This Draft update has outstanding planner work.", status="Draft update",
					filter_key="plan_items", priority=30,
					action=_action("continue_update", "Continue update", routes["update_route"]),
				)
			)
	for row in eligible_rows:
		row["organisation_unit_label"] = ou_labels.get(
			row["organisation_unit"], row["organisation_unit"]
		)
	work.extend(eligible_rows)
	# Highest-priority row wins when one source record meets multiple predicates.
	deduped: dict[str, dict[str, Any]] = {}
	for row in sorted(work, key=lambda value: (value["priority"], value["reference"])):
		deduped.setdefault(row["resource_key"], row)
	selected_filter = cstr(work_filter or "all").strip() or "all"
	if selected_filter not in FILTER_KEYS:
		selected_filter = "all"
	needle = cstr(search).strip()
	work = [row for row in deduped.values() if _matches(row, selected_filter, needle)][:50]
	waiting.sort(key=lambda value: (value["priority"], value["reference"]))
	payload["work_requiring_action"] = work
	payload["waiting_on_others"] = waiting[:50]
	payload["work_queue"] = work
	payload["counts"] = {
		"work_requiring_action": len(work),
		"waiting_on_others": len(waiting),
	}
	return payload
