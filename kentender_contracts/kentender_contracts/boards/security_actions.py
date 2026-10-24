# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Security action screens (boards D16, D37, D37-A, D37-P, D37-X; CM-CHG-001 v0.8 sections 5.20, 10.3, 10.8).

The claim, its decision, the communication delivered and the issuer's outcome are four screens of one claim and four facts; a replacement is verified before it takes over, and a return follows the evidenced final
acceptance. Nothing here says the issuer paid on a request or a decision, and nothing is released because an instrument expired."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import formatdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import records, security_actions

SECURITY = "Contract Security"


def _day(value: Any) -> str:
	return formatdate(value, "d MMM yyyy") if value else "—"


def _long(value: Any) -> str:
	return formatdate(value, "d MMMM yyyy") if value else "—"


def _instrument(ctx: Context, row) -> dict[str, Any]:
	basis = (ctx.terms.get("security") or {}).get("statement") or "As issued"
	return kit.R("Instrument", kit.r(["Instrument", f"{row.reference} (verified)"], ["Amount", money(row.amount, ctx.currency)], ["Expiry", _day(row.expires_on)], ["Custodian", ctx.name(row.verified_by or row.recorded_by)], ["Claim basis", basis]))


def _claim_rows(ctx: Context, claim) -> dict[str, Any]:
	return kit.R("Proposed claim", kit.r(["Amount", money(claim.amount, ctx.currency)], ["Grounds", claim.grounds], ["Recipient", claim.recipient], ["Claimant authority", claim.mandate]))


def _evidence(claim) -> list[str]:
	return [e["label"] for e in records.loads(claim.evidence_json, [])]


def prepare(ctx: Context, *, correcting=None) -> dict[str, Any]:
	"""D37: the custodian prepares the supported claim; the figures are entered in the dialog that requests it (the amount never exceeds the instrument)."""
	instrument = security_actions.operative(ctx.case)
	basis = (ctx.terms.get("security") or {}).get("statement") or "As issued"
	rows = kit.R("Proposed claim", kit.r(["Amount", "Entered when you request the claim"], ["Grounds", correcting.grounds if correcting else "Entered when you request the claim"], ["Recipient", instrument.issuer], ["Claimant authority", "Entered when you request the claim"]))
	b = chrome.base(ctx, "D37", d="D37", name="Security claim", title="Review security claim", tab="Obligations", next=chrome.form_turn(ctx, "RequestSecurityClaim", "Prepare the supported claim."),
		subj="Security " + instrument.reference, regions=[_instrument(ctx, instrument), rows], p="Request claim", s2=["View instrument", "Cancel"], ev=[f"Instrument {instrument.reference}", "Claim basis"])
	b["actions"]["Request claim"] = kit.dialog("request")
	b["actions"]["View instrument"] = kit.tab("Agreement")
	b["actions"]["Cancel"] = kit.tab("Obligations")
	b["dialogs"]["request"] = kit.dlg("Request claim", [kit.fl(kit.tx("Amount", "", "amount"), kit.ta("Grounds", correcting.grounds if correcting else "", "grounds"), kit.tx("Recipient", instrument.issuer, "recipient"),
		kit.tx("Claimant authority", correcting.mandate if correcting else "", "mandate"), kit.file("Evidence", "", "evidence"))], "Request", command="RequestSecurityClaim", args={"correcting": correcting.claim_no} if correcting else {})
	return b


