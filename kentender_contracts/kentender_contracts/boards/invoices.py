# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Invoices tab: the supplier's claim, procurement's review and certification, and the embedded Finance editors
(boards D18, D18-R, D18-C, D08, D08-C, D33, D33-W, D33-A, D09-F, D17, D17-S, D09; CM-CHG-001 v0.8 sections 5.8, 5.12, 10.7).

Finance works on the native record through these screens (section 5.12): the maker's draft and the approver's decision are the same Purchase Invoice and Payment Entry, not a copy."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt, formatdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import payment, position, records, work

COMPANY_DEFAULT = "company"


def _invoice(ctx: Context, number: int):
	name = frappe.db.get_value("Contract Invoice", {"contract_case": ctx.case, "invoice_no": number}, "name")
	return frappe.get_doc("Contract Invoice", name)


def _no(subject: str) -> int:
	return cint(subject.split()[-1])


def _company() -> str:
	return frappe.defaults.get_global_default("company") or frappe.db.get_value("Company", {}, "name")


def _claim_rows(ctx: Context, invoice) -> list[list[str]]:
	match = records.loads(invoice.matching_json)
	return [[l["item"] if "item" in l else (ctx.terms["lines"][0].get("description") or "Item"), str(r["claimed_quantity"]), str(r["eligible_quantity"] + (r["claimed_quantity"] if r["outcome"] == "Supported" else 0)),
		money(r["claimed_rate"], ctx.currency), money(r["amount"], ctx.currency), money(min(r["claimed_quantity"], r["eligible_quantity"]) * (r["contract_rate"] or r["claimed_rate"]), ctx.currency)]
		for l, r in zip(records.loads(invoice.lines_json), match["rows"])]


def _item(ctx: Context) -> str:
	return (ctx.terms.get("lines") or [{}])[0].get("description") or "Item"


def eligible_unclaimed(ctx: Context) -> dict[str, int]:
	claimed = payment._claimed(ctx.case)
	return {lid: max(0, l["accepted"] - claimed.get(lid, 0)) for lid, l in ctx.position["lines"].items()}


def d18(ctx: Context) -> dict:
	"""Submit invoice (the supplier's representative or signatory)."""
	line = (ctx.terms.get("lines") or [{}])[0]
	qty = eligible_unclaimed(ctx).get(line.get("line_id"), 0)
	rate = flt(line.get("rate"))
	fields = [kit.tx("Invoice number", "", "claim_reference"), kit.dt("Invoice date", "", "invoice_date")]
	items = kit.t(["Item", "Quantity", "Rate", "Tax", "Total"], [[_item(ctx), f"#{qty}", money(rate, ctx.currency), "Included" if ctx.terms.get("tax_included") else "Excluded", money(qty * rate, ctx.currency)]], [1, 2, 4],
		inputs={"0,1": f"quantity.{line.get('line_id')}"})
	b = chrome.base(ctx, "D18", d="D18", name="Supplier invoice", title="Submit invoice", tab="Invoices", next=chrome.next_block(ctx) or kit.turn("Enter the invoice details.", ctx.name(ctx.user)), ev=["Agreement 1"],
		regions=[kit.R("Invoice", kit.fl(*fields)), kit.R("Items", items)], p="Submit invoice", s2=["Cancel"])
	b["lineId"] = line.get("line_id")
	b["actions"]["Submit invoice"] = kit.command("SubmitContractInvoice")
	b["actions"]["Cancel"] = kit.tab("Invoices")
	return b


def d18r(ctx: Context, invoice) -> dict:
	match = records.loads(invoice.matching_json)
	problems = [m for r in match["rows"] for m in r["reasons"]] + (["The claim is more than the contract still supports."] if match.get("exceeds_remaining") else [])
	b = chrome.base(ctx, "D18-R", d="D18", name="Supplier invoice", title="Submit invoice", tab="Invoices", next=chrome.next_block(ctx),
		regions=[kit.R(f"Invoice {invoice.claim_reference}", kit.r(["Status", "Needs review"], ["Received", when(invoice.received_at)], ["Claimed", f"{sum(cint(l['quantity']) for l in records.loads(invoice.lines_json))} {_item(ctx).lower()} · {money(invoice.claimed_amount, ctx.currency)}"]),
			kit.xs(problems[0] if problems else "The invoice needs review."))], ev=["Agreement 1"])
	return b


