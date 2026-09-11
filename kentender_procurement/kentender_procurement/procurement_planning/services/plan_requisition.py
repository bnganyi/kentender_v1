# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §7.4/§8/§8.2 — Requisition eligibility (Slice H).

`GetRequisitionEligiblePlanItem.v2` is the published, read-only contract
Procurement Requisitions calls to decide whether — and how much of — a Plan
Item it may draw against (invariant 1: it creates nothing). Planning owns
the balance ledger (`Plan Drawdown Reference`) Requisitions posts to.

REQ-CHG-001 v1.6 (2026-09-07) is that live caller: the read gate widened
from Procurement Planner/Auditor-only to every registered Requisitions
role (`planning_roles.REQUISITION_CALLER_ROLES`), Organisation-Unit-scoped
roles gated to the Plan Item's own contributing departments; the two
drawdown commands moved from a System-Manager placeholder gate (closing
FU-07) to the Head of Procurement Function, the office REQ-CHG-001 v1.6
§9.1A names as the sole authoriser of a Requisition's drawdown.

§9's twenty-one error codes are Planning's own UI-facing vocabulary; a
programmatic contract call from a sibling module is not a Planning screen,
so `record_requisition_drawdown`'s balance/state failures raise a plain
`frappe.ValidationError` instead of forcing an unrelated §9 code onto a
condition the contract's own author never named one for (§9's own docstring:
"an invented code is a defect in the caller") — the same reasoning
`authz.not_found()` already uses to sit outside that closed set.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.services import envelope, plan_read
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	DEPARTMENTAL_ROLES,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	REQUISITION_CALLER_SITE_WIDE_ROLES,
)


def _authorise_requisition_reader(actor: str, *, contributing_org_units: set[str]) -> None:
	"""REQ-CHG-001 v1.6 §5A/§8 (closes part of FU-07) — every registered
	Requisitions-caller role may read the eligibility projection: the two
	Site-wide roles unconditionally, and the two Organisation-Unit-scoped
	roles only when their assignment covers one of this Plan Item's own
	contributing departments — never a department the Plan Item does not
	name (mirrors §7.5 invariant 1 at the read boundary, not just at
	drawdown)."""
	if authz.is_technical(actor):
		return
	for role in REQUISITION_CALLER_SITE_WIDE_ROLES:
		if authz.can_read_site(role, actor):
			return
	for role in DEPARTMENTAL_ROLES:
		scope = authz.permitted_ou_scopes(actor, role)
		if scope and scope & contributing_org_units:
			return
	authz.not_found()


def _authorise_requisition_authoriser(actor: str) -> None:
	"""§9.1/§9.1A — Head of Procurement Function is the sole caller of the
	two drawdown-writing commands (closes Planning FU-07: these were
	System-Manager-gated only because no Requisitions role vocabulary
	existed here yet)."""
	authz.require_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor)


