# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Generated reports (CM-CHG-001 v0.8 sections 5.7, 5.15, 7, 8 CM_REPORT, 19.3 CM-R-14 and CM-R-15; plan Phase 8; board D15).

A report is **derived** from recorded facts and never typed: the monthly progress of each contract, the variations that took effect in a quarter, the follow-up of invoices and payments, and the terminations. Each is
generated once for a type and a period; a period uses the site's time with an explicit inclusive start and an exclusive next start; the report keeps its exact **cutoff** and the version of every record it read.

* A source that cannot be read leaves an **Incomplete** draft with the reason and its recovery owner: an incomplete report is never submitted. "No records in this period" is said only after every source was read.
* A regeneration is a **successor**: it never overwrites a submitted report, which keeps its rows exactly.
* The head of procurement submits a reviewed report to the Accounting Officer, or records the actual external submission with its reference, date, destination and copy; no fresh approval of routine submission is
  introduced. Dispatch and delivery are tracked apart: a delivery that failed is recorded as pending delivery and retried, and the submitted rows do not change.
* Recipients, deadlines and statutory formats the sources do not establish are not invented; a report states only what the records hold."""

from __future__ import annotations

from datetime import date
from typing import Any

import frappe
from frappe.utils import add_months, cint, cstr, flt, get_first_day, getdate

from kentender_contracts.services import authority, change, clock, dispatch, events, intents, obligations, payment, position, preflight, records, termination, warranty, work
from kentender_contracts.services.errors import Guards, fail, invalid

REPORT = "Contract Report"
CASE = "Contract Case"
INVOICE = "Contract Invoice"
TYPES: dict[str, dict[str, Any]] = {
	"Progress": {"rule": "CM-R-14", "months": 1, "recipient": "Accounting Officer", "title": "Monthly contract progress"},
	"Variation": {"rule": "CM-R-15", "months": 3, "recipient": "Accounting Officer", "title": "Effective variations"},
	"Payment follow-up": {"rule": "", "months": 1, "recipient": "Finance and head of procurement function", "title": "Payment follow-up"},
	"Termination record": {"rule": "CM-R-16", "months": 1, "recipient": "Accounting Officer; head of procurement function", "title": "Terminations"},
}
CLOSED_LIFECYCLES = ("Active", "Closed", "Terminated")


def get(name: str):
	return frappe.get_doc(REPORT, name)


def period_of(report_type: str, on) -> tuple[date, date]:
	"""The period containing `on`: a calendar month, or a calendar quarter for variations, in the site's time. Inclusive start, exclusive next start."""
	day = getdate(on)
	months = TYPES[report_type]["months"]
	first = get_first_day(day)
	start = add_months(first, -((first.month - 1) % months))
	return start, add_months(start, months)


def label_of(report_type: str, start: date) -> str:
	if TYPES[report_type]["months"] == 3:
		return f"Q{(start.month - 1) // 3 + 1} {start.year}"
	return start.strftime("%B %Y")


def rows_of(row) -> list[dict[str, Any]]:
	return records.loads(row.rows_json, [])


def sources(row) -> dict[str, Any]:
	return records.loads(row.sources_json)


def submission(row) -> dict[str, Any]:
	return records.loads(row.submission_json)


def latest(report_type: str, start) -> Any:
	name = frappe.db.get_value(REPORT, {"report_type": report_type, "period_start": getdate(start), "contract_case": ["is", "not set"]}, "name", order_by="version_no desc")
	return frappe.get_doc(REPORT, name) if name else None


def for_case(case: str, limit: int = 24) -> list[Any]:
	"""The period reports whose sources include this contract, newest first (a superseded version is kept apart): where the head finds what was generated and what was submitted."""
	found = []
	for name in frappe.get_all(REPORT, filters={"state": ["!=", "Superseded"], "contract_case": ["is", "not set"]}, pluck="name", order_by="period_start desc, version_no desc", limit=limit * 4):
		row = frappe.get_doc(REPORT, name)
		if any(c.get("case") == case for c in sources(row).get("cases", [])):
			found.append(row)
		if len(found) >= limit:
			break
	return found


def covered_cases(period_end) -> list[str]:
	"""The contracts in Contract Management that had taken effect before the period ended, in this site's namespace."""
	found = []
	for name in frappe.get_all(CASE, filters={"lifecycle": ["in", list(CLOSED_LIFECYCLES)], "fixture_namespace": records.namespace()}, pluck="name", order_by="creation asc"):
		effective = frappe.db.get_value("Contract Agreement Version", {"contract_case": name, "state": "Effective", "change": ["is", "not set"]}, "effective_at")
		if effective and getdate(effective) < getdate(period_end):
			found.append(name)
	return found


