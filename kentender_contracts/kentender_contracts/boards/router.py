# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Which screen a person sees on a contract (CM-CHG-001 v0.8 sections 6.3, 9.0, 10.3).

The contract page has five tabs. The screen under a tab is the **board of the viewer's own leading obligation** when that obligation belongs to the tab, and otherwise the tab's read-only summary
with the same next step above it. The page opens on the tab of the leading obligation. A route can also name a subject (`agreement/1`, `deliveries/record-delivery`, `invoices/submit-invoice`).
The server decides; a viewer who may not read the contract gets the stable denial, never a hint of what exists (section 6.2)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_contracts.boards import adjustments, agreement, changes, chrome, completion, delivery, ending, existing, invoices, issues as issue_boards, funding_board, kit, obligations, outside, reports, security, security_actions as security_boards, termination as termination_boards
from kentender_contracts.boards.context import Context
from kentender_contracts.services import adjustment, advance, bindings, change, closeout, closure_correction, issues, obligations as obligation_service, payment, records, reporting, security_actions, termination, warranty
from kentender_contracts.services.errors import fail

TAB_KEYS = {t.lower(): t for t in chrome.TABS}


def _arrival_items(ctx: Context, number: int) -> list[dict]:
	return records.loads(frappe.db.get_value("Contract Arrival", {"contract_case": ctx.case, "arrival_no": number}, "items_json") or "[]", [])


def _report(ctx: Context, version: int):
	return frappe.get_doc("Contract Acceptance", frappe.db.get_value("Contract Acceptance", {"contract_case": ctx.case, "version_no": version}, "name"))


def _number(subject: str) -> int:
	return int(subject.split()[-1])


