# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Funding check and reservation — BUD-UI-06 / BUD-FR-009–016."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate, today

from kentender_budget.services.budget_authorization import (
	CAP_BUDGET_RESERVE,
	require_budget_capability,
)
from kentender_budget.services.budget_contracts import resolve_scoped_entity
from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_permissions import (
	ROLE_AUDITOR,
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	entity_for_user,
	require_any_role,
)
from kentender_budget.services.budget_reference import allocate_reservation_reference

LINEAGE_NOTE = (
	"This reservation follows the same requirement through Planning and Tendering. "
	"Those stages will not create additional funding holds."
)

DECISION_AVAILABLE = "Funding available"
DECISION_INSUFFICIENT = "Insufficient funding"


def _resolve_line(budget_line: str) -> Any:
	key = (budget_line or "").strip()
	if not key:
		frappe.throw(_("Budget Line is required"))
	name = key
	if not frappe.db.exists("Budget Line", name):
		name = frappe.db.get_value("Budget Line", {"generated_reference": key}, "name")
	if not name:
		frappe.throw(_("Budget Line not found"), frappe.DoesNotExistError)
	return frappe.get_doc("Budget Line", name)


def _active_budget(budget_name: str) -> Any:
	bud = frappe.get_doc("Budget", budget_name)
	if bud.status != "Active":
		frappe.throw(_("Budget must be Active for funding check"))
	return bud


def _available(line) -> float:
	return flt(line.approved_amount) - flt(line.amount_reserved) - flt(line.amount_committed)


def demand_doctype_available() -> bool:
	"""DEM-INT-009 — Budget Demand reads follow DocType availability, not CONSUMERS_LIVE."""
	return bool(frappe.db.exists("DocType", "Demand"))


def _demand_context_fallback(key: str = "") -> dict[str, str]:
	code = (key or "").strip()
	return {
		"id": "",
		"code": code,
		"name": code,
		"owner_org_unit": "",
		"status": "",
		"current_stage": "",
		# Compat aliases used by reserve payload builders.
		"demand_code": code,
		"demand_title": code,
	}


def _demand_context(demand: str | None) -> dict[str, str]:
	"""DEM-INT-009 — resolve MVP Demand by document name or demand_code."""
	key = (demand or "").strip()
	if not key:
		return _demand_context_fallback("")
	if not demand_doctype_available():
		return _demand_context_fallback(key)

	name = key if frappe.db.exists("Demand", key) else ""
	if not name:
		name = frappe.db.get_value("Demand", {"demand_code": key}, "name") or ""
	if not name:
		return _demand_context_fallback(key)

	doc = frappe.get_doc("Demand", name)
	code = (getattr(doc, "demand_code", None) or "").strip() or name
	title = (doc.title or "").strip() or code
	return {
		"id": name,
		"code": code,
		"name": title,
		"owner_org_unit": (getattr(doc, "owner_org_unit", None) or "").strip(),
		"status": (doc.status or "").strip(),
		"current_stage": (getattr(doc, "current_stage", None) or "").strip(),
		"demand_code": code,
		"demand_title": title,
	}


