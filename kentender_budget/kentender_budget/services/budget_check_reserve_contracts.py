# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §8.2/§9.1 — the Finance confirmation boundary. `check_funding`
is non-mutating and returns a short-lived check token; `reserve_funding`
re-validates every allocation under a stable-order row lock and creates one
reservation per source allocation, atomically (all-or-none). Repeating the
same correlation_id returns the original effective result (BUD-BR-011).

Caller (Procurement Planning) authority — the assigned Finance Confirmation
capability, task, PE/FY, source-set and amount scope — is authorised here
directly; Budget never trusts Planning's own route visibility as authority
(§12.6).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_reference import allocate_reservation_reference

_CHECK_TOKEN_TTL_SECONDS = 300
_FINANCE_CAPABILITY_ROLE = "Finance Confirmation Officer"


def _require_finance_capability(procuring_entity: str) -> None:
	from kentender_core.services.authorization_native import require_role_capability
	from kentender_core.services.authorization_policy import ResourceContext

	user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return
	if _FINANCE_CAPABILITY_ROLE not in frappe.get_roles(user):
		frappe.throw(_("Not permitted to confirm funding"), frappe.PermissionError, title="BUDGET_FINANCE_TASK_DENIED")
	pe_scope = set(frappe.get_all("User Permission", filters={"user": user, "allow": "Procuring Entity"}, pluck="for_value"))
	if pe_scope and procuring_entity not in pe_scope:
		frappe.throw(_("Not permitted for this procuring entity"), frappe.PermissionError, title="BUDGET_FINANCE_TASK_DENIED")


def _resolve_line(budget_line: str) -> Any:
	key = (budget_line or "").strip()
	if not key:
		frappe.throw(_("Budget Line is required"))
	name = key if frappe.db.exists("Budget Line", key) else frappe.db.get_value("Budget Line", {"generated_reference": key}, "name")
	if not name:
		frappe.throw(_("Budget Line {0} not found").format(key), frappe.DoesNotExistError, title="BUDGET_LINE_NOT_ELIGIBLE")
	return frappe.get_doc("Budget Line", name)


def _line_active_version_and_position(budget_line_doc):
	from kentender_budget.services.budget_contracts import _active_version, _line_position, _line_version_for

	version = _active_version(budget_line_doc.budget)
	if not version:
		# BUD-BR-023 — a Closed Budget admits no new reservations. A Closed
		# Budget Version means the Budget itself is Closed (no other Active
		# version exists for it); distinguish that from the generic "not
		# eligible" case so callers get the specific documented error code.
		if frappe.db.exists("Budget Version", {"budget": budget_line_doc.budget, "status": "Closed"}):
			frappe.throw(_("The Budget is Closed and cannot accept a new reservation"), frappe.ValidationError, title="BUDGET_CLOSED")
		frappe.throw(_("Budget Line has no Active Budget Version"), frappe.ValidationError, title="BUDGET_LINE_NOT_ELIGIBLE")
	line_version = _line_version_for(version.name, budget_line_doc.name)
	if not line_version:
		frappe.throw(_("Budget Line is not eligible under the Active Version"), frappe.ValidationError, title="BUDGET_LINE_NOT_ELIGIBLE")
	return version, line_version, _line_position(budget_line_doc.name, line_version)