def _by_subject(ctx: Context, lead: dict[str, Any]):
	command, subject = lead["command"], lead["subject"]
	is_entity = bool(ctx.agreement and bindings.entity_signatory(ctx.case, ctx.user))
	if ":waiting:" in command:
		return None
	if command == "RequestContractSignatures":
		board = agreement.d02(ctx)
		_offer_ending(ctx, board)
		return board
	if command == "SignContractVersion":
		if subject.startswith("amendment"):
			return changes.sign(ctx, _change_of(ctx, subject), entity=bool(bindings.entity_signatory(ctx.case, ctx.user)))
		return agreement.d03(ctx, entity=is_entity)
	if command in change.COMMANDS:
		return _change_board(ctx, lead)
	if command == "ResolveDeliveryException":
		board = delivery.deliveries_summary(ctx)
		board["next"] = chrome.next_block(ctx)
		delivery.resolve_dialog(board, frappe.db.get_value("Contract Arrival", {"contract_case": ctx.case, "arrival_no": _number(subject)}, "name"))
		return board
	if command == "ReviseContractIntake":
		return existing.d12(ctx, ctx.user, ctx.case)
	if command == "ConfirmOpeningPosition":
		return existing.d21(ctx)
	if command == "StartContractManagement":
		return existing.d21h(ctx)
	if command in ("RequestExistingContractFunding", "ConfirmContractFundingEvidence"):
		return funding_board.d21f(ctx)
	if command == "ReviewAwardRestriction":
		board = _agreement_summary(ctx)
		board["next"] = chrome.next_block(ctx)
		ending.restriction(board, subject.split(" ", 1)[1])
		return board
	if command == "RecordContractNotProceeding":
		board = _agreement_summary(ctx)
		board["next"] = chrome.next_block(ctx)
		ending.attach(board, primary=True)
		return board
	if command == "RecordOutsideContractSignature":
		return outside.d26(ctx, "Entity" if " entity " in subject else "Supplier", differs=bool(outside.mismatched(ctx)))
	if command == "ConfirmOutsideSignatureEvidence":
		return outside.d26(ctx, outside.mismatched(ctx)[0], differs=True) if outside.mismatched(ctx) else outside.d26e(ctx)
	if command == "RecordContractSecurity":
		return invoices.guarantee_record(ctx) if subject.startswith("advance guarantee") else security.d25r(ctx, lead["version"])
	if command in _ISSUE_COMMANDS:
		return _issue_board(ctx, lead)
	if command in _OBLIGATION_COMMANDS:
		return _obligation_board(ctx, lead)
	if command == "VerifyContractSecurity":
		if subject.startswith("advance guarantee"):
			return invoices.guarantee_verify(ctx, lead["version"])
		return security_boards.replacement(ctx, lead["version"]) if ctx.doc.lifecycle in ("Active", "Terminated") else security.d25(ctx, lead["version"])
	if command == "SignAdvanceCertification":
		return invoices.d29(ctx, advance.live(ctx.case))
	if command == "RecommendContractInspectors":
		if subject.startswith("replacement for "):
			return agreement.d24x(ctx, subject.split("replacement for ", 1)[1])
		return agreement.d23r(ctx)
	if command == "AppointContractInspectors":
		return agreement.d23(ctx)
	if command == "DeclareContractInterest":
		return agreement.d24(ctx)
	if command == "RecordInspectionObservations":
		if ctx.mine("SignTechnicalCertificate", f"inspection {_number(subject)}"):
			return delivery.d19(ctx, _number(subject))  # the units that have a reading are confirmed first; the rest wait for theirs
		return delivery.d31(ctx, _number(subject)) if delivery.is_service(ctx, _arrival_items(ctx, _number(subject))) else delivery.d05(ctx, _number(subject))
	if command == "SignTechnicalCertificate":
		return delivery.d19(ctx, _number(subject))
	if command == "PrepareAcceptanceReport":
		return delivery.d06(ctx, _number(subject))
	if command == "SignAcceptanceReport":
		return delivery.d31a(ctx, lead["version"]) if delivery.report_is_service(ctx, _report(ctx, lead["version"])) else delivery.d07(ctx, lead["version"])
	if command == "DecideContractAcceptance":
		return delivery.d07a(ctx, lead["version"])
	if command == "SignContractCertification":
		inv = invoices._invoice(ctx, _number(subject))
		approved = adjustment.pending_application(ctx.case)
		if approved:
			return adjustments.certification(ctx, inv, flt(frappe.db.get_value("Contract Invoice", inv.name, "claimed_amount")), approved[0])
		gap = next((g for g in payment.liability_gap(ctx.case) if g["successor"] == inv.name and not g["reconciled"]), None)
		if gap:
			return invoices.d08l(ctx, inv, gap)
		plan = advance.recovery_plan(ctx.case, inv)
		return invoices.d29r(ctx, inv, plan) if plan and plan["recovery"] > 0 else invoices.d08c(ctx, inv)
	if command == "RequestInvoiceCorrection":
		return invoices.d08(ctx, invoices._invoice(ctx, _number(subject)))
	if command == "ResolveInvoiceDuplicate":
		return invoices.d08d(ctx, invoices._invoice(ctx, _number(subject)))
	if command == "CorrectContractInvoice":
		return invoices.d18c(ctx, invoices._invoice(ctx, _number(subject)))
	if command == "SaveNativeFinanceDraft":
		if lead.get("state") == "blocked" and "adjustment mapping" in ((lead.get("blocker") or {}).get("holds") or []):
			return adjustments.held(ctx)
		if subject.startswith("payment advance"):
			return invoices.d09f(ctx, _payment_invoice(ctx, subject))
		inv = invoices._invoice(ctx, _number(subject))
		return invoices.d33(ctx, inv, mode="maker") if subject.startswith("accounting invoice") else invoices.d09f(ctx, inv)
	if command == "SubmitNativeFinanceForApproval":
		return invoices.d09f(ctx, _payment_invoice(ctx, subject))
	if command == "ApproveNativeFinanceRecord":
		if subject.startswith("credit invoice"):
			return _credit_board(ctx, subject)
		if subject.startswith("accounting invoice"):
			return invoices.d33(ctx, invoices._invoice(ctx, _number(subject)), mode="approver")
		return invoices.d17(ctx, _payment_invoice(ctx, subject), subject.split()[-1])
	if command == "RecordFinanceSettlement":
		return invoices.d17(ctx, _payment_invoice(ctx, subject), subject.split()[-1], settle=True)
	if command == "ReconcileInvoiceLiability":
		gap = next((g for g in payment.liability_gap(ctx.case) if f"invoice {g['successor_no']}" == subject), None)
		return invoices.liability(ctx, gap) if gap else None
	if command == "IssueCompletionCertificate":
		return obligations.d22(ctx)
	if command == "SignFinalContractAcceptance":
		return completion.acceptance(ctx)
	if command == "ConfirmCertificateDelivery":
		return _delivery_board(ctx, lead)
	if command == "ConfirmContractClosure":
		return completion.correction_decision(ctx, closure_correction.get(ctx.case, _number(subject)))
	if command == "PrepareContractClosureCorrection":
		return completion.correction_request(ctx, correcting=closure_correction.get(ctx.case, _number(subject)))
	if command == "SignContractCloseout":
		if lead.get("state") == "blocked" and warranty.open_claims(ctx.case):
			return completion.blocked_closeout(ctx)
		return obligations.d11(ctx, frappe.db.get_value("Contract Closeout", {"contract_case": ctx.case, "state": "Awaiting signature"}, "name"))
	if command == "RestoreContractOperation":
		return obligations.operations(ctx)
	return None


