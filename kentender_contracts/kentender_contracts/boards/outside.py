# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Signing outside the system: boards D26, D26-E, D26-H (CM-CHG-001 v0.8 section 10; plan Phase 5).

HOP records each party's executed copy (D26), then checks both and confirms (D26-E). If a recorded copy no longer binds the version in force, nothing can be confirmed and the screen says so (D26-H)
with what was entered kept. The signed copies are opened through an audience-checked download, never by a public link."""

from __future__ import annotations

import frappe
from frappe.utils import formatdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context
from kentender_contracts.services import clock, formation
from kentender_contracts.services import outside_signature as service

PARTY_LABEL = {"Supplier": "Supplier", "Entity": "Procuring entity"}


def _basis(ctx: Context, agreement, party: str | None = None) -> dict:
	_ok, method = service.permitted(ctx.terms)
	authority = "Supplier authorised-signatory assignment" if party == "Supplier" else "Entity signing appointment" if party == "Entity" else "The authority the agreement names for each party"
	return kit.R("Signing basis", kit.r(["Whole-document version", f"Agreement {agreement.version_no}"], ["Authority source", authority], ["Reviewed method", method or "Outside signing permitted by the issued terms"]))


def _slot(ctx: Context, party: str):
	name = frappe.db.get_value(service.SIGNATURE, {"contract_case": ctx.case, "agreement_version": ctx.agreement.version_no, "party": party}, "name")
	return frappe.get_doc(service.SIGNATURE, name)


def _date(value) -> str:
	return formatdate(value, "d MMM yyyy") if value else ""


def d26(ctx: Context, party: str = "Supplier", *, differs: bool = False) -> dict:
	"""Record an outside signature (HOP, or an authorised preparer)."""
	slot = _slot(ctx, party)
	held = service.evidence_of(slot)
	today = str(clock.now())[:10]
	fields = [kit.sel("Party", PARTY_LABEL[party], list(PARTY_LABEL.values()), "party"), kit.tx("Signed by", held.get("signed_by") or ctx.name(slot.signer), "signed_by"),
		kit.tx("Capacity", held.get("capacity") or slot.capacity, "capacity"), kit.dt("Signed on", str(slot.signed_on or "") or today, "signed_on"), kit.file("Signed copy", "", "copy"), kit.ta("Notes", held.get("notes", ""), "notes")]
	title = "Record an outside signature"
	turn = kit.blk(f"The signed copies do not match agreement {ctx.agreement.version_no}.", ctx.name(ctx.user), ["Record source evidence", "View differences"]) if differs else \
		kit.turn(f"Record the {party.lower()}'s signed agreement.", ctx.name(ctx.user))
	board = chrome.base(ctx, "D26-H" if differs else "D26", d="D26", name="Record outside signature", title=title, tab="Agreement", next=turn, regions=[kit.R("Signature evidence", kit.fl(*fields)), _basis(ctx, ctx.agreement, party)],
		p="" if differs else "Save signature evidence", s2=[] if differs else [f"View agreement {ctx.agreement.version_no}"], ev=[f"Agreement {ctx.agreement.version_no}"])
	if not differs:
		board["actions"]["Save signature evidence"] = kit.command("RecordOutsideContractSignature")
		board["actions"][f"View agreement {ctx.agreement.version_no}"] = kit.route(ctx.case, "agreement", str(ctx.agreement.version_no))
	return board


def d26e(ctx: Context) -> dict:
	"""Check signed agreement (HOP): both signed copies, then confirm."""
	rows, actions = [], {}
	for party in ("Supplier", "Entity"):
		slot = _slot(ctx, party)
		held = service.evidence_of(slot)
		if slot.state == "Signed":
			rows.append([PARTY_LABEL[party], ctx.name(slot.signer), slot.capacity, _date(slot.signed_at), "Signed electronically"])
			continue
		label = f"Signed agreement {ctx.agreement.version_no} — {party.lower()}"
		rows.append([PARTY_LABEL[party], held.get("signed_by", ""), held.get("capacity", ""), _date(slot.signed_on), "@" + label])
		actions[label] = {"do": "download", "url": f"/api/method/kentender_contracts.api.contract.download_evidence?contract={ctx.case}&file={slot.copy_reference}"}
	board = chrome.base(ctx, "D26-E", d="D26", name="Record outside signature", title="Check signed agreement", tab="Agreement", next=chrome.next_block(ctx), regions=[
		kit.R("Signed copies", kit.t(["Party", "Signed by", "Capacity", "Signed on", "Copy"], rows)), _basis(ctx, ctx.agreement)], p="Confirm signature evidence", s2=[kit.disabled("Report a problem")],
		ev=[f"Agreement {ctx.agreement.version_no}"])
	board["actions"].update(actions)
	board["actions"]["Confirm signature evidence"] = kit.command("ConfirmOutsideSignatureEvidence")
	return board


def mismatched(ctx: Context) -> list[str]:
	"""The parties whose recorded copy does not bind the version in force."""
	out = []
	for party in ("Supplier", "Entity"):
		slot = _slot(ctx, party)
		if slot.state == "Evidence recorded" and service.evidence_of(slot).get("agreement_digest") != ctx.agreement.rendered_digest:
			out.append(party)
	return out