def check_funding(
	plan_item: str,
	plan_version: str,
	finance_task: str,
	source_set_hash: str,
	allocations: list[dict[str, Any]],
	correlation_id: str,
) -> dict[str, Any]:
	"""§9.1 `check_funding` — non-mutating per-allocation eligibility, positions,
	required amounts, after-confirmation balances and a short-lived check token."""
	allocations = allocations or []
	if not allocations:
		frappe.throw(_("At least one allocation is required"), frappe.ValidationError, title="BUDGET_SCOPE_REQUIRED")

	results = []
	all_sufficient = True
	budget = None
	for alloc in allocations:
		line_doc = _resolve_line(alloc.get("budget_line") or "")
		if budget is None:
			budget = frappe.get_doc("Budget", line_doc.budget)
		_require_finance_capability(budget.procuring_entity)
		version, line_version, position = _line_active_version_and_position(line_doc)
		# BUD-BR-008 — the allocation's funding source shall equal the Budget
		# Line's, independently of any upstream filtering (list_eligible_budget_lines
		# already filters by funding_source, but a caller bypassing that read
		# must not be able to reserve against a mismatched line).
		requested_funding_source = (alloc.get("funding_source") or "").strip()
		if requested_funding_source and requested_funding_source != line_version.funding_source:
			frappe.throw(
				_("{0} funding source does not match the allocation").format(line_version.title),
				frappe.ValidationError,
				title="BUDGET_LINE_NOT_ELIGIBLE",
			)
		requested = flt(alloc.get("amount"))
		if requested <= 0:
			frappe.throw(_("Requested amount must be greater than zero"), frappe.ValidationError, title="BUDGET_SCOPE_REQUIRED")
		sufficient = position["available"] >= requested
		all_sufficient = all_sufficient and sufficient
		results.append(
			{
				"budget_line": line_doc.name,
				"plan_source_allocation": alloc.get("plan_source_allocation") or "",
				"requested_amount": requested,
				"available_before": position["available"],
				"available_after": max(0.0, position["available"] - requested) if sufficient else position["available"],
				"sufficient": sufficient,
				"shortfall": 0.0 if sufficient else (requested - position["available"]),
				"budget_version_at_check": version.name,
			}
		)

	token = frappe.generate_hash(length=24)
	frappe.cache().set_value(
		f"budget_check_token:{token}",
		{
			"plan_item": plan_item,
			"plan_version": plan_version,
			"finance_task": finance_task,
			"source_set_hash": source_set_hash,
			"correlation_id": correlation_id,
			"allocations": [
				{
					"budget_line": r["budget_line"],
					"plan_source_allocation": r["plan_source_allocation"],
					"amount": r["requested_amount"],
					"funding_source": (a.get("funding_source") or "").strip(),
				}
				for r, a in zip(results, allocations)
			],
		},
		expires_in_sec=_CHECK_TOKEN_TTL_SECONDS,
	)

	from kentender_budget.services.budget_audit_contracts import EVENT_CHECK_PERFORMED, safe_record_event

	safe_record_event(
		budget=budget.name,
		event_type=EVENT_CHECK_PERFORMED,
		actor=frappe.session.user,
		correlation_id=correlation_id,
		calling_module="Procurement Planning",
		downstream_reference=plan_item,
	)

	return {"token": token, "all_sufficient": all_sufficient, "allocations": results}


def _existing_reservations_for_correlation(correlation_id: str) -> list[Any] | None:
	names = frappe.get_all("Funding Reservation", filters={"correlation_id": correlation_id}, pluck="name")
	if not names:
		return None
	return [frappe.get_doc("Funding Reservation", n) for n in names]


