# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-007 — Request / confirm / return Plan Item Finance (PLN-FR-040…049)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ALLOC_EFFECTIVE,
	DOCTYPE_DECISION,
	ERR_INSUFFICIENT_FUNDING,
	FINANCE_AWAITING,
	FINANCE_CONFIRMED,
	FINANCE_DECISION_CONFIRM,
	FINANCE_DECISION_RETURN,
	FINANCE_NOT_REQUESTED,
	FINANCE_RETURNED,
	FINANCE_STALE,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	ITEM_REMOVED,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	CAP_PLAN_FINANCE_CONFIRM,
	CAP_PLAN_FINANCE_RETURN,
	CAP_PLAN_FINANCE_TASK,
	ROLE_BUDGET_OFFICER,
	assert_can_add_demand,
	assert_planning_scope,
)
from kentender_procurement.procurement_planning.services.plan_item_field_issues import (
	collect_plan_item_field_issues,
)
from kentender_procurement.procurement_planning.services.update_plan_item import (
	_request_finance_issues,
)
from kentender_procurement.procurement_planning.services._invariants import new_concurrency_token
from kentender_procurement.procurement_planning.services.planning_tasks import (
	authorize_planning_task,
	create_governed_planning_task,
	idempotent_decision,
	invalidate_planning_task,
	planning_task_action_allowed,
	task_owner,
	transition_planning_task,
)


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


@contextmanager
def _as_user(user: str) -> Iterator[None]:
	prev = frappe.session.user
	if user and user != prev:
		frappe.set_user(user)
	try:
		yield
	finally:
		if user and user != prev:
			frappe.set_user(prev)


def _iv_for_item(plan_item: str) -> tuple[Any, Any, Any]:
	item = frappe.get_doc("Procurement Plan Item", plan_item)
	plan = frappe.get_doc("Procurement Plan", item.plan)
	draft = cstr(plan.open_draft_version or "").strip()
	focus = draft or cstr(plan.current_approved_version or "").strip()
	iv_name = cstr(item.draft_item_version or "").strip()
	if not iv_name and focus:
		iv_name = cstr(
			frappe.db.get_value(
				"Procurement Plan Item Version",
				{"plan_item": item.name, "plan_version": focus},
				"name",
			)
			or ""
		)
	if not iv_name:
		iv_name = cstr(item.current_approved_item_version or "")
	if not iv_name:
		frappe.throw("Draft Plan Item Version not found.")
	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	return item, plan, iv


def _source_demand_row(plan_item: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"Plan Demand Allocation",
		filters={"plan_item": plan_item, "status": ["in", [ALLOC_DRAFT, ALLOC_EFFECTIVE]]},
		fields=["demand", "allocated_amount"],
		order_by="creation asc",
		limit=1,
	)
	alloc = rows[0] if rows else None
	if not alloc or not alloc.demand:
		return None
	demand = frappe.db.get_value(
		"Demand",
		alloc.demand,
		["name", "demand_code", "title"],
		as_dict=True,
	)
	if not demand:
		return None
	return {
		"demand": demand.name,
		"demand_code": demand.demand_code,
		"title": demand.title,
		"allocated_amount": flt(alloc.allocated_amount),
	}


def _dfa_for_demand(demand: str) -> Any | None:
	if not demand or not frappe.db.exists("DocType", "Demand Funding Allocation"):
		return None
	name = frappe.db.get_value("Demand Funding Allocation", {"demand": demand}, "name")
	if not name:
		return None
	return frappe.get_doc("Demand Funding Allocation", name)


