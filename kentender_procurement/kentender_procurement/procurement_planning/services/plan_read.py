# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.1 — Annual Plan, Plan Item, Finance, governance and
publication read models (PLN-UI-07..14).

`GetPlanVersion` serves the Draft workbench (PLN-DES-07): summary strip with
the reserved share, the unallocated accepted-source pool (§8.1
ListAcceptedDPPSources, classification joined through the immutable
validation decision), the Plan Items, and the nine-row readiness card.
`GetPlanItem` serves the editor (PLN-DES-09/09A): read-only sources, the
Identity / Classification and method / Preference and structure cards, the
live-recomputed baseline schedule with its closed period disclosure, and —
on an Active Version — the baseline / forecast / actual tiers. `GetFinanceTask`
serves the plan-level affordability statement (PLN-DES-10);
`GetPlanGovernanceTask` the immutable snapshot (PLN-DES-11/12);
`GetPublicationTask` the attempt result (PLN-DES-13).

**Source correction required** is derived here, never stored (§4.9). Every
offer (`mutable`, `can_act`, `can_request_funding`, `can_submit`) is
computed from the same resolver the commands use (read-offer parity).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, fmt_money, formatdate

from kentender_procurement.procurement_planning.errors import MESSAGES
from kentender_procurement.procurement_planning.services import needs_intake, readiness, references, schedule
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_AUDITOR,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)

PAGE = "procurement-planning"
PLAN_READERS = (ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR, ROLE_FINANCE_CONFIRMATION_OFFICER, ROLE_ACCOUNTING_OFFICER, ROLE_PLAN_STATUTORY_APPROVER)


def _money(amount: float) -> str:
	return f"KES {fmt_money(flt(amount), precision=0, currency=None).strip()}"


def _date(value) -> str:
	return formatdate(value, "d MMM yyyy") if value else ""


def _eat(value) -> str:
	"""A UTC instant rendered as EAT (§12.13)."""
	if not value:
		return ""
	from frappe.utils import convert_utc_to_timezone, format_datetime, get_datetime

	local = convert_utc_to_timezone(get_datetime(value), "Africa/Nairobi")
	return f"{format_datetime(local, 'd MMM yyyy, HH:mm')} EAT"


def _unit_label(unit: str) -> str:
	return cstr(frappe.db.get_value("UOM", unit, "uom_name") or unit)


def _quantity_display(quantity, unit: str) -> str:
	return f"{flt(quantity):g} {_unit_label(unit).lower()}".strip()


def _ou_label(ou: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


def _plan_root(plan_reference: str):
	name = frappe.db.get_value("Annual Plan", {"plan_reference": cstr(plan_reference)})
	if not name:
		authz.not_found()
	return frappe.get_doc("Annual Plan", name)


def _open_version(plan):
	name = cstr(plan.open_successor_version) or cstr(plan.active_version)
	if not name:
		authz.not_found()
	return frappe.get_doc("Annual Plan Version", name)


def _classifications(dpp_version: str) -> dict[str, str]:
	decision = frappe.db.get_value(
		"Departmental Plan Validation Decision",
		{"submission": frappe.db.get_value("Departmental Plan Submission", {"dpp_version": dpp_version}, "name"), "decision": "Accept departmental plan"},
		"classifications",
	)
	return json.loads(decision) if decision else {}


def _line_labels(fiscal_year: str) -> dict[str, dict[str, Any]]:
	from kentender_procurement.procurement_planning.services import budget_gateway

	try:
		return budget_gateway.line_labels(fiscal_year)
	except Exception:
		return {}


def _accepted_entry_rows(fiscal_year: str) -> list[dict[str, Any]]:
	"""§8.1 ListAcceptedDPPSources — every current accepted entry that
	proceeds, its classification and its current allocation (if any)."""
	accepted = frappe.get_all(
		"Departmental Plan", filters={"fiscal_year": fiscal_year, "current_accepted_version": ("!=", "")},
		fields=["name", "organisation_unit", "current_accepted_version"],
	)
	labels = _line_labels(fiscal_year)
	rows: list[dict[str, Any]] = []
	for root in accepted:
		version = root.current_accepted_version
		classifications = _classifications(version)
		entries = frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": version},
			fields=["name", "entry_id", "title", "source_origin", "quantity", "unit", "required_by_date", "budget_line", "indicative_amount", "not_proceeding_reason"],
		)
		ou_label = _ou_label(root.organisation_unit)
		for entry in entries:
			if cstr(entry.not_proceeding_reason).strip():
				continue
			rows.append(
				{
					"dpp_entry": entry.name,
					"entry_id": entry.entry_id,
					"title": entry.title,
					"department": ou_label,
					"organisation_unit": root.organisation_unit,
					"source_origin": entry.source_origin,
					"classification": cstr(classifications.get(entry.entry_id)),
					"quantity": flt(entry.quantity),
					"quantity_display": _quantity_display(entry.quantity, entry.unit),
					"unit": entry.unit,
					"required_by_date": cstr(entry.required_by_date),
					"required_by_display": _date(entry.required_by_date),
					"budget_line": entry.budget_line,
					"budget_line_display": labels.get(cstr(entry.budget_line), {}).get("reference") or cstr(entry.budget_line),
					"indicative_amount": flt(entry.indicative_amount),
					"amount_display": _money(entry.indicative_amount),
				}
			)
	return rows