def d18c(ctx: Context, invoice) -> dict:
	"""Correct invoice: the held claim stays as version 1 and a linked successor replaces it."""
	line = (ctx.terms.get("lines") or [{}])[0]
	qty = eligible_unclaimed(ctx).get(line.get("line_id"), 0)
	rate = flt(line.get("rate"))
	b = chrome.base(ctx, "D18-C", d="D18", name="Supplier invoice", title="Correct invoice", tab="Invoices", next=chrome.next_block(ctx), ev=["Agreement 1"],
		regions=[kit.R("Version 1 (retained)", kit.r(["Invoice", f"{invoice.claim_reference} version 1"], ["Claimed", f"{sum(cint(l['quantity']) for l in records.loads(invoice.lines_json))} {_item(ctx).lower()} · {money(invoice.claimed_amount, ctx.currency)}"], ["Received", when(invoice.received_at)])),
			kit.R("Correction", kit.t(["Item", "Quantity", "Rate", "Tax", "Total"], [[_item(ctx), f"#{qty}", money(rate, ctx.currency), "Included", money(qty * rate, ctx.currency)]], [1, 2, 4], inputs={"0,1": f"quantity.{line.get('line_id')}"}),
				kit.fl(kit.ta("Reason", "", "reason")))],
		p="Submit correction", s2=["Cancel"])
	b["lineId"] = line.get("line_id")
	b["actions"]["Submit correction"] = kit.command("CorrectContractInvoice", successor_of=invoice.name, claim_reference=f"{invoice.claim_reference}-R", invoice_date=str(invoice.invoice_date))
	b["actions"]["Cancel"] = kit.tab("Invoices")
	return b


def _comparison(ctx: Context, invoice, warn: bool) -> dict:
	cols = ["Item", "Invoiced", "Eligible", "Rate", "Claimed", "Supported"]
	rows = _claim_rows(ctx, invoice)
	blocks: list[dict] = [kit.t(cols, rows, [1, 2, 3, 4, 5])]
	if warn:
		blocks.append(kit.xs("Some units have not been accepted."))
	return kit.R("Comparison", *blocks)


def d08(ctx: Context, invoice) -> dict:
	"""Review invoice: procurement sees a claim that does not match what is accepted and asks for a correction (correction-first)."""
	b = chrome.base(ctx, "D08", d="D08", name="Invoice review", title="Review invoice", tab="Invoices", next=chrome.next_block(ctx), ev=[f"Supplier invoice {invoice.claim_reference}", "Acceptance report 1", "Receipt 1"],
		regions=[_comparison(ctx, invoice, True)], p="Request correction")
	b["actions"]["Request correction"] = kit.dialog("correction")
	b["dialogs"]["correction"] = kit.dlg("Request correction", [kit.r(["Recipient", ctx.doc.supplier_name]), kit.fl(kit.ta("Message", "", "reason"))], "Send request", command="RequestInvoiceCorrection", args={"invoice": invoice.name})
	return b


def d08c(ctx: Context, invoice) -> dict:
	"""Corrected claim: certify (the exact matching, the exact accepted units)."""
	accepted = [u["unit"] for u in ctx.position["units"].values() if u["status"] == "Accepted"]
	rejected = [u["unit"] for u in ctx.position["units"].values() if u["status"] in ("Rejected", "Returned")]
	statement = (f"I certify that invoice {invoice.claim_reference}, for {money(invoice.claimed_amount, ctx.currency)}, is supported by the cited effective contract and accepted goods or services, "
		"after the adjustments and recoveries shown in the certification schedule.")
	b = chrome.base(ctx, "D08-C", d="D08", name="Invoice review", title="Review invoice", tab="Invoices", next=chrome.next_block(ctx), ev=[f"Supplier invoice {invoice.claim_reference}", "Acceptance report 1", "Receipt 1"],
		regions=[_comparison(ctx, invoice, False), kit.R("Certification", kit.x(statement), kit.r(["Accepted units", ", ".join(accepted) or "—"], ["Rejected units", (", ".join(rejected) + " — not certified") if rejected else "None"], ["Recipient", "Finance"]))],
		p="Sign certification")
	b["actions"]["Sign certification"] = kit.command("SignContractCertification", invoice=invoice.name)
	return b