def check_funding(
	budget_line: str | None = None,
	requested_amount: float | None = None,
	demand: str | None = None,
	procuring_entity: str | None = None,
	_locked_line: Any = None,
) -> dict[str, Any]:
	"""Read-only funding check (BUD-AC-010). Does not mutate balances.

	`_locked_line` is internal-only: `reserve_funding` passes its own
	already-`FOR UPDATE`-locked, freshly-read Budget Line doc here so this
	check reuses those balances instead of re-reading the line with a plain
	(non-locking) SELECT — which could return stale balances under
	REPEATABLE READ if this same DB transaction already did an earlier plain
	read of the row (see the comment in `reserve_funding`). External/direct
	callers never pass this and get the normal fresh read.
	"""
	require_any_role(
		ROLE_VIEWER,
		ROLE_OFFICER,
		ROLE_REVIEWER,
		ROLE_AUTHORITY,
		ROLE_AUDITOR,
		"System Manager",
		"Procurement Approval Authority",
	)
	line = _locked_line if _locked_line is not None else _resolve_line(budget_line or "")
	bud = _active_budget(line.budget)
	pe = resolve_scoped_entity(procuring_entity or entity_for_user() or None)
	if pe and bud.procuring_entity and pe != bud.procuring_entity:
		frappe.throw(_("Not permitted for this procuring entity"), frappe.PermissionError)
	if not line.is_active:
		frappe.throw(_("Budget Line must be active"))

	requested = flt(requested_amount)
	if requested <= 0:
		frappe.throw(_("Requested amount must be greater than zero"))

	currency = bud.currency or line.currency or "KES"
	available_before = _available(line)
	available_after = available_before - requested
	sufficient = available_before >= requested
	shortfall = 0.0 if sufficient else (requested - available_before)

	demand_ctx = _demand_context(demand)
	decision = DECISION_AVAILABLE if sufficient else DECISION_INSUFFICIENT

	return {
		"decision": decision,
		"decision_kind": "available" if sufficient else "insufficient",
		"sufficient": sufficient,
		"budget": {
			"id": bud.name,
			"code": bud.generated_reference or "",
			"name": bud.title or bud.generated_reference or "",
			"status": bud.status,
			"fiscal_period": bud.fiscal_period or "",
			"currency": currency,
			"procuring_entity": bud.procuring_entity or "",
		},
		"budget_line": {
			"id": line.name,
			"code": line.generated_reference or "",
			"name": line.title or line.generated_reference or "",
			"primary_target_code": line.primary_target_code or "",
			"primary_target_name": line.primary_target_name or "",
		},
		"demand": demand_ctx,
		"requested_amount": requested,
		"available_before": available_before,
		"available_after": max(0.0, available_after) if sufficient else available_before,
		"shortfall": shortfall,
		"requested_display": format_kes_full(requested, currency=currency),
		"available_before_display": format_kes_full(available_before, currency=currency),
		"available_after_display": format_kes_full(
			max(0.0, available_after) if sufficient else available_before, currency=currency
		),
		"shortfall_display": format_kes_full(shortfall, currency=currency) if shortfall else "",
		"lineage_note": LINEAGE_NOTE,
		"capabilities": {
			"can_reserve": sufficient,
			"can_select_line": True,
			"read_only_check": True,
		},
	}