_ISSUE_COMMANDS = ("SendContractCorrespondence", "ReplyContractCorrespondence", "ResolveContractIssue", "RecordWarrantyReturn", "ReconcileWarrantyReturn", "VerifyContractRemedy")
_OBLIGATION_COMMANDS = ("PrepareContractAdjustment", "DecideContractAdjustment", "RequestSecurityClaim", "DecideSecurityClaim", "RecordSecurityClaimCommunication", "RecordSecurityAction", "RequestContractTermination",
	"DecideContractTermination", "RecordTerminationNotice", "RecordTerminationEffect", "PrepareTerminationSettlement", "CompleteTerminationSettlement", "SubmitContractReport", "ResolvePublicationRequirement", "RecordContractAwardPublication")


def _issue_board(ctx: Context, lead: dict[str, Any]):
	command, subject = lead["command"], lead["subject"]
	row = issues.get(ctx.case, _number(subject))
	if row is None:
		return None
	if command == "SendContractCorrespondence":
		return issue_boards.notice(ctx, row) if row.kind == "Warranty claim" else issue_boards.send(ctx, row)
	if command == "ReplyContractCorrespondence":
		return issue_boards.reply(ctx, row)
	if command == "ResolveContractIssue":
		return issue_boards.resolve(ctx, row)
	if command == "RecordWarrantyReturn":
		return issue_boards.arrange(ctx, row)
	if command == "ReconcileWarrantyReturn":
		return issue_boards.reconcile(ctx, row)
	return issue_boards.verify(ctx, row)


def _obligation_board(ctx: Context, lead: dict[str, Any]):
	command, subject = lead["command"], lead["subject"]
	if command == "PrepareContractAdjustment":
		return adjustments.propose(ctx)
	if command == "DecideContractAdjustment":
		return adjustments.decide(ctx, adjustment.get(ctx.case, _number(subject)))
	if command in ("RequestSecurityClaim", "DecideSecurityClaim", "RecordSecurityClaimCommunication"):
		claim = security_actions.get_claim(ctx.case, _number(subject))
		return security_boards.prepare(ctx, correcting=claim) if command == "RequestSecurityClaim" else security_boards.decide(ctx, claim) if command == "DecideSecurityClaim" else security_boards.communicate(ctx, claim)
	if command == "RecordSecurityAction":
		if subject.endswith(" return"):
			return security_boards.give_back(ctx)
		return security_boards.replacement(ctx, _number(subject), recording=True)
	if command in ("RequestContractTermination", "DecideContractTermination", "RecordTerminationNotice", "RecordTerminationEffect", "PrepareTerminationSettlement", "CompleteTerminationSettlement"):
		row = termination.get(ctx.case, _number(subject))
		return {"RequestContractTermination": lambda: termination_boards.request(ctx, correcting=row), "DecideContractTermination": lambda: termination_boards.decide(ctx, row), "RecordTerminationNotice": lambda: termination_boards.notice(ctx, row),
			"RecordTerminationEffect": lambda: termination_boards.effect(ctx, row), "PrepareTerminationSettlement": lambda: termination_boards.prepare(ctx, row), "CompleteTerminationSettlement": lambda: termination_boards.complete(ctx, row)}[command]()
	if command in ("ResolvePublicationRequirement", "RecordContractAwardPublication"):
		row = obligation_service.get(ctx.case, "Publication", "publication")
		return reports.publication(ctx, row) if row is not None else None
	return reports.progress(ctx, reporting.get(subject.split(" ", 1)[1]))


