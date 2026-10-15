# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Registering a contract that was signed before KenTender (CM-CHG-001 v0.8 sections 5.13, 7; boards D12, D21, D21-H; plan Phase 5, tracker CM8-508).

An authorised preparer records the executed contract and where it stands (**Register**), revises it as findings come (**Revise**, which voids every confirmation), Finance confirms the opening
position against the native records it is linked to (**Confirm opening position**), and the head of procurement confirms the source and terms and **starts management**. Nothing is signed again, no
tender, bid, evaluation or award is invented, and nothing historical is posted: the history is an opening position the rest of the module reads as a starting offset (`opening.py`).

* A stable unique key (site, origin system, external contract identity) prevents a second case for the same contract.
* Saving is always possible while incomplete; what is still missing is named, and starting is refused until it is given.
* An unknown figure stays unknown. A contract with no prior activity says so, and has zero opening balances.
* The terms are stored in the same shape as a formed agreement's, so delivery, inspection and invoices work on a registered contract exactly as on any other.
* The external agreement stays authoritative for its terms; the evidence is recorded as coming from an external source, never as verified by an e-procurement system."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe.utils import cint, cstr, flt, get_datetime, getdate

from kentender_contracts.native import adapter
from kentender_contracts.services import authority, clock, events, evidence, formation, intents, opening, parties, people, preflight, records, security, service_principal, simulation, work
from kentender_contracts.services.errors import fail, invalid
from kentender_core.services import supplier_account_contract

CASE = "Contract Case"
AGREEMENT = "Contract Agreement Version"
ARRIVAL = "Contract Arrival"
SOURCES = ("External records", "eGP")
YES_NO = ("Yes", "No")
ACTIVITY = ("None", "Some")
TAX = ("Included", "Excluded")
COMPARATORS = (">=", "<=", ">", "<", "=")
LABELS = {
	"source": "Source", "reference": "Source contract reference", "supplier": "Supplier", "agreement_file": "Signed agreement", "signed_on": "Signed on", "effective_on": "Effective on", "cutover": "Cutover",
	"current_value": "Current value", "original_value": "Original value", "items": "Items", "delivery_due": "Delivery due", "payment_days": "Payment days", "warranty_months": "Warranty months",
	"acceptance": "Acceptance criteria", "security_required": "Whether a performance security is required", "advance_allowed": "Whether an advance is provided", "owner": "Contract owner",
	"managing_unit": "Managing unit", "entity_signatory": "Entity signatory", "supplier_signatory": "Supplier signatory", "prior_activity": "Prior activity", "clauses": "Source clause reference",
	"item_mapping": "Catalogue item for each line", "native_supplier": "Supplier in Finance", "asset_location": "Asset location", "egp_tender_reference": "eGP tender reference",
	"egp_contract_reference": "eGP contract reference", "units_in_custody": "Unit references of the goods in custody", "opening": "The opening figures",
}
PRIVATE = {"agreement_file"}


def profile_id() -> str:
	return "SYNTHETIC-ILLUSTRATIVE" if simulation.enabled() else "KE-PPADA-2015"


def origin_key(source: str, reference: str) -> str:
	"""Site, origin system and external contract identity (the site is the database this key lives in)."""
	reference = re.sub(r"\s+", " ", cstr(reference).strip()).lower()
	return f"{cstr(source).strip().lower()}|{reference}"


def _preparer(actor: str, unit: str = "") -> None:
	"""A person who prepares contracts for the unit, or, before a unit is chosen, anywhere (the unit is one of the facts still to give)."""
	if unit:
		preflight.acts_as_preparer(actor, unit)
		return
	from kentender_contracts.services import picker_sources

	if not picker_sources.preparing_units(actor):
		fail("CM_AUTHORITY", missing="responsibility", responsibility="Contract preparation", provisioned_by="System setup, by a System Manager")


def _entity_name() -> str:
	return cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_name")) or "The procuring entity"


def _entity_type() -> str:
	return cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_type")) if frappe.get_meta("Site Procuring Entity").has_field("pe_type") else ""


def _number(value: Any, label: str, problems: dict[str, str], key: str, *, minimum: float = 0.0, integer: bool = False, required_positive: bool = False) -> float | None:
	text = cstr(value).replace(",", "").strip()
	if not text:
		return None
	try:
		number = float(text)
	except ValueError:
		problems[key] = f"Enter {label.lower()} as a number."
		return None
	if integer and number != int(number):
		problems[key] = f"Enter {label.lower()} as a whole number."
	elif number < minimum or (required_positive and number <= 0):
		problems[key] = f"{label} must be {'above zero' if required_positive else 'zero or more'}."
	return number


