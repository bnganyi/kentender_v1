# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §9.1A — the Budget owner contracts.

One complete-array `check_funding` returning one token; `reserve_funding` in
REQ's own authorisation transaction, one reservation per drawdown line;
`release_reservation` for revocation. Budget owns balances, locks and ledger
effects. Budget's closed code travels as the message title (the convention
Planning's `budget_gateway` reads); an insufficient-funds refusal is
`REQ_FUNDING_UNAVAILABLE`, any other owner refusal
`REQ_OWNER_VALIDATION_UNAVAILABLE`.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_requisitions.services.errors import fail

CALLING_MODULE = "Procurement Requisitions"


def _budget_code(before: int) -> str:
	titles = [m.get("title") for m in (frappe.local.message_log or [])[before:] if isinstance(m, dict)]
	return next((t for t in reversed(titles) if t and str(t).startswith("BUDGET_")), "")


def _call(fn, **kwargs):
	before = len(frappe.local.message_log or [])
	try:
		return fn(**kwargs)
	except frappe.ValidationError as exc:
		code = _budget_code(before)
		frappe.local.message_log = (frappe.local.message_log or [])[:before]
		if code == "BUDGET_INSUFFICIENT_FUNDS":
			fail("REQ_FUNDING_UNAVAILABLE", detail={"budget_code": code, "budget_message": str(exc)})
		if code == "BUDGET_MONEY_PRECISION_INVALID":
			fail("REQ_MONEY_PRECISION_INVALID", detail={"budget_code": code})
		fail("REQ_OWNER_VALIDATION_UNAVAILABLE", detail={"budget_code": code, "budget_message": str(exc)})


def check_funding(*, plan_item: str, plan_version: str, source_set_hash: str, allocations: list[dict[str, Any]], correlation_id: str, caller_reference: str) -> dict[str, Any]:
	from kentender_budget.services.budget_check_reserve_contracts import check_funding as contract

	return _call(
		contract, plan_item=plan_item, plan_version=plan_version, source_set_hash=source_set_hash, allocations=allocations,
		correlation_id=correlation_id, calling_module=CALLING_MODULE, caller_reference=caller_reference,
	)


def reserve_funding(*, token: str, source_set_hash: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_budget.services.budget_check_reserve_contracts import reserve_funding as contract

	return _call(contract, token=token, source_set_hash=source_set_hash, idempotency_key=idempotency_key)


def release_reservation(*, reservation: str, downstream_event_id: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_budget.services.budget_commitment_contracts import release_reservation as contract

	return _call(
		contract, reservation=reservation, amount=None, downstream_event_id=downstream_event_id,
		downstream_event_type="ProcurementRequisitionRevoked", idempotency_key=idempotency_key,
	)


def line_positions(budget_lines: list[str]) -> dict[str, dict[str, Any]]:
	"""Display only (§10.1: "display check is not authorisation"): each Budget
	Line's current approved/available position through Budget's non-mutating
	`get_budget_line_position`, read under the system principal the same way
	Planning's display reads do. No token, no reservation, no ledger event;
	authorisation always rechecks through `check_funding`/`reserve_funding`."""
	from kentender_budget.services.budget_contracts import get_budget_line_position
	from kentender_procurement.procurement_planning.services.budget_gateway import _system_principal

	out: dict[str, dict[str, Any]] = {}
	with _system_principal():
		for line in sorted(set(budget_lines)):
			result = get_budget_line_position(line)
			if result.get("outcome") in ("FORBIDDEN", "NOT_FOUND"):
				continue
			out[line] = {"code": result.get("code") or line, "positions": result.get("positions") or {}}
	return out
