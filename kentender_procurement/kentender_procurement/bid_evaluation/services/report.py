# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The evaluation report (EVL-CHG-001 v0.4 §5.5, §9.12; plan D19; tracker
EVL4-901, EVL4-902, EVL4-913; boards D07-DRAFT, D07-PREVIEW, D07-NO-RESPONSIVE,
D07-NO-AGREEMENT, D07-TIE, D07-FUNDING, D07-EXPIRED).

Generated continuously from the authoritative record, in the §9.12 order:
summary first; Tender and committee; Bid findings; Financial comparison;
Clarifications and committee record; Recommendation and reasons; signatures
last. The secretary edits only the narrative, never a source fact. The
outcome is exactly one of: a recommendation; No responsive bids; No single
recommendation — equal evaluated totals; No agreed recommendation; No current
recommendation — tender validity expired; or a qualified report of an
unresolved rule, discrepancy or evidence issue. A funding shortfall only
qualifies a recommendation. The report never constitutes an award."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_evaluation.services import aggregate, checks, comparison, member_department, people, records, roster, timers
from kentender_procurement.services import sequence

REPORT = "Evaluation Report Version"
NOT_AN_AWARD = "This report does not constitute an award."
EXPIRED = "No current recommendation — tender validity expired"
NO_AGREEMENT = "No agreed recommendation"
QUALIFIED = "Qualified report"
SECTIONS = ("Tender and committee", "Bid findings", "Financial comparison", "Clarifications and committee record", "Recommendation and reasons")


def draft(doc) -> Any:
	"""The current draft version, created on first use."""
	name = frappe.db.get_value(REPORT, {"evaluation_case": doc.name, "state": "Draft"}, "name")
	if name:
		return frappe.get_doc(REPORT, name)
	number = sequence.next_count(REPORT, {"evaluation_case": doc.name})
	previous = frappe.db.get_value(REPORT, {"evaluation_case": doc.name}, ["narrative"], as_dict=True, order_by="version_number desc")
	return records.insert(frappe.get_doc({"doctype": REPORT, "report_id": f"{doc.name}-RPT-{number:02d}", "evaluation_case": doc.name, "version_number": number,
		"state": "Draft", "narrative": (previous or {}).get("narrative") or "", "record_version": 1}))


def _when(value) -> str:
	return get_datetime(value).strftime("%-d %b %Y, %H:%M") + " EAT" if value else ""


def _committee(doc) -> dict[str, Any]:
	appointment = roster.current_appointment(doc.name)
	secretary = frappe.db.get_value("Evaluation Secretary Appointment", {"evaluation_case": doc.name, "status": "Current"},
		["secretary_user", "full_name", "appointment_reference", "assigned_at", "basis", "appointing_authority", "assigned_by"], as_dict=True)
	return {
		"members": [{"name": m["full_name"], "department": member_department.display(m["department"]), "capacity": m["capacity"], "user": m["member_user"]}
			for m in roster.current_members(doc.name)],
		"appointment_reference": cstr(appointment.appointment_reference) if appointment else "",
		"appointed_at": _when(appointment.appointed_at) if appointment else "",
		"secretary": {"name": secretary.full_name, "reference": secretary.appointment_reference, "user": secretary.secretary_user, "basis": cstr(secretary.basis),
			"authority": cstr(secretary.appointing_authority), "at": _when(secretary.assigned_at),
			"by": cstr(frappe.db.get_value("User", secretary.assigned_by, "full_name")) or cstr(secretary.assigned_by)} if secretary else None,
		"history": _appointment_history(doc.name),
	}


def _appointment_history(case: str) -> list[dict[str, Any]]:
	"""The appointment record and its history: each appointment with its reference, the appointing officer, the time and the roster it produced, and each
	later completion of a Not recorded department (EVL-CHG-001 v0.7 §3), and every secretary record (by office, then each written delegation, EVL-CHG-001 v0.8
	§3), in time order. The reference and the officer are recorded by the server."""
	out: list[dict[str, Any]] = []
	for a in frappe.get_all("Evaluation Appointment", filters={"evaluation_case": case}, fields=["name", "version_number", "change_kind", "appointment_reference", "reason",
			"appointed_at", "appointed_by"], order_by="version_number asc"):
		members = frappe.get_all("Evaluation Committee Member", filters={"parent": a.name, "parenttype": "Evaluation Appointment"},
			fields=["full_name", "capacity", "status", "member_user", "department", "department_recorded_by", "department_recorded_at"], order_by="idx asc")
		out.append({"version": a.version_number, "kind": a.change_kind, "reference": a.appointment_reference, "reason": cstr(a.reason), "at": _when(a.appointed_at),
			"by": cstr(frappe.db.get_value("User", a.appointed_by, "full_name")) or cstr(a.appointed_by), "_when": a.appointed_at,
			"members": [{"name": m.full_name, "capacity": m.capacity} for m in members if m.status == "Current"]})
		for m in members:
			if m.department_recorded_at:
				out.append({"version": a.version_number, "kind": "Department recorded", "person": m.full_name, "department": m.department,
					"by": cstr(frappe.db.get_value("User", m.department_recorded_by, "full_name")) or cstr(m.department_recorded_by), "at": _when(m.department_recorded_at),
					"_when": m.department_recorded_at})
	for s in frappe.get_all("Evaluation Secretary Appointment", filters={"evaluation_case": case}, fields=["full_name", "basis", "appointment_reference", "appointing_authority",
			"assigned_at", "assigned_by", "status", "source_appointment"], order_by="creation asc, name asc"):
		out.append({"kind": "Secretary by office" if s.basis == "By office" else "Delegated", "person": s.full_name, "reference": s.appointment_reference,
			"authority": cstr(s.appointing_authority), "by": cstr(frappe.db.get_value("User", s.assigned_by, "full_name")) or cstr(s.assigned_by), "at": _when(s.assigned_at),
			"current": s.status == "Current", "_when": s.assigned_at,
			"appointment": cstr(frappe.db.get_value("Evaluation Appointment", s.source_appointment, "appointment_reference")) if s.source_appointment else ""})
	out.sort(key=lambda h: (get_datetime(h["_when"]) if h["_when"] else get_datetime("1970-01-01"), {"Department recorded": 1, "Secretary by office": 2, "Delegated": 3}.get(h["kind"], 0)))
	for h in out:
		h.pop("_when", None)
	return out