def reserve_funding(
	token: str,
	finance_task: str,
	source_set_hash: str,
	idempotency_key: str,
	actor: str | None = None,
) -> dict[str, Any]:
	"""§9.1/§8.2 `reserve_funding` — locks all affected lines in stable ID
	order, reloads every position, creates one reservation per source
	allocation or none (BUD-BR-010/011/013)."""
	correlation_id = idempotency_key
	existing = _existing_reservations_for_correlation(correlation_id)
	if existing:
		return {"ok": True, "reused": True, "reservations": [_reservation_result(r) for r in existing]}

	cached = frappe.cache().get_value(f"budget_check_token:{token}")
	if not cached or cached.get("finance_task") != finance_task or cached.get("source_set_hash") != source_set_hash:
		frappe.throw(_("The funding check has expired or no longer matches this task"), frappe.ValidationError, title="BUDGET_CHECK_STALE")

	allocations = cached["allocations"]
	line_docs = {a["budget_line"]: _resolve_line(a["budget_line"]) for a in allocations}
	budget_lines_sorted = sorted(line_docs.keys())

	# Lock all affected lines in stable ID order (§8.2 step 5) before reloading
	# any position, to prevent concurrent oversubscription (BUD-BR-013).
	frappe.db.sql(
		"select name from `tabBudget Line` where name in %s order by name for update",
		(budget_lines_sorted,),
	)

	actor_name = (actor or frappe.session.user or "System").strip()
	prepared: list[dict[str, Any]] = []
	for alloc in allocations:
		line_doc = line_docs[alloc["budget_line"]]
		budget = frappe.get_doc("Budget", line_doc.budget)
		version, line_version, position = _line_active_version_and_position(line_doc)
		requested_funding_source = (alloc.get("funding_source") or "").strip()
		if requested_funding_source and requested_funding_source != line_version.funding_source:
			frappe.throw(
				_("{0} funding source does not match the allocation").format(line_version.title),
				frappe.ValidationError,
				title="BUDGET_LINE_NOT_ELIGIBLE",
			)
		# `plan_source_allocation` is unique on Funding Reservation (§4.5) — a
		# prior reservation under a *different* correlation is a genuine
		# conflict (BUD-BR-011/§13 BUDGET_RESERVATION_CONFLICT), not something
		# to silently insert on top of or crash on with a raw DB constraint
		# error. The whole-correlation reuse check above already handled the
		# same-correlation retry case.
		clashing = frappe.db.get_value(
			"Funding Reservation", {"plan_source_allocation": alloc["plan_source_allocation"]}, ["name", "correlation_id"], as_dict=True
		)
		if clashing and clashing.correlation_id != correlation_id:
			frappe.throw(
				_("This allocation already has a different effective reservation"),
				frappe.ValidationError,
				title="BUDGET_RESERVATION_CONFLICT",
			)
		requested = flt(alloc["amount"])
		if position["available"] < requested:
			frappe.throw(
				_("Insufficient funding for {0}: available {1}, requested {2}").format(
					line_version.title, format_kes_full(position["available"]), format_kes_full(requested)
				),
				frappe.ValidationError,
				title="BUDGET_INSUFFICIENT_FUNDS",
			)
		prepared.append({"line_doc": line_doc, "budget": budget, "version": version, "requested": requested, "plan_source_allocation": alloc["plan_source_allocation"]})

	created = []
	for p in prepared:
		ref = allocate_reservation_reference(p["budget"].procuring_entity)
		doc = frappe.get_doc(
			{
				"doctype": "Funding Reservation",
				"generated_reference": ref,
				"budget": p["budget"].name,
				"budget_version_at_creation": p["version"].name,
				"budget_line": p["line_doc"].name,
				"status": "Active",
				"plan_item": cached["plan_item"],
				"plan_source_allocation": p["plan_source_allocation"],
				"original_amount": p["requested"],
				"remaining_amount": p["requested"],
				"currency": p["budget"].currency,
				"correlation_id": correlation_id,
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc)

		from kentender_budget.services.budget_audit_contracts import EVENT_RESERVED, safe_record_event

		safe_record_event(
			budget=p["budget"].name,
			budget_line=p["line_doc"].name,
			reservation=doc.name,
			event_type=EVENT_RESERVED,
			actor=actor_name,
			correlation_id=correlation_id,
			calling_module="Procurement Planning",
			downstream_reference=f"{cached['plan_item']} · {doc.name}",
			amount=p["requested"],
			currency=p["budget"].currency,
		)

	frappe.cache().delete_value(f"budget_check_token:{token}")
	return {"ok": True, "reused": False, "reservations": [_reservation_result(r) for r in created]}


def _reservation_result(doc) -> dict[str, Any]:
	return {
		"reservation_id": doc.name,
		"reservation_code": doc.generated_reference,
		"status": doc.status,
		"budget_line": doc.budget_line,
		"plan_source_allocation": doc.plan_source_allocation,
		"original_amount": flt(doc.original_amount),
		"remaining_amount": flt(doc.remaining_amount),
		"currency": doc.currency,
	}


def _resolve_reservation(reservation: str) -> Any:
	key = (reservation or "").strip()
	if not key:
		frappe.throw(_("Reservation is required"))
	name = key if frappe.db.exists("Funding Reservation", key) else frappe.db.get_value("Funding Reservation", {"generated_reference": key}, "name")
	if not name:
		frappe.throw(_("Reservation {0} not found").format(key), frappe.DoesNotExistError)
	return frappe.get_doc("Funding Reservation", name)
