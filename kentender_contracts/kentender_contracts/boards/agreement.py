# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Agreement tab: preparation, signing, appointment and declarations (boards D02, D02-V, D03, D03-W, D03-A, D23, D23-R, D23-P, D24, D24-X; CM-CHG-001 v0.8 section 10).

Each builder reads the design's board for the same state and draws the same regions with live data. Where the design cannot draw something real -- the particulars a preparer must still complete -- the
region appears only while it is needed, so a complete state is exactly the board."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, formatdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import bindings, formation, people, records, source_package
from kentender_contracts.services.errors import fail

SIGNATURE_STATE = {"Signed": "!Signed", "Requested": "!Awaiting signature", "Waiting": "!Awaiting signature", "Pending": "!Awaiting signature", "Failed": "!Awaiting signature"}


def _delivery_due(ctx: Context) -> str:
	due = (ctx.terms.get("delivery") or {}).get("due")
	return formatdate(due, "d MMMM yyyy") if due else ""


def _security(ctx: Context) -> str:
	sec = ctx.terms.get("security") or {}
	return sec.get("statement") or ("Required" if sec.get("required") else "Not required under these test terms")


def _warranty(ctx: Context, short: bool = False) -> str:
	w = ctx.terms.get("warranty") or {}
	return f"{w.get('months')} months" if short else f"{w.get('months')} months from each unit’s acceptance" if w.get("months") else ""


def _items(ctx: Context) -> str:
	lines = ctx.terms.get("lines") or []
	return ", ".join(f"{cint(l['quantity'])} {l.get('description') or l.get('item')} at {money(l['rate'], ctx.currency)} each" for l in lines)


def summary_region(ctx: Context) -> dict:
	return kit.R("Summary", kit.f(["Contract value", money(ctx.terms.get("total"), ctx.currency)], ["Delivery", _delivery_due(ctx)], ["Warranty", _warranty(ctx, True)], ["Security", _security(ctx)]))


def _version(ctx: Context) -> int:
	return ctx.agreement.version_no if ctx.agreement else 1


def agreement_region(ctx: Context) -> dict:
	rows = kit.r(["Supplier", ctx.doc.supplier_name], ["Items", _items(ctx)], ["Contract value", money(ctx.terms.get("total"), ctx.currency) + (", tax included" if ctx.terms.get("tax_included") else "")],
		["Delivery due", _delivery_due(ctx)], ["Warranty", _warranty(ctx)], ["Performance security", _security(ctx)])
	return kit.R("Agreement summary", rows, kit.lk(f"View agreement {_version(ctx)}"))


def package_region(ctx: Context) -> dict:
	manifest = records.loads(frappe.db.get_value("Contract Source Package", ctx.agreement.source_package, "manifest_json")) if ctx.agreement and ctx.agreement.source_package else {"documents": []}
	category = {"S7": "Agreement", "S2": "Tender form", "S3": "Price schedule", "S4": "Requirements and specifications", "S5": "Conditions of contract", "S8": "Award notification"}
	rows = [[category.get(d["source"], d["label"]), d["label"], f"{d['from']} 1"] for d in manifest.get("documents", [])]
	return kit.R("Incorporated documents", kit.t(["Category", "Document", "Source"], rows))


def parties_region(ctx: Context) -> dict:
	parties = ctx.terms.get("parties") or {}
	return kit.R("Parties and execution", kit.t(["Party", "Signatory", "Capacity", "Witness"], [["Procuring entity", parties.get("entity", {}).get("signatory", ""), parties.get("entity", {}).get("capacity", ""), "Captured at signing"],
		["Supplier", parties.get("supplier", {}).get("signatory", ""), parties.get("supplier", {}).get("capacity", ""), "Captured at signing"]]))


def signatures_region(ctx: Context) -> dict:
	if not ctx.signatures and ctx.doc.source_kind == "External record":
		return kit.R("Signatures", kit.xh("This contract was signed outside Contract Management and is recorded from an external source. Nobody is asked to sign it again."))
	rows = [[ctx.name(s["signer"]), "Supplier authorised signatory" if s["party"] == "Supplier" else "Entity signatory", SIGNATURE_STATE.get(s["state"], "!Awaiting signature")] for s in ctx.signatures]
	return kit.R("Signatures", kit.t(["Signatory", "Capacity", "Status"], rows))


