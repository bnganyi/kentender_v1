# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Termination and settlement screens (boards D20, D20-P, D20-T, D39-P, D39, D39-C, D39-H; CM-CHG-001 v0.8 sections 5.7, 5.21, 10.4, 10.8).

The financial position on every screen is generated from the records. Terminated is shown as Terminated and never as Completed or Settled; settlement is its own screen and its own fact, and the commitment's
closure is acknowledged separately by the funding owner."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import formatdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import funding_closure, records, termination, work


def _long(value: Any) -> str:
	return formatdate(value, "d MMMM yyyy") if value else "—"


def _evidence(row) -> list[str]:
	return [e["label"] for e in termination.basis(row).get("evidence", [])]


def _position(ctx: Context, row) -> dict[str, Any]:
	found = records.loads(row.financial_json)
	cur = found.get("currency", ctx.currency)
	return kit.R("Financial position", kit.f(["Accepted value", money(found["accepted_value"], cur)], ["Cash paid", money(found["cash_paid"], cur)], ["Supported unpaid", money(found["supported_unpaid"], cur)],
		["Advance balance", money(found["advance_balance"], cur)], ["Disputed claim", money(found["disputed"], cur)]))


def _grounds(row) -> dict[str, Any]:
	parts = termination.basis(row)
	return kit.R("Grounds", kit.r(["Grounds", parts["grounds"]], ["Contractual notice", f"{parts['clause']}; notice and cure evidence attached"], ["HOP recommendation", parts["recommendation"]]))


def _regions(ctx: Context, row) -> list[dict[str, Any]]:
	return [_grounds(row), _position(ctx, row), kit.R("Supporting evidence", kit.lk(*_evidence(row)))]


def request(ctx: Context, *, correcting=None) -> dict[str, Any]:
	"""The head of procurement's request (authored: the artboards start at the Accounting Officer's decision): the grounds, the clause, the evidence and the recommendation, beside the generated position."""
	now = termination.financials(ctx.case)
	cur = now["currency"]
	fields = [kit.sel("Grounds", correcting.grounds if correcting else termination.GROUNDS[0], list(termination.GROUNDS), "grounds"), kit.tx("Clause relied on", termination.basis(correcting)["clause"] if correcting else "", "clause"),
		kit.ta("Recommendation", termination.basis(correcting)["recommendation"] if correcting else "", "recommendation"), kit.file("Notice, cure and legal advice evidence", "", "evidence")]
	b = chrome.base(ctx, "D20-N", d="D20", name="Termination review", title="Request contract termination", tab="Obligations", next=chrome.form_turn(ctx, "RequestContractTermination", "State the grounds for termination."),
		regions=[kit.R("Grounds", kit.fl(*fields)), kit.R("Financial position", kit.f(["Accepted value", money(now["accepted_value"], cur)], ["Cash paid", money(now["cash_paid"], cur)], ["Supported unpaid", money(now["supported_unpaid"], cur)],
			["Advance balance", money(now["advance_balance"], cur)], ["Disputed claim", money(now["disputed"], cur)]))], p="Request termination", s2=["Cancel"], ev=[])
	b["actions"]["Request termination"] = kit.command("RequestContractTermination", **({"correcting": correcting.termination_no} if correcting else {}))
	b["actions"]["Cancel"] = kit.tab("Obligations")
	return b


