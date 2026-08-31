# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §8.1 — Annual Plan workbench and Plan Item reads.

`GetPlanVersion` (PLN-UI-07/08, PLN-DES-07) serves the Draft workbench: the
summary strip, the unallocated accepted-source pool (§8.1 ListAcceptedDPPSources
joined through the immutable validation decision for classification — never a
classification field invented on DPPEntry/PlanSourceAllocation) and the
current Plan Items. `GetPlanItem` (PLN-UI-09, PLN-DES-09/09A) serves one
item's read-only source rows, its editable procurement-package fields and its
planned schedule.

§4.9's **Source correction required** is derived here, never stored: an
allocation's `dpp_entry` document is pinned to the DPP Version it was formed
from, and a later DPP successor's acceptance creates a *new* Departmental
Plan Entry document for the same stable `entry_id` (dpp_lifecycle.copy_entries).
An allocation whose pinned entry document is no longer the root's
`current_accepted_version`'s entry for that `entry_id` has fallen behind its
source (§12.7)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, fmt_money, formatdate

from kentender_procurement.procurement_planning.services import authority
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_BUDGET_OFFICER,
	ROLE_PLANNING_AUDITOR,
	ROLE_PROCUREMENT_PLANNER,
)


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
	return cstr(frappe.db.get_value("Unit Of Measure", unit, "unit_label") or unit)


def _quantity_display(quantity, unit: str) -> str:
	value = flt(quantity)
	shown = f"{value:g}"
	return f"{shown} {_unit_label(unit).lower()}".strip()


def _authorise_planner(actor: str, procuring_entity: str) -> None:
	"""§6 — Planner or Planning Auditor, PE-scoped; the workbench and every
	Plan Item are PE-wide (unlike DPP validation tasks, never OU-narrowed)."""
	authority.require_scope(
		actor, roles=(ROLE_PROCUREMENT_PLANNER, ROLE_PLANNING_AUDITOR),
		procuring_entity=procuring_entity,
	)


def _plan_root(plan_reference: str):
	name = frappe.db.get_value("Annual Plan", {"plan_reference": cstr(plan_reference)})
	if not name:
		authority.not_found()
	return frappe.get_doc("Annual Plan", name)


def _open_version(plan):
	"""The Version the workbench shows: the open successor while one exists
	(Draft through governance), else the sole Active Version (§5.2)."""
	name = cstr(plan.open_successor_version) or cstr(plan.active_version)
	if not name:
		authority.not_found()
	return frappe.get_doc("Annual Plan Version", name)


def _classifications(dpp_version: str) -> dict[str, str]:
	"""§8.1 — join each accepted entry through its immutable acceptance
	decision to obtain the classification; no field on DPPEntry carries it."""
	decision_name = frappe.db.get_value(
		"Departmental Plan Validation Decision",
		{"submission": frappe.db.get_value(
			"Departmental Plan Submission", {"dpp_version": dpp_version}, "name"
		), "decision": "Accept departmental plan"},
		"classifications",
	)
	return json.loads(decision_name) if decision_name else {}


def _accepted_entry_rows(pe_fy_context: str) -> list[dict[str, Any]]:
	"""§8.1 ListAcceptedDPPSources — every current accepted entry in this
	PE/FY, its classification and its current allocation (if any)."""
	accepted = frappe.get_all(
		"Departmental Plan",
		filters={"pe_fy_context": pe_fy_context, "current_accepted_version": ("!=", "")},
		fields=["name", "organisation_unit", "current_accepted_version"],
	)
	rows: list[dict[str, Any]] = []
	for root in accepted:
		version = root.current_accepted_version
		classifications = _classifications(version)
		entries = frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": version},
			fields=[
				"name", "entry_id", "title", "source_origin", "quantity", "unit",
				"required_by_date", "budget_line", "indicative_amount",
			],
		)
		ou_label = cstr(
			frappe.db.get_value("Organisation Unit", root.organisation_unit, "unit_name")
			or root.organisation_unit
		)
		for entry in entries:
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
					"indicative_amount": flt(entry.indicative_amount),
					"amount_display": _money(entry.indicative_amount),
				}
			)
	return rows