def _allocated_dpp_entries(plan_version: str) -> set[str]:
	return set(frappe.get_all("Plan Source Allocation", filters={"plan_version": plan_version, "allocation_state": ("in", ("Draft", "Active"))}, pluck="dpp_entry"))


def source_correction_required(dpp_entry: str) -> bool:
	entry = frappe.db.get_value("Departmental Plan Entry", dpp_entry, ["entry_id", "dpp_version"], as_dict=True)
	if not entry:
		return True
	root_name = frappe.db.get_value("Departmental Plan Version", entry.dpp_version, "departmental_plan")
	current_accepted = frappe.db.get_value("Departmental Plan", root_name, "current_accepted_version")
	if not current_accepted or current_accepted == entry.dpp_version:
		return False
	current_entry = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": current_accepted, "entry_id": entry.entry_id}, "name")
	return current_entry != dpp_entry


def resolve_item_doc_name(plan_item_id: str) -> str:
	"""A Plan Item's business id can name two live docs at once (the Active
	predecessor's frozen copy and its Draft successor's copy); the one open
	to act on wins — the same precedence `_open_version` uses."""
	rows = frappe.get_all("Annual Plan Item", filters={"plan_item_id": cstr(plan_item_id)}, fields=["name", "plan_version"])
	if not rows:
		authz.not_found()
	if len(rows) == 1:
		return rows[0].name
	plan_name = frappe.db.get_value("Annual Plan Version", rows[0].plan_version, "annual_plan")
	open_successor = cstr(frappe.db.get_value("Annual Plan", plan_name, "open_successor_version"))
	for row in rows:
		if row.plan_version == open_successor:
			return row.name
	return rows[0].name


# --------------------------------------------------------------------------
# Readiness (PLN-DES-07 card)
# --------------------------------------------------------------------------


