# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Desk APIs for Demands MVP-1 UI."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, flt, formatdate, getdate

from kentender_core.services.org_scope_access import user_scope_rows
from kentender_procurement.demands.services.demand_lifecycle import (
	create_or_update_demand,
	get_demand,
	list_demands_for_workspace,
	project_demand,
	submit_demand,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_REQUESTER,
	assert_demand_scope,
	can_edit_requester_fields,
	can_read_demand,
	require_operational_roles,
)


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def _action_for(row: dict[str, Any]) -> tuple[str, str]:
	status = (row.get("status") or "").strip()
	stage = (row.get("current_stage") or "").strip()
	if status == "Returned":
		return "Resolve", "demand-form"
	if status == "Draft":
		return "Open", "demand-form"
	if status == "Approved":
		return "View", "demand-detail"
	if stage in (
		"Business Review",
		"Procurement Enrichment",
		"Budget Confirmation",
		"Final Approval",
	):
		return "Review", "demand-review"
	return "Open", "demand-detail"


def _owner_label(user: str | None) -> str:
	if not user:
		return "—"
	try:
		return frappe.utils.get_fullname(user) or user
	except Exception:
		return user


def _owning_unit_short(org_unit: str | None) -> str:
	"""Stitch shows unit name only (not full ownership path)."""
	if not org_unit:
		return "—"
	if frappe.db.exists("Organisation Unit", org_unit):
		name = frappe.db.get_value("Organisation Unit", org_unit, "unit_name")
		if name:
			return str(name)
	return str(org_unit)


def _required_by_display(value: Any) -> str:
	if not value:
		return "—"
	try:
		return formatdate(getdate(value), "dd MMM yyyy")
	except Exception:
		return str(value)


def _enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	out = []
	for r in rows:
		action_label, route = _action_for(r)
		estimate = flt(r.get("confirmed_estimate")) or flt(r.get("requester_estimate"))
		out.append(
			{
				**r,
				"owning_unit_label": _owning_unit_short(r.get("owner_org_unit")),
				"estimate_display": _money(estimate, r.get("currency") or "KES"),
				"required_by_display": _required_by_display(r.get("required_by_date")),
				"current_owner": _owner_label(r.get("current_owner")),
				"action_label": action_label,
				"action_route": route,
			}
		)
	return out


def _summary_for_actor(actor: str, base_rows: list[dict[str, Any]]) -> dict[str, int]:
	my_drafts = 0
	returned_to_me = 0
	my_approvals = 0
	budget_confirmations = 0
	for r in base_rows:
		st = r.get("status")
		stage = r.get("current_stage")
		req = r.get("requester")
		if st == "Draft" and req == actor:
			my_drafts += 1
		if st == "Returned" and req == actor:
			returned_to_me += 1
		if st == "In Review" and stage in (
			"Business Review",
			"Final Approval",
			"Procurement Enrichment",
		):
			my_approvals += 1
		if st == "In Review" and stage == "Budget Confirmation":
			budget_confirmations += 1
	return {
		"my_drafts": my_drafts,
		"returned_to_me": returned_to_me,
		"my_approvals": my_approvals,
		"budget_confirmations": budget_confirmations,
	}