def _allocated_dpp_entries(plan_version: str) -> set[str]:
	return set(
		frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_version": plan_version, "allocation_state": ("in", ("Draft", "Active"))},
			pluck="dpp_entry",
		)
	)


def source_correction_required(dpp_entry: str) -> bool:
	entry = frappe.db.get_value(
		"Departmental Plan Entry", dpp_entry, ["entry_id", "dpp_version"], as_dict=True
	)
	if not entry:
		return True
	root_name = frappe.db.get_value("Departmental Plan Version", entry.dpp_version, "departmental_plan")
	current_accepted = frappe.db.get_value("Departmental Plan", root_name, "current_accepted_version")
	if not current_accepted or current_accepted == entry.dpp_version:
		return False
	current_entry = frappe.db.get_value(
		"Departmental Plan Entry", {"dpp_version": current_accepted, "entry_id": entry.entry_id}, "name"
	)
	return current_entry != dpp_entry


def _item_rows(plan_version: str) -> list[dict[str, Any]]:
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": plan_version, "item_state": ("!=", "Dissolved")},
		fields=["name", "plan_item_id", "title", "item_state", "finance_state", "requirement_type"],
		order_by="creation asc",
	)
	rows = []
	for item in items:
		allocations = frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
			fields=["dpp_entry", "indicative_amount"],
		)
		value = sum(flt(a.indicative_amount) for a in allocations)
		correction_required = any(source_correction_required(a.dpp_entry) for a in allocations)
		rows.append(
			{
				"plan_item_id": item.plan_item_id,
				"title": item.title,
				"item_state": item.item_state,
				"finance_state": item.finance_state,
				"requirement_type": item.requirement_type,
				"sources": len(allocations),
				"value_display": _money(value),
				"source_correction_required": correction_required,
				"route": ["procurement-plan-item", item.plan_item_id],
			}
		)
	return rows


def get_annual_plan(*, plan_reference: str, user: str | None = None) -> dict[str, Any]:
	"""PLN-UI-07/08 — the Draft Annual Plan workbench (PLN-DES-07)."""
	actor = cstr(user or frappe.session.user)
	plan = _plan_root(plan_reference)
	_authorise_planner(actor, plan.procuring_entity)
	version = _open_version(plan)

	all_accepted = _accepted_entry_rows(plan.pe_fy_context)
	allocated_ids = _allocated_dpp_entries(version.name)
	unallocated = [row for row in all_accepted if row["dpp_entry"] not in allocated_ids]
	items = _item_rows(version.name)
	item_value = sum(
		flt(a.indicative_amount)
		for a in frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_version": version.name, "allocation_state": ("in", ("Draft", "Active"))},
			fields=["indicative_amount"],
		)
	)
	pe_label = cstr(
		frappe.db.get_value("Procuring Entity", plan.procuring_entity, "legal_name") or plan.procuring_entity
	)
	fy_label = cstr(
		frappe.db.get_value("Financial Year", plan.financial_year, "label") or plan.financial_year
	)
	if fy_label and not fy_label.upper().startswith("FY"):
		fy_label = f"FY {fy_label}"
	ready_for_submission = bool(items) and not unallocated and all(
		row["finance_state"] == "Confirmed" and not row["source_correction_required"] for row in items
	)
	return {
		"outcome": "OK",
		"plan_reference": plan.plan_reference,
		"version_reference": version.name,
		"record_version": int(version.record_version or 0),
		"header": {
			"eyebrow": "ANNUAL PROCUREMENT PLAN",
			"title": plan.title or f"{pe_label} Annual Procurement Plan",
			"reference_line": f"{plan.plan_reference} · Version {version.version_number}",
			"badge": version.version_status,
		},
		"mutable": version.version_status == "Draft",
		"is_correction": bool(version.correction_of_plan_version),
		"summary": {
			"accepted_entries": len(all_accepted),
			"allocated": len(all_accepted) - len(unallocated),
			"plan_items": len(items),
			"value_display": _money(item_value),
		},
		"unallocated_sources": unallocated,
		"unallocated_caption": (
			f"{len(unallocated)} entr{'y' if len(unallocated) == 1 else 'ies'} available"
			if unallocated else ""
		),
		"plan_items": items,
		"ready_for_submission": ready_for_submission,
	}