def _source_finance_rows(plan_item: str) -> list[dict[str, Any]]:
	allocs = frappe.get_all(
		"Plan Demand Allocation",
		filters={"plan_item": plan_item, "status": ["in", [ALLOC_DRAFT, ALLOC_EFFECTIVE]]},
		fields=["name", "demand", "demand_item", "source_org_unit", "source_funding_allocation", "allocated_amount", "allocated_quantity"],
		order_by="creation asc",
	)
	rows: list[dict[str, Any]] = []
	for alloc in allocs:
		demand = frappe.db.get_value("Demand", alloc.demand, ["demand_code", "title", "required_by_date"], as_dict=True) or {}
		need = frappe.db.get_value("Demand Item", alloc.demand_item, ["description", "quantity", "uom"], as_dict=True) or {}
		dfa_name = cstr(alloc.source_funding_allocation) or cstr(frappe.db.get_value("Demand Funding Allocation", {"demand": alloc.demand}, "name"))
		dfa = frappe.get_doc("Demand Funding Allocation", dfa_name) if dfa_name and frappe.db.exists("Demand Funding Allocation", dfa_name) else None
		line_id = cstr(dfa.budget_line if dfa else "")
		rows.append({
			"allocation": alloc.name, "demand": alloc.demand, "demand_code": cstr(demand.get("demand_code")), "demand_title": cstr(demand.get("title")),
			"demand_item": alloc.demand_item, "need_item": cstr(need.get("description")), "quantity": flt(alloc.allocated_quantity or need.get("quantity")), "uom": cstr(need.get("uom")),
			"required_by_date": str(demand.get("required_by_date") or ""), "source_org_unit": cstr(alloc.source_org_unit),
			"funding_allocation": dfa_name, "budget_line_id": line_id, "budget_line": _budget_line_display(line_id), "amount": flt(alloc.allocated_amount),
			"reservation": cstr(dfa.funding_reservation if dfa else ""),
		})
	return rows