# -- Finance: the accounting invoice ------------------------------------------------------------------------------------------------------
def _source(ctx: Context, invoice) -> dict:
	cert = frappe.db.get_value("Contract Certification", {"contract_case": ctx.case, "invoice": invoice.name, "state": "Signed"}, "name") or ""
	return kit.R("Source", kit.r(["Source claim", invoice.claim_reference], ["Certification", "Signed" if cert else "Not signed"], ["Company", _company()], ["Supplier", ctx.doc.supplier_name], ["Currency", ctx.currency],
		["Invoice date", formatdate(invoice.invoice_date, "d MMMM yyyy")]))


def _accepted_items(ctx: Context, invoice) -> dict:
	lines = records.loads(invoice.lines_json)
	return kit.R("Accepted items", kit.t(["Item", "Quantity", "Rate", "Total"], [[_item(ctx), str(l["quantity"]), money(r["claimed_rate"], ctx.currency), money(r["amount"], ctx.currency)]
		for l, r in zip(lines, records.loads(invoice.matching_json)["rows"])], [1, 2, 3]))


def _accounting(invoice, *, editable: bool) -> dict:
	pi = frappe.get_doc("Purchase Invoice", invoice.native_invoice)
	row = pi.items[0] if pi.items else None
	values = {"posting_date": str(pi.posting_date), "payable_account": pi.credit_to, "expense_account": row.expense_account if row else "", "tax_template": pi.taxes_and_charges or "", "cost_centre": (row.cost_center if row else "") or ""}
	if not editable:
		return kit.R("Accounting details", kit.r(["Posting date", formatdate(values["posting_date"], "d MMMM yyyy")], ["Payable account", values["payable_account"]], ["Accounting treatment", values["expense_account"]],
			["Tax treatment", values["tax_template"] or "Tax included in the price"], ["Cost centre", values["cost_centre"]]))
	record = "contracts.native_record"
	return kit.R("Accounting details", kit.fl(kit.dt("Posting date", values["posting_date"], "posting_date"), kit.pick("Payable account", values["payable_account"], record, "payable_account", {"kind": "account.payable"}, values["payable_account"], "account"),
		kit.pick("Accounting treatment", values["expense_account"], record, "expense_account", {"kind": "account.expense"}, values["expense_account"], "account"),
		kit.pick("Tax treatment", values["tax_template"], record, "tax_template", {"kind": "tax_template"}, values["tax_template"], "tax template"),
		kit.pick("Cost centre", values["cost_centre"], record, "cost_centre", {"kind": "cost_centre"}, values["cost_centre"], "cost centre")),
		kit.xh("The supplier's quantities and prices are not editable here. The tax breakdown is generated from the configured template."))


def d33(ctx: Context, invoice, *, mode: str = "maker") -> dict:
	"""Finance invoice preparation (maker), D33-W (submitted, waiting) and D33-A (approver review)."""
	ident = {"maker": "D33", "waiting": "D33-W", "approver": "D33-A"}[mode]
	regions = [_source(ctx, invoice), _accepted_items(ctx, invoice), _accounting(invoice, editable=mode == "maker")]
	if mode == "approver":
		regions.append(kit.R("Prepared by", kit.r(["Finance maker", ctx.name(invoice.finance_maker)])))
	title = "Prepare accounting invoice" if mode != "approver" else "Review accounting invoice"
	b = chrome.base(ctx, ident, d="D33", name="Finance invoice preparation", title=title, tab="Invoices", next=chrome.next_block(ctx), regions=regions, ev=[f"Supplier invoice {invoice.claim_reference}", "Certification 1", "Receipt 1"])
	if mode == "maker":
		b["p"], b["s2"] = "Submit invoice for approval", ["Save draft"]
		b["actions"]["Save draft"] = kit.command("SaveNativeFinanceDraft", kind="invoice", invoice=invoice.name)
		b["actions"]["Submit invoice for approval"] = {**kit.command("SaveNativeFinanceDraft", kind="invoice", invoice=invoice.name), "then": {"command": "SubmitNativeFinanceForApproval", "args": {"kind": "invoice", "invoice": invoice.name}}}
	elif mode == "approver":
		b["p"], b["s2"] = "Approve accounting invoice", ["Return invoice for correction"]
		b["actions"]["Approve accounting invoice"] = kit.command("ApproveNativeFinanceRecord", kind="invoice", invoice=invoice.name)
		b["actions"]["Return invoice for correction"] = kit.dialog("return")
		b["dialogs"]["return"] = kit.dlg("Return invoice for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return invoice", command="ReturnNativeFinanceForCorrection", args={"kind": "invoice", "invoice": invoice.name})
	return b