def _item_docs(version_name: str) -> list:
	return [frappe.get_doc("Annual Plan Item", n) for n in frappe.get_all("Annual Plan Item", filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")}, order_by="creation asc", pluck="name")]


def plan_readiness(version, plan) -> dict[str, Any]:
	"""The exact blocker list and the DES-07 nine-row card."""
	from kentender_procurement.procurement_planning.services import plan_finance, strategy_gateway

	reference = readiness.reference_for(plan.fiscal_year)
	items = _item_docs(version.name)
	eligible = {row["id"] for row in strategy_gateway.list_eligible_strategic_objectives()}
	blockers: list[dict[str, Any]] = []
	per_check = {"objective": [], "reservation": [], "contents": [], "schedule": [], "method": []}
	for item in items:
		allocations = readiness._allocations(item.name)
		if any(source_correction_required(a.dpp_entry) for a in allocations):
			blockers.append({"code": "PLN_SOURCE_CORRECTION_REQUIRED", "plan_item_id": item.plan_item_id, "message": f"{MESSAGES['PLN_SOURCE_CORRECTION_REQUIRED']} ({item.plan_item_id})"})
		objective_ok = bool(cstr(item.strategic_objective)) and (cstr(item.strategic_objective) in eligible or version.version_status == "Active")
		for blocker in readiness.item_blockers(item, allocations, reference, objective_eligible=objective_ok):
			blockers.append({**blocker, "plan_item_id": item.plan_item_id, "message": f"{MESSAGES[blocker['code']]} ({item.plan_item_id})"})
			key = {
				"PLN_OBJECTIVE_INELIGIBLE": "objective", "PLN_RESERVATION_REQUIRED": "reservation",
				"PLN_PLAN_CONTENTS_INCOMPLETE": "contents", "PLN_ENTRY_INCOMPLETE": "contents",
				"PLN_SCHEDULE_INVALID": "schedule", "PLN_DELIVERY_BOUNDARY_INSUFFICIENT": "schedule",
				"PLN_METHOD_NOT_ADMISSIBLE": "method", "PLN_REFERENCE_UNAVAILABLE": "method",
			}[blocker["code"]]
			per_check[key].append(item.plan_item_id)
	for pid in readiness.low_value_cumulative_breaches(version.name, reference):
		blockers.append({"code": "PLN_METHOD_NOT_ADMISSIBLE", "plan_item_id": pid, "message": f"Low value procurement exceeds the per-item annual limit ({pid})."})
		per_check["method"].append(pid)

	share = readiness.reserved_share(version.name)
	target = reference.get("reservation", {}).get("target_percent")
	county_target = reference.get("reservation", {}).get("county_target_percent")
	is_county = bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county"))
	advisories = readiness.splitting_advisory(version.name, reference)
	affordability = None
	if items:
		try:
			affordability = plan_finance.affordability_statement(plan, version)
		except Exception:
			affordability = None
	within_approved = bool(affordability and affordability.get("within_approved"))
	if items and affordability and not within_approved:
		blockers.append({"code": "PLN_PLAN_NOT_AFFORDABLE", "message": MESSAGES["PLN_PLAN_NOT_AFFORDABLE"], "failing_lines": affordability.get("failing_lines", [])})
	funding_current = plan_finance.funding_is_current(version, affordability) if items and affordability else False

	def _state(started: bool, failing: list[str]) -> tuple[str, str]:
		if not started:
			return "Not started", "neutral"
		return ("Complete", "live") if not failing else (f"{len(failing)} to fix", "attention")

	started = bool(items)
	checks = [
		{"check": "Every Plan Item has a Strategic Objective", **dict(zip(("result", "kind"), _state(started, per_check["objective"])))},
		{"check": "Every Plan Item has a reservation category", **dict(zip(("result", "kind"), _state(started, per_check["reservation"])))},
		{"check": "Every Plan Item records plan horizon, aggregation and lotting", **dict(zip(("result", "kind"), _state(started, per_check["contents"])))},
		{"check": "Baseline schedule meets the governed periods and delivery boundary", **dict(zip(("result", "kind"), _state(started, per_check["schedule"])))},
		{"check": "Procurement method admissible for value", **dict(zip(("result", "kind"), _state(started, per_check["method"])))},
		{"check": "Plan within approved budget", "result": ("Within approved" if within_approved else ("Exceeds approved" if affordability else "Not started")) if started else "Not started", "kind": ("live" if within_approved else "critical") if (started and affordability) else "neutral"},
		{"check": "Plan funding confirmed", "result": ("Confirmed" if funding_current else {"Awaiting Finance": "Awaiting Finance", "Returned": "Returned by Finance", "Stale": "Confirmation stale"}.get(version.funding_state, "Not started")) if started else "Not started", "kind": "live" if funding_current else ("attention" if version.funding_state in ("Awaiting Finance", "Returned", "Stale") else "neutral")},
		{"check": "Preference and reservation target", "result": (f"{share['percent']:.0f}% of plan value reserved · target {target:.0f}%" if target else f"{share['percent']:.0f}% of plan value reserved · target not published"), "kind": "advisory"},
		{"check": "Contract splitting review", "result": ("No advisory" if not advisories else ("Confirmed" if cstr(version.splitting_confirmation).strip() else f"{len(advisories)} advisory")), "kind": "neutral" if not advisories or cstr(version.splitting_confirmation).strip() else "advisory"},
	]
	if is_county:
		checks.append({"check": "County resident-tenderer reservation", "result": f"{share['county_percent']:.0f}% of plan value · minimum {county_target or 20:.0f}%", "kind": "advisory"})
	return {
		"checks": checks,
		"blockers": blockers,
		"advisories": advisories,
		"reserved_share": share,
		"reservation_target": target,
		"reference_available": bool(reference.get("available")),
		"affordability": affordability,
		"funding_current": funding_current,
		"within_approved": within_approved,
	}


# --------------------------------------------------------------------------
# GetPlanVersion (PLN-DES-07 / DES-14)
# --------------------------------------------------------------------------


def _item_rows(plan_version: str) -> list[dict[str, Any]]:
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": plan_version, "item_state": ("!=", "Dissolved")},
		fields=["name", "plan_item_id", "title", "item_state", "requirement_type", "procurement_method", "reservation_category", "baseline_delivery_completion_date"],
		order_by="creation asc",
	)
	rows = []
	for item in items:
		allocations = readiness._allocations(item.name)
		value = sum(flt(a.indicative_amount) for a in allocations)
		rows.append(
			{
				"plan_item_id": item.plan_item_id,
				"title": item.title,
				"item_state": item.item_state,
				"requirement_type": item.requirement_type,
				"procurement_method": cstr(item.procurement_method),
				"reservation_category": cstr(item.reservation_category) or "—",
				"completion_display": _date(item.baseline_delivery_completion_date),
				"sources": len(allocations),
				"departments": " / ".join(sorted({_ou_label(a_ou) for a_ou in {frappe.db.get_value("Plan Source Allocation", a.name, "organisation_unit") for a in allocations}})),
				"value_display": _money(value),
				"source_correction_required": any(source_correction_required(a.dpp_entry) for a in allocations),
				"route": ["procurement-plan-item", item.plan_item_id],
			}
		)
	return rows


def get_annual_plan(*, plan_reference: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	plan = _plan_root(plan_reference)
	authz.require_site_read(PLAN_READERS, actor)
	can_act = authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	version = _open_version(plan)

	all_accepted = _accepted_entry_rows(plan.fiscal_year)
	allocated_ids = _allocated_dpp_entries(version.name)
	unallocated = [row for row in all_accepted if row["dpp_entry"] not in allocated_ids]
	items = _item_rows(version.name)
	item_value = sum(flt(a.indicative_amount) for a in frappe.get_all("Plan Source Allocation", filters={"plan_version": version.name, "allocation_state": ("in", ("Draft", "Active"))}, fields=["indicative_amount"]))
	readiness_report = plan_readiness(version, plan) if version.version_status == "Draft" else None
	mutable = version.version_status == "Draft" and can_act and version.funding_state != "Awaiting Finance"
	no_blockers = bool(readiness_report) and not readiness_report["blockers"]
	share = readiness_report["reserved_share"] if readiness_report else readiness.reserved_share(version.name)
	target = readiness_report["reservation_target"] if readiness_report else None
	return {
		"outcome": "OK",
		"plan_reference": plan.plan_reference,
		"version_reference": version.name,
		"version_status": version.version_status,
		"funding_state": version.funding_state,
		"record_version": int(version.record_version or 0),
		"fiscal_year": plan.fiscal_year,
		"header": {
			"eyebrow": "ANNUAL PROCUREMENT PLAN",
			"title": plan.title,
			"reference_line": f"{plan.plan_reference} · Version {version.version_number}",
			"badge": version.version_status,
		},
		"mutable": mutable,
		"can_act": can_act,
		"is_correction": bool(version.correction_of_plan_version),
		"is_successor": bool(version.based_on_version),
		"has_open_successor": bool(plan.open_successor_version),
		"summary": {
			"accepted_entries": len(all_accepted),
			"allocated": len(all_accepted) - len(unallocated),
			"plan_items": len(items),
			"value_display": _money(item_value),
			"reserved_share_display": f"{share['percent']:.0f}% of plan value · target {target:.0f}%" if target else f"{share['percent']:.0f}% of plan value",
		},
		"unallocated_sources": unallocated,
		"unallocated_caption": f"{len(unallocated)} entr{'y' if len(unallocated) == 1 else 'ies'} available" if unallocated else "",
		"plan_items": items,
		"readiness": readiness_report["checks"] if readiness_report else [],
		"blockers": readiness_report["blockers"] if readiness_report else [],
		"splitting_advisories": readiness_report["advisories"] if readiness_report else [],
		"splitting_confirmation": cstr(version.splitting_confirmation),
		"can_request_funding": mutable and no_blockers and not unallocated and version.funding_state in ("Not requested", "Returned", "Stale"),
		"can_submit": mutable and no_blockers and not unallocated and bool(readiness_report and readiness_report["funding_current"]),
		"late_activation_required": bool(frappe.db.get_value("Fiscal Year", plan.fiscal_year, "year_start_date") and frappe.utils.getdate(frappe.utils.nowdate()) >= frappe.utils.getdate(frappe.db.get_value("Fiscal Year", plan.fiscal_year, "year_start_date"))),
		"latest_publication": _latest_publication(version.name),
		"active_view": _active_view(version, plan) if version.version_status == "Active" else None,
	}


def _decision_line(version_name: str, stage: str) -> str:
	task = frappe.db.get_value("Plan Governance Task", {"plan_version": version_name, "stage": stage}, "decision")
	if not task:
		return ""
	row = frappe.db.get_value("Plan Governance Decision", task, ["actor", "capacity", "decided_at"], as_dict=True)
	if not row:
		return ""
	who = cstr(frappe.db.get_value("User", row.actor, "full_name") or row.actor)
	label = row.capacity if stage == "Statutory approval" else who
	return f"{label} · {_eat(row.decided_at)}"


def _active_view(version, plan) -> dict[str, Any]:
	"""PLN-UI-14 — the Active Plan (PLN-DES-14): items with their
	Requisition-availability projection, the schedule card and the
	governance card."""
	from kentender_procurement.procurement_planning.services import strategy_gateway

	objectives = {row["id"]: row["title"] for row in strategy_gateway.list_eligible_strategic_objectives()}
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version.name, "item_state": "Active"},
		fields=["name", "plan_item_id", "title", "requirement_type", "procurement_method", "strategic_objective", "baseline_delivery_completion_date", "record_version", *schedule.BASELINE_FIELDS, *schedule.FORECAST_FIELDS, *schedule.ACTUAL_FIELDS],
		order_by="creation asc",
	)
	rows = []
	departments = set()
	for item in items:
		allocations = frappe.get_all(
			"Plan Source Allocation", filters={"plan_item": item.name, "allocation_state": "Active"},
			fields=["name", "organisation_unit", "source_origin", "quantity", "unit", "indicative_amount"],
		)
		drawn = _drawn(allocations)
		departments |= {a.organisation_unit for a in allocations}
		origins = {a.source_origin for a in allocations}
		total_qty = sum(flt(a.quantity) for a in allocations)
		unit_label = _unit_label(allocations[0].unit) if allocations else ""
		value = sum(flt(a.indicative_amount) for a in allocations)
		rows.append(
			{
				"plan_item_id": item.plan_item_id,
				"title": item.title,
				"department": " / ".join(sorted({_ou_label(ou) for ou in {a.organisation_unit for a in allocations}})),
				"source_origin": next(iter(origins)) if len(origins) == 1 else "Multiple",
				"strategic_objective_label": objectives.get(cstr(item.strategic_objective)) or cstr(frappe.db.get_value("Strategy Node", item.strategic_objective, "title") or ""),
				"procurement_method": cstr(item.procurement_method),
				"completion_display": _date(item.baseline_delivery_completion_date),
				"value_display": _money(value),
				"requisition_availability_display": f"{total_qty - drawn[0]:g} {unit_label.lower()} · {_money(value - drawn[1])}".strip(),
				"behind_baseline": schedule.behind_baseline(item),
				"schedule": schedule.schedule_rows(item),
				"record_version": int(item.record_version or 0),
				"route": ["procurement-plan-item", item.plan_item_id],
			}
		)
	item_value = sum(flt(a.indicative_amount) for a in frappe.get_all("Plan Source Allocation", filters={"plan_version": version.name, "allocation_state": "Active"}, fields=["indicative_amount"]))
	health = schedule.schedule_health(version.name)
	publication = frappe.db.get_value(
		"Annual Plan Publication", {"plan_version": version.name, "result": "Acknowledged"}, ["name", "acknowledged_at", "external_reference"], as_dict=True, order_by="attempt_number desc",
	)
	return {
		"summary": {
			"plan_items": len(rows),
			"value_display": _money(item_value),
			"departments": len(departments),
			"schedule_health_display": f"{health['behind']} of {health['total']} item{'s' if health['total'] != 1 else ''} behind baseline",
			"activated_display": _eat(version.activated_at),
		},
		"items": rows,
		"governance_card": {
			"ao_adoption_line": _decision_line(version.name, "Accounting Officer adoption"),
			"statutory_approval_line": _decision_line(version.name, "Statutory approval"),
			"publication_line": f"Acknowledged · {_eat(publication.acknowledged_at)}" if publication else "",
			"publication": publication.name if publication else "",
			"publication_route": [PAGE, "publication", publication.name] if publication else None,
		},
	}


