# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Issue and warranty screens (boards D13, D13-S, D13-C, D16-W, D16-P, D35, D35-V, D35-C, D35-H; CM-CHG-001 v0.8 sections 5.7, 5.18, 5.20, 10.3, 10.8).

An issue is read from its record: the facts, the thread, the remedy asked for and who holds the next move. A warranty claim is the same record with its own stages (`services/warranty.py`), drawn as the warranty boards;
a closed one is shown by its resolution. The supplier sees their own side only: the matter, what was sent to them and their reply, never an internal Finance task."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, formatdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import issues, people, records, warranty


def _day(value: Any) -> str:
	return formatdate(value, "d MMM yyyy") if value else "—"


def _long(value: Any) -> str:
	return formatdate(value, "d MMMM yyyy") if value else "—"


def _units(units: list[str]) -> str:
	return units[0] if len(units) == 1 else ", ".join(units[:-1]) + " and " + units[-1] if units else "—"


def _issue_region(ctx: Context, row) -> dict[str, Any]:
	facts = records.loads(row.facts_json)
	if row.kind == "Delivery issue":
		rows = [["Units", _units(sorted(facts.get("units", [])))], ["Result", facts.get("result", "")], ["Observed", facts.get("observed", "")]]
	elif row.kind == "Warranty claim":
		rows = [["Unit", facts["unit"]], ["Fault", facts["fault"]], ["Notice", _day(facts["notice_date"])], ["Warranty ends", _day(facts["warranty_ends"])]]
	else:
		rows = [["Matter", facts.get("description", "")], ["Reported by", ctx.name(facts.get("reported_by", ""))]]
	rows += [["Requested remedy", row.requested_remedy or "—"], ["Requested reply date", _long(row.reply_by)]]
	return kit.R("Issue", kit.r(*rows))


def _thread(ctx: Context, row, direction: str) -> Any:
	sent = [m for m in issues.thread(row) if m["direction"] == direction]
	return sent[-1] if sent else None


def _evidence(row) -> list[str]:
	links = records.loads(row.links_json)
	out = []
	if links.get("acceptance"):
		out.append("Acceptance report " + str(frappe.db.get_value("Contract Acceptance", links["acceptance"], "version_no") or 1))
	if row.kind == "Delivery issue":
		out.append("Inspection " + str(((records.loads(row.facts_json).get("inspection") or "arrival 1").split()[-1])))
	return out


def _problem_dialog(b: dict[str, Any]) -> None:
	b["actions"]["Report a new issue"] = kit.dialog("new")
	b["dialogs"]["new"] = kit.dlg("Report an issue", [kit.fl(kit.tx("Title", "", "title"), kit.ta("Description", "", "description"))], "Report", command="RecordContractIssue", args={})


def send(ctx: Context, row) -> dict[str, Any]:
	"""D13: the contract's owner sends the findings (or any message) to the supplier. The draft is the system's own sentence from the inspection, which the owner may edit."""
	holder = ctx.name(row.owner_user)
	draft = records.loads(row.links_json).get("draft", "")
	last = (issues.thread(row) or [{}])[-1] if row.state == "Awaiting reply" else {}
	title = row.title
	region = kit.R("Message to supplier", kit.fl(kit.ta("Message", "" if last else draft, "message")))
	b = chrome.base(ctx, "D13", d="D13", name="Delivery issue", title=title, tab="Obligations", next=chrome.next_block(ctx), subj=f"Issue {row.issue_no} version {row.record_version}", regions=[_issue_region(ctx, row), region],
		p="Send message", s2=["View acceptance report"] if row.kind == "Delivery issue" else [], ev=_evidence(row))
	b["actions"]["Send message"] = kit.command("SendContractCorrespondence", issue=row.name)
	b["actions"]["View acceptance report"] = kit.tab("Deliveries")
	return b


def reply(ctx: Context, row) -> dict[str, Any]:
	"""D13-S: the supplier's representative answers on the issue and may propose a remedy; they never close it."""
	message = _thread(ctx, row, "to supplier")
	entity = (ctx.terms.get("parties") or {}).get("entity", {}).get("name", "the procuring entity")
	regions = [_issue_region(ctx, row), kit.R(f"Message from {entity}", kit.x(message["text"] if message else "")), kit.R("Your reply", kit.fl(kit.ta("Reply", "", "message"), kit.tx("Remedy you propose", "", "remedy")))]
	b = chrome.base(ctx, "D13-S", d="D13", name="Delivery issue", title=row.title, tab="Obligations", back="Back to my contracts", next=chrome.next_block(ctx), subj=f"Issue {row.issue_no} version {row.record_version}", regions=regions,
		p="Send reply", s2=["View acceptance report"] if row.kind == "Delivery issue" else [], ev=[])
	b["actions"]["Send reply"] = kit.command("ReplyContractCorrespondence", issue=row.name)
	b["actions"]["View acceptance report"] = kit.tab("Deliveries")
	return b