def reserve_funding(
	budget_line: str | None = None,
	plan_item_code: str | None = None,
	demand_name: str | None = None,
	requested_amount: float | None = None,
	idempotency_key: str | None = None,
	actor: str | None = None,
	procuring_entity: str | None = None,
	generated_reference: str | None = None,
) -> dict[str, Any]:
	"""Create a Funding Reservation once a Procurement Plan Item's funding request
	has been confirmed complete (BUD-FR-009/010) — one task before Requisition,
	never at Departmental Need submission, approval or acceptance. Budget does
	not itself validate Plan Item completeness (that gate belongs to Procurement
	Planning); this contract trusts the caller and records `plan_item_code` as
	the reservation's primary identity and idempotency/duplicate-prevention key
	(BUD-FR-011/012). `demand_name` is optional secondary lineage only, never
	required and never the correlation key.
	"""
	require_any_role(
		ROLE_OFFICER,
		ROLE_REVIEWER,
		ROLE_AUTHORITY,
		"System Manager",
	)
	key = (idempotency_key or "").strip()
	if key:
		existing = frappe.db.get_value(
			"Funding Reservation", {"idempotency_key": key}, "name"
		)
		if existing:
			doc = frappe.get_doc("Funding Reservation", existing)
			return _reservation_result(doc, reused=True)

	line = _resolve_line(budget_line or "")
	bud = frappe.get_doc("Budget", line.budget)
	# BUD-CHG-001 §8 — Finance Confirmation Officer capability, scoped to this Budget's PE.
	require_budget_capability(CAP_BUDGET_RESERVE, bud)
	# Row lock against parallel oversubscription (BUD-FR-011/012, BUD-AC-011).
	# A locking read of the balance columns themselves is required here — not
	# `line.reload()` (a plain SELECT). Under MariaDB's default REPEATABLE READ
	# isolation, the plain reads already done above (role/capability checks)
	# establish this transaction's snapshot; a plain reload after FOR UPDATE can
	# still return pre-lock stale balances even though the lock itself is held
	# correctly. Only a locking SELECT is guaranteed to return latest-committed
	# data regardless of when the snapshot was established.
	locked = frappe.db.sql(
		"SELECT amount_reserved, amount_committed FROM `tabBudget Line` WHERE name=%s FOR UPDATE",
		(line.name,),
		as_dict=True,
	)[0]
	line.amount_reserved = locked.amount_reserved
	line.amount_committed = locked.amount_committed

	plan_item = (plan_item_code or "").strip()
	if not plan_item:
		frappe.throw(_("Plan Item is required for reservation"))

	check = check_funding(
		budget_line=line.name,
		requested_amount=requested_amount,
		demand=demand_name,
		procuring_entity=procuring_entity,
		_locked_line=line,
	)
	if not check["sufficient"]:
		from kentender_budget.services.budget_notification_service import (
			notify_funding_insufficient,
		)

		bud_for_notify = frappe.get_doc("Budget", line.budget)
		notify_funding_insufficient(
			budget_doc=bud_for_notify,
			budget_line_code=line.generated_reference or line.name,
			demand_code=plan_item
			or (demand_name or "").strip()
			or (check.get("demand") or {}).get("demand_code")
			or "",
			requested_amount=flt(requested_amount),
			shortfall_display=check.get("shortfall_display") or "",
		)
		frappe.throw(
			_("Insufficient funding. Shortfall: {0}").format(check["shortfall_display"]),
			title=_("Insufficient funding"),
		)

	demand_ctx = check["demand"]
	demand_code = demand_ctx["demand_code"] or (demand_name or "").strip()
	demand_title = demand_ctx["demand_title"] or demand_code

	# One active reservation per Plan Item + line (no duplicate holds).
	dup = frappe.db.get_value(
		"Funding Reservation",
		{
			"budget_line": line.name,
			"plan_item_code": plan_item,
			"status": ["in", ["Reserved", "Partially converted"]],
		},
		"name",
	)
	if dup and not key:
		doc = frappe.get_doc("Funding Reservation", dup)
		return _reservation_result(doc, reused=True)

	requested = flt(requested_amount)
	preferred = (generated_reference or "").strip()
	if preferred and not frappe.db.exists(
		"Funding Reservation", {"generated_reference": preferred}
	):
		ref = preferred
	else:
		ref = allocate_reservation_reference(bud.procuring_entity)
	idem = key or f"{plan_item}:{line.generated_reference}:{flt(requested):.2f}"

	# Re-check idempotency after lock (race).
	existing2 = frappe.db.get_value("Funding Reservation", {"idempotency_key": idem}, "name")
	if existing2:
		doc = frappe.get_doc("Funding Reservation", existing2)
		return _reservation_result(doc, reused=True)

	doc = frappe.get_doc(
		{
			"doctype": "Funding Reservation",
			"budget": bud.name,
			"budget_line": line.name,
			"generated_reference": ref,
			"status": "Reserved",
			"event_date": getdate(today()),
			"plan_item_code": plan_item,
			"demand_code": demand_code,
			"demand_title": demand_title,
			"original_amount": requested,
			"remaining_reserved": requested,
			"currency": bud.currency or "KES",
			"idempotency_key": idem,
		}
	)
	doc.insert(ignore_permissions=True)

	# Bump line reserved balance.
	new_reserved = flt(line.amount_reserved) + requested
	frappe.db.set_value(
		"Budget Line",
		line.name,
		"amount_reserved",
		new_reserved,
		update_modified=True,
	)

	# BUD-SUP-005 — live mutation evidence for Funding Lifecycle / Audit History.
	from kentender_budget.services.budget_audit_contracts import EVENT_RESERVED, safe_record_event

	safe_record_event(
		budget=bud.name,
		event_type=EVENT_RESERVED,
		record_doctype="Funding Reservation",
		record_code=ref,
		budget_line=line.name,
		after_summary=format_kes_full(requested, currency=bud.currency or "KES"),
		source_reference=plan_item,
		actor=(actor or frappe.session.user or "System").strip(),
		actor_kind="user",
	)

	if actor:
		doc.flags.reservation_actor = actor
	doc.reload()
	return _reservation_result(doc, reused=False)