# -- the rows ------------------------------------------------------------------------------------------------------------------------------
def _commenced(case: str):
	at = frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective", "change": ["is", "not set"]}, "effective_at")
	return getdate(at) if at else None


def _expected_completion(case: str, terms: dict[str, Any], now: dict[str, Any]) -> str:
	"""The operative due date while delivery is open; once everything ordered is accepted, the end of the longest warranty still running from an accepted unit."""
	if now["remaining"] or not now["ordered"]:
		return terms["delivery"]["due"]
	ends = [warranty.warranty_ends(case, unit) for unit, row in now["units"].items() if row["status"] == "Accepted"]
	ends = [e for e in ends if e]
	return str(max(ends)) if ends else terms["delivery"]["due"]


def progress_row(case: str) -> dict[str, Any]:
	doc = frappe.get_doc(CASE, case)
	terms = change.operative_terms(case)
	now = position.position(case)
	rates = {l["line_id"]: flt(l["rate"]) for l in terms["lines"]}
	accepted_value = sum(row["accepted"] * rates[lid] for lid, row in now["lines"].items())
	invoices = frappe.get_all(INVOICE, filters={"contract_case": case, "state": ["!=", "Superseded"]}, pluck="name")
	cash = sum(payment.settled_amount(i) for i in invoices)
	noncash = sum(payment.invoice_position(case, i)["noncash"] for i in invoices if frappe.db.get_value(INVOICE, i, "state") in ("Certified", "Partly paid", "Paid"))
	item = next((l.get("description") or l.get("item") for l in terms["lines"] if l.get("kind") != "service"), "units")
	replacements = sum(1 for u in now["units"].values() if u["replaces"] and u["status"] == "Accepted")
	open_issues = frappe.db.count("Contract Issue", {"contract_case": case, "kind": "Delivery issue", "state": ["!=", "Closed"]})
	return {"case": case, "contract": doc.contract_id, "title": terms.get("title") or doc.title, "supplier": doc.supplier_name, "value": flt(terms["total"]), "commenced": str(_commenced(case) or ""), "status": doc.lifecycle,
		"cash_confirmed": cash, "noncash": noncash, "accepted_value": accepted_value, "unpaid": max(0.0, accepted_value - cash - noncash), "expected_completion": _expected_completion(case, terms, now), "accepted": now["accepted"],
		"ordered": now["ordered"], "item": cstr(item).lower(), "replacements": replacements, "open_issues": open_issues, "currency": terms.get("currency", "KES")}


def variation_rows(case: str, start, end) -> list[dict[str, Any]]:
	original = change.original_terms(case)
	out = []
	for row in change.effective_changes(case):
		if not (getdate(start) <= getdate(row.effective_at) < getdate(end)):
			continue
		amendment = change.amendment_of(row)
		terms = records.loads(amendment.terms_json)
		decision = records.loads(row.decision_json)
		note = records.loads(row.rule_json)
		funding = frappe.db.get_value(intents.INTENT, {"contract_case": case, "operation_kind": "Funding adjustment", "subject": change.amendment_subject(row)}, "state")
		out.append({"case": case, "contract": frappe.db.get_value(CASE, case, "contract_id"), "amendment": row.change_no, "kind": row.kind, "original_amount": flt(original["total"]), "current_amount": flt(terms["total"]),
			"original_quantity": sum(cint(l["quantity"]) for l in original["lines"]), "current_quantity": sum(cint(l["quantity"]) for l in terms["lines"]), "cumulative_percent": note.get("cumulative_value_percent"),
			"grounds": row.reason, "decision": decision.get("outcome"), "decided_by": decision.get("by"), "effective_at": str(row.effective_at), "funding": "Acknowledged" if funding in intents.SETTLED else "Pending" if funding else "Not needed",
			"due": terms["delivery"]["due"]})
	return out


def payment_rows(case: str) -> list[dict[str, Any]]:
	out = []
	for inv in frappe.get_all(INVOICE, filters={"contract_case": case, "state": ["!=", "Superseded"]}, fields=["name", "claim_reference", "state", "claimed_amount", "received_at", "accounting_state"], order_by="invoice_no asc"):
		now = payment.invoice_position(case, inv.name) if inv.state in ("Certified", "Partly paid", "Paid") else None
		out.append({"case": case, "contract": frappe.db.get_value(CASE, case, "contract_id"), "invoice": inv.claim_reference, "received": str(inv.received_at), "claimed": flt(inv.claimed_amount), "state": inv.state,
			"liability_posted": inv.accounting_state == "Posted", "certified": now["certified"] if now else 0.0, "recorded": now["recorded"] if now else 0.0, "cash_confirmed": now["cash_confirmed"] if now else 0.0,
			"noncash": now["noncash"] if now else 0.0, "outstanding": now["outstanding"] if now else 0.0})
	return out