def decide(ctx: Context, claim) -> dict[str, Any]:
	"""D37-A: the Accounting Officer's decision on the exact claim. The decision gives no cash status and the amount stays the request's."""
	instrument = frappe.get_doc(SECURITY, claim.security)
	b = chrome.base(ctx, "D37-A", d="D37", name="Security claim", title="Review security claim", tab="Obligations", next=chrome.next_block(ctx), subj="Security " + instrument.reference,
		regions=[_instrument(ctx, instrument), _claim_rows(ctx, claim)], p="Approve claim", s2=["Decline", "Return for correction"], ev=_evidence(claim))
	args = {"claim": claim.claim_no}
	b["actions"]["Approve claim"] = kit.dialog("approve")
	b["actions"]["Decline"] = kit.dialog("decline")
	b["actions"]["Return for correction"] = kit.dialog("return")
	for key, title, decision in (("approve", "Approve claim", "Approve"), ("decline", "Decline claim", "Decline"), ("return", "Return for correction", "Return")):
		b["dialogs"][key] = kit.dlg(title, [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm decision", command="DecideSecurityClaim", args={**args, "decision": decision})
	return b


def communicate(ctx: Context, claim) -> dict[str, Any]:
	"""The approved claim, as it is actually delivered to the issuer, with its evidence (authored: the artboards start at the issuer's outcome)."""
	instrument = frappe.get_doc(SECURITY, claim.security)
	fields = [kit.dt("Delivered on", "", "sent_on"), kit.tx("Channel", "", "channel"), kit.tx("Delivery reference", "", "reference"), kit.file("Proof of delivery", "", "evidence")]
	b = chrome.base(ctx, "D37-C", d="D37", name="Security claim", title="Send the approved claim", tab="Obligations", next=chrome.next_block(ctx), subj="Security " + instrument.reference,
		regions=[_instrument(ctx, instrument), _claim_rows(ctx, claim), kit.R("Delivery", kit.fl(*fields))], p="Record delivery", s2=[], ev=_evidence(claim))
	b["actions"]["Record delivery"] = kit.command("RecordSecurityClaimCommunication", claim=claim.claim_no)
	return b


def waiting(ctx: Context, claim) -> dict[str, Any]:
	"""D37-P: the claim is delivered; the issuer's outcome is awaited and may be recorded as it arrives. Cash is Finance's separate recovery."""
	instrument = frappe.get_doc(SECURITY, claim.security)
	sent = records.loads(claim.communication_json)
	outcome = records.loads(claim.outcome_json)
	b = chrome.base(ctx, "D37-P", d="D37", name="Security claim", title="Review security claim", tab="Obligations", next=chrome.next_block(ctx), subj="Security " + instrument.reference,
		regions=[_instrument(ctx, instrument), kit.R("Approved claim", kit.r(["Amount", money(claim.amount, ctx.currency)], ["Communication", f"Delivered {_long(sent.get('sent_on'))}"],
			["Outcome", f"{money(outcome.get('proceeds', 0), ctx.currency)} proceeds (issuer reference {outcome['issuer_reference']})" if outcome else "Not recorded"]))], p="", s2=[] if outcome else ["Record claim outcome"], ev=_evidence(claim))
	b["actions"]["Record claim outcome"] = kit.dialog("outcome")
	b["dialogs"]["outcome"] = kit.dlg("Record claim outcome", [kit.fl(kit.tx("Issuer reference", "", "issuer_reference"), kit.dt("Date", "", "outcome_on"), kit.file("Evidence", "", "evidence"), kit.tx("Actual proceeds", "", "proceeds"))],
		"Save outcome", command="RecordSecurityClaimOutcome", args={"claim": claim.claim_no})
	return b


def replacement(ctx: Context, number: int, *, recording: bool = False) -> dict[str, Any]:
	"""D37-X: a replacement or extension is verified (or rejected) while the instrument in force stays operative; once verified it is recorded as the replacement."""
	new = frappe.get_doc(SECURITY, frappe.db.get_value(SECURITY, {"contract_case": ctx.case, "version_no": number}, "name"))
	old = security_actions.operative(ctx.case)
	status = "Operative" if new.state == "Verified" and recording else {"Verified": "Verified", "Recorded": "Not verified"}.get(new.state, new.state)
	table = kit.t(["Instrument", "Amount", "Expiry", "Status"], [[old.reference, money(old.amount, ctx.currency), _day(old.expires_on), "!Operative"], [new.reference, money(new.amount, ctx.currency), _day(new.expires_on), f"!{status}"]], [1])
	confirmation = new.confirmation_reference or "Awaiting the issuer's confirmation"
	note = kit.xh("The old instrument remains operative until the replacement is verified. Nothing is released on expiry.")
	if recording:
		b = chrome.base(ctx, "D37-R", d="D37", name="Security claim", title="Record the replacement security", tab="Obligations", next=chrome.next_block(ctx), regions=[kit.R("Instruments", table, kit.r(["Issuer confirmation", confirmation]), note)],
			p="Record replacement", s2=[], ev=[f"Instrument {new.reference}"])
		b["actions"]["Record replacement"] = kit.command("RecordSecurityAction", action="Replace", security=new.name)
		return b
	b = chrome.base(ctx, "D37-X", d="D37", name="Security claim", title="Verify replacement security", tab="Obligations", next=chrome.next_block(ctx), regions=[kit.R("Instruments", table, kit.r(["Issuer confirmation", confirmation]), note)],
		p="Verify replacement", s2=["Reject replacement"], ev=[f"Instrument {new.reference}"])
	b["actions"]["Verify replacement"] = kit.dialog("verify")
	b["actions"]["Reject replacement"] = kit.dialog("reject")
	b["dialogs"]["verify"] = kit.dlg("Verify replacement", [kit.r(["Instrument", new.reference], ["Issuer", new.issuer], ["Amount", money(new.amount, ctx.currency)]),
		kit.fl(kit.tx("Issuer's confirmation reference", "", "confirmation_reference"), kit.dt("Confirmation received", "", "received_on"), kit.ta("Basis", "", "basis"))], "Verify", command="VerifyContractSecurity", args={"security": new.name})
	b["dialogs"]["reject"] = kit.dlg("Reject replacement", [kit.fl(kit.ta("Reason", "", "reason"))], "Reject", command="RejectContractSecurity", args={"security": new.name})
	return b


def give_back(ctx: Context) -> dict[str, Any]:
	"""D16: the security is returned after the evidenced final acceptance; the return is due the profile's days after it."""
	instrument = security_actions.operative(ctx.case)
	accepted = security_actions.final_acceptance(ctx.case)
	due = security_actions.return_due(ctx.case)
	days = (due - accepted["on"]).days if accepted and due else 0
	b = chrome.base(ctx, "D16", d="D16", name="Security follow-up", title="Performance security", tab="Obligations", next=chrome.next_block(ctx), subj="Agreement 1",
		regions=[kit.R("Instrument", kit.r(["Instrument", instrument.reference], ["Guaranteed amount", money(instrument.amount, ctx.currency)], ["AO final acceptance", _long(accepted["on"])], ["Return due", f"{_long(due)} — {days} days from AO final acceptance"],
			["Status", "Return due"])), kit.R("Return", kit.fl(kit.dt("Return date", "", "returned_on"), kit.file("Evidence", "", "evidence")))], p="Record return", s2=["View guarantee"], ev=[f"Guarantee {instrument.reference}"])
	b["actions"]["Record return"] = kit.command("RecordSecurityAction", action="Return")
	b["actions"]["View guarantee"] = kit.tab("Agreement")
	return b