def resolve(ctx: Context, row) -> dict[str, Any]:
	"""The owner's review of the supplier's reply and proposed remedy, and the reasoned disposition that closes the thread (authored: the artboards show the send, the reply and the closed issue)."""
	rows = [[when(m["at"]), "Ministry" if m["direction"] == "to supplier" else "Supplier", m["text"] + (f" Remedy proposed: {m['proposed_remedy']}" if m.get("proposed_remedy") else "")] for m in issues.thread(row)]
	b = chrome.base(ctx, "D13-R", d="D13", name="Delivery issue", title=row.title, tab="Obligations", next=chrome.next_block(ctx), subj=f"Issue {row.issue_no} version {row.record_version}",
		regions=[_issue_region(ctx, row), kit.R("Messages", kit.t(["When", "From", "Message"], rows) if rows else kit.xh("Nothing has been sent yet."))], p="Resolve issue" if row.kind != "Warranty claim" else "", s2=[], ev=[])
	if row.kind != "Warranty claim":
		b["actions"]["Resolve issue"] = kit.dialog("resolve")
		b["dialogs"]["resolve"] = kit.dlg("Resolve issue", [kit.fl(kit.ta("Disposition", "", "disposition"))], "Resolve", command="ResolveContractIssue", args={"issue": row.name})
	return b


def closed(ctx: Context, row) -> dict[str, Any]:
	"""D13-C: the issue is closed with its resolution; a later matter starts a linked issue."""
	b = chrome.base(ctx, "D13-C", d="D13", name="Delivery issue", title=row.title, tab="Obligations", next=kit.done("This issue is closed."), subj=f"Issue {row.issue_no} version {row.record_version}",
		regions=[_issue_region(ctx, row), kit.R("Resolution", kit.x(row.resolution or ""))], p="", s2=["Report a new issue", "View replacement acceptance"] if row.kind == "Delivery issue" else ["Report a new issue"], ev=[])
	_problem_dialog(b)
	b["actions"]["View replacement acceptance"] = kit.tab("Deliveries")
	return b


# -- warranty -------------------------------------------------------------------------------------------------------------------------------
def _claim_region(ctx: Context, row, *, ended: bool = False) -> dict[str, Any]:
	found = warranty.facts(row)
	accepted = warranty.accepted_on(ctx.case, found["unit"])
	warranty_line = f"Expired {_long(found['warranty_ends'])}; timely claim remains open" if ended else f"Ends {_long(found['warranty_ends'])}"
	months = (ctx.terms.get("warranty") or {}).get("months")
	return kit.R("Claim", kit.r(["Unit", found["unit"]], ["Accepted", _day(accepted)], ["Source terms", f"Agreement warranty, {months} months from each unit's acceptance"], ["Fault", found["fault"]], ["Warranty", warranty_line],
		["Evidence", found.get("evidence") or "—"]))


def _expired(row) -> bool:
	from kentender_contracts.services import clock

	return clock.now().date() > frappe.utils.getdate(warranty.facts(row)["warranty_ends"])


def notice(ctx: Context, row) -> dict[str, Any]:
	"""D16-W: send the defect notice to the supplier; D16-P once it has been sent and the remedy is pending."""
	if issues.thread(row):
		sent = (issues.thread(row) or [{}])[0]
		b = chrome.base(ctx, "D16-P", d="D16", name="Security follow-up", title="Warranty claim", tab="Obligations", next=chrome.next_block(ctx), subj=f"Agreement 1 · warranty claim {row.issue_no}",
			regions=[_claim_region(ctx, row, ended=_expired(row)), kit.R("Notice", kit.r(["Defect notice", f"Sent {_day(sent['at'])}"]))], s2=["View notice", "View claim history"], ev=["Defect notice 1"])
		b["actions"]["View notice"] = b["actions"]["View claim history"] = kit.tab("History")
		return b
	b = chrome.base(ctx, "D16-W", d="D16", name="Security follow-up", title="Warranty claim", tab="Obligations", next=chrome.next_block(ctx), subj=f"Agreement 1 · warranty claim {row.issue_no}",
		regions=[_claim_region(ctx, row), kit.R("Defect notice", kit.fl(kit.ta("Notice", warranty.facts(row)["fault"], "message")))], p="Send notice", s2=["View warranty"], ev=[])
	b["actions"]["Send notice"] = kit.command("SendContractCorrespondence", issue=row.name)
	b["actions"]["View warranty"] = kit.tab("Agreement")
	return b


