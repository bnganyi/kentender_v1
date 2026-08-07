# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Desk APIs for Demands MVP-1 UI."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, flt, formatdate, getdate

from kentender_procurement.demands.services.demand_creation_scope import (
	MODE_BLOCKED,
	MODE_SINGLE,
	assert_creation_pair_allowed,
	resolve_demand_creation_scope,
)
from kentender_procurement.demands.services.demand_lifecycle import (
	cancel_and_release_demand,
	create_or_update_demand,
	enrich_demand,
	get_demand,
	list_demands_for_workspace,
	project_demand,
	record_business_decision,
	record_procurement_decision,
	submit_demand,
	suggest_strategy_context,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUSINESS,
	ROLE_PAA,
	ROLE_REQUESTER,
	assert_business_approver_segregation,
	assert_demand_scope,
	can_business_decide,
	can_edit_requester_fields,
	can_procurement_enrich,
	can_read_demand,
	ensure_demand_roles,
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

	creation_scope = resolve_demand_creation_scope(actor)
	return {
		"ok": True,
		"summary": summary,
		"entities": entities,
		"rows": page_rows,
		"total": total,
		"page": page_n,
		"page_size": size,
		"queue": q or "all",
		"creation_scope": {
			"selection_mode": creation_scope["selection_mode"],
			"blocked_reason": creation_scope.get("blocked_reason"),
		},
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
		["actor", "actor_role", "decided_at", "reason", "comment", "decision_input_snapshot"],
		as_dict=True,
		order_by="decided_at desc",
	)
	if not row:
		return None
	actor_name = frappe.utils.get_fullname(row.actor) if row.actor else "—"
	role = (row.actor_role or "").strip()
	# Prefer first known operational label if legacy comma-joined roles were stored.
	if "," in role:
		_labels = {
			"Requester": "Requester",
			"Business Approver": "Business Approver",
			"Procurement Approval Authority": "Procurement Approval Authority",
			"Budget Officer": "Budget Officer",
		}
		parts = [p.strip() for p in role.split(",") if p.strip()]
		role = next((p for p in parts if p in _labels), parts[0] if parts else "")
	returned_by = f"{actor_name}, {role}" if role else actor_name
	date_disp = ""
	if row.decided_at:
		try:
			date_disp = formatdate(getdate(row.decided_at), "dd MMMM yyyy")
		except Exception:
			date_disp = str(row.decided_at)
	reason = (row.reason or row.comment or "").strip()
	hints: list[dict[str, str]] = []
	available_funding = None
	available_funding_display = ""
	raw_snap = row.decision_input_snapshot or ""
	if isinstance(raw_snap, str) and raw_snap.strip().startswith("{"):
		try:
			snap = json.loads(raw_snap)
			if isinstance(snap, dict):
				for h in snap.get("correction_hints") or []:
					if not isinstance(h, dict):
						continue
					key = (h.get("key") or "").strip()
					label = (h.get("label") or key).strip()
					if key or label:
						hints.append({"key": key or label, "label": label or key})
				af = snap.get("available_funding")
				if af is not None and af != "":
					available_funding = flt(af)
					available_funding_display = f"{available_funding:,.2f}"
		except Exception:
			pass
	return {
		"returned_by": returned_by,
		"returned_at_display": date_disp,
		"reason": reason,
		"correction_hints": hints,
		"available_funding": available_funding,
		"available_funding_display": available_funding_display,
	}


_STATUS_DISPLAY = {
	"In Review": "In review",
	"Returned": "Returned",
	"Draft": "Draft",
	"Approved": "Approved",
	"Rejected": "Rejected",
	"Cancelled": "Cancelled",
}


def _form_demand_dto(doc) -> dict[str, Any]:
	base = project_demand(doc)
	base["procuring_entity_label"] = _entity_label(doc.procuring_entity)
	base["owner_org_unit_label"] = _unit_label(doc.owner_org_unit)
	base["requester_estimate_display"] = _money(
		flt(doc.requester_estimate), doc.currency or "KES"
	).replace((doc.currency or "KES") + " ", "")
	base["required_by_display"] = _required_by_display(doc.required_by_date)
	base["status_display"] = _STATUS_DISPLAY.get(doc.status, doc.status or "")
	est = flt(doc.requester_estimate)
	cur = doc.currency or "KES"
	base["estimate_header_display"] = f"{cur} {est:,.0f}" if est else f"{cur} 0"
	if doc.required_by_date:
		try:
			base["required_by_date"] = str(getdate(doc.required_by_date))
		except Exception:
			base["required_by_date"] = str(doc.required_by_date)
	for item in base.get("items") or []:
		est = flt(item.get("requester_estimate"))
		item["requester_estimate_display"] = f"{est:,.2f}" if est else ""
	if doc.status == "Returned":
		notice = _return_notice(doc.name)
		base["return_notice"] = notice
		base["available_funding"] = (notice or {}).get("available_funding")
		base["available_funding_display"] = (notice or {}).get("available_funding_display") or ""
	else:
		base["return_notice"] = None
		base["available_funding"] = None
		base["available_funding_display"] = ""
	return base


def _parse_json_arg(raw: Any) -> Any:
	if isinstance(raw, str) and raw.strip():
		try:
			return json.loads(raw)
		except Exception:
			return raw
	return raw


@frappe.whitelist()
def get_demand_form_context(
	procuring_entity: str | None = None,
	owner_org_unit: str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-02 create defaults — Contract v2.2 §7.5 creation-scope states."""
	actor = frappe.session.user
	if not can_read_demand(user=actor):
		frappe.throw("Not permitted to open Demand form", frappe.PermissionError)
	scope = resolve_demand_creation_scope(actor)
	pe = scope.get("procuring_entity")
	ou = scope.get("owner_org_unit")
	# Multi-scope: optional explicit pair for contact options after user selects.
	req_pe = (procuring_entity or "").strip() or None
	req_ou = (owner_org_unit or "").strip() or None
	if req_pe and req_ou and (req_pe, req_ou) != (pe, ou):
		from kentender_procurement.demands.services.demand_creation_scope import pair_is_eligible

		if pair_is_eligible(req_pe, req_ou, user=actor):
			pe, ou = req_pe, req_ou
	contacts = _contact_options(pe, ou) if pe else []
	can_edit = can_edit_requester_fields(user=actor) and scope["selection_mode"] != MODE_BLOCKED
	return {
		"ok": True,
		"can_edit": can_edit,
		"selection_mode": scope["selection_mode"],
		"pairs": scope["pairs"],
		"selected_pair": scope["selected_pair"],
		"blocked_reason": scope.get("blocked_reason"),
		"procuring_entity": scope.get("procuring_entity"),
		"owner_org_unit": scope.get("owner_org_unit"),
		"procuring_entity_label": scope.get("procuring_entity_label")
		or _entity_label(scope.get("procuring_entity")),
		"owner_org_unit_label": scope.get("owner_org_unit_label")
		or _unit_label(scope.get("owner_org_unit")),
		"contacts": contacts,
		"currency": "KES",
		"demand_routes": ["Standard", "Additional", "Emergency"],
		"confidence_levels": ["High", "Medium", "Low"],
		"uom_options": ["Lot", "Pieces", "Months"],
		# Create shell: Request Preparation is Current (shared record chrome).
		"stage_indicator": _stage_indicator("Request Preparation", "Draft"),
	}


@frappe.whitelist()
def get_demand_form(demand: str | None = None) -> dict[str, Any]:
	"""DEM-UI-02 / DEM-UI-03 load projection."""
	actor = frappe.session.user
	if not can_read_demand(user=actor):
		frappe.throw("Not permitted to open Demand form", frappe.PermissionError)
	ctx = get_demand_form_context()
	if not demand:
		return {
			"ok": True,
			"mode": "create",
			"context": ctx,
			"demand": None,
			"stage_indicator": ctx.get("stage_indicator")
			or _stage_indicator("Request Preparation", "Draft"),
		}
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
		"stage_indicator": _stage_indicator(doc.current_stage or "", doc.status or ""),
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
	# Create: only auto-fill PE/OU for single_readonly; never Admin/list fallback.
	if not demand:
		scope = resolve_demand_creation_scope(actor)
		if scope["selection_mode"] == MODE_SINGLE and scope.get("selected_pair"):
			vals.setdefault("procuring_entity", scope["selected_pair"]["procuring_entity"])
			vals.setdefault("owner_org_unit", scope["selected_pair"]["owner_org_unit"])
		assert_creation_pair_allowed(
			vals.get("procuring_entity"),
			vals.get("owner_org_unit"),
			user=actor,
		)
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


@frappe.whitelist()
def cancel_demand_form(demand: str, reason: str | None = None) -> dict[str, Any]:
	"""DEM-UI-03 Cancel demand (Draft/Returned preparation) with reason."""
	actor = frappe.session.user
	require_operational_roles(ROLE_REQUESTER, user=actor)
	if not (demand or "").strip():
		frappe.throw("Demand is required", frappe.ValidationError)
	if not (reason or "").strip():
		frappe.throw("A cancellation reason is required", frappe.ValidationError)
	result = cancel_and_release_demand(demand=demand, reason=reason, user=actor)
	doc = get_demand(result["demand"]["name"])
	return {"ok": True, "demand": _form_demand_dto(doc)}


_UI03_HINTS = [
	{"key": "items", "label": "Need items and participant quantities"},
	{"key": "expected_outcome", "label": "Expected outcome for the revised scope"},
	{"key": "requester_estimate", "label": "Requester estimate"},
]


def _ensure_ui03_ba(pe: str, ou: str) -> str:
	"""Ephemeral Business Approver for DEM-UI-03 factory (not the Requester)."""
	email = "dem-ui03-ba@example.test"
	ensure_demand_roles()
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "DEM",
				"last_name": "UI03 Approver",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	if ROLE_BUSINESS not in have:
		user.append("roles", {"role": ROLE_BUSINESS})
		user.save(ignore_permissions=True)
	existing = frappe.db.exists(
		"User Scope Assignment",
		{
			"user": email,
			"procuring_entity": pe,
			"organisation_unit": ou,
			"role": ROLE_BUSINESS,
		},
	)
	if not existing:
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": ROLE_BUSINESS,
				"procuring_entity": pe,
				"organisation_unit": ou,
				"include_descendants": 1,
				"fixture_namespace": "DEMANDS_UI03_FACTORY",
			}
		).insert(ignore_permissions=True)
	return email


@frappe.whitelist()
def prepare_returned_demand_ui03(
	requester: str | None = None,
	procuring_entity: str | None = None,
	owner_org_unit: str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-03 Playwright factory — create → submit → Return with Stitch hints.

	Restricted to System Manager / Administrator.
	"""
	actor = frappe.session.user
	if actor != "Administrator" and "System Manager" not in frappe.get_roles(actor):
		frappe.throw("Not permitted", frappe.PermissionError)

	req = (requester or "").strip() or "moh.medicalservices.officer@example.test"
	pe = (procuring_entity or "").strip() or "PE-MOH"
	ou = (owner_org_unit or "").strip() or "MOH-DIR-DHP"
	if not frappe.db.exists("User", req):
		frappe.throw(f"Requester {req} is missing", frappe.ValidationError)

	from frappe.utils import add_days, today

	created = create_or_update_demand(
		values={
			"procuring_entity": pe,
			"owner_org_unit": ou,
			"title": "Digital health technical staff certification programme",
			"need_statement": "Certify technical staff for digital health programmes",
			"need_rationale": "Skills gap blocks service continuity",
			"expected_outcome": "Certified cohort ready for deployment",
			"beneficiaries": "County digital health teams",
			"delivery_location": "Nairobi",
			"required_by_date": add_days(today(), 120),
			"demand_route": "Standard",
			"urgency": "Medium",
			"estimate_confidence": "Medium",
			"estimate_basis": "Programme unit cost × participants",
			"currency": "KES",
			"fixture_namespace": "DEMANDS_UI03_FACTORY",
		},
		items=[
			{
				"description": "Certification cohort seats",
				"quantity": 100,
				"uom": "Pieces",
				"requester_estimate": 95000000,
			}
		],
		user=req,
	)
	name = created["demand"]["name"]
	submit_demand(demand=name, user=req)
	ba = _ensure_ui03_ba(pe, ou)
	record_business_decision(
		demand=name,
		decision="Return",
		reason=(
			"The proposed scope exceeds available funding by KES 15,000,000. "
			"Revise the number of participants or provide a phased delivery approach."
		),
		user=ba,
		correction_hints=list(_UI03_HINTS),
		available_funding=80000000,
	)
	frappe.db.commit()
	doc = get_demand(name)
	return {
		"ok": True,
		"demand": doc.name,
		"demand_code": doc.demand_code,
		"status": doc.status,
		"form": _form_demand_dto(doc),
	}


_REVIEW_STAGE_ORDER = (
	"Request Preparation",
	"Business Review",
	"Procurement Enrichment",
	"Budget Confirmation",
	"Final Approval",
)

_BUSINESS_REVIEW_PROMPTS = (
	"The need is necessary and supports the unit's responsibilities.",
	"The expected outcome and beneficiaries are clear.",
	"The timing and priority are justified.",
	"The owning unit accepts accountability for the Demand.",
)

_NON_FINAL_DISCLAIMER = (
	"Business support does not confirm funding or constitute final procurement approval."
)


def _stage_indicator(current_stage: str, status: str) -> list[dict[str, str]]:
	"""Shared DEM-UIC-002 stage strip states for the current Demand."""
	stage = (current_stage or "").strip()
	st = (status or "").strip()
	if st in ("Approved", "Rejected", "Cancelled") or stage == "Complete":
		return [
			{"key": k, "label": k, "state": "Complete"} for k in _REVIEW_STAGE_ORDER
		]
	try:
		idx = _REVIEW_STAGE_ORDER.index(stage)
	except ValueError:
		idx = 0
	out: list[dict[str, str]] = []
	for i, key in enumerate(_REVIEW_STAGE_ORDER):
		if i < idx:
			state = "Complete"
		elif i == idx:
			state = "Current"
		else:
			state = "Not started"
		out.append({"key": key, "label": key, "state": state})
	return out


_ENRICHMENT_CATEGORIES = (
	"ICT infrastructure and services",
	"Medical Equipment",
	"Software Licensing",
	"Works",
	"Goods",
	"Services",
)

_AGGREGATION_TREATMENTS = (
	"Retain as one aggregation candidate for Planning",
	"Merge with existing demand",
	"Proceed independently",
)

# DEM-ABS — never surface procurement-method / tender chrome on enrichment.
_FORBIDDEN_ENRICHMENT_KEYS = frozenset(
	{
		"procurement_method",
		"tender_method",
		"method_of_procurement",
		"evaluation_method",
	}
)


def _review_demand_dto(doc) -> dict[str, Any]:
	base = _form_demand_dto(doc)
	base["technical_contact_label"] = (
		frappe.utils.get_fullname(doc.technical_contact) if doc.technical_contact else "—"
	)
	base["requester_label"] = (
		frappe.utils.get_fullname(doc.requester) if doc.requester else "—"
	)
	# status_display + estimate_header_display already on _form_demand_dto
	cur = doc.currency or "KES"
	conf = flt(doc.confirmed_estimate)
	base["confirmed_estimate_display"] = f"{conf:,.2f}" if conf else ""
	base["confirmed_estimate_header"] = f"{cur} {conf:,.0f}" if conf else f"{cur} 0"
	for item in base.get("items") or []:
		qty = item.get("quantity")
		uom = (item.get("uom") or "").strip()
		if qty is not None and qty != "":
			try:
				qty_n = flt(qty)
				qty_s = f"{qty_n:g}" if qty_n == int(qty_n) else f"{qty_n}"
			except Exception:
				qty_s = str(qty)
			item["quantity_display"] = f"{qty_s} {uom}".strip() if uom else qty_s
		else:
			item["quantity_display"] = uom or "—"
		cq = item.get("confirmed_quantity")
		if cq is None or cq == "":
			item["confirmed_quantity"] = item.get("quantity")
		cu = (item.get("confirmed_uom") or "").strip()
		if not cu:
			item["confirmed_uom"] = item.get("uom") or ""
		ce = item.get("confirmed_estimate")
		if ce is None or ce == "":
			item["confirmed_estimate"] = item.get("requester_estimate")
		ce_n = flt(item.get("confirmed_estimate"))
		item["confirmed_estimate_display"] = f"{ce_n:,.2f}" if ce_n else ""
	# Strip abs-forbidden keys if ever present on projection.
	for key in _FORBIDDEN_ENRICHMENT_KEYS:
		base.pop(key, None)
	return base


def _strategy_refs_dto(demand_name: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Demand Strategy Reference",
		filters={"demand": demand_name},
		fields=[
			"name",
			"reference_type",
			"plan",
			"plan_version_id",
			"target_id",
			"target_code",
			"target_name",
			"hierarchy_path",
			"snapshot_label",
			"selection_source",
			"confirmation_reason",
		],
		order_by="creation asc",
	)
	return list(rows or [])


def _value_treatments_dto(demand_name: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Demand Value Treatment",
		filters={"demand": demand_name},
		fields=[
			"name",
			"plan_value_commitment",
			"pvc_version_id",
			"pvc_snapshot",
			"applicability",
			"treatment",
			"rationale",
		],
		order_by="creation asc",
	)
	return list(rows or [])


def _business_support_summary(demand_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"Demand Decision",
		filters={
			"demand": demand_name,
			"stage": "Business Review",
			"decision": "Support",
		},
		fields=["actor", "comment", "decided_at"],
		order_by="decided_at desc",
		limit=1,
	)
	if not rows:
		return None
	row = rows[0]
	return {
		"actor": row.actor,
		"actor_label": frappe.utils.get_fullname(row.actor) if row.actor else "—",
		"comment": row.comment or "",
		"decided_at": str(row.decided_at) if row.decided_at else None,
	}


def _enrichment_readiness(doc) -> tuple[bool, list[str]]:
	blockers: list[str] = []
	if flt(doc.confirmed_estimate) <= 0:
		blockers.append("confirmed estimate is required")
	if not (doc.procurement_category or "").strip():
		blockers.append("procurement category is required")
	primaries = frappe.get_all(
		"Demand Strategy Reference",
		filters={"demand": doc.name, "reference_type": "Primary"},
		pluck="name",
	)
	if len(primaries) != 1:
		blockers.append("exactly one Primary Strategy reference is required")
	return (len(blockers) == 0, blockers)


def _enrichment_projection(doc) -> dict[str, Any]:
	refs = _strategy_refs_dto(doc.name)
	primaries = [r for r in refs if (r.get("reference_type") or "") == "Primary"]
	supporting = [r for r in refs if (r.get("reference_type") or "") == "Supporting"]
	ready, blockers = _enrichment_readiness(doc)
	return {
		"categories": list(_ENRICHMENT_CATEGORIES),
		"aggregation_treatments": list(_AGGREGATION_TREATMENTS),
		"demand_routes": ["Standard", "Additional", "Emergency"],
		"strategy_alignment": "Assigned" if primaries else "Not assigned",
		"strategy_references": refs,
		"primary_strategy": primaries[0] if primaries else None,
		"supporting_strategies": supporting,
		"value_treatments": _value_treatments_dto(doc.name),
		"business_decision_summary": _business_support_summary(doc.name),
		"send_ready": ready,
		"send_blockers": blockers,
		"duplicate_assessment": doc.get("duplicate_assessment") or "None found",
		"related_demands_note": doc.get("related_demands_note") or "",
		"aggregation_treatment": doc.get("aggregation_treatment") or "",
		"aggregation_rationale": doc.get("aggregation_rationale") or "",
	}


@frappe.whitelist()
def get_demand_review(demand: str) -> dict[str, Any]:
	"""DEM-UI-04…08 shared review load projection (Business + Enrichment stages)."""
	actor = frappe.session.user
	if not can_read_demand(user=actor):
		frappe.throw("Not permitted to open Demand review", frappe.PermissionError)
	if not (demand or "").strip():
		frappe.throw("Demand is required", frappe.ValidationError)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=False,
	)
	stage = (doc.current_stage or "").strip()
	is_business = stage == "Business Review" and doc.status == "In Review"
	is_enrichment = stage == "Procurement Enrichment" and doc.status == "In Review"
	can_decide = False
	can_enrich = False
	allowed: list[str] = []
	if is_business and can_business_decide(user=actor):
		try:
			assert_business_approver_segregation(requester=doc.requester, actor=actor)
			can_decide = True
			allowed = ["Support", "Return", "Reject"]
		except Exception:
			can_decide = False
			allowed = []
	if is_enrichment and can_procurement_enrich(user=actor):
		can_enrich = True
		allowed = [
			"Save enrichment",
			"Send for budget confirmation",
			"Return",
			"Reject",
		]
	enrichment = _enrichment_projection(doc) if is_enrichment else None
	return {
		"ok": True,
		"stage": stage,
		"can_decide": can_decide,
		"can_enrich": can_enrich,
		"allowed_actions": allowed,
		"show_non_final_disclaimer": is_business,
		"non_final_disclaimer": _NON_FINAL_DISCLAIMER if is_business else "",
		"review_prompts": list(_BUSINESS_REVIEW_PROMPTS) if is_business else [],
		"stage_indicator": _stage_indicator(stage, doc.status),
		"demand": _review_demand_dto(doc),
		"enrichment": enrichment,
	}


@frappe.whitelist()
def record_business_decision_form(
	demand: str,
	decision: str,
	reason: str | None = None,
	comment: str | None = None,
	correction_hints: str | list | None = None,
	available_funding: float | str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-04 — Support / Return / Reject via whitelist."""
	actor = frappe.session.user
	require_operational_roles(ROLE_BUSINESS, user=actor)
	if not (demand or "").strip():
		frappe.throw("Demand is required", frappe.ValidationError)
	action = (decision or "").strip()
	if action not in ("Support", "Return", "Reject"):
		frappe.throw("decision must be Support, Return or Reject", frappe.ValidationError)
	if action in ("Return", "Reject") and not (reason or "").strip():
		frappe.throw("A reason is required", frappe.ValidationError)
	doc = get_demand(demand)
	assert_business_approver_segregation(requester=doc.requester, actor=actor)
	hints = _parse_json_arg(correction_hints)
	if hints is not None and not isinstance(hints, list):
		hints = []
	af = None
	if available_funding is not None and available_funding != "":
		af = flt(available_funding)
	result = record_business_decision(
		demand=demand,
		decision=action,
		reason=reason,
		comment=comment,
		user=actor,
		correction_hints=hints if action == "Return" else None,
		available_funding=af if action == "Return" else None,
	)
	fresh = get_demand(result["demand"]["name"])
	return {"ok": True, "demand": _review_demand_dto(fresh)}


def _ensure_ui04_ba(pe: str, ou: str) -> str:
	"""Canonical Business Approver for DEM-UI-04 factory (Contract §7.1)."""
	email = "moh.business.approver@example.test"
	ensure_demand_roles()
	from frappe.utils.password import update_password

	from kentender_core.seeds import constants as CoreC

	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "James",
				"last_name": "Mwangi",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	update_password(email, CoreC.TEST_PASSWORD)
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	changed = False
	if ROLE_BUSINESS not in have:
		user.append("roles", {"role": ROLE_BUSINESS})
		changed = True
	if "Desk User" not in have:
		user.append("roles", {"role": "Desk User"})
		changed = True
	if changed:
		user.save(ignore_permissions=True)
	existing = frappe.db.exists(
		"User Scope Assignment",
		{
			"user": email,
			"procuring_entity": pe,
			"organisation_unit": ou,
			"role": ROLE_BUSINESS,
		},
	)
	if not existing:
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": ROLE_BUSINESS,
				"procuring_entity": pe,
				"organisation_unit": ou,
				"include_descendants": 1,
				"fixture_namespace": "DEMANDS_UI04_FACTORY",
			}
		).insert(ignore_permissions=True)
	return email


@frappe.whitelist()
def prepare_business_review_ui04(
	requester: str | None = None,
	procuring_entity: str | None = None,
	owner_org_unit: str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-04 Playwright factory — create → submit; leave In Review / Business Review.

	Restricted to System Manager / Administrator.
	"""
	actor = frappe.session.user
	if actor != "Administrator" and "System Manager" not in frappe.get_roles(actor):
		frappe.throw("Not permitted", frappe.PermissionError)

	req = (requester or "").strip() or "moh.medicalservices.officer@example.test"
	pe = (procuring_entity or "").strip() or "PE-MOH"
	ou = (owner_org_unit or "").strip() or "MOH-DIR-DHP"
	if not frappe.db.exists("User", req):
		frappe.throw(f"Requester {req} is missing", frappe.ValidationError)

	from frappe.utils import add_days, today

	ba = _ensure_ui04_ba(pe, ou)
	created = create_or_update_demand(
		values={
			"procuring_entity": pe,
			"owner_org_unit": ou,
			"title": "National digital health infrastructure upgrade",
			"need_statement": (
				"Major upgrade to national digital health infrastructure to support "
				"clinical data centralisation and resilient compute services for district hospitals."
			),
			"need_rationale": "Clinical data continuity requires resilient national infrastructure",
			"expected_outcome": "Resilient compute and network services for district hospitals",
			"beneficiaries": (
				"Ministry of Health staff (HQ); 47 county health facilities and data centers; "
				"National reference laboratories"
			),
			"delivery_location": "National Data Centre, Nairobi",
			"required_by_date": add_days(today(), 90),
			"demand_route": "Standard",
			"urgency": "Medium",
			"estimate_confidence": "Medium",
			"estimate_basis": "Recent framework prices and vendor quotes",
			"currency": "KES",
			"fixture_namespace": "DEMANDS_UI04_FACTORY",
		},
		items=[
			{
				"description": "Resilient compute capacity for clinical workloads",
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": 300000000,
			},
			{
				"description": "Network and monitoring for district sites",
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": 155000000,
			},
		],
		user=req,
	)
	name = created["demand"]["name"]
	# Align total with Stitch header example when items sum cleanly.
	frappe.db.set_value("Demand", name, "requester_estimate", 455000000, update_modified=False)
	submit_demand(demand=name, user=req)
	frappe.db.commit()
	doc = get_demand(name)
	return {
		"ok": True,
		"demand": doc.name,
		"demand_code": doc.demand_code,
		"status": doc.status,
		"current_stage": doc.current_stage,
		"business_approver": ba,
		"review": _review_demand_dto(doc),
	}


@frappe.whitelist()
def enrich_demand_form(
	demand: str,
	values: str | dict | None = None,
	items: str | list | None = None,
	strategy_references: str | list | None = None,
	value_treatments: str | list | None = None,
	send_for_budget: int | str | bool | None = 0,
) -> dict[str, Any]:
	"""DEM-UI-05 — Save enrichment / Send for Budget confirmation."""
	actor = frappe.session.user
	require_operational_roles(ROLE_PAA, user=actor)
	if not (demand or "").strip():
		frappe.throw("Demand is required", frappe.ValidationError)
	vals = _parse_json_arg(values) or {}
	if not isinstance(vals, dict):
		vals = {}
	for key in _FORBIDDEN_ENRICHMENT_KEYS:
		vals.pop(key, None)

	def _optional_list(raw: Any) -> list | None:
		"""None / blank means 'leave unchanged'; [] means explicit clear."""
		parsed = _parse_json_arg(raw)
		if parsed is None or parsed == "":
			return None
		if not isinstance(parsed, list):
			frappe.throw("Expected a list payload", frappe.ValidationError)
		return parsed

	item_rows = _optional_list(items)
	refs = _optional_list(strategy_references)
	treatments = _optional_list(value_treatments)
	result = enrich_demand(
		demand=demand,
		values=vals,
		items=item_rows,
		strategy_references=refs,
		value_treatments=treatments,
		send_for_budget=bool(cint(send_for_budget)),
		user=actor,
	)
	fresh = get_demand(result["demand"]["name"])
	return {
		"ok": True,
		"demand": _review_demand_dto(fresh),
		"enrichment": _enrichment_projection(fresh),
		"stage": fresh.current_stage,
	}


@frappe.whitelist()
def suggest_strategy_context_form(
	demand: str,
	q: str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-05A — scoped Strategy suggestions for Assign drawer."""
	actor = frappe.session.user
	require_operational_roles(ROLE_PAA, user=actor)
	if not (demand or "").strip():
		frappe.throw("Demand is required", frappe.ValidationError)
	raw = suggest_strategy_context(demand=demand, user=actor)
	suggestions = list(raw.get("suggestions") or [])
	needle = (q or "").strip().lower()
	if needle:
		filtered = []
		for s in suggestions:
			hay = " ".join(
				[
					str(s.get("node_name") or ""),
					str(s.get("node_code") or ""),
					str(s.get("plan_code") or ""),
					str(s.get("snapshot_label") or ""),
				]
			).lower()
			if needle in hay:
				filtered.append(s)
		suggestions = filtered
	# Display DTO: name + code only (never raw id as primary label).
	out = []
	for s in suggestions:
		out.append(
			{
				"plan_version_id": s.get("plan_version_id"),
				"plan_code": s.get("plan_code"),
				"plan_version": s.get("plan_version"),
				"target_id": s.get("node_id"),
				"target_code": s.get("node_code"),
				"target_name": s.get("node_name"),
				"snapshot_label": s.get("snapshot_label")
				or f"{s.get('node_name')} ({s.get('node_code')})",
				"hierarchy_path": s.get("snapshot_label") or "",
				"path": s.get("path") or [],
				"display_name": s.get("node_name") or "",
				"display_code": s.get("node_code") or "",
			}
		)
	return {
		"ok": True,
		"demand_code": raw.get("demand_code"),
		"strategy_alignment": raw.get("strategy_alignment") or "Not assigned",
		"suggestions": out,
	}


@frappe.whitelist()
def record_procurement_decision_form(
	demand: str,
	decision: str,
	reason: str | None = None,
	comment: str | None = None,
	correction_hints: str | list | None = None,
) -> dict[str, Any]:
	"""DEM-UI-05 — PAA Return / Reject from Procurement Enrichment."""
	actor = frappe.session.user
	require_operational_roles(ROLE_PAA, user=actor)
	if not (demand or "").strip():
		frappe.throw("Demand is required", frappe.ValidationError)
	action = (decision or "").strip()
	if action not in ("Return", "Reject"):
		frappe.throw("decision must be Return or Reject", frappe.ValidationError)
	if not (reason or "").strip():
		frappe.throw("A reason is required", frappe.ValidationError)
	hints = _parse_json_arg(correction_hints)
	if hints is not None and not isinstance(hints, list):
		hints = []
	result = record_procurement_decision(
		demand=demand,
		decision=action,
		reason=reason,
		comment=comment,
		user=actor,
		correction_hints=hints if action == "Return" else None,
	)
	fresh = get_demand(result["demand"]["name"])
	return {"ok": True, "demand": _review_demand_dto(fresh), "stage": fresh.current_stage}


def _ensure_ui05_paa(pe: str, ou: str) -> str:
	"""Canonical Procurement Approval Authority for DEM-UI-05 factory."""
	email = "moh.procurement.approver@example.test"
	ensure_demand_roles()
	from frappe.utils.password import update_password

	from kentender_core.seeds import constants as CoreC

	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Amina",
				"last_name": "Otieno",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	update_password(email, CoreC.TEST_PASSWORD)
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	changed = False
	if ROLE_PAA not in have:
		user.append("roles", {"role": ROLE_PAA})
		changed = True
	if "Desk User" not in have:
		user.append("roles", {"role": "Desk User"})
		changed = True
	if changed:
		user.save(ignore_permissions=True)
	existing = frappe.db.exists(
		"User Scope Assignment",
		{
			"user": email,
			"procuring_entity": pe,
			"organisation_unit": ou,
			"role": ROLE_PAA,
		},
	)
	if not existing:
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": ROLE_PAA,
				"procuring_entity": pe,
				"organisation_unit": ou,
				"include_descendants": 1,
				"fixture_namespace": "DEMANDS_UI05_FACTORY",
			}
		).insert(ignore_permissions=True)
	return email


@frappe.whitelist()
def prepare_enrichment_ui05(
	requester: str | None = None,
	procuring_entity: str | None = None,
	owner_org_unit: str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-05 Playwright factory — create → submit → Support → Enrichment.

	Restricted to System Manager / Administrator.
	"""
	actor = frappe.session.user
	if actor != "Administrator" and "System Manager" not in frappe.get_roles(actor):
		frappe.throw("Not permitted", frappe.PermissionError)

	req = (requester or "").strip() or "moh.medicalservices.officer@example.test"
	pe = (procuring_entity or "").strip() or "PE-MOH"
	ou = (owner_org_unit or "").strip() or "MOH-DIR-DHP"
	if not frappe.db.exists("User", req):
		frappe.throw(f"Requester {req} is missing", frappe.ValidationError)

	from frappe.utils import add_days, today

	ba = _ensure_ui04_ba(pe, ou)
	paa = _ensure_ui05_paa(pe, ou)
	created = create_or_update_demand(
		values={
			"procuring_entity": pe,
			"owner_org_unit": ou,
			"title": "National digital health infrastructure upgrade",
			"need_statement": (
				"Urgent upgrade of core server infrastructure to support the new "
				"National EMR system rollout."
			),
			"need_rationale": "Clinical data continuity requires resilient national infrastructure",
			"expected_outcome": "Resilient compute and network services for district hospitals",
			"beneficiaries": "National hospitals, 50M+ citizens",
			"delivery_location": "National Data Centre, Nairobi",
			"required_by_date": add_days(today(), 90),
			"demand_route": "Standard",
			"urgency": "Medium",
			"estimate_confidence": "Medium",
			"estimate_basis": "Market research and infrastructure assessment",
			"currency": "KES",
			"fixture_namespace": "DEMANDS_UI05_FACTORY",
		},
		items=[
			{
				"description": "High-performance compute cluster",
				"quantity": 2,
				"uom": "units",
				"requester_estimate": 200000000,
			},
			{
				"description": "Scalable storage arrays (10 PB)",
				"quantity": 1,
				"uom": "set",
				"requester_estimate": 255000000,
			},
		],
		user=req,
	)
	name = created["demand"]["name"]
	frappe.db.set_value("Demand", name, "requester_estimate", 455000000, update_modified=False)
	submit_demand(demand=name, user=req)
	record_business_decision(
		demand=name,
		decision="Support",
		comment="Aligned with unit digital health responsibilities",
		user=ba,
	)
	frappe.db.commit()
	doc = get_demand(name)
	return {
		"ok": True,
		"demand": doc.name,
		"demand_code": doc.demand_code,
		"status": doc.status,
		"current_stage": doc.current_stage,
		"business_approver": ba,
		"procurement_approver": paa,
		"review": _review_demand_dto(doc),
		"enrichment": _enrichment_projection(doc),
	}