def _particulars_fields(ctx: Context, missing: list[str]) -> dict:
	have = ctx.terms.get("particulars", {})
	fields = []
	if "agreement_date" in missing:
		fields.append(kit.dt("Agreement date", have.get("agreement_date", ""), "agreement_date"))
	if "entity_signatory" in missing:
		fields.append(kit.pick("Entity signatory", have.get("entity_signatory", ""), "contracts.person", "entity_signatory", {"role": "Entity contract signing"}, ctx.name(have.get("entity_signatory", "")), "signatory"))
	if "item_mapping" in missing:
		for line in ctx.terms.get("lines") or []:
			current = (have.get("item_mapping") or {}).get(line["line_id"], "")
			fields.append(kit.pick(f"Catalogue item for {line.get('description') or line.get('item')}", current, "contracts.native_record", f"item_mapping.{line['line_id']}", {"kind": "item"}, current, "item"))
	if "native_supplier" in missing:
		fields.append(kit.pick("Supplier in Finance", have.get("native_supplier", ""), "contracts.native_record", "native_supplier", {"kind": "supplier"}, have.get("native_supplier", ""), "supplier"))
	if "ag_clearance" in missing:
		fields.append(kit.tx("Attorney-General clearance reference", have.get("ag_clearance", ""), "ag_clearance"))
	if "asset_location" in missing:
		fields.append(kit.pick("Asset location", have.get("asset_location", ""), "contracts.native_record", "asset_location", {"kind": "location"}, have.get("asset_location", ""), "location"))
	return kit.R("Particulars to complete", kit.fl(*fields), kit.xh("These are the details the issued terms do not supply. Save them, then send the agreement for signature."))


def d02(ctx: Context) -> dict:
	"""Prepare agreement (HOP or an authorised preparer)."""
	missing = ctx.assembled["missing"]
	failed = ctx.assembled["failed"]
	next_ = chrome.next_block(ctx)
	if failed and ctx.mine("RequestContractSignatures"):
		next_ = kit.blk("A required source cannot be verified.", ctx.name(ctx.user), ["View issue"], "; ".join(f"{f['source']} {f['category']}: {f['reason']}" for f in failed))
	b = chrome.base(ctx, "D02", d="D02", name="Prepare agreement", title="Prepare contract", tab="Agreement", next=next_, ev=["Award package 1", "Issued terms 1"],
		regions=[summary_region(ctx), agreement_region(ctx)], p="Send for signature")
	if failed:
		b["p"], b["s2"], b["regions"] = "", [], [kit.R("Sources", kit.t(["Source", "What", "Held by", "Problem"], [[f["source"], f["category"], f["owner"] or "—", f["reason"]] for f in failed]))]
		return b
	if missing:
		b["regions"].insert(0, _particulars_fields(ctx, missing))
		b["p"], b["s2"] = "Save particulars", [kit.disabled("Send for signature")]
		b["actions"]["Save particulars"] = kit.command("SaveContractParticulars")
	else:
		b["actions"]["Send for signature"] = kit.command("RequestContractSignatures")
	b["actions"][f"View agreement {_version(ctx)}"] = kit.route(ctx.case, "agreement", str(_version(ctx)))
	return b


