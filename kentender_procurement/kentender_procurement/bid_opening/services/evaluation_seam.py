# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening's published reads for Bid Evaluation (EVL-CHG-001 v0.4 §5.1,
§5.6, §6 "BOP → Evaluation"; EVL plan D5; closes FU-BOP-11/12 on uptake).

Evaluation never reads a Bid Opening record directly; it asks here:

- `completion(tender)`: the once-only Evaluation Handoff with its digest
  checked by recomputation. The stored payload is compact JSON while its
  digest is taken over the parsed payload (`records.digest`), so the check
  recomputes from the parsed payload rather than hashing the stored text
  (EVL C5; noted for the next BOP revision, FU-EVL-05).
- `acknowledge(handoff_id)`: the recorded owner take-up, once (EVL v0.4 §12:
  automatic intake is the take-up; there is no manual receipt approval).
- `final_outcome(tender)`: Bids opened / No bids / Not held / Cancelled /
  Incomplete, and never "No bids" for an opening that is incomplete.
- `register_rows(tender)`: the frozen register rows, for cross-checking only.
- `supplements(tender)`: completed-record corrections as new source events.
- `is_excluded_from_evaluation(tender, user)`: the independent opening
  member cannot evaluate the same tender (BOP-A17).

No bid content crosses here: package bytes come from Bid Submission's own
seam, released against this completion (EVL plan D6)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_opening.services import appointment, finish, records

HANDOFF = "Evaluation Handoff"


def _case(tender: str):
	name = records.case_for(tender)
	return frappe.get_doc(records.CASE, name) if name else None


def completion(tender: str) -> dict[str, Any] | None:
	name = frappe.db.get_value(HANDOFF, {"tender": tender}, "name")
	if not name:
		return None
	row = frappe.get_doc(HANDOFF, name)
	try:
		payload = json.loads(row.payload_json or "")
	except ValueError:
		return {"handoff_id": row.handoff_id, "verified": False, "payload": None, "digest": row.handoff_digest}
	return {
		"handoff_id": row.handoff_id, "digest": row.handoff_digest, "verified": records.digest(payload) == row.handoff_digest, "payload": payload,
		"issued_at": row.issued_at, "delivery_status": row.delivery_status, "opening_case": row.opening_case,
	}


def acknowledge(handoff_id: str) -> bool:
	"""Set Delivered once; a second call changes nothing."""
	row = frappe.get_doc(HANDOFF, handoff_id)
	if row.delivery_status == "Delivered":
		return False
	row.delivery_status = "Delivered"
	records.save(row)
	return True


def final_outcome(tender: str) -> dict[str, Any] | None:
	"""The opening's authoritative final outcome, or Incomplete while it is not final."""
	doc = _case(tender)
	if doc is None:
		return None
	if doc.state == "Opening complete":
		outcome = "Bids opened" if doc.outcome == "Bids opened" else "No bids"
	elif doc.state == "Not held":
		outcome = "Not held"
	elif doc.state == "Cancelled after start":
		outcome = "Cancelled"
	else:
		outcome = "Incomplete"
	return {"outcome": outcome, "opening": doc.opening_id, "completed_at": doc.completed_at, "register": cstr(doc.register),
		"evaluation_handoff": cstr(doc.evaluation_handoff), "state": doc.state}


def register_rows(tender: str) -> list[dict[str, Any]]:
	doc = _case(tender)
	return finish.register_rows(doc.name) if doc else []


def supplements(tender: str) -> list[dict[str, Any]]:
	"""Completed-record corrections, oldest first, each with its own identity."""
	doc = _case(tender)
	if doc is None or not doc.proceeding:
		return []
	return frappe.get_all("Proceeding Supplement", filters={"proceeding": doc.proceeding}, fields=["supplement_id", "kind", "correct_information", "reason",
		"author", "recorded_at"], order_by="recorded_at asc")


def is_excluded_from_evaluation(tender: str, user: str) -> bool:
	return appointment.is_excluded_from_evaluation(tender, user)
