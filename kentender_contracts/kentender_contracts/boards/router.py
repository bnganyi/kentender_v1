# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Which screen a person sees on a contract (CM-CHG-001 v0.8 sections 6.3, 9.0, 10.3).

The contract page has five tabs. The screen under a tab is the **board of the viewer's own leading obligation** when that obligation belongs to the tab, and otherwise the tab's read-only summary
with the same next step above it. The page opens on the tab of the leading obligation. A route can also name a subject (`agreement/1`, `deliveries/record-delivery`, `invoices/submit-invoice`).
The server decides; a viewer who may not read the contract gets the stable denial, never a hint of what exists (section 6.2)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_contracts.boards import agreement, chrome, delivery, invoices, kit, obligations
from kentender_contracts.boards.context import Context
from kentender_contracts.services import bindings, closeout, payment, records
from kentender_contracts.services.errors import fail

TAB_KEYS = {t.lower(): t for t in chrome.TABS}


def _number(subject: str) -> int:
	return int(subject.split()[-1])


def _by_subject(ctx: Context, lead: dict[str, Any]):
	command, subject = lead["command"], lead["subject"]
	is_entity = bool(ctx.agreement and bindings.entity_signatory(ctx.case, ctx.user))
	if ":waiting:" in command:
		return None
	if command == "RequestContractSignatures":
		return agreement.d02(ctx)
	if command == "SignContractVersion":
		return agreement.d03(ctx, entity=is_entity)
	if command == "RecommendContractInspectors":
		return agreement.d23r(ctx)
	if command == "AppointContractInspectors":
		return agreement.d23(ctx)
	if command == "DeclareContractInterest":
		return agreement.d24(ctx)
	if command == "RecordInspectionObservations":
		return delivery.d05(ctx, _number(subject))
	if command == "SignTechnicalCertificate":
		return delivery.d19(ctx, _number(subject))
	if command == "PrepareAcceptanceReport":
		return delivery.d06(ctx, _number(subject))
	if command == "SignAcceptanceReport":
		return delivery.d07(ctx, lead["version"])
	if command == "SignContractCertification":
		return invoices.d08c(ctx, invoices._invoice(ctx, _number(subject)))
	if command == "RequestInvoiceCorrection":
		return invoices.d08(ctx, invoices._invoice(ctx, _number(subject)))
	if command == "CorrectContractInvoice":
		return invoices.d18c(ctx, invoices._invoice(ctx, _number(subject)))
	if command == "SaveNativeFinanceDraft":
		inv = invoices._invoice(ctx, _number(subject))
		return invoices.d33(ctx, inv, mode="maker") if subject.startswith("accounting invoice") else invoices.d09f(ctx, inv)
	if command == "SubmitNativeFinanceForApproval":
		return invoices.d09f(ctx, _payment_invoice(ctx, subject))
	if command == "ApproveNativeFinanceRecord":
		if subject.startswith("accounting invoice"):
			return invoices.d33(ctx, invoices._invoice(ctx, _number(subject)), mode="approver")
		return invoices.d17(ctx, _payment_invoice(ctx, subject), subject.split()[-1])
	if command == "RecordFinanceSettlement":
		return invoices.d17(ctx, _payment_invoice(ctx, subject), subject.split()[-1], settle=True)
	if command == "IssueCompletionCertificate":
		return obligations.d22(ctx)
	if command == "SignContractCloseout":
		return obligations.d11(ctx, frappe.db.get_value("Contract Closeout", {"contract_case": ctx.case, "state": "Awaiting signature"}, "name"))
	if command == "RestoreContractOperation":
		return obligations.operations(ctx)
	return None


def _by_waiting(ctx: Context, lead: dict[str, Any]):
	"""The screen for something the viewer is waiting on, where the design draws one (the declarations a recommender waits for)."""
	command, subject = lead["command"], lead["subject"]
	if command.startswith("DeclareContractInterest:waiting"):
		return agreement.d23p(ctx)
	if command.startswith("RequestInvoiceCorrection:waiting"):
		return invoices.d18r(ctx, invoices._invoice(ctx, _number(subject)))
	if command.startswith("ApproveNativeFinanceRecord:waiting:accounting"):
		return invoices.d33(ctx, invoices._invoice(ctx, _number(subject)), mode="waiting")
	if command.startswith("ApproveNativeFinanceRecord:waiting:payment"):
		return invoices.d09f(ctx, _payment_invoice(ctx, subject), waiting=True)
	return None


