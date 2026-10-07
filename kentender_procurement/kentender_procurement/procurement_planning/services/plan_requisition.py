# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.4.5/§5.4.6/§7.4/§8/§8.2 — Requisition eligibility,
drawdown, scope lock and the correction-request lifecycle (Slice H; Phase
2g execution, plan D9).

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

`AuthoriseRequisitionDrawdown` locks the same stable `Plan Item` root
(`services/scope_lock.guard`) that `ReceivePlanItemCorrectionRequest` and its
dispositions lock, so a concurrently recorded correction hold and a racing
authorisation cannot bypass each other (§4.10, PLN-RI-029); a first
successful drawdown then permanently fixes the item's procurement scope
under that same lock (§5.4.6). §8's codes cover every named condition this
module raises (`PLN_ITEM_SCOPE_LOCKED`, `PLN_ITEM_AUTHORISATION_HELD`,
`PLN_ALLOWANCE_EXCEEDED`, `PLN_CORRECTION_NOT_ACTIVE`); a residual
precondition with no dedicated code (item not Active, funding not current,
malformed allocation shape) still raises a plain `frappe.ValidationError` —
REQ is expected to have already checked eligibility through the read
contract above, so these are defensive, not user-facing, failures (the same
reasoning `authz.not_found()` already uses to sit outside the closed set).
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import budget_gateway, envelope, outcome_event, plan_read, scope_lock
from kentender_procurement.procurement_planning.services import money as money_boundary
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	DEPARTMENTAL_ROLES,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	REQUISITION_CALLER_SITE_WIDE_ROLES,
)
from kentender_procurement.procurement_planning.write_family import planning_command


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


def _drawn_totals(allocation_names: set[str]) -> dict[str, tuple[Decimal, Decimal]]:
	"""Exact drawn quantity/amount per allocation (REQ-CHG-001 v1.11 §5.14):
	stored Currency/Float values are read back through the money boundary
	and summed as `Decimal`, never with a float epsilon."""
	rows = frappe.get_all(
		"Plan Drawdown Reference",
		filters={"allocation": ("in", list(allocation_names) or ("",)), "drawdown_state": "Active"},
		fields=["allocation", "quantity", "amount"],
	)
	totals: dict[str, tuple[Decimal, Decimal]] = {}
	for row in rows:
		qty, amount = totals.get(row.allocation, (Decimal(0), Decimal(0)))
		totals[row.allocation] = (qty + _dec(row.quantity), amount + _dec(row.amount))
	return totals


def _dec(value) -> Decimal:
	converted = money_boundary._to_decimal(value)
	return converted if converted is not None else Decimal(0)


def _qty_text(value) -> str:
	return money_boundary.quantity_text(value)


def _money_text(value) -> str:
	return money_boundary.money_text(value)


def _reservation_rule(item, fiscal_year: str) -> tuple[dict[str, Any], dict[str, Any]]:
	"""REQ-CHG-001 v1.11 §5.4/§5A — the exact verified rule snapshot the item's
	designation, and separately its County treatment, are bound to. Planning
	reads it through the owner's regulatory reference; REQ only consumes the
	result. No APP-wide denominator, target or shortfall is exposed."""
	from kentender_procurement.procurement_planning.services import profiles, readiness

	reference = readiness.reference_for(fiscal_year) or {}
	rules = reference.get("reservation") or {}
	verified = cstr(reference.get("verification_status")) in profiles.VERIFIED_STATUSES
	published = bool(rules.get("published"))
	designation = cstr(item.reservation_category) or readiness.NONE_RESERVATION
	listed = {cstr(r.get("category")) for r in rules.get("categories") or []}
	applies = designation == readiness.NONE_RESERVATION or designation in listed
	snapshot = cstr(reference.get("reference"))
	base = {
		"snapshot_id": snapshot,
		"version_number": int(reference.get("version_number") or 0),
		"verification_status": cstr(reference.get("verification_status")),
		"applies_to_designation": applies,
		"available": bool(snapshot and verified and published and applies),
	}
	is_county = bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county"))
	county_applicable = bool(item.county_resident_reservation)
	county = {
		"applicable": county_applicable,
		"entity_is_county": is_county,
		"snapshot_id": snapshot if county_applicable else "",
		"available": (not county_applicable) or bool(snapshot and verified and is_county and rules.get("county_target_percent") is not None),
	}
	return base, county