def _requisition_item_name(plan_item_id: str) -> str:
	"""Invariant 18 / §4.4 — "An Active item remains eligible until an
	acknowledged successor changes it"; "the Active predecessor remains
	operational until the correction or successor is approved, published
	and acknowledged". While a Draft successor is open the same
	`plan_item_id` names two docs, and `plan_read.resolve_item_doc_name`'s
	"open successor wins" precedence is the Planning *editor's* rule, not
	this contract's: the successor's copy is Draft with Draft allocations, so
	resolving to it made every OU-scoped Requisitions reader `Not found`
	(no Active allocation → no contributing unit; live 2026-09-11, Grace
	Wanjiku on PPI-MOH-2027-001 with PLN-MOH-2027-001-V2 awaiting statutory
	approval) and would have posted drawdowns against the wrong copy. The
	Active copy wins here; with none (never activated, superseded), the
	editor's precedence still decides which Draft/historical copy answers
	"not eligible"."""
	active = frappe.get_all(
		"Annual Plan Item", filters={"plan_item_id": cstr(plan_item_id), "item_state": "Active"}, pluck="name", limit_page_length=2,
	)
	if len(active) == 1:
		return active[0]
	return plan_read.resolve_item_doc_name(plan_item_id)


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
	"""§7.4 `GetRequisitionEligiblePlanItem.v2` — read-only (invariant 1).

	REQ-CHG-001 v1.6 §4.14/§5A — every field that document names is
	enumerated here explicitly (REQ-AC-056): `reservation_category`,
	`lotting_indicator`, `lot_count`, `plan_horizon`,
	`multi_year_justification`, `contributing_org_unit_ids`, `currency`,
	`award_packages`, and per source `plan_item_line_id`/`source_line_id`.
	"""
	actor = authz.actor(user)
	name = _requisition_item_name(plan_item_id)
	item = frappe.get_doc("Annual Plan Item", name)
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	contributing_org_units = set(
		frappe.get_all("Plan Source Allocation", filters={"plan_item": item.name, "allocation_state": "Active"}, pluck="organisation_unit")
	)
	_authorise_requisition_reader(actor, contributing_org_units=contributing_org_units)

	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item.name, "allocation_state": "Active"},
		fields=[
			"name", "allocation_id", "dpp_entry", "source_origin", "need", "need_revision",
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
				# REQ-CHG-001 v1.6 §5.1/§5.3 — `plan_item_line_id` is this same
				# allocation id; Planning has no separate "Plan Item Line" grain
				# (the line IS the source allocation). `source_line_id` mirrors
				# dpp_lifecycle.py's own submission-snapshot formula exactly.
				"plan_item_line_id": a.allocation_id,
				"source_line_id": cstr(a.need) or a.dpp_entry,
				"source_origin": a.source_origin,
				"dpp_entry": a.dpp_entry if a.source_origin == "Direct departmental requirement" else "",
				"need": cstr(a.need) or None,
				"need_revision": cstr(a.need_revision) or None,
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

	# §7.4 — "Finance evidence remains current": the plan-level confirmation
	# on the Version (§4.11); there is no per-item finance state or
	# reservation (Planning holds none).
	funding_confirmed = version.funding_state == "Confirmed"
	confirmation = frappe.db.get_value(
		"Plan Finance Decision",
		{"task": ("in", frappe.get_all("Plan Finance Task", filters={"plan_version": version.name}, pluck="name") or ("",)), "decision": "Confirm plan funding"},
		"decision_reference", order_by="decided_at desc",
	)
	# §7.4/invariant 18: eligibility follows the item's own current state —
	# an open (unacknowledged) successor proposing removal never changes it;
	# only an acknowledged one does, and that already moves this copy off
	# "Active" (Superseded) or "Removed in successor". §7.1's Need-withdrawal
	# clause needs no separate check here: Needs itself refuses to publish a
	# withdrawal while an Active Plan dependency exists.
	eligible = (
		item.item_state == "Active"
		and funding_confirmed
		and total_remaining_qty > 0
		and total_remaining_value > 0
	)
	from kentender_procurement.procurement_planning.services import schedule

	return {
		"outcome": "OK",
		"eligible": eligible,
		"plan_reference": plan.plan_reference,
		"version_reference": version.name,
		"plan_item_id": item.plan_item_id,
		"record_version": int(item.record_version or 0),
		"fiscal_year": plan.fiscal_year,
		"requirement_type": item.requirement_type,
		# REQ-CHG-001 v1.6 §5.2 — "requirement_title ... Initially inherited
		# from Planning". Found missing 2026-09-07 while wiring Requisitions'
		# own PrepareITEquipmentRequisition; adding here rather than inventing
		# a second, independent title on the Requisitions side (§2.2).
		"title": item.title,
		"procurement_category": cstr(item.procurement_category),
		"procurement_method": item.procurement_method,
		"strategic_objective": item.strategic_objective,
		"objective_path": item.objective_path,
		"strategic_objective_path": item.objective_path,
		"reservation_category": cstr(item.reservation_category),
		"lotting_indicator": cstr(item.lotting_indicator),
		"lot_count": int(item.lot_count or 0),
		"plan_horizon": cstr(item.plan_horizon),
		"multi_year_justification": cstr(item.multi_year_justification),
		"contributing_org_unit_ids": sorted(contributing_org_units),
		"currency": "KES",
		"award_packages": 1,
		"planned_dates": {f"{m}_date": cstr(item.get(f"baseline_{m}_date")) for m in schedule.MILESTONES},
		"forecast_dates": {f"{m}_date": cstr(item.get(f"forecast_{m}_date")) for m in schedule.MILESTONES},
		"funding_confirmation_references": [confirmation] if confirmation else [],
		"funding_state": version.funding_state,
		"total_quantity": total_qty,
		"total_value": total_value,
		"remaining_quantity": total_remaining_qty,
		"remaining_value": total_remaining_value,
		"sources": sources,
		"evaluated_at": cstr(now_datetime()),
	}


def list_requisition_eligible_plan_items(*, user: str | None = None) -> list[dict[str, Any]]:
	"""REQ-CHG-001 v1.6 §10.1 `GetRequisitionWorkspace` — every Plan Item
	this actor may start a Requisition against: `item_state == "Active"`,
	plan-level funding confirmed, and at least one Active Plan Source
	Allocation with a positive remaining balance, restricted to the
	actor's own readable Organisation Units for the two OU-scoped roles
	(mirrors `_authorise_requisition_reader`'s per-item check, applied here
	across every candidate item rather than one already-named item)."""
	actor = authz.actor(user)
	site_wide = False
	if authz.is_technical(actor):
		site_wide = True
	else:
		for role in REQUISITION_CALLER_SITE_WIDE_ROLES:
			if authz.can_read_site(role, actor):
				site_wide = True
				break
	scoped_units: set[str] = set()
	if not site_wide:
		for role in DEPARTMENTAL_ROLES:
			scoped_units |= authz.permitted_ou_scopes(actor, role)
		if not scoped_units:
			return []

	candidates = frappe.get_all(
		"Annual Plan Item",
		filters={"item_state": "Active"},
		fields=["name", "plan_item_id", "title", "procurement_category", "plan_version", "record_version"],
		order_by="creation asc",
		limit_page_length=0,
	)
	if not candidates:
		return []
	versions = {
		v.name: v
		for v in frappe.get_all(
			"Annual Plan Version", filters={"name": ("in", [c.plan_version for c in candidates])},
			fields=["name", "annual_plan", "funding_state"],
		)
	}
	confirmed_item_names = [c.name for c in candidates if versions.get(c.plan_version, {}).get("funding_state") == "Confirmed"]
	if not confirmed_item_names:
		return []
	plans = {
		p.name: p
		for p in frappe.get_all(
			"Annual Plan", filters={"name": ("in", [versions[v].annual_plan for v in {c.plan_version for c in candidates if c.name in confirmed_item_names}])},
			fields=["name", "fiscal_year"],
		)
	}
	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": ("in", confirmed_item_names), "allocation_state": "Active"},
		fields=["name", "plan_item", "organisation_unit", "quantity", "indicative_amount"],
	)
	units_by_item: dict[str, set[str]] = {}
	allocation_names_by_item: dict[str, set[str]] = {}
	approved_by_item: dict[str, tuple[float, float]] = {}
	for a in allocations:
		units_by_item.setdefault(a.plan_item, set()).add(a.organisation_unit)
		allocation_names_by_item.setdefault(a.plan_item, set()).add(a.name)
		qty, amount = approved_by_item.get(a.plan_item, (0.0, 0.0))
		approved_by_item[a.plan_item] = (qty + flt(a.quantity), amount + flt(a.indicative_amount))
	all_allocation_names = {n for names in allocation_names_by_item.values() for n in names}
	drawn = _drawn_totals(all_allocation_names)

	rows: list[dict[str, Any]] = []
	for c in candidates:
		if c.name not in confirmed_item_names:
			continue
		units = units_by_item.get(c.name, set())
		if not units:
			continue
		if not site_wide and not (units & scoped_units):
			continue
		remaining_qty = remaining_amount = 0.0
		for a_name in allocation_names_by_item.get(c.name, set()):
			drawn_qty, drawn_amt = drawn.get(a_name, (0.0, 0.0))
			a = next(a for a in allocations if a.name == a_name)
			remaining_qty += flt(a.quantity) - drawn_qty
			remaining_amount += flt(a.indicative_amount) - drawn_amt
		if remaining_qty <= 0 or remaining_amount <= 0:
			continue
		version = versions[c.plan_version]
		plan = plans.get(version.annual_plan) or {}
		rows.append(
			{
				"plan_item_id": c.plan_item_id, "title": cstr(c.title), "procurement_category": cstr(c.procurement_category),
				"fiscal_year": cstr(plan.get("fiscal_year")), "contributing_org_unit_ids": sorted(units),
				"remaining_quantity": remaining_qty, "remaining_value": remaining_amount, "record_version": int(c.record_version or 0),
			}
		)
	return rows


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
	actor = authz.actor(user)
	payload = {
		"plan_item_id": plan_item_id, "requisition_reference": cstr(requisition_reference).strip(),
		"requesting_org_unit": requesting_org_unit, "allocations": allocations,
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	_authorise_requisition_authoriser(actor)

	requisition_reference = cstr(requisition_reference).strip()
	if not requisition_reference or not allocations:
		frappe.throw("A Requisition reference and at least one source allocation are required.")

	item_name = _requisition_item_name(plan_item_id)
	item = envelope.locked("Annual Plan Item", item_name)
	envelope.check_record_version(item, expected_record_version)
	if item.item_state != "Active" or frappe.db.get_value("Annual Plan Version", item.plan_version, "funding_state") != "Confirmed":
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
			authz.not_found()
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
	actor = authz.actor(user)
	payload = {"drawdown_reference": drawdown_reference}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	_authorise_requisition_authoriser(actor)

	if not drawdown_reference or not frappe.db.exists("Plan Drawdown Reference", drawdown_reference):
		authz.not_found()
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


# --------------------------------------------------------------------------
# §7.4A — the inbound half of a Requisition's upstream-correction route
# --------------------------------------------------------------------------


def _authorise_correction_requester(actor: str, *, contributing_org_units: set[str]) -> str:
	"""§7.4A step 1 — Head of User Department for one of the Plan Item's own
	contributing departments, or Head of Procurement Function (Site-wide).
	Returns the exact role exercised, for the immutable record."""
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	if authorise_record(user=actor, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, organisation_unit="", purpose=PURPOSE_COMMAND).allowed:
		return ROLE_HEAD_OF_PROCUREMENT_FUNCTION
	scope = authz.permitted_ou_scopes(actor, ROLE_HEAD_OF_USER_DEPARTMENT)
	if scope and scope & contributing_org_units:
		return ROLE_HEAD_OF_USER_DEPARTMENT
	authz.not_found()
	return ""


def receive_plan_item_correction_request(
	*,
	plan_item_id: str,
	requisition_reference: str,
	requisition_version: str,
	reason: str,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""REQ-CHG-001 v1.6 §7.4A step 2/3 — the inbound half of a Requisition's
	upstream-correction route: preserve the exact request as one immutable
	row and surface it to the Procurement Planner as a My Work item. This
	command performs no correction itself; Planning's own governed
	correction/successor mechanism (§7.4A step 4) is a separate, later act."""
	actor = authz.actor(user)
	payload = {
		"plan_item_id": plan_item_id, "requisition_reference": cstr(requisition_reference).strip(),
		"requisition_version": cstr(requisition_version).strip(), "reason": cstr(reason).strip(),
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	reason = cstr(reason).strip()
	if len(reason) < 20 or len(reason) > 1000:
		frappe.throw("A correction reason of 20–1,000 characters is required.")
	requisition_reference = cstr(requisition_reference).strip()
	requisition_version = cstr(requisition_version).strip()
	if not requisition_reference or not requisition_version:
		frappe.throw("A Requisition reference and Version are required.")

	item_name = _requisition_item_name(plan_item_id)
	item = frappe.get_doc("Annual Plan Item", item_name)
	contributing_org_units = set(
		frappe.get_all("Plan Source Allocation", filters={"plan_item": item.name, "allocation_state": "Active"}, pluck="organisation_unit")
	)
	requested_role = _authorise_correction_requester(actor, contributing_org_units=contributing_org_units)

	doc = frappe.get_doc(
		{
			"doctype": "Plan Item Correction Request",
			"plan_item": item.name, "plan_item_id": item.plan_item_id,
			"requisition_reference": requisition_reference, "requisition_version": requisition_version,
			"reason": reason, "requested_by": actor, "requested_role": requested_role,
			"requested_at": now_datetime(), "status": "Open", "idempotency_key": idempotency_key,
			"fixture_namespace": cstr(item.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	result = {"ok": True, "idempotent": False, "correction_request": doc.name, "status": doc.status}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ReceivePlanItemCorrectionRequest", payload=payload,
		result=result, document_type="Plan Item Correction Request", document_name=doc.name,
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def resolve_plan_item_correction_request(
	*, correction_request: str, resolution_note: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	"""§7.4A step 4 — the Procurement Planner records that Planning's own
	governed correction/successor route has been applied. This command does
	not itself edit the Plan Item; it closes the inbound request once the
	real correction (a Plan successor, or a correction to a still-open
	Version) has happened through Planning's ordinary commands."""
	actor = authz.actor(user)
	payload = {"correction_request": correction_request, "resolution_note": cstr(resolution_note).strip()}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)

	if not correction_request or not frappe.db.exists("Plan Item Correction Request", correction_request):
		authz.not_found()
	doc = envelope.locked("Plan Item Correction Request", correction_request)
	envelope.check_record_version(doc, expected_record_version)
	if doc.status != "Open":
		frappe.throw("This correction request has already been resolved.")
	resolution_note = cstr(resolution_note).strip()
	if len(resolution_note) < 10:
		frappe.throw("A resolution note of at least 10 characters is required.")

	envelope.bump(doc, status="Resolved", resolved_by=actor, resolved_at=now_datetime(), resolution_note=resolution_note)
	result = {"ok": True, "idempotent": False, "action": "resolved", "correction_request": doc.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ResolvePlanItemCorrectionRequest", payload=payload,
		result=result, document_type="Plan Item Correction Request", document_name=doc.name,
		actor=actor, fixture_namespace=cstr(doc.fixture_namespace),
	)
	return result