def decide(ctx: Context, row) -> dict[str, Any]:
	"""D20: the Accounting Officer decides the request."""
	b = chrome.base(ctx, "D20", d="D20", name="Termination review", title="Review contract termination", tab="Obligations", next=chrome.next_block(ctx), subj=f"Agreement 1 · termination {row.termination_no} draft {termination.basis(row).get('draft', 1)}",
		regions=_regions(ctx, row), p="Approve termination", s2=["Decline", "Return for correction"], ev=_evidence(row))
	args = {"termination": row.termination_no}
	b["actions"]["Approve termination"] = kit.dialog("approve")
	b["actions"]["Decline"] = kit.dialog("decline")
	b["actions"]["Return for correction"] = kit.dialog("return")
	for key, title, decision in (("approve", "Approve termination", "Approve"), ("decline", "Decline termination", "Decline"), ("return", "Return for correction", "Return")):
		b["dialogs"][key] = kit.dlg(title, [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm decision", command="DecideContractTermination", args={**args, "decision": decision})
	return b


def notice(ctx: Context, row) -> dict[str, Any]:
	"""The head of procurement records the actual delivery of the approved notice and the day the termination takes effect (authored)."""
	fields = [kit.dt("Delivered on", "", "delivered_on"), kit.tx("How it was delivered", "", "method"), kit.tx("Delivery reference", "", "reference"), kit.dt("Takes effect on", "", "effective_on"), kit.file("Proof of delivery", "", "evidence")]
	b = chrome.base(ctx, "D20-R", d="D20", name="Termination review", title="Record the termination notice", tab="Obligations", next=chrome.next_block(ctx), regions=_regions(ctx, row)[:2] + [kit.R("Notice delivery", kit.fl(*fields))],
		p="Record delivery", s2=[], ev=_evidence(row))
	b["actions"]["Record delivery"] = kit.command("RecordTerminationNotice", termination=row.termination_no)
	return b


def effect(ctx: Context, row) -> dict[str, Any]:
	"""The delivered notice names a later date: the head of procurement records that it took effect when it has come."""
	found = records.loads(row.notice_json)
	b = chrome.base(ctx, "D20-E", d="D20", name="Termination review", title="Record that the termination took effect", tab="Obligations", next=chrome.next_block(ctx),
		regions=[kit.R("Notice", kit.r(["Delivered", _long(found["delivered_on"])], ["Takes effect", _long(found["effective_on"])], ["Reference", found["reference"]]))], p="Record effect", s2=[], ev=_evidence(row))
	b["actions"]["Record effect"] = kit.command("RecordTerminationEffect", termination=row.termination_no)
	return b


def pending(ctx: Context, row) -> dict[str, Any]:
	"""D20-P: approved, the notice not yet delivered. D20-T: the termination is effective and Finance is settling what was accepted; the lifecycle shows Terminated and no Complete contract action."""
	if row.state == "Approved":
		b = chrome.base(ctx, "D20-P", d="D20", name="Termination review", title="Review contract termination", tab="Obligations", next=chrome.next_block(ctx), subj=f"Agreement 1 · termination {row.termination_no} draft {termination.basis(row).get('draft', 1)}",
			regions=_regions(ctx, row), p="", s2=["View notice", "View delivery status"], ev=_evidence(row))
		b["actions"]["View notice"] = b["actions"]["View delivery status"] = kit.tab("History")
		return b
	b = chrome.base(ctx, "D20-T", d="D20", name="Termination review", title="Review contract termination", tab="Obligations", next=chrome.next_block(ctx), subj=f"Agreement 1 · termination {row.termination_no} draft {termination.basis(row).get('draft', 1)}",
		regions=_regions(ctx, row), p="", s2=["View termination record", "View settlement"], ev=_evidence(row))
	b["actions"]["View termination record"] = b["actions"]["View settlement"] = kit.tab("History")
	return b


# -- settlement ----------------------------------------------------------------------------------------------------------------------------
def _reconciliation(ctx: Context, row, recon: dict[str, Any], reference: str) -> dict[str, Any]:
	cur = recon["currency"]
	other = recon["advance_balance"] + recon["disputed"] + recon["authorised_costs"]
	return kit.R("Reconciliation", kit.r(["Finance reconciliation", reference or "Entered when you submit"], ["Accepted", money(recon["accepted_value"], cur)], ["Cash", money(recon["cash_paid"], cur)],
		["Advance, credits, costs, disputes", money(other, cur)], ["Final supported obligation", money(recon["supported_obligation"], cur)], ["Budget decrease", recon["budget_decrease"]],
		["Unclassified remaining items", "None" if not recon["remaining"] else f"{len(recon['remaining'])} listed"]))


def prepare(ctx: Context, row) -> dict[str, Any]:
	"""D39-P: the head of procurement reviews the reconciled settlement and submits it for completion; D39-H when something stands that nobody has resolved or classified."""
	recon = termination.reconciliation(ctx.case, row)
	prepared = records.loads(row.settlement_json)
	named = {(c["kind"], c["ref"]) for c in prepared.get("classified", [])}
	open_items = [r for r in recon["remaining"] if (r["kind"], r["ref"]) not in named]
	advance = next((r for r in recon["remaining"] if r["kind"] == "Advance recovery"), None)
	dialog_fields = [kit.tx("Finance reconciliation reference", prepared.get("finance_reference", ""), "finance_reference")] + [kit.ta(f"Clause that lets '{r['what']}' survive", "", f"basis.{r['kind']}|{r['ref']}") for r in recon["remaining"]]
	if advance is not None and not any(c["kind"] == "Advance recovery" for c in prepared.get("classified", [])):
		b = chrome.base(ctx, "D39-H", d="D39", name="Termination settlement", title="Review termination settlement", tab="Obligations",
			next=kit.blk("The advance recovery needs resolution.", "Finance owner", ["View recovery", "View remaining obligations"]), subj="Finance reconciliation",
			regions=[kit.R("Settlement", kit.r(["Accepted work", money(recon["accepted_value"], recon["currency"])], ["Outstanding advance", money(recon["advance_balance"], recon["currency"])], ["Survivor disposition", "None valid"]))], p="", s2=[], ev=[])
		b["actions"]["View recovery"] = b["actions"]["View remaining obligations"] = kit.tab("Obligations")
		return b
	b = chrome.base(ctx, "D39-P", d="D39", name="Termination settlement", title="Review termination settlement", tab="Obligations", next=chrome.next_block(ctx), subj="Finance reconciliation",
		regions=[_reconciliation(ctx, row, recon, prepared.get("finance_reference", ""))], p="Submit settlement for completion", s2=["Return for correction", "View reconciliation"], ev=["Finance reconciliation"])
	b["actions"]["Submit settlement for completion"] = kit.dialog("prepare")
	b["actions"]["View reconciliation"] = kit.tab("Invoices")
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["dialogs"]["prepare"] = kit.dlg("Submit settlement for completion", [kit.fl(*dialog_fields)], "Submit", command="PrepareTerminationSettlement", args={"termination": row.termination_no})
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return", command="ReturnContractTermination", args={"termination": row.termination_no, "stage": "settlement"})
	return b


def _settlement_region(ctx: Context, recon: dict[str, Any], closure: str) -> dict[str, Any]:
	cur = recon["currency"]
	return kit.R("Settlement", kit.r(["Accepted work", money(recon["accepted_value"], cur)], ["Cash confirmed", money(recon["cash_paid"], cur)], ["Advance", money(recon["advance_balance"], cur)], ["Credit", money(0, cur)],
		["Authorised costs", money(recon["authorised_costs"], cur)], ["Dispute", money(recon["disputed"], cur)], ["Unperformed balance", f"{money(recon['unperformed_balance'], cur)} extinguished by effective termination"],
		["Final supported obligation", money(recon["supported_obligation"], cur)], ["Budget decrease", recon["budget_decrease"]], ["Closure acknowledgement", closure]))


def complete(ctx: Context, row) -> dict[str, Any]:
	"""D39: the Accounting Officer completes the settlement."""
	recon = termination.reconciliation(ctx.case, row)
	b = chrome.base(ctx, "D39", d="D39", name="Termination settlement", title="Complete termination settlement", tab="Obligations", next=chrome.next_block(ctx), subj="HOP-reviewed reconciliation",
		regions=[_settlement_region(ctx, recon, funding_closure.status(ctx.case, f"closure {termination.subject_of(row)}").replace("Not requested", "Pending"))], p="Complete settlement", s2=["Return for correction", "View termination"],
		ev=["Finance reconciliation", "HOP review"])
	b["actions"]["Complete settlement"] = kit.dialog("complete")
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["actions"]["View termination"] = kit.tab("History")
	b["dialogs"]["complete"] = kit.dlg("Complete settlement", [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm completion", command="CompleteTerminationSettlement", args={"termination": row.termination_no})
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return", command="ReturnContractTermination", args={"termination": row.termination_no, "stage": "settlement"})
	return b


def settled(ctx: Context, row) -> dict[str, Any]:
	"""D39-C: the settlement is completed on its own date; the lifecycle stays Terminated and the funding finalisation is shown as acknowledged or pending."""
	done = records.loads(row.settlement_json)
	status = funding_closure.status(ctx.case, f"closure {termination.subject_of(row)}")
	sentence = "Funding finalisation pending with the Budget owner." if status != "Acknowledged" else "The Budget owner acknowledged the commitment's closure."
	b = chrome.base(ctx, "D39-C", d="D39", name="Termination settlement", title="Complete termination settlement", tab="Obligations",
		next=kit.done(f"{ctx.name(done['completed_by'])} completed the termination settlement on {when(done['completed_at'])}.", sentence),
		regions=[_settlement_region(ctx, done["reconciliation"], "Acknowledged" if status == "Acknowledged" else "Pending")], p="", s2=["View settlement", "View funding update"], ev=[])
	b["actions"]["View settlement"] = b["actions"]["View funding update"] = kit.tab("History")
	return b
