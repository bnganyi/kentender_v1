# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reporting screens (boards D15, D15-L; CM-CHG-001 v0.8 sections 5.15, 10.3).

The report is read from its record, never composed on the screen: its period, its cutoff, the rows it was generated with, who submits it and to whom. A report that could not read a source says so and offers no
submission. The publication duty is shown with its trigger kept to the minute, the separate fact of the signing, and a deadline that is not confirmed, never a countdown."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import formatdate, getdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import obligations, records, reporting


def _long(value: Any) -> str:
	return formatdate(value, "d MMMM yyyy") if value else "—"


def _summary(row: dict[str, Any]) -> str:
	cur = row["currency"]
	replaced = f"; {row['replacements']} {'was a replacement unit' if row['replacements'] == 1 else 'were replacement units'}" if row["replacements"] else ""
	noncash = f"noncash adjustment {money(row['noncash'], cur)}" if row["noncash"] else "no noncash adjustment"
	issues = "No open delivery issue." if not row["open_issues"] else f"{row['open_issues']} open delivery issue{'s' if row['open_issues'] != 1 else ''}."
	return f"{row['accepted']} {row['item']}{'' if row['accepted'] == 1 else 's'} accepted{replaced}. Unpaid {money(row['unpaid'], cur)}; {noncash}. {issues}"


def progress(ctx: Context, report) -> dict[str, Any]:
	"""D15: the monthly progress report, reviewed and submitted by the head of procurement."""
	rows = reporting.rows_of(report)
	trail = reporting.sources(report)
	label = trail["label"]
	submitted = report.state == "Submitted"
	detail = reporting.submission(report)
	table = kit.t(["Contract", "Title", "Contract value", "Commenced", "Status", "Cash confirmed", "Expected completion"],
		[[r["contract"], r["title"], money(r["value"], r["currency"]), _long(r["commenced"]), r["status"], money(r["cash_confirmed"], r["currency"]), _long(r["expected_completion"])] for r in rows], [2, 5])
	text = [kit.x(_summary(r)) for r in rows] if rows else [kit.x("No records in this period.")]
	if trail["failed"]:
		text = [kit.xs("This report is incomplete because a source could not be read."), *[kit.xh(f"{f['case']}: {f['reason']} (recovery owner: {f['owner']})") for f in trail["failed"]]]
	submission = kit.R("Submission", kit.r(["Author", f"{ctx.name(report.prepared_by)}, HOP"], ["Recipient", f"{ctx.name(next(iter(__import__('kentender_contracts.services.work', fromlist=['holders']).holders('Accounting Officer')), ''))}, {report.recipient}"],
		["AO receipt", (detail.get("delivery") or "Recorded after submission") if submitted else "Recorded after submission"]))
	next_ = chrome.next_block(ctx) if not submitted else kit.done(f"The {label} report was submitted on {when(report.submitted_at)}.")
	b = chrome.base(ctx, "D15", d="D15", name="Contract reporting", title=reporting.TYPES[report.report_type]["title"], tab="Obligations", next=next_, subj=f"{label} {report.report_type.lower()} report draft {report.version_no}",
		regions=[kit.R("Coverage", kit.r(["Report month" if report.report_type != "Variation" else "Report quarter", label], ["Contracts covered", f"{trail['covered']} in Contract Management"],
			["Contracts outside Contract Management", "Not included — reconcile before claiming full coverage"])), kit.R("Report", table, *text), submission],
		p="" if submitted or trail["failed"] else "Submit report", s2=["View contract"], ev=["Agreement 1", "Finance reconciliation"])
	b["actions"]["Submit report"] = kit.command("SubmitContractReport", report=report.name)
	b["actions"]["View contract"] = kit.tab("Agreement")
	if not submitted and not trail["failed"]:
		b["s2"].append("Record external submission")
		b["actions"]["Record external submission"] = kit.dialog("external")
		b["dialogs"]["external"] = kit.dlg("Record external submission", [kit.fl(kit.tx("Destination", "", "destination"), kit.tx("Reference", "", "reference"), kit.dt("Submitted on", "", "submitted_on"), kit.file("Copy submitted", "", "copy"))],
			"Save submission", command="RecordContractReportSubmission", args={"report": report.name})
	return b


def publication(ctx: Context, row) -> dict[str, Any]:
	"""D15-L: the publication requirement needs review. The trigger and the separate fact are shown as they happened; the deadline is not confirmed and no countdown is invented."""
	found = obligations.detail(row)
	events = found["events"]
	award = next((e for e in events if e["event"] == "Award decision recorded"), events[0])
	signed = next((e for e in events if e["event"] == "Contract signed"), None)
	b = chrome.base(ctx, "D15-L", d="D15", name="Contract reporting", title="Publication requirement needs review", tab="Obligations", subj="Publication obligation",
		next=kit.blk("The applicable publication deadline needs confirmation.", ctx.name(ctx.user), ["Record source evidence", "View source event", "View signing record"]),
		regions=[kit.R("Obligation", kit.r(["Trigger", f"Award decision recorded {when(award['at'])}"], ["Separate fact", f"Contract signed {when(signed['at'])}" if signed else "Contract not yet signed"],
			["Destinations", found.get("destinations", "")], ["Deadline", "Not confirmed — set by current directions"], ["Responsible review", "Procurement/reporting owner"]))], ev=["Award decision event", "Signing record"])
	b["st"] = "Needs review"
	b["actions"]["Record source evidence"] = kit.dialog("evidence")
	b["actions"]["View source event"] = b["actions"]["View signing record"] = kit.tab("History")
	b["dialogs"]["evidence"] = kit.dlg("Record source evidence", [kit.fl(kit.tx("Source reference", "", "reference"), kit.dt("Dated", "", "dated"), kit.file("Copy", "", "copy"), kit.ta("Notes", "", "notes"))],
		"Save evidence", command="RecordLegalSourceEvidence", args={"obligation": row.name})
	return b