# -- Finance: the payment -----------------------------------------------------------------------------------------------------------------
def _payment_source(ctx: Context, invoice, amount: float) -> dict:
	cert = frappe.db.get_value("Contract Certification", {"contract_case": ctx.case, "invoice": invoice.name, "state": "Signed"}, "name") or ""
	return kit.R("Source", kit.r(["Company", _company()], ["Supplier", ctx.doc.supplier_name], ["Currency", ctx.currency], ["Source", invoice.claim_reference], ["Certification", "Signed" if cert else "Not signed"],
		["Accounting invoice", "Posted" if invoice.accounting_state == "Posted" else invoice.accounting_state], ["Payable / certified outstanding", money(amount, ctx.currency)], ["Payment hold", "None"],
		["Beneficiary", "Verified account on file"]))


def _draft_payment(ctx: Context, invoice):
	for p in payment.payments(ctx.case):
		if p["invoice"] == invoice.name and p["docstatus"] == 0:
			return frappe.get_doc("Payment Entry", p["name"])
	return None


def d09f(ctx: Context, invoice, *, waiting: bool = False) -> dict:
	"""Prepare payment (the Finance maker); D09-F · Submitted when it is with the approver."""
	from kentender_contracts.native import payment_guard

	available = payment_guard.entitlement(invoice.native_invoice)["available"]
	pe = _draft_payment(ctx, invoice)
	modes = sorted(frappe.get_all("Mode of Payment", pluck="name", limit=50))
	amount = flt(pe.paid_amount) if pe else available
	payable = frappe.db.get_value("Purchase Invoice", invoice.native_invoice, "credit_to")
	fields = [kit.dt("Posting date", str(pe.posting_date) if pe else frappe.utils.today(), "posting_date"),
		kit.sel("Payment method", (pe.mode_of_payment if pe else "") or "", modes, "mode_of_payment"), kit.pick("Bank account", (pe.paid_from if pe else "") or "", "contracts.native_record", "paid_from", {"kind": "account.bank"}, (pe.paid_from if pe else "") or "", "bank account"),
		kit.ro("Payable account", payable, "payable_account"), kit.tx("Amount", f"{amount:.2f}", "amount"), kit.ro("Invoice allocation — " + invoice.claim_reference, money(amount, ctx.currency), "allocation"),
		kit.tx("Reference", (pe.reference_no if pe else "") or "", "reference_no")]
	regions = [_payment_source(ctx, invoice, available), kit.R("Payment details", kit.fl(*fields)), kit.R("Calculated", kit.f(["Supported deductions", money(0, ctx.currency)], ["Advance recovery", money(0, ctx.currency)], ["Unapplied amount", money(0, ctx.currency)]))]
	b = chrome.base(ctx, "D09-F · Submitted" if waiting else "D09-F", d="D09", name="Payment follow-up", title="Prepare payment", tab="Invoices", next=chrome.next_block(ctx), regions=regions,
		ev=["Certification 1", "Accounting invoice", "Verified beneficiary reference"])
	if not waiting:
		b["p"], b["s2"] = "Submit payment for approval", ["Save draft"]
		save = kit.command("SaveNativeFinanceDraft", kind="payment", invoice=invoice.name)
		b["actions"]["Save draft"] = save
		b["actions"]["Submit payment for approval"] = {**save, "then": {"command": "SubmitNativeFinanceForApproval", "args": {"kind": "payment"}, "carry": ["payment"]}}
	return b


