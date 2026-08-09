# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-001 — Procurement Planning workspace projection."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import (
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
	is_planning_read_only,
	list_eligible_procuring_entities,
	require_operational_roles,
	resolve_pe_for_create,
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
		try:
			assert_planning_scope(
				procuring_entity=pe,
				org_unit=cstr(r.owner_org_unit or "").strip() or None,
				user=user,
				require_write=False,
			)
		except Exception:
			continue
		status = cstr(r.status)
		ready = int(r.planning_ready or 0)
		usage = cstr(r.planning_usage or "Not taken up")
		amount = flt(r.confirmed_estimate or r.requester_estimate)
		currency = cstr(r.currency or "KES")
		ou = cstr(r.owner_org_unit or "")
		row_filter = "all"
		reason = ""
		action_label = "View"
		action = "view"
		queue_status = status
		if status == "Approved" and ready and usage != "Fully planned":
			row_filter = "approved_demands"
			reason = "Approved Demand ready for planning"
			action_label = "Add to plan"
			action = "add_to_plan"
			queue_status = "Ready"
		elif status == "Returned":
			row_filter = "returned"
			reason = "Returned for correction"
			action_label = "View return"
			action = "view_return"
			queue_status = "Returned"
		else:
			continue
		if work_filter not in ("all", "all_work", "") and work_filter != row_filter:
			if work_filter == "approved_not_started" and row_filter != "approved_demands":
				continue
			if work_filter == "needs_attention" and row_filter not in (
				"returned",
				"approved_demands",
			):
				continue
			if work_filter not in (
				"approved_not_started",
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
		else "These controls filter the workspace; they do not assign ownership to new records."
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
			validation = (
				frappe.db.get_value(
					"Procurement Plan Version", focus_version, "validation_projection"
				)
				or "Not run"
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
			"departmental_contributions_label": "0 of 1 submitted",
			"period_start": str(plan.period_start or ""),
			"period_end": str(plan.period_end or ""),
			"builder_route": f"/app/procurement-plan-builder?plan={plan.name}",
			"procuring_entity": for_pe,
			"procuring_entity_label": _entity_label(for_pe),
		}

	current_plan = None
	queue: list[dict[str, Any]] = []
	if view_all:
		# Prefer first accessible plan for the summary panel; queue merges all PEs.
		for e in filter_entities:
			try:
				loaded = _load_plan(e["id"])
			except Exception:
				continue
			if current_plan is None and loaded:
				current_plan = loaded
			queue.extend(
				_work_queue(pe=e["id"], user=actor, work_filter=cstr(work_filter or "all"))
			)
		pe_label = "All authorised entities"
	else:
		assert_planning_scope(procuring_entity=pe, org_unit=None, user=actor, require_write=False)
		current_plan = _load_plan(pe)
		queue = _work_queue(pe=pe, user=actor, work_filter=cstr(work_filter or "all"))
		pe_label = _entity_label(pe)

	# Create requires an operational create-scope PE — never Viewer / all-entities.
	create_pe = None if view_all or pe == PE_FILTER_ALL else pe
	create_scope = resolve_pe_for_create(actor, create_pe)
	can_create = (not read_only) and create_scope.get("selection_mode") != MODE_BLOCKED

	# Soften queue actions in read-only support view.
	if read_only:
		for row in queue:
			if row.get("action") == "add_to_plan":
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
