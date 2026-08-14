# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-001 — Procurement Planning workspace projection."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import (
	FINANCE_AWAITING,
	FINANCE_RETURNED,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VERSION_APPROVED,
	VERSION_DRAFT,
	VERSION_RETURNED,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	PE_FILTER_ALL,
	READ_PLAN_ROLES,
	assert_planning_scope,
	get_available_actions,
	has_any_operational_role,
	has_finance_task_capability,
	has_planning_scope,
	is_planning_read_only,
	list_eligible_procuring_entities,
	primary_queue_action,
	require_operational_roles,
	resolve_pe_for_create,
)
from kentender_procurement.procurement_planning.services.validate_plan import (
	effective_validation_status,
)


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def _entity_label(pe: str) -> str:
	if not pe or not frappe.db.exists("Procuring Entity", pe):
		return pe or ""
	return str(
		frappe.db.get_value("Procuring Entity", pe, "entity_name")
		or frappe.db.get_value("Procuring Entity", pe, "procuring_entity_name")
		or pe
	)


def _ou_label(ou: str) -> str:
	if not ou or not frappe.db.exists("Organisation Unit", ou):
		return ou or ""
	return str(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


def _fy_options() -> list[dict[str, str]]:
	# Controlled FY list for MVP-1 demos + UI empty-draft fixture year.
	return [
		{"id": "2027/28", "label": "2027/28"},
		{"id": "2028/29", "label": "2028/29"},
		{"id": "2026/27", "label": "2026/27"},
		{"id": "2029/30", "label": "2029/30"},
	]


def _version_label(version_name: str | None) -> str:
	if not version_name or not frappe.db.exists("Procurement Plan Version", version_name):
		return "—"
	row = frappe.db.get_value(
		"Procurement Plan Version",
		version_name,
		["version_number", "status"],
		as_dict=True,
	)
	if not row:
		return "—"
	return f"{row.status} Version {int(row.version_number or 0)}"


def _plan_item_stats(plan_name: str, version_name: str | None) -> dict[str, Any]:
	items = frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan_name, "baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]]},
		pluck="name",
	)
	total = 0.0
	if version_name:
		for item in items:
			iv = frappe.db.get_value(
				"Procurement Plan Item Version",
				{"plan_item": item, "plan_version": version_name},
				"confirmed_estimate",
			)
			if iv is None:
				# Fall back to current approved item version amount
				civ = frappe.db.get_value(
					"Procurement Plan Item", item, "current_approved_item_version"
				)
				if civ:
					iv = frappe.db.get_value(
						"Procurement Plan Item Version", civ, "confirmed_estimate"
					)
			total += flt(iv)
	return {"item_count": len(items), "planned_total": total}