def _funding_sources(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Group Need Item rows by their authoritative Demand funding allocation."""
	grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
	for row in rows:
		key = (cstr(row["funding_allocation"]), cstr(row["demand"]), cstr(row["budget_line_id"]))
		if key not in grouped:
			grouped[key] = dict(row)
			grouped[key]["amount"] = 0.0
		grouped[key]["amount"] += flt(row["amount"])
	return list(grouped.values())


def _budget_line_display(line_id: str) -> dict[str, str]:
	empty = {"id": "", "code": "", "name": "", "display": "—"}
	if not line_id or not frappe.db.exists("Budget Line", line_id):
		return empty
	title = cstr(frappe.db.get_value("Budget Line", line_id, "title") or "").strip()
	code = cstr(
		frappe.db.get_value("Budget Line", line_id, "generated_reference")
		or frappe.db.get_value("Budget Line", line_id, "budget_line_code")
		or ""
	).strip()
	name = title or code or line_id
	if name == line_id and len(line_id) <= 12 and name.isalnum():
		name = code or "Budget Line"
	display = f"{name} ({code})" if code and name != code else name
	return {"id": line_id, "code": code, "name": name, "display": display}


def _existing_reservation(dfa: Any | None, line_id: str, *, iv: Any | None = None) -> Any | None:
	if not dfa:
		return None
	rsv_name = cstr(dfa.funding_reservation or "").strip()
	if not rsv_name or not frappe.db.exists("Funding Reservation", rsv_name):
		return None
	rsv = frappe.get_doc("Funding Reservation", rsv_name)
	if cstr(rsv.status) not in ("Reserved", "Partially converted"):
		return None
	if line_id and cstr(rsv.budget_line) != line_id:
		return None
	from kentender_core.seeds.kentender_mvp_v1 import constants as C

	code = cstr(rsv.generated_reference or "")
	owned = cstr(getattr(iv, "finance_reservation", None) or "") if iv is not None else ""
	if code == C.RSV_CODE and owned not in (rsv.name, code):
		return None
	return rsv


def effective_finance_status(iv: Any) -> str:
	"""Live status — Confirmed becomes Stale when amount or Budget Line diverges."""
	status = cstr(getattr(iv, "finance_status", None) or FINANCE_NOT_REQUESTED).strip()
	demand = _source_demand_row(iv.plan_item)
	dfa = _dfa_for_demand(demand["demand"] if demand else "")
	live_line = cstr(dfa.budget_line if dfa else "").strip()
	return effective_finance_status_from_values(
		status=status,
		snapshot_amount=getattr(iv, "finance_snapshot_amount", 0),
		snapshot_budget_line=getattr(iv, "finance_snapshot_budget_line", None),
		live_amount=getattr(iv, "confirmed_estimate", 0),
		live_budget_line=live_line,
	)


def effective_finance_status_from_values(
	*,
	status: str | None,
	snapshot_amount: float | None,
	snapshot_budget_line: str | None,
	live_amount: float | None,
	live_budget_line: str | None,
) -> str:
	"""Apply the canonical Finance stale predicate to preloaded values."""
	current = cstr(status or FINANCE_NOT_REQUESTED).strip() or FINANCE_NOT_REQUESTED
	if current != FINANCE_CONFIRMED:
		return current
	snap_amt = flt(snapshot_amount or 0)
	snap_line = cstr(snapshot_budget_line or "").strip()
	live_amt = flt(live_amount or 0)
	live_line = cstr(live_budget_line or "").strip()
	if snap_amt and abs(live_amt - snap_amt) > 0.005:
		return FINANCE_STALE
	if snap_line and live_line and snap_line != live_line:
		return FINANCE_STALE
	return FINANCE_CONFIRMED


def finance_status_label(iv: Any | None) -> str:
	if not iv:
		return FINANCE_NOT_REQUESTED
	return effective_finance_status(iv)


def plan_finance_summary(*, plan: str, version: str) -> dict[str, Any]:
	"""Current Finance status for included Plan Items on a version (PLN-AC-009 / §10.3)."""
	confirmed = 0
	unconfirmed: list[str] = []
	total = 0
	for it in frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan, "baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]]},
		fields=["name", "plan_item_code"],
		order_by="creation asc",
	):
		iv_name = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": it.name, "plan_version": version},
			"name",
		)
		if not iv_name:
			continue
		iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
		status = effective_finance_status(iv)
		total += 1
		if status == FINANCE_CONFIRMED:
			confirmed += 1
		else:
			unconfirmed.append(cstr(it.plan_item_code or it.name))
	return {
		"finance_item_count": total,
		"finance_confirmed_count": confirmed,
		"finance_confirmed_label": f"{confirmed} of {total}",
		"all_confirmed": bool(total) and confirmed == total,
		"unconfirmed_codes": unconfirmed,
	}


def finance_not_confirmed_error(*, plan: str, version: str) -> dict[str, str] | None:
	"""Form error when any included item is not currently Finance Confirmed."""
	summary = plan_finance_summary(plan=plan, version=version)
	if summary["finance_item_count"] and not summary["all_confirmed"]:
		return {
			"form": (
				"Confirm current Finance for every included Plan Item before this decision."
			)
		}
	return None


def _persist_stale_if_needed(iv: Any) -> str:
	status = effective_finance_status(iv)
	if status == FINANCE_STALE and cstr(iv.finance_status) == FINANCE_CONFIRMED:
		iv.finance_status = FINANCE_STALE
		iv.save(ignore_permissions=True)
	return status


def request_plan_item_finance(
	*,
	plan_item: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""Create or reuse one Awaiting confirmation task after planning completeness."""
	actor = assert_can_add_demand(user)
	item_name = cstr(plan_item).strip()
	if not item_name or not frappe.db.exists("Procurement Plan Item", item_name):
		return {"ok": False, "errors": {"form": "Plan Item not found"}}
	item, plan, iv = _iv_for_item(item_name)
	if cstr(item.baseline_state) == ITEM_REMOVED:
		return {"ok": False, "errors": {"form": "Removed Plan Items cannot request Finance."}}
	assert_planning_scope(
		procuring_entity=cstr(plan.procuring_entity).strip(),
		org_unit=cstr(item.owner_org_unit or "").strip() or None,
		user=actor,
		require_write=True,
	)
	field_issues = collect_plan_item_field_issues(iv=iv, payload={}, include_preference=False)
	finance_issues = _request_finance_issues(iv, field_issues)
	if finance_issues:
		return {
			"ok": True,
			"complete": False,
			"finance_status": finance_status_label(iv),
			"field_issues": finance_issues,
			"plan_item": item_name,
			"item_version": iv.name,
		}
	status = effective_finance_status(iv)
	if status == FINANCE_AWAITING:
		return {
			"ok": True,
			"complete": True,
			"idempotent": True,
			"finance_status": FINANCE_AWAITING,
			"plan_item": item_name,
			"item_version": iv.name,
			"task": cstr(getattr(iv, "finance_task_id", "")),
			"task_token": cstr(getattr(iv, "finance_task_token", "")),
			"assignee": cstr(getattr(iv, "finance_task_assignee", "")),
			"actor": actor,
		}
	if status == FINANCE_CONFIRMED:
		return {
			"ok": True,
			"complete": True,
			"idempotent": True,
			"finance_status": FINANCE_CONFIRMED,
			"plan_item": item_name,
			"item_version": iv.name,
			"actor": actor,
		}
	predecessor = cstr(getattr(iv, "finance_task_id", ""))
	task, iteration = create_governed_planning_task(
		prefix="PLN-FIN", record=iv, id_field="finance_task_id", iteration_field="finance_task_iteration",
		task_type=CAP_PLAN_FINANCE_TASK, subject_type="Procurement Plan Item Version", subject_id=iv.name,
		procuring_entity=cstr(plan.procuring_entity), financial_year=cstr(plan.financial_year),
		organisation_unit=cstr(item.owner_org_unit), predecessor_task_id=predecessor,
		idempotency_key=f"planning:finance:{iv.name}:{int(iv.finance_task_iteration or 0) + 1}", actor=actor,
	)
	task_id = task.name
	task_token = cstr(task.concurrency_token)
	assignee = task_owner(task)
	iv.finance_status = FINANCE_AWAITING
	iv.finance_task_id = task_id
	iv.finance_task_iteration = iteration
	iv.finance_task_assignee = assignee
	iv.finance_task_state = "Open"
	iv.finance_task_predecessor = predecessor or None
	iv.finance_task_token = task_token
	iv.save(ignore_permissions=True)
	from kentender_procurement.procurement_planning.services.planning_notification_service import (
		notify_finance_requested,
	)

	notify_finance_requested(plan=plan, item=item, iv=iv, actor=actor)
	return {
		"ok": True,
		"complete": True,
		"idempotent": False,
		"finance_status": FINANCE_AWAITING,
		"plan_item": item_name,
		"item_version": iv.name,
		"task": task_id,
		"task_token": task_token,
		"assignee": assignee,
		"actor": actor,
	}


def _task_payload(
	*,
	item: Any,
	plan: Any,
	iv: Any,
	actor: str,
	check: dict[str, Any] | None,
	demand: dict[str, Any] | None,
	line: dict[str, str],
	existing_rsv: Any | None,
) -> dict[str, Any]:
	status = _persist_stale_if_needed(iv)
	amount = flt(iv.confirmed_estimate)
	currency = cstr(iv.currency or plan.currency or "KES")
	sufficient = False
	shortfall = 0.0
	available_before = 0.0
	available_after = 0.0
	if existing_rsv:
		sufficient = True
		available_before = flt(check.get("available_before") if check else 0) + flt(
			existing_rsv.remaining_reserved
		)
		available_after = flt(check.get("available_before") if check else 0)
	elif check:
		sufficient = bool(check.get("sufficient"))
		shortfall = flt(check.get("shortfall") or 0)
		available_before = flt(check.get("available_before") or 0)
		available_after = flt(check.get("available_after") or 0)
	variant = "sufficient" if sufficient else "shortfall"
	can_confirm = (
		planning_task_action_allowed(task_id=cstr(iv.finance_task_id), actor=actor, capability=CAP_PLAN_FINANCE_CONFIRM)
		and status in (FINANCE_AWAITING, FINANCE_STALE)
		and sufficient
	)
	can_return = planning_task_action_allowed(task_id=cstr(iv.finance_task_id), actor=actor, capability=CAP_PLAN_FINANCE_RETURN) and status in (
		FINANCE_AWAITING,
		FINANCE_STALE,
	)
	ver_num = int(
		frappe.db.get_value("Procurement Plan Version", iv.plan_version, "version_number") or 1
	)
	ver_status = cstr(
		frappe.db.get_value("Procurement Plan Version", iv.plan_version, "status") or "Draft"
	)
	ou = cstr(item.owner_org_unit or "")
	ou_label = cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou) if ou else ""
	if sufficient:
		availability_status = "Sufficient"
		notice = ""
	else:
		availability_status = "Insufficient funding"
		notice = (
			"This Plan Item cannot be confirmed because the Budget Line is short by "
			f"{_money(shortfall, currency)}."
			if shortfall
			else "This Plan Item cannot be confirmed because the Budget Line has insufficient funding."
		)
	return {
		"ok": True,
		"surface": "task",
		"variant": variant,
		"plan": plan.name,
		"plan_title": plan.title,
		"plan_code": plan.plan_code,
		"plan_item": item.name,
		"plan_item_code": item.plan_item_code,
		"item_version": iv.name,
		"task": cstr(iv.finance_task_id),
		"task_token": cstr(iv.finance_task_token),
		"requirement_title": iv.requirement_title,
		"owner_org_unit": ou,
		"owner_org_unit_label": ou_label,
		"plan_item_status_label": f"{item.baseline_state} · Planning complete",
		"version_label": f"{ver_status} Version {ver_num}",
		"finance_status": status,
		"finance_status_label": status,
		"amount": amount,
		"amount_display": _money(amount, currency),
		"currency": currency,
		"source_demand": demand.get("title") if demand else "",
		"source_demand_id": demand.get("demand") if demand else "",
		"source_demand_code": demand.get("demand_code") if demand else "",
		"budget_line": line,
		"available_before": available_before,
		"available_before_display": _money(available_before, currency),
		"available_after": available_after,
		"available_after_display": _money(available_after, currency),
		"shortfall": shortfall,
		"shortfall_display": _money(shortfall, currency) if shortfall else "",
		"sufficient": sufficient,
		"can_confirm": can_confirm,
		"can_return": can_return,
		"availability_status": availability_status,
		"notice": notice,
		"existing_reservation": cstr(existing_rsv.generated_reference if existing_rsv else "")
		or cstr(existing_rsv.name if existing_rsv else ""),
		"builder_route": f"/app/procurement-plan-builder?plan={plan.name}",
		"budget_funding_route": _budget_activity_route(line.get("id") if line else ""),
	}


