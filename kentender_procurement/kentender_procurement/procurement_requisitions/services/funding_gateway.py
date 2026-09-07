# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §9.1A/§9.1 — the Budget contracts, under the spec's
verbs. Requisitions calls only Budget's published `budget_api` module.

`check_funding` and `reserve_funding` are the two calls this module is the
first and only real caller of (BUD-CHG-001 v1.6 §8.1: Planning checks
affordability but never reserves). No `finance_task` is ever supplied;
`calling_module` is always "Procurement Requisitions"; `caller_reference` is
the Requisition's own reference, which is what Budget's D1 conflict rule
(REQ-102) uses to tell a genuine double-authorise apart from two independent
Requisitions legitimately holding their own reservations against the same
Plan Source Allocation.
"""

from __future__ import annotations

from typing import Any

CALLING_MODULE = "Procurement Requisitions"


def check_funding(
	*, plan_item: str, plan_version: str, source_set_hash: str, allocations: list[dict[str, Any]],
	correlation_id: str, caller_reference: str,
) -> dict[str, Any]:
	from kentender_budget.api.budget_api import check_funding as contract

	return contract(
		plan_item=plan_item, plan_version=plan_version, source_set_hash=source_set_hash,
		allocations=allocations, correlation_id=correlation_id,
		calling_module=CALLING_MODULE, caller_reference=caller_reference,
	)


def reserve_funding(*, token: str, source_set_hash: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_budget.api.budget_api import reserve_funding as contract

	return contract(token=token, source_set_hash=source_set_hash, idempotency_key=idempotency_key)


def release_reservation(
	*, reservation: str, amount: float | None, downstream_event_id: str, idempotency_key: str,
) -> dict[str, Any]:
	from kentender_budget.services.budget_commitment_contracts import release_reservation as contract

	return contract(
		reservation=reservation, amount=amount, downstream_event_id=downstream_event_id,
		downstream_event_type="ProcurementRequisitionRevoked", idempotency_key=idempotency_key,
	)