def d17(ctx: Context, invoice, payment_entry: str, *, settle: bool = False) -> dict:
	"""Finance payment approval (the approver) and, once posted, the settlement record (D17-S)."""
	pe = frappe.get_doc("Payment Entry", payment_entry)
	if settle:
		fields = [kit.ro("Amount", money(pe.paid_amount, ctx.currency), "amount"), kit.dt("Settlement date", "", "effective_date"), kit.tx("Bank reference", "", "evidence")]
		b = chrome.base(ctx, "D17-S", d="D17", name="Finance payment approval", title="Review payment", tab="Invoices", next=chrome.next_block(ctx), regions=[kit.R("Settlement", kit.fl(*fields))], p="Confirm payment",
			ev=["Certification 1", "Accounting invoice", f"Payment Entry {payment_entry}"])
		b["actions"]["Confirm payment"] = kit.command("RecordFinanceSettlement", payment=payment_entry)
		return b
	pay = kit.R("Payment", kit.r(["Supplier", ctx.doc.supplier_name], ["Invoice", invoice.claim_reference], ["Certified / payable", money(pe.paid_amount, ctx.currency)], ["Proposed cash", money(pe.paid_amount, ctx.currency)],
		["Prepared by", ctx.name(pe.owner)], ["Payment hold", "None"], ["Beneficiary reference", "Verified account on file"], ["Settlement", "Not confirmed"]))
	det = kit.R("Payment details", kit.r(["Posting date", formatdate(pe.posting_date, "d MMMM yyyy")], ["Payment method", pe.mode_of_payment or ""], ["Bank account", pe.paid_from or ""], ["Payable account", pe.paid_to or ""],
		["Amount", money(pe.paid_amount, ctx.currency)], ["Allocation", f"{invoice.claim_reference} · {money(pe.paid_amount, ctx.currency)}"], ["Reference", pe.reference_no or ""],
		["Supported deductions / advance recovery / unapplied", " / ".join([money(0, ctx.currency)] * 3)]))
	b = chrome.base(ctx, "D17", d="D17", name="Finance payment approval", title="Review payment", tab="Invoices", next=chrome.next_block(ctx), regions=[pay, det], p="Approve payment", s2=["Return payment for correction"],
		ev=["Certification 1", "Accounting invoice", f"Payment Entry {payment_entry}"])
	b["actions"]["Approve payment"] = kit.command("ApproveNativeFinanceRecord", kind="payment", payment=payment_entry)
	b["actions"]["Return payment for correction"] = kit.dialog("return")
	b["dialogs"]["return"] = kit.dlg("Return payment for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return payment", command="ReturnNativeFinanceForCorrection", args={"kind": "payment", "payment": payment_entry})
	return b


def d09(ctx: Context, invoice=None) -> dict:
	"""Invoice and payment: the read-only follow-up of the latest claim (the contract owner's and every reader's view of the Invoices tab)."""
	rows = []
	for inv in ctx.invoices:
		pays = [p for p in payment.payments(ctx.case) if p["invoice"] == inv.name]
		posted = [p for p in pays if p["docstatus"] == 1]
		settled = payment.settled_amount(inv.name)
		rows.append([inv.claim_reference, money(inv.claimed_amount, ctx.currency), f"!{inv.state}" if inv.state in ("Paid", "Certified") else inv.state, inv.accounting_state if inv.native_invoice else "—", money(sum(flt(p["paid_amount"]) for p in posted), ctx.currency) + " recorded" if posted else "—", money(settled, ctx.currency) + " confirmed" if settled else "Not confirmed"])
	focus = invoice or (ctx.invoices[-1] if ctx.invoices else None)
	regions = []
	if focus is not None:
		pays = [p for p in payment.payments(ctx.case) if p["invoice"] == focus.name and p["docstatus"] == 1]
		cert = "Signed" if frappe.db.exists("Contract Certification", {"invoice": focus.name, "state": "Signed"}) else "Not signed"
		regions.append(kit.R("", kit.r(["Invoice", money(focus.claimed_amount, ctx.currency)], ["Certification", cert], ["Accounting entry", "Posted" if focus.accounting_state == "Posted" else "Not posted"],
			["Payment", money(sum(flt(p["paid_amount"]) for p in pays), ctx.currency) + " recorded" if pays else "None yet"], ["Settlement", "Confirmed" if payment.settled_amount(focus.name) else "Not confirmed"])))
	if len(ctx.invoices) > 1:
		regions.append(kit.R("Invoices", kit.t(["Invoice", "Claimed", "Status", "Accounting", "Payment", "Settlement"], rows, [1])))
	if not regions:
		regions.append(kit.R("Invoices", kit.xh("No invoice has been submitted yet.")))
	b = chrome.base(ctx, "D09", d="D09", name="Payment follow-up", title="Invoice and payment", tab="Invoices", next=chrome.next_block(ctx), regions=regions, ev=[])
	if ctx.doc.lifecycle == "Active" and "supplier" in ctx.audiences and any(v > 0 for v in eligible_unclaimed(ctx).values()):
		b["p"] = "Submit invoice"
		b["actions"]["Submit invoice"] = kit.route(ctx.case, "invoices", "submit-invoice")
	return b