def _payment_invoice(ctx: Context, subject: str):
	entry = subject.split()[-1]
	for p in payment.payments(ctx.case):
		if p["name"] == entry:
			return frappe.get_doc("Contract Invoice", p["invoice"])
	# a payment subject names its invoice before the draft exists ("payment invoice N")
	return invoices._invoice(ctx, _number(subject))


def summary(ctx: Context, tab: str) -> dict[str, Any]:
	if tab == "Agreement":
		return _agreement_summary(ctx)
	if tab == "Deliveries":
		return delivery.deliveries_summary(ctx)
	if tab == "Invoices":
		return invoices.d09(ctx)
	if tab == "Obligations":
		return obligations.obligations(ctx)
	return obligations.history(ctx)


def _agreement_summary(ctx: Context) -> dict[str, Any]:
	hidden = bool(ctx.agreement and ctx.agreement.state == "Draft" and not ctx.sees("terms"))  # a draft is the preparers' until it is sent
	if hidden:
		board = chrome.base(ctx, "D02-S", d="D02", name="Agreement", title="Agreement", tab="Agreement", next=chrome.next_block(ctx), regions=[kit.R("Agreement", kit.xh("The agreement has not been sent for signature yet."))])
		return board
	if ctx.agreement and ctx.agreement.state in ("Awaiting signatures", "Effective"):
		board = agreement.d03(ctx, entity=False, waiting=True)
		board["id"], board["p"] = "D03-S", ""
	elif ctx.agreement:
		board = agreement.d02(ctx)
		board["p"], board["s2"], board["actions"] = "", [], {k: v for k, v in board["actions"].items() if k.startswith("View")}
	else:
		board = chrome.base(ctx, "D02-S", d="D02", name="Agreement", title="Agreement", tab="Agreement", next=chrome.next_block(ctx), regions=[kit.R("Agreement", kit.xh("The agreement has not been prepared yet."))])
	appointed = ctx.appointment
	if appointed["appointment"]:
		board["regions"].append(kit.R("Inspectors", agreement._members_table(appointed["members"])))
	return board


def board_for(case: str, user: str, *, tab: str | None = None, subject: tuple[str, ...] = ()) -> dict[str, Any]:
	"""The screen for this viewer: a record page with its tab, next step, regions and actions. Denial is `CM_AUTHORITY` with `denied`, drawn by the client as the shared denied page."""
	if not case or not frappe.db.exists("Contract Case", case):
		fail("CM_AUTHORITY", denied=True, reason="You do not have access to this contract.")
	ctx = Context(case, user)
	if not ctx.grants:
		fail("CM_AUTHORITY", denied=True, reason="You do not have access to this contract.")
	lead = ctx.lead
	selected = TAB_KEYS.get((tab or "").lower()) or (chrome.tab_of(lead["command"]) if lead else "Agreement")
	board = None
	if subject:
		board = _subject_board(ctx, selected, subject)
	own = bool(lead) and lead["holder"].lower() == user.lower() and lead["state"] in ("actionable", "blocked")  # someone else's leading item is only a "waiting on" line, never a screen to act on
	if board is None and own and chrome.tab_of(lead["command"]) == selected:
		board = _by_subject(ctx, lead)
	if board is None and not own:
		for item in sorted((t for t in ctx.tasks if t["holder"].lower() == user.lower() and t["state"] == "waiting" and chrome.tab_of(t["command"]) == selected), key=lambda t: t["assigned_at"]):
			board = _by_waiting(ctx, item)
			if board:
				break
	if board is None and not own and selected == "Agreement" and ctx.doc.lifecycle == "Preparing" and ctx.can_prepare:
		board = agreement.d02(ctx)  # an authorised preparer prepares the agreement whether or not the head of procurement's task is theirs (section 5.3)
	if board is None:
		board = summary(ctx, selected)
	board["tab"] = selected
	board["tabs"] = [{"label": t, "route": [case, t.lower()]} for t in chrome.TABS]
	board["audiences"] = ctx.audiences
	return board


def _subject_board(ctx: Context, tab: str, subject: tuple[str, ...]) -> dict[str, Any] | None:
	if subject[0] == "agreement" and len(subject) > 1 and "terms" in _sets(ctx):
		return agreement.d02v(ctx, int(subject[1]))
	if subject == ("record-delivery",) and "receiver" in ctx.audiences:
		return delivery.d04(ctx)
	if subject == ("submit-invoice",) and "supplier" in ctx.audiences:
		return invoices.d18(ctx)
	return None


def _sets(ctx: Context) -> set[str]:
	from kentender_contracts.services import audience

	return set(audience.field_sets(ctx.grants))
