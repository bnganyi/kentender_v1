# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §9.1 `get_funding_lineage` — ordered Budget, version-at-
confirmation, line, reservation, commitment and ledger identities for one
Plan Item, source allocation, reservation, contract or commitment reference,
within the caller's authorised scope.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_budget.services.budget_authorization import require_budget_version_read_scope
from kentender_budget.services.budget_contracts import _active_version, resolve_scoped_entity


def _resolve_reservations(*, plan_item: str | None, plan_source_allocation: str | None, reservation: str | None, contract: str | None, commitment: str | None) -> list[Any]:
	if reservation:
		key = reservation.strip()
		name = key if frappe.db.exists("Funding Reservation", key) else frappe.db.get_value("Funding Reservation", {"generated_reference": key}, "name")
		return [frappe.get_doc("Funding Reservation", name)] if name else []
	if plan_source_allocation:
		names = frappe.get_all("Funding Reservation", filters={"plan_source_allocation": plan_source_allocation}, pluck="name")
		return [frappe.get_doc("Funding Reservation", n) for n in names]
	if plan_item:
		names = frappe.get_all("Funding Reservation", filters={"plan_item": plan_item}, pluck="name")
		return [frappe.get_doc("Funding Reservation", n) for n in names]
	if contract or commitment:
		filters: dict[str, Any] = {}
		if commitment:
			key = commitment.strip()
			filters["name"] = key if frappe.db.exists("Procurement Commitment", key) else frappe.db.get_value("Procurement Commitment", {"generated_reference": key}, "name")
		if contract:
			filters["contract"] = contract
		com_names = frappe.get_all("Procurement Commitment", filters=filters, pluck="reservation")
		return [frappe.get_doc("Funding Reservation", n) for n in set(com_names) if n]
	return []


def get_funding_lineage(
	*,
	plan_item: str | None = None,
	plan_source_allocation: str | None = None,
	reservation: str | None = None,
	contract: str | None = None,
	commitment: str | None = None,
) -> dict[str, Any]:
	reservations = _resolve_reservations(
		plan_item=plan_item, plan_source_allocation=plan_source_allocation, reservation=reservation, contract=contract, commitment=commitment
	)
	if not reservations:
		return {"rows": []}

	rows = []
	for rsv in reservations:
		budget = frappe.get_doc("Budget", rsv.budget)
		resolve_scoped_entity(budget.procuring_entity)
		version_at_creation = frappe.get_doc("Budget Version", rsv.budget_version_at_creation)
		require_budget_version_read_scope(version_at_creation)

		line = frappe.get_doc("Budget Line", rsv.budget_line)
		line_version = frappe.db.get_value(
			"Budget Line Version", {"budget_version": version_at_creation.name, "budget_line": line.name}, ["title"], as_dict=True
		)
		commitments = frappe.get_all(
			"Procurement Commitment",
			filters={"reservation": rsv.name},
			fields=["name", "generated_reference", "contract", "current_amount", "status"],
		)
		rows.append(
			{
				"budget": {"id": budget.name, "code": budget.generated_reference},
				"budget_version_at_creation": {"id": version_at_creation.name, "code": version_at_creation.generated_reference},
				"budget_line": {"id": line.name, "code": line.generated_reference, "title": (line_version or {}).get("title") or ""},
				"reservation": {
					"id": rsv.name,
					"code": rsv.generated_reference,
					"status": rsv.status,
					"plan_item": rsv.plan_item,
					"plan_source_allocation": rsv.plan_source_allocation,
					"original_amount": rsv.original_amount,
					"remaining_amount": rsv.remaining_amount,
				},
				"commitments": [
					{"id": c.name, "code": c.generated_reference, "contract": c.contract, "current_amount": c.current_amount, "status": c.status}
					for c in commitments
				],
			}
		)
	return {"rows": rows}
