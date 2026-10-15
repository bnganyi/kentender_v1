# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What every contract screen shares: the page chrome and the next step (CM-CHG-001 v0.8 sections 6.3, 10.1A; KT-STD-001 3B).

`base` draws the record page the way every board does (title, supplier, contract reference, status, tab, back link) and stamps it with the case and the revision a command must be sent with.
`next_block` maps the shared, server-produced `next_step` answer onto the design's four kinds, so no wording is computed in the browser and a screen never offers an action its next step does not."""

from __future__ import annotations

from typing import Any

from kentender_contracts.boards import kit
from kentender_contracts.boards.context import Context, when
from kentender_contracts.services import next_steps, tasks
from kentender_core.services import next_step as shared

TABS = ("Agreement", "Deliveries", "Invoices", "Obligations", "History")
LIFECYCLE_LABEL = {"Preparing": "Preparing", "Awaiting signatures": "Awaiting signatures", "Active": "Active", "Closed": "Closed", "Did not proceed": "Did not proceed", "Terminated": "Terminated"}


def base(ctx: Context, board_id: str, **o) -> dict[str, Any]:
	board = _base(ctx, board_id, **o)
	for fix in ((board.get("next") or {}).get("fixes") or []):  # a blocked step's fixes go somewhere: the contract's remaining work, where every hold is listed with its holder
		board["actions"].setdefault(fix, kit.tab("Obligations"))
	return board


def _base(ctx: Context, board_id: str, **o) -> dict[str, Any]:
	supplier_view = "supplier" in ctx.audiences and len(ctx.audiences) == 1
	o.setdefault("d", board_id.split("-")[0].split(" ")[0])
	o.setdefault("back", "Back to my contracts" if supplier_view else "Back to contracts")
	return kit.board(id=board_id, ref=ctx.doc.contract_id, sub=ctx.doc.supplier_name or "", st=LIFECYCLE_LABEL.get(ctx.doc.lifecycle, ctx.doc.lifecycle), case=ctx.case, version=int(ctx.doc.record_version or 0), **o)


def headline_for(lead: dict[str, Any]) -> str:
	return lead["title"]


def next_block(ctx: Context) -> dict[str, Any] | None:
	"""The viewer's next step in the board's own four kinds. `None` for a reader with no personal work (section 6.3 "Not involved")."""
	if ctx.neutral:
		return None
	answer = next_steps.answer(ctx_view(ctx), headline_for=headline_for)
	kind = answer["kind"]
	if kind == shared.KIND_NOT_INVOLVED:
		return None
	if kind == shared.KIND_DONE:
		import frappe

		if not frappe.db.exists("Contract Task", {"contract_case": ctx.case, "holder": ctx.user}):
			return None  # never involved: no next-step block at all (section 6.3 "Not involved")
		return kit.done(answer.get("headline") or "Nothing is waiting for you on this contract.")
	lead = ctx_view(ctx)["leading"]
	holder = ctx.name(lead["holder"]) if lead else ""
	since = when(lead["assigned_at"]) if lead else ""
	if kind == shared.KIND_YOUR_TURN:
		return kit.turn(answer["headline"], holder)
	if kind == shared.KIND_BLOCKED:
		blocker = (answer.get("blockers") or [{}])[0]
		fixes = [f["label"] for f in (blocker.get("fixes") or [])]
		return kit.blk(answer["headline"], holder, fixes, blocker.get("message", ""))
	names = ", ".join(sorted({ctx.name(t["holder"]) for t in ctx.tasks if t["state"] in ("actionable", "blocked") and t["subject"] == lead["subject"] and t["holder"].lower() != ctx.user.lower()})) if lead else ""
	return kit.wait(answer["headline"], f"{names or holder}; assigned {since}." if since else names)


def ctx_view(ctx: Context) -> dict[str, Any]:
	return ctx.view


def tab_of(command: str) -> str:
	return TAB_OF_COMMAND.get(command.split(":")[0], "Agreement")


TAB_OF_COMMAND = {
	"RequestContractSignatures": "Agreement", "SignContractVersion": "Agreement", "RecordContractSecurity": "Agreement", "VerifyContractSecurity": "Agreement", "ReviseContractIntake": "Agreement", "ReviewAwardRestriction": "Agreement", "RecordContractNotProceeding": "Agreement", "ConfirmOpeningPosition": "Invoices", "StartContractManagement": "Agreement", "RecommendContractInspectors": "Agreement", "AppointContractInspectors": "Agreement", "DeclareContractInterest": "Agreement",
	"RecordInspectionObservations": "Deliveries", "ResolveDeliveryException": "Deliveries", "SignTechnicalCertificate": "Deliveries", "PrepareAcceptanceReport": "Deliveries", "SignAcceptanceReport": "Deliveries", "RequestAcceptanceCorrection": "Deliveries", "DecideContractAcceptance": "Deliveries",
	"SignContractCertification": "Invoices", "ResolveInvoiceDuplicate": "Invoices", "RequestInvoiceCorrection": "Invoices", "CorrectContractInvoice": "Invoices", "SaveNativeFinanceDraft": "Invoices", "CorrectFinanceSettlement": "Invoices", "ReconcileInvoiceLiability": "Invoices",
	"SubmitNativeFinanceForApproval": "Invoices", "ApproveNativeFinanceRecord": "Invoices", "RecordFinanceSettlement": "Invoices",
	"IssueCompletionCertificate": "Obligations", "PrepareContractCloseout": "Obligations", "SignContractCloseout": "Obligations", "RestoreContractOperation": "Obligations",
}