def _items(text: str, problems: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
	"""One item per line: `Description | Quantity | UOM | Rate | Included or Excluded | Accepted | In custody | Invoiced quantity` (the last three are the opening position; blank means not established)."""
	lines, opening_lines = [], {}
	for number, raw in enumerate([r for r in cstr(text).splitlines() if r.strip()], start=1):
		parts = [p.strip() for p in raw.split("|")] + [""] * 8
		description, quantity, uom, rate, tax = parts[:5]
		line_id = f"L{number}"
		try:
			qty, price = int(quantity.replace(",", "")), float(rate.replace(",", ""))
		except ValueError:
			problems["items"] = f"Line {number}: enter the quantity as a whole number and the rate as a number."
			continue
		if not description or qty <= 0 or price <= 0 or not uom or tax not in TAX:
			problems["items"] = f"Line {number}: give a description, a quantity and a rate above zero, a unit of measure, and Included or Excluded."
			continue
		if not frappe.db.exists("UOM", uom):
			problems["items"] = f"Line {number}: {uom} is not a unit of measure on this site."
			continue
		extra = {}
		for name, value in zip(("accepted", "in_custody", "invoiced_quantity"), parts[5:8]):
			if value == "":
				extra[name] = None
			elif value.isdigit():
				extra[name] = int(value)
			else:
				problems["items"] = f"Line {number}: {name.replace('_', ' ')} must be a whole number or blank."
		lines.append({"line_id": line_id, "item": description, "description": description, "uom": uom, "quantity": qty, "rate": price, "amount": qty * price, "tax": tax})
		opening_lines[line_id] = extra
	return lines, opening_lines


def _criteria(text: str, lines: list[dict[str, Any]], problems: dict[str, str]) -> list[dict[str, Any]]:
	"""One criterion per line: `Name | comparator | value | unit`. They are the frozen yardstick inspection records against."""
	out = []
	for number, raw in enumerate([r for r in cstr(text).splitlines() if r.strip()], start=1):
		parts = [p.strip() for p in raw.split("|")] + [""] * 4
		name, comparator, value, unit = parts[:4]
		if not name or comparator not in COMPARATORS or value == "":
			problems["acceptance"] = f"Line {number}: give a name, a comparison ({', '.join(COMPARATORS)}) and a value."
			continue
		try:
			typed: Any = float(value) if re.fullmatch(r"-?\d+(\.\d+)?", value) else value
			typed = int(typed) if isinstance(typed, float) and typed == int(typed) else typed
		except ValueError:
			typed = value
		out.append({"id": f"C{number}", "name": name, "comparator": comparator, "value": typed, "unit": unit, "line_id": lines[0]["line_id"] if len(lines) == 1 else "", "coverage": "every unit"})
	return out


def _supplier(values: dict[str, Any], problems: dict[str, str]) -> dict[str, Any] | None:
	country, registration = cstr(values.get("supplier_country")).strip(), cstr(values.get("supplier_registration")).strip()
	if not country and not registration:
		return None
	provider = supplier_account_contract.provider()
	found = provider.find_active_account(country=country, registration_number=registration) if provider and country and registration else None
	if not found:
		problems["supplier_registration"] = "No active supplier account has this country and registration number."
		return None
	facts = provider.organisation(organisation_id=found["organisation_id"]) or {}
	signatories = provider.organisation_signatories(organisation_id=found["organisation_id"], at=clock.now())
	return {"organisation": found["organisation_id"], "name": found.get("legal_name") or facts.get("legal_name"), "address": facts.get("registered_address", ""), "signatories": [s["user"] for s in signatories]}


def supplier_signatory_label(values: dict[str, Any]) -> str:
	"""Who signs for the supplier, as the supplier's own account names them (read-only on the intake)."""
	signatories = (_supplier({"supplier_country": values.get("supplier_country"), "supplier_registration": values.get("supplier_registration")}, {}) or {}).get("signatories") or []
	return people.full_name(signatories[0]) if signatories else "Not yet known"


def read(values: dict[str, Any], actor: str, *, previous: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Everything given, checked for form. Returns the clean values, the problems with them (a value given wrongly), and what is still missing (a value not given)."""
	values = {**(previous or {}), **{k: v for k, v in (values or {}).items() if v is not None}}
	values = {k: ("" if v == "Select" else v) for k, v in values.items()}  # a select left on its prompt is a value not given
	problems: dict[str, str] = {}
	clean: dict[str, Any] = {"source": cstr(values.get("source")).strip() or SOURCES[0], "reference": cstr(values.get("reference")).strip(), "amendments": cstr(values.get("amendments")).strip() or "None",
		"clauses": cstr(values.get("clauses")).strip(), "restrictions": cstr(values.get("restrictions")).strip(), "egp_tender_reference": cstr(values.get("egp_tender_reference")).strip(),
		"egp_contract_reference": cstr(values.get("egp_contract_reference")).strip(), "supplier_country": cstr(values.get("supplier_country")).strip(), "supplier_registration": cstr(values.get("supplier_registration")).strip(),
		"prior_activity": cstr(values.get("prior_activity")).strip(), "security_required": cstr(values.get("security_required")).strip(), "advance_allowed": cstr(values.get("advance_allowed")).strip(),
		"items": cstr(values.get("items")), "acceptance": cstr(values.get("acceptance")), "units_in_custody": cstr(values.get("units_in_custody")), "agreement_file": cstr(values.get("agreement_file")).strip()}
	if clean["source"] not in SOURCES:
		problems["source"] = "Choose External records or eGP."
	if not clean["reference"]:
		problems["reference"] = "Enter the contract reference as the source gives it."
	for name in ("signed_on", "effective_on"):
		text = cstr(values.get(name)).strip()
		clean[name] = ""
		if text:
			try:
				clean[name] = str(getdate(text))
			except Exception:
				problems[name] = f"Enter {LABELS[name].lower()} as a date."
	if clean["signed_on"] and clean["effective_on"] and not problems and getdate(clean["effective_on"]) < getdate(clean["signed_on"]):
		problems["effective_on"] = "The contract cannot take effect before it was signed."
	text = cstr(values.get("cutover")).strip()
	clean["cutover"] = ""
	if text:
		try:
			clean["cutover"] = str(get_datetime(text))
		except Exception:
			problems["cutover"] = "Enter the cutover as a date and time."
	if clean["cutover"] and clean["effective_on"] and not problems.get("cutover") and get_datetime(clean["cutover"]).date() < getdate(clean["effective_on"]):
		problems["cutover"] = "The cutover cannot be before the contract took effect."
	for name, label in (("original_value", "the original value"), ("current_value", "the current value")):
		number = _number(values.get(name), label, problems, name, required_positive=True)
		clean[name] = number
	clean["delivery_due"] = ""
	if cstr(values.get("delivery_due")).strip():
		try:
			clean["delivery_due"] = str(getdate(values.get("delivery_due")))
		except Exception:
			problems["delivery_due"] = "Enter the delivery date as a date."
	clean["payment_days"] = _number(values.get("payment_days"), "the payment days", problems, "payment_days", integer=True, required_positive=True)
	clean["warranty_months"] = _number(values.get("warranty_months"), "the warranty months", problems, "warranty_months", integer=True, required_positive=True)
	for name in ("security_required", "advance_allowed"):
		if clean[name] and clean[name] not in YES_NO:
			problems[name] = "Choose Yes or No."
	if clean["prior_activity"] and clean["prior_activity"] not in ACTIVITY:
		problems["prior_activity"] = "Choose None or Some."
	lines, opening_lines = _items(clean["items"], problems)
	clean["lines"], clean["opening_lines"] = lines, opening_lines
	total = sum(l["amount"] for l in lines)
	if lines and clean["current_value"] and abs(total - clean["current_value"]) > 0.005 and "items" not in problems:
		problems["current_value"] = f"The items come to {total:,.2f}, not {clean['current_value']:,.2f}."
	clean["criteria"] = _criteria(clean["acceptance"], lines, problems)
	if lines and len({l["tax"] for l in lines}) > 1 and "items" not in problems:
		problems["items"] = "Use one tax treatment (Included or Excluded) for every item."
	for name in ("opening_invoiced", "opening_credits", "opening_cash_paid", "opening_outstanding", "opening_advance"):
		clean[name] = _number(values.get(name), LABELS.get(name, name.replace("_", " ")), problems, name)
	clean["links"] = {k: cstr(values.get(f"link_{k}")).strip() for k in ("purchase_order", "purchase_receipt", "purchase_invoice", "payment_entry")}
	for key, doctype in (("purchase_order", "Purchase Order"), ("purchase_receipt", "Purchase Receipt"), ("purchase_invoice", "Purchase Invoice"), ("payment_entry", "Payment Entry")):
		if clean["links"][key] and not frappe.db.exists(doctype, clean["links"][key]):
			problems[f"link_{key}"] = f"{doctype} {clean['links'][key]} does not exist."
	supplier = _supplier(values, problems)
	clean["supplier"] = supplier
	for name in ("owner", "entity_signatory"):
		clean[name] = cstr(values.get(name)).strip()
		if clean[name] and not frappe.db.exists("User", clean[name]):
			problems[name] = "Choose a person with an account."
	if clean["entity_signatory"] and not problems.get("entity_signatory") and not people.holds(clean["entity_signatory"], "Entity contract signing"):
		problems["entity_signatory"] = "This person does not hold the Entity contract signing responsibility."
	clean["managing_unit"] = cstr(values.get("managing_unit")).strip()
	if clean["managing_unit"]:
		if not frappe.db.exists("Organisation Unit", clean["managing_unit"]):
			problems["managing_unit"] = "Choose an existing unit."
		else:
			try:
				_preparer(actor, clean["managing_unit"])
			except Exception:
				problems["managing_unit"] = "You do not prepare contracts for this unit."
	mapping = {k.split(".", 1)[1]: cstr(v).strip() for k, v in values.items() if cstr(k).startswith("item_mapping.") and cstr(v).strip()}
	if isinstance(values.get("item_mapping"), dict):
		mapping.update({k: cstr(v).strip() for k, v in values["item_mapping"].items() if cstr(v).strip()})
	bad = [k for k, v in mapping.items() if not frappe.db.exists("Item", v)]
	if bad:
		problems["item_mapping"] = "Choose an existing catalogue item for " + ", ".join(bad) + "."
	clean["item_mapping"] = mapping
	for name, doctype in (("native_supplier", "Supplier"), ("asset_location", "Location")):
		clean[name] = cstr(values.get(name)).strip()
		if clean[name] and not frappe.db.exists(doctype, clean[name]):
			problems[name] = f"Choose an existing {doctype.lower()}."
	return {"clean": clean, "problems": problems, "missing": _missing(clean, supplier)}


def _missing(clean: dict[str, Any], supplier: dict[str, Any] | None) -> list[str]:
	need = []
	checks = [("reference", clean["reference"]), ("supplier", supplier), ("agreement_file", clean["agreement_file"]), ("signed_on", clean["signed_on"]), ("effective_on", clean["effective_on"]),
		("cutover", clean["cutover"]), ("original_value", clean["original_value"]), ("current_value", clean["current_value"]), ("items", clean["lines"]), ("delivery_due", clean["delivery_due"]),
		("payment_days", clean["payment_days"]), ("warranty_months", clean["warranty_months"]), ("acceptance", clean["criteria"]), ("security_required", clean["security_required"]),
		("advance_allowed", clean["advance_allowed"]), ("owner", clean["owner"]), ("managing_unit", clean["managing_unit"]), ("entity_signatory", clean["entity_signatory"]),
		("prior_activity", clean["prior_activity"]), ("clauses", clean["clauses"])]
	if clean["source"] == "eGP":
		checks += [("egp_tender_reference", clean["egp_tender_reference"]), ("egp_contract_reference", clean["egp_contract_reference"])]
	need += [k for k, v in checks if not v]
	if supplier and not supplier["signatories"]:
		need.append("supplier_signatory")
	if clean["lines"] and not all(clean["item_mapping"].get(l["line_id"]) for l in clean["lines"]):
		need.append("item_mapping")
	elif clean["lines"] and not clean["asset_location"] and any(formation._creates_assets(code) for code in clean["item_mapping"].values()):
		need.append("asset_location")
	if not clean["native_supplier"]:
		need.append("native_supplier")
	if clean["prior_activity"] == "Some":
		for name in ("opening_invoiced", "opening_credits", "opening_cash_paid", "opening_outstanding", "opening_advance"):
			if clean[name] is None:
				need.append(name)
		if any(v is None for line in clean["opening_lines"].values() for v in line.values()):
			need.append("opening")
		if sum(cint((line or {}).get("in_custody")) for line in clean["opening_lines"].values()) and len([u for u in clean["units_in_custody"].splitlines() if u.strip()]) != sum(cint((line or {}).get("in_custody")) for line in clean["opening_lines"].values()):
			need.append("units_in_custody")
	elif clean["prior_activity"] == "None" and any(v for line in clean["opening_lines"].values() for v in line.values()):
		need.append("opening")
	return list(dict.fromkeys(need))


def _opening(clean: dict[str, Any]) -> dict[str, Any]:
	some = clean["prior_activity"] == "Some"
	lines = {lid: {k: (v if v is not None else (0 if not some else None)) for k, v in extra.items()} for lid, extra in clean["opening_lines"].items()}
	return {"prior_activity": clean["prior_activity"], "lines": lines, "invoiced": clean["opening_invoiced"] if some else 0.0, "credits": clean["opening_credits"] if some else 0.0,
		"cash_paid": clean["opening_cash_paid"] if some else 0.0, "outstanding": clean["opening_outstanding"] if some else 0.0, "advance": clean["opening_advance"] if some else 0.0,
		"units_in_custody": [u.strip() for u in clean["units_in_custody"].splitlines() if u.strip()] if some else [], "links": clean["links"]}


def _consistent(clean: dict[str, Any], problems: dict[str, str]) -> None:
	"""The opening position cannot exceed what the contract allows, and its own figures must agree."""
	if clean["prior_activity"] != "Some":
		return
	lines = {l["line_id"]: l for l in clean["lines"]}
	paid_up = 0.0
	for lid, extra in clean["opening_lines"].items():
		line = lines.get(lid)
		accepted, custody, billed = (extra.get(k) for k in ("accepted", "in_custody", "invoiced_quantity"))
		if line and accepted is not None and custody is not None and accepted + custody > line["quantity"]:
			problems["items"] = f"Line {lid[1:]}: accepted and in custody ({accepted + custody}) are more than the quantity ({line['quantity']})."
		if accepted is not None and billed is not None and billed > accepted:
			problems["items"] = f"Line {lid[1:]}: more units are invoiced ({billed}) than accepted ({accepted})."
		if line and billed is not None:
			paid_up += billed * line["rate"]
	invoiced, credits, cash, outstanding = (clean[k] for k in ("opening_invoiced", "opening_credits", "opening_cash_paid", "opening_outstanding"))
	if invoiced is not None and all(v.get("invoiced_quantity") is not None for v in clean["opening_lines"].values()) and abs(invoiced - paid_up) > 0.005:
		problems["opening_invoiced"] = f"The invoiced quantities at the contract rate come to {paid_up:,.2f}, not {invoiced:,.2f}."
	if None not in (invoiced, credits, cash, outstanding) and abs((invoiced - credits - cash) - outstanding) > 0.005:
		problems["opening_outstanding"] = f"Invoiced less credits less cash paid is {invoiced - credits - cash:,.2f}, not {outstanding:,.2f}."
	if None not in (invoiced, credits) and credits > invoiced:
		problems["opening_credits"] = "Credits cannot be more than what was invoiced."


def _terms(clean: dict[str, Any]) -> dict[str, Any]:
	supplier = clean["supplier"] or {}
	signatory = (supplier.get("signatories") or [""])[0]
	return {
		"title": clean["reference"], "currency": "KES", "tax_included": all(l["tax"] == "Included" for l in clean["lines"]) if clean["lines"] else True, "total": clean["current_value"] or 0, "lines": clean["lines"],
		"delivery": {"due": clean["delivery_due"], "destination": ""}, "warranty": {"months": cint(clean["warranty_months"]), "from": "each unit's acceptance"},
		"security": {"required": clean["security_required"] == "Yes", "statement": "Required by the executed contract" if clean["security_required"] == "Yes" else "Not required by the executed contract"},
		"advance": {"allowed": clean["advance_allowed"] == "Yes"}, "payment": {"basis": "certified invoice for accepted units", "days": cint(clean["payment_days"]), "terms": f"within {cint(clean['payment_days'])} days of a correct invoice and eligible acceptance"},
		"criteria": clean["criteria"], "signing_window": {}, "funding": {"external": True}, "restrictions": [r.strip() for r in clean["restrictions"].replace(";", "\n").splitlines() if r.strip() and r.strip().lower() != "none"],
		"parties": {"entity": {"name": _entity_name(), "address": "", "entity_type": _entity_type(), "user": clean["entity_signatory"], "signatory": people.full_name(clean["entity_signatory"]) if clean["entity_signatory"] else "",
			"capacity": "Entity signatory"}, "supplier": {"name": supplier.get("name", ""), "organisation": supplier.get("organisation", ""), "user": signatory,
			"signatory": people.full_name(signatory) if signatory else "", "capacity": "Authorised signatory"}},
		"particulars": {"agreement_date": clean["signed_on"], "entity_signatory": clean["entity_signatory"], "native_supplier": clean["native_supplier"], "item_mapping": clean["item_mapping"],
			"asset_location": clean["asset_location"]},
		"origin": {"source": clean["source"], "reference": clean["reference"], "evidence": "Recorded from external source"},
	}


def stored(case: str) -> dict[str, Any]:
	"""The draft (or in-force) agreement of a registered contract and the values it was registered from."""
	agreement = frappe.get_doc(AGREEMENT, frappe.db.get_value(AGREEMENT, {"contract_case": case}, "name", order_by="version_no desc"))
	return {"agreement": agreement, "intake": records.loads(agreement.intake_json)}


def _apply(doc, agreement, parsed: dict[str, Any], actor: str, *, evidence_record: dict[str, Any] | None, revision: int) -> dict[str, Any]:
	clean = parsed["clean"]
	terms = _terms(clean)
	intake = records.loads(agreement.intake_json) if agreement is not None else {}
	history = intake.get("history", [])
	raw = {k: v for k, v in clean.items() if k not in ("lines", "opening_lines", "supplier", "criteria", "links")}
	raw.update({"supplier_country": clean["supplier_country"], "supplier_registration": clean["supplier_registration"], "links": clean["links"]})
	new = {"revision": revision, "values": raw, "opening": _opening(clean), "evidence": evidence_record or intake.get("evidence"), "missing": parsed["missing"], "confirmations": {}, "history": history,
		"digest": records.digest({"terms": terms, "opening": _opening(clean), "evidence": (evidence_record or intake.get("evidence") or {}).get("digest")})}
	if intake:
		history.append({"revision": intake.get("revision"), "digest": intake.get("digest"), "by": actor, "at": str(clock.now())})
	fields = {"amount": terms["total"], "currency": "KES", "operative_date": clean["effective_on"] or None, "terms_json": records.dumps(terms), "items_json": records.dumps(clean["lines"]),
		"missing_json": records.dumps(parsed["missing"]), "intake_json": records.dumps(new), "rendered_html": "", "rendered_digest": new["digest"]}
	if agreement is None:
		agreement = records.new(AGREEMENT, contract_case=doc.name, version_no=1, state="Draft", record_version=1, **fields)
	else:
		records.update(agreement, **fields, record_version=cint(agreement.record_version) + 1)
	supplier = clean["supplier"] or {}
	records.bump(doc, title=clean["reference"], supplier_organisation=supplier.get("organisation") or doc.supplier_organisation, supplier_name=supplier.get("name") or doc.supplier_name, currency="KES",
		contract_value=clean["current_value"] or 0, responsible_user=clean["owner"] or doc.responsible_user, managing_unit=clean["managing_unit"] or doc.managing_unit, current_agreement=agreement.version_no,
		intake_revision=revision, legal_profile=profile_id())
	return {"agreement": agreement, "missing": parsed["missing"], "intake": new}


def _tasks(case: str, agreement, intake: dict[str, Any], actor: str) -> None:
	"""The preparer is asked to finish the intake while facts are missing; once complete Finance is asked to confirm the opening position (when there was prior activity) and the head of procurement to start."""
	subject = f"intake {intake['revision']}"
	work.finish(case, state="Superseded", actor=actor)
	if intake["missing"]:
		work.assign(case, "ReviseContractIntake", "Record the signed contract and its current position.", subject, intake["revision"], [actor], role="Contract preparation")
		return
	if opening.prior_activity(intake["opening"]):
		work.assign(case, "ConfirmOpeningPosition", "Confirm the opening position.", subject, intake["revision"], work.holders("Finance approval"), role="Finance approval")
		work.assign(case, work.waiting_command("StartContractManagement", "finance"), "Waiting for Finance to confirm the opening position.", subject, intake["revision"], work.holders(work.HOP), role=work.HOP, state="Waiting")
	else:
		work.assign(case, "StartContractManagement", "Start managing this contract.", subject, intake["revision"], work.holders(work.HOP), role=work.HOP)


def register_existing_contract(*, idempotency_key: str, actor: str, values: dict[str, Any]) -> dict[str, Any]:
	"""`RegisterExistingContract`: one draft case, the executed agreement as evidence and the review findings; no ledger effect."""
	def body() -> dict[str, Any]:
		parsed = read(values, actor)
		clean = parsed["clean"]
		_preparer(actor, clean["managing_unit"])
		problems = dict(parsed["problems"])
		if not clean["reference"]:
			problems.setdefault("reference", "Enter the contract reference as the source gives it.")
		if not clean["supplier"]:
			problems.setdefault("supplier_registration", "Name the supplier by country and registration number.")
		_consistent(clean, problems)
		invalid(problems)
		key = origin_key(clean["source"], clean["reference"])
		same = frappe.db.get_value(CASE, {"origin_key": key}, ["name", "contract_id"], as_dict=True)
		if same:
			fail("CM_DUPLICATE", contract=same.name, reference=same.contract_id, reason="This contract is already registered.")
		held = evidence.checked(clean["agreement_file"], actor, field="agreement_file", required=False)
		doc = records.new(CASE, contract_id=formation._next_contract_id(), source_kind="External record", source_reference=clean["reference"], origin_key=key, source_system=clean["source"], lifecycle="Preparing",
			received_at=clock.now(), record_version=1, supplier_organisation=(clean["supplier"] or {}).get("organisation"), supplier_name=(clean["supplier"] or {}).get("name"), legal_profile=profile_id())
		applied = _apply(doc, None, parsed, actor, evidence_record=_evidence_of(held), revision=1)
		_tasks(doc.name, applied["agreement"], applied["intake"], actor)
		events.record(doc.name, "Existing contract registered", actor, f"Existing contract {clean['reference']} registered from {clean['source']}.", missing=applied["missing"], digest=applied["intake"]["digest"])
		return records.summary(doc, intake="created", open=doc.name, missing=applied["missing"])

	return records.command("RegisterExistingContract", case="", idempotency_key=idempotency_key, actor=actor, payload={"values": {k: v for k, v in (values or {}).items()}}, body=body)


def _evidence_of(held: dict[str, Any] | None) -> dict[str, Any] | None:
	return {"file": held["file"], "name": held["name"], "digest": held["digest"], "media_type": held["media_type"], "check_result": held["check_result"], "basis": "Recorded from external source"} if held else None


def revise_intake(case: str, *, expected_version: int, idempotency_key: str, actor: str, values: dict[str, Any]) -> dict[str, Any]:
	"""`ReviseContractIntake`: a reviewed successor of the intake. Every confirmation given to the earlier revision is void."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Preparing")
		_require_external(doc)
		current = stored(case)
		agreement, intake = current["agreement"], current["intake"]
		parsed = read(values, actor, previous={**intake["values"], **_flatten_links(intake["values"].get("links", {}))})
		clean = parsed["clean"]
		problems = dict(parsed["problems"])
		_consistent(clean, problems)
		invalid(problems)
		key = origin_key(clean["source"], clean["reference"])
		if key != doc.origin_key and frappe.db.exists(CASE, {"origin_key": key, "name": ["!=", case]}):
			fail("CM_DUPLICATE", reason="Another contract is already registered with this reference.")
		held = evidence.checked(values.get("agreement_file") if values.get("agreement_file") and values.get("agreement_file") != (intake.get("evidence") or {}).get("file") else "", actor, field="agreement_file", required=False)
		applied = _apply(doc, agreement, parsed, actor, evidence_record=_evidence_of(held), revision=cint(doc.intake_revision) + 1)
		records.update(doc, origin_key=key, source_system=clean["source"])
		_tasks(case, applied["agreement"], applied["intake"], actor)
		events.record(case, "Intake revised", actor, f"Intake revision {applied['intake']['revision']} saved; earlier confirmations are void.", missing=applied["missing"], digest=applied["intake"]["digest"])
		return records.summary(doc, missing=applied["missing"], revision=applied["intake"]["revision"])

	return records.command("ReviseContractIntake", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "values": values}, body=body,
		authorise=lambda: _preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or ""))