def termination_rows(case: str, start, end) -> list[dict[str, Any]]:
	out = []
	for name in frappe.get_all(termination.TERM, filters={"contract_case": case, "state": ["in", ["Effective", "Settlement prepared", "Settled"]]}, pluck="name"):
		row = frappe.get_doc(termination.TERM, name)
		if not row.effective_at or not (getdate(start) <= getdate(row.effective_at) < getdate(end)):
			continue
		now = records.loads(row.financial_json)
		notice = records.loads(row.notice_json)
		out.append({"case": case, "contract": frappe.db.get_value(CASE, case, "contract_id"), "termination": row.termination_no, "grounds": row.grounds, "notice_delivered": notice.get("delivered_on"), "effective": str(row.effective_at),
			"accepted_value": flt(now.get("accepted_value")), "cash_paid": flt(now.get("cash_paid")), "supported_unpaid": flt(now.get("supported_unpaid")), "advance_balance": flt(now.get("advance_balance")),
			"disputed": flt(now.get("disputed")), "state": row.state})
	return out


def build_rows(report_type: str, case: str, start, end) -> list[dict[str, Any]]:
	if report_type == "Progress":
		return [progress_row(case)]
	if report_type == "Variation":
		return variation_rows(case, start, end)
	if report_type == "Payment follow-up":
		return payment_rows(case)
	return termination_rows(case, start, end)


# -- generate -----------------------------------------------------------------------------------------------------------------------------
def _guards(cases: list[str], command: str) -> Guards:
	guards, seen = Guards(), set()
	for case in cases or []:
		doc = frappe.get_doc(CASE, case)
		if doc.legal_profile in seen:
			continue
		seen.add(doc.legal_profile)
		for reason in preflight.rules(doc, command).reasons:
			guards.add(reason["code"], **reason["detail"])
	return guards


def generate(report_type: str, *, period_start: str, idempotency_key: str, actor: str, system: bool = False) -> dict[str, Any]:
	"""`GenerateContractReport`: derive the report for one completed period from the records, with its cutoff and the version of every record read. A source that cannot be read leaves an Incomplete draft. The
	scheduled run is the system's (`system=True`): it generates the same report and submits nothing."""

	def authorise() -> None:
		authority.require(actor, "Head of Procurement Function")

	def body() -> dict[str, Any]:
		invalid({"report_type": "" if report_type in TYPES else "Choose the report."})
		start, end = period_of(report_type, period_start)
		invalid({"period_start": "" if getdate(period_start) == start else f"A {TYPES[report_type]['title'].lower()} period starts on {start}."})
		if getdate(clock.now()) < end:
			invalid({"period_start": f"The period ends on {end}; the report is generated when it has ended."})
		cases = covered_cases(end)
		_guards(cases, "GenerateContractReport").raise_if_any()
		rows, trail, failed = [], [], []
		for case in cases:
			try:
				rows.extend(build_rows(report_type, case, start, end))
				trail.append({"case": case, "version": cint(frappe.db.get_value(CASE, case, "record_version")), "read": True})
			except Exception as exc:  # noqa: BLE001 - the report keeps what it could not read, never a guess
				frappe.log_error(title=f"Contract report {report_type} could not read {case}")
				trail.append({"case": case, "version": cint(frappe.db.get_value(CASE, case, "record_version")), "read": False})
				failed.append({"case": case, "reason": f"{type(exc).__name__}: {str(exc)[:200]}", "owner": "Technical operator"})
		earlier = latest(report_type, start)
		number = records.next_number(REPORT, {"report_type": report_type, "period_start": start}, "version_no")
		if earlier is not None and earlier.state in ("Draft", "Incomplete"):
			records.update(earlier, state="Superseded", record_version=cint(earlier.record_version) + 1)
		row = records.new(REPORT, report_type=report_type, period_start=start, period_end=end, version_no=number, state="Incomplete" if failed else "Draft", cutoff=clock.now(),
			sources_json=records.dumps({"cases": trail, "failed": failed, "label": label_of(report_type, start), "covered": len(cases), "supersedes": earlier.name if earlier else ""}), rows_json=records.dumps(rows),
			recipient=TYPES[report_type]["recipient"], prepared_by=actor, prepared_at=clock.now(), submission_json=records.dumps({}), record_version=1)
		anchor = cases[0] if cases else ""
		if anchor and rows and not failed:
			work.assign(anchor, "SubmitContractReport", f"Review and submit the {label_of(report_type, start)} report.", f"report {row.name}", 1, work.holders(work.HOP), role=work.HOP)
		if failed:
			for item in failed:
				work.incident(item["case"], "RestoreContractOperation", "Restore the report source", f"report {row.name}", 1)
		events.record(anchor, "Report generated", actor, f"The {label_of(report_type, start)} {report_type.lower()} report was generated ({len(rows)} row(s)).", report=row.name, incomplete=bool(failed)) if anchor else None
		return {"ok": True, "report": row.name, "state": row.state, "rows": len(rows), "version": number, "empty": not rows and not failed}

	return records.command("GenerateContractReport", case="", idempotency_key=idempotency_key, actor=actor, payload={"type": report_type, "start": str(period_start)}, body=body, authorise=None if system else authorise)