def _hold_and_scope(plan_item_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
	state = scope_lock.status(plan_item_id)
	requests = frappe.get_all(
		"Plan Item Correction Request",
		filters={"plan_item_id": plan_item_id, "status": ("in", ("Open", "In progress"))},
		fields=["name", "status", "requisition_reference", "requested_at"],
		order_by="creation asc",
	)
	hold = {
		"held": bool(requests) or state["held"],
		"unresolved_requests": [
			{"correction_request": r.name, "status": r.status, "requisition_reference": cstr(r.requisition_reference), "requested_at": cstr(r.requested_at)}
			for r in requests
		],
	}
	scope = {"locked": state["locked"], "locked_since": state["since"], "first_authorised_requisition": state["first_requisition"]}
	return hold, scope


def get_requisition_eligible_plan_item(*, plan_item_id: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4 `GetRequisitionEligiblePlanItem.v2` — read-only (invariant 1).

	REQ-CHG-001 v1.6 §4.14/§5A — every field that document names is
	enumerated here explicitly (REQ-AC-056): `reservation_category`,
	`lotting_indicator`, `lot_count`, `plan_horizon` (fixed `Single year`, v1.18 §4.6),
	`contributing_org_unit_ids`, `currency`,
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
	total_qty = total_value = total_remaining_qty = total_remaining_value = Decimal(0)
	for a in allocations:
		drawn_qty, drawn_amount = drawn.get(a.name, (Decimal(0), Decimal(0)))
		approved_qty, approved_amount = _dec(a.quantity), _dec(a.indicative_amount)
		remaining_qty = approved_qty - drawn_qty
		remaining_amount = approved_amount - drawn_amount
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
				# REQ-CHG-001 v1.11 §4 — `plan_item_line_id` is this same exact
				# allocation id; Planning has no separate "Plan Item Line"
				# grain. `source_line_id` is the stable Need, or direct DPP
				# entry, paired with `source_origin`.
				"plan_item_line_id": a.allocation_id,
				"source_line_id": cstr(a.need) or a.dpp_entry,
				"source_origin": a.source_origin,
				"dpp_entry": a.dpp_entry,
				"need": cstr(a.need) or None,
				"need_revision": cstr(a.need_revision) or None,
				"organisation_unit": a.organisation_unit,
				"title": entry.get("title") or "",
				"description": entry.get("description") or "",
				"expected_operational_result": entry.get("expected_operational_result") or "",
				"approved_quantity": _qty_text(approved_qty),
				"remaining_quantity": _qty_text(remaining_qty),
				"unit": a.unit,
				"required_by_date": cstr(a.required_by_date),
				"budget_line": a.budget_line,
				"allocated_amount": _money_text(approved_amount),
				"remaining_amount": _money_text(remaining_amount),
			}
		)
		total_qty += approved_qty
		total_value += approved_amount
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

	rule, county_rule = _reservation_rule(item, plan.fiscal_year)
	hold, scope = _hold_and_scope(item.plan_item_id)
	required_by = sorted(d for d in (cstr(a.required_by_date) for a in allocations) if d)
	return {
		"outcome": "OK",
		"eligible": eligible,
		"plan_id": plan.name,
		"plan_reference": plan.plan_reference,
		"version_reference": version.name,
		"plan_version_id": version.name,
		"plan_item_id": item.plan_item_id,
		"plan_item_reference": cstr(frappe.db.get_value("Plan Item", item.plan_item_id, "plan_item_reference")),
		"plan_item_version_id": item.name,
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
		"strategic_objective_id": cstr(item.strategic_objective),
		"objective_path": item.objective_path,
		"strategic_objective_path": item.objective_path,
		"reservation_category": cstr(item.reservation_category),
		"county_resident_reservation": bool(item.county_resident_reservation),
		"reservation_rule": rule,
		"county_rule": county_rule,
		"scope": scope,
		"hold": hold,
		"lotting_indicator": cstr(item.lotting_indicator),
		"lot_count": int(item.lot_count or 0),
		"plan_horizon": cstr(item.plan_horizon),
		"contributing_org_unit_ids": sorted(contributing_org_units),
		"currency": budget_gateway.budget_currency(plan.fiscal_year),
		"award_packages": 1,
		"planned_dates": {f"{m}_date": cstr(item.get(f"baseline_{m}_date")) for m in schedule.MILESTONES},
		# §5.14 — three separate dates: the source-derived Plan completion
		# boundary (the latest source required-by date), the separately
		# calculated estimate, and REQ's own operational date (not here).
		"plan_completion_boundary": required_by[-1] if required_by else "",
		"estimated_completion_date": cstr(item.estimated_completion_date),
		"funding_confirmation_references": [confirmation] if confirmation else [],
		"funding_state": version.funding_state,
		"total_quantity": _qty_text(total_qty),
		"total_value": _money_text(total_value),
		"remaining_quantity": _qty_text(total_remaining_qty),
		"remaining_value": _money_text(total_remaining_value),
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
	for a in allocations:
		units_by_item.setdefault(a.plan_item, set()).add(a.organisation_unit)
		allocation_names_by_item.setdefault(a.plan_item, set()).add(a.name)
	all_allocation_names = {n for names in allocation_names_by_item.values() for n in names}
	drawn = _drawn_totals(all_allocation_names)
	references = dict(
		frappe.get_all("Plan Item", filters={"name": ("in", sorted({c.plan_item_id for c in candidates}))}, fields=["name", "plan_item_reference"], as_list=True)
	)

	rows: list[dict[str, Any]] = []
	for c in candidates:
		if c.name not in confirmed_item_names:
			continue
		units = units_by_item.get(c.name, set())
		if not units:
			continue
		if not site_wide and not (units & scoped_units):
			continue
		remaining_qty = remaining_amount = Decimal(0)
		for a_name in allocation_names_by_item.get(c.name, set()):
			drawn_qty, drawn_amt = drawn.get(a_name, (Decimal(0), Decimal(0)))
			a = next(a for a in allocations if a.name == a_name)
			remaining_qty += _dec(a.quantity) - drawn_qty
			remaining_amount += _dec(a.indicative_amount) - drawn_amt
		if remaining_qty <= 0 or remaining_amount <= 0:
			continue
		version = versions[c.plan_version]
		plan = plans.get(version.annual_plan) or {}
		rows.append(
			{
				"plan_item_id": c.plan_item_id, "plan_item_reference": cstr(references.get(c.plan_item_id)),
				"title": cstr(c.title), "procurement_category": cstr(c.procurement_category),
				"fiscal_year": cstr(plan.get("fiscal_year")), "contributing_org_unit_ids": sorted(units),
				"remaining_quantity": _qty_text(remaining_qty), "remaining_value": _money_text(remaining_amount), "record_version": int(c.record_version or 0),
			}
		)
	return rows


def _strict(value, *, parse, field: str, code: str):
	"""REQ-CHG-001 v1.11 §5.14 — a drawdown value crossing this command is an
	exact decimal string (or int/Decimal); a binary float is refused, never
	rounded or read through `repr`."""
	if isinstance(value, float):
		fail(code, detail={"field": field, "offered": repr(value)})
	return parse(value, field=field)


@planning_command
def authorise_requisition_drawdown(
	*,
	plan_item_id: str,
	requisition_reference: str,
	allocations: list[dict[str, Any]],
	expected_record_version,
	idempotency_key: str,
	requisition_version: str = "",
	correlation_id: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""REQ-CHG-001 v1.11 §9.1 `AuthoriseRequisitionDrawdown` — the one
	canonical Planning drawdown command. One call carries every allocation
	the Requisition draws; every one draws within its own remaining original
	allowance, or none does. Each row is recorded against its own
	allocation's department (a combined item draws from more than one).

	Runs inside the caller's transaction and never commits: the Requisition
	authorisation, this drawdown and scope marker, Budget's reservations, the
	decision, handoff and outbox commit together or roll back together."""
	actor = authz.actor(user)
	payload = {
		"plan_item_id": plan_item_id, "requisition_reference": cstr(requisition_reference).strip(),
		"requisition_version": cstr(requisition_version).strip(), "allocations": allocations,
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

	# §5.4.5/PLN-RI-029 — recheck the hold under the same stable-item guard
	# `ReceivePlanItemCorrectionRequest` records/disposes it with, so a
	# concurrently recorded request cannot be bypassed by a stale read.
	root = scope_lock.guard(item.plan_item_id)
	if root.authorisation_hold:
		fail("PLN_ITEM_AUTHORISATION_HELD", detail={"plan_item_id": item.plan_item_id, "open_requests": int(root.open_correction_requests or 0)})

	# Validate every requested allocation first and only write once the whole
	# batch is known good — all or none, without leaning on a request-level
	# rollback a direct in-process caller never goes through.
	to_create = []
	seen: set[str] = set()
	for spec in allocations:
		allocation_id = cstr(spec.get("plan_source_allocation_id"))
		if allocation_id in seen:
			frappe.throw(f"Source allocation {allocation_id} appears more than once in one drawdown.")
		seen.add(allocation_id)
		allocation_name = frappe.db.get_value("Plan Source Allocation", {"allocation_id": allocation_id, "plan_item": item.name}, "name")
		if not allocation_name:
			authz.not_found()
		allocation = envelope.locked("Plan Source Allocation", allocation_name)
		if allocation.allocation_state != "Active":
			frappe.throw(f"Source allocation {allocation.allocation_id} is not currently drawable.")
		requested_qty = _strict(spec.get("quantity"), parse=money_boundary.parse_quantity, field="quantity", code="PLN_MONEY_PRECISION_INVALID")
		requested_amount = _strict(spec.get("amount"), parse=money_boundary.parse_money, field="amount", code="PLN_MONEY_PRECISION_INVALID")
		drawn_qty, drawn_amount = _drawn_totals({allocation.name}).get(allocation.name, (Decimal(0), Decimal(0)))
		approved_qty, approved_amount = _dec(allocation.quantity), _dec(allocation.indicative_amount)
		if drawn_qty + requested_qty > approved_qty or drawn_amount + requested_amount > approved_amount:
			fail(
				"PLN_ALLOWANCE_EXCEEDED",
				f"The requested drawdown exceeds the remaining balance for source allocation {allocation.allocation_id}.",
				detail={
					"allocation_id": allocation.allocation_id,
					"requested_quantity": _qty_text(requested_qty), "requested_amount": _money_text(requested_amount),
					"remaining_quantity": _qty_text(approved_qty - drawn_qty), "remaining_amount": _money_text(approved_amount - drawn_amount),
				},
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
				"requisition_version": cstr(requisition_version).strip(),
				"correlation_id": cstr(correlation_id).strip(),
				"requesting_org_unit": allocation.organisation_unit,
				"quantity": _qty_text(requested_qty), "amount": _money_text(requested_amount),
				"drawdown_state": "Active",
				"fixture_namespace": cstr(item.fixture_namespace),
			}
		).insert(ignore_permissions=True)
		created.append(
			{
				"plan_source_allocation_id": allocation.allocation_id,
				"drawdown_reference": doc.name,
				"record_version": int(doc.record_version or 0),
			}
		)

	first_lock = scope_lock.lock(root, requisition_reference=requisition_reference)

	result = {
		"ok": True, "idempotent": False, "action": "recorded",
		"drawdowns": created, "scope_locked_by_this_drawdown": bool(first_lock),
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="AuthoriseRequisitionDrawdown", payload=payload,
		result=result, document_type="Plan Drawdown Reference", document_name=created[0]["drawdown_reference"],
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def list_requisition_drawdowns(*, requisition_reference: str, user: str | None = None) -> list[dict[str, Any]]:
	"""REQ-CHG-001 v1.11 §9.1 — the published read a Requisition's revocation
	uses to find its exact originating drawdowns (never a direct table read by
	the caller). Head of Procurement Function only."""
	actor = authz.actor(user)
	_authorise_requisition_authoriser(actor)
	rows = frappe.get_all(
		"Plan Drawdown Reference",
		filters={"requisition_reference": cstr(requisition_reference).strip()},
		fields=["name", "allocation", "quantity", "amount", "drawdown_state", "reversal_reference", "record_version", "requesting_org_unit", "requisition_version"],
		order_by="creation asc",
	)
	allocation_ids = {
		a.name: a.allocation_id
		for a in frappe.get_all("Plan Source Allocation", filters={"name": ("in", [r.allocation for r in rows] or ("",))}, fields=["name", "allocation_id"])
	}
	return [
		{
			"drawdown_reference": r.name,
			"plan_source_allocation_id": allocation_ids.get(r.allocation, ""),
			"organisation_unit": cstr(r.requesting_org_unit),
			"requisition_version": cstr(r.requisition_version),
			"quantity": _qty_text(r.quantity),
			"amount": _money_text(r.amount),
			"drawdown_state": r.drawdown_state,
			"reversal_reference": cstr(r.reversal_reference),
			"record_version": int(r.record_version or 0),
		}
		for r in rows
	]


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


@planning_command
def receive_plan_item_correction_request(
	*,
	plan_item_id: str,
	requisition_reference: str,
	requisition_version: str,
	reason: str,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""REQ-CHG-001 v1.6 §7.4A step 2/3 / PLN-RI-029 — the inbound half of a
	Requisition's upstream-correction route: preserve the exact request as
	one immutable row, hold new drawdown authorisations against the stable
	item, and surface the request to the Procurement Planner as a My Work
	item — recording the request and making the hold effective are atomic,
	under the same stable-item guard `AuthoriseRequisitionDrawdown` rechecks
	it against. This command performs no correction itself; Planning's own
	governed correction/successor mechanism (§7.4A step 4) is a separate,
	later act."""
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

	root = scope_lock.guard(item.plan_item_id)
	doc = frappe.get_doc(
		{
			"doctype": "Plan Item Correction Request",
			"plan_item": item.name, "plan_item_id": item.plan_item_id, "plan_version": item.plan_version,
			"requisition_reference": requisition_reference, "requisition_version": requisition_version,
			"reason": reason, "requested_by": actor, "requested_role": requested_role,
			"requested_at": now_datetime(), "status": "Open", "idempotency_key": idempotency_key,
			"fixture_namespace": cstr(item.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	scope_lock.recompute_hold(root)
	result = {"ok": True, "idempotent": False, "correction_request": doc.name, "status": doc.status}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ReceivePlanItemCorrectionRequest", payload=payload,
		result=result, document_type="Plan Item Correction Request", document_name=doc.name,
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def _authorise_disposition(actor: str, correction_request: str, expected_record_version):
	"""Start/Resolve/Close without change share one Planner-only gate and
	row lock; the role check runs before the existence/version check
	(established precedent: a non-Planner is refused Not-found rather than
	a version-mismatch that would disclose the record exists)."""
	assignment = authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	if not correction_request or not frappe.db.exists("Plan Item Correction Request", correction_request):
		authz.not_found()
	doc = envelope.locked("Plan Item Correction Request", correction_request)
	envelope.check_record_version(doc, expected_record_version)
	return doc, assignment


def start_plan_item_correction(
	*, correction_request: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	"""§7.2 `StartPlanItemCorrection` — Open moves to In progress; the hold
	remains in force (recomputed from the same Open-or-In-progress set)
	while the Planner routes the actual edit to its true source owner (a
	Need/DPP update, or a Plan successor for a Planning-owned fact). This
	command never itself edits the Plan Item."""
	actor = authz.actor(user)
	payload = {"correction_request": correction_request}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	doc, assignment = _authorise_disposition(actor, correction_request, expected_record_version)
	if doc.status != "Open":
		frappe.throw("Only an Open correction request can be started.")

	disposition = frappe.get_doc(
		{
			"doctype": "Plan Item Correction Disposition", "correction_request": doc.name, "action": "Start",
			"actor": actor, "authority_snapshot": authz.authority_snapshot(assignment), "disposed_at": now_datetime(),
			"command_idempotency_key": idempotency_key, "fixture_namespace": cstr(doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	envelope.bump(doc, status="In progress")
	result = {"ok": True, "idempotent": False, "action": "started", "correction_request": doc.name, "disposition": disposition.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="StartPlanItemCorrection", payload=payload, result=result,
		document_type="Plan Item Correction Request", document_name=doc.name, actor=actor, fixture_namespace=cstr(doc.fixture_namespace),
	)
	return result


@planning_command
def resolve_plan_item_correction_request(
	*,
	correction_request: str,
	correcting_plan_version: str,
	replacement_plan_item_id: str = "",
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""§7.2/§5.4.5 `ResolvePlanItemCorrectionRequest` — allowed only once the
	named correcting Plan Version is Active, and only once the disposition
	identifies the replacement eligible lineage (`replacement_plan_item_id`
	defaults to this same stable item — the ordinary case, since stable
	identity carries into a successor per §5.4.4; a name is required only
	when the correction reformed the item under a new identity). Emits
	`PlanItemCorrectionOutcome.v1` (REQ-CHG-001 v1.11 §9.1B) so a fresh
	Draft may be started; the stopped Requisition Version is never itself
	revived here."""
	actor = authz.actor(user)
	correcting_plan_version = cstr(correcting_plan_version).strip()
	replacement_plan_item_id = cstr(replacement_plan_item_id).strip()
	payload = {
		"correction_request": correction_request, "correcting_plan_version": correcting_plan_version,
		"replacement_plan_item_id": replacement_plan_item_id,
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	doc, assignment = _authorise_disposition(actor, correction_request, expected_record_version)
	if doc.status not in ("Open", "In progress"):
		frappe.throw("This correction request has already reached a final outcome.")
	if not correcting_plan_version:
		frappe.throw("Name the exact Active Plan Version that corrects this request.")
	if frappe.db.get_value("Annual Plan Version", correcting_plan_version, "version_status") != "Active":
		fail("PLN_CORRECTION_NOT_ACTIVE", detail={"correcting_plan_version": correcting_plan_version})

	replacement_plan_item_id = replacement_plan_item_id or cstr(doc.plan_item_id)
	if not frappe.db.exists(
		"Annual Plan Item",
		{"plan_item_id": replacement_plan_item_id, "plan_version": correcting_plan_version, "item_state": "Active"},
	):
		frappe.throw("Name the exact Active Plan Item on that Version that replaces this stable item's eligibility.")

	root = scope_lock.guard(cstr(doc.plan_item_id))
	lineage = {"replaced_plan_item": replacement_plan_item_id, "correcting_plan_version": correcting_plan_version}
	disposition = frappe.get_doc(
		{
			"doctype": "Plan Item Correction Disposition", "correction_request": doc.name, "action": "Resolve",
			"actor": actor, "authority_snapshot": authz.authority_snapshot(assignment), "disposed_at": now_datetime(),
			"correcting_plan_version": correcting_plan_version, "replacement_lineage": json.dumps(lineage),
			"command_idempotency_key": idempotency_key, "fixture_namespace": cstr(doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	envelope.bump(
		doc, status="Resolved", resolved_by=actor, resolved_at=now_datetime(),
		resolution_note=f"Resolved against {correcting_plan_version}.",
	)
	hold = scope_lock.recompute_hold(root)

	# REQ-CHG-001 v1.11 §9.1B — the terminal outcome, emitted in this same
	# disposition transaction to the registered consumer.
	outcome_event.deliver(
		outcome_event.build(
			request=doc, disposition=disposition, outcome="Resolved", hold=hold,
			eligibility_revision=int(root.record_version or 0),
			correcting_plan_version=correcting_plan_version,
			lineage=outcome_event.replacement_lineage(correcting_plan_version, replacement_plan_item_id),
		)
	)

	result = {
		"ok": True, "idempotent": False, "action": "resolved", "correction_request": doc.name,
		"disposition": disposition.name, "replacement_plan_item_id": replacement_plan_item_id, "hold": hold,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ResolvePlanItemCorrectionRequest", payload=payload, result=result,
		document_type="Plan Item Correction Request", document_name=doc.name, actor=actor, fixture_namespace=cstr(doc.fixture_namespace),
	)
	return result


def close_plan_item_correction_without_change(
	*, correction_request: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	"""§7.2/§5.4.5 `ClosePlanItemCorrectionWithoutChange` — a reasoned
	no-change outcome; it never itself revives or authorises the stopped
	Requisition (REQ's own amendment defines the requester's permitted
	follow-up for this outcome)."""
	actor = authz.actor(user)
	reason = cstr(reason).strip()
	payload = {"correction_request": correction_request, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	doc, assignment = _authorise_disposition(actor, correction_request, expected_record_version)
	if doc.status not in ("Open", "In progress"):
		frappe.throw("This correction request has already reached a final outcome.")
	if not (20 <= len(reason) <= 1000):
		frappe.throw("A no-change reason of 20–1,000 characters is required.")

	root = scope_lock.guard(cstr(doc.plan_item_id))
	disposition = frappe.get_doc(
		{
			"doctype": "Plan Item Correction Disposition", "correction_request": doc.name, "action": "Close without change",
			"actor": actor, "authority_snapshot": authz.authority_snapshot(assignment), "disposed_at": now_datetime(),
			"reason": reason, "command_idempotency_key": idempotency_key, "fixture_namespace": cstr(doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	envelope.bump(doc, status="Closed without change", resolved_by=actor, resolved_at=now_datetime(), resolution_note=reason)
	hold = scope_lock.recompute_hold(root)

	outcome_event.deliver(
		outcome_event.build(
			request=doc, disposition=disposition, outcome="Closed without change", hold=hold,
			eligibility_revision=int(root.record_version or 0), reason=reason,
		)
	)

	result = {"ok": True, "idempotent": False, "action": "closed_without_change", "correction_request": doc.name, "disposition": disposition.name, "hold": hold}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ClosePlanItemCorrectionWithoutChange", payload=payload, result=result,
		document_type="Plan Item Correction Request", document_name=doc.name, actor=actor, fixture_namespace=cstr(doc.fixture_namespace),
	)
	return result


def correction_request_facts(*, correction_request: str = "", requisition_reference: str = "") -> list[dict[str, Any]]:
	"""REQ-CHG-001 v1.11 §7.4B/§9.1B — the published, read-only facts of the
	Planning correction requests a Requisition raised: exact lineage, owner
	status and the dispositions so far. Requisitions uses it to authenticate
	an outcome event and to render its stopped page; it never reads these
	tables itself. No APP-wide figure is included."""
	filters: dict[str, Any] = {}
	if correction_request:
		filters["name"] = cstr(correction_request)
	if requisition_reference:
		filters["requisition_reference"] = cstr(requisition_reference)
	if not filters:
		return []
	rows = frappe.get_all(
		"Plan Item Correction Request", filters=filters,
		fields=["name", "plan_item_id", "plan_item", "plan_version", "requisition_reference", "requisition_version", "reason", "requested_by", "requested_role", "requested_at", "status", "resolved_by", "resolved_at", "resolution_note"],
		order_by="creation asc",
	)
	out = []
	for row in rows:
		dispositions = frappe.get_all(
			"Plan Item Correction Disposition", filters={"correction_request": row.name},
			fields=["name", "action", "actor", "disposed_at", "correcting_plan_version", "reason"], order_by="creation asc",
		)
		out.append(
			{
				"correction_request": row.name, "plan_item_id": row.plan_item_id, "plan_item_version_id": row.plan_item, "plan_version_id": row.plan_version,
				"requisition_reference": row.requisition_reference, "requisition_version": row.requisition_version, "reason": row.reason,
				"requested_by": row.requested_by, "requested_role": row.requested_role, "requested_at": cstr(row.requested_at), "status": row.status,
				"resolved_by": cstr(row.resolved_by), "resolved_at": cstr(row.resolved_at), "resolution_note": cstr(row.resolution_note),
				"dispositions": [
					{"disposition": d.name, "action": d.action, "actor": d.actor, "disposed_at": cstr(d.disposed_at), "correcting_plan_version": cstr(d.correcting_plan_version), "reason": cstr(d.reason)}
					for d in dispositions
				],
			}
		)
	return out
