# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §7.4/§8/§8.2 — Requisition eligibility (Slice H).

`GetRequisitionEligiblePlanItem.v2` is the published, read-only contract
Procurement Requisitions calls to decide whether — and how much of — a Plan
Item it may draw against (invariant 1: it creates nothing). Planning owns
the balance ledger (`Plan Drawdown Reference`) a real Requisitions module
would post to; §2.1 excludes a Requisition, its specification and any
purchase-request record from this repo, so nothing in this module ever
creates one, and no such module exists here yet to call
`record_requisition_drawdown`/`reverse_requisition_drawdown` for real. Both
commands are still built and tested against the published contract §7.4
actually specifies, exactly as PLN-706/`_no_downstream_use` were carried
forward with no live caller until their consuming slice existed.

§9's twenty-one error codes are Planning's own UI-facing vocabulary; a
programmatic contract call from a sibling module is not a Planning screen,
so `record_requisition_drawdown`'s balance/state failures raise a plain
`frappe.ValidationError` instead of forcing an unrelated §9 code onto a
condition the contract's own author never named one for (§9's own docstring:
"an invented code is a defect in the caller") — the same reasoning
`authority.not_found()` already uses to sit outside that closed set.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.services import authority, envelope, plan_read
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_PLANNING_AUDITOR,
	ROLE_PROCUREMENT_PLANNER,
)


def _authorise_planner(actor: str, procuring_entity: str) -> None:
	authority.require_scope(
		actor, roles=(ROLE_PROCUREMENT_PLANNER, ROLE_PLANNING_AUDITOR), procuring_entity=procuring_entity,
	)


def _authorise_system_caller(actor: str) -> None:
	"""No Requisitions role vocabulary exists in this repo to authorise
	against (§2.1); a System Manager/Administrator system-principal call —
	the same shape Planning's own budget_gateway/needs_intake calls use
	against Budget/Needs — is the narrowest gate available today."""
	if actor != "Administrator" and "System Manager" not in frappe.get_roles(actor):
		authority.not_found()


def _drawn_totals(allocation_names: set[str]) -> dict[str, tuple[float, float]]:
	rows = frappe.get_all(
		"Plan Drawdown Reference",
		filters={"allocation": ("in", list(allocation_names) or ("",)), "drawdown_state": "Active"},
		fields=["allocation", "quantity", "amount"],
	)
	totals: dict[str, tuple[float, float]] = {}
	for row in rows:
		qty, amount = totals.get(row.allocation, (0.0, 0.0))
		totals[row.allocation] = (qty + flt(row.quantity), amount + flt(row.amount))
	return totals