def _findings(doc) -> list[dict[str, Any]]:
	run = checks.current_run(doc.name)
	human = aggregate.human_record(doc.name)
	out = []
	for bid in frappe.get_all("Evaluation Bid", filters={"evaluation_case": doc.name}, fields=["name", "tenderer_name", "entry_number"], order_by="entry_number asc"):
		res = aggregate.bid_results(doc.name, run, bid.name, human) if run else {"requirements": [], "groups": {}, "responsiveness": ""}
		def table(group):
			return [{"requirement": r["label"], "requirement_key": r["requirement_key"], "evidence": "; ".join(dict.fromkeys(
				c.offered_display for c in r["checks"] if c.offered_display and c.result != aggregate.NA)), "finding": r["result"], "basis": r["basis"],
				"reason": r["reason"], "qualified": r["qualified"]} for r in res["requirements"] if r["group_id"] == group]
		out.append({"bid": bid.name, "bidder": bid.tenderer_name, "eligibility": table(aggregate.ELIGIBILITY), "technical": table(aggregate.TECHNICAL),
			"groups": res["groups"], "responsiveness": res["responsiveness"]})
	return out


def _price(doc) -> list[dict[str, Any]]:
	run = checks.current_run(doc.name)
	out = []
	for row in frappe.get_all("Evaluation Check Result", filters={"check_run": run, "check_kind": "calculation"}, fields=["evaluation_bid", "calculation_json"]) if run else []:
		calc = json.loads(row.calculation_json or "{}")
		out.append({"bid": row.evaluation_bid, "lines": calc.get("lines") or [], "currency": calc.get("currency"), "submitted_total": calc.get("submitted_total"),
			"calculated_total": calc.get("calculated_total"), "problems": calc.get("problems") or []})
	return out


def _clarifications(doc) -> list[dict[str, Any]]:
	out = []
	for c in frappe.get_all("Evaluation Clarification", filters={"evaluation_case": doc.name}, fields=["name", "question", "reply_scope", "reply_deadline", "sent_at",
			"status", "disposition", "disposition_result", "disposition_reason", "closed_at", "withdrawal_reason", "replaces"], order_by="creation asc"):
		reply = frappe.db.get_value("Evaluation Clarification Reply", {"clarification": c.name, "state": "Sent"}, ["body", "received_at", "timeliness"], as_dict=True)
		out.append({**{k: cstr(v) for k, v in c.items()}, "deadline": _when(c.reply_deadline), "sent": _when(c.sent_at), "closed": _when(c.closed_at),
			"reply": {"body": reply.body, "received": _when(reply.received_at), "timeliness": reply.timeliness} if reply else None})
	return out


def _sessions(doc) -> list[dict[str, Any]]:
	if not doc.proceeding:
		return []
	out = []
	for s in frappe.get_all("Proceeding Session", filters={"proceeding": doc.proceeding}, fields=["session_id", "session_number", "subject", "actual_start", "actual_end"],
			order_by="session_number asc"):
		attendance = frappe.get_all("Proceeding Attendance", filters={"session": s.session_id, "movement": "Arrival"}, fields=["person_name", "capacity", "occurred_at"],
			order_by="occurred_at asc")
		out.append({"number": s.session_number, "subject": s.subject, "start": _when(s.actual_start), "end": _when(s.actual_end),
			"attendance": [{"name": a.person_name, "capacity": a.capacity, "joined": _when(a.occurred_at)} for a in attendance]})
	return out


def _disagreements(doc) -> list[dict[str, Any]]:
	return [{"member": people.full_name(d.member_user), "statement": d.statement, "at": _when(d.recorded_at)} for d in frappe.get_all("Evaluation Disagreement",
		filters={"evaluation_case": doc.name}, fields=["member_user", "statement", "recorded_at"], order_by="recorded_at asc")]