def _entity_options(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
	seen: dict[str, str] = {}
	for r in rows:
		pe = (r.get("procuring_entity") or "").strip()
		if not pe or pe in seen:
			continue
		label = pe
		if frappe.db.exists("Procuring Entity", pe):
			label = (
				frappe.db.get_value("Procuring Entity", pe, "entity_name")
				or frappe.db.get_value("Procuring Entity", pe, "procuring_entity_name")
				or pe
			)
		seen[pe] = str(label)
	return [{"id": k, "name": v, "code": k} for k, v in sorted(seen.items(), key=lambda x: x[1])]


@frappe.whitelist()
def list_demands_workspace(
	queue: str | None = None,
	search: str | None = None,
	status: str | None = None,
	stage: str | None = None,
	procuring_entity: str | None = None,
	page: int | str | None = 1,
	page_size: int | str | None = 20,
	filters: str | dict | None = None,
) -> dict[str, Any]:
	"""DEM-UI-01 queue payload."""
	actor = frappe.session.user
	extra: dict[str, Any] = {"limit": 500}
	if isinstance(filters, str) and filters.strip():
		try:
			parsed = json.loads(filters)
			if isinstance(parsed, dict):
				extra.update(parsed)
		except Exception:
			pass
	elif isinstance(filters, dict):
		extra.update(filters)

	ws = list_demands_for_workspace(user=actor, filters=extra)
	rows = list(ws.get("rows") or [])
	entities = _entity_options(rows)
	summary = _summary_for_actor(actor, rows)

	q = (queue or "").strip()
	if q == "my_drafts":
		rows = [r for r in rows if r.get("status") == "Draft" and r.get("requester") == actor]
	elif q == "returned_to_me":
		rows = [r for r in rows if r.get("status") == "Returned" and r.get("requester") == actor]
	elif q == "my_approvals":
		rows = [
			r
			for r in rows
			if r.get("status") == "In Review"
			and r.get("current_stage")
			in ("Business Review", "Final Approval", "Procurement Enrichment")
		]
	elif q == "budget_confirmations":
		rows = [
			r
			for r in rows
			if r.get("status") == "In Review" and r.get("current_stage") == "Budget Confirmation"
		]

	pe = (procuring_entity or "").strip()
	if pe:
		rows = [r for r in rows if r.get("procuring_entity") == pe]

	st = (status or "").strip()
	if st and st not in ("All", "All Statuses"):
		rows = [r for r in rows if r.get("status") == st]
	sg = (stage or "").strip()
	if sg and sg not in ("All", "All Stages"):
		rows = [r for r in rows if r.get("current_stage") == sg]

	needle = (search or "").strip().lower()
	if needle:
		rows = [
			r
			for r in rows
			if needle in (r.get("demand_code") or "").lower()
			or needle in (r.get("title") or "").lower()
		]

	page_n = max(1, cint(page) or 1)
	size = max(1, min(500, cint(page_size) or 20))
	total = len(rows)
	start = (page_n - 1) * size
	page_rows = _enrich_rows(rows[start : start + size])

	return {
		"ok": True,
		"summary": summary,
		"entities": entities,
		"rows": page_rows,
		"total": total,
		"page": page_n,
		"page_size": size,
		"queue": q or "all",
	}


def _entity_label(pe: str | None) -> str:
	if not pe:
		return ""
	if frappe.db.exists("Procuring Entity", pe):
		return str(
			frappe.db.get_value("Procuring Entity", pe, "entity_name")
			or frappe.db.get_value("Procuring Entity", pe, "procuring_entity_name")
			or pe
		)
	return str(pe)


def _unit_label(ou: str | None) -> str:
	if not ou:
		return ""
	if frappe.db.exists("Organisation Unit", ou):
		return str(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)
	return str(ou)


def _default_scope_for_actor(actor: str) -> tuple[str | None, str | None]:
	"""Prefer Requester scope row; fall back to first assignment / PE-MOH admin default."""
	rows = user_scope_rows(actor)
	req_rows = [r for r in rows if (r.get("role") or "") == ROLE_REQUESTER]
	pick = (req_rows or rows or [None])[0]
	if pick:
		return pick.get("procuring_entity"), pick.get("organisation_unit")
	if actor == "Administrator" or "System Manager" in frappe.get_roles(actor):
		pe = "PE-MOH" if frappe.db.exists("Procuring Entity", "PE-MOH") else None
		ou = "MOH-DIR-DHP" if frappe.db.exists("Organisation Unit", "MOH-DIR-DHP") else None
		return pe, ou
	return None, None


def _contact_options(pe: str | None, ou: str | None) -> list[dict[str, str]]:
	"""Users with desk access in the same PE (display name, store User name)."""
	filters: dict[str, Any] = {}
	if pe:
		filters["procuring_entity"] = pe
	if ou:
		filters["organisation_unit"] = ou
	users = frappe.get_all(
		"User Scope Assignment",
		filters=filters or None,
		pluck="user",
		limit=80,
	)
	out: list[dict[str, str]] = []
	seen: set[str] = set()
	for u in users:
		if not u or u in seen or u in ("Guest", "Administrator"):
			continue
		if not frappe.db.exists("User", u):
			continue
		seen.add(u)
		out.append({"id": u, "name": frappe.utils.get_fullname(u) or u, "code": u})
	out.sort(key=lambda r: r["name"].lower())
	return out


def _return_notice(demand_name: str) -> dict[str, Any] | None:
	row = frappe.db.get_value(
		"Demand Decision",
		{"demand": demand_name, "decision": "Return"},
		["actor", "decided_at", "reason", "comment"],
		as_dict=True,
		order_by="decided_at desc",
	)
	if not row:
		return None
	actor_name = frappe.utils.get_fullname(row.actor) if row.actor else "—"
	date_disp = ""
	if row.decided_at:
		try:
			date_disp = formatdate(getdate(row.decided_at), "dd MMMM yyyy")
		except Exception:
			date_disp = str(row.decided_at)
	reason = (row.reason or row.comment or "").strip()
	return {
		"returned_by": actor_name,
		"returned_at_display": date_disp,
		"reason": reason,
		"correction_hints": [],
	}


def _form_demand_dto(doc) -> dict[str, Any]:
	base = project_demand(doc)
	base["procuring_entity_label"] = _entity_label(doc.procuring_entity)
	base["owner_org_unit_label"] = _unit_label(doc.owner_org_unit)
	base["requester_estimate_display"] = _money(
		flt(doc.requester_estimate), doc.currency or "KES"
	).replace((doc.currency or "KES") + " ", "")
	base["required_by_display"] = _required_by_display(doc.required_by_date)
	if doc.required_by_date:
		try:
			base["required_by_date"] = str(getdate(doc.required_by_date))
		except Exception:
			base["required_by_date"] = str(doc.required_by_date)
	for item in base.get("items") or []:
		est = flt(item.get("requester_estimate"))
		item["requester_estimate_display"] = f"{est:,.2f}" if est else ""
	if doc.status == "Returned":
		base["return_notice"] = _return_notice(doc.name)
	else:
		base["return_notice"] = None
	return base


def _parse_json_arg(raw: Any) -> Any:
	if isinstance(raw, str) and raw.strip():
		try:
			return json.loads(raw)
		except Exception:
			return raw
	return raw


@frappe.whitelist()
def get_demand_form_context() -> dict[str, Any]:
	"""DEM-UI-02 create defaults (PE/OU labels + contacts)."""
	actor = frappe.session.user
	if not can_read_demand(user=actor):
		frappe.throw("Not permitted to open Demand form", frappe.PermissionError)
	pe, ou = _default_scope_for_actor(actor)
	return {
		"ok": True,
		"can_edit": can_edit_requester_fields(user=actor),
		"procuring_entity": pe,
		"owner_org_unit": ou,
		"procuring_entity_label": _entity_label(pe),
		"owner_org_unit_label": _unit_label(ou),
		"contacts": _contact_options(pe, ou),
		"currency": "KES",
		"demand_routes": ["Standard", "Additional", "Emergency"],
		"confidence_levels": ["High", "Medium", "Low"],
		"uom_options": ["Lot", "Pieces", "Months"],
	}


@frappe.whitelist()
def get_demand_form(demand: str | None = None) -> dict[str, Any]:
	"""DEM-UI-02 / DEM-UI-03 load projection."""
	actor = frappe.session.user
	if not can_read_demand(user=actor):
		frappe.throw("Not permitted to open Demand form", frappe.PermissionError)
	ctx = get_demand_form_context()
	if not demand:
		return {"ok": True, "mode": "create", "context": ctx, "demand": None}
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=False,
	)
	return {
		"ok": True,
		"mode": "edit",
		"context": ctx,
		"demand": _form_demand_dto(doc),
	}


