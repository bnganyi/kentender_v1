# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.17 §8.9 / §9.5 — the bounded Requisitions cancellation mode of
`release_reservation`: release the exact unused reservations of a Tender whose
whole-Tender cancellation recovery Requisitions has verified, as one set, in
Requisitions' recovery transaction.

What it does, per reservation and only if every reservation passes first:
the remaining hold goes to zero (R falls, V rises by the same amount; A and C
do not move), the reservation becomes `Released` (never reused by a fresh
Requisition), one ordinary `Reservation released` ledger event records the
cancellation, recovery, Requisition, drawdown line and source with the line's
before and after positions, and one `Reservation Cancellation Release` row,
unique by cancellation and originating drawdown line, records that it was done.
The original amount and authorisation are never edited.

What it refuses (`BUDGET_CANCELLATION_RECOVERY_INVALID`, nothing released): a
reservation another requisition created, one whose lineage is not the pinned
drawdown line and source, one that is Converted, Partially Converted, Released
for another reason or has a commitment, one whose history shows any effect
beyond reserving and revalidating, and one whose remaining amount is not its
original amount (a partial legacy effect is never repaired by guessing).
`BUDGET_CANCELLATION_RECOVERY_CONFLICT`: the reservation has changed since the
revision Requisitions pinned, or a release already recorded for this
cancellation and drawdown line carried different facts.

It skips the open-Budget check on purpose: a release only lowers a hold, and the
displayed historical Available difference on a Closed Budget is not authority to
reserve there. The closure is recorded on the release row. Authenticated by the
Requisitions service principal only (`budget_service_principal`); in-process,
never a web endpoint; it never commits.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_budget.services.budget_audit_contracts import EVENT_RELEASED, EVENT_RESERVED, EVENT_REVALIDATED, record_event
from kentender_budget.services.budget_check_reserve_contracts import _resolve_reservation
from kentender_budget.services.budget_commitment_contracts import _current_line_version, _idempotent, _require_key
from kentender_budget.services.budget_locking import locked_doc, lock_budgets_of_lines
from kentender_budget.services.budget_money import parse_money, scale_for, stored, text
from kentender_budget.services.budget_service_principal import (
	ACTION_RELEASE_CANCELLED,
	PRINCIPAL_LABEL,
	PRINCIPAL_REQUISITIONS,
	refuse,
	require_principal,
)
from kentender_budget.services.budget_write_family import budget_write

RELEASE = "Reservation Cancellation Release"
REASON = "TenderCancelled"
INVALID = "BUDGET_CANCELLATION_RECOVERY_INVALID"
CONFLICT = "BUDGET_CANCELLATION_RECOVERY_CONFLICT"
MESSAGES = {
	INVALID: "The linked records do not support releasing this reservation. Review the recorded issue.",
	CONFLICT: "This reservation has changed. Review the linked recovery issue before trying again.",
}
#: A reservation that is still just a hold has only ever been reserved and (perhaps) revalidated.
UNTOUCHED_EVENTS = frozenset({EVENT_RESERVED, EVENT_REVALIDATED})
RELEASABLE_STATUSES = ("Active", "Needs Attention")