def get_plan_item(*, plan_item_id: str, user: str | None = None) -> dict[str, Any]:
	"""PLN-UI-09 — the Plan Item editor, single-source (PLN-DES-09) or
	combined (PLN-DES-09A) by the same read model and screen."""
	actor = cstr(user or frappe.session.user)
	name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": cstr(plan_item_id)})
	if not name:
		authority.not_found()
	item = frappe.get_doc("Annual Plan Item", name)
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise_planner(actor, plan.procuring_entity)

	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
		fields=[
			"dpp_entry", "source_origin", "need", "need_version", "organisation_unit",
			"quantity", "unit", "required_by_date", "budget_line", "indicative_amount",
		],
		order_by="creation asc",
	)
	sources = []
	value = 0.0
	correction_required = False
	for allocation in allocations:
		value += flt(allocation.indicative_amount)
		if source_correction_required(allocation.dpp_entry):
			correction_required = True
		entry_title = cstr(frappe.db.get_value("Departmental Plan Entry", allocation.dpp_entry, "title"))
		dpp_version = frappe.db.get_value("Departmental Plan Entry", allocation.dpp_entry, "dpp_version")
		dpp_root = frappe.db.get_value("Departmental Plan Version", dpp_version, "departmental_plan")
		dpp_reference = cstr(frappe.db.get_value("Departmental Plan", dpp_root, "dpp_reference"))
		dpp_version_number = frappe.db.get_value("Departmental Plan Version", dpp_version, "version_number")
		ou_label = cstr(
			frappe.db.get_value("Organisation Unit", allocation.organisation_unit, "unit_name")
			or allocation.organisation_unit
		)
		need_reference_line = ""
		if allocation.need:
			need_version_number = frappe.db.get_value(
				"Departmental Need Version", allocation.need_version, "version_number"
			)
			need_reference_line = f"{allocation.need} · Version {need_version_number}"
		sources.append(
			{
				"requirement": entry_title,
				"department": ou_label,
				"source_origin": allocation.source_origin,
				"departmental_plan_line": f"{dpp_reference} · Version {dpp_version_number}",
				"need_reference_line": need_reference_line,
				"quantity_display": _quantity_display(allocation.quantity, allocation.unit),
				"required_by_display": _date(allocation.required_by_date),
				"budget_line": allocation.budget_line,
				"amount_display": _money(allocation.indicative_amount),
			}
		)

	from kentender_procurement.procurement_planning.services import strategy_gateway

	objectives = strategy_gateway.list_eligible_strategic_objectives(procuring_entity=plan.procuring_entity)
	# an already-selected Objective remains shown even if it later becomes
	# ineligible (§7.2 "An already Active Plan preserves its approved lineage");
	# the editor still flags it via `objective_eligible`.
	objective_eligible = (not item.strategic_objective) or any(
		row["id"] == item.strategic_objective for row in objectives
	)

	combined = len(sources) > 1
	return {
		"outcome": "OK",
		"plan_item_id": item.plan_item_id,
		"record_version": int(item.record_version or 0),
		"mutable": item.item_state == "Draft" and version.version_status == "Draft",
		"combined": combined,
		"source_correction_required": correction_required,
		"header": {
			"eyebrow": "PLAN ITEM",
			"title": item.title,
			"reference_line": f"{item.plan_item_id} · {version.version_status} Version {version.version_number}",
			"item_state_badge": {"Draft": "Proposed"}.get(item.item_state, item.item_state),
			"finance_state_badge": item.finance_state,
		},
		"plan_reference": plan.plan_reference,
		"sources": sources,
		"sources_caption": (
			f"{len(sources)} sources · "
			f"{sum(flt(a.quantity) for a in allocations):g} {_unit_label(allocations[0].unit).lower()} · "
			f"{_money(value)}"
			if combined else ""
		),
		"item": {
			"title": item.title,
			"description": item.description,
			"requirement_type": item.requirement_type,
			"strategic_objective": item.strategic_objective,
			"objective_path": item.objective_path,
			"procurement_method": item.procurement_method,
			"aggregation_reason": item.aggregation_reason,
		},
		"objective_eligible": objective_eligible,
		"strategic_objectives": objectives,
		"schedule": {
			"invitation_date": cstr(item.invitation_date),
			"bid_opening_date": cstr(item.bid_opening_date),
			"evaluation_completion_date": cstr(item.evaluation_completion_date),
			"award_approval_date": cstr(item.award_approval_date),
			"award_notification_date": cstr(item.award_notification_date),
			"contract_signing_date": cstr(item.contract_signing_date),
			"delivery_completion_date": cstr(item.delivery_completion_date),
		},
	}