def _change_of(ctx: Context, subject: str):
	"""The change a task subject names: `change N ...` or `amendment N`."""
	return change.get(ctx.case, int(subject.split()[1]))


def _change_board(ctx: Context, lead: dict[str, Any]):
	command, subject = lead["command"], lead["subject"]
	row = _change_of(ctx, subject)
	if row is None:
		return None
	if command == "RequestContractChange":
		return changes.request(ctx, row.kind, correcting=row)
	if command == "AppointContractChangeReviewers":
		return changes.appoint(ctx, row)
	if command in ("RecordContractChangeReview", "SignContractChangeReview"):
		kind = change.KIND_OF_SLUG[subject.split(" review ", 1)[1]]
		return changes.review(ctx, row, kind, signing=command == "SignContractChangeReview")
	if command == "SubmitContractChangeForDecision":
		return changes.submit(ctx, row)
	if command == "DecideContractChange":
		return changes.decide(ctx, row)
	return changes.activate(ctx, row)


def _delivery_board(ctx: Context, lead: dict[str, Any]):
	"""The certificate whose delivery is the viewer's next step: the first delivery (D22-P), or the delivery a reopened closure withdrew (D38-R)."""
	name = frappe.db.get_value("Contract Certificate", {"contract_case": ctx.case, "kind": "Completion", "state": "Signed", "subject_version": lead["version"]}, "name")
	if not name:
		return None
	certificate = frappe.get_doc("Contract Certificate", name)
	withdrawn = (closeout.delivery_of(certificate).get("withdrawn") or {}).get("correction")
	if withdrawn:
		return completion.reopened(ctx, frappe.get_doc("Contract Correction", withdrawn), certificate)
	return completion.delivery(ctx, certificate)


def _by_waiting(ctx: Context, lead: dict[str, Any]):
	"""The screen for something the viewer is waiting on, where the design draws one (the declarations a recommender waits for)."""
	command, subject = lead["command"], lead["subject"]
	if command.startswith("SignContractVersion:waiting") and subject.startswith("amendment"):
		return changes.pending(ctx, _change_of(ctx, subject))
	if command.startswith("RecordTerminationNotice:waiting") and subject.startswith("termination"):
		return termination_boards.pending(ctx, termination.get(ctx.case, _number(subject)))
	if command == "RecordSecurityClaimOutcome":
		return security_boards.waiting(ctx, security_actions.get_claim(ctx.case, _number(subject)))
	if command.startswith("ReplyContractCorrespondence:waiting") and subject.startswith("issue"):
		row = issues.get(ctx.case, _number(subject))
		return issue_boards.notice(ctx, row) if row.kind == "Warranty claim" else issue_boards.resolve(ctx, row)
	if command.startswith("DeclareContractInterest:waiting"):
		return agreement.d23p(ctx)
	if command.startswith("RecordContractSecurity:waiting"):
		return security.d25j(ctx)
	if command.startswith("RequestInvoiceCorrection:waiting"):
		return invoices.d18r(ctx, invoices._invoice(ctx, _number(subject)))
	if command.startswith("ApproveNativeFinanceRecord:waiting:credit"):
		return _credit_board(ctx, subject)
	if command.startswith("ApproveNativeFinanceRecord:waiting:accounting"):
		return invoices.d33(ctx, invoices._invoice(ctx, _number(subject)), mode="waiting")
	if command.startswith("ApproveNativeFinanceRecord:waiting:payment"):
		return invoices.d09f(ctx, _payment_invoice(ctx, subject), waiting=True)
	return None