def _diligence(doc) -> str:
	from kentender_procurement.bid_evaluation.services import diligence

	plan = diligence.current_plan(doc.name)
	if plan:
		outcome = frappe.db.get_value("Evaluation Conclusion", {"evaluation_case": doc.name, "kind": "Verification outcome"}, "reason", order_by="recorded_at desc")
		return f"{plan.scope}. {cstr(outcome) or 'Verification in progress.'}".strip()
	basis = frappe.db.get_value("Evaluation Conclusion", {"evaluation_case": doc.name, "kind": "Due diligence basis"}, "reason", order_by="recorded_at desc")
	return cstr(basis) or "No due-diligence exercise or basis has been recorded."


def outcome(doc, table: dict[str, Any] | None = None) -> dict[str, Any]:
	"""The report's single outcome and its qualifications."""
	table = table or comparison.compare(doc.name)
	dated = timers.dated(doc)
	qualifications = []
	unresolved = frappe.get_all("Evaluation Conclusion", filters={"evaluation_case": doc.name, "kind": "Qualified report"}, fields=["reason"])
	qualifications += [cstr(q.reason) for q in unresolved]
	if frappe.db.exists("Evaluation Conclusion", {"evaluation_case": doc.name, "kind": NO_AGREEMENT}):
		return {"outcome": NO_AGREEMENT, "recommended": None, "reason": frappe.db.get_value("Evaluation Conclusion", {"evaluation_case": doc.name, "kind": NO_AGREEMENT},
			"reason", order_by="recorded_at desc"), "qualifications": qualifications, "provisional": False}
	if table["outcome"] == "Recommendation":
		if dated["validity_expired"]:
			return {"outcome": EXPIRED, "recommended": None, "reason": f"Tender validity ended {_when(dated['validity_end'])}; no extension recorded.",
				"qualifications": qualifications, "provisional": False}
		if unresolved:
			return {"outcome": QUALIFIED, "recommended": None, "reason": "; ".join(qualifications), "qualifications": qualifications, "provisional": False}
		rec = table["recommended"]
		if table.get("funding") and table["funding"].get("qualification"):
			qualifications.append(table["funding"]["qualification"])
		return {"outcome": "Recommendation", "recommended": rec, "reason": table["reason"], "qualifications": qualifications, "provisional": False,
			"funding": table.get("funding")}
	if table["outcome"]:
		return {"outcome": table["outcome"], "recommended": None, "reason": table["reason"], "qualifications": qualifications, "provisional": False}
	return {"outcome": None, "recommended": None, "reason": "", "qualifications": qualifications, "provisional": True}


def build(doc) -> dict[str, Any]:
	table = comparison.compare(doc.name)
	result = outcome(doc, table)
	rec = result.get("recommended")
	summary = {
		"outcome": result["outcome"], "recommendation": f"Recommendation: {rec['bidder']}" if rec else cstr(result["outcome"]),
		"evaluated_total": f"{rec['currency']} {float(rec['evaluated_total']):,.2f}" if rec else "", "reason": result["reason"],
		"qualifications": result["qualifications"], "diligence": _diligence(doc), "not_an_award": NOT_AN_AWARD,
	}
	return {
		"summary": summary,
		"tender_and_committee": {"tender": doc.tender_reference, "title": doc.tender_title, "bids_opened": len(table["rows"]),
			"opening_completed": _when(doc.opening_completed_at), **_committee(doc)},
		"bid_findings": _findings(doc),
		"financial_comparison": {"rows": table["rows"], "prices": _price(doc), "provisional": table["provisional"], "funding": table.get("funding")},
		"clarifications_and_record": {"clarifications": _clarifications(doc), "sessions": _sessions(doc), "disagreements": _disagreements(doc)},
		"recommendation": {**result, "statement": _statement(result), "not_an_award": NOT_AN_AWARD},
		"sections": list(SECTIONS),
	}


def _statement(result: dict[str, Any]) -> str:
	rec = result.get("recommended")
	if rec:
		return f"Recommend {rec['bidder']} at {rec['currency']} {float(rec['evaluated_total']):,.2f}. {result['reason']} {NOT_AN_AWARD}".strip()
	return f"{result['outcome'] or 'No outcome yet'}. {result['reason']} {NOT_AN_AWARD}".strip()


def save_narrative(*, tender: str, narrative: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	"""SaveReportNarrative: the secretary's committee summary, nothing else."""
	from kentender_procurement.bid_evaluation.services import guards

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.secretary(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		guards.open_case(doc).raise_if_any()
		if doc.state != "Reviewing":
			from kentender_procurement.bid_evaluation.services.errors import fail

			fail("EVL_VERSION_CONFLICT", {"reason": "not_reviewing", "state": doc.state})
		report = draft(doc)
		records.check_version(report, expected_version)
		records.bump(report, narrative=cstr(narrative))
		return records.summary(doc, report=report.name, report_version=report.record_version)

	return records.command("SaveReportNarrative", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"narrative": narrative,
		"expected_version": expected_version}, body=body)