def get_finance_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	"""PLN-UI-10 — the Finance confirmation task (PLN-DES-10). Reloads every
	Budget Line position live (§12.9: "the displayed As-at time must match
	the snapshot") via the two published Budget reads; `check_funding` is
	itself non-mutating (§9.1) and mints the short-lived check token the
	Confirm command consumes."""
	from kentender_procurement.procurement_planning.services import budget_gateway

	actor = cstr(user or frappe.session.user)
	if not task or not frappe.db.exists("Plan Finance Task", task):
		authority.not_found()
	task_doc = frappe.get_doc("Plan Finance Task", task)
	authority.require_scope(
		actor, roles=(ROLE_BUDGET_OFFICER,), procuring_entity=task_doc.procuring_entity,
	)
	item = frappe.get_doc("Annual Plan Item", task_doc.plan_item)
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	ou_label = ""
	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
		fields=["name", "organisation_unit", "budget_line", "indicative_amount"],
		order_by="creation asc",
	)
	if allocations:
		ou_label = cstr(
			frappe.db.get_value("Organisation Unit", allocations[0].organisation_unit, "unit_name")
			or allocations[0].organisation_unit
		)

	lines_by_id = {
		row["id"]: row
		for row in budget_gateway.list_eligible_budget_lines(
			procuring_entity=plan.procuring_entity, financial_year=plan.financial_year,
		)
	}

	check_token = ""
	all_sufficient = True
	positions_by_line: dict[str, dict[str, Any]] = {}
	decided = task_doc.status != "Open"
	if not decided:
		check = budget_gateway.check_funding(
			plan_item=item.name, plan_version=version.name, finance_task=task_doc.name,
			source_set_hash=task_doc.source_set_hash,
			allocations=[
				{
					"budget_line": a.budget_line, "amount": flt(a.indicative_amount),
					"plan_source_allocation": a.name,
				}
				for a in allocations
			],
			correlation_id=task_doc.name,
		)
		check_token = cstr(check.get("token"))
		all_sufficient = bool(check.get("all_sufficient"))
		positions_by_line = {row["budget_line"]: row for row in check.get("allocations", [])}

	rows = []
	for allocation in allocations:
		line = lines_by_id.get(allocation.budget_line, {})
		position = positions_by_line.get(allocation.budget_line, {})
		rows.append(
			{
				"budget_line_label": (
					f"{allocation.budget_line} — {line.get('title')}" if line.get("title") else allocation.budget_line
				),
				"funding_source": cstr(line.get("funding_source")) or "—",
				"approved_display": _money(line.get("approved") or 0),
				"reserved_display": _money(line.get("reserved") or 0),
				"committed_display": _money(line.get("committed") or 0),
				"available_display": _money(line.get("available") or 0),
				"required_display": _money(position.get("requested_amount") or allocation.indicative_amount),
				"available_after_display": _money(
					position.get("available_after") if position else (line.get("available") or 0)
				),
				"sufficient": bool(position.get("sufficient", True)) if position else True,
			}
		)

	return {
		"outcome": "OK",
		"task": task_doc.name,
		"task_reference": task_doc.task_reference,
		"task_token": task_doc.task_token,
		"status": task_doc.status,
		"decided": decided,
		"budget_check_token": check_token,
		"all_sufficient": all_sufficient,
		"header": {
			"eyebrow": "FINANCE CONFIRMATION",
			"title": "Confirm funding for Plan Item",
			"reference_line": f"{task_doc.task_reference} · {item.plan_item_id}",
			"badge": "Awaiting Finance" if task_doc.status == "Open" else task_doc.status,
		},
		"plan_item": {
			"title": item.title,
			"department": ou_label,
			"requirement_type": item.requirement_type,
			"value_display": _money(sum(flt(a.indicative_amount) for a in allocations)),
			"procurement_method": item.procurement_method,
			"delivery_completion_display": _date(item.delivery_completion_date),
		},
		"as_at_display": _eat(frappe.utils.now_datetime()),
		"lines": rows,
	}