def _latest_publication(version_name: str) -> dict[str, Any] | None:
	row = frappe.db.get_value(
		"Annual Plan Publication", {"plan_version": version_name}, ["name", "result", "attempt_number"], as_dict=True, order_by="attempt_number desc",
	)
	if not row:
		return None
	return {"publication": row.name, "result": row.result, "attempt_number": row.attempt_number, "route": [PAGE, "publication", row.name]}


def _drawn(allocations: list) -> tuple[float, float]:
	names = [a.name for a in allocations]
	if not names:
		return 0.0, 0.0
	rows = frappe.get_all("Plan Drawdown Reference", filters={"allocation": ("in", names), "drawdown_state": "Active"}, fields=["quantity", "amount"])
	return sum(flt(r.quantity) for r in rows), sum(flt(r.amount) for r in rows)


# --------------------------------------------------------------------------
# GetPlanItem (PLN-DES-09 / 09A)
# --------------------------------------------------------------------------


def get_plan_item(*, plan_item_id: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import strategy_gateway

	actor = authz.actor(user)
	name = resolve_item_doc_name(plan_item_id)
	item = frappe.get_doc("Annual Plan Item", name)
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	authz.require_site_read(PLAN_READERS, actor)
	can_act = authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	reference = readiness.reference_for(plan.fiscal_year)
	labels = _line_labels(plan.fiscal_year)

	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
		fields=["name", "dpp_entry", "source_origin", "need", "need_version", "organisation_unit", "quantity", "unit", "required_by_date", "budget_line", "indicative_amount"],
		order_by="creation asc",
	)
	sources, value, correction_required = [], 0.0, False
	for allocation in allocations:
		value += flt(allocation.indicative_amount)
		if source_correction_required(allocation.dpp_entry):
			correction_required = True
		entry_title = cstr(frappe.db.get_value("Departmental Plan Entry", allocation.dpp_entry, "title"))
		dpp_version = frappe.db.get_value("Departmental Plan Entry", allocation.dpp_entry, "dpp_version")
		dpp_root = frappe.db.get_value("Departmental Plan Version", dpp_version, "departmental_plan")
		dpp_reference = cstr(frappe.db.get_value("Departmental Plan", dpp_root, "dpp_reference"))
		dpp_version_number = frappe.db.get_value("Departmental Plan Version", dpp_version, "version_number")
		line = labels.get(cstr(allocation.budget_line), {})
		sources.append(
			{
				"requirement": entry_title,
				"department": _ou_label(allocation.organisation_unit),
				"source_origin": allocation.source_origin,
				"departmental_plan_line": f"{dpp_reference} · Version {dpp_version_number}",
				"need_reference_line": f"{allocation.need} · Version {needs_intake.need_version_number(allocation.need_version)}" if allocation.need else "",
				"quantity_display": _quantity_display(allocation.quantity, allocation.unit),
				"required_by_display": _date(allocation.required_by_date),
				"budget_line": allocation.budget_line,
				"budget_line_display": line.get("label") or cstr(allocation.budget_line),
				"amount_display": _money(allocation.indicative_amount),
			}
		)

	objectives = strategy_gateway.list_eligible_strategic_objectives()
	objective_eligible = (not item.strategic_objective) or any(row["id"] == item.strategic_objective for row in objectives)
	band = readiness.resolve_band(reference, cstr(item.procurement_category) or "Services", value)
	categories = readiness.reservation_categories(reference)
	is_county = bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county"))
	blockers = readiness.item_blockers(item, allocations, reference, objective_eligible=objective_eligible) if version.version_status == "Draft" else []
	price_index = reference.get("market_price_index", {})
	price_rows = [r for r in price_index.get("rows", []) if r.get("procurement_category") == cstr(item.procurement_category)] if price_index.get("published") else []
	periods = {f: int(item.get(f) or 0) for f in schedule.PERIOD_FIELDS}
	defaults = schedule.default_periods(reference, cstr(item.procurement_category) or "Services", cstr(item.procurement_method) or readiness.OPEN_TENDER)
	combined = len(sources) > 1
	mutable = item.item_state == "Draft" and version.version_status == "Draft" and can_act and version.funding_state != "Awaiting Finance"
	return {
		"outcome": "OK",
		"plan_item_id": item.plan_item_id,
		"record_version": int(item.record_version or 0),
		"mutable": mutable,
		"can_act": can_act,
		"combined": combined,
		"is_active": version.version_status == "Active" and item.item_state == "Active",
		"source_correction_required": correction_required,
		"header": {
			"eyebrow": "PLAN ITEM",
			"title": item.title,
			"reference_line": f"{item.plan_item_id} · {version.version_status} Version {version.version_number}",
			"item_state_badge": {"Draft": "Proposed"}.get(item.item_state, item.item_state),
		},
		"plan_reference": plan.plan_reference,
		"sources": sources,
		"sources_caption": f"{len(sources)} sources · {sum(flt(a.quantity) for a in allocations):g} {_unit_label(allocations[0].unit).lower()} · {_money(value)}" if combined else "",
		"planned_value_display": _money(value),
		"identity": {
			"title": item.title,
			"description": item.description,
			"requirement_type": item.requirement_type,
			"procurement_category": cstr(item.procurement_category),
			"aggregation_reason": cstr(item.aggregation_reason),
		},
		"classification": {
			"strategic_objective": cstr(item.strategic_objective),
			"objective_path": cstr(item.objective_path),
			"objective_eligible": objective_eligible,
			"strategic_objectives": objectives,
			"procurement_method": cstr(item.procurement_method),
			"admissible_methods": band["admissible_methods"],
			"proposed_method": band["proposed_method"],
			"value_band": band["band_label"] or ("Threshold matrix not configured for this financial year" if not band["available"] else ""),
			"reference_available": band["available"],
		},
		"preference": {
			"reservation_category": cstr(item.reservation_category),
			"reservation_category_reason": cstr(item.reservation_category_reason),
			"reservation_categories": [c["category"] for c in categories],
			"highest_advantage": readiness.highest_advantage(reference),
			"county_resident_reservation": bool(item.county_resident_reservation),
			"county_control_available": is_county,
			"exclusive_preference": bool(item.exclusive_preference),
			"plan_horizon": cstr(item.plan_horizon),
			"multi_year_justification": cstr(item.multi_year_justification),
			"aggregation_indicator": cstr(item.aggregation_indicator),
			"lotting_indicator": cstr(item.lotting_indicator),
			"lot_count": int(item.lot_count or 0),
			"helper": "Recorded for the entity's 30% target. Choose None only where no reservation applies.",
		},
		"baseline": {
			"target_invitation_date": cstr(item.baseline_invitation_date),
			"periods": periods,
			"defaults": defaults,
			"using_defaults": all(periods[f] == defaults[f] for f in schedule.PERIOD_FIELDS),
			"defaults_line": f"Using governed defaults for {cstr(item.procurement_category) or 'Services'} · {cstr(item.procurement_method) or readiness.OPEN_TENDER}",
			"floors": {"tendering_period_days": schedule.TENDERING_FLOOR, "standstill_period_days": schedule.STANDSTILL_FLOOR},
			"ceilings": {"evaluation_period_days": schedule.EVALUATION_CEILING},
			"rows": [
				{"milestone": m, "label": schedule.MILESTONE_LABELS[m], "date": cstr(item.get(f"baseline_{m}_date")), "date_display": _date(item.get(f"baseline_{m}_date")), "from_requisition": m == "delivery_completion"}
				for m in schedule.MILESTONES
			],
			"delivery_boundary_ok": schedule.delivery_boundary_ok({f: item.get(f) for f in schedule.BASELINE_FIELDS}),
			"locked": version.version_status != "Draft",
		},
		"schedule": schedule.schedule_rows(item) if version.version_status == "Active" else [],
		"revisions": [
			{"milestone": r.milestone, "label": schedule.MILESTONE_LABELS.get(r.milestone, r.milestone), "previous": cstr(r.previous_forecast_date), "new": cstr(r.new_forecast_date), "reason": r.reason, "cascade_id": cstr(r.cascade_id), "revised_by": r.revised_by, "revised_at": _eat(r.revised_at)}
			for r in frappe.get_all("Plan Item Forecast Revision", filters={"plan_item": item.name}, fields=["milestone", "previous_forecast_date", "new_forecast_date", "reason", "cascade_id", "revised_by", "revised_at"], order_by="revised_at asc, creation asc")
		],
		"market_price_index": {"published": bool(price_rows), "rows": price_rows, "helper": "Market price index: not published for this category." if not price_rows else ""},
		"blockers": blockers,
	}


