# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.10 §8.3/§9.1 — the funding confirmation boundary. `check_funding`
is non-mutating: it validates the complete array, totals the rows that share a
Budget Line before testing availability, and returns per-row and per-line
results plus one short-lived token bound to the exact payload digest.
`reserve_funding` re-validates that payload under a stable-order row lock and
creates one reservation per drawdown line (one per source allocation for
Planning-era callers with no drawdown line), all or none, inside the caller's
transaction — it never commits. Same key + same payload returns the original
mapping; same key + changed payload is refused (BUD-BR-011).

Caller authority — the assigned Finance Confirmation Officer or Head of
Procurement Function Site-wide responsibility, task, source-set and amount
scope — is authorised here directly via `authorise_record()`; Budget never
trusts a caller's own route visibility as authority (§12.6). No Procuring
Entity or Fiscal Year scope participates (BUD-BR-001).

Two callers exist as of REQ-CHG-001 v1.6 D1: Procurement Planning's own
`check_plan_affordability` path never reaches these two functions at all
(BUD-CHG-001 v1.6 §8.1 — Planning checks, never reserves); Procurement
Requisitions is the first and only module that calls `check_funding` then
`reserve_funding` for real, at `AuthoriseRequisition` (REQ-CHG-001 v1.6
§9.1A). `calling_module` and `caller_reference` are recorded rather than
hard-coded so the audit trail and the reservation-conflict rule both name
the actual caller. `finance_task` is optional: Planning-era callers supply
one, Requisitions does not (it has no Finance task at all).
"""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_reference import allocate_reservation_reference

_CHECK_TOKEN_TTL_SECONDS = 300

# BUD-CHG-001 v1.10 §4.8 Money at this boundary: currency units, KES scale 2,
# at most 18 integral digits. Accepted: a plain decimal string, an int or a
# Decimal. Refused without rounding: a float, exponent notation, NaN/Infinity,
# excess scale, overflow. Budget's own storage is still Currency (its FU-30),
# so stored positions are read back through `_stored_money`.
_MONEY_SCALE = 2
_MONEY_TEXT = re.compile(r"^\d{1,18}(\.\d{1,2})?$")
_QUANTUM = Decimal(1).scaleb(-_MONEY_SCALE)


def _money_error(value) -> None:
	frappe.throw(
		_("Amount {0} is not an exact amount in currency units with at most 2 decimal places").format(repr(value)),
		frappe.ValidationError,
		title="BUDGET_MONEY_PRECISION_INVALID",
	)


def _exact_money(value) -> Decimal:
	if isinstance(value, bool) or isinstance(value, float) or value is None:
		_money_error(value)
	if isinstance(value, int):
		amount = Decimal(value)
	elif isinstance(value, Decimal):
		amount = value
	else:
		text = str(value).strip()
		if not _MONEY_TEXT.match(text):
			_money_error(value)
		amount = Decimal(text)
	if not amount.is_finite() or amount != amount.quantize(_QUANTUM) or len(str(int(abs(amount)))) > 18:
		_money_error(value)
	if amount <= 0:
		frappe.throw(_("Requested amount must be greater than zero"), frappe.ValidationError, title="BUDGET_MONEY_PRECISION_INVALID")
	return amount.quantize(_QUANTUM)


def _stored_money(value) -> Decimal:
	"""A Currency value read back from Budget's own storage."""
	return Decimal(repr(flt(value))).quantize(_QUANTUM)


def _text(amount: Decimal) -> str:
	return f"{amount.quantize(_QUANTUM):f}"


def _payload_digest(context: dict[str, Any], rows: list[dict[str, Any]]) -> str:
	body = json.dumps({"context": context, "rows": rows}, sort_keys=True, separators=(",", ":"))
	return hashlib.sha256(body.encode()).hexdigest()


# REQ-CHG-001 v1.6 D1 — either Site-wide responsibility may call
# check_funding/reserve_funding: Finance Confirmation Officer (the original
# Planning-era caller) or Head of Procurement Function (Procurement
# Requisitions' authorising office). The error title stays
# BUDGET_FINANCE_TASK_DENIED — it is a closed vocabulary (§13) naming the
# funding boundary's own denial, not either caller's identity.
ROLE_HEAD_OF_PROCUREMENT_FUNCTION = "Head of Procurement Function"
_CHECK_RESERVE_CALLER_ROLES = (
	"Finance Confirmation Officer",
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
)


def _require_check_reserve_capability() -> None:
	"""§7/§17.1 / REQ-CHG-001 v1.6 D1 — Finance Confirmation Officer or Head
	of Procurement Function, via `authorise_record()`. No Procuring Entity,
	Fiscal Year or capability string participates (BUD-BR-001)."""
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	user = frappe.session.user
	for role in _CHECK_RESERVE_CALLER_ROLES:
		if authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND).allowed:
			return
	frappe.throw(
		_("Not permitted to confirm or reserve funding — requires Finance Confirmation Officer or Head of Procurement Function"),
		frappe.PermissionError,
		title="BUDGET_FINANCE_TASK_DENIED",
	)


