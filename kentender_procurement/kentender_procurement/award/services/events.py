# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`AwardDecisionRecorded v1` (AWD-CHG-001 v0.4 §4, §5.8, AWD-IF-05;
AWD-AC-031).

Each committed Award or No award decision version retains exactly one
immutable event, created in the same transaction as the decision, and a
delivery record for Contracting — independently of the Award package and its
eligibility gates. A return, an instruction or a notice-only authorisation
creates none. A command retry reuses the original event; a failed delivery
keeps the same event for retry and names a technical owner; receipt completes
delivery, not publication."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.award.services import checks, clock, contracting, people, profile, records, state

EVENT = state.EVENT
TYPE = "AwardDecisionRecorded"
VERSION = 1


def payload(doc, decision) -> dict[str, Any]:
	from kentender_core.utils.instants import to_utc_iso

	out = {
		"event_type": TYPE, "event_version": VERSION, "event_id": f"{decision.name}-EVT", "award_case": doc.name, "tender": doc.tender,
		"tender_reference": doc.tender_reference, "lot": doc.lot or "1", "cycle": decision.cycle, "decision": decision.name, "decision_version": decision.version,
		"outcome": decision.outcome, "accounting_officer": people.full_name(decision.decided_by), "recorded_at": to_utc_iso(decision.decided_at),
		"opinion": decision.opinion, "report": decision.source_report, "legal_profile_version": cstr(profile.current().get("profile_version")),
		"reference": f"{decision.name}-EVT", "fixture_namespace": doc.fixture_namespace,
	}
	if decision.outcome == "Award":
		out.update(supplier=decision.supplier_name, supplier_organisation=decision.supplier_organisation, bid=decision.bid_reference,
			amount=decision.submitted_amount, evaluated_amount=decision.evaluated_amount, currency=decision.currency)
	return out


def record(doc, decision) -> Any:
	"""One event per committed decision version; a retry returns the same one."""
	if decision.outcome not in state.COMMITTED or not decision.committed:
		return None
	name = frappe.db.get_value(EVENT, {"decision": decision.name}, "name")
	if name:
		return frappe.get_doc(EVENT, name)
	body = payload(doc, decision)
	row = records.new(EVENT, event_id=body["event_id"], award_case=doc.name, decision=decision.name, event_type=TYPE, event_version=VERSION,
		payload_json=records.dumps(body), recipient="Contracting", status="Pending", attempts_json="[]", fixture_namespace=doc.fixture_namespace)
	deliver(doc, row)
	return row


def deliver(doc, row) -> str:
	if row.status == "Delivered":
		return row.status
	attempt = {"at": str(clock.now())}
	try:
		result = contracting.deliver_event(records.loads(row.payload_json))
	except contracting.ReceiverUnavailable as exc:
		attempt.update(outcome="Failed", detail=cstr(exc))
		records.append_json(row, "attempts_json", attempt)
		records.update(row, status="Failed")
		checks.open_support_issue(doc, "DeliverAwardDecisionEvent", f"event:{row.name}", "Restore award decision delivery",
			"An award decision event could not be delivered to Contracting. It will be delivered again automatically.")
		return row.status
	attempt.update(outcome="Delivered", receipt=result["receipt"])
	records.append_json(row, "attempts_json", attempt)
	records.update(row, status="Delivered", receipt_reference=result["receipt"], received_at=result.get("received_at") or clock.now())
	checks.support_resolved(f"event:{row.name}")
	return row.status


def retry_pending() -> int:
	count = 0
	for name in frappe.get_all(EVENT, filters={"status": ("in", ("Pending", "Failed"))}, pluck="name"):
		row = frappe.get_doc(EVENT, name)
		doc = frappe.get_doc(records.CASE, row.award_case)
		if deliver(doc, row) == "Delivered":
			count += 1
	return count
