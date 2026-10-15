# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Registering an existing contract: boards D12, D21, D21-H (CM-CHG-001 v0.8 sections 5.13, 10; plan Phase 5, tracker CM8-508, CM8-511).

D12 records the executed contract and where it stands (the preparer, saved while incomplete and revised as findings come); D21 is Finance confirming the opening position against the native records it is
linked to; D21-H is the head of procurement starting management. The server builds each screen from the saved intake, so what is shown is what the commands will check."""

from __future__ import annotations

import frappe
from frappe.utils import flt

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money
from kentender_contracts.services import existing, opening, people, records

ITEM_COLS = ["Item description", "Quantity", "UOM", "Rate", "Tax treatment", "Serial tracking", "Accepted", "In custody", "Invoiced quantity"]
ITEM_ROWS_EXTRA = 3
ITEM_FIELDS = ("description", "quantity", "uom", "rate", "tax", None, "accepted", "in_custody", "invoiced_quantity")


def _v(values: dict, name: str, default=""):
	found = values.get(name)
	return default if found is None else found


def _unit_label(unit: str) -> str:
	return (frappe.db.get_value("Organisation Unit", unit, "unit_name") or unit) if unit else ""


def _num(x) -> str:
	return "" if x is None else (f"{x:g}" if isinstance(x, float) else str(x))


def _item_rows(lines: list[dict], opening_lines: dict, mapping: dict) -> tuple[list[list[str]], dict[str, str]]:
	"""The editable item table: the saved lines, then blank rows to add more. A cell's prefix says how it is drawn (`~` text, `#` number, `^` choice, none read-only)."""
	rows, inputs = [], {}
	count = max(len(lines), 0) + ITEM_ROWS_EXTRA
	for i in range(count):
		line = lines[i] if i < len(lines) else {}
		extra = opening_lines.get(line.get("line_id", ""), {}) if line else {}
		serial = ""
		if line and mapping.get(line["line_id"]):
			serial = "Yes" if frappe.db.get_value("Item", mapping[line["line_id"]], "has_serial_no") else "No"
		rows.append([f"~{line.get('description', '')}", f"#{_num(line.get('quantity'))}", f"~{line.get('uom', '')}", f"~{_num(line.get('rate'))}", f"^{line.get('tax', 'Included')}|Included,Excluded", serial or "—",
			f"#{_num(extra.get('accepted'))}", f"#{_num(extra.get('in_custody'))}", f"#{_num(extra.get('invoiced_quantity'))}"])
		for c, field in enumerate(ITEM_FIELDS):
			if field:
				inputs[f"{i},{c}"] = f"row.{i + 1}.{field}"
	return rows, inputs