def _resolve_line(budget_line: str) -> Any:
	key = (budget_line or "").strip()
	if not key:
		frappe.throw(_("Budget Line is required"))
	name = key if frappe.db.exists("Procurement Budget Line", key) else frappe.db.get_value("Procurement Budget Line", {"generated_reference": key}, "name")
	if not name:
		frappe.throw(_("Budget Line {0} not found").format(key), frappe.DoesNotExistError, title="BUDGET_LINE_NOT_ELIGIBLE")
	return frappe.get_doc("Procurement Budget Line", name)


def _line_active_version_and_position(budget_line_doc):
	from kentender_budget.services.budget_contracts import _active_version, _line_position, _line_version_for

	version = _active_version(budget_line_doc.budget)
	if not version:
		# BUD-BR-023 — a Closed Budget admits no new reservations. A Closed
		# Budget Version means the Budget itself is Closed (no other Active
		# version exists for it); distinguish that from the generic "not
		# eligible" case so callers get the specific documented error code.
		if frappe.db.exists("Procurement Budget Version", {"budget": budget_line_doc.budget, "status": "Closed"}):
			frappe.throw(_("The Budget is Closed and cannot accept a new reservation"), frappe.ValidationError, title="BUDGET_CLOSED")
		frappe.throw(_("Budget Line has no Active Budget Version"), frappe.ValidationError, title="BUDGET_LINE_NOT_ELIGIBLE")
	line_version = _line_version_for(version.name, budget_line_doc.name)
	if not line_version:
		frappe.throw(_("Budget Line is not eligible under the Active Version"), frappe.ValidationError, title="BUDGET_LINE_NOT_ELIGIBLE")
	return version, line_version, _line_position(budget_line_doc.name, line_version)


def _normalise_rows(allocations: list[dict[str, Any]]) -> list[dict[str, Any]]:
	rows = []
	for alloc in allocations:
		rows.append(
			{
				"budget_line": (alloc.get("budget_line") or "").strip(),
				"plan_source_allocation": alloc.get("plan_source_allocation") or "",
				"drawdown_line_id": (alloc.get("drawdown_line_id") or "").strip(),
				"source_organisation_unit": (alloc.get("source_organisation_unit") or "").strip(),
				"funding_source": (alloc.get("funding_source") or "").strip(),
				"amount": _text(_exact_money(alloc.get("amount"))),
			}
		)
	drawdowns = [r["drawdown_line_id"] for r in rows if r["drawdown_line_id"]]
	if len(drawdowns) != len(set(drawdowns)):
		frappe.throw(_("A drawdown line appears more than once in one funding check"), frappe.ValidationError, title="BUDGET_RESERVATION_CONFLICT")
	return rows


def _line_totals(rows: list[dict[str, Any]], line_docs: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], Any]:
	"""BUD-CHG-001 v1.10 §8.3 — total every row that shares a Budget Line,
	then test the total against that line's availability."""
	totals: dict[str, dict[str, Any]] = {}
	budget = None
	for row in rows:
		line_doc = line_docs[row["budget_line"]]
		if budget is None:
			budget = frappe.get_doc("Procurement Budget", line_doc.budget)
		entry = totals.get(line_doc.name)
		if entry is None:
			version, line_version, position = _line_active_version_and_position(line_doc)
			entry = totals[line_doc.name] = {
				"version": version,
				"line_version": line_version,
				"available": _stored_money(position["available"]),
				"required": Decimal(0),
			}
		# BUD-BR-008 — the allocation's funding source shall equal the Budget
		# Line's, independently of any upstream filtering.
		if row["funding_source"] and row["funding_source"] != entry["line_version"].funding_source:
			frappe.throw(
				_("{0} funding source does not match the allocation").format(entry["line_version"].title),
				frappe.ValidationError,
				title="BUDGET_LINE_NOT_ELIGIBLE",
			)
		entry["required"] += Decimal(row["amount"])
	return totals, budget