# --------------------------------------------------------------------------
# GetFinanceTask (PLN-DES-10)
# --------------------------------------------------------------------------


def get_finance_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance

	actor = authz.actor(user)
	if not task or not frappe.db.exists("Plan Finance Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Plan Finance Task", task)
	authz.require_site_read((ROLE_FINANCE_CONFIRMATION_OFFICER, ROLE_PROCUREMENT_PLANNER, ROLE_ACCOUNTING_OFFICER, ROLE_AUDITOR), actor)
	version = frappe.get_doc("Annual Plan Version", task_doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	decided = task_doc.status != "Open"
	statement = json.loads(task_doc.affordability_statement or "{}") if decided else plan_finance.affordability_statement(plan, version)
	if decided and task_doc.decision:
		decision_statement = frappe.db.get_value("Plan Finance Decision", task_doc.decision, "affordability_statement")
		if decision_statement:
			statement = json.loads(decision_statement)
	totals = readiness.line_totals(version.name)
	used = [line for line in statement.get("lines", []) if flt(line.get("planned")) > 0]
	items = frappe.db.count("Annual Plan Item", {"plan_version": version.name, "item_state": ("!=", "Dissolved")})
	share = readiness.reserved_share(version.name)
	target = readiness.reference_for(plan.fiscal_year).get("reservation", {}).get("target_percent")
	rows = [
		{
			"budget_line": line["budget_line"],
			"budget_line_label": f"{line.get('reference') or line['budget_line']} — {line.get('title')}" if line.get("title") else (line.get("reference") or line["budget_line"]),
			"funding_source": cstr(line.get("funding_source")) or "—",
			"approved_display": _money(line.get("approved")),
			"planned_display": _money(line.get("planned")),
			"within_approved": bool(line.get("within_approved")),
			"within_approved_display": "Yes" if line.get("within_approved") else "No",
			"reserved_display": _money(line.get("reserved")),
			"committed_display": _money(line.get("committed")),
			"available_display": _money(line.get("available")),
			"within_available": bool(line.get("within_available")),
			"excess_display": _money(line.get("excess_over_approved")) if not line.get("within_approved") else "",
		}
		for line in statement.get("lines", [])
	]
	within_approved = bool(statement.get("within_approved"))
	within_available = bool(statement.get("within_available"))
	can_decide = authz.has_site_role(ROLE_FINANCE_CONFIRMATION_OFFICER, actor) and not decided and not authz.is_segregated(actor, authz.ACTION_FINANCE_DECIDE, plan_version=version.name)
	return {
		"outcome": "OK",
		"task": task_doc.name,
		"task_reference": task_doc.task_reference,
		"task_token": task_doc.task_token,
		"status": task_doc.status,
		"decided": decided,
		"can_decide": can_decide,
		"can_confirm": can_decide and within_approved,
		"header": {
			"eyebrow": "PLAN FUNDING CONFIRMATION",
			"title": plan.title,
			"reference_line": f"{task_doc.task_reference} · {plan.plan_reference} · Version {version.version_number}",
			"badge": "Awaiting Finance" if task_doc.status == "Open" else task_doc.status,
		},
		"summary": {
			"plan_items": items,
			"value_display": _money(sum(totals.values())),
			"lines_used": len(used),
			"reserved_share_display": f"{share['percent']:.0f}% of plan value · target {target:.0f}%" if target else f"{share['percent']:.0f}% of plan value",
		},
		"as_at_display": _eat(statement.get("as_at")),
		"lines": rows,
		"within_approved": within_approved,
		"within_available": within_available,
		"notice": (
			{"kind": "live", "text": "The consolidated plan is within the approved budget on every Procurement Budget Line."}
			if within_approved
			else {"kind": "critical", "text": "The planned total exceeds the approved amount on one or more Procurement Budget Lines. Return the plan to the Planner."}
		),
		"advisory": None if within_available else {"kind": "advisory", "text": "The planned total exceeds the currently available amount on at least one line. Planning and drawdown run on different horizons; this blocks nothing."},
		"quiet_line": "Confirmation records that this plan fits the approved budget. It reserves no funds; reservation happens at requisition.",
		"failing_lines": statement.get("failing_lines", []),
	}


# --------------------------------------------------------------------------
# GetPlanGovernanceTask (PLN-DES-11/12)
# --------------------------------------------------------------------------


def get_plan_governance_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	actor = authz.actor(user)
	if not task or not frappe.db.exists("Plan Governance Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Plan Governance Task", task)
	role = ROLE_ACCOUNTING_OFFICER if task_doc.stage == "Accounting Officer adoption" else ROLE_PLAN_STATUTORY_APPROVER
	authz.require_site_read((role, ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR), actor)
	version = frappe.get_doc("Annual Plan Version", task_doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	snapshot = json.loads(version.submitted_snapshot) if version.submitted_snapshot else {}
	rows = snapshot.get("rows", snapshot if isinstance(snapshot, list) else [])
	total_value = sum(flt(row.get("value")) for row in rows)
	authority_card = None
	if task_doc.stage == "Statutory approval":
		ao_decision = frappe.db.get_value("Plan Governance Task", {"plan_version": version.name, "stage": "Accounting Officer adoption"}, "decision")
		ao_actor, ao_decided_at = "", ""
		if ao_decision:
			row = frappe.db.get_value("Plan Governance Decision", ao_decision, ["actor", "decided_at"], as_dict=True)
			ao_actor = cstr(frappe.db.get_value("User", row.actor, "full_name") or row.actor) if row else ""
			ao_decided_at = _eat(row.decided_at) if row else ""
		is_board = plan_governance.is_board_capacity(task_doc.capacity)
		authority_card = {
			"capacity": "Governing body" if is_board else task_doc.capacity,
			"capacity_detail": task_doc.capacity,
			"is_board": is_board,
			"ao_adoption_line": f"{ao_actor} · {ao_decided_at}" if ao_actor else "",
		}
	target = snapshot.get("reservation_target_percent")
	share = snapshot.get("reserved_share_percent", 0)
	advisory_line = (
		f"Reserved share {share:.0f}% of plan value · target {target:.0f}%. " if target else f"Reserved share {share:.0f}% of plan value. "
	) + ("No contract splitting advisory." if not snapshot.get("splitting_advisory_count") else f"{snapshot['splitting_advisory_count']} contract splitting advisory confirmed by the Planner.")
	action = authz.ACTION_AO_DECIDE if task_doc.stage == "Accounting Officer adoption" else authz.ACTION_STATUTORY_DECIDE
	can_decide = task_doc.status == "Open" and authz.has_site_role(role, actor) and not authz.is_segregated(actor, action, plan_version=version.name)
	return {
		"outcome": "OK",
		"task": task_doc.name,
		"task_reference": task_doc.task_reference,
		"task_token": task_doc.task_token,
		"status": task_doc.status,
		"stage": task_doc.stage,
		"can_decide": can_decide,
		"header": {
			"eyebrow": f"{task_doc.stage.upper()} · {plan.plan_reference} · VERSION {version.version_number}",
			"title": plan.title,
			"badge": version.version_status,
		},
		"authority_card": authority_card,
		"decision_statement": (
			f"I adopt the complete consolidated Annual Procurement Plan Version {version.version_number} shown above and submit it for the statutory approval applicable to this Procuring Entity."
			if task_doc.stage == "Accounting Officer adoption" else ""
		),
		"items": rows,
		"caption": f"{len(rows)} Plan Item{'s' if len(rows) != 1 else ''} · {_money(total_value)}",
		"advisory_line": advisory_line,
		"late_activation_reason": cstr(version.late_activation_reason),
		"confirm_label": "Adopt and submit" if task_doc.stage == "Accounting Officer adoption" else "Approve Annual Procurement Plan",
		"return_dialog": (
			{"title": "Return Plan Version for correction?", "lede": f"The submitted Version {version.version_number} remains unchanged. State the correction required."}
			if task_doc.stage == "Accounting Officer adoption"
			else {"title": "Return adopted Plan Version for correction?", "lede": f"The Accounting-Officer-adopted Version {version.version_number} remains unchanged. State the correction required."}
		),
	}


# --------------------------------------------------------------------------
# GetPublicationTask (PLN-DES-13)
# --------------------------------------------------------------------------


def get_publication_task(*, publication: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if not publication or not frappe.db.exists("Annual Plan Publication", publication):
		authz.not_found()
	doc = frappe.get_doc("Annual Plan Publication", publication)
	authz.require_site_read(PLAN_READERS, actor)
	version = frappe.get_doc("Annual Plan Version", doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	destination = frappe.db.get_value("Annual Plan Publication Destination", doc.destination, ["destination_id", "title"], as_dict=True) or {}
	from kentender_core.services.authorization import is_technical

	items = frappe.db.count("Annual Plan Item", {"plan_version": version.name, "item_state": ("in", ("Active", "Draft", "Superseded"))})
	value = sum(flt(a.indicative_amount) for a in frappe.get_all("Plan Source Allocation", filters={"plan_version": version.name, "allocation_state": ("in", ("Draft", "Active", "Superseded"))}, fields=["indicative_amount"]))
	badge, badge_kind = {"Acknowledged": ("Acknowledged", "live"), "Failed": ("Publication failed", "critical")}.get(doc.result, ("Publication pending", "attention"))
	return {
		"outcome": "OK",
		"publication": doc.name,
		"publication_reference": doc.publication_reference,
		"header": {"eyebrow": "ANNUAL PLAN PUBLICATION", "title": "Publication result", "reference_line": f"{plan.plan_reference} · Version {version.version_number}", "badge": badge, "badge_kind": badge_kind},
		"plan_reference": plan.plan_reference,
		"plan_title": plan.title,
		"approved_plan": {
			"financial_year": references.fy_label(plan.fiscal_year),
			"plan_items": items,
			"value_display": _money(value),
			"statutory_approval_line": _decision_line(version.name, "Statutory approval"),
		},
		"configuration": destination.get("destination_id", ""),
		"result_display": {"Acknowledged": "Acknowledged", "Failed": "Not acknowledged"}.get(doc.result, "Awaiting acknowledgement"),
		"acknowledgement_reference": cstr(doc.external_reference) or "Not received",
		"quiet_notice": "Publication is an automatic system action after statutory approval. It runs without a business-role control.",
		"version": {"reference": version.version_reference, "status": version.version_status, "number": version.version_number},
		"destination": {"id": destination.get("destination_id", ""), "title": destination.get("title", "")},
		"attempt_number": doc.attempt_number,
		"result": doc.result,
		"external_reference": cstr(doc.external_reference),
		"attempted_display": _eat(doc.attempted_at),
		"acknowledged_display": _eat(doc.acknowledged_at),
		"legal_character": cstr(doc.legal_character),
		"payload_hash": doc.payload_hash,
		"can_retry": is_technical(actor) and version.version_status == "Publication failed",
	}
