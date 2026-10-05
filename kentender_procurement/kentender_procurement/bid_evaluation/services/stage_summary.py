# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Evaluation's summary on the Tender record (OVS-CHG-001 v0.6 §4, §4.1, §8,
§13; plan D4; tracker OVS6-0303).

The Accounting Officer and the Head of Procurement Function see administrative
facts until a report version is delivered, and the decision and its reason
after. A Head of User Department whose unit contributed sees a department-level
summary of the delivered outcome. A reader who may not know the evaluation
exists gets nothing at all. Everything after delivery comes from the frozen
delivered version (`oversight.py`), never the live case."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import next_steps, oversight, people, reads, records, roster
from kentender_procurement.tenders.services import stage_summary as ss

KEY, LABEL = "bid-evaluation", "Bid evaluation"
STATUS_ONLY_NOTICE = "Bid details are shared with you when the committee's report is sent."


def for_tender(*, tender: str, user: str) -> list[dict[str, Any]]:
	case = records.case_for(tender)
	if not case:
		return []
	doc = frappe.get_doc(records.CASE, case)
	a = reads.access(doc, user)
	if not a["read"]:
		return []
	return ss.guarded(KEY, LABEL, lambda: _build(doc, a))


def _recommendation(rec: dict[str, Any]) -> list[dict[str, str]]:
	"""The decision as facts: the recommended bidder, or the outcome when there is none."""
	outcome = cstr(rec.get("outcome"))
	if outcome == "Recommendation" and rec.get("recommended"):
		return [ss.fact("Recommendation", rec["recommended"].get("bidder"))]
	return [ss.fact("Outcome", outcome)]


def _build(doc, a: dict[str, Any]) -> dict[str, Any]:
	ref = doc.tender_reference
	rows = oversight.deliveries(doc.name)
	returned = oversight.correction(doc, rows)
	status = "Returned for correction" if returned else doc.state
	links = [ss.link("view-record", "View evaluation", ["tenders", ref, "evaluation"])]
	outstanding = {"text": returned["headline"], "holder": ""} if returned else None
	if rows and a["report"]:
		links.append(ss.link("view-report", "View report", ["tenders", ref, "evaluation", "report"]))

	if rows and a["department"]:
		d = oversight.department_summary(doc)
		facts = [*_recommendation({"outcome": d["outcome"], "recommended": {"bidder": d["recommended_bidder"]} if d["recommended_bidder"] else None}),
			ss.fact("Evaluated total", d["evaluated_total"]), ss.fact("Report sent", d["delivered"])]
		return ss.summary(key=KEY, label=LABEL, status=status, disclosure=ss.SUMMARY, facts=facts, outcome={"label": "Outcome", "value": d["outcome"]},
			recorded_at=d["delivered"], reason=d["reason"], outstanding=outstanding, version=f"Report {d['version_number']}", links=links)

	if rows and (a["oversight_full"] or a["report"]):
		d = oversight.delivered_report(doc)
		rec, summary = d["recommendation"], d["summary"]
		facts = [*_recommendation(rec), ss.fact("Evaluated total", summary.get("evaluated_total")), ss.fact("Report sent", d["delivered"]), ss.fact("Sent to", d["recipient_name"])]
		return ss.summary(key=KEY, label=LABEL, status=status, disclosure=ss.FULL, facts=facts, outcome={"label": "Outcome", "value": cstr(rec.get("outcome"))},
			actor=d["recipient_name"], recorded_at=d["delivered"], reason=cstr(rec.get("reason")), outstanding=outstanding, version=f"Report {d['version_number']}", links=links)

	# administrative facts only
	facts = []
	appointment = roster.current_appointment(doc.name)
	if appointment:
		facts.append(ss.fact("Committee appointed", next_steps.when(appointment.appointed_at)))
	deadline = reads.conditions(doc)["evaluation_deadline"]
	if deadline and doc.state in ("Reviewing", "Signing"):
		facts.append(ss.fact("Evaluation deadline", deadline))
	chair = roster.chair(doc.name)
	if chair:
		facts.append(ss.fact("Chair", people.full_name(chair)))
	outcome = None
	if doc.state == "No evaluation required":
		outcome = {"label": "Outcome", "value": "No bids were received"}
	elif doc.state == "Cancelled":
		event = next((e for e in reads.work(doc, a).get("owner_events", []) if e["kind"] == "Cancellation"), None)
		if event:
			facts += [ss.fact("Cancelled", event["received"]), ss.fact("Instruction", event["instruction_reference"])]
	return ss.summary(key=KEY, label=LABEL, status=status, disclosure=ss.STATUS_ONLY, facts=facts, outcome=outcome, outstanding=outstanding,
		notice="" if a["bids"] or doc.state in ("No evaluation required", "Cancelled") else STATUS_ONLY_NOTICE, links=links)