def check_funding(
	plan_item: str,
	plan_version: str,
	source_set_hash: str,
	allocations: list[dict[str, Any]],
	correlation_id: str,
	*,
	finance_task: str | None = None,
	calling_module: str = "Procurement Planning",
	caller_reference: str = "",
) -> dict[str, Any]:
	"""§9.1 `check_funding` — non-mutating, complete-array check. Rows sharing a
	Budget Line are totalled before availability is tested (BUD-CHG-001 v1.10
	§8.3); returns per-row and per-line results and one token bound to the
	exact payload digest."""
	allocations = allocations or []
	if not allocations:
		frappe.throw(_("At least one allocation is required"), frappe.ValidationError)
	_require_check_reserve_capability()

	rows = _normalise_rows(allocations)
	line_docs = {r["budget_line"]: _resolve_line(r["budget_line"]) for r in rows}
	rows = [{**r, "budget_line": line_docs[r["budget_line"]].name} for r in rows]
	line_docs = {doc.name: doc for doc in line_docs.values()}
	totals, budget = _line_totals(rows, line_docs)

	lines = []
	for name in sorted(totals):
		entry = totals[name]
		sufficient = entry["available"] >= entry["required"]
		lines.append(
			{
				"budget_line": name,
				"required_amount": _text(entry["required"]),
				"available_before": _text(entry["available"]),
				"available_after": _text(entry["available"] - entry["required"]) if sufficient else _text(entry["available"]),
				"sufficient": sufficient,
				"shortfall": _text(Decimal(0)) if sufficient else _text(entry["required"] - entry["available"]),
				"budget_version_at_check": entry["version"].name,
			}
		)
	by_line = {line["budget_line"]: line for line in lines}
	all_sufficient = all(line["sufficient"] for line in lines)
	results = [
		{
			"budget_line": row["budget_line"],
			"plan_source_allocation": row["plan_source_allocation"],
			"drawdown_line_id": row["drawdown_line_id"],
			"requested_amount": row["amount"],
			"available_before": by_line[row["budget_line"]]["available_before"],
			"sufficient": by_line[row["budget_line"]]["sufficient"],
			"budget_version_at_check": by_line[row["budget_line"]]["budget_version_at_check"],
		}
		for row in rows
	]

	context = {
		"plan_item": plan_item,
		"plan_version": plan_version,
		"finance_task": finance_task,
		"source_set_hash": source_set_hash,
		"calling_module": calling_module,
		"caller_reference": caller_reference,
	}
	token = frappe.generate_hash(length=24)
	frappe.cache().set_value(
		f"budget_check_token:{token}",
		{**context, "correlation_id": correlation_id, "allocations": rows, "payload_digest": _payload_digest(context, rows)},
		expires_in_sec=_CHECK_TOKEN_TTL_SECONDS,
	)

	from kentender_budget.services.budget_audit_contracts import EVENT_CHECK_PERFORMED, safe_record_event

	safe_record_event(
		budget=budget.name,
		event_type=EVENT_CHECK_PERFORMED,
		actor=frappe.session.user,
		correlation_id=correlation_id,
		calling_module=calling_module,
		downstream_reference=caller_reference or plan_item,
	)

	return {"token": token, "all_sufficient": all_sufficient, "allocations": results, "lines": lines, "token_ttl_seconds": _CHECK_TOKEN_TTL_SECONDS}


def _existing_reservations_for_correlation(correlation_id: str) -> list[Any] | None:
	names = frappe.get_all("Funding Reservation", filters={"correlation_id": correlation_id}, pluck="name")
	if not names:
		return None
	return [frappe.get_doc("Funding Reservation", n) for n in names]


