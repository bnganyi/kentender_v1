# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Funding check and reservation — BUD-UI-06 / BUD-FR-060–070 / Phase 5."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate, today

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


def _value_treatment_summary(line_name: str) -> str:
	rows = frappe.get_all(
		"Budget Line Value Treatment",
		filters={"parent": line_name, "parenttype": "Budget Line"},
		fields=["treatment"],
		order_by="idx asc",
	)
	labels = []
	seen = set()
	for r in rows:
		t = (r.treatment or "").strip()
		if t and t not in seen:
			seen.add(t)
			labels.append(t)
	if not labels:
		return "—"
	if len(labels) == 1:
		return labels[0]
	return f"{labels[0]} +{len(labels) - 1}"


def _demand_context(demand: str | None) -> dict[str, str]:
	key = (demand or "").strip()
	if not key:
		return {
			"demand_id": "",
			"demand_code": "",
			"demand_title": "",
			"department": "",
		}
	# Prefer Demand DocType when present; else treat key as business code.
	name = key
	if not frappe.db.exists("Demand", name):
		name = frappe.db.get_value("Demand", {"demand_id": key}, "name") or ""
	if name and frappe.db.exists("Demand", name):
		doc = frappe.get_doc("Demand", name)
		return {
			"demand_id": name,
			"demand_code": (getattr(doc, "demand_id", None) or name),
			"demand_title": (doc.title or doc.name or ""),
			"department": (getattr(doc, "requesting_department", None) or getattr(doc, "department", None) or ""),
		}
	return {
		"demand_id": "",
		"demand_code": key,
		"demand_title": key,
		"department": "",
	}


def check_funding(
	budget_line: str | None = None,
	requested_amount: float | None = None,
	demand: str | None = None,
	procuring_entity: str | None = None,
) -> dict[str, Any]:
	"""Read-only funding check (BUD-FR-060/061 / BUD-AC-008). Does not mutate balances."""
	require_any_role(
		ROLE_VIEWER, ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_AUDITOR, "System Manager"
	)
	line = _resolve_line(budget_line or "")
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
			"value_treatment": _value_treatment_summary(line.name),
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
	demand_name: str | None = None,
	requested_amount: float | None = None,
	idempotency_key: str | None = None,
	actor: str | None = None,
	procuring_entity: str | None = None,
) -> dict[str, Any]:
	"""Create a Funding Reservation from an authorised Demand event (BUD-FR-062–066)."""
	require_any_role(ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, "System Manager")
	key = (idempotency_key or "").strip()
	if key:
		existing = frappe.db.get_value(
			"Funding Reservation", {"idempotency_key": key}, "name"
		)
		if existing:
			doc = frappe.get_doc("Funding Reservation", existing)
			return _reservation_result(doc, reused=True)

	line = _resolve_line(budget_line or "")
	# Row lock against parallel oversubscription.
	frappe.db.sql(
		"SELECT name FROM `tabBudget Line` WHERE name=%s FOR UPDATE",
		(line.name,),
	)
	line.reload()

	check = check_funding(
		budget_line=line.name,
		requested_amount=requested_amount,
		demand=demand_name,
		procuring_entity=procuring_entity,
	)
	if not check["sufficient"]:
		from kentender_budget.services.budget_notification_service import (
			notify_funding_insufficient,
		)

		bud_for_notify = frappe.get_doc("Budget", line.budget)
		notify_funding_insufficient(
			budget_doc=bud_for_notify,
			budget_line_code=line.generated_reference or line.name,
			demand_code=(demand_name or "").strip()
			or (check.get("demand") or {}).get("demand_code")
			or "",
			requested_amount=flt(requested_amount),
			shortfall_display=check.get("shortfall_display") or "",
		)
		frappe.throw(
			_("Insufficient funding. Shortfall: {0}").format(check["shortfall_display"]),
			title=_("Insufficient funding"),
		)

	bud = frappe.get_doc("Budget", line.budget)
	demand_ctx = check["demand"]
	demand_code = demand_ctx["demand_code"] or (demand_name or "").strip()
	demand_title = demand_ctx["demand_title"] or demand_code
	if not demand_code:
		frappe.throw(_("Demand is required for reservation"))

	# One active reservation per Demand + line (no duplicate holds).
	dup = frappe.db.get_value(
		"Funding Reservation",
		{
			"budget_line": line.name,
			"demand_code": demand_code,
			"status": ["in", ["Reserved", "Partially converted"]],
		},
		"name",
	)
	if dup and not key:
		doc = frappe.get_doc("Funding Reservation", dup)
		return _reservation_result(doc, reused=True)

	requested = flt(requested_amount)
	ref = allocate_reservation_reference(bud.procuring_entity)
	idem = key or f"{demand_code}:{line.generated_reference}:{flt(requested):.2f}"

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
		source_reference=demand_code,
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


def list_active_lines_for_check(
	procuring_entity: str | None = None,
	fiscal_period: str | None = None,
) -> list[dict[str, Any]]:
	"""Active Budget Lines for the Check/Reserve line selector."""
	require_any_role(
		ROLE_VIEWER, ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_AUDITOR, "System Manager"
	)
	pe = resolve_scoped_entity(procuring_entity or entity_for_user() or None)
	if not pe and frappe.session.user != "Administrator":
		if "System Manager" not in frappe.get_roles():
			frappe.throw(_("No procuring entity assigned"), frappe.PermissionError)
	filters: dict[str, Any] = {"status": "Active"}
	if pe:
		filters["procuring_entity"] = pe
	if fiscal_period:
		filters["fiscal_period"] = fiscal_period
	budgets = frappe.get_all("Budget", filters=filters, pluck="name")
	if not budgets:
		return []
	lines = frappe.get_all(
		"Budget Line",
		filters={"budget": ["in", budgets], "is_active": 1},
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
	out = []
	for ln in lines:
		avail = flt(ln.approved_amount) - flt(ln.amount_reserved) - flt(ln.amount_committed)
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