def _budget_activity_route(line_id: str) -> str:
	line_id = cstr(line_id or "").strip()
	if not line_id or not frappe.db.exists("Budget Line", line_id):
		return "/app/budget-funding"
	budget = cstr(frappe.db.get_value("Budget Line", line_id, "budget") or "").strip()
	if not budget:
		return "/app/budget-funding"
	code = cstr(frappe.db.get_value("Budget", budget, "generated_reference") or "").strip()
	return f"/app/budget-funding-activity/{code or budget}"


def get_plan_finance_task(
	*,
	task: str,
	user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	task_id = cstr(task).strip()
	workflow_task = authorize_planning_task(
		task_id=task_id, actor=actor, capability=CAP_PLAN_FINANCE_TASK,
		subject_type="Procurement Plan Item Version",
	)
	iv_name = cstr(workflow_task.subject_id)
	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	if cstr(iv.finance_task_id) != task_id:
		frappe.throw("Task not found.", frappe.PermissionError, title="PLN_TASK_NOT_FOUND")
	item_name = cstr(iv.plan_item)
	item, plan, iv = _iv_for_item(item_name)
	assert_planning_scope(
		procuring_entity=cstr(plan.procuring_entity).strip(),
		org_unit=cstr(item.owner_org_unit or "").strip() or None,
		user=actor,
		require_write=False,
	)
	status = effective_finance_status(iv)
	if status == FINANCE_NOT_REQUESTED:
		return {
			"ok": False,
			"errors": {"form": "Finance confirmation has not been requested for this Plan Item."},
		}
	demand = _source_demand_row(item.name)
	dfa = _dfa_for_demand(demand["demand"] if demand else "")
	line_id = cstr(dfa.budget_line if dfa else "").strip()
	line = _budget_line_display(line_id)
	existing = _existing_reservation(dfa, line_id, iv=iv)
	check: dict[str, Any] | None = None
	if line_id:
		from kentender_budget.services.budget_check_reserve_contracts import check_funding

		with _as_user(actor):
			check = check_funding(
				budget_line=line_id,
				requested_amount=flt(iv.confirmed_estimate),
				demand=demand["demand"] if demand else None,
				procuring_entity=cstr(plan.procuring_entity).strip(),
			)
	payload = _task_payload(
		item=item,
		plan=plan,
		iv=iv,
		actor=actor,
		check=check,
		demand=demand,
		line=line,
		existing_rsv=existing,
	)
	sources = _source_finance_rows(item.name)
	if sources:
		from kentender_budget.services.budget_check_reserve_contracts import check_funding
		for source in sources:
			if not source["budget_line_id"]:
				source["funding_check"] = {"sufficient": False, "available_before": 0, "available_after": 0, "shortfall": source["amount"]}
				continue
			with _as_user(actor):
				source["funding_check"] = check_funding(budget_line=source["budget_line_id"], requested_amount=source["amount"], demand=source["demand"], procuring_entity=cstr(plan.procuring_entity))
		payload["sources"] = sources
		payload["sufficient"] = all(bool(s["funding_check"].get("sufficient")) for s in sources)
		payload["variant"] = "sufficient" if payload["sufficient"] else "shortfall"
		payload["can_confirm"] = bool(payload["can_confirm"] and payload["sufficient"])
		payload["available_before"] = sum(flt(s["funding_check"].get("available_before")) for s in sources)
		payload["available_after"] = sum(flt(s["funding_check"].get("available_after")) for s in sources)
		payload["shortfall"] = sum(flt(s["funding_check"].get("shortfall")) for s in sources)
		payload["available_before_display"] = _money(payload["available_before"], payload["currency"])
		payload["available_after_display"] = _money(payload["available_after"], payload["currency"])
		payload["shortfall_display"] = _money(payload["shortfall"], payload["currency"]) if payload["shortfall"] else ""
		if not payload["sufficient"]:
			payload["notice"] = f"This Plan Item cannot be confirmed because its source Budget Lines are short by {payload['shortfall_display']}."
	payload.update({"task": task_id, "task_token": cstr(iv.finance_task_token), "task_iteration": int(iv.finance_task_iteration or 1), "assignee": actor})
	return payload


def _record_finance_decision(
	*,
	plan_version: str,
	plan_item: str,
	actor: str,
	decision_type: str,
	decision: str,
	reason: str,
	task_id: str,
	task_iteration: int,
	idempotency_key: str,
) -> None:
	frappe.get_doc(
		{
			"doctype": DOCTYPE_DECISION,
			"plan_version": plan_version,
			"plan_item": plan_item,
			"decision_type": decision_type,
			"decision_stage": "Plan Item finance",
			"actor": actor,
			"actor_role": ROLE_BUDGET_OFFICER,
			"decision": decision,
			"reason": reason,
			"decided_at": now_datetime(),
			"task_id": task_id,
			"task_iteration": task_iteration,
			"command_idempotency_key": idempotency_key,
		}
	).insert(ignore_permissions=True)


def confirm_plan_item_funding(
	*,
	task: str,
	expected_token: str | None = None,
	note: str | None = None,
	idempotency_key: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	task_id = cstr(task).strip()
	replay = idempotent_decision(
		idempotency_key, actor=actor, task_id=task_id, capability=CAP_PLAN_FINANCE_CONFIRM
	)
	if replay:
		return replay
	workflow_task = authorize_planning_task(
		task_id=task_id, actor=actor, capability=CAP_PLAN_FINANCE_CONFIRM,
		subject_type="Procurement Plan Item Version",
	)
	iv_name = cstr(workflow_task.subject_id)
	task_iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	if cstr(task_iv.finance_task_id) != task_id:
		frappe.throw("Task not found.", frappe.PermissionError, title="PLN_TASK_NOT_FOUND")
	item_name = cstr(task_iv.plan_item)
	item, plan, iv = _iv_for_item(item_name)
	assert_planning_scope(
		procuring_entity=cstr(plan.procuring_entity).strip(),
		org_unit=cstr(item.owner_org_unit or "").strip() or None,
		user=actor,
		require_write=False,
	)
	status = _persist_stale_if_needed(iv)
	if status == FINANCE_NOT_REQUESTED:
		return {"ok": False, "errors": {"form": "Finance confirmation has not been requested."}}
	if status == FINANCE_RETURNED:
		return {"ok": False, "errors": {"form": "Returned items must be re-requested by the planner."}}
	if status == FINANCE_CONFIRMED:
		return {
			"ok": True,
			"idempotent": True,
			"finance_status": FINANCE_CONFIRMED,
			"plan_item": item_name,
			"item_version": iv.name,
			"reservation": cstr(iv.finance_reservation or iv.reservation_reference or ""),
			"actor": actor,
		}

	sources = _funding_sources(_source_finance_rows(item.name))
	if not sources or any(not row["budget_line_id"] for row in sources):
		return {"ok": False, "errors": {"form": "Every source must have a proposed Budget Line before funding can be confirmed."}}
	from kentender_budget.services.budget_check_reserve_contracts import check_funding, reserve_funding
	checks = []
	with _as_user(actor):
		for source in sources:
			dfa = frappe.get_doc("Demand Funding Allocation", source["funding_allocation"]) if source["funding_allocation"] else None
			existing = _existing_reservation(dfa, source["budget_line_id"], iv=iv)
			if existing and flt(existing.remaining_reserved) >= flt(source["amount"]):
				check = {"sufficient": True, "shortfall": 0, "existing_reservation": existing.name}
			else:
				check = check_funding(budget_line=source["budget_line_id"], requested_amount=source["amount"], demand=source["demand"], procuring_entity=cstr(plan.procuring_entity))
			checks.append(check)
	if not all(check.get("sufficient") for check in checks):
		shortfall = sum(flt(check.get("shortfall")) for check in checks)
		return {"ok": False, "error_code": ERR_INSUFFICIENT_FUNDING, "errors": {"form": f"This Plan Item cannot be confirmed because its source Budget Lines are short by {_money(shortfall, cstr(iv.currency or plan.currency))}."}}
	reservation_names: list[str] = []
	reservation_codes: list[str] = []
	owned = 0
	from kentender_core.seeds.kentender_mvp_v1 import constants as C
	with _as_user(actor):
		for index, source in enumerate(sources):
			dfa = frappe.get_doc("Demand Funding Allocation", source["funding_allocation"]) if source["funding_allocation"] else None
			existing = _existing_reservation(dfa, source["budget_line_id"], iv=iv)
			if existing and flt(existing.remaining_reserved) >= flt(source["amount"]):
				reservation_names.append(cstr(existing.name))
				reservation_codes.append(cstr(existing.generated_reference or existing.name))
				continue
			preferred_ref = None
			if len(sources) == 1 and cstr(item.plan_item_code) == C.PLAN_ITEM_CODE:
				preferred_ref = C.RSV_CODE
			elif len(sources) == 1 and cstr(item.plan_item_code) == C.PLAN_ITEM_CODE_SCN:
				preferred_ref = C.RSV_CODE_SCN
			result = reserve_funding(budget_line=source["budget_line_id"], demand_name=source["demand"], requested_amount=source["amount"], idempotency_key=f"{cstr(idempotency_key)}:source:{index}", actor=actor, procuring_entity=cstr(plan.procuring_entity), generated_reference=preferred_ref)
			name = cstr(result.get("reservation_id"))
			code = cstr(result.get("reservation_code") or name)
			reservation_names.append(name); reservation_codes.append(code)
			owned += 0 if result.get("reused") else 1
			if source["funding_allocation"]:
				frappe.db.set_value("Demand Funding Allocation", source["funding_allocation"], {"funding_reservation": name, "reservation_status": cstr(result.get("status") or "Reserved")}, update_modified=False)
	amount = sum(row["amount"] for row in sources)
	line_id = sources[0]["budget_line_id"] if len(sources) == 1 else "MULTIPLE"
	reservation_name = ",".join(reservation_names)
	reservation_code = ", ".join(reservation_codes)

	completed_task = transition_planning_task(
		task_id=task_id, actor=actor, capability=CAP_PLAN_FINANCE_CONFIRM,
		target_state="Completed", expected_token=cstr(expected_token),
	)
	iv.finance_status = FINANCE_CONFIRMED
	iv.finance_snapshot_amount = amount
	iv.finance_snapshot_budget_line = line_id
	iv.finance_confirmed_at = now_datetime()
	iv.finance_confirmed_by = actor
	iv.finance_reservation = reservation_name or reservation_code
	iv.finance_owned_reservation = 1 if owned else 0
	iv.reservation_reference = reservation_code or reservation_name
	iv.finance_task_state = "Confirmed"
	iv.finance_task_token = cstr(completed_task.concurrency_token)
	iv.save(ignore_permissions=True)
	_record_finance_decision(
		plan_version=iv.plan_version,
		plan_item=item.name,
		actor=actor,
		decision_type=FINANCE_DECISION_CONFIRM,
		decision=FINANCE_CONFIRMED,
		reason=cstr(note or "").strip(),
		task_id=task_id,
		task_iteration=int(iv.finance_task_iteration or 1),
		idempotency_key=cstr(idempotency_key),
	)
	frappe.db.commit()
	return {
		"ok": True,
		"idempotent": False,
		"finance_status": FINANCE_CONFIRMED,
		"plan_item": item_name,
		"item_version": iv.name,
		"reservation": reservation_code or reservation_name,
		"actor": actor,
	}


def return_plan_item_from_finance(
	*,
	task: str,
	expected_token: str | None = None,
	reason: str | None = None,
	idempotency_key: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	task_id = cstr(task).strip()
	note = cstr(reason or "").strip()
	if not note:
		return {"ok": False, "errors": {"reason": "A return reason is required."}}
	replay = idempotent_decision(
		idempotency_key, actor=actor, task_id=task_id, capability=CAP_PLAN_FINANCE_RETURN
	)
	if replay:
		return replay
	workflow_task = authorize_planning_task(
		task_id=task_id, actor=actor, capability=CAP_PLAN_FINANCE_RETURN,
		subject_type="Procurement Plan Item Version",
	)
	iv_name = cstr(workflow_task.subject_id)
	task_iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	if cstr(task_iv.finance_task_id) != task_id:
		frappe.throw("Task not found.", frappe.PermissionError, title="PLN_TASK_NOT_FOUND")
	item_name = cstr(task_iv.plan_item)
	item, plan, iv = _iv_for_item(item_name)
	assert_planning_scope(
		procuring_entity=cstr(plan.procuring_entity).strip(),
		org_unit=cstr(item.owner_org_unit or "").strip() or None,
		user=actor,
		require_write=False,
	)
	status = effective_finance_status(iv)
	if status == FINANCE_RETURNED:
		return {
			"ok": True,
			"idempotent": True,
			"finance_status": FINANCE_RETURNED,
			"plan_item": item_name,
			"actor": actor,
		}
	if status not in (FINANCE_AWAITING, FINANCE_STALE, FINANCE_CONFIRMED):
		return {"ok": False, "errors": {"form": "This Finance task cannot be returned."}}
	returned_task = transition_planning_task(
		task_id=task_id, actor=actor, capability=CAP_PLAN_FINANCE_RETURN,
		target_state="Returned", expected_token=cstr(expected_token),
	)
	iv.finance_status = FINANCE_RETURNED
	iv.finance_task_state = "Returned"
	iv.finance_task_token = cstr(returned_task.concurrency_token)
	iv.save(ignore_permissions=True)
	_record_finance_decision(
		plan_version=iv.plan_version,
		plan_item=item.name,
		actor=actor,
		decision_type=FINANCE_DECISION_RETURN,
		decision=FINANCE_RETURNED,
		reason=note,
		task_id=task_id,
		task_iteration=int(iv.finance_task_iteration or 1),
		idempotency_key=cstr(idempotency_key),
	)
	frappe.db.commit()
	return {
		"ok": True,
		"idempotent": False,
		"finance_status": FINANCE_RETURNED,
		"plan_item": item_name,
		"item_version": iv.name,
		"actor": actor,
	}


def cancel_awaiting_or_release_owned(
	*,
	plan_item: str,
	version: str,
) -> dict[str, Any]:
	"""Used by release_draft_finance_effects — cancel Awaiting or release Planning-owned RSV."""
	iv_name = frappe.db.get_value(
		"Procurement Plan Item Version",
		{"plan_item": plan_item, "plan_version": version},
		"name",
	)
	if not iv_name:
		return {
			"ok": True,
			"released": False,
			"cancelled_task": False,
			"idempotent": False,
			"reason": "no_finance_task",
		}
	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	status = effective_finance_status(iv)
	if status in ("", FINANCE_NOT_REQUESTED):
		return {
			"ok": True,
			"released": False,
			"cancelled_task": False,
			"idempotent": False,
			"reason": "no_finance_task",
		}
	released = False
	cancelled = False
	if int(iv.finance_owned_reservation or 0) and cstr(iv.finance_reservation or "").strip():
		from kentender_budget.api.dia_budget_control import release_reservation

		for reservation_id in filter(None, (part.strip() for part in cstr(iv.finance_reservation).split(","))):
			release_reservation(reservation_id=reservation_id, reason="Plan Item removed from draft")
		released = True
		iv.finance_owned_reservation = 0
	if status in (FINANCE_AWAITING, FINANCE_STALE, FINANCE_RETURNED, FINANCE_CONFIRMED):
		cancelled = status in (FINANCE_AWAITING, FINANCE_STALE, FINANCE_RETURNED)
		iv.finance_status = FINANCE_NOT_REQUESTED
		if cstr(getattr(iv, "finance_task_state", "")) == "Open":
			invalidate_planning_task(
				task_id=cstr(iv.finance_task_id), subject_type="Procurement Plan Item Version",
				subject_id=iv.name, actor=frappe.session.user,
				reason="Plan Item removed from draft",
			)
			iv.finance_task_state = "Cancelled"
			iv.finance_task_token = new_concurrency_token()
		iv.save(ignore_permissions=True)
	return {
		"ok": True,
		"released": released,
		"cancelled_task": cancelled or released,
		"idempotent": False,
		"reason": "released" if released else ("cancelled_task" if cancelled else "cleared"),
	}