def reserve_funding(
	token: str,
	source_set_hash: str,
	idempotency_key: str,
	*,
	finance_task: str | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""§9.1/§8.3 `reserve_funding` — validates the same token and exact payload
	inside the caller's transaction, locks the affected lines in stable ID
	order, rechecks the per-line totals and creates one reservation per
	drawdown line or none. Never commits (BUD-CHG-001 v1.10 §8.3: the REQ
	authorisation commits every owner's effects together or none of them)."""
	_require_check_reserve_capability()
	correlation_id = idempotency_key
	cached = frappe.cache().get_value(f"budget_check_token:{token}")
	existing = _existing_reservations_for_correlation(correlation_id)
	if existing:
		# Same key + same payload replays the original mapping, even after a
		# later release; same key + changed payload is refused (§8.3).
		stored = {r.payload_digest for r in existing if r.payload_digest}
		if cached and stored and cached.get("payload_digest") not in stored:
			frappe.throw(
				_("This request differs from the original attempt. Check the original result before retrying; no new effect was created."),
				frappe.ValidationError,
				title="BUDGET_IDEMPOTENCY_CONFLICT",
			)
		return {"ok": True, "reused": True, "reservations": [_reservation_result(r) for r in existing]}

	# finance_task is optional (REQ-CHG-001 v1.6 D1): compare only when the
	# check actually recorded one. A caller with no finance_task at check
	# time (Requisitions) must reserve with no finance_task at reserve time
	# either — supplying one where the check had none is itself a mismatch.
	if not cached or cached.get("finance_task") != finance_task or cached.get("source_set_hash") != source_set_hash:
		frappe.throw(_("The funding check has expired or no longer matches this task"), frappe.ValidationError, title="BUDGET_CHECK_STALE")
	calling_module = cached.get("calling_module") or "Procurement Planning"
	caller_reference = cached.get("caller_reference") or ""
	rows = cached["allocations"]

	line_docs = {r["budget_line"]: _resolve_line(r["budget_line"]) for r in rows}
	# Lock all affected lines in stable ID order (§8.2 step 5) before reloading
	# any position, to prevent concurrent oversubscription (BUD-BR-013).
	frappe.db.sql(
		"select name from `tabProcurement Budget Line` where name in %s order by name for update",
		(tuple(sorted(line_docs)),),
	)

	for row in rows:
		if row.get("drawdown_line_id"):
			# BUD-BR-011 — each authorised REQ drawdown line receives exactly
			# one reservation; a new key cannot duplicate it.
			if frappe.db.exists("Funding Reservation", {"drawdown_line_id": row["drawdown_line_id"]}):
				frappe.throw(
					_("This drawdown line already has funding reserved"),
					frappe.ValidationError,
					title="BUDGET_RESERVATION_CONFLICT",
				)
			continue
		# Planning-era rows carry no drawdown line: an Active/Partially
		# Converted reservation for the same allocation from the same caller
		# under a different correlation is a double-authorise (REQ v1.6 D1).
		clashing = frappe.db.get_value(
			"Funding Reservation",
			{"plan_source_allocation": row["plan_source_allocation"], "status": ["in", ("Active", "Partially Converted")]},
			["name", "correlation_id", "caller_reference"],
			as_dict=True,
		)
		if clashing and clashing.correlation_id != correlation_id and (clashing.caller_reference or "") == caller_reference:
			frappe.throw(
				_("This allocation already has a different effective reservation from the same caller"),
				frappe.ValidationError,
				title="BUDGET_RESERVATION_CONFLICT",
			)

	totals, _budget = _line_totals(rows, line_docs)
	for name in sorted(totals):
		entry = totals[name]
		if entry["available"] < entry["required"]:
			frappe.throw(
				_("Insufficient funding for {0}: available {1}, requested {2}, shortfall {3}").format(
					entry["line_version"].title,
					format_kes_full(float(entry["available"])),
					format_kes_full(float(entry["required"])),
					format_kes_full(float(entry["required"] - entry["available"])),
				),
				frappe.ValidationError,
				title="BUDGET_INSUFFICIENT_FUNDS",
			)

	actor_name = (actor or frappe.session.user or "System").strip()
	created = []
	for row in rows:
		line_doc = line_docs[row["budget_line"]]
		budget = frappe.get_doc("Procurement Budget", line_doc.budget)
		version = totals[line_doc.name]["version"]
		doc = frappe.get_doc(
			{
				"doctype": "Funding Reservation",
				"generated_reference": allocate_reservation_reference(),
				"budget": budget.name,
				"budget_version_at_creation": version.name,
				"budget_line": line_doc.name,
				"status": "Active",
				"plan_item": cached["plan_item"],
				"plan_source_allocation": row["plan_source_allocation"],
				"drawdown_line_id": row.get("drawdown_line_id") or None,
				"source_organisation_unit": row.get("source_organisation_unit") or "",
				"original_amount": row["amount"],
				"remaining_amount": row["amount"],
				"currency": budget.currency,
				"correlation_id": correlation_id,
				"payload_digest": cached.get("payload_digest") or "",
				"calling_module": calling_module,
				"caller_reference": caller_reference,
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc)

		from kentender_budget.services.budget_audit_contracts import EVENT_RESERVED, safe_record_event

		safe_record_event(
			budget=budget.name,
			budget_line=line_doc.name,
			reservation=doc.name,
			event_type=EVENT_RESERVED,
			actor=actor_name,
			correlation_id=correlation_id,
			calling_module=calling_module,
			downstream_reference=(caller_reference or cached["plan_item"]) + f" · {doc.name}",
			amount=flt(row["amount"]),
			currency=budget.currency,
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
		"drawdown_line_id": doc.drawdown_line_id or "",
		"source_organisation_unit": doc.source_organisation_unit or "",
		"original_amount": _text(_stored_money(doc.original_amount)),
		"remaining_amount": _text(_stored_money(doc.remaining_amount)),
		"currency": doc.currency,
		"calling_module": doc.calling_module,
		"caller_reference": doc.caller_reference,
	}


def _resolve_reservation(reservation: str) -> Any:
	key = (reservation or "").strip()
	if not key:
		frappe.throw(_("Reservation is required"))
	name = key if frappe.db.exists("Funding Reservation", key) else frappe.db.get_value("Funding Reservation", {"generated_reference": key}, "name")
	if not name:
		frappe.throw(_("Reservation {0} not found").format(key), frappe.DoesNotExistError)
	return frappe.get_doc("Funding Reservation", name)