def _flatten_links(links: dict[str, str]) -> dict[str, str]:
	return {f"link_{k}": v for k, v in (links or {}).items()}


def _require_external(doc) -> None:
	if doc.source_kind != "External record":
		fail("CM_CHANGED", reason="This contract did not come from an existing signed contract.")


def confirm_opening_position(case: str, *, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ConfirmOpeningPosition`: Finance confirms that the source's figures agree with the native records they are linked to, for this exact revision."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Preparing")
		_require_external(doc)
		current = stored(case)
		agreement, intake = current["agreement"], current["intake"]
		if intake["missing"]:
			fail("CM_INCOMPLETE", missing=intake["missing"], reason="The intake is not complete.")
		if not opening.prior_activity(intake["opening"]):
			fail("CM_CHANGED", reason="There was no prior activity to confirm.")
		rows = opening.reconcile(intake["opening"], len(intake["opening"].get("units_in_custody", [])))
		differing = [r["measure"] for r in rows if not r["match"]]
		if differing:
			fail("CM_RECONCILE", differing=differing, reason="The source and the linked native records differ: " + ", ".join(differing) + ".")
		intake["confirmations"]["finance"] = {"by": actor, "at": str(clock.now()), "revision": intake["revision"], "rows": rows}
		records.update(agreement, intake_json=records.dumps(intake), record_version=cint(agreement.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="ConfirmOpeningPosition", actor=actor)
		work.assign(case, "StartContractManagement", "Start managing this contract.", f"intake {intake['revision']}", intake["revision"], work.holders(work.HOP), role=work.HOP)
		events.record(case, "Opening position confirmed", actor, "Finance confirmed the opening position.", revision=intake["revision"], rows=rows)
		return records.summary(doc, revision=intake["revision"])

	return records.command("ConfirmOpeningPosition", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version}, body=body,
		authorise=lambda: authority.require(actor, "Finance approval"))


def _blockers(doc, current: dict[str, Any]) -> list[dict[str, Any]]:
	"""Everything that stops management starting, together, each naming who clears it."""
	intake, agreement = current["intake"], current["agreement"]
	terms = records.loads(agreement.terms_json)
	found = []
	if intake["missing"]:
		found.append({"hold": "intake incomplete", "kind": "Rule", "reason": "The intake is missing: " + ", ".join(LABELS.get(m, m.replace("_", " ")).lower() for m in intake["missing"]) + ".", "holder": "Contract preparer",
			"clears_with": "The missing facts are recorded", "consequence": "StartContractManagement"})
	if opening.prior_activity(intake["opening"]) and (intake["confirmations"].get("finance") or {}).get("revision") != intake["revision"]:
		found.append({"hold": "opening position unconfirmed", "kind": "Rule", "reason": "Finance has not confirmed the opening position of this revision.", "holder": "Finance approver",
			"clears_with": "Finance confirms the opening position", "consequence": "StartContractManagement"})
	if terms.get("restrictions"):
		found.append({"hold": "award restriction", "kind": "Restriction", "reason": "An active restriction is recorded on the contract.", "holder": "Head of procurement function", "clears_with": "The restriction is resolved by its owner",
			"consequence": "StartContractManagement"})
	if (terms.get("security") or {}).get("required") and not security.verified(doc.name):
		found.append({"hold": "SECURITY_REQUIRED_NOT_VERIFIED", "kind": "Restriction", "reason": "The performance security the contract requires has not been verified.", "holder": "Head of procurement function",
			"clears_with": "The issuer's confirmation is recorded and the security is verified", "consequence": "StartContractManagement"})
	return found


def start_management(case: str, *, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`StartContractManagement`: the head of procurement confirms the source and terms of this exact revision and the existing agreement becomes Active at its actual effective date. It creates only the
	work that is outstanding and asks nobody to sign again."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Preparing")
		_require_external(doc)
		current = stored(case)
		guards = preflight.rules(doc, "StartContractManagement")
		for finding in _blockers(doc, current):
			guards.add("CM_HOLD", **finding)
		guards.raise_if_any()
		agreement, intake = current["agreement"], current["intake"]
		terms = records.loads(agreement.terms_json)
		effective = get_datetime(intake["values"]["effective_on"])
		intake["confirmations"]["source_and_terms"] = {"by": actor, "at": str(clock.now()), "revision": intake["revision"]}
		records.update(agreement, state="Effective", effective_at=effective, intake_json=records.dumps(intake), record_version=cint(agreement.record_version) + 1)
		records.bump(doc, lifecycle="Active", operative_date=getdate(effective))
		work.finish(case, state="Done", actor=actor)
		subject = f"agreement {agreement.version_no}"
		order = intake["opening"]["links"].get("purchase_order")
		intents.record(case, subject, agreement.version_no, "Purchase order", "effective", recovery_owner="Technical operator")
		units = intake["opening"].get("units_in_custody", [])
		custody = {lid: cint(v.get("in_custody")) for lid, v in intake["opening"]["lines"].items() if cint(v.get("in_custody"))}
		if custody:
			items, cursor = [], 0
			for lid, quantity in custody.items():
				named = units[cursor:cursor + quantity]
				cursor += quantity
				line = next(l for l in terms["lines"] if l["line_id"] == lid)
				items.append({"line_id": lid, "item": line.get("description"), "quantity": quantity, "units": named, "unidentified": quantity - len(named)})
			number = records.next_number(ARRIVAL, {"contract_case": case}, "arrival_no")
			arrival = records.new(ARRIVAL, contract_case=case, arrival_no=number, delivery_reference="Opening position", received_at=get_datetime(intake["values"]["cutover"]), recorded_at=clock.now(), receiver=actor,
				destination="As at cutover", items_json=records.dumps(items), notes="Goods in custody at the cutover, from the opening position.", state="Recorded", record_version=1)
			appointed_to = work.holders(work.HOP)
			work.assign(case, "RecordInspectionObservations", "Inspect the delivery.", f"arrival {number}", 1, appointed_to, role="Contract inspection")
			events.record(case, "Opening custody recorded", actor, f"{sum(custody.values())} units in custody at the cutover were recorded for inspection.", arrival=arrival.name)
		work.assign(case, "RecommendContractInspectors", "Recommend the inspectors for this contract.", subject, agreement.version_no, work.holders(work.HOP), role=work.HOP)
		events.record(case, "Management started", actor, "Management of the existing contract started; nobody is asked to sign it again.", agreement=agreement.name, revision=intake["revision"], order=order or "")
		return records.summary(doc, agreement=agreement.name, order=order or "")

	recorded = records.command("StartContractManagement", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version}, body=body,
		authorise=lambda: authority.require(actor, "Head of Procurement Function"))
	frappe.db.commit()
	_link_or_create_order(case, actor)
	return recorded


def _link_or_create_order(case: str, actor: str) -> None:
	"""The native order: an existing one is linked as the contract's own (never recreated); otherwise the order is created through the same operation-intent route as any other agreement."""
	current = stored(case)
	order = (current["intake"]["opening"].get("links") or {}).get("purchase_order")
	if not order:
		formation.carry_out_effects(case, actor)
		return
	agreement = current["agreement"]
	name = frappe.db.get_value(intents.INTENT, {"contract_case": case, "operation_kind": "Purchase order", "subject": f"agreement {agreement.version_no}"}, "name")
	if name:
		intents.execute(name, lambda identity: (order, "Purchase Order"), lambda identity: order, native_doctype="Purchase Order")
		frappe.db.commit()