def _credit_board(ctx: Context, subject: str):
	"""The Debit Note Finance prepared for a corrected claim's original liability: the approver's review, or the maker's waiting view."""
	gap = next((g for g in payment.liability_gap(ctx.case) if str(g["successor_no"]) == subject.split()[-1] and not g["reconciled"]), None)
	return invoices.liability(ctx, gap) if gap else None


def _payment_invoice(ctx: Context, subject: str):
	entry = subject.split()[-1]
	for p in payment.payments(ctx.case):
		if p["name"] == entry:
			if p["kind"] == "advance":
				return invoices.advance_as_invoice(frappe.get_doc("Contract Advance", p["invoice"]))
			return frappe.get_doc("Contract Invoice", p["invoice"])
	if subject.startswith("payment advance"):  # the draft does not exist yet
		return invoices.advance_as_invoice(advance.live(ctx.case))
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
	if ctx.doc.source_kind == "External record" and ctx.doc.lifecycle == "Preparing" and ctx.can_prepare:
		return existing.d12(ctx, ctx.user, ctx.case)  # an existing contract being registered is the preparers' until management starts
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
	_offer_outside(ctx, board)
	_offer_ending(ctx, board)
	appointed = ctx.appointment
	if appointed["appointment"]:
		board["regions"].append(kit.R("Inspectors", agreement._members_table(appointed["members"])))
	if ctx.doc.source_kind == "External record":
		funding_board.attach(ctx, board)  # how an independently registered contract is funded stays one press away on its agreement for the people who work with it, after management has started too (CM-CHG-001 v0.10 section 10.9)
	return board


def _offer_ending(ctx: Context, board: dict[str, Any]) -> None:
	"""The preparer may record that the contract did not proceed while it is not yet in force."""
	if ctx.can_prepare and ctx.doc.lifecycle in ("Preparing", "Awaiting signatures") and ending.LABEL not in board["actions"]:
		ending.attach(board)


def _offer_outside(ctx: Context, board: dict[str, Any]) -> None:
	"""While the agreement is out for signature and its terms permit it, a preparer may record a party's signed copy instead of waiting for the electronic signature."""
	if not (ctx.agreement and ctx.agreement.state == "Awaiting signatures" and ctx.can_prepare and service_outside_permitted(ctx)):
		return
	pending = frappe.get_all("Contract Signature", filters={"contract_case": ctx.case, "agreement_version": ctx.agreement.version_no, "state": ["in", ["Requested", "Waiting", "Failed", "Evidence recorded"]]}, fields=["party", "state"], order_by="sequence asc")
	if not pending:
		return
	party = next((s["party"] for s in pending if s["state"] != "Evidence recorded"), pending[0]["party"]).lower()
	label = "Record an outside signature"
	for region in board.get("regions", []):
		for block in region.get("b", []):
			if block.get("k") == "links":
				block["items"].append(label)
				board["actions"][label] = kit.route(ctx.case, "agreement", "outside", party)
				return


def register_board(user: str) -> dict[str, Any]:
	"""The registration form for a contract signed before KenTender: a person who prepares contracts, or the stable denial."""
	from kentender_contracts.services import picker_sources

	if not picker_sources.preparing_units(user):
		fail("CM_AUTHORITY", denied=True, reason="You do not have access to this contract.")
	board = existing.d12(None, user)
	board["tab"], board["tabs"], board["audiences"] = "Agreement", [], []
	return board