class CancellationReleaseError(frappe.ValidationError):
	"""A typed refusal: `code` is one of the two Budget recovery codes, `detail` names the reservation and the cause."""

	def __init__(self, code: str, detail: dict[str, Any] | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(MESSAGES[code])


def _fail(code: str, **detail) -> None:
	log = getattr(frappe.local, "message_log", None)
	if log is not None:
		log.append({"message": MESSAGES[code], "title": code, "indicator": "red", "kt_budget": {"code": code, "detail": detail}})
	raise CancellationReleaseError(code, detail)


def release_key(cancellation_id: str, drawdown_line_id: str) -> str:
	return f"{(cancellation_id or '').strip()}:{(drawdown_line_id or '').strip()}"


def _digest(cancellation_id: str, requisition_reference: str, reservation: str, drawdown_line_id: str, plan_source_allocation: str, amount: str) -> str:
	"""The facts a release of this cancellation and drawdown line carried, so an identical replay is recognised and a changed one is a conflict."""
	body = {
		"cancellation_id": cancellation_id, "requisition": requisition_reference, "reservation": reservation,
		"drawdown_line_id": drawdown_line_id, "plan_source_allocation": plan_source_allocation, "amount": amount,
	}
	return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


# --------------------------------------------------------------------------
# What is true of one reservation now
# --------------------------------------------------------------------------


def _facts(doc, *, locked: bool) -> dict[str, Any]:
	"""The reservation's history as last committed (a locking read when `locked`, because MariaDB runs at
	REPEATABLE READ and a plain read could miss an effect another command committed while this one waited)."""
	suffix = " for update" if locked else ""
	commitment = frappe.db.get_value("Procurement Commitment", {"reservation": doc.name}, "name", for_update=locked)
	events = sorted(row[0] for row in frappe.db.sql("select event_type from `tabBudget Audit Event` where reservation = %s" + suffix, (doc.name,)))
	released = frappe.db.get_value(RELEASE, {"reservation": doc.name}, ["name", "release_key", "payload_digest"], as_dict=True, for_update=locked)
	return {"commitment": commitment or "", "events": events, "released": released}


def revision_of(doc, facts: dict[str, Any]) -> str:
	"""The revision token Requisitions pins: it changes with any status, amount, commitment or ledger effect."""
	scale = scale_for(doc.currency)
	body = {
		"status": doc.status, "original": text(stored(doc.original_amount, scale=scale), scale=scale), "remaining": text(stored(doc.remaining_amount, scale=scale), scale=scale),
		"commitment": facts["commitment"], "events": facts["events"], "released": (facts["released"] or {}).get("name") or "",
	}
	return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _assess(doc, row: dict[str, Any], *, caller, key: str, digest: str, facts: dict[str, Any]) -> tuple[str, dict[str, Any]]:
	"""`ok`, `reused` (already released by this very cancellation with these facts), `invalid` or `conflict`, with the cause."""
	scale = scale_for(doc.currency)
	detail = {"reservation": doc.name, "drawdown_line_id": row["drawdown_line_id"]}
	released = facts["released"]
	if released:
		if released.release_key == key and released.payload_digest == digest:
			return "reused", detail
		if released.release_key == key:
			return "conflict", {**detail, "cause": "A release for this cancellation and drawdown line was recorded with different facts."}
		return "invalid", {**detail, "cause": "The reservation was already released by another cancellation."}
	if doc.calling_module != PRINCIPAL_LABEL[PRINCIPAL_REQUISITIONS] or (doc.caller_reference or "") != caller.reference:
		return "invalid", {**detail, "cause": "The reservation was not created by this Requisition."}
	if (doc.drawdown_line_id or "") != row["drawdown_line_id"] or (row["plan_source_allocation"] and (doc.plan_source_allocation or "") != row["plan_source_allocation"]):
		return "invalid", {**detail, "cause": "The reservation does not belong to the pinned drawdown line and source."}
	if doc.status == "Released":
		return "invalid", {**detail, "cause": "The reservation was released for another reason."}
	if doc.status in ("Converted", "Partially Converted") or facts["commitment"]:
		return "invalid", {**detail, "cause": "The reservation has been converted, wholly or in part.", "commitment": facts["commitment"]}
	if doc.status not in RELEASABLE_STATUSES:
		return "invalid", {**detail, "cause": "The reservation is not in a state that can be released.", "status": doc.status}
	other = sorted(set(facts["events"]) - UNTOUCHED_EVENTS)
	if other:
		return "invalid", {**detail, "cause": "The reservation's history shows an effect other than reserving it.", "events": other}
	original, remaining = stored(doc.original_amount, scale=scale), stored(doc.remaining_amount, scale=scale)
	if remaining != original:
		return "invalid", {**detail, "cause": "Part of the reservation has already been used or released.", "original": text(original, scale=scale), "remaining": text(remaining, scale=scale)}
	if original != row["amount"]:
		return "invalid", {**detail, "cause": "The reservation's original amount differs from the amount authorised for this drawdown line.", "expected": text(row["amount"], scale=scale), "actual": text(original, scale=scale)}
	if row["expected_revision"] and revision_of(doc, facts) != row["expected_revision"]:
		return "conflict", {**detail, "cause": "The reservation changed after its evidence was pinned."}
	return "ok", detail


def _parse_rows(releases) -> list[dict[str, Any]]:
	if not releases:
		_fail(INVALID, cause="No reservation was named.")
	rows, seen = [], set()
	for spec in releases:
		reservation = str(spec.get("reservation") or "").strip()
		line = str(spec.get("drawdown_line_id") or "").strip()
		if not reservation or not line:
			_fail(INVALID, cause="A reservation and its originating drawdown line must both be named.")
		try:
			doc = _resolve_reservation(reservation)
		except frappe.DoesNotExistError:
			_fail(INVALID, reservation=reservation, cause="The reservation is not recorded.")
		if doc.name in seen:
			_fail(INVALID, reservation=doc.name, cause="A reservation appears more than once.")
		seen.add(doc.name)
		rows.append(
			{
				"name": doc.name, "drawdown_line_id": line, "plan_source_allocation": str(spec.get("plan_source_allocation") or "").strip(),
				"amount": parse_money(spec.get("amount"), scale=scale_for(doc.currency), field="amount"), "expected_revision": str(spec.get("expected_revision") or "").strip(),
			}
		)
	return sorted(rows, key=lambda r: r["name"])


def _caller_for(caller, requisition_reference: str):
	caller = require_principal(caller, ACTION_RELEASE_CANCELLED)
	if not caller.reference or caller.reference != (requisition_reference or "").strip():
		refuse(_("Requisitions may release only the reservations of the Requisition it acts for."))
	return caller


# --------------------------------------------------------------------------
# The read Requisitions pins before it takes any lock
# --------------------------------------------------------------------------


def get_cancellation_release_basis(*, cancellation_id: str, requisition_reference: str, releases: list[dict[str, Any]], caller=None) -> dict[str, Any]:
	"""Budget's own account of each reservation, for Requisitions to pin: whether a release would be supported now, why not, and the
	revision token. A plain read; the release decides again under the locks."""
	caller = _caller_for(caller, requisition_reference)
	out = []
	for row in _parse_rows(releases):
		doc = frappe.get_doc("Funding Reservation", row["name"])
		facts = _facts(doc, locked=False)
		key = release_key(cancellation_id, row["drawdown_line_id"])
		scale = scale_for(doc.currency)
		digest = _digest(cancellation_id, caller.reference, doc.name, row["drawdown_line_id"], row["plan_source_allocation"], text(row["amount"], scale=scale))
		state, detail = _assess(doc, {**row, "expected_revision": ""}, caller=caller, key=key, digest=digest, facts=facts)
		out.append(
			{
				"reservation": doc.name, "drawdown_line_id": row["drawdown_line_id"], "verdict": state, "detail": detail, "revision": revision_of(doc, facts),
				"status": doc.status, "budget": doc.budget, "budget_line": doc.budget_line, "original_amount": text(stored(doc.original_amount, scale=scale), scale=scale),
				"remaining_amount": text(stored(doc.remaining_amount, scale=scale), scale=scale), "currency": doc.currency,
				"closed_budget": bool(frappe.db.get_value("Procurement Budget Version", {"budget": doc.budget, "status": "Closed"}, "name")),
			}
		)
	return {"ok": True, "reservations": out, "supported": all(r["verdict"] in ("ok", "reused") for r in out)}


# --------------------------------------------------------------------------
# The release
# --------------------------------------------------------------------------


def release_reservations_for_cancelled_tender(
	*, recovery_id: str, cancellation_id: str, requisition_reference: str, releases: list[dict[str, Any]], idempotency_key: str, caller=None,
) -> dict[str, Any]:
	"""§9.5 — release the complete exact set of one cancelled Tender's unused reservations, or none of it. `releases` is
	`[{"reservation", "drawdown_line_id", "plan_source_allocation", "amount", "expected_revision"}]`. A replay with the same key returns the first
	result; a new key finds the unique release row and reuses it; the same key with different facts is an idempotency conflict."""
	caller = _caller_for(caller, requisition_reference)
	key = _require_key(idempotency_key)
	recovery_id, cancellation_id = (recovery_id or "").strip(), (cancellation_id or "").strip()
	if not (recovery_id and cancellation_id):
		_fail(INVALID, cause="The recovery and the cancellation must be named.")
	rows = _parse_rows(releases)
	params = {
		"recovery_id": recovery_id, "cancellation_id": cancellation_id,
		"releases": [{k: (text(v, scale=2) if isinstance(v, Decimal) else v) for k, v in r.items()} for r in rows],
	}
	return _idempotent(
		action=ACTION_RELEASE_CANCELLED, caller=caller, key=key, params=params,
		fn=lambda: _release_set(rows, caller, recovery_id, cancellation_id, key),
		budget_for=lambda result: ((result.get("released") or [{}])[0]).get("budget"),
	)


def _release_set(rows: list[dict[str, Any]], caller, recovery_id: str, cancellation_id: str, command_key: str) -> dict[str, Any]:
	savepoint = f"cr_{frappe.generate_hash(length=10)}"
	frappe.db.savepoint(savepoint)
	try:
		# the shared Budget lock order: every Version row of each Budget, then each Line row, then the reservations in name order
		lock_budgets_of_lines([frappe.db.get_value("Funding Reservation", r["name"], "budget_line") for r in rows])
		docs = {r["name"]: locked_doc("Funding Reservation", r["name"]) for r in rows}
		decided = []
		for row in rows:
			doc = docs[row["name"]]
			scale = scale_for(doc.currency)
			key = release_key(cancellation_id, row["drawdown_line_id"])
			digest = _digest(cancellation_id, caller.reference, doc.name, row["drawdown_line_id"], row["plan_source_allocation"], text(row["amount"], scale=scale))
			facts = _facts(doc, locked=True)
			state, detail = _assess(doc, row, caller=caller, key=key, digest=digest, facts=facts)
			if state in ("invalid", "conflict"):
				_fail(INVALID if state == "invalid" else CONFLICT, **detail)
			decided.append((row, doc, key, digest, facts, state))

		released = []
		for row, doc, key, digest, facts, state in decided:
			scale = scale_for(doc.currency)
			amount = row["amount"]
			if state == "reused":
				release = frappe.get_doc(RELEASE, facts["released"].name)
				released.append(_row_result(doc, release, reused=True))
				continue
			version = _current_line_version(doc.budget_line, for_update=True)
			before = _position(doc.budget_line, version)
			doc.remaining_amount = Decimal(0)
			doc.status = "Released"
			with budget_write():
				doc.save(ignore_permissions=True)
			after = _position(doc.budget_line, version)
			closed = bool(frappe.db.get_value("Procurement Budget Version", {"budget": doc.budget, "status": "Closed"}, "name", for_update=True))
			event = record_event(
				budget=doc.budget, budget_line=doc.budget_line, reservation=doc.name, event_type=EVENT_RELEASED, actor=frappe.session.user,
				correlation_id=f"{command_key}#{doc.name}", calling_module=PRINCIPAL_LABEL[PRINCIPAL_REQUISITIONS],
				downstream_reference=f"{recovery_id}:{cancellation_id}", amount=amount, currency=doc.currency,
				reason=f"{REASON}: Requisition {caller.reference}; drawdown line {row['drawdown_line_id']}; source {doc.plan_source_allocation or ''}",
				before=before, after=after,
			)
			with budget_write():
				release = frappe.get_doc(
					{
						"doctype": RELEASE, "release_key": key, "recovery_id": recovery_id, "cancellation_id": cancellation_id,
						"requisition_reference": caller.reference, "reservation": doc.name, "drawdown_line_id": row["drawdown_line_id"],
						"plan_source_allocation": doc.plan_source_allocation or "", "budget": doc.budget, "budget_line": doc.budget_line,
						"amount": amount, "currency": doc.currency, "closed_context": "Budget Closed" if closed else "", "payload_digest": digest,
						"audit_event": event, "released_at": now_datetime(), "fixture_namespace": doc.fixture_namespace or "",
					}
				).insert(ignore_permissions=True)
			doc.reload()
			released.append(_row_result(doc, release, reused=False))
		frappe.db.release_savepoint(savepoint)
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		raise
	scale = scale_for(docs[rows[0]["name"]].currency)
	total = sum((r["amount"] for r in rows), Decimal(0))
	return {"ok": True, "released": released, "total": text(total, scale=scale), "all_reused": all(r["reused"] for r in released)}


def _position(budget_line: str, version) -> dict[str, float]:
	from kentender_budget.services.budget_contracts import _line_position_exact

	exact = _line_position_exact(budget_line, version, for_update=True)
	return {key: float(value) for key, value in exact.items()}


def _row_result(doc, release, *, reused: bool) -> dict[str, Any]:
	scale = scale_for(doc.currency)
	facts = _facts(doc, locked=False)
	return {
		"reservation": doc.name, "reservation_code": doc.generated_reference, "budget": doc.budget, "budget_line": doc.budget_line, "status": doc.status,
		"amount": text(stored(release.amount, scale=scale), scale=scale), "currency": doc.currency, "release": release.name, "ledger_event": release.audit_event,
		"drawdown_line_id": release.drawdown_line_id, "closure": release.closed_context or "", "reused": reused, "revision": revision_of(doc, facts),
	}
