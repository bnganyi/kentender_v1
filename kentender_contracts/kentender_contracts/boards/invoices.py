# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Invoices tab: the supplier's claim, procurement's review and certification, and the embedded Finance editors
(boards D18, D18-R, D18-C, D08, D08-C, D33, D33-W, D33-A, D09-F, D17, D17-S, D09; CM-CHG-001 v0.8 sections 5.8, 5.12, 10.7).

Finance works on the native record through these screens (section 5.12): the maker's draft and the approver's decision are the same Purchase Invoice and Payment Entry, not a copy."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt, formatdate

from kentender_contracts.boards import chrome, kit, statements
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import advance, holds, payment, position, records, work

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
	return [[_item(ctx, l["line_id"]), str(r["claimed_quantity"]), str(r["eligible_quantity"] + (r["claimed_quantity"] if r["outcome"] == "Supported" else 0)),
		money(r["claimed_rate"], ctx.currency), money(r["amount"], ctx.currency), money(min(r["claimed_quantity"], r["eligible_quantity"]) * (r["contract_rate"] or r["claimed_rate"]), ctx.currency)]
		for l, r in zip(records.loads(invoice.lines_json), match["rows"])]


def _line(ctx: Context, line_id: str = "") -> dict:
	"""The line a claim is for: the one named, else the first that still has accepted quantity to claim, else the first."""
	lines = ctx.terms.get("lines") or [{}]
	if line_id:
		return next((l for l in lines if l.get("line_id") == line_id), lines[0])
	left = eligible_unclaimed(ctx)
	return next((l for l in lines if left.get(l.get("line_id"))), lines[0])


def _item(ctx: Context, line_id: str = "") -> str:
	return _line(ctx, line_id).get("description") or "Item"


def _claimed_item(ctx: Context, invoice) -> str:
	"""The name of the item an invoice claims."""
	return _item(ctx, records.loads(invoice.lines_json)[0]["line_id"])


def eligible_unclaimed(ctx: Context) -> dict[str, int]:
	claimed = payment._claimed(ctx.case)
	return {lid: max(0, l["accepted"] - claimed.get(lid, 0)) for lid, l in ctx.position["lines"].items()}


def d18(ctx: Context) -> dict:
	"""Submit invoice (the supplier's representative or signatory)."""
	line = _line(ctx)
	qty = eligible_unclaimed(ctx).get(line.get("line_id"), 0)
	rate = flt(line.get("rate"))
	fields = [kit.tx("Invoice number", "", "claim_reference"), kit.dt("Invoice date", "", "invoice_date")]
	items = kit.t(["Item", "Quantity", "Rate", "Tax", "Total"], [[_item(ctx, line.get("line_id")), f"#{qty}", money(rate, ctx.currency), "Included" if ctx.terms.get("tax_included") else "Excluded", money(qty * rate, ctx.currency)]], [1, 2, 4],
		inputs={"0,1": f"quantity.{line.get('line_id')}"})
	b = chrome.base(ctx, "D18", d="D18", name="Supplier invoice", title="Submit invoice", tab="Invoices", next=chrome.next_block(ctx) or kit.turn("Enter the invoice details.", ctx.name(ctx.user)), ev=["Agreement 1"],
		regions=[kit.R("Invoice", kit.fl(*fields)), kit.R("Items", items)], p="Submit invoice", s2=["Cancel"])
	b["lineId"] = line.get("line_id")
	b["actions"]["Submit invoice"] = kit.command("SubmitContractInvoice")
	b["actions"]["Cancel"] = kit.tab("Invoices")
	return b


def d18r(ctx: Context, invoice) -> dict:
	match = records.loads(invoice.matching_json)
	problems = [f["reason"] for f in match.get("findings", [])] or [m for r in match["rows"] for m in r["reasons"]]
	b = chrome.base(ctx, "D18-R", d="D18", name="Supplier invoice", title="Submit invoice", tab="Invoices", next=chrome.next_block(ctx),
		regions=[kit.R(f"Invoice {invoice.claim_reference}", kit.r(["Status", "Needs review"], ["Received", when(invoice.received_at)], ["Claimed", f"{sum(cint(l['quantity']) for l in records.loads(invoice.lines_json))} {_claimed_item(ctx, invoice).lower()} · {money(invoice.claimed_amount, ctx.currency)}"]),
			kit.xs(problems[0] if problems else "The invoice needs review."))], ev=["Agreement 1"])
	return b