def d12(ctx: Context | None, user: str, case: str = "", *, source: str = "") -> dict:
	"""Register existing contract (the preparer): a new intake, or a saved one revised. `source` overrides the origin shown (the eGP variant draws its references)."""
	current = existing.stored(case) if case else None
	intake = current["intake"] if current else {}
	values = dict(intake.get("values") or {})
	if source:
		values["source"] = source
	op = intake.get("opening") or {}
	lines = records.loads(current["agreement"].items_json, []) if current else []
	name = lambda u: people.full_name(u) if u else ""
	mapping = values.get("item_mapping") or {}
	egp = lambda f: {**f, "when": {"source": "eGP"}}
	missing = intake.get("missing") or []
	supplier_who = existing.supplier_signatory_label(values)
	source_region = [
		kit.fl(kit.sel("Source", _v(values, "source", existing.SOURCES[0]), list(existing.SOURCES), "source"), kit.tx("Source contract reference", _v(values, "reference"), "reference"),
			egp(kit.tx("eGP tender reference", _v(values, "egp_tender_reference"), "egp_tender_reference")), egp(kit.tx("eGP contract reference", _v(values, "egp_contract_reference"), "egp_contract_reference")),
			kit.tx("Supplier's country", _v(values, "supplier_country"), "supplier_country"), kit.tx("Supplier's registration number", _v(values, "supplier_registration"), "supplier_registration"),
			kit.file("Signed agreement", _v(values, "agreement_file"), "agreement_file"), kit.ta("Amendments", _v(values, "amendments", "None"), "amendments"),
			kit.dt("Signed on", _v(values, "signed_on"), "signed_on"), kit.dt("Effective on", _v(values, "effective_on"), "effective_on"),
			{**kit.dt("Cutover", str(_v(values, "cutover"))[:16].replace(" ", "T"), "cutover"), "o": {"time": True}})]
	if missing:
		source_region.append(kit.xh("Still to give: " + ", ".join(existing.LABELS.get(m, m.replace("_", " ")).lower() for m in missing) + "."))
	parties_region = kit.fl(
		kit.pick("Contract owner", _v(values, "owner"), "contracts.person", "owner", {"role": "Contract inspection"}, name(_v(values, "owner")), "contract owner"),
		kit.pick("Managing unit", _v(values, "managing_unit"), "contracts.unit", "managing_unit", {}, _unit_label(_v(values, "managing_unit")), "unit"),
		kit.ro("Supplier signatory", supplier_who), kit.pick("Entity signatory", _v(values, "entity_signatory"), "contracts.person", "entity_signatory", {"role": "Entity contract signing"}, name(_v(values, "entity_signatory")), "signatory"),
		kit.ro("Review regime", "Kenya public procurement — applicability review pending"), kit.tx("Source clause reference", _v(values, "clauses"), "clauses"))
	rows, inputs = _item_rows(lines, intake.get("opening", {}).get("lines", {}) if intake else {}, mapping)
	native = [kit.pick("Supplier in Finance", _v(values, "native_supplier"), "contracts.native_record", "native_supplier", {"kind": "supplier"}, _v(values, "native_supplier"), "supplier"),
		kit.pick("Asset location", _v(values, "asset_location"), "contracts.native_record", "asset_location", {"kind": "location"}, _v(values, "asset_location"), "location")]
	for line in lines:
		native.append(kit.pick(f"Catalogue item for {line.get('description')}", mapping.get(line["line_id"], ""), "contracts.native_record", f"item_mapping.{line['line_id']}", {"kind": "item"}, mapping.get(line["line_id"], ""), "item"))
	days, warranty = _v(values, "payment_days"), _v(values, "warranty_months")
	links = (op.get("links") or {}) if op else {}
	picks = lambda label, key, kind: {**kit.pick(label, links.get(key, ""), "contracts.native_record", f"link_{key}", {"kind": kind}, links.get(key, ""), kind.replace("_", " ")), "when": {"prior_activity": "Some"}}
	money_field = lambda label, key: {**kit.tx(label, "" if op.get(key) is None else f"{op.get(key):g}", f"opening_{key}"), "when": {"prior_activity": "Some"}}
	regions = [
		kit.R("Source", *source_region),
		kit.R("Parties and ownership", parties_region),
		kit.R("Value and items", kit.fl(kit.tx("Original value", _num(values.get("original_value")), "original_value"), kit.tx("Current value", _num(values.get("current_value")), "current_value"), kit.ro("Currency", "KES", "currency")),
			kit.t(ITEM_COLS, rows, inputs=inputs), kit.fl(*native), kit.xh("Fill one row for each item; leave the opening columns blank for a figure that is not established.")),
		kit.R("Operative terms", kit.fl(kit.dt("Delivery", _v(values, "delivery_due"), "delivery_due"), kit.tx("Payment days", _num(values.get("payment_days")), "payment_days"), kit.tx("Warranty months", _num(values.get("warranty_months")), "warranty_months"),
			kit.sel("Advance provided", _v(values, "advance_allowed") or "Select", ["Select", *existing.YES_NO], "advance_allowed"),
			kit.sel("Performance security required", _v(values, "security_required") or "Select", ["Select", *existing.YES_NO], "security_required"), kit.tx("Active restrictions", _v(values, "restrictions"), "restrictions"),
			kit.wide(kit.ta("Acceptance criteria", _v(values, "acceptance"), "acceptance"))),
			kit.r(["Payment", f"Within {days} days of correct invoice and eligible acceptance" if days else "Not yet given"], ["Warranty", f"{warranty} months per accepted unit" if warranty else "Not yet given"],
				["Restrictions", _v(values, "restrictions") or "None recorded"], ["Completion", "After all contractual obligations"]), kit.xh("One acceptance criterion per line: Name | comparison (>=, <=, >, <, =) | value | unit.")),
		kit.R("Opening position", kit.fl(kit.sel("Prior activity", _v(values, "prior_activity") or "Select", ["Select", *existing.ACTIVITY], "prior_activity"), kit.ro("Currency", "KES", "opening_currency"), money_field("Invoiced (KES)", "invoiced"),
			money_field("Credits (KES)", "credits"), money_field("Confirmed cash paid (KES)", "cash_paid"), money_field("Outstanding (KES)", "outstanding"), money_field("Advance (KES)", "advance"),
			{**kit.wide(kit.ta("Unit references of the goods in custody", "\n".join(op.get("units_in_custody", [])) if op else "", "units_in_custody")), "when": {"prior_activity": "Some"}},
			picks("Linked order", "purchase_order", "purchase_order"), picks("Linked receipt", "purchase_receipt", "purchase_receipt"), picks("Linked invoice", "purchase_invoice", "purchase_invoice"),
			picks("Linked payment", "payment_entry", "payment_entry")),
			kit.r(["Linked receipt", links.get("purchase_receipt") or "Not linked"], ["Linked invoice", links.get("purchase_invoice") or "Not linked"], ["Linked payment and settlement", links.get("payment_entry") or "Not linked"]),
			kit.xh("Draft entered facts, not confirmed native balances until Finance review. Unknown values stay blank as Not established.")),
		kit.R("", kit.pv("View source clauses", [[_v(values, "clauses") or "Not yet given", "Locators for the values above"]], False))]
	title = "Register existing contract"
	if ctx is None:
		board = kit.board(id="D12", d="D12", name="Existing contract", title=title, ref="", sub="", st="Preparing", tab="Agreement", back="Back to contracts", case="", version=0, regions=regions, p="Save and review", s2=["Cancel"], ev=[],
			next=kit.turn("Record the signed contract and its current position.", name(user)))
	else:
		board = chrome.base(ctx, "D12", d="D12", name="Existing contract", title=title, tab="Agreement", next=chrome.next_block(ctx) or kit.turn("Record the signed contract and its current position.", name(user)), regions=regions,
			p="Save and review", s2=["Cancel"], ev=[])
	board["actions"]["Save and review"] = kit.command("ReviseContractIntake" if case else "RegisterExistingContract")
	board["actions"]["Cancel"] = kit.route() if not case else kit.tab("Agreement")
	return board