def _reservation_result(doc, *, reused: bool) -> dict[str, Any]:
	currency = doc.currency or "KES"
	return {
		"ok": True,
		"reused": reused,
		"reservation_id": doc.name,
		"reservation_code": doc.generated_reference,
		"status": doc.status,
		"budget_line": doc.budget_line,
		"demand_code": doc.demand_code,
		"original_amount": flt(doc.original_amount),
		"remaining_reserved": flt(doc.remaining_reserved),
		"original_amount_display": format_kes_full(doc.original_amount, currency=currency),
		"remaining_reserved_display": format_kes_full(doc.remaining_reserved, currency=currency),
		"idempotency_key": doc.idempotency_key or "",
	}


def _resolve_reservation(reservation: str) -> Any:
	key = (reservation or "").strip()
	if not key:
		frappe.throw(_("Reservation is required"))
	name = key if frappe.db.exists("Funding Reservation", key) else ""
	if not name:
		name = frappe.db.get_value("Funding Reservation", {"generated_reference": key}, "name") or ""
	if not name:
		frappe.throw(_("Reservation {0} not found").format(key), frappe.DoesNotExistError)
	return frappe.get_doc("Funding Reservation", name)


def release_reservation(
	reservation: str | None = None,
	*,
	reason: str | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""Release an active Funding Reservation, restoring the line's reserved balance."""
	doc = _resolve_reservation(reservation or "")
	bud = frappe.get_doc("Budget", doc.budget)
	# BUD-CHG-001 §8 — same Finance Confirmation Officer capability that creates a
	# reservation also releases it; scoped to this Budget's PE.
	require_budget_capability(CAP_BUDGET_RESERVE, bud)

	if doc.status in ("Released", "Cancelled"):
		return _reservation_result(doc, reused=True)

	remaining = flt(doc.remaining_reserved)
	doc.status = "Released"
	doc.remaining_reserved = 0
	doc.save(ignore_permissions=True)
	if remaining and doc.budget_line:
		cur = flt(frappe.db.get_value("Budget Line", doc.budget_line, "amount_reserved"))
		frappe.db.set_value(
			"Budget Line",
			doc.budget_line,
			"amount_reserved",
			max(0.0, cur - remaining),
			update_modified=True,
		)

	from kentender_budget.services.budget_audit_contracts import EVENT_RELEASED, safe_record_event

	safe_record_event(
		budget=bud.name,
		event_type=EVENT_RELEASED,
		record_doctype="Funding Reservation",
		record_code=doc.generated_reference,
		budget_line=doc.budget_line,
		before_summary=format_kes_full(remaining, currency=doc.currency or "KES"),
		after_summary=format_kes_full(0, currency=doc.currency or "KES"),
		source_reference=doc.demand_code or "",
		reason=(reason or "").strip(),
		actor=(actor or frappe.session.user or "System").strip(),
		actor_kind="user",
	)

	doc.reload()
	return _reservation_result(doc, reused=False)


def list_eligible_budget_lines(
	procuring_entity: str | None = None,
	fiscal_period: str | None = None,
	min_amount: float | None = None,
	classification: str | None = None,
) -> list[dict[str, Any]]:
	"""BUD-CHG-001 §12 `list_eligible_budget_lines` — scoped Active lines with
	operational balances, for the Check/Reserve line selector. `min_amount`
	excludes lines whose available balance cannot cover it; `classification`
	filters to one Budget Line classification.
	"""
	require_any_role(
		ROLE_VIEWER,
		ROLE_OFFICER,
		ROLE_REVIEWER,
		ROLE_AUTHORITY,
		ROLE_AUDITOR,
		"System Manager",
		"Procurement Approval Authority",
	)
	pe = resolve_scoped_entity(procuring_entity or entity_for_user() or None)
	if not pe and "System Manager" not in frappe.get_roles():
		frappe.throw(_("No procuring entity assigned"), frappe.PermissionError)
	filters: dict[str, Any] = {"status": "Active"}
	if pe:
		filters["procuring_entity"] = pe
	if fiscal_period:
		filters["fiscal_period"] = fiscal_period
	budgets = frappe.get_all("Budget", filters=filters, pluck="name")
	if not budgets:
		return []
	line_filters: dict[str, Any] = {"budget": ["in", budgets], "is_active": 1}
	if classification:
		line_filters["classification"] = classification
	lines = frappe.get_all(
		"Budget Line",
		filters=line_filters,
		fields=[
			"name",
			"generated_reference",
			"title",
			"approved_amount",
			"amount_reserved",
			"amount_committed",
			"primary_target_code",
			"primary_target_name",
			"budget",
		],
		order_by="idx asc",
	)
	floor = flt(min_amount)
	out = []
	for ln in lines:
		avail = flt(ln.approved_amount) - flt(ln.amount_reserved) - flt(ln.amount_committed)
		if floor > 0 and avail < floor:
			continue
		out.append(
			{
				"id": ln.name,
				"code": ln.generated_reference or "",
				"name": ln.title or ln.generated_reference or "",
				"available_before": avail,
				"available_before_display": format_kes_full(avail),
				"primary_target_code": ln.primary_target_code or "",
				"primary_target_name": ln.primary_target_name or "",
				"budget": ln.budget,
			}
		)
	return out


def revalidate_reservation(
	reservation: str | None = None,
	*,
	material_event: str | None = None,
	new_estimated_amount: float | None = None,
	evidence: str | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""BUD-CHG-001 §12 `revalidate_reservation` / §7.2 / §7.4 — re-check an active
	reservation after a named material event (Plan Item/Requisition amendment,
	Tender or Award value change, Contract event, Budget Revision, ...). Budget
	does not independently confirm the event occurred in the source module — it
	trusts the caller and records `material_event`/`evidence` as correlation.
	Idempotent by result: repeat calls that don't change the outcome do not
	emit a duplicate audit event (BUD-CHG-001 §11).
	"""
	doc = _resolve_reservation(reservation or "")
	bud = frappe.get_doc("Budget", doc.budget)
	require_budget_capability(CAP_BUDGET_RESERVE, bud)

	event = (material_event or "").strip()
	if not event:
		frappe.throw(_("A material-event reference is required to revalidate"))
	if doc.status not in ("Reserved", "Partially converted", "Needs attention"):
		frappe.throw(_("Only an active reservation can be revalidated"))

	line = frappe.get_doc("Budget Line", doc.budget_line)
	available = flt(line.approved_amount) - flt(line.amount_reserved) - flt(line.amount_committed)
	increase = (
		max(0.0, flt(new_estimated_amount) - flt(doc.remaining_reserved))
		if new_estimated_amount is not None
		else 0.0
	)
	valid = bud.status == "Active" and increase <= available

	prior_status = doc.status
	if valid:
		new_status = (
			"Partially converted" if flt(doc.remaining_reserved) < flt(doc.original_amount) else "Reserved"
		)
	else:
		new_status = "Needs attention"

	if new_status != prior_status:
		doc.status = new_status
		doc.save(ignore_permissions=True)

		from kentender_budget.services.budget_audit_contracts import (
			EVENT_REVALIDATED,
			safe_record_event,
		)

		safe_record_event(
			budget=bud.name,
			event_type=EVENT_REVALIDATED,
			record_doctype="Funding Reservation",
			record_code=doc.generated_reference,
			budget_line=doc.budget_line,
			before_summary=prior_status,
			after_summary=new_status,
			source_reference=event,
			reason=(evidence or "").strip(),
			actor=(actor or frappe.session.user or "System").strip(),
			actor_kind="user",
		)
		doc.reload()

	return {
		"ok": True,
		"reservation_id": doc.name,
		"reservation_code": doc.generated_reference,
		"status": doc.status,
		"valid": valid,
		"remaining_reserved": flt(doc.remaining_reserved),
		"remaining_reserved_display": format_kes_full(doc.remaining_reserved, currency=doc.currency or "KES"),
		"material_event": event,
	}