def d18c(ctx: Context, invoice) -> dict:
	"""Correct invoice: the held claim stays as version 1 and a linked successor replaces it."""
	line = _line(ctx, records.loads(invoice.lines_json)[0]["line_id"])
	claimed = payment._claimed(ctx.case, exclude=invoice.name)  # the claim being corrected no longer holds the entitlement its successor will take
	qty = max(0, ctx.position["lines"][line["line_id"]]["accepted"] - claimed.get(line["line_id"], 0))
	rate = flt(line.get("rate"))
	b = chrome.base(ctx, "D18-C", d="D18", name="Supplier invoice", title="Correct invoice", tab="Invoices", next=chrome.next_block(ctx), ev=["Agreement 1"],
		regions=[kit.R("Version 1 (retained)", kit.r(["Invoice", f"{invoice.claim_reference} version 1"], ["Claimed", f"{sum(cint(l['quantity']) for l in records.loads(invoice.lines_json))} {_claimed_item(ctx, invoice).lower()} · {money(invoice.claimed_amount, ctx.currency)}"], ["Received", when(invoice.received_at)])),
			kit.R("Correction", kit.t(["Item", "Quantity", "Rate", "Tax", "Total"], [[_claimed_item(ctx, invoice), f"#{qty}", money(rate, ctx.currency), "Included", money(qty * rate, ctx.currency)]], [1, 2, 4], inputs={"0,1": f"quantity.{line.get('line_id')}"}),
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


def d08d(ctx: Context, invoice) -> dict:
	"""An apparent duplicate (authored; the artboards show the review of a claim that does not match): Finance sees the claim beside the one it appears to repeat and decides, with a reason. The claim is
	never deleted: a duplicate is set aside and kept, one that is not goes on to be matched on its own merits."""
	match = records.loads(invoice.matching_json)
	other = frappe.get_doc("Contract Invoice", match["duplicate_of"])
	rows = [[f"{other.claim_reference} (recorded {when(other.received_at)})", str(sum(cint(l["quantity"]) for l in records.loads(other.lines_json))), money(other.claimed_amount, ctx.currency)],
		[f"{invoice.claim_reference} (recorded {when(invoice.received_at)})", str(sum(cint(l["quantity"]) for l in records.loads(invoice.lines_json))), money(invoice.claimed_amount, ctx.currency)]]
	b = chrome.base(ctx, "D08-D", d="D08", name="Invoice review", title="Review possible duplicate", tab="Invoices", next=chrome.next_block(ctx), ev=[f"Supplier invoice {invoice.claim_reference}", f"Supplier invoice {other.claim_reference}"],
		regions=[kit.R("Possible duplicate", kit.t(["Invoice", "Quantity", "Amount"], rows, [1, 2]), kit.xs(match["findings"][0]["reason"]))], p="Set aside as duplicate", s2=["This is not a duplicate"])
	b["actions"]["Set aside as duplicate"] = kit.dialog("duplicate")
	b["actions"]["This is not a duplicate"] = kit.dialog("distinct")
	b["dialogs"]["duplicate"] = kit.dlg("Set aside as duplicate", [kit.fl(kit.ta("Reason", "", "reason"))], "Set aside", command="ResolveInvoiceDuplicate", args={"invoice": invoice.name, "disposition": "Duplicate"})
	b["dialogs"]["distinct"] = kit.dlg("This is not a duplicate", [kit.fl(kit.ta("Reason", "", "reason"))], "Release for review", command="ResolveInvoiceDuplicate", args={"invoice": invoice.name, "disposition": "Not a duplicate"})
	return b


def d08c(ctx: Context, invoice) -> dict:
	"""Corrected claim: certify (the exact matching, the exact accepted units)."""
	accepted = [u["unit"] for u in ctx.position["units"].values() if u["status"] == "Accepted"]
	rejected = [u["unit"] for u in ctx.position["units"].values() if u["status"] in ("Rejected", "Returned")]
	statement = statements.CERTIFICATION.format(invoice=invoice.claim_reference, amount=money(invoice.claimed_amount, ctx.currency))
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
	return kit.R("Accepted items", kit.t(["Item", "Quantity", "Rate", "Total"], [[_claimed_item(ctx, invoice), str(l["quantity"]), money(r["claimed_rate"], ctx.currency), money(r["amount"], ctx.currency)]
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
	unresolved = payment.accounting_setup(ctx.case, invoice.name) if mode == "maker" and invoice.native_invoice else []
	b = chrome.base(ctx, "D33-U" if unresolved else ident, d="D33", name="Finance invoice preparation", title=title, tab="Invoices",
		next=kit.blk("The accounting setup needs review.", "Finance configuration owner", ["View certification"], "; ".join(unresolved)) if unresolved else chrome.next_block(ctx), regions=regions, ev=[f"Supplier invoice {invoice.claim_reference}", "Certification 1", "Receipt 1"])
	if unresolved:
		b["p"], b["s2"] = "", []  # submission is unavailable until the configuration owner resolves the mapping
	elif mode == "maker":
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
def advance_as_invoice(row):
	"""An advance seen by the Finance payment screens: it has a claim reference, an amount and a certification, no native invoice and no accounting step."""
	return frappe._dict(name=row.name, claim_reference=row.claim_reference, invoice_no=row.advance_no, native_invoice="", accounting_state="Posted", state=row.state, contract_case=row.contract_case,
		claimed_amount=row.amount, is_advance=True, finance_maker="")


def _payment_source(ctx: Context, invoice, amount: float) -> dict:
	cert = (frappe.db.get_value("Contract Advance", invoice.name, "proof_reference") if invoice.get("is_advance") else frappe.db.get_value("Contract Certification", {"contract_case": ctx.case, "invoice": invoice.name, "state": "Signed"}, "name")) or ""
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

	from kentender_contracts.services import formation

	advance_payment = bool(invoice.get("is_advance"))
	available = payment_guard.advance_entitlement(formation.native_order(ctx.case))["available"] if advance_payment else payment_guard.entitlement(invoice.native_invoice)["available"]
	pe = _draft_payment(ctx, invoice)
	modes = sorted(frappe.get_all("Mode of Payment", pluck="name", limit=50))
	amount = flt(pe.paid_amount) if pe else available
	payable = frappe.db.get_value("Company", _company(), "default_payable_account") if advance_payment else frappe.db.get_value("Purchase Invoice", invoice.native_invoice, "credit_to")
	fields = [kit.dt("Posting date", str(pe.posting_date) if pe else frappe.utils.today(), "posting_date"),
		kit.sel("Payment method", (pe.mode_of_payment if pe else "") or "", modes, "mode_of_payment"), kit.pick("Bank account", (pe.paid_from if pe else "") or "", "contracts.native_record", "paid_from", {"kind": "account.bank"}, (pe.paid_from if pe else "") or "", "bank account"),
		kit.ro("Payable account", payable, "payable_account"), kit.tx("Amount", f"{amount:.2f}", "amount"), kit.ro("Invoice allocation — " + invoice.claim_reference, money(amount, ctx.currency), "allocation"),
		kit.tx("Reference", (pe.reference_no if pe else "") or "", "reference_no")]
	regions = [_payment_source(ctx, invoice, available), kit.R("Payment details", kit.fl(*fields)), kit.R("Calculated", kit.f(["Supported deductions", money(0, ctx.currency)], ["Advance recovery", money(0, ctx.currency)], ["Unapplied amount", money(0, ctx.currency)]))]
	b = chrome.base(ctx, "D09-F · Submitted" if waiting else "D09-F", d="D09", name="Payment follow-up", title="Prepare payment", tab="Invoices", next=chrome.next_block(ctx), regions=regions,
		ev=["Certification 1", "Accounting invoice", "Verified beneficiary reference"])
	if not waiting:
		b["p"], b["s2"] = "Submit payment for approval", ["Save draft"]
		save = kit.command("SaveNativeFinanceDraft", kind="advance", advance=invoice.name) if advance_payment else kit.command("SaveNativeFinanceDraft", kind="payment", invoice=invoice.name)
		b["actions"]["Save draft"] = save
		b["actions"]["Submit payment for approval"] = {**save, "then": {"command": "SubmitNativeFinanceForApproval", "args": {"kind": "payment"}, "carry": ["payment"]}}
	return b


def d17(ctx: Context, invoice, payment_entry: str, *, settle: bool = False) -> dict:
	"""Finance payment approval (the approver) and, once posted, the settlement record (D17-S)."""
	pe = frappe.get_doc("Payment Entry", payment_entry)
	hold = next(iter(holds.blocking(ctx.case, "pay", f"invoice {invoice.invoice_no}")), None) if not settle else None
	if hold:  # D17-H: the payment is held; only the missing step is shown
		pay = kit.R("Payment", kit.r(["Supplier", ctx.doc.supplier_name], ["Invoice", invoice.claim_reference], ["Prepared by", ctx.name(pe.owner)], ["Payment hold", hold.reason], ["Settlement", "Not confirmed"]))
		return chrome.base(ctx, "D17-H", d="D17", name="Finance payment approval", title="Review payment", tab="Invoices", next=kit.blk("This payment is on hold.", ctx.name(next(iter(work.holders(work.HOP)), "")), ["View missing certification"], hold.reason),
			regions=[pay], p="", s2=[], ev=["Certification 1", "Accounting invoice", f"Payment Entry {payment_entry}"])
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


def _view(board: dict, label: str, title: str, rows: list[list[str]]) -> None:
	"""A read-only look at a linked record, drawn over the screen (the linked views keep the case header, section 10.7); it changes nothing."""
	key = label.lower().replace(" ", "-")
	board["actions"][label] = kit.dialog(key)
	board["dialogs"][key] = kit.dlg(title, [kit.r(*rows)], "", ["Close"], local=True)


def _certification_rows(ctx: Context, invoice) -> list[list[str]]:
	cert = frappe.db.get_value("Contract Certification", {"contract_case": ctx.case, "invoice": invoice.name, "state": "Signed"}, ["certified_amount", "certified_at", "certifier"], as_dict=True)
	if not cert:
		return [["Certification", "Not signed"]]
	return [["Certified", money(cert.certified_amount, ctx.currency)], ["Signed by", ctx.name(cert.certifier)], ["Signed", when(cert.certified_at)]]


def _settlement_rows(ctx: Context, invoice) -> list[dict]:
	return frappe.get_all("Contract Settlement", filters={"invoice": invoice.name}, fields=["name", "native_payment", "amount", "state", "effective_date", "evidence_json", "reversed_at", "corrects"], order_by="creation asc")


def d28(ctx: Context, invoice) -> dict:
	"""An invoice paid in instalments (D28): what procurement certified, the cash that is confirmed, the noncash adjustments and what is still outstanding, each settlement kept as its own row. D28-C once the
	last instalment is confirmed; D28-V when one was reversed (the original confirmation and the reversal stay side by side)."""
	pos = payment.invoice_position(ctx.case, invoice.name)
	rows = _settlement_rows(ctx, invoice)
	reversed_ = any(r["state"] == "Reversed" for r in rows)
	ident = "D28-V" if reversed_ and pos["outstanding"] > 0 else "D28-C" if invoice.state == "Paid" else "D28"
	facts = [["Certified", money(pos["certified"], ctx.currency)], ["Cash confirmed", money(pos["cash_confirmed"], ctx.currency)], ["Noncash adjustment", money(pos["noncash"], ctx.currency)], ["Outstanding", money(pos["outstanding"], ctx.currency)]]
	if ident != "D28-C":
		facts.append(["Invoice", invoice.state])
	table = [[r["native_payment"], money(r["amount"], ctx.currency), f"!{r['state']}", f"Reversed {when(r['reversed_at'])}" if r["state"] == "Reversed" else formatdate(r["effective_date"], "d MMM yyyy"),
		(records.loads(r["evidence_json"] or "{}").get("evidence") or "—")] for r in rows]
	settlements = kit.R("Settlements", kit.t(["Payment entry", "Amount", "Status", "Date", "Bank reference"], table, [1]), *([kit.lk("Original settlement", "Reversal")] if ident == "D28-V" else []))
	b = chrome.base(ctx, ident, d="D28", name="Partly paid invoice", title="Invoice and payment", tab="Invoices", next=chrome.next_block(ctx), regions=[kit.R("", kit.r(*facts)), settlements],
		s2=["View certification", "View settlement"], ev=["Certification 1", rows[0]["native_payment"] if rows else ""])
	_view(b, "View certification", "Certification", _certification_rows(ctx, invoice))
	_view(b, "View settlement", "Settlements", [[r["native_payment"], f"{money(r['amount'], ctx.currency)} · {r['state']}"] for r in rows] or [["Settlement", "None yet"]])
	return b


def _advance_clause_region(ctx: Context, row) -> dict:
	found = records.loads(row.clause_json)
	return kit.R("Advance clause", kit.r(["Allowed", f"{found['percent']:g}% of {money(ctx.terms.get('total'), ctx.currency)} = {money(found['amount'], ctx.currency)}"], ["Payable", "After effective signature"], ["Recovery", advance.recovery_text(found)]))


def _guarantee_region(ctx: Context, case: str, amount: float) -> dict:
	g = advance.guarantee(case)
	ok = advance.verified_guarantee(case, amount)
	if not g:
		return kit.R("Advance guarantee", kit.r(["Guarantee", "—"], ["Status", "Not recorded"]))
	return kit.R("Advance guarantee", kit.r(["Guarantee", g.reference], ["Beneficiary", g.beneficiary], ["Amount", money(g.amount, ctx.currency)], ["Issuer", g.issuer], ["Valid through", formatdate(g.expires_on, "d MMM yyyy")],
		["Issuer confirmation", g.confirmation_reference or "—"], ["Status", "Verified" if ok else "Not verified"]))


def d29(ctx: Context, row) -> dict:
	"""Advance support (D29): procurement reviews the issued clause, the guarantee and the claim before signing. D29-H while the guarantee is not verified: nothing but the way to see it."""
	held = advance.verified_guarantee(ctx.case, row.amount) is None
	regions = [_advance_clause_region(ctx, row), _guarantee_region(ctx, ctx.case, row.amount)] + ([] if held else [kit.R("Claim", kit.f(["Claim", row.claim_reference], ["Amount", money(row.amount, ctx.currency)]))])
	custodian = ctx.name(next(iter(work.holders("Finance preparation")), ""))
	b = chrome.base(ctx, "D29-H" if held else "D29", d="D29", name="Advance support", title="Review advance request", tab="Invoices",
		next=kit.blk("The advance guarantee has not been verified.", custodian, ["View guarantee", "View issue"]) if held else chrome.next_block(ctx), regions=regions, ev=["Advance clause", "Guarantee"],
		p="" if held else "Sign advance certification", s2=["View guarantee", "View issue"][:1] if held else ["View advance clause", "View guarantee"])
	if not held:
		b["actions"]["Sign advance certification"] = kit.command("SignAdvanceCertification", advance=row.name)
	found = records.loads(row.clause_json)
	_view(b, "View advance clause", "Advance clause", [["Allowed", f"{found['percent']:g}% of {money(ctx.terms.get('total'), ctx.currency)}"], ["Payable", "After effective signature"], ["Recovery", advance.recovery_text(found)]])
	g = advance.guarantee(ctx.case)
	_view(b, "View guarantee", "Advance guarantee", [["Guarantee", g.reference if g else "Not recorded"], ["Status", g.state if g else "Not recorded"]])
	b["actions"]["View issue"] = kit.tab("Obligations")
	return b


def d29r(ctx: Context, invoice, plan: dict) -> dict:
	"""Recovery on an invoice (D29-R): procurement signs the certification knowing how much of the advance it recovers, what cash remains and what is left to recover."""
	line = _line(ctx, records.loads(invoice.lines_json)[0]["line_id"])
	table = kit.t(["Invoice", "Gross", "Advance recovery", "Proposed cash", "Advance remaining"], [[f"Accepted goods — {plan['units']} {_item(ctx, line.get('line_id')).lower()}", money(invoice.claimed_amount, ctx.currency),
		money(plan["recovery"], ctx.currency), money(plan["cash"], ctx.currency), money(plan["remaining"], ctx.currency)]], [1, 2, 3, 4])
	rows = kit.r(["Prior cash advance", money(plan["paid"], ctx.currency)], ["Later invoices", f"{money(plan['remaining'], ctx.currency)} of the advance is still to be recovered"])
	b = chrome.base(ctx, "D29-R", d="D29", name="Advance support", title="Review invoice", tab="Invoices", next=chrome.next_block(ctx), regions=[kit.R("Recovery", table, rows)], p="Sign certification", s2=["View advance clause"],
		ev=[f"Supplier invoice {invoice.claim_reference}", "Advance clause"])
	b["actions"]["Sign certification"] = kit.command("SignContractCertification", invoice=invoice.name)
	row = advance.live(ctx.case)
	found = records.loads(row.clause_json)
	_view(b, "View advance clause", "Advance clause", [["Allowed", f"{found['percent']:g}% of {money(ctx.terms.get('total'), ctx.currency)}"], ["Recovery", advance.recovery_text(found)]])
	return b


def d08l(ctx: Context, invoice, gap: dict) -> dict:
	"""A corrected claim after Finance posted the original liability (D08-L): the claims side by side, the liability, the credit still needed and that no payable is established. No second liability."""
	original = frappe.get_doc("Contract Invoice", gap["original"])
	claims = kit.t(["Claim", "Received", "Quantity", "Amount"], [["Original claim", when(original.received_at), str(sum(cint(l["quantity"]) for l in records.loads(original.lines_json))), money(original.claimed_amount, ctx.currency)],
		["Corrected claim", when(invoice.received_at), str(sum(cint(l["quantity"]) for l in records.loads(invoice.lines_json))), money(invoice.claimed_amount, ctx.currency)]], [2, 3])
	position_ = kit.r(["Native liability posted", money(gap["liability"], ctx.currency)], ["Required credit", money(gap["required"], ctx.currency)], ["Reconciled payable", "Established" if gap["reconciled"] else "Not established"],
		["Supported amount", money(gap["supported"], ctx.currency)])
	owner = ctx.name(next(iter(work.holders("Finance preparation")), ""))
	b = chrome.base(ctx, "D08-L", d="D08", name="Corrected claim after early liability", title="Review corrected invoice", tab="Invoices",
		next=kit.blk("Finance must reconcile the original liability.", owner, ["View correction", "View accounting invoice"]), regions=[kit.R("Claims", claims), kit.R("Accounting position", position_)], p="", s2=[],
		ev=[f"Supplier invoice {original.claim_reference}", f"Supplier invoice {invoice.claim_reference} version 2", "Accounting invoice"])
	_view(b, "View correction", "Correction", [["Original claim", f"{original.claim_reference} · {money(original.claimed_amount, ctx.currency)}"], ["Corrected claim", f"{invoice.claim_reference} · {money(invoice.claimed_amount, ctx.currency)}"]])
	_view(b, "View accounting invoice", "Accounting invoice", [["Native invoice", gap["native"]], ["Liability posted", money(gap["liability"], ctx.currency)], ["Credit received", money(gap["credited"], ctx.currency)]])
	return b


def d09(ctx: Context, invoice=None) -> dict:
	"""Invoice and payment: the read-only follow-up of the latest claim (the contract owner's and every reader's view of the Invoices tab)."""
	focus = invoice or next((i for i in reversed(ctx.invoices) if i.state not in ("Superseded", "Set aside")), ctx.invoices[-1] if ctx.invoices else None)
	if focus is not None and (len(_settlement_rows(ctx, focus)) > 1 or focus.state == "Partly paid" or any(r["state"] == "Reversed" for r in _settlement_rows(ctx, focus))):
		return d28(ctx, focus)
	rows = []
	for inv in ctx.invoices:
		pays = [p for p in payment.payments(ctx.case) if p["invoice"] == inv.name]
		posted = [p for p in pays if p["docstatus"] == 1]
		settled = payment.settled_amount(inv.name)
		rows.append([inv.claim_reference, money(inv.claimed_amount, ctx.currency), f"!{inv.state}" if inv.state in ("Paid", "Certified") else inv.state, inv.accounting_state if inv.native_invoice else "—", money(sum(flt(p["paid_amount"]) for p in posted), ctx.currency) + " recorded" if posted else "—",
			"Confirmed" if settled else "Not confirmed"])
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
	supplier = ctx.doc.lifecycle == "Active" and "supplier" in ctx.audiences
	if supplier and any(v > 0 for v in eligible_unclaimed(ctx).values()):
		b["p"] = "Submit invoice"
		b["actions"]["Submit invoice"] = kit.route(ctx.case, "invoices", "submit-invoice")
	found = advance.clause(ctx.terms)
	if supplier and found and not advance.live(ctx.case):  # the supplier claims the advance the issued terms provide (authored: the artboards show only the review)
		b["s2"] = [*b.get("s2", []), "Claim advance"]
		b["actions"]["Claim advance"] = kit.dialog("advance")
		b["dialogs"]["advance"] = kit.dlg("Claim advance", [kit.xh(f"The issued terms provide an advance of {money(found['amount'], ctx.currency)}, paid after the agreement is effective and recovered on later invoices."),
			kit.fl(kit.tx("Advance claim number", "", "claim_reference"), kit.tx("Amount", f"{found['amount']:.2f}", "amount"))], "Claim advance", command="PrepareContractAdvance", args={})
	return b


def guarantee_record(ctx: Context) -> dict:
	"""Record the advance guarantee (the Finance advance custodian): the instrument the supplier supplied, to be verified from the issuer's confirmation (authored; the artboards show the verified guarantee)."""
	row = advance.live(ctx.case)
	entity = ((ctx.terms.get("parties") or {}).get("entity") or {}).get("name", "")
	fields = [kit.tx("Issuer", "", "issuer"), kit.tx("Beneficiary", entity, "beneficiary"), kit.tx("Reference", "", "reference"), kit.tx("Amount", f"{flt(row.amount):.2f}" if row else "", "amount"), kit.dt("Issued", "", "issued_on"),
		kit.dt("Expires", "", "expires_on"), kit.file("Attachment", "", "attachment")]
	b = chrome.base(ctx, "D29-G", d="D29", name="Advance guarantee", title="Record advance guarantee", tab="Invoices", next=chrome.next_block(ctx),
		regions=[kit.R("Advance requirement", kit.f(["Advance claimed", money(row.amount, ctx.currency) if row else "—"])), kit.R("Instrument", kit.fl(*fields))], p="Save guarantee", s2=["Cancel"], ev=[])
	b["actions"]["Save guarantee"] = kit.command("RecordContractSecurity", kind="Advance guarantee")
	b["actions"]["Cancel"] = kit.tab("Invoices")
	return b


def guarantee_verify(ctx: Context, number: int) -> dict:
	"""Verify the recorded advance guarantee from the issuer's confirmation (procurement; authored)."""
	g = frappe.get_doc("Contract Security", frappe.db.get_value("Contract Security", {"contract_case": ctx.case, "version_no": number}, "name"))
	instrument = kit.r(["Issuer", g.issuer], ["Beneficiary", g.beneficiary], ["Reference", g.reference], ["Amount", money(g.amount, ctx.currency)], ["Expires", formatdate(g.expires_on, "d MMM yyyy")])
	b = chrome.base(ctx, "D29-V", d="D29", name="Advance guarantee", title="Verify advance guarantee", tab="Invoices", next=chrome.next_block(ctx), regions=[kit.R("Instrument", instrument),
		kit.R("Issuer confirmation", kit.r(["Source verification status", "Awaiting the issuer's confirmation"], ["Recorded by", f"{ctx.name(g.recorded_by)}, {when(g.recorded_at)}"]))], p="Verify guarantee", ev=[f"Guarantee {g.reference}"])
	b["actions"]["Verify guarantee"] = kit.dialog("verify")
	b["dialogs"]["verify"] = kit.dlg("Verify guarantee", [kit.r(["Instrument", g.reference], ["Issuer", g.issuer], ["Amount", money(g.amount, ctx.currency)]),
		kit.fl(kit.tx("Issuer's confirmation reference", "", "confirmation_reference"), kit.dt("Confirmation received", "", "received_on"), kit.ta("Basis", "", "basis"))], "Verify",
		command="VerifyContractSecurity", args={"security": g.name, "kind": "Advance guarantee"})
	return b
