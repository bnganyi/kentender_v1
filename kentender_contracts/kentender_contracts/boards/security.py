# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The performance security boards (CM-CHG-001 v0.8 sections 5.3, 5.10, 19.3; boards D25, D25-R, D25-J).

HOP records the instrument the supplier supplied (D25-R), checks the issuer's confirmation and verifies or rejects it (D25). The supplier sees only its own side: the instrument that was rejected, why, and that a
replacement is awaited (D25-J). What the issued terms require, and so what "enough" means, is read from the terms, never from a constant here."""

from __future__ import annotations

import frappe
from frappe.utils import formatdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import security as service


def _date(value) -> str:
	return formatdate(value, "d MMM yyyy") if value else ""


def _requirement(ctx: Context, supplied: float | None = None):
	need = service.requirement(ctx.terms) or {"amount": 0, "statement": ""}
	rows = [["Contract sum", money(ctx.terms.get("total"), ctx.currency)], ["Required under the issued terms", money(need["amount"], ctx.currency)]]
	if supplied is not None:
		rows.append(["Amount supplied", money(supplied, ctx.currency)])
	return kit.R("Security requirement", kit.f(*rows))


def _row(ctx: Context, number: int):
	name = frappe.db.get_value(service.SECURITY, {"contract_case": ctx.case, "version_no": number}, "name")
	return frappe.get_doc(service.SECURITY, name) if name else None


def d25r(ctx: Context, number: int, *, replacing: bool = False) -> dict:
	"""Record the instrument (HOP). The entity's name is offered as the beneficiary because the issued terms name the entity as the party the security protects."""
	entity = ((ctx.terms.get("parties") or {}).get("entity") or {}).get("name", "")
	fields = [kit.tx("Issuer", "", "issuer"), kit.tx("Beneficiary", entity, "beneficiary"), kit.tx("Reference", "", "reference"), kit.tx("Amount", "", "amount"), kit.dt("Issued", "", "issued_on"),
		kit.dt("Expires", "", "expires_on"), kit.file("Attachment", "", "attachment")]
	board = chrome.base(ctx, "D25-R", d="D25", name="Verify security", title="Record replacement security" if replacing else "Record performance security", tab="Obligations" if replacing else "Agreement",
		next=chrome.form_turn(ctx, "RecordContractSecurity", "Record the replacement instrument.") if replacing else chrome.next_block(ctx), regions=[_requirement(ctx), kit.R("Instrument", kit.fl(*fields))], p="Save security", s2=["Cancel"], ev=[])
	board["actions"]["Save security"] = kit.command("RecordContractSecurity")
	board["actions"]["Cancel"] = kit.tab("Obligations" if replacing else "Agreement")
	return board


def d25(ctx: Context, number: int) -> dict:
	"""Verify or reject a recorded instrument (HOP): the instrument, the requirement it is checked against and the issuer's confirmation, which HOP enters in the verify dialog."""
	row = _row(ctx, number)
	instrument = kit.r(["Issuer", row.issuer], ["Beneficiary", row.beneficiary], ["Reference", row.reference], ["Issued", _date(row.issued_on)], ["Expires", _date(row.expires_on)])
	confirmation = kit.r(["Source verification status", "Awaiting the issuer's confirmation"], ["Recorded by", f"{ctx.name(row.recorded_by)}, {when(row.recorded_at)}"])
	board = chrome.base(ctx, "D25", d="D25", name="Verify security", title="Verify performance security", tab="Agreement", next=chrome.next_block(ctx), regions=[_requirement(ctx, row.amount), kit.R("Instrument", instrument),
		kit.R("Issuer confirmation", confirmation)], p="Verify security", s2=["Reject security"], ev=[f"Guarantee {row.reference}"])
	board["actions"]["Verify security"] = kit.dialog("verify")
	board["actions"]["Reject security"] = kit.dialog("reject")
	board["dialogs"]["verify"] = kit.dlg("Verify security", [kit.r(["Instrument", row.reference], ["Issuer", row.issuer], ["Amount", money(row.amount, ctx.currency)]),
		kit.fl(kit.tx("Issuer's confirmation reference", "", "confirmation_reference"), kit.dt("Confirmation received", "", "received_on"), kit.ta("Basis", "", "basis"))], "Verify",
		command="VerifyContractSecurity", args={"security": row.name})
	board["dialogs"]["reject"] = kit.dlg("Reject security", [kit.fl(kit.ta("Reason", "", "reason"))], "Reject", command="RejectContractSecurity", args={"security": row.name})
	return board


def d25j(ctx: Context) -> dict:
	"""What the supplier sees after a rejection: the rejected instrument, the reason and that a replacement is awaited."""
	rows = frappe.get_all(service.SECURITY, filters={"contract_case": ctx.case, "state": "Rejected"}, fields=["reference", "rejection_reason"], order_by="version_no desc", limit=1)
	last = rows[0] if rows else {"reference": "", "rejection_reason": ""}
	board = chrome.base(ctx, "D25-J", d="D25", name="Verify security", title="Performance security", tab="Agreement", next=chrome.next_block(ctx),
		regions=[kit.R("Rejected instrument", kit.r(["Reference", last["reference"]], ["Reason", last["rejection_reason"]], ["History", "Rejected instrument retained"]))],
		p="", s2=["View contract"], ev=[f"Guarantee {last['reference']}"])
	board["actions"]["View contract"] = kit.tab("Agreement")
	return board