def _work_queue(*, pe: str, user: str, work_filter: str = "all") -> list[dict[str, Any]]:
	"""Compact Approved-ready + Returned Demands in PE scope (not Gate 04 modal)."""
	if not frappe.db.exists("DocType", "Demand"):
		return []
	rows = frappe.get_all(
		"Demand",
		filters={"procuring_entity": pe},
		fields=[
			"name",
			"demand_code",
			"title",
			"status",
			"planning_ready",
			"planning_usage",
			"confirmed_estimate",
			"requester_estimate",
			"currency",
			"owner_org_unit",
		],
		order_by="modified desc",
		limit_page_length=50,
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		# Soft filter — never throw/msgprint for out-of-scope Demand OUs.
		if not has_planning_scope(
			procuring_entity=pe,
			org_unit=cstr(r.owner_org_unit or "").strip() or None,
			user=user,
			require_write=False,
		):
			continue
		status = cstr(r.status)
		ready = int(r.planning_ready or 0)
		usage = cstr(r.planning_usage or "Not taken up")
		amount = flt(r.confirmed_estimate or r.requester_estimate)
		currency = cstr(r.currency or "KES")
		ou = cstr(r.owner_org_unit or "")
		row_filter = "all"
		reason = ""
		action, action_label = primary_queue_action(
			user,
			{
				"kind": "workspace_demand",
				"demand_status": status,
				"planning_ready": ready,
				"planning_usage": usage,
			},
		)
		queue_status = status
		if status == "Approved" and ready and usage != "Fully planned":
			row_filter = "approved_demands"
			reason = "Approved Demand ready for planning"
			queue_status = "Ready"
		elif status == "Returned":
			row_filter = "needs_attention"
			reason = "Returned for correction"
			queue_status = "Returned"
		else:
			continue
		wf = cstr(work_filter or "all").strip() or "all"
		if wf in ("all", "all_work"):
			pass
		elif wf == "approved_demands" and row_filter != "approved_demands":
			continue
		elif wf == "returned_by_finance" and row_filter != "returned_by_finance":
			continue
		elif wf == "needs_attention" and row_filter != "needs_attention":
			continue
		elif wf not in (
			"approved_demands",
			"returned_by_finance",
			"needs_attention",
			row_filter,
		):
			continue
		out.append(
			{
				"demand": r.name,
				"demand_code": r.demand_code,
				"title": r.title,
				"organisation_unit": ou,
				"organisation_unit_label": _ou_label(ou),
				"amount": amount,
				"amount_display": _money(amount, currency),
				"reason": reason,
				"status": queue_status,
				"filter_key": row_filter,
				"action": action,
				"action_label": action_label,
				"available_actions": get_available_actions(
					user,
					{
						"kind": "workspace_demand",
						"demand_status": status,
						"planning_ready": ready,
						"planning_usage": usage,
					},
				),
			}
		)
	return out


def _finance_work_queue(*, pe: str, user: str, work_filter: str = "all") -> list[dict[str, Any]]:
	"""Awaiting confirmation (BO) and Returned by Finance (planner) Plan Item rows."""
	from kentender_procurement.procurement_planning.services.plan_item_finance import (
		finance_status_label,
	)

	wf = cstr(work_filter or "all").strip() or "all"
	want_awaiting = wf in ("all", "all_work", "awaiting_finance")
	want_returned = wf in ("all", "all_work", "returned_by_finance")
	if not want_awaiting and not want_returned:
		return []
	plans = frappe.get_all(
		"Procurement Plan",
		filters={"procuring_entity": pe},
		fields=["name", "title", "open_draft_version", "current_approved_version", "currency"],
		limit_page_length=20,
	)
	out: list[dict[str, Any]] = []
	for plan in plans:
		focus = cstr(plan.open_draft_version or plan.current_approved_version or "")
		if not focus:
			continue
		items = frappe.get_all(
			"Procurement Plan Item",
			filters={"plan": plan.name, "baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]]},
			fields=["name", "plan_item_code", "owner_org_unit"],
		)
		for it in items:
			iv_name = frappe.db.get_value(
				"Procurement Plan Item Version",
				{"plan_item": it.name, "plan_version": focus},
				"name",
			)
			if not iv_name:
				continue
			iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
			status = finance_status_label(iv)
			row_filter = ""
			reason = ""
			if status == FINANCE_AWAITING and want_awaiting:
				row_filter = "awaiting_finance"
				reason = "Plan Item awaiting Finance confirmation"
			elif status == FINANCE_RETURNED and want_returned:
				row_filter = "returned_by_finance"
				reason = "Returned by Finance"
			else:
				continue
			action, action_label = primary_queue_action(
				user,
				{"kind": "finance_item", "finance_status": status},
			)
			ou = cstr(it.owner_org_unit or "")
			out.append(
				{
					"demand": "",
					"demand_code": it.plan_item_code,
					"plan": plan.name,
					"plan_item": it.name,
					"plan_item_code": it.plan_item_code,
					"title": iv.requirement_title or it.plan_item_code,
					"organisation_unit": ou,
					"organisation_unit_label": _ou_label(ou),
					"amount": flt(iv.confirmed_estimate),
					"amount_display": _money(flt(iv.confirmed_estimate), plan.currency or "KES"),
					"reason": reason,
					"status": status,
					"filter_key": row_filter,
					"action": action,
					"action_label": action_label,
					"available_actions": get_available_actions(
						user,
						{"kind": "finance_item", "finance_status": status},
					),
					"builder_route": (
						f"/app/procurement-plan-builder?plan={plan.name}&finance_item={it.name}"
					),
				}
			)
	return out


def get_planning_workspace(
	*,
	procuring_entity: str | None = None,
	financial_year: str | None = "2027/28",
	work_filter: str | None = "all",
	user: str | None = None,
) -> dict[str, Any]:
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

	entities = list_eligible_procuring_entities(actor)
	# Workspace filters use any Planning USA PE (broader than create-only).
	from kentender_core.services.org_scope_access import user_scope_rows

	pe_seen: set[str] = set()
	filter_entities: list[dict[str, str]] = []
	for row in user_scope_rows(actor):
		pe = cstr(row.get("procuring_entity") or "").strip()
		if not pe or pe in pe_seen:
			continue
		pe_seen.add(pe)
		ref = next((e for e in entities if e["id"] == pe), None)
		filter_entities.append(ref or {"id": pe, "code": pe, "name": _entity_label(pe)})
	filter_entities.sort(key=lambda e: e["id"])

	read_only = is_planning_read_only(actor)
	fy = cstr(financial_year or "2027/28").strip() or "2027/28"
	helper = (
		"Read-only support view. These controls filter visibility; they do not grant "
		"ownership or operational Planning authority."
		if read_only
		else "These controls define the workspace scope; they do not assign ownership to records."
	)

	if not filter_entities:
		return {
			"ok": True,
			"selection_mode": MODE_BLOCKED,
			"procuring_entities": [],
			"financial_years": _fy_options(),
			"procuring_entity": None,
			"financial_year": fy,
			"blocked_reason": "No operational Planning assignment exists.",
			"current_plan": None,
			"work_queue": [],
			"can_create_plan": False,
			"read_only": True,
			"helper_text": helper,
		}

	# Multi-PE filter list includes an explicit "all" option (never a silent default owner).
	pe_options = list(filter_entities)
	if len(filter_entities) > 1:
		pe_options = [
			{
				"id": PE_FILTER_ALL,
				"code": "",
				"name": "All authorised entities",
				"label": "All authorised entities",
			}
		] + pe_options

	requested = cstr(procuring_entity or "").strip()
	pe_ids = {e["id"] for e in filter_entities}

	if len(filter_entities) == 1:
		pe = filter_entities[0]["id"]
		mode = MODE_SINGLE
		view_all = False
	elif requested == PE_FILTER_ALL or (not requested and read_only):
		# Explicit all-entities view (default for support viewers). Never invents an owner PE.
		pe = PE_FILTER_ALL
		mode = MODE_MULTI
		view_all = True
	elif requested and requested in pe_ids:
		pe = requested
		mode = MODE_MULTI
		view_all = False
	elif requested:
		frappe.throw(
			frappe._("Selected Procuring Entity is not in your Planning scope."),
			frappe.PermissionError,
			title="PLN_SCOPE_DENIED",
		)
	else:
		# Operational multi: no silent default — options only until a PE is chosen.
		create_scope = resolve_pe_for_create(actor, None)
		return {
			"ok": True,
			"selection_mode": MODE_MULTI,
			"procuring_entities": pe_options,
			"financial_years": _fy_options(),
			"procuring_entity": None,
			"financial_year": fy,
			"blocked_reason": None,
			"current_plan": None,
			"work_queue": [],
			"can_create_plan": create_scope.get("selection_mode") != MODE_BLOCKED,
			"read_only": read_only,
			"helper_text": helper,
		}

	def _load_plan(for_pe: str) -> dict[str, Any] | None:
		assert_planning_scope(
			procuring_entity=for_pe, org_unit=None, user=actor, require_write=False
		)
		plan = frappe.db.get_value(
			"Procurement Plan",
			{"procuring_entity": for_pe, "financial_year": fy},
			[
				"name",
				"plan_code",
				"title",
				"lifecycle_state",
				"currency",
				"current_approved_version",
				"open_draft_version",
				"coordinating_org_unit",
				"period_start",
				"period_end",
			],
			as_dict=True,
		)
		if not plan:
			return None
		focus_version = cstr(plan.open_draft_version or plan.current_approved_version or "")
		stats = _plan_item_stats(plan.name, focus_version or None)
		validation = "Not run"
		if focus_version and frappe.db.exists("Procurement Plan Version", focus_version):
			stored = frappe.db.get_value(
				"Procurement Plan Version", focus_version, "validation_projection"
			)
			validation = effective_validation_status(
				plan=plan.name, version=focus_version, stored=cstr(stored or "")
			)
		return {
			"plan": plan.name,
			"plan_code": plan.plan_code,
			"title": plan.title,
			"lifecycle_state": plan.lifecycle_state,
			"currency": plan.currency or "KES",
			"current_approved_version": plan.current_approved_version,
			"open_draft_version": plan.open_draft_version,
			"version_label": _version_label(focus_version),
			"item_count": stats["item_count"],
			"planned_total": stats["planned_total"],
			"planned_total_display": _money(stats["planned_total"], plan.currency or "KES"),
			"validation_projection": validation,
			"departmental_contributions_label": "—",
			"period_start": str(plan.period_start or ""),
			"period_end": str(plan.period_end or ""),
			"builder_route": (
				f"/app/procurement-plan-approved?plan={plan.name}"
				if plan.current_approved_version
				else f"/app/procurement-plan-builder?plan={plan.name}"
			),
			"procuring_entity": for_pe,
			"procuring_entity_label": _entity_label(for_pe),
		}

	current_plan = None
	queue: list[dict[str, Any]] = []
	if view_all:
		# Prefer first accessible plan for the summary panel; queue merges all PEs.
		for e in filter_entities:
			if not has_planning_scope(
				procuring_entity=e["id"], org_unit=None, user=actor, require_write=False
			):
				continue
			loaded = _load_plan(e["id"])
			if current_plan is None and loaded:
				current_plan = loaded
			queue.extend(
				_work_queue(pe=e["id"], user=actor, work_filter=cstr(work_filter or "all"))
			)
			queue.extend(
				_finance_work_queue(
					pe=e["id"], user=actor, work_filter=cstr(work_filter or "all")
				)
			)
		pe_label = "All authorised entities"
	else:
		assert_planning_scope(procuring_entity=pe, org_unit=None, user=actor, require_write=False)
		current_plan = _load_plan(pe)
		finance_only = has_finance_task_capability(actor) and is_planning_read_only(actor)
		if finance_only:
			queue = _finance_work_queue(
				pe=pe, user=actor, work_filter=cstr(work_filter or "all")
			)
		else:
			queue = _work_queue(pe=pe, user=actor, work_filter=cstr(work_filter or "all"))
			queue.extend(
				_finance_work_queue(
					pe=pe, user=actor, work_filter=cstr(work_filter or "all")
				)
			)
		pe_label = _entity_label(pe)

	# Create requires an operational create-scope PE — never Viewer / all-entities.
	create_pe = None if view_all or pe == PE_FILTER_ALL else pe
	create_scope = resolve_pe_for_create(actor, create_pe)
	can_create = (not read_only) and create_scope.get("selection_mode") != MODE_BLOCKED

	# Soften every operational queue action in read-only support view.
	if read_only:
		for row in queue:
			if row.get("action") in ("add_to_plan", "confirm_funding", "continue_item"):
				row["action"] = "view"
				row["action_label"] = "View"

	return {
		"ok": True,
		"selection_mode": mode,
		"procuring_entities": pe_options,
		"financial_years": _fy_options(),
		"procuring_entity": pe,
		"procuring_entity_label": pe_label,
		"financial_year": fy,
		"blocked_reason": None,
		"helper_text": helper,
		"current_plan": current_plan,
		"work_queue": queue,
		"can_create_plan": can_create,
		"read_only": read_only,
		"register_route": "/app/procurement-plan-register",
		"workspace_route": "/app/planning-workspace",
	}