def get_plan_governance_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	"""PLN-UI-11/12 — the Accounting Officer adoption (PLN-DES-11) and
	statutory approval (PLN-DES-12) tasks, from the same read model and
	screen: both fix the exact immutable `submitted_snapshot` (never a live
	query — §13 evidence is never re-derived) and differ only in the
	authority card and decision-statement copy."""
	from kentender_procurement.procurement_planning.services import planning_roles

	actor = cstr(user or frappe.session.user)
	if not task or not frappe.db.exists("Plan Governance Task", task):
		authority.not_found()
	task_doc = frappe.get_doc("Plan Governance Task", task)
	role = (
		planning_roles.ROLE_ACCOUNTING_OFFICER if task_doc.stage == "Accounting Officer adoption"
		else planning_roles.ROLE_PLAN_STATUTORY_APPROVER
	)
	authority.require_scope(actor, roles=(role,), procuring_entity=task_doc.procuring_entity)

	version = frappe.get_doc("Annual Plan Version", task_doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	pe_label = cstr(
		frappe.db.get_value("Procuring Entity", plan.procuring_entity, "legal_name") or plan.procuring_entity
	)
	rows = json.loads(version.submitted_snapshot) if version.submitted_snapshot else []
	total_value = sum(flt(row.get("value")) for row in rows)

	authority_card = None
	if task_doc.stage == "Statutory approval":
		ao_decision = frappe.db.get_value(
			"Plan Governance Task", {"plan_version": version.name, "stage": "Accounting Officer adoption"}, "decision"
		)
		ao_actor, ao_decided_at = "", ""
		if ao_decision:
			row = frappe.db.get_value(
				"Plan Governance Decision", ao_decision, ["actor", "decided_at"], as_dict=True
			)
			ao_actor = cstr(frappe.db.get_value("User", row.actor, "full_name") or row.actor) if row else ""
			ao_decided_at = _eat(row.decided_at) if row else ""
		authority_card = {
			"capacity": task_doc.capacity,
			"is_board": task_doc.capacity == "Board of Directors or similar governing body",
			"ao_adoption_line": f"{ao_actor} · {ao_decided_at}" if ao_actor else "",
		}

	return {
		"outcome": "OK",
		"task": task_doc.name,
		"task_reference": task_doc.task_reference,
		"task_token": task_doc.task_token,
		"status": task_doc.status,
		"stage": task_doc.stage,
		"header": {
			"eyebrow": f"{task_doc.stage.upper()} · {plan.plan_reference} · VERSION {version.version_number}",
			"title": plan.title or f"{pe_label} Annual Procurement Plan",
			"badge": version.version_status,
		},
		"authority_card": authority_card,
		"decision_statement": (
			"I adopt the complete consolidated Annual Procurement Plan Version "
			f"{version.version_number} shown above and submit it for the statutory approval "
			"applicable to this Procuring Entity."
			if task_doc.stage == "Accounting Officer adoption" else ""
		),
		"items": rows,
		"caption": f"{len(rows)} Plan Item{'s' if len(rows) != 1 else ''} · {_money(total_value)}",
		"confirm_label": (
			"Adopt and submit" if task_doc.stage == "Accounting Officer adoption"
			else "Approve Annual Procurement Plan"
		),
		"return_dialog": (
			{
				"title": "Return Plan Version for correction?",
				"lede": f"The submitted Version {version.version_number} remains unchanged. State the correction required.",
			}
			if task_doc.stage == "Accounting Officer adoption" else
			{
				"title": "Return adopted Plan Version for correction?",
				"lede": (
					f"The Accounting-Officer-adopted Version {version.version_number} remains unchanged. "
					"State the correction required."
				),
			}
		),
	}
