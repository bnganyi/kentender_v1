# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The contract's history (CM-CHG-001 v0.8 section 12): one append-only `Contract Event` for each thing that happened, with who did it and the trusted time it was recorded.

An event is written in the same transaction as the change it describes, so history can neither miss a change nor describe one that rolled back. It is also the kept audit
entry (`records.audit`) for the same action. Events are never edited; a correction is a later event."""

from __future__ import annotations

from typing import Any

from kentender_contracts.services import clock, records

EVENT = "Contract Event"


def record(case: str, event_type: str, actor: str, summary: str, **detail: Any) -> Any:
	row = records.new(EVENT, contract_case=case, event_type=event_type, occurred_at=clock.now(), actor=actor, summary=summary, detail_json=records.dumps(detail))
	records.audit(case, event_type, actor, summary=summary)
	return row


def history(case: str) -> list[dict[str, Any]]:
	import frappe

	rows = frappe.get_all(EVENT, filters={"contract_case": case}, fields=["name", "event_type", "occurred_at", "actor", "summary", "detail_json"], order_by="occurred_at asc, creation asc")
	return [{"event": r.name, "type": r.event_type, "at": r.occurred_at, "actor": r.actor, "summary": r.summary, "detail": records.loads(r.detail_json)} for r in rows]