def board_for(case: str, user: str, *, tab: str | None = None, subject: tuple[str, ...] = ()) -> dict[str, Any]:
	"""The screen for this viewer: a record page with its tab, next step, regions and actions. Denial is `CM_AUTHORITY` with `denied`, drawn by the client as the shared denied page."""
	if case == "register":
		return register_board(user)
	if not case or not frappe.db.exists("Contract Case", case):
		fail("CM_AUTHORITY", denied=True, reason="You do not have access to this contract.")
	ctx = Context(case, user)
	if not ctx.grants:
		fail("CM_AUTHORITY", denied=True, reason="You do not have access to this contract.")
	lead = ctx.lead
	selected = TAB_KEYS.get((tab or "").lower()) or (chrome.tab_of(lead["command"], lead["subject"], ctx.doc.lifecycle) if lead else "Agreement")
	board = None
	if subject:
		board = _subject_board(ctx, selected, subject)
	own = bool(lead) and lead["holder"].lower() == user.lower() and lead["state"] in ("actionable", "blocked")  # someone else's leading item is only a "waiting on" line, never a screen to act on
	if board is None and own and chrome.tab_of(lead["command"], lead["subject"], ctx.doc.lifecycle) == selected:
		board = _by_subject(ctx, lead)
	if board is None and not own:
		for item in sorted((t for t in ctx.tasks if t["holder"].lower() == user.lower() and t["state"] == "waiting" and chrome.tab_of(t["command"], t["subject"], ctx.doc.lifecycle) == selected), key=lambda t: t["assigned_at"]):
			board = _by_waiting(ctx, item)
			if board:
				break
	if board is None and not own and selected == "Agreement" and ctx.doc.lifecycle == "Active" and _declared_no_conflict(ctx):
		board = agreement.d24s(ctx)  # the member's own receipt of the declaration, until there is something else for them to do
	if board is None and not own and selected == "Agreement" and ctx.doc.lifecycle == "Preparing" and ctx.can_prepare and ctx.doc.source_kind != "External record":
		board = agreement.d02(ctx)  # an authorised preparer prepares the agreement whether or not the head of procurement's task is theirs (section 5.3)
		_offer_ending(ctx, board)
	if board is None:
		board = summary(ctx, selected)
	if own and lead["state"] == "actionable":
		_point_to_the_step(ctx, board, lead, selected)
	board["tab"] = selected
	board["tabs"] = [{"label": t, "route": [case, t.lower()]} for t in chrome.TABS]
	board["audiences"] = ctx.audiences
	return board


STEP_LABEL = "Go to your next step"


def _point_to_the_step(ctx: Context, board: dict[str, Any], lead: dict[str, Any], selected: str) -> None:
	"""The next-step block is drawn on every tab and the step is taken on its own tab: from another tab the block says what to do, so the way there is one press away. Nobody is left on a screen that names their
	step and gives them no way to it (section 6.3; KT-STD-001 3B.7)."""
	step = board.get("next")
	home = chrome.tab_of(lead["command"], lead["subject"], ctx.doc.lifecycle)
	if not step or step.get("k") != "turn" or board.get("p") or home == selected or STEP_LABEL in board["actions"]:
		return
	board["s2"] = [*board.get("s2", []), STEP_LABEL]
	board["actions"][STEP_LABEL] = kit.tab(home)


def _subject_board(ctx: Context, tab: str, subject: tuple[str, ...]) -> dict[str, Any] | None:
	"""The screen a route names under a tab: `/<contract>/<tab>/<subject...>`. A leading tab name is tolerated (the first routes of the thread carried it) so a link and a direct address land on the same screen."""
	if subject and subject[0].lower() == tab.lower():
		subject = subject[1:]
	if not subject:
		return None
	if subject[0] == "outside" and len(subject) > 1 and tab == "Agreement" and ctx.can_prepare and ctx.doc.lifecycle == "Awaiting signatures" and service_outside_permitted(ctx):
		return outside.d26(ctx, "Entity" if subject[1] == "entity" else "Supplier", differs=bool(outside.mismatched(ctx)))
	if subject == ("recommend",) and tab == "Agreement" and ctx.can_prepare and ctx.doc.lifecycle == "Active":
		return agreement.d23r(ctx)
	if subject == ("appointment",) and tab == "Agreement":
		return _agreement_summary(ctx)
	if subject == ("funding",) and tab in ("Agreement", "Invoices") and funding_board.visible(ctx):
		return funding_board.d21f(ctx)
	if subject == ("intake",) and tab == "Agreement" and ctx.doc.source_kind == "External record" and ctx.can_prepare:
		return existing.d12(ctx, ctx.user, ctx.case)
	if subject[0] == "amendment" and len(subject) > 1 and subject[1].isdigit() and tab == "Agreement" and ({"terms", "supplier_view"} & _sets(ctx)):
		row = change.get(ctx.case, int(subject[1]))
		return changes.amendment_view(ctx, row) if row is not None and row.amendment_version else None
	if subject[0] in ("request-extension", "request-quantity") and tab == "Obligations" and change.can_request(ctx.case, ctx.user):
		return changes.request(ctx, "Extension" if subject[0] == "request-extension" else "Quantity", proposed=int(subject[1]) if len(subject) > 1 and subject[1].isdigit() else None)
	if tab == "Obligations":
		found = _obligation_route(ctx, subject)
		if found is not None:
			return found
	if subject[0].isdigit() and tab == "Agreement" and "terms" in _sets(ctx):
		return agreement.d02v(ctx, int(subject[0]))
	if subject == ("record-delivery",) and "receiver" in ctx.audiences:
		return delivery.d04(ctx)
	if subject == ("submit-invoice",) and "supplier" in ctx.audiences:
		return invoices.d18(ctx)
	if subject[0] == "record-liability" and len(subject) > 1 and subject[1].isdigit() and tab == "Invoices":
		name = frappe.db.get_value("Contract Invoice", {"contract_case": ctx.case, "invoice_no": int(subject[1])}, "name")
		row = frappe.get_doc("Contract Invoice", name) if name else None
		return invoices.d33(ctx, row, mode="maker", early=True) if invoices.may_record_liability(ctx, row) else None
	return None