def d02v(ctx: Context, version: int) -> dict:
	"""View agreement N: the source-based Form No. 4 with its bound insertions and the incorporated documents."""
	agreement = frappe.get_doc("Contract Agreement Version", frappe.db.get_value("Contract Agreement Version", {"contract_case": ctx.case, "version_no": version}, "name"))
	terms = records.loads(agreement.terms_json)
	particulars = terms.get("particulars", {})
	parties = terms.get("parties", {})
	insertions = kit.t(["Insertion", "Bound value", "Source"], [
		["Agreement date", formatdate(particulars["agreement_date"], "d MMMM yyyy") if particulars.get("agreement_date") else "Not yet entered", "Prepared particulars"],
		["Procuring entity", parties.get("entity", {}).get("name", ""), "Award entity particulars"], ["Supplier", parties.get("supplier", {}).get("name", ""), "Accepted supplier identity"],
		["Goods", ", ".join(f"{cint(l['quantity'])} {l.get('description')}" for l in terms.get("lines", [])), "Issued requirements, awarded lot"],
		["Amount", money(terms.get("total"), terms.get("currency", "KES")) + (", tax included" if terms.get("tax_included") else ""), "Accepted price schedule"],
		["Entity signatory", f"{parties.get('entity', {}).get('signatory', '')}, {parties.get('entity', {}).get('capacity', '')}", "Authority record"],
		["Supplier representative", f"{parties.get('supplier', {}).get('signatory', '')}, {parties.get('supplier', {}).get('capacity', '')}", "Supplier authority evidence"]])
	text = [kit.xh(p) for p in _plain_paragraphs(agreement.rendered_html)]
	b = chrome.base(ctx, "D02-V", d="D02", name="Agreement", title=f"Agreement {version}", tab="Agreement", back="Back to contract", next=None, ev=["Award package 1", "Issued terms 1"],
		regions=[kit.R("Form No. 4 particulars", insertions), package_region(ctx), kit.R("Agreement text", *text)], p="")
	b["actions"]["Back to contract"] = kit.route(ctx.case, "agreement")
	return b


def _plain_paragraphs(html: str) -> list[str]:
	import re

	body = re.sub(r"<h1>.*?</h1>", "", html, flags=re.S)
	return [re.sub(r"<[^>]+>", "", p).strip() for p in re.findall(r"<p>(.*?)</p>", body, flags=re.S) if re.sub(r"<[^>]+>", "", p).strip()]


def d03(ctx: Context, *, entity: bool = False, waiting: bool = False) -> dict:
	"""Sign contract (the supplier's signatory, or the entity's second); D03-W when the viewer signed and the other party has not."""
	regions = [summary_region(ctx), agreement_region(ctx)]
	if entity:
		regions.append(signatures_region(ctx))
	identifier = "D03-W" if waiting else "D03-A" if entity else "D03"
	party = "Entity" if entity else "Supplier"
	b = chrome.base(ctx, identifier, d="D03", name="Supplier signature", title="Sign contract", tab="Agreement", next=chrome.next_block(ctx), regions=regions, ev=["Agreement 1"],
		p="" if waiting else "Sign contract", s2=["View agreement"] if waiting else [])
	if not waiting:
		b["actions"]["Sign contract"] = kit.command("SignContractVersion", party=party)
	b["actions"]["View agreement"] = b["actions"][f"View agreement {ctx.agreement.version_no}"] = kit.route(ctx.case, "agreement", str(ctx.agreement.version_no))
	return b


# -- appointment -----------------------------------------------------------------------------------------------------------------------
def d23r(ctx: Context) -> dict:
	"""Recommend inspectors (HOP draft)."""
	labels = ["User department", "Technical", "Procurement"]
	inspector = {"role": "Contract inspection"}
	fields = [kit.pick("Chair", "", "contracts.person", "chair", inspector, "", "chair"), kit.sel("Chair capacity", labels[0], labels, "chair_label"),
		kit.pick("Technical member (gives the technical confirmation)", "", "contracts.person", "member_technical", {"role": "Technical certification"}, "", "technical member"), kit.sel("Member capacity", labels[1], labels, "member_technical_label"),
		kit.pick("Member", "", "contracts.person", "member_other", inspector, "", "member"), kit.sel("Member capacity", labels[2], labels, "member_other_label"), kit.dt("From date", "", "from_date"), kit.dt("Until date", "", "until_date")]
	b = chrome.base(ctx, "D23-R", d="D23", name="Appoint inspectors", title="Recommend inspectors", tab="Agreement", next=chrome.next_block(ctx), regions=[kit.R("Proposed members", kit.fl(*fields))],
		p="Recommend inspectors", ev=[])
	b["actions"]["Recommend inspectors"] = kit.command("RecommendContractInspectors")
	return b