def _progress_region(ctx: Context, row) -> dict[str, Any]:
	found, body = warranty.facts(row), records.loads(row.links_json)
	stage = warranty.stage(row)
	finance = ctx.name(next(iter(__import__("kentender_contracts.services.work", fromlist=["holders"]).holders("Finance preparation")), ""))
	reconciled = "reconciliation" in body
	return kit.R("Progress", kit.f(["Returned", "Yes" if "returned" in body else "No"], ["Replacement", "Accepted" if body.get("replacement") else "Not received"],
		["Finance correction", "Reconciled" if reconciled else f"Pending — {finance}"]))


def _claim35(ctx: Context, row) -> dict[str, Any]:
	found = warranty.facts(row)
	return kit.R("Claim", kit.r(["Unit", found["unit"]], ["Warranty ends", _day(found["warranty_ends"])], ["Fault", found["fault"]], ["Notice sent", when(found["notice_date"])], ["Remedy", f"{row.requested_remedy} under issued terms"]))


def arrange(ctx: Context, row) -> dict[str, Any]:
	"""D35: the owner arranges the return of the faulty unit and records the actual collection."""
	found = warranty.facts(row)
	b = chrome.base(ctx, "D35", d="D35", name="Paid-unit warranty replacement", title="Follow up warranty replacement", tab="Obligations", next=chrome.next_block(ctx), subj="All units accepted, invoiced and paid",
		regions=[_claim35(ctx, row), _progress_region(ctx, row)], p="Record return", s2=[], ev=["Defect notice 1"])
	b["actions"]["Record return"] = kit.dialog("return")
	b["dialogs"]["return"] = kit.dlg("Record return", [kit.fl(kit.ro("Unit", found["unit"]), kit.dt("Actual collection date", "", "collected_on"), kit.file("Evidence", "", "evidence"))], "Record return",
		command="RecordWarrantyReturn", args={"issue": row.name})
	return b


def _findings(ctx: Context, row) -> dict[str, Any]:
	"""The measured findings of the replacement unit, from its inspection."""
	from kentender_contracts.boards import delivery as boards
	from kentender_contracts.services import delivery

	found = warranty.facts(row)
	replacement = warranty.replacement_of(ctx.case, found["unit"])
	rows: list[list[str]] = []
	if replacement:
		unit = ctx.position["units"][replacement]
		inspection = delivery.current_inspection(ctx.case, unit["arrival"])
		if inspection is not None:
			measured = records.loads(inspection.findings_json)
			only = {"units": {replacement: measured["units"][replacement]}} if replacement in measured.get("units", {}) else None
			rows = [[r[0], r[2], r[3]] for r in boards._findings_rows(ctx, only, delivery.criteria_for(ctx.terms, unit["line_id"]))]
	return kit.R("Findings", kit.t(["Check", "Observed", "Result"], rows or [["Replacement unit", replacement or "Not received", "!Needs review"]]),
		kit.r(["Evidence", f"Inspection of {replacement}" if replacement else "—"], ["Verification source", "Current technical certificate and fully signed replacement report"]))


def verify(ctx: Context, row) -> dict[str, Any]:
	"""D35-V: the technical capacity confirms the remedy evidence; D35-H when Finance's reconciliation (or the replacement's receipt) is incomplete."""
	found, body = warranty.facts(row), records.loads(row.links_json)
	missing = warranty.missing_evidence(ctx.case, row)
	replacement = warranty.replacement_of(ctx.case, found["unit"])
	state = "Reconciled" if not missing else "Incomplete"
	remedy = kit.R("Remedy", kit.r(["Returned unit", found["unit"]], ["Replacement", replacement or "—"], ["Return/credit and replacement receipt", state], ["Acquisition entitlement", "Unchanged"], ["Additional cash or payable", f"{ctx.currency} 0"]))
	if missing:
		b = chrome.base(ctx, "D35-H", d="D35", name="Paid-unit warranty replacement", title="Verify warranty remedy", tab="Obligations", next=kit.blk(missing[0]["what"] if "Finance" not in missing[0]["what"] else "Finance must reconcile the replacement.", ctx.name(missing[0]["holder"]),
			["View affected records", "View claim"]), regions=[remedy, _findings(ctx, row)], p="", s2=[], ev=[])
		b["actions"]["View affected records"] = b["actions"]["View claim"] = kit.tab("History")
		return b
	b = chrome.base(ctx, "D35-V", d="D35", name="Paid-unit warranty replacement", title="Verify warranty remedy", tab="Obligations", next=chrome.next_block(ctx), regions=[remedy, _findings(ctx, row)], p="Verify remedy",
		s2=["Request correction"], ev=["Replacement report"])
	b["actions"]["Verify remedy"] = kit.command("VerifyContractRemedy", issue=row.name)
	b["actions"]["Request correction"] = kit.dialog("correction")
	b["dialogs"]["correction"] = kit.dlg("Request correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Request", command="RecordContractIssue", args={})
	return b