@frappe.whitelist()
def save_demand_form(
	demand: str | None = None,
	values: str | dict | None = None,
	items: str | list | None = None,
) -> dict[str, Any]:
	"""DEM-UI-02 Save draft / Save changes."""
	actor = frappe.session.user
	require_operational_roles(ROLE_REQUESTER, user=actor)
	vals = _parse_json_arg(values) or {}
	if not isinstance(vals, dict):
		vals = {}
	item_rows = _parse_json_arg(items)
	if item_rows is not None and not isinstance(item_rows, list):
		item_rows = []
	# Prefer scoped defaults when create omits PE/OU.
	if not demand:
		pe, ou = _default_scope_for_actor(actor)
		vals.setdefault("procuring_entity", pe)
		vals.setdefault("owner_org_unit", ou)
	result = create_or_update_demand(
		demand=demand or None,
		values=vals,
		items=item_rows,
		user=actor,
	)
	doc = get_demand(result["demand"]["name"])
	return {"ok": True, "demand": _form_demand_dto(doc)}


@frappe.whitelist()
def submit_demand_form(
	demand: str | None = None,
	values: str | dict | None = None,
	items: str | list | None = None,
) -> dict[str, Any]:
	"""DEM-UI-02 Submit / DEM-UI-03 Resubmit — save then submit."""
	actor = frappe.session.user
	require_operational_roles(ROLE_REQUESTER, user=actor)
	saved = save_demand_form(demand=demand, values=values, items=items)
	name = saved["demand"]["name"]
	submitted = submit_demand(demand=name, user=actor)
	doc = get_demand(submitted["demand"]["name"])
	return {"ok": True, "demand": _form_demand_dto(doc)}