def _members_table(members: list[dict]) -> dict:
	return kit.t(["Member", "Role", "Capacity"], [[m["name"], m["capacity"], m.get("role_label") or ("Technical" if m.get("certifier") else "")] for m in members])


def d23(ctx: Context) -> dict:
	"""Appoint inspectors (the Accounting Officer's review of the recommendation)."""
	proposal = ctx.proposal
	members = records.loads(proposal.members_json, [])
	b = chrome.base(ctx, "D23", d="D23", name="Appoint inspectors", title="Appoint inspectors", tab="Agreement", next=chrome.next_block(ctx), ev=[f"Recommendation {proposal.reference}"],
		regions=[kit.R("Proposed members", _members_table(members)), kit.R("Proposal", kit.f(["Proposed period", _period(proposal)], ["Recommended by", f"{ctx.name(proposal.recommended_by)}, {when(proposal.creation)}"], ["Recommendation reference", proposal.reference]))],
		p="Appoint inspectors", s2=["Return for correction"])
	b["actions"]["Appoint inspectors"] = kit.dialog("appoint")
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["dialogs"]["appoint"] = kit.dlg("Appoint inspectors", [kit.fl(kit.dt("From date", str(proposal.effective_from or "")[:10], "from_date"), kit.dt("Until date", str(proposal.effective_to or "")[:10], "until_date")),
		kit.r(*[[m["name"], f"{m['capacity']} · {m.get('role_label', '')}"] for m in members], ["Period", _period(proposal)])], "Appoint", command="AppointContractInspectors", args={"appointment": proposal.name})
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return", command="ReturnContractAppointment", args={"appointment": proposal.name})
	return b


def _period(proposal) -> str:
	if not proposal.effective_from and not proposal.effective_to:
		return "From appointment, until replaced"
	return f"{formatdate(proposal.effective_from, 'd MMM yyyy') if proposal.effective_from else 'Appointment'}–{formatdate(proposal.effective_to, 'd MMM yyyy') if proposal.effective_to else 'until replaced'}"


def d23p(ctx: Context) -> dict:
	"""Declaration pending: who has declared and who has not."""
	state = ctx.appointment
	rows = [[m["name"], m["capacity"], "Conflict declared" if m.get("conflict") else "No conflict declared" if m.get("declared_at") else "Declaration pending"] for m in state["members"]]
	b = chrome.base(ctx, "D23-P", d="D23", name="Appoint inspectors", title="Appoint inspectors", tab="Agreement", next=chrome.next_block(ctx), ev=[f"Appointment {state['reference']}"],
		regions=[kit.R("Declarations", kit.t(["Member", "Role", "Declaration"], rows)), kit.R("Appointment", kit.f(["Reference", state["reference"] or ""], ["Written record", f"Appointment {state['version']}"], ["Period", "From appointment, until replaced"]))])
	return b


def d24(ctx: Context) -> dict:
	"""Declare interest (an appointed member)."""
	ctx_region = kit.R("Contract", kit.f(["Contract", ctx.doc.contract_id], ["Title", ctx.terms.get("title") or ctx.doc.title or ""], ["Supplier", ctx.doc.supplier_name]))
	decl = ["I have no conflict of interest", "I have a conflict of interest"]
	conflict = kit.ta("Description", "", "conflict")
	conflict["when"] = {"declaration": 1}
	field = kit.rad("Your declaration", decl, -1, "declaration")
	note = kit.xs("You will not be able to inspect or sign this contract while this conflict remains unresolved.")
	note["when"] = {"declaration": 1}
	b = chrome.base(ctx, "D24", d="D24", name="Declare interest", title="Declare interest", tab="Agreement", next=chrome.next_block(ctx), ev=[f"Appointment {ctx.appointment['reference']}"],
		regions=[ctx_region, kit.R("Declaration", kit.fl(field, conflict), note)], p="Save declaration")
	b["actions"]["Save declaration"] = kit.command("DeclareContractInterest")
	return b