def get_requisition_eligible_plan_item(*, plan_item_id: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4 `GetRequisitionEligiblePlanItem.v2` — read-only (invariant 1)."""
	actor = cstr(user or frappe.session.user)
	name = plan_read.resolve_item_doc_name(plan_item_id)
	item = frappe.get_doc("Annual Plan Item", name)
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise_planner(actor, plan.procuring_entity)

	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item.name, "allocation_state": "Active"},
		fields=[
			"name", "allocation_id", "dpp_entry", "source_origin", "need", "need_version",
			"organisation_unit", "quantity", "unit", "required_by_date", "budget_line", "indicative_amount",
		],
		order_by="creation asc",
	)
	drawn = _drawn_totals({a.name for a in allocations})

	sources: list[dict[str, Any]] = []
	total_qty = total_value = total_remaining_qty = total_remaining_value = 0.0
	for a in allocations:
		drawn_qty, drawn_amount = drawn.get(a.name, (0.0, 0.0))
		remaining_qty = flt(a.quantity) - drawn_qty
		remaining_amount = flt(a.indicative_amount) - drawn_amount
		entry = (
			frappe.db.get_value(
				"Departmental Plan Entry", a.dpp_entry,
				["title", "description", "expected_operational_result"], as_dict=True,
			)
			or {}
		)
		sources.append(
			{
				"plan_source_allocation_id": a.allocation_id,
				"source_origin": a.source_origin,
				"dpp_entry": a.dpp_entry if a.source_origin == "Direct departmental requirement" else "",
				"need": cstr(a.need) or None,
				"need_version": cstr(a.need_version) or None,
				"organisation_unit": a.organisation_unit,
				"title": entry.get("title") or "",
				"description": entry.get("description") or "",
				"expected_operational_result": entry.get("expected_operational_result") or "",
				"approved_quantity": flt(a.quantity),
				"remaining_quantity": remaining_qty,
				"unit": a.unit,
				"required_by_date": cstr(a.required_by_date),
				"budget_line": a.budget_line,
				"allocated_amount": flt(a.indicative_amount),
				"remaining_amount": remaining_amount,
			}
		)
		total_qty += flt(a.quantity)
		total_value += flt(a.indicative_amount)
		total_remaining_qty += remaining_qty
		total_remaining_value += remaining_amount

	finance_refs = frappe.get_all(
		"Plan Reservation Reference", filters={"plan_item": item.name}, pluck="name",
	)
	# §7.4/invariant 18: eligibility follows the item's own current state —
	# an open (unacknowledged) successor proposing removal never changes it;
	# only an acknowledged one does, and that already moves this copy off
	# "Active" (Superseded) or "Removed in successor". §7.1's Need-withdrawal
	# clause needs no separate check here: Needs itself refuses to publish a
	# withdrawal while an Active Plan dependency exists, so that state is
	# already structurally unreachable.
	eligible = (
		item.item_state == "Active"
		and item.finance_state == "Confirmed"
		and total_remaining_qty > 0
		and total_remaining_value > 0
	)
	return {
		"outcome": "OK",
		"eligible": eligible,
		"plan_reference": plan.plan_reference,
		"version_reference": version.name,
		"plan_item_id": item.plan_item_id,
		"record_version": int(item.record_version or 0),
		"procuring_entity": plan.procuring_entity,
		"financial_year": plan.financial_year,
		"requirement_type": item.requirement_type,
		"procurement_method": item.procurement_method,
		"strategic_objective": item.strategic_objective,
		"objective_path": item.objective_path,
		"planned_dates": {
			"invitation_date": cstr(item.invitation_date),
			"bid_opening_date": cstr(item.bid_opening_date),
			"evaluation_completion_date": cstr(item.evaluation_completion_date),
			"award_approval_date": cstr(item.award_approval_date),
			"award_notification_date": cstr(item.award_notification_date),
			"contract_signing_date": cstr(item.contract_signing_date),
			"delivery_completion_date": cstr(item.delivery_completion_date),
		},
		"funding_confirmation_references": finance_refs,
		"finance_state": item.finance_state,
		"total_quantity": total_qty,
		"total_value": total_value,
		"remaining_quantity": total_remaining_qty,
		"remaining_value": total_remaining_value,
		"sources": sources,
		"evaluated_at": cstr(now_datetime()),
	}


def record_requisition_drawdown(
	*,
	plan_item_id: str,
	requisition_reference: str,
	requesting_org_unit: str,
	allocations: list[dict[str, Any]],
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""§7.4/§8.2 — atomic: every requested allocation draws within its own
	remaining balance, or none draw at all. `allocations` is
	`[{"plan_source_allocation_id": ..., "quantity": ..., "amount": ...}, …]`.
	`expected_record_version` is the Plan Item's own — §8.2's blanket rule
	("all mutating commands require an expected record version"); it also
	means a racing second drawdown against the same item must re-read the
	freshly-consumed balance before it can proceed, on top of the per-
	allocation row lock below."""
	actor = cstr(user or frappe.session.user)
	payload = {
		"plan_item_id": plan_item_id, "requisition_reference": cstr(requisition_reference).strip(),
		"requesting_org_unit": requesting_org_unit, "allocations": allocations,
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	_authorise_system_caller(actor)

	requisition_reference = cstr(requisition_reference).strip()
	if not requisition_reference or not allocations:
		frappe.throw("A Requisition reference and at least one source allocation are required.")

	item_name = plan_read.resolve_item_doc_name(plan_item_id)
	item = envelope.locked("Annual Plan Item", item_name)
	envelope.check_record_version(item, expected_record_version)
	if item.item_state != "Active" or item.finance_state != "Confirmed":
		frappe.throw("This Plan Item is not currently eligible for a Requisition drawdown.")

	# Validate every requested allocation first, and only write once the
	# whole batch is known good — "every reservation or none" (§7.3's own
	# CheckAndReserveFunding phrasing) can't lean on request-level rollback
	# here, since a direct Python caller (every test in this repo, and any
	# future in-process Requisitions caller) never goes through
	# frappe.handler's own catch-and-rollback wrapper.
	to_create = []
	for spec in allocations:
		allocation_name = frappe.db.get_value(
			"Plan Source Allocation",
			{"allocation_id": cstr(spec.get("plan_source_allocation_id")), "plan_item": item.name},
			"name",
		)
		if not allocation_name:
			authority.not_found()
		allocation = envelope.locked("Plan Source Allocation", allocation_name)
		if allocation.allocation_state != "Active":
			frappe.throw(f"Source allocation {allocation.allocation_id} is not currently drawable.")
		requested_qty = flt(spec.get("quantity"))
		requested_amount = flt(spec.get("amount"))
		if requested_qty <= 0 or requested_amount <= 0:
			frappe.throw("A drawdown quantity and value must both be positive.")
		drawn_qty, drawn_amount = _drawn_totals({allocation.name}).get(allocation.name, (0.0, 0.0))
		if (
			drawn_qty + requested_qty > flt(allocation.quantity) + 1e-6
			or drawn_amount + requested_amount > flt(allocation.indicative_amount) + 1e-6
		):
			frappe.throw(
				f"The requested drawdown exceeds the remaining balance for source "
				f"allocation {allocation.allocation_id}."
			)
		to_create.append((allocation, requested_qty, requested_amount))

	created: list[dict[str, Any]] = []
	for allocation, requested_qty, requested_amount in to_create:
		doc = frappe.get_doc(
			{
				"doctype": "Plan Drawdown Reference",
				"plan_item": item.name, "plan_item_id": item.plan_item_id,
				"allocation": allocation.name,
				"requisition_reference": requisition_reference,
				"requesting_org_unit": requesting_org_unit,
				"quantity": requested_qty, "amount": requested_amount,
				"drawdown_state": "Active",
				"fixture_namespace": cstr(item.fixture_namespace),
			}
		).insert(ignore_permissions=True)
		created.append({"drawdown_reference": doc.name, "record_version": int(doc.record_version or 0)})

	result = {"ok": True, "idempotent": False, "action": "recorded", "drawdown_references": created}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RecordRequisitionDrawdown", payload=payload,
		result=result, document_type="Plan Drawdown Reference", document_name=created[0]["drawdown_reference"],
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def reverse_requisition_drawdown(
	*, drawdown_reference: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	"""§7.4/§8.2 — reversal is atomic and returns the exact quantity/value to
	the source allocation's remaining balance (`_drawn_totals` excludes
	Reversed rows); it never edits the original drawdown row's own recorded
	quantity/amount (§5.3 invariant 20's spirit: recorded evidence is never
	edited, only superseded by a new state)."""
	actor = cstr(user or frappe.session.user)
	payload = {"drawdown_reference": drawdown_reference}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	_authorise_system_caller(actor)

	if not drawdown_reference or not frappe.db.exists("Plan Drawdown Reference", drawdown_reference):
		authority.not_found()
	drawdown = envelope.locked("Plan Drawdown Reference", drawdown_reference)
	envelope.check_record_version(drawdown, expected_record_version)
	if drawdown.drawdown_state != "Active":
		frappe.throw("This drawdown has already been reversed.")

	reversal_reference = f"REV-{drawdown.name}"
	envelope.bump(drawdown, drawdown_state="Reversed", reversal_reference=reversal_reference)
	result = {"ok": True, "idempotent": False, "action": "reversed", "reversal_reference": reversal_reference}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ReverseRequisitionDrawdown", payload=payload,
		result=result, document_type="Plan Drawdown Reference", document_name=drawdown.name,
		actor=actor, fixture_namespace=cstr(drawdown.fixture_namespace),
	)
	return result