def generate_scheduled(actor: str = "Administrator") -> list[str]:
	"""The scheduled run: one report for each type whose latest completed period has none yet. A report already made for the period is never made twice."""
	made = []
	today = getdate(clock.now())
	for report_type in TYPES:
		start, _end = period_of(report_type, add_months(period_of(report_type, today)[0], -TYPES[report_type]["months"]))
		if latest(report_type, start) is not None or not covered_cases(period_of(report_type, start)[1]):
			continue
		made.append(generate(report_type, period_start=str(start), idempotency_key=f"scheduled-{report_type}-{start}", actor=actor, system=True)["report"])
	return made


# -- submit -------------------------------------------------------------------------------------------------------------------------------
def _anchor(row) -> str:
	trail = sources(row)["cases"]
	return trail[0]["case"] if trail else ""


def submit(report: str, *, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SubmitContractReport`: the head of procurement submits the reviewed report to its recipient. The rows are immutable from now on; the dispatch and its delivery are tracked apart."""
	row = get(report)
	anchor = _anchor(row)

	def authorise() -> None:
		authority.require(actor, "Head of Procurement Function")

	def body() -> dict[str, Any]:
		current = records.lock(anchor) if anchor else None
		now = get(report)
		if now.state == "Incomplete":
			fail("CM_REPORT", report=report, failed=sources(now)["failed"], reason="A source could not be read, so the report is not submitted.")
		if now.state != "Draft":
			fail("CM_CHANGED", report=report, state=now.state)
		cases = [t["case"] for t in sources(now)["cases"]]
		_guards(cases, "SubmitContractReport").raise_if_any()
		records.update(now, state="Submitted", submitted_by=actor, submitted_at=clock.now(), submission_json=records.dumps({"kind": "Internal", "recipient": now.recipient, "delivery": "Pending delivery"}), record_version=cint(now.record_version) + 1)
		if anchor:
			intents.record(anchor, f"report {now.name}", 1, "Report dispatch", "send", recovery_owner="Technical operator")
			work.finish(anchor, command="SubmitContractReport", subject=f"report {now.name}", actor=actor)
		for item in rows_of(now):
			if now.report_type == "Variation":
				obligations.satisfy(item["case"], "Variation report", f"amendment {item['amendment']}", f"Reported in the {label_of(now.report_type, getdate(now.period_start))} variation report")
		if anchor:
			events.record(anchor, "Report submitted", actor, f"The {label_of(now.report_type, getdate(now.period_start))} {now.report_type.lower()} report was submitted to the {now.recipient}.", report=now.name)
		return {"ok": True, "report": now.name, "state": "Submitted", "contract": anchor, "lifecycle": current.lifecycle if current else "", "record_version": cint(current.record_version) if current else 0}

	out = records.command("SubmitContractReport", case=anchor, idempotency_key=idempotency_key, actor=actor, payload={"report": report}, body=body, authorise=authorise)
	frappe.db.commit()
	if anchor:
		dispatch_report(anchor, report, actor)
	return out


def dispatch_report(anchor: str, report: str, actor: str) -> dict[str, Any]:
	"""Deliver a submitted report to its recipient through the dispatch operation; delivery is recorded with its evidence, and a failure leaves it pending delivery, to be retried."""
	row = get(report)
	if submission(row).get("kind") != "Internal":
		return {"ok": True, "delivered": False}
	name = frappe.db.get_value(intents.INTENT, {"operation_identity": intents.identity(anchor, f"report {report}", 1, "Report dispatch", "send")}, "name")
	if not name:
		return {"ok": True, "delivered": False}
	recipients = sorted(set(work.holders("Accounting Officer")) | (set(work.holders(work.HOP)) if "Finance" in row.recipient else set()))

	def executor(identity: str):
		try:
			return dispatch.deliver(identity, case=anchor, recipients=recipients, subject=TYPES[row.report_type]["title"], text=f"The {label_of(row.report_type, getdate(row.period_start))} report has been submitted."), "Report delivery"
		except dispatch.Failed as exc:
			raise intents.OwnerRefused(str(exc)) from exc

	result = intents.execute(name, executor, lambda identity: dispatch.find(identity), native_doctype="Report delivery")
	with records.atomic():
		found = get(report)
		detail = submission(found)
		if result["state"] in intents.SETTLED:
			detail.update(delivery="Delivered", delivery_evidence=result["reference"], delivered_at=str(clock.now()))
			work.finish(anchor, command="RestoreContractOperation", subject=f"report {report}", actor=actor)
		else:
			detail["delivery"] = "Pending delivery"
			work.incident(anchor, "RestoreContractOperation", "Restore the report delivery", f"report {report}", 1)
		records.update(found, submission_json=records.dumps(detail))  # the rows are untouched; only how delivery stands
	frappe.db.commit()
	return {"ok": True, "delivered": result["state"] in intents.SETTLED}


def retry_dispatches(case: str, actor: str = "") -> int:
	"""Technical recovery: deliver again every submitted report of this contract that is still pending delivery. The same operation: nothing is delivered twice."""
	count = 0
	for name in frappe.get_all(REPORT, filters={"state": "Submitted"}, pluck="name"):
		row = get(name)
		if submission(row).get("kind") == "Internal" and submission(row).get("delivery") != "Delivered" and _anchor(row) == case:
			dispatch_report(case, name, actor)
			count += 1
	return count


def record_submission(report: str, *, destination: str, reference: str, submitted_on: str, copy: str, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordContractReportSubmission`: the actual external submission, with its destination, reference, date and copy. The record is of what happened; it is not an approval and creates no recipient the sources do not name."""
	row = get(report)
	anchor = _anchor(row)

	def authorise() -> None:
		authority.require(actor, "Head of Procurement Function")

	def body() -> dict[str, Any]:
		now = get(report)
		if now.state == "Incomplete":
			fail("CM_REPORT", report=report, failed=sources(now)["failed"], reason="A source could not be read, so the report is not submitted.")
		if now.state not in ("Draft", "Submitted"):
			fail("CM_CHANGED", report=report, state=now.state)
		day = records.day(submitted_on)
		invalid({"destination": "" if cstr(destination).strip() else "Enter where it was submitted.", "reference": "" if cstr(reference).strip() else "Enter the submission reference.", "submitted_on": "" if day else "Enter the submission date.",
			"copy": "" if cstr(copy).strip() else "Attach the copy that was submitted."})
		cases = [t["case"] for t in sources(now)["cases"]]
		_guards(cases, "RecordContractReportSubmission").raise_if_any()
		detail = submission(now)
		external = detail.get("external", [])
		external.append({"destination": cstr(destination).strip(), "reference": cstr(reference).strip(), "on": str(day), "copy": cstr(copy).strip(), "by": actor, "at": str(clock.now())})
		fields = {"submission_json": records.dumps({**detail, "external": external}), "record_version": cint(now.record_version) + 1}
		if now.state == "Draft":
			fields.update(state="Submitted", submitted_by=actor, submitted_at=clock.now())
			if anchor:
				work.finish(anchor, command="SubmitContractReport", subject=f"report {now.name}", actor=actor)
		records.update(now, **fields)
		if now.report_type == "Variation":
			for item in rows_of(now):
				obligations.satisfy(item["case"], "Variation report", f"amendment {item['amendment']}", f"Submitted to {cstr(destination).strip()} ({cstr(reference).strip()})")
		if anchor:
			events.record(anchor, "Report submission recorded", actor, f"The report was submitted to {cstr(destination).strip()} on {day.strftime('%-d %B %Y')} ({cstr(reference).strip()}).", report=now.name)
		return {"ok": True, "report": now.name, "state": "Submitted", "contract": anchor}

	return records.command("RecordContractReportSubmission", case=anchor, idempotency_key=idempotency_key, actor=actor, payload={"report": report, "destination": destination, "reference": reference, "on": submitted_on, "copy": copy},
		body=body, authorise=authorise)