def _obligation_route(ctx: Context, subject: tuple[str, ...]):
	"""The screens a person opens from the Obligations tab: a request form, an issue, a report."""
	head = subject[0]
	if head == "issue" and len(subject) > 1 and subject[1].isdigit():
		row = issues.get(ctx.case, int(subject[1]))
		if row is None:
			return None
		if "supplier" in ctx.audiences and len(ctx.audiences) == 1:  # the supplier sees the matter and answers it; the owner's review and the internal stages are not theirs
			return issue_boards.closed(ctx, row) if row.state == "Closed" else issue_boards.reply(ctx, row)
		if row.kind == "Warranty claim":
			return issue_boards.warranty_view(ctx, row)
		return issue_boards.closed(ctx, row) if row.state == "Closed" else issue_boards.resolve(ctx, row)
	if head == "publication":
		row = obligation_service.get(ctx.case, "Publication", "publication")
		return reports.publication(ctx, row) if row is not None else None
	if head == "report" and len(subject) > 1:
		return reports.progress(ctx, reporting.get(subject[1]))
	if head == "request-termination" and ctx.can_prepare and ctx.doc.lifecycle == "Active" and termination.live(ctx.case) is None:
		return termination_boards.request(ctx)
	if head == "request-security-claim" and ctx.can_prepare and security_actions.operative(ctx.case) and ctx.doc.lifecycle in ("Active", "Terminated"):
		return security_boards.prepare(ctx)
	if head == "record-replacement" and ctx.can_prepare and security_actions.operative(ctx.case) and ctx.doc.lifecycle in ("Active", "Terminated"):
		return security.d25r(ctx, 0, replacing=True)
	if head == "claim-warranty" and ctx.doc.lifecycle in ("Active", "Closed") and obligations.may_manage(ctx):
		return issue_boards.new_claim(ctx)
	if head == "request-correction" and ctx.doc.lifecycle == "Closed" and obligations.may_correct(ctx) and closure_correction.live(ctx.case) is None:
		return completion.correction_request(ctx)
	if head == "request-correction" and ctx.doc.lifecycle == "Terminated" and obligations.may_correct(ctx):
		return completion.terminated_source(ctx)  # a termination is not corrected here: the screen says so and points to the termination and its settlement
	return None


def _declared_no_conflict(ctx: Context) -> bool:
	from kentender_contracts.services import bindings

	found = bindings.member(ctx.case, ctx.user) if ctx.appointment["appointment"] else None
	return bool(found and found["member"].get("declared_at") and not found["member"].get("conflict") and "supplier" not in ctx.audiences)


def service_outside_permitted(ctx: Context) -> bool:
	from kentender_contracts.services import outside_signature

	return bool(ctx.agreement) and outside_signature.permitted(ctx.terms)[0]


def _sets(ctx: Context) -> set[str]:
	from kentender_contracts.services import audience

	return set(audience.field_sets(ctx.grants))
