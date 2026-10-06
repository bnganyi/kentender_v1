# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening's summary on the Tender record (OVS-CHG-001 v0.6 §4, §4.1, §8,
§13; BOP-CHG-001 v0.11 §6, §7; plan D4; tracker OVS6-0302).

The Accounting Officer, the Head of Procurement Function, the Procurement
Officer and the Auditor read the opening as BOP already lets them. Until the
opening is complete they see its status and the scheduled time, with no bid
count; once it is complete they also see when it finished and how many bids
were opened. A Head of User Department whose unit contributed sees the same
completed facts as a summary and has no opening record to open (OVS-P01: no
decryption or ceremony power). A technical reader sees status only."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_opening.services import labels, people, reads, records
from kentender_procurement.tenders.services import stage_summary as ss
from kentender_procurement.tenders.services import tender_authorization as authz

KEY, LABEL = "bid-opening", "Bid opening"
#: where BOP's own words differ from the stored state (`reads.status_line`)
STATUS = {"Opening": "In session", "Interrupted": "Paused", "Not held": "Did not take place", "Cancelled after start": "Ended — Tender cancelled",
	"Opening complete": "Complete"}


def for_tender(*, tender: str, user: str) -> list[dict[str, Any]]:
	case = records.case_for(tender)
	if not case:
		return []
	readable = reads.can_read(case, user)
	department = not readable and authz.is_department_head_of(frappe.get_doc("Tender", tender), user)
	if not (readable or department):
		return []
	doc = frappe.get_doc(records.CASE, case)
	return ss.guarded(KEY, LABEL, lambda: _build(doc, readable=readable, department=department, technical=people.technical(user)))


def _build(doc, *, readable: bool, department: bool, technical: bool) -> dict[str, Any]:
	status = STATUS.get(doc.state, doc.state)
	links = [ss.link("view-record", "View opening record", ["tenders", doc.tender_reference, "opening"])] if readable else []
	if doc.state == "Opening complete" and not technical:
		bids = frappe.db.count("Opening Entry", {"opening_case": doc.name})
		facts = [ss.fact("Opening completed", labels.when_seconds(doc.completed_at)), ss.fact("Bids opened", bids if doc.outcome != "No bids" else 0)]
		if readable:
			facts.append(ss.fact("Minutes", frappe.db.get_value("Proceeding", doc.proceeding, "state") if doc.proceeding else ""))
		return ss.summary(key=KEY, label=LABEL, status=status, disclosure=ss.FULL if readable else ss.SUMMARY, facts=facts,
			outcome={"label": "Outcome", "value": doc.outcome} if doc.outcome else None, recorded_at=labels.when_seconds(doc.completed_at), links=links)
	facts = []
	if doc.state in ("Awaiting deadline", "Ready to open", "Not held"):
		facts.append(ss.fact("Opening scheduled for", labels.when(doc.effective_deadline)))
	elif doc.started_at:
		facts.append(ss.fact("Opening started", labels.when_seconds(doc.started_at)))
	return ss.summary(key=KEY, label=LABEL, status=status, disclosure=ss.STATUS_ONLY, facts=facts, links=links)