def done(ctx: Context, row) -> dict[str, Any]:
	"""D35-C: the remedy was verified and the claim is closed: the original cash stands, there is no additional invoice entitlement."""
	found, body = warranty.facts(row), records.loads(row.links_json)
	cash = sum(__import__("kentender_contracts.services.payment", fromlist=["settled_amount"]).settled_amount(n) for n in frappe.get_all("Contract Invoice", filters={"contract_case": ctx.case}, pluck="name"))
	b = chrome.base(ctx, "D35-C", d="D35", name="Paid-unit warranty replacement", title="Follow up warranty replacement", tab="Obligations", next=kit.done(f"The remedy was verified and the claim closed on {_long(row.closed_at)}."),
		regions=[kit.R("Outcome", kit.r(["Original cash", money(cash, ctx.currency)], ["Additional invoice entitlement", "None"], ["Original unit", found["unit"]], ["Replacement", body.get("replacement") or "—"]))], p="", s2=["View remedy", "View history"], ev=[])
	b["actions"]["View remedy"] = b["actions"]["View history"] = kit.tab("History")
	return b


def reconcile(ctx: Context, row) -> dict[str, Any]:
	"""Finance names the native return and credit of the collected unit (authored: the artboards show the blocked wait and the verification)."""
	found = warranty.facts(row)
	fields = [kit.pick("Native return of the receipt", "", "contracts.native_record", "return_document", {"kind": "purchase_receipt"}, "", "return"), kit.pick("Native credit against the invoice", "", "contracts.native_record", "credit_document",
		{"kind": "purchase_invoice"}, "", "credit"), kit.ta("Note", "", "note")]
	b = chrome.base(ctx, "D35-F", d="D35", name="Paid-unit warranty replacement", title="Reconcile the returned unit", tab="Obligations", next=chrome.next_block(ctx), regions=[_claim35(ctx, row), kit.R("Return", kit.r(["Unit", found["unit"]],
		["Collected", _day(records.loads(row.links_json).get("returned", {}).get("on"))]), kit.fl(*fields))], p="Reconcile return", s2=[], ev=[])
	b["actions"]["Reconcile return"] = kit.command("ReconcileWarrantyReturn", issue=row.name)
	return b


def new_claim(ctx: Context) -> dict[str, Any]:
	"""Record a warranty claim for an accepted unit (authored: the artboards show the claim once recorded)."""
	fields = [kit.tx("Unit", "", "unit"), kit.ta("Fault", "", "fault"), kit.dt("Notice given on", "", "notice_date"),
		kit.sel("Remedy asked for", warranty.REMEDIES[0], list(warranty.REMEDIES), "remedy"), kit.file("Evidence", "", "evidence")]
	b = chrome.base(ctx, "D16-N", d="D16", name="Warranty claim", title="Record a warranty claim", tab="Obligations", next=chrome.form_turn(ctx, "RecordWarrantyClaim", "Describe the fault."), regions=[kit.R("Claim", kit.fl(*fields))],
		p="Record claim", s2=["Cancel"], ev=[])
	b["actions"]["Record claim"] = kit.command("RecordWarrantyClaim")
	b["actions"]["Cancel"] = kit.tab("Obligations")
	return b


def warranty_view(ctx: Context, row) -> dict[str, Any]:
	"""A warranty claim opened from the Obligations tab: the screen for the stage it is at, or the closed claim."""
	if row.state == "Closed":
		return done(ctx, row)
	stage = warranty.stage(row)
	if stage == "notice":
		return notice(ctx, row)
	if stage == "return":
		return arrange(ctx, row)
	if stage == "reconcile" and people.holds(ctx.user, "Finance preparation"):
		return reconcile(ctx, row)
	return verify(ctx, row)
