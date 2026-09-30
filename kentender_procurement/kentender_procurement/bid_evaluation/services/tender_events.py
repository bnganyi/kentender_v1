# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ReceiveTenderEvent (EVL-CHG-001 v0.4 §5.7, §6 "Tenders / downstream owner →
Evaluation", §7.2; plan D8, D16; tracker EVL4-911; boards D08-PAUSED,
D08-CANCELLED, P-PREP, P-SIGN, C-PREP, C-SIGN).

Authoritative owner facts are recorded once by their source identity and
applied by their scope; Evaluation never infers a status from an absent
consumer and adds no cancel or resume approval of its own.

- **Suspension** pauses new committee decisions, requests and report
  signing; appointment and declaration continue only where the instruction
  explicitly permits them. Drafts, evidence and history are kept.
- **Resumption** comes only from the same owning authority; commands recheck
  source, roster and validity before any further decision.
- **Cancellation** closes the evaluation and supplier reply actions,
  withdraws pending signing, keeps a factual partial record and creates no
  completion or recommendation. An already delivered report stays historical
  and is marked with the later cancellation.
- **Validity extension**, a **dated rule** and a downstream **award
  decision** are recorded for the timers and the correction route.

Tenders (TPR-CHG-001 v0.13) produces only a cancellation before close today.
On a test environment `record_simulated_event` stands in for the owner events
it cannot yet produce (FU-EVL-02); it is refused elsewhere."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_evaluation.services import clock, prc, records, simulation

EVENT = "Evaluation Source Event"
KINDS = ("Suspension", "Resumption", "Cancellation", "Validity extension", "Award decision", "Dated rule")


def _record(doc, *, event_key: str, kind: str, source: str, source_reference: str = "", authority: str = "", instruction_reference: str = "", reason: str = "",
		effective_at=None, detail: dict | None = None, permitted_actions: list[str] | None = None) -> tuple[Any, bool]:
	name = frappe.db.get_value(EVENT, {"event_key": event_key}, "name")
	if name:
		return frappe.get_doc(EVENT, name), False
	number = frappe.db.count(EVENT, {"evaluation_case": doc.name}) + 1
	row = records.insert(frappe.get_doc({
		"doctype": EVENT, "source_event_id": f"{doc.name}-SE-{number:02d}", "evaluation_case": doc.name, "event_key": event_key, "source": source, "kind": kind,
		"source_reference": source_reference, "authority": authority, "instruction_reference": instruction_reference, "reason": cstr(reason),
		"effective_at": effective_at, "received_at": clock.now(), "detail_json": json.dumps(detail or {}, default=str, sort_keys=True),
		"permitted_actions_json": json.dumps(permitted_actions or []),
		"delivered_context": "After delivery" if doc.state == "Report sent" else "Before delivery",
	}))
	return row, True


def _apply(doc, row, idempotency_key: str) -> None:
	from kentender_procurement.bid_evaluation.services import lifecycle

	event = prc.owner_event(doc, f"Tender{row.kind.replace(' ', '')}", f"source:{row.event_key}", {"kind": row.kind, "reference": row.source_reference,
		"instruction": row.instruction_reference}, idempotency_key=idempotency_key, note=cstr(row.reason))
	if row.kind == "Suspension":
		records.bump(doc, suspended=1, suspension_event=row.name, last_committed_event=event)
	elif row.kind == "Resumption":
		records.bump(doc, suspended=0, suspension_event="", last_committed_event=event)
	elif row.kind == "Cancellation":
		lifecycle.withdraw_signing(doc, kind="Cancellation", reason="The evaluation ended under the recorded cancellation.", idempotency_key=idempotency_key,
			actor=None)
		for name in frappe.get_all("Evaluation Clarification", filters={"evaluation_case": doc.name, "status": ("in", ("Authorised", "Sent"))}, pluck="name"):
			request = frappe.get_doc("Evaluation Clarification", name)
			request.status, request.closed_at, request.closure_reason = "Closed", clock.now(), "Cancelled"
			records.save(request)
		if doc.state != "Report sent":
			from kentender_procurement.bid_evaluation.services import prc_owner
			from kentender_procurement.proceedings.services import record_versions

			with prc_owner.acting(doc.name):
				record_versions.abort(**prc.ref(doc), cancellation_reference=cstr(row.source_reference or row.event_key),
					idempotency_key=prc.key(idempotency_key, "abort"), actor=prc.SYSTEM)
			records.bump(doc, state="Cancelled", cancellation_event=row.name, suspended=0, last_committed_event=event)
		else:
			records.bump(doc, cancellation_event=row.name, last_committed_event=event)  # delivery is not reversed
	else:
		records.bump(doc, last_committed_event=event)


def receive(*, tender: str, event_key: str, kind: str, source: str, **facts) -> dict[str, Any]:
	if kind not in KINDS:
		raise ValueError(f"Unknown owner event kind {kind!r}")

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if doc.state in records.TERMINAL and kind != "Award decision":
			return records.summary(doc, recorded=False, reason="closed")
		row, new = _record(doc, event_key=event_key, kind=kind, source=source, **facts)
		if new:
			_apply(doc, row, event_key)
		return records.summary(doc, recorded=new, source_event=row.name)

	return records.command("ReceiveTenderEvent", tender=tender, idempotency_key=f"tender-event:{event_key}", actor="system",
		payload={"kind": kind, "source": source, **{k: cstr(v) for k, v in facts.items()}}, body=body)


def consume(tender: str) -> int:
	"""The Tenders owner's published facts for this Tender, once each."""
	from kentender_procurement.tenders.services import evaluation_seam as tenders

	if not records.case_for(tender):
		return 0
	count = 0
	for event in tenders.status_events(tender):
		out = receive(tender=tender, event_key=event["event_key"], kind=event["kind"], source=event["source"], source_reference=event["source_reference"],
			authority=event["authority"], reason=event["reason"], effective_at=event["effective_at"])
		count += 1 if out.get("recorded") else 0
	return count


def record_simulated_event(*, tender: str, kind: str, instruction_reference: str, authority: str, reason: str = "", effective_at=None,
		permitted_actions: list[str] | None = None, detail: dict | None = None) -> dict[str, Any]:
	"""Test environment only: an owner event Tenders cannot produce yet."""
	if not simulation.enabled():
		frappe.throw("Simulated owner events exist only on a test environment.")
	return receive(tender=tender, event_key=f"SIM:{kind}:{instruction_reference}", kind=kind, source="Simulation", source_reference=instruction_reference,
		authority=authority, instruction_reference=instruction_reference, reason=reason, effective_at=get_datetime(effective_at) if effective_at else None,
		permitted_actions=permitted_actions, detail=detail)