def _fmt(row: dict) -> tuple[str, str]:
	f = (lambda v: "Not linked" if v is None else (f"{v:g}" if row["kind"] == "quantity" else money(v)))
	native = f"Custody record {row['native']:g}" if row["measure"] == "In custody" and row["native"] is not None else f(row["native"])
	return f(row["source"]), native


def d21(ctx: Context) -> dict:
	"""Review prior activity (Finance approval): the source's opening figures against the linked native records."""
	current = existing.stored(ctx.case)
	intake = current["intake"]
	rows = opening.reconcile(intake["opening"], len(intake["opening"].get("units_in_custody", [])))
	differing = [r["measure"] for r in rows if not r["match"]]
	table = kit.t(["Fact", "Source", "Native linked"], [[r["measure"], *_fmt(r)] for r in rows], num=(1, 2))
	next_ = chrome.next_block(ctx)
	if differing and ctx.mine("ConfirmOpeningPosition"):
		next_ = kit.blk("The source and the linked records differ.", ctx.name(ctx.user), ["Report difference"], "; ".join(differing))
	board = chrome.base(ctx, "D21", d="D21", name="Opening position", title="Review prior activity", tab="Invoices", next=next_, regions=[kit.R("Opening comparison", table)], p="" if differing else "Confirm opening position",
		s2=[kit.disabled("Report difference")], ev=[])
	if not differing:
		board["actions"]["Confirm opening position"] = kit.command("ConfirmOpeningPosition")
	return board


def d21h(ctx: Context) -> dict:
	"""Start managing this contract (the head of procurement)."""
	current = existing.stored(ctx.case)
	intake = current["intake"]
	prior = opening.prior_activity(intake["opening"])
	finance = intake["confirmations"].get("finance")
	custody = sum(int(v.get("in_custody") or 0) for v in intake["opening"]["lines"].values())
	facts = kit.r(["Source and terms", "To confirm when management starts"], ["Opening position", "Confirmed" if finance else ("No prior activity" if not prior else "Not yet confirmed")],
		["Next work", f"Inspect {custody} units in custody" if custody else "Recommend the inspectors"])
	board = chrome.base(ctx, "D21-H", d="D21", name="Opening position", title="Start managing this contract", tab="Agreement", next=chrome.next_block(ctx), regions=[kit.R("Intake", facts)], p="Start management",
		s2=["View source contract"], ev=[])
	board["actions"]["Start management"] = kit.command("StartContractManagement")
	board["actions"]["View source contract"] = kit.route(ctx.case, "agreement", "intake")
	return board
