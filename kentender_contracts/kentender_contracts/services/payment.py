# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Invoices, certification, Finance and settlement (CM-CHG-001 v0.8 sections 5.8, 5.12, 6.1, 7; plan Phase 4).

* **Claim.** The supplier submits an invoice against the contract once. Every line is matched automatically with what the contract supports -- the accepted, received and not yet claimed units, the
  contract price, the remaining contractual amount -- and each discrepancy is recorded with its reason. A claim that matches is **Submitted** and gets its native Purchase Invoice (through the
  operation-intent model, from the receipt that carries the accepted units); one that does not is **Held** for review and a linked successor claim corrects it, so the original receipt time is never reset.
* **Certification.** Procurement's personal proof freezes the contractual support of one invoice (the exact matching, the exact acceptance it rests on). An acceptance-report signer cannot certify a claim
  that acceptance supports (CM-OD-09). The certified amount is the ceiling the native payment guard enforces; nothing else lets a payment through.
* **Finance.** A Finance maker prepares the native payment; a different person with Finance approval approves it through the native workflow inside the controlled operation. The guard rechecks the
  entitlement under a lock when it posts.
* **Settlement.** A posted payment is not a settled one: an independent Finance person confirms it with attributable evidence. A partly settled invoice is Partly paid."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, flt, getdate

from kentender_contracts.native import adapter, payment_guard
from kentender_contracts.services import adjustment, advance, authority, clock, delivery, events, formation, holds, intents, opening, parties, people, position, preflight, records, segregation, service_principal, signing_flow, work
from kentender_contracts.services import errors
from kentender_contracts.services.errors import fail, invalid

CASE = "Contract Case"
INVOICE = "Contract Invoice"
CERTIFICATION = "Contract Certification"
SETTLEMENT = "Contract Settlement"
TOLERANCE = 0.005
ACTIVE_INVOICE = ["not in", ["Superseded", "Set aside"]]


def _terms(case: str) -> dict[str, Any]:
	return records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective"}, "terms_json", order_by="version_no desc"))


def _claimed(case: str, exclude: str = "") -> dict[str, int]:
	"""Quantity already claimed per line by claims that still stand (a superseded claim no longer holds its entitlement)."""
	out: dict[str, int] = {}
	for row in frappe.get_all(INVOICE, filters={"contract_case": case, "state": ACTIVE_INVOICE, "name": ["!=", exclude]}, fields=["lines_json"]):
		for line in records.loads(row.lines_json, []):
			out[line["line_id"]] = out.get(line["line_id"], 0) + cint(line["quantity"])
	for lid in (opening.of(case).get("lines") or {}):  # what a registered existing contract had already claimed before management started
		out[lid] = out.get(lid, 0) + opening.line(case, lid)["invoiced_quantity"]
	return out


def _claimed_on_receipts(case: str, exclude: str = "") -> dict[str, int]:
	out: dict[str, int] = {}
	for row in frappe.get_all(INVOICE, filters={"contract_case": case, "state": ACTIVE_INVOICE, "name": ["!=", exclude]}, fields=["lines_json"]):
		for line in records.loads(row.lines_json, []):
			if line.get("receipt"):
				out[line["receipt"]] = out.get(line["receipt"], 0) + cint(line["quantity"])
	return out


def _receipt_qty(receipt: str) -> int:
	return cint(sum(flt(q) for q in frappe.get_all("Purchase Receipt Item", filters={"parent": receipt}, pluck="qty")))


HOP_HOLDER, FINANCE_HOLDER = "Head of procurement function", "Finance"


def _finding(kind: str, reason: str, holder: str, line_id: str = "") -> dict[str, str]:
	"""One discrepancy: what differs, why, and who must act on it (the supplier corrects through the head of procurement; Finance reconciles what only the ledger can)."""
	return {"kind": kind, "reason": reason, "holder": holder, "line_id": line_id}


def apparent_duplicate(case: str, claim_reference: str, lines: list[dict[str, Any]], invoice_date: str, *, exclude: str = "") -> str:
	"""The invoice this one appears to repeat: the same supplier invoice number, or the same lines on the same invoice date. A claim of the same quantity on another day is a separate legitimate claim."""
	wanted = sorted((cstr(l["line_id"]), cint(l["quantity"])) for l in lines)
	for row in frappe.get_all(INVOICE, filters={"contract_case": case, "state": ACTIVE_INVOICE, "name": ["!=", exclude or ""]}, fields=["name", "claim_reference", "invoice_date", "lines_json"]):
		if cstr(row.claim_reference).strip().lower() == cstr(claim_reference).strip().lower():
			return row.name
		if cstr(row.invoice_date) == cstr(getdate(invoice_date)) and sorted((cstr(l["line_id"]), cint(l["quantity"])) for l in records.loads(row.lines_json, [])) == wanted:
			return row.name
	return ""


def match_claim(case: str, lines: list[dict[str, Any]], *, exclude: str = "", duplicate_of: str = "") -> dict[str, Any]:
	"""Compare a claim with what the contract supports. Returns the frozen matching: a row per line, a finding for each discrepancy (kind, reason and who acts on it) and an overall outcome
	(`Supported` or `Needs review`). Price, tax treatment, accepted eligible quantity, previous claims, the receipt that carries the units and the remaining contractual amount are each compared."""
	terms = _terms(case)
	ordered = {l["line_id"]: l for l in terms["lines"]}
	services = delivery.service_lines(terms)
	now = position.position(case)["lines"]
	claimed = _claimed(case, exclude)
	on_receipt = _claimed_on_receipts(case, exclude)
	receipts = delivery.posted_receipts(case)
	carried = (opening.of(case).get("links") or {}).get("purchase_receipt")  # the existing contract's own receipt carries the units accepted before management started
	if carried:
		receipts = [carried, *receipts]
		on_receipt[carried] = on_receipt.get(carried, 0) + sum(opening.line(case, lid)["invoiced_quantity"] for lid in (opening.of(case).get("lines") or {}))
	rows, findings = [], []
	value = flt(terms["total"])
	previous_amount = opening.invoiced(case) + sum(flt(r) for r in frappe.get_all(INVOICE, filters={"contract_case": case, "state": ACTIVE_INVOICE, "name": ["!=", exclude]}, pluck="claimed_amount"))
	if duplicate_of:
		findings.append(_finding("Duplicate", f"This appears to repeat invoice {frappe.db.get_value(INVOICE, duplicate_of, 'claim_reference') or duplicate_of}.", FINANCE_HOLDER))
	for line in lines:
		contract = ordered.get(line["line_id"])
		quantity, rate = cint(line["quantity"]), flt(line.get("rate") if line.get("rate") not in (None, "") else (contract or {}).get("rate"))
		problems: list[dict[str, str]] = []
		if contract is None:
			problems.append(_finding("Line", "This line is not in the contract.", HOP_HOLDER, line["line_id"]))
			rows.append({"line_id": line["line_id"], "claimed_quantity": quantity, "eligible_quantity": 0, "claimed_rate": rate, "contract_rate": None, "amount": quantity * rate, "previously_claimed": 0, "receipt": "",
				"outcome": "Needs review", "reasons": [p["reason"] for p in problems], "findings": problems})
			findings += problems
			continue
		eligible = max(0, now[line["line_id"]]["accepted"] - claimed.get(line["line_id"], 0))
		if quantity <= 0:
			problems.append(_finding("Quantity", "The quantity must be above zero.", HOP_HOLDER, line["line_id"]))
		if quantity > eligible:
			problems.append(_finding("Quantity", f"{quantity} claimed but only {eligible} accepted and unclaimed.", HOP_HOLDER, line["line_id"]))
		if abs(rate - flt(contract["rate"])) > TOLERANCE:
			problems.append(_finding("Price", f"The price {rate:,.2f} differs from the contract price {flt(contract['rate']):,.2f}.", HOP_HOLDER, line["line_id"]))
		claimed_tax = line.get("tax_included")
		if claimed_tax not in (None, "") and bool(cint(claimed_tax)) != bool(terms.get("tax_included")):
			problems.append(_finding("Tax", f"The invoice is {'inclusive' if cint(claimed_tax) else 'exclusive'} of tax; the contract price is {'inclusive' if terms.get('tax_included') else 'exclusive'}.", HOP_HOLDER, line["line_id"]))
		room = {r: _receipt_qty(r) - on_receipt.get(r, 0) for r in receipts}
		receipt = min((r for r in receipts if room[r] >= quantity), key=lambda r: room[r], default="") if line["line_id"] not in services else ""  # the receipt with the least room that still carries the claim, so a small claim does not use up the room a later, larger one needs; a service is received into nothing: its entitlement is the acceptance itself
		if quantity > 0 and quantity <= eligible and not receipt and line["line_id"] not in services:
			problems.append(_finding("Receipt", "The claim spans more than one receipt.", FINANCE_HOLDER, line["line_id"]))
		rows.append({"line_id": line["line_id"], "claimed_quantity": quantity, "eligible_quantity": eligible, "claimed_rate": rate, "contract_rate": flt(contract["rate"]), "amount": quantity * rate,
			"previously_claimed": claimed.get(line["line_id"], 0), "receipt": receipt, "outcome": "Needs review" if problems else "Supported", "reasons": [p["reason"] for p in problems], "findings": problems})
		findings += problems
	amount = sum(r["amount"] for r in rows)
	remaining = value - previous_amount
	over = amount > remaining + TOLERANCE
	if over:
		findings.append(_finding("Remaining amount", f"{amount:,.2f} is more than the {max(remaining, 0):,.2f} still open under the contract.", HOP_HOLDER))
	return {"rows": rows, "amount": amount, "previous_claims": previous_amount, "contract_value": value, "remaining_contractual": remaining, "duplicate_of": duplicate_of, "findings": findings,
		"outcome": "Needs review" if over or duplicate_of or any(r["outcome"] != "Supported" for r in rows) else "Supported", "exceeds_remaining": over}


def _claim_authority(case: str, actor: str) -> None:
	organisation = frappe.db.get_value(CASE, case, "supplier_organisation")
	segregation.supplier_signs_only_as_signatory(actor, signatories=parties.signatories(organisation, clock.now()), representatives=parties.representatives(organisation, clock.now()), action="claim")


def _claim_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
	clean = [{"line_id": cstr(l.get("line_id")), "quantity": cint(l.get("quantity")), "rate": l.get("rate"), **({"tax_included": l["tax_included"]} if l.get("tax_included") not in (None, "") else {})} for l in lines or []]
	invalid({"lines": "" if clean and all(l["line_id"] for l in clean) else "Name the lines and quantities you are claiming."})
	invalid({"lines": "" if len(clean) == 1 else "Claim one line on each invoice: the goods and a service are invoiced separately."})
	return clean


def submit_invoice(case: str, *, expected_version: int, idempotency_key: str, actor: str, claim_reference: str, invoice_date: str, lines: list[dict[str, Any]], successor_of: str = "", reason: str = "") -> dict[str, Any]:
	"""`SubmitContractInvoice` / `CorrectContractInvoice` (with `successor_of`): record the claim and its automatic matching; a supported claim then gets its native invoice."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active", "Terminated")  # what was accepted before a termination can still be claimed
		invalid({"claim_reference": "" if cstr(claim_reference).strip() else "Enter your invoice number.", "invoice_date": "" if cstr(invoice_date).strip() else "Enter the invoice date."})
		clean = _claim_lines(lines)
		earlier, reuse = None, False
		if successor_of:
			earlier = frappe.get_doc(INVOICE, successor_of)
			if earlier.contract_case != case or earlier.state != "Held":
				fail("CM_CHANGED", invoice=successor_of, state=earlier.state)
		same = apparent_duplicate(case, claim_reference, clean, invoice_date, exclude=successor_of)  # held for Finance review, never refused or deleted (section 5.8)
		match = match_claim(case, clean, exclude=successor_of, duplicate_of=same)
		number = records.next_number(INVOICE, {"contract_case": case}, "invoice_no")
		held = match["outcome"] != "Supported"
		stored = [{**l, "receipt": r["receipt"], "amount": r["amount"]} for l, r in zip(clean, match["rows"])]
		received = clock.now()
		row = records.new(INVOICE, contract_case=case, invoice_no=number, claim_reference=claim_reference.strip(), invoice_date=getdate(invoice_date), received_at=received,
			first_received_at=(earlier.first_received_at or earlier.received_at) if earlier else received, claimed_amount=match["amount"],
			state="Held" if held else "Submitted", lines_json=records.dumps(stored), matching_json=records.dumps(match), successor_of=successor_of or None, submitted_by=actor, record_version=1)
		if earlier:
			records.update(earlier, state="Superseded", record_version=cint(earlier.record_version) + 1)
			work.finish(case, subject=f"invoice {earlier.invoice_no}", state="Superseded", actor=actor)
			reuse = _retire_native(case, earlier, row, actor)
		records.bump(doc, invoice_state="Invoice held for review" if held else "Invoice submitted")
		subject = f"invoice {number}"
		native = False
		if held and same:
			work.assign(case, "ResolveInvoiceDuplicate", "Review the invoice: it appears to repeat another.", subject, 1, work.holders("Finance preparation"), role="Finance preparation")
			work.assign(case, work.waiting_command("ResolveInvoiceDuplicate", "supplier"), "Waiting for the invoice review.", subject, 1, [actor], role="Supplier Representative", state="Waiting")
		elif held:
			work.assign(case, "RequestInvoiceCorrection", "Review the invoice: it does not match what the contract supports.", subject, 1, work.holders(work.HOP), role=work.HOP)
			work.assign(case, work.waiting_command("RequestInvoiceCorrection", "supplier"), "Waiting for the invoice review.", subject, 1, [actor], role="Supplier Representative", state="Waiting")
		else:
			if not reuse:  # a liability Finance already posted for the claim this one corrects stands as the one liability: a second draft would double it
				intents.record(case, subject, 1, "Native invoice", "native", recovery_owner="Finance; technical recovery")
				native = True
			work.assign(case, "SignContractCertification", "Review the invoice and sign the certification.", subject, 1, work.holders(work.HOP), role=work.HOP)
			work.assign(case, work.waiting_command("SignContractCertification", "procurement"), "Waiting for the certification.", subject, 1, [actor], role="Supplier Representative", state="Waiting")
		if held and not same and not reuse and _draftable(case, clean[0]):  # a disputed claim is still invoiced natively as a draft, so Finance holds the supplier's whole claim (section 5.8)
			intents.record(case, subject, 1, "Native invoice", "native", recovery_owner="Finance; technical recovery")
			native = True
		events.record(case, "Invoice submitted" if not successor_of else "Invoice corrected", actor, f"Invoice {claim_reference} for {match['amount']:,.2f} {'held for review' if held else 'matched'}.", invoice=row.name,
			outcome=match["outcome"], successor_of=successor_of, reason=reason)
		return records.summary(doc, invoice=row.name, invoice_no=number, matching=match["outcome"], state=row.state, native=native)

	recorded = records.command("CorrectContractInvoice" if successor_of else "SubmitContractInvoice", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "claim": claim_reference, "date": invoice_date, "lines": lines, "successor_of": successor_of, "reason": reason}, body=body, authorise=lambda: _claim_authority(case, actor))
	frappe.db.commit()
	if recorded.get("native"):
		_carry_out_native_invoice(case, recorded["invoice"], actor)
	return records.summary(frappe.get_doc(CASE, case), **{k: v for k, v in recorded.items() if k not in ("ok", "contract", "lifecycle", "record_version", "native")})


def _draftable(case: str, line: dict[str, Any]) -> bool:
	"""A held claim gets a native draft from the order unless its item is an asset (an asset is made when it is received) and only up to the ordered quantity."""
	terms = _terms(case)
	ordered = next((l for l in terms["lines"] if l["line_id"] == line["line_id"]), None)
	code = (terms["particulars"].get("item_mapping") or {}).get(line["line_id"])
	return bool(ordered and code and cint(line["quantity"]) > 0 and cint(line["quantity"]) <= cint(ordered["quantity"]) and not frappe.db.get_value("Item", code, "is_fixed_asset") and formation.native_order(case))


def _retire_native(case: str, earlier, successor, actor: str) -> bool:
	"""A corrected claim replaces the superseded one's native invoice. A draft is discarded and regenerated for the successor. One already posted (Finance recognised the liability) is kept: it stands as the
	successor's invoice too, so there is one liability and not two, and Finance is asked to bring it to the supported amount with a native credit before the successor can be certified or paid (section 5.18).
	Returns True when the posted invoice is carried to the successor."""
	if not earlier.native_invoice:
		return False
	if adapter.discard_draft_invoice(earlier.native_invoice):
		frappe.db.delete("Contract Transaction Link", {"native_doctype": "Purchase Invoice", "native_name": earlier.native_invoice})  # the name is free again (ERPNext reuses it): the link must not outlive the draft
		events.record(case, "Native draft discarded", actor, f"The draft invoice {earlier.native_invoice} of the superseded claim {earlier.claim_reference} was discarded.", invoice=earlier.name, native=earlier.native_invoice)
		return False
	posted = adapter.posted(earlier.native_invoice)
	if not posted:
		return False
	records.update(successor, native_invoice=earlier.native_invoice, accounting_state="Posted", finance_maker=earlier.finance_maker)
	required = posted - flt(successor.claimed_amount)
	if required > TOLERANCE:
		work.assign(case, "ReconcileInvoiceLiability", f"Reconcile the original liability: a native credit of {required:,.2f} is needed.", f"invoice {successor.invoice_no}", 1, work.holders("Finance preparation"), role="Finance preparation")
		events.record(case, "Liability needs a credit", actor, f"Invoice {earlier.claim_reference} was posted for {posted:,.2f}; the corrected claim supports {flt(successor.claimed_amount):,.2f}, so a native credit of {required:,.2f} is needed.",
			invoice=earlier.name, native=earlier.native_invoice, required=required)
	return True


def _carry_out_native_invoice(case: str, invoice: str, actor: str) -> dict[str, Any]:
	row = frappe.get_doc(INVOICE, invoice)
	intent = frappe.db.get_value(intents.INTENT, {"operation_identity": intents.identity(case, f"invoice {row.invoice_no}", 1, "Native invoice", "native")}, "name")
	if not intent:
		return {}
	line = records.loads(row.lines_json)[0]
	code = _terms(case)["particulars"]["item_mapping"][line["line_id"]]
	soft = row.state == "Held"  # a disputed claim's draft is a courtesy to Finance: if the owner refuses it, no one is asked to recover it

	def executor(identity: str):
		try:
			with service_principal.acting():
				if line.get("receipt"):
					return adapter.invoice_receipt(line["receipt"], identity, bill_no=row.claim_reference, bill_date=str(row.invoice_date), qty=line["quantity"], submit=False), "Purchase Invoice"
				return adapter.invoice_order(formation.native_order(case), identity, bill_no=row.claim_reference, bill_date=str(row.invoice_date), item_code=code, qty=line["quantity"]), "Purchase Invoice"
		except frappe.ValidationError as exc:
			raise intents.OwnerRefused(str(exc)) from exc

	result = intents.execute(intent, executor, lambda identity: adapter.find_by_identity("Purchase Invoice", identity), native_doctype="Purchase Invoice")
	with records.atomic():
		if result["state"] in intents.SETTLED:
			records.update(frappe.get_doc(INVOICE, invoice), native_invoice=result["reference"], accounting_state="Not prepared")
			work.finish(case, command="RestoreContractOperation", subject=f"invoice {row.invoice_no}", actor=actor)
			events.record(case, "Native invoice linked", actor, f"Native invoice {result['reference']} created for invoice {row.claim_reference}.", invoice=invoice, native=result["reference"])
		elif not soft:
			work.incident(case, "RestoreContractOperation", "Restore the native invoice", f"invoice {row.invoice_no}", 1)
		else:
			events.record(case, "Native draft not made", actor, f"No draft invoice was made for the disputed claim {row.claim_reference}.", invoice=invoice)
	frappe.db.commit()
	return result


def request_invoice_correction(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str, reason: str) -> dict[str, Any]:
	"""`RequestInvoiceCorrection`: HOP asks the supplier to correct a held claim. The original stays recorded; a linked successor replaces it."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"reason": "" if cstr(reason).strip() else "Enter what the supplier should correct."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(INVOICE, invoice)
		if row.contract_case != case or row.state != "Held":
			fail("CM_CHANGED", invoice=invoice, state=row.state)
		subject = f"invoice {row.invoice_no}"
		work.finish(case, command="RequestInvoiceCorrection", subject=subject, actor=actor)
		work.assign(case, "CorrectContractInvoice", f"Correct your invoice: {reason}", subject, 1, [row.submitted_by], role="Supplier Representative")
		records.bump(doc)
		events.record(case, "Invoice correction requested", actor, f"Correction of invoice {row.claim_reference} requested: {reason}", invoice=invoice)
		return records.summary(doc, invoice=invoice)

	return records.command("RequestInvoiceCorrection", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice, "reason": reason},
		body=body, authorise=lambda: authority.require(actor, "Head of Procurement Function"))


def resolve_duplicate(case: str, *, invoice: str, disposition: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ResolveInvoiceDuplicate` (authored; FU-CM-92): Finance decides whether a claim held as an apparent duplicate is one. A duplicate is set aside with the reason and keeps no entitlement; one that is not
	is matched again on its own merits and goes on to certification, or to the head of procurement for correction if it still does not match. The claim is never deleted."""
	preflight.exists(case)
	choices = ("Duplicate", "Not a duplicate")

	def body() -> dict[str, Any]:
		invalid({"disposition": "" if disposition in choices else "Choose whether this is a duplicate.", "reason": "" if cstr(reason).strip() else "Enter why."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(INVOICE, invoice)
		if row.contract_case != case or row.state != "Held" or not records.loads(row.matching_json).get("duplicate_of"):
			fail("CM_CHANGED", invoice=invoice, state=row.state)
		subject = f"invoice {row.invoice_no}"
		work.finish(case, command="ResolveInvoiceDuplicate", subject=subject, actor=actor)
		if disposition == "Duplicate":
			records.update(row, state="Set aside", record_version=cint(row.record_version) + 1)
			records.bump(doc)
			events.record(case, "Invoice set aside", actor, f"Invoice {row.claim_reference} set aside as a duplicate: {reason}", invoice=invoice, reason=reason)
			return records.summary(doc, invoice=invoice, state="Set aside")
		lines = [{k: v for k, v in l.items() if k in ("line_id", "quantity", "rate", "tax_included")} for l in records.loads(row.lines_json)]
		match = match_claim(case, lines, exclude=invoice)
		held = match["outcome"] != "Supported"
		records.update(row, state="Held" if held else "Submitted", matching_json=records.dumps(match), claimed_amount=match["amount"], record_version=cint(row.record_version) + 1)
		records.bump(doc, invoice_state="Invoice held for review" if held else "Invoice submitted")
		if held:
			work.assign(case, "RequestInvoiceCorrection", "Review the invoice: it does not match what the contract supports.", subject, 1, work.holders(work.HOP), role=work.HOP)
		else:
			intents.record(case, subject, 1, "Native invoice", "native", recovery_owner="Finance; technical recovery")
			work.assign(case, "SignContractCertification", "Review the invoice and sign the certification.", subject, 1, work.holders(work.HOP), role=work.HOP)
		events.record(case, "Invoice duplicate cleared", actor, f"Invoice {row.claim_reference} is not a duplicate: {reason}", invoice=invoice, outcome=match["outcome"], reason=reason)
		return records.summary(doc, invoice=invoice, state=row.state, matching=match["outcome"])

	recorded = records.command("ResolveInvoiceDuplicate", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice, "disposition": disposition, "reason": reason},
		body=body, authorise=lambda: authority.require(actor, "Finance preparation"))
	frappe.db.commit()
	if recorded.get("state") == "Submitted":
		_carry_out_native_invoice(case, invoice, actor)
	return records.summary(frappe.get_doc(CASE, case), **{k: v for k, v in recorded.items() if k not in ("ok", "contract", "lifecycle", "record_version")})


# -- a posted liability that a corrected claim no longer supports ------------------------------------------------------------------------------
def _final_successor(invoice: str):
	"""The claim at the end of a chain of corrections that still stands, or None."""
	row = frappe.db.get_value(INVOICE, {"successor_of": invoice, "state": ["!=", "Set aside"]}, "name")
	while row:
		nxt = frappe.db.get_value(INVOICE, {"successor_of": row, "state": ["!=", "Set aside"]}, "name")
		if not nxt:
			return frappe.get_doc(INVOICE, row)
		row = nxt
	return None


def liability_gap(case: str) -> list[dict[str, Any]]:
	"""For each superseded claim whose native invoice Finance posted: the successor, the liability, what the successor supports, the credit still needed and whether it has arrived."""
	out = []
	for orig in frappe.get_all(INVOICE, filters={"contract_case": case, "state": "Superseded", "native_invoice": ["is", "set"]}, fields=["name", "invoice_no", "native_invoice", "claim_reference", "received_at"]):
		posted = adapter.posted(orig.native_invoice)
		final = _final_successor(orig.name) if posted else None
		if not final:
			continue
		required = max(0.0, posted - flt(final.claimed_amount))
		credited = adapter.credit_against(orig.native_invoice)
		out.append({"original": orig.name, "original_no": orig.invoice_no, "native": orig.native_invoice, "successor": final.name, "successor_no": final.invoice_no, "liability": posted, "supported": flt(final.claimed_amount),
			"required": required, "credited": credited, "reconciled": credited + TOLERANCE >= required})
	return out


@holds.provider("claim liability")
def _liability_holds(case: str):
	for gap in liability_gap(case):
		if not gap["reconciled"]:
			yield holds.Hold(key=f"liability:{gap['original']}", kind="Correction", reason=f"Finance must reconcile the original liability of {gap['liability']:,.2f}: a native credit of {gap['required']:,.2f} is needed.",
				blocks=frozenset({"certify_invoice", "pay"}), owner="Finance", clearing="A native credit that brings the liability to the supported amount", scope=(f"invoice {gap['successor_no']}", f"invoice {gap['original_no']}"))


def receive_finance_result(case: str, *, native_invoice: str, actor: str = "") -> dict[str, Any]:
	"""`ReceiveFinanceResult` (service-only): ERPNext reports a native credit against an invoice of this contract. Contract Management never writes the ledger; it reads the credit, and when the liability
	now equals what the corrected claim supports the hold lifts and Finance's task is done."""
	for gap in liability_gap(case):
		if gap["native"] != native_invoice:
			continue
		by = actor or "Administrator"
		events.record(case, "Native credit received", by, f"A native credit of {gap['credited']:,.2f} now stands against invoice {gap['native']}; {gap['required']:,.2f} is needed.", native=native_invoice, credited=gap["credited"], required=gap["required"])
		if gap["reconciled"]:
			work.finish(case, command="ReconcileInvoiceLiability", subject=f"invoice {gap['successor_no']}", actor=by)
			events.record(case, "Liability reconciled", by, f"The liability now equals what the corrected claim supports ({gap['supported']:,.2f}).", native=native_invoice)
		return {"reconciled": gap["reconciled"], **gap}
	return {"reconciled": None}


def reconcile_liability(case: str, *, invoice: str, credit_document: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ReconcileInvoiceLiability`: Finance names the native credit note that brings the liability posted for a superseded claim down to what the corrected claim supports. The credit is raised in the accounting
	records (there is no credit-note editor here: FU-CM-119); Contract Management reads it, never writes the ledger, and when the credits stand at the amount needed the hold lifts and Finance's task is done.
	A document that is not a posted credit against that original invoice is refused, and a credit that is too small says how much more is needed."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		gap = next((g for g in liability_gap(case) if g["successor"] == invoice), None)
		if gap is None:
			fail("CM_CHANGED", invoice=invoice, reason="No liability is waiting for a credit on this claim.")
		found = frappe.db.get_value("Purchase Invoice", cstr(credit_document).strip(), ["docstatus", "is_return", "return_against"], as_dict=True) if cstr(credit_document).strip() else None
		invalid({"credit_document": "" if found and found.docstatus == 1 and found.is_return and found.return_against == gap["native"] else "This is not a posted credit against the original invoice."})
		result = receive_finance_result(case, native_invoice=gap["native"], actor=actor)  # the owner is read, and the hold and the task end with its answer
		if not result.get("reconciled"):
			fail("CM_RECONCILE", invoice=invoice, reason=f"The credits against the original invoice are {result['credited']:,.2f}; {result['required']:,.2f} is needed.", required=result["required"], credited=result["credited"])
		records.bump(doc)
		return records.summary(doc, invoice=invoice, reconciled=True)

	return records.command("ReconcileInvoiceLiability", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice, "credit": credit_document}, body=body,
		authorise=lambda: authority.require(actor, "Finance preparation"))


# -- Finance: the credit adjustment prepared from the claim (the Project Owner's decision of 16 October 2026, FU-CM-119) -------------------------
def _ask_for_credit(case: str, gap: dict[str, Any]) -> None:
	"""Finance's obligation to bring the original liability down: assigned when the corrected claim supports less than was posted, and reopened (the same item, its history kept) when a credit note is returned or leaves a shortfall."""
	needed = gap["required"] - gap["credited"]
	work.assign(case, "ReconcileInvoiceLiability", f"Reconcile the original liability: a native credit of {needed:,.2f} is needed.", f"invoice {gap['successor_no']}", 1, work.holders("Finance preparation"), role="Finance preparation")


def _liability_of(case: str, invoice: str) -> dict[str, Any]:
	gap = next((g for g in liability_gap(case) if g["successor"] == invoice), None)
	if gap is None or gap["reconciled"]:
		fail("CM_CHANGED", invoice=invoice, reason="No liability is waiting for a credit on this claim.")
	return gap


def _credit_identity(case: str, gap: dict[str, Any]) -> str:
	"""One credit note for what is still needed: it changes only when a credit has already been posted, so a replay finds the draft and a later shortfall gets its own."""
	return intents.identity(case, f"credit invoice {gap['successor_no']}", 1, "Native invoice", f"credit-{round(gap['credited'] * 100)}")


def credit_draft(case: str, gap: dict[str, Any]) -> dict[str, Any] | None:
	"""The Draft credit note Finance prepared for this liability and who prepared it, or None. Read only."""
	name = frappe.db.get_value("Purchase Invoice", {"cm_operation_identity": _credit_identity(case, gap), "docstatus": 0}, "name")
	if not name:
		return None
	maker = next((e["actor"] for e in reversed(events.history(case)) if e["type"] == "Credit note prepared" and e["detail"].get("credit") == name), "")
	return {"credit": name, "amount": abs(flt(frappe.db.get_value("Purchase Invoice", name, "grand_total"))), "maker": maker}


def prepare_liability_credit(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SaveNativeFinanceDraft` for the original liability: Finance prepares, from the corrected claim, the credit note that brings the liability posted for the superseded claim down to what the corrected claim
	supports, and hands it to a different Finance person to post. ERPNext stays the accounting owner: the credit is its own document, made and posted there; nothing here writes the ledger. Preparing it
	certifies no claim and releases no payment hold; the hold lifts when the credit is posted."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		from frappe.model.workflow import apply_workflow, get_workflow_name

		doc = records.lock(case)
		records.check_version(doc, expected_version)
		gap = _liability_of(case, invoice)
		if credit_draft(case, gap):
			fail("CM_CHANGED", invoice=invoice, reason="A credit note is already waiting for approval.")
		needed = gap["required"] - gap["credited"]
		made = native(adapter.prepare_credit, gap["native"], _credit_identity(case, gap), amount=needed, bill_no=f"CN-{gap['original_no']}-{gap['successor_no']}")
		if get_workflow_name("Purchase Invoice"):
			with _as_user(actor):
				apply_workflow(frappe.get_doc("Purchase Invoice", made["credit"]), "Submit for approval")
		subject = f"credit invoice {gap['successor_no']}"
		work.finish(case, command="ReconcileInvoiceLiability", subject=f"invoice {gap['successor_no']}", state="Superseded", actor=actor)  # it rests while the credit note waits, and is reopened if it is returned or falls short
		work.assign(case, "ApproveNativeFinanceRecord", "Review the credit note.", subject, 1, work.holders("Finance approval"), role="Finance approval")
		work.assign(case, work.waiting_command("ApproveNativeFinanceRecord", "credit"), "Waiting for the Finance approver.", subject, 1, [actor], role="Finance preparation", state="Waiting")
		records.bump(doc)
		events.record(case, "Credit note prepared", actor, f"A credit note of {made['amount']:,.2f} against invoice {gap['native']} was prepared and submitted for approval.", invoice=invoice, native=gap["native"], credit=made["credit"], amount=made["amount"])
		return records.summary(doc, invoice=invoice, credit=made["credit"], amount=made["amount"])

	return records.command("SaveNativeFinanceDraft", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice, "kind": "credit"}, body=body,
		authorise=lambda: authority.require(actor, "Finance preparation"))


def approve_liability_credit(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ApproveNativeFinanceRecord` for the credit note: a different Finance person posts it natively. The hook on that posting reads the credit (`receive_finance_result`): the liability comes down to what the
	corrected claim supports, the hold on its certification and payment lifts, and Finance's reconcile task is done."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		gap = _liability_of(case, invoice)
		draft = credit_draft(case, gap)
		if not draft:
			fail("CM_CHANGED", invoice=invoice, reason="There is no credit note waiting for approval.")
		segregation.finance_maker_not_approver(actor, [draft["maker"]])
		native(adapter.post_invoice, draft["credit"], actor)
		subject = f"credit invoice {gap['successor_no']}"
		work.finish(case, command="ApproveNativeFinanceRecord", subject=subject, actor=actor)
		after = next(g for g in liability_gap(case) if g["successor"] == invoice)
		if not after["reconciled"]:  # a credit that still falls short leaves Finance's task open for the rest
			_ask_for_credit(case, after)
		records.bump(doc, invoice_state="Liability credit posted")
		events.record(case, "Credit note posted", actor, f"Credit note {draft['credit']} against invoice {gap['native']} was posted.", invoice=invoice, native=gap["native"], credit=draft["credit"])
		return records.summary(doc, invoice=invoice, credit=draft["credit"], reconciled=after["reconciled"])

	return records.command("ApproveNativeFinanceRecord", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice, "kind": "credit"}, body=body,
		authorise=lambda: authority.require(actor, "Finance approval"))


def return_liability_credit(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str, reason: str) -> dict[str, Any]:
	"""`ReturnNativeFinanceForCorrection` for the credit note: the approver sends it back with the reason. The unposted draft is discarded, and its maker is told why, so a new one is prepared."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"reason": "" if cstr(reason).strip() else "Enter the reason."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		gap = _liability_of(case, invoice)
		draft = credit_draft(case, gap)
		if not draft:
			fail("CM_CHANGED", invoice=invoice, reason="There is no credit note waiting for approval.")
		adapter.discard_draft_invoice(draft["credit"])
		subject = f"credit invoice {gap['successor_no']}"
		work.finish(case, command="ApproveNativeFinanceRecord", subject=subject, actor=actor)
		_ask_for_credit(case, gap)
		if draft["maker"]:
			work.alert(case, [draft["maker"]], f"The credit note was returned: {reason}", "ApproveNativeFinanceRecord", subject)
		records.bump(doc)
		events.record(case, "Credit note returned", actor, f"The credit note against invoice {gap['native']} was returned: {reason}", invoice=invoice, native=gap["native"], credit=draft["credit"], maker=draft["maker"])
		return records.summary(doc, invoice=invoice)

	return records.command("ReturnNativeFinanceForCorrection", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice, "kind": "credit", "reason": reason},
		body=body, authorise=lambda: authority.require(actor, "Finance approval"))


# -- certification --------------------------------------------------------------------------------------------------------------------
def _acceptance_signers(case: str) -> list[str]:
	out = []
	for row in frappe.get_all("Contract Acceptance", filters={"contract_case": case, "state": "Effective"}, fields=["signers_json"]):
		out += [s["user"] for s in records.loads(row.signers_json, []) if s.get("state") == "Signed"]
	return out


def sign_certification(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SignContractCertification`: HOP's personal proof of one invoice's contractual support. It freezes the matching; it does not re-evaluate every check."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Head of Procurement Function")
		segregation.certifier_not_acceptance_signer(actor, _acceptance_signers(case))

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(INVOICE, invoice)
		if row.contract_case != case:
			raise frappe.DoesNotExistError("Not found")
		if row.state == "Certified":
			return records.summary(doc, invoice=invoice, already=True)
		if row.state != "Submitted":
			fail("CM_INVOICE", invoice=invoice, state=row.state, reason="This invoice needs review before certification.")
		if not row.native_invoice:
			fail("CM_RECONCILE", invoice=invoice, reason="The native invoice has not been created yet.")
		guards = preflight.rules(doc, "SignContractCertification")
		preflight.holds(guards, case, "certify_invoice", f"invoice {row.invoice_no}")
		guards.raise_if_any()
		match = records.loads(row.matching_json)
		plan = advance.recovery_plan(case, row)
		cert = frappe.db.get_value(CERTIFICATION, {"contract_case": case, "invoice": invoice, "state": ["!=", "Superseded"]}, "name")
		if not cert:
			cert = records.new(CERTIFICATION, contract_case=case, invoice=invoice, state="Awaiting signature", matching_json=records.dumps({**match, "advance_recovery": plan}), certified_amount=match["amount"], certifier=actor,
				acceptance_versions_json=records.dumps(sorted(frappe.get_all("Contract Acceptance", filters={"contract_case": case, "state": "Effective"}, pluck="name"))), record_version=1).name
		intent = signing_flow.record(case, f"certification invoice {row.invoice_no}", 1, "sign")
		digest = records.digest({"invoice": invoice, "matching": match, "native": row.native_invoice, "amount": match["amount"]})
		return records.summary(doc, invoice=invoice, certification=cert, intent=intent.name, digest=digest, amount=match["amount"], invoice_no=row.invoice_no)

	recorded = records.command("SignContractCertification", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice}, body=body, authorise=authorise)
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=recorded["certification"], target_digest=recorded["digest"], version=1, action="Sign the procurement certification")
	if not signing_flow.settled(result):
		with records.atomic():
			work.incident(case, "RestoreContractOperation", "Restore signing", f"certification invoice {recorded['invoice_no']}", 1)
		frappe.db.commit()
		signing_flow.unfinished(result, certification=recorded["certification"])
	with records.atomic():
		doc = records.lock(case)
		cert = frappe.get_doc(CERTIFICATION, recorded["certification"])
		row = frappe.get_doc(INVOICE, invoice)
		if cert.state != "Signed":
			records.update(cert, state="Signed", proof_reference=result["reference"], certified_at=clock.now(), certifier=actor, record_version=cint(cert.record_version) + 1)
			records.update(row, state="Certified", record_version=cint(row.record_version) + 1)
			adapter.certify_invoice(row.native_invoice, recorded["amount"])
			records.bump(doc, invoice_state="Invoice certified")
			subject = f"invoice {row.invoice_no}"
			work.finish(case, command="SignContractCertification", subject=subject, actor=actor)
			work.finish(case, command="RestoreContractOperation", subject=f"certification invoice {row.invoice_no}", actor=actor)
			if row.accounting_state == "Posted":  # Finance already recognised the liability: payment is the next step, and the hold that stood in its way is lifted by this certification
				work.assign(case, "SaveNativeFinanceDraft", "Prepare the payment record.", f"payment invoice {row.invoice_no}", 1, work.holders("Finance preparation"), role="Finance preparation")
			else:
				work.assign(case, "SaveNativeFinanceDraft", "Complete the accounting details for the invoice.", f"accounting invoice {row.invoice_no}", 1, work.holders("Finance preparation"), role="Finance preparation")
			work.assign(case, work.waiting_command("SaveNativeFinanceDraft", "finance"), "Waiting for Finance.", subject, 1, work.holders(work.HOP), role=work.HOP, state="Waiting")
			events.record(case, "Certification signed", actor, f"Invoice {row.claim_reference} certified for {recorded['amount']:,.2f}.", certification=cert.name, proof=result["reference"])
		out = records.summary(doc, invoice=invoice, certification=cert.name, state="Certified")
	frappe.db.commit()
	return out


# -- Finance: the accounting invoice (D33) ------------------------------------------------------------------------------------------------
def _accounting_row(case: str, invoice: str):
	row = frappe.get_doc(INVOICE, invoice)
	if row.contract_case != case:
		raise frappe.DoesNotExistError("Not found")
	if row.state not in ("Submitted", "Held", "Certified", "Partly paid") or not row.native_invoice:  # Finance may recognise a lawful liability before certification; payment stays held until it (section 5.8)
		fail("CM_INVOICE", invoice=invoice, state=row.state, reason="Only a claim with a native invoice can be prepared for accounting.")
	return row


def native(call, *args, **kwargs):
	"""Run a native call and show ERPNext's own refusal in plain words on the same screen (section 7): the message, never a stack, with the owner who can fix a configuration."""
	try:
		return call(*args, **kwargs)
	except errors.ContractError:
		raise
	except frappe.ValidationError as exc:
		message = frappe.utils.strip_html(str(exc)).strip() or "ERPNext refused the update."
		fail("CM_RECONCILE", native=message, reason=message, holder="Finance configuration owner")


def accounting_setup(case: str, invoice: str) -> list[str]:
	"""What stops the accounting invoice being posted because the site's accounting is not set up for it (the owner is the Finance configuration owner); empty when nothing does."""
	return adapter.accounting_setup_problems(_accounting_row(case, invoice).native_invoice)


def save_accounting_invoice(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str, posting_date: str, payable_account: str, cost_centre: str,
		expense_account: str, tax_template: str = "") -> dict[str, Any]:
	"""`SaveNativeFinanceDraft` for the supplier invoice: the Finance maker completes the accounting details of the Draft native invoice. Quantities and rates are the supplier's and are not editable here."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({k: ("" if cstr(v).strip() else f"Choose the {label}.") for k, v, label in (("posting_date", posting_date, "posting date"), ("payable_account", payable_account, "payable account"),
			("cost_centre", cost_centre, "cost centre"), ("expense_account", expense_account, "accounting treatment"))})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = _accounting_row(case, invoice)
		if row.accounting_state in ("Submitted for approval", "Posted"):
			fail("CM_CHANGED", invoice=invoice, accounting=row.accounting_state)
		saved = native(adapter.prepare_invoice, row.native_invoice, posting_date=posting_date, payable_account=payable_account, cost_centre=cost_centre, expense_account=expense_account, tax_template=tax_template)
		if adjustment.apply_to_native(case, invoice, row.native_invoice):  # an approved delay adjustment is a native deduction on this invoice, through Finance's verified mapping
			saved["grand_total"] = frappe.db.get_value("Purchase Invoice", row.native_invoice, "grand_total")
		plan = advance.recovery_plan(case, row)
		if plan and plan["recovery"] > 0:  # the advance is recovered on this invoice at the issued rate, set against it natively and never more than the advance still holds
			applied = native(adapter.apply_advance, row.native_invoice, plan["payment"], plan["recovery"])
			saved["grand_total"] = frappe.db.get_value("Purchase Invoice", row.native_invoice, "grand_total")
			events.record(case, "Advance recovery set", actor, f"{applied:,.2f} of the advance is recovered on invoice {row.claim_reference}.", invoice=invoice, advance=plan["advance"], recovery=applied)
		records.update(row, accounting_state="Draft saved", finance_maker=actor, record_version=cint(row.record_version) + 1)
		records.bump(doc)
		events.record(case, "Accounting invoice saved", actor, f"Accounting details of invoice {row.claim_reference} saved.", invoice=invoice, native=row.native_invoice)
		return records.summary(doc, invoice=invoice, native_invoice=row.native_invoice, accounting="Draft saved", total=saved["grand_total"])

	return records.command("SaveNativeFinanceDraft", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "invoice": invoice, "date": posting_date, "payable": payable_account, "cost": cost_centre, "expense": expense_account, "tax": tax_template},
		body=body, authorise=lambda: authority.require(actor, "Finance preparation"))


def submit_accounting_invoice(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SubmitNativeFinanceForApproval` for the supplier invoice: the maker hands the saved draft to the Finance approver."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		from frappe.model.workflow import apply_workflow, get_workflow_name

		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = _accounting_row(case, invoice)
		if row.accounting_state != "Draft saved":
			fail("CM_CHANGED", invoice=invoice, accounting=row.accounting_state)
		if row.finance_maker and row.finance_maker.lower() != actor.lower():
			fail("CM_AUTHORITY", missing="responsibility", reason="The person who prepared the draft submits it.")
		problems = accounting_setup(case, invoice)
		if problems:
			fail("CM_RECONCILE", reason="The accounting setup needs review.", holder="Finance configuration owner", problems=problems)
		if get_workflow_name("Purchase Invoice"):
			with _as_user(actor):
				apply_workflow(frappe.get_doc("Purchase Invoice", row.native_invoice), "Submit for approval")
		records.update(row, accounting_state="Submitted for approval", record_version=cint(row.record_version) + 1)
		work.finish(case, command="SaveNativeFinanceDraft", subject=f"accounting invoice {row.invoice_no}", actor=actor)
		work.assign(case, "ApproveNativeFinanceRecord", "Review the accounting invoice.", f"accounting invoice {row.invoice_no}", 1, work.holders("Finance approval"), role="Finance approval")
		work.assign(case, work.waiting_command("ApproveNativeFinanceRecord", "accounting"), "Waiting for the Finance approver.", f"accounting invoice {row.invoice_no}", 1, [actor], role="Finance preparation", state="Waiting")
		records.bump(doc)
		events.record(case, "Accounting invoice submitted", actor, f"Accounting invoice for {row.claim_reference} submitted for approval.", invoice=invoice)
		return records.summary(doc, invoice=invoice, accounting="Submitted for approval")

	return records.command("SubmitNativeFinanceForApproval", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice}, body=body,
		authorise=lambda: authority.require(actor, "Finance preparation"))


def approve_accounting_invoice(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ApproveNativeFinanceRecord` for the supplier invoice: a different Finance person posts the accounting invoice natively. Liability recognition is a Finance fact, kept apart from payment."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = _accounting_row(case, invoice)
		if row.accounting_state == "Posted":
			return records.summary(doc, invoice=invoice, already=True)
		if row.accounting_state != "Submitted for approval":
			fail("CM_CHANGED", invoice=invoice, accounting=row.accounting_state)
		segregation.finance_maker_not_approver(actor, [row.finance_maker])
		native(adapter.post_invoice, row.native_invoice, actor)
		records.update(row, accounting_state="Posted", record_version=cint(row.record_version) + 1)
		work.finish(case, command="ApproveNativeFinanceRecord", subject=f"accounting invoice {row.invoice_no}", actor=actor)
		work.finish(case, command=work.waiting_command("SaveNativeFinanceDraft", "finance"), actor=actor)
		if row.state in ("Certified", "Partly paid"):  # a liability recognised before certification waits for it; payment is prepared once it is signed
			work.assign(case, "SaveNativeFinanceDraft", "Prepare the payment record.", f"payment invoice {row.invoice_no}", 1, work.holders("Finance preparation"), role="Finance preparation")
		records.bump(doc, invoice_state="Accounting invoice posted")
		events.record(case, "Accounting invoice posted", actor, f"Accounting invoice {row.native_invoice} posted.", invoice=invoice, native=row.native_invoice)
		return records.summary(doc, invoice=invoice, accounting="Posted")

	return records.command("ApproveNativeFinanceRecord", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice}, body=body,
		authorise=lambda: authority.require(actor, "Finance approval"))


def return_accounting_invoice(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str, reason: str) -> dict[str, Any]:
	"""`ReturnNativeFinanceForCorrection` for the supplier invoice: the approver sends the draft back to its maker with the reason."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"reason": "" if cstr(reason).strip() else "Enter the reason."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = _accounting_row(case, invoice)
		if row.accounting_state != "Submitted for approval":
			fail("CM_CHANGED", invoice=invoice, accounting=row.accounting_state)
		records.update(row, accounting_state="Draft saved", record_version=cint(row.record_version) + 1)
		work.finish(case, command="ApproveNativeFinanceRecord", subject=f"accounting invoice {row.invoice_no}", actor=actor)
		work.assign(case, "SaveNativeFinanceDraft", f"Correct the accounting invoice: {reason}", f"accounting invoice {row.invoice_no}", 2, [row.finance_maker], role="Finance preparation")
		records.bump(doc)
		events.record(case, "Accounting invoice returned", actor, f"Accounting invoice for {row.claim_reference} returned: {reason}", invoice=invoice)
		return records.summary(doc, invoice=invoice, accounting="Draft saved")

	return records.command("ReturnNativeFinanceForCorrection", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "invoice": invoice, "reason": reason},
		body=body, authorise=lambda: authority.require(actor, "Finance approval"))


# -- Finance: the payment (D09-F, D17) ----------------------------------------------------------------------------------------------------
def _as_user(user: str):
	"""The Finance maker's or approver's own native session (see `service_principal`): the native workflow checks them, not a service."""
	return service_principal.acting_as(user)


def payments(case: str, *, cancelled: bool = False) -> list[dict[str, Any]]:
	"""The native payment entries of the contract: those of its invoices and the advance. Cancelled ones are left out unless asked for (they still count when a new payment is numbered).
	An advance is known by the operation that made it, because ERPNext moves its reference from the order to the invoices it is set against."""
	out = []
	advance = frappe.db.get_value("Contract Advance", {"contract_case": case, "state": ["in", ["Certified", "Paid"]]}, ["name", "advance_no"], as_dict=True, order_by="advance_no desc")
	advanced = [r for r in frappe.get_all(intents.INTENT, filters={"contract_case": case, "operation_kind": "Native payment", "subject": ["like", "payment advance %"]}, pluck="result_reference") if r]
	for invoice in frappe.get_all(INVOICE, filters={"contract_case": case, "state": ACTIVE_INVOICE, "native_invoice": ["is", "set"]}, fields=["name", "native_invoice", "invoice_no"]):
		for pe in frappe.get_all("Payment Entry Reference", filters={"reference_doctype": "Purchase Invoice", "reference_name": invoice.native_invoice}, pluck="parent"):
			if pe in advanced:  # an advance also refers to the invoice it is set against: it is not that invoice's payment
				continue
			doc = frappe.db.get_value("Payment Entry", pe, ["name", "docstatus", "workflow_state", "paid_amount", "owner", "reference_no", "posting_date"], as_dict=True)
			if doc.docstatus < 2 or cancelled:
				out.append({**doc, "invoice": invoice.name, "invoice_no": invoice.invoice_no, "native_invoice": invoice.native_invoice, "kind": "invoice", "subject": f"invoice {invoice.invoice_no}"})
	if advance:  # the money advanced against the order, before any invoice
		for pe in advanced:
			doc = frappe.db.get_value("Payment Entry", pe, ["name", "docstatus", "workflow_state", "paid_amount", "owner", "reference_no", "posting_date"], as_dict=True)
			if doc and (doc.docstatus < 2 or cancelled):
				out.append({**doc, "invoice": advance.name, "invoice_no": advance.advance_no, "native_invoice": "", "kind": "advance", "subject": f"advance {advance.advance_no}"})
	return out


def draft_payment(case: str, invoice: str) -> str:
	"""The invoice's unposted native payment, if its maker has one (saving again updates it; it never makes a second)."""
	return next((p["name"] for p in payments(case) if p["invoice"] == invoice and p["docstatus"] == 0), "")


def save_finance_draft(case: str, *, invoice: str, expected_version: int, idempotency_key: str, actor: str, mode_of_payment: str, paid_from: str, reference_no: str, amount: float | None = None) -> dict[str, Any]:
	"""`SaveNativeFinanceDraft`: the Finance maker's draft native payment for a certified invoice, once per payment identity. Reads and the draft are the maker's; posting is the approver's."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"mode_of_payment": "" if cstr(mode_of_payment).strip() else "Choose how it is paid.", "paid_from": "" if cstr(paid_from).strip() else "Choose the account it is paid from.",
			"reference_no": "" if cstr(reference_no).strip() else "Enter the payment reference."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(INVOICE, invoice)
		if row.contract_case != case or row.state not in ("Certified", "Partly paid"):
			fail("CM_INVOICE", invoice=invoice, state=row.state, reason="Only a certified invoice can be paid.")
		if row.accounting_state != "Posted":
			fail("CM_INVOICE", invoice=invoice, accounting=row.accounting_state, reason="The accounting invoice is not posted yet.")
		held = payment_guard.entitlement(row.native_invoice, lock=True)
		wanted = flt(amount) if amount not in (None, "") else held["available"]
		if wanted <= 0 or wanted > held["available"] + TOLERANCE:
			fail("CM_HOLD", reason=f"The contract supports paying {held['available']:,.2f} on this invoice.", available=held["available"], requested=wanted, consequence="pay")
		guards = preflight.holds(preflight.rules(doc, "SaveNativeFinanceDraft"), case, "pay", f"invoice {row.invoice_no}")
		guards.raise_if_any()
		unposted = draft_payment(case, invoice)
		if unposted:
			with _as_user(actor):
				adapter.update_payment_draft(unposted, amount=wanted, mode_of_payment=mode_of_payment, paid_from=paid_from, reference_no=reference_no)
			records.bump(doc)
			events.record(case, "Payment draft saved", actor, f"Draft payment {unposted} updated.", payment=unposted, invoice=invoice)
			return records.summary(doc, invoice=invoice, payment=unposted, amount=wanted, updated=True)
		number = len([p for p in payments(case, cancelled=True) if p["invoice"] == invoice]) + 1  # a cancelled entry keeps its number: its operation identity is not reused
		intent = intents.record(case, f"payment invoice {row.invoice_no}", number, "Native payment", "draft", recovery_owner="Finance; technical recovery")
		return records.summary(doc, invoice=invoice, intent=intent.name, amount=wanted, payment_no=number)

	recorded = records.command("SaveNativeFinanceDraft", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "invoice": invoice, "mode": mode_of_payment, "from": paid_from, "ref": reference_no, "amount": amount}, body=body,
		authorise=lambda: authority.require(actor, "Finance preparation"))
	frappe.db.commit()
	if recorded.get("updated"):
		return recorded
	row = frappe.get_doc(INVOICE, invoice)

	def executor(identity: str):
		try:
			with _as_user(actor):
				return adapter.payment_draft(row.native_invoice, identity, amount=recorded["amount"], mode_of_payment=mode_of_payment, paid_from=paid_from, reference_no=reference_no), "Payment Entry"
		except frappe.ValidationError as exc:
			raise intents.OwnerRefused(str(exc)) from exc

	result = intents.execute(recorded["intent"], executor, lambda identity: adapter.find_by_identity("Payment Entry", identity), native_doctype="Payment Entry")
	with records.atomic():
		doc = records.lock(case)
		if result["state"] in intents.SETTLED:
			work.finish(case, command="SaveNativeFinanceDraft", subject=f"payment invoice {row.invoice_no}", actor=actor)
			work.assign(case, "SubmitNativeFinanceForApproval", "Submit the payment for approval.", f"payment {result['reference']}", 1, [actor], role="Finance preparation")
			records.bump(doc)
			events.record(case, "Payment drafted", actor, f"Draft payment {result['reference']} prepared for {recorded['amount']:,.2f}.", payment=result["reference"], invoice=invoice)
		else:
			work.incident(case, "RestoreContractOperation", "Restore the native payment", f"invoice {row.invoice_no}", recorded["payment_no"])
	frappe.db.commit()
	if result["state"] not in intents.SETTLED:
		fail("CM_RECONCILE", intent=recorded["intent"], state=result["state"], reason="The payment draft could not be created. Finance can restore it.")
	return records.summary(frappe.get_doc(CASE, case), invoice=invoice, payment=result["reference"], amount=recorded["amount"])


def _native_entry(case: str, payment: str):
	pe = frappe.get_doc("Payment Entry", payment)
	row = next((p for p in payments(case) if p["name"] == payment), None)
	if row is None:
		raise frappe.DoesNotExistError("Not found")
	return pe, row


def submit_finance_for_approval(case: str, *, payment: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SubmitNativeFinanceForApproval`: the maker's step in the native workflow."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		from frappe.model.workflow import apply_workflow

		doc = records.lock(case)
		records.check_version(doc, expected_version)
		pe, row = _native_entry(case, payment)
		if pe.docstatus != 0 or pe.workflow_state not in (None, "", "Draft"):
			fail("CM_CHANGED", payment=payment, state=pe.workflow_state)
		guards = preflight.holds(preflight.rules(doc, "SubmitNativeFinanceForApproval"), case, "pay", row["subject"])
		guards.raise_if_any()
		with _as_user(actor):
			apply_workflow(frappe.get_doc("Payment Entry", payment), "Submit for approval")
		work.finish(case, command="SubmitNativeFinanceForApproval", subject=f"payment {payment}", actor=actor)
		work.assign(case, "ApproveNativeFinanceRecord", "Approve the payment.", f"payment {payment}", 1, work.holders("Finance approval"), role="Finance approval")
		work.assign(case, work.waiting_command("ApproveNativeFinanceRecord", "payment"), "Waiting for the Finance approver.", f"payment {payment}", 1, [actor], role="Finance preparation", state="Waiting")
		records.bump(doc)
		events.record(case, "Payment submitted for approval", actor, f"Payment {payment} submitted for approval.", payment=payment)
		return records.summary(doc, payment=payment)

	return records.command("SubmitNativeFinanceForApproval", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "payment": payment}, body=body,
		authorise=lambda: authority.require(actor, "Finance preparation"))


def approve_finance_record(case: str, *, payment: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ApproveNativeFinanceRecord`: a different Finance person approves and the native workflow posts the payment inside the controlled operation. The guard rechecks the entitlement under a lock."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Finance approval")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		pe, row = _native_entry(case, payment)
		if pe.docstatus == 1:
			return records.summary(doc, payment=payment, already=True)
		if pe.workflow_state != "Pending Approval":
			fail("CM_CHANGED", payment=payment, state=pe.workflow_state)
		segregation.finance_maker_not_approver(actor, [pe.owner])
		guards = preflight.holds(preflight.rules(doc, "ApproveNativeFinanceRecord"), case, "pay", row["subject"])
		guards.raise_if_any()
		identity = frappe.db.get_value("Payment Entry", payment, "cm_operation_identity")
		adapter.approve_payment(payment, identity, actor)
		work.finish(case, command="ApproveNativeFinanceRecord", subject=f"payment {payment}", actor=actor)
		work.assign(case, "RecordFinanceSettlement", "Confirm that the payment settled.", f"payment {payment}", 1, work.holders("Finance approval"), role="Finance approval")
		records.bump(doc, invoice_state="Payment recorded")
		events.record(case, "Payment approved", actor, f"Payment {payment} approved and posted.", payment=payment)
		return records.summary(doc, payment=payment)

	return records.command("ApproveNativeFinanceRecord", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "payment": payment}, body=body, authorise=authorise)


def return_finance_for_correction(case: str, *, payment: str, expected_version: int, idempotency_key: str, actor: str, reason: str) -> dict[str, Any]:
	"""`ReturnNativeFinanceForCorrection`: the approver sends the draft back to its maker with the reason."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		from frappe.model.workflow import apply_workflow

		invalid({"reason": "" if cstr(reason).strip() else "Enter the reason."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		pe, row = _native_entry(case, payment)
		if pe.workflow_state != "Pending Approval":
			fail("CM_CHANGED", payment=payment, state=pe.workflow_state)
		with _as_user(actor):
			apply_workflow(frappe.get_doc("Payment Entry", payment), "Return")
		work.finish(case, command="ApproveNativeFinanceRecord", subject=f"payment {payment}", actor=actor)
		work.assign(case, "SubmitNativeFinanceForApproval", f"Correct the payment: {reason}", f"payment {payment}", 2, [pe.owner], role="Finance preparation")
		records.bump(doc)
		events.record(case, "Payment returned", actor, f"Payment {payment} returned for correction: {reason}", payment=payment)
		return records.summary(doc, payment=payment)

	return records.command("ReturnNativeFinanceForCorrection", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "payment": payment, "reason": reason},
		body=body, authorise=lambda: authority.require(actor, "Finance approval"))


# -- settlement -----------------------------------------------------------------------------------------------------------------------
def settled_amount(invoice: str) -> float:
	"""Confirmed cash: the settlements that stand (a reversed or corrected one does not)."""
	return sum(flt(a) for a in frappe.get_all(SETTLEMENT, filters={"invoice": invoice, "state": "Confirmed"}, pluck="amount"))


def invoice_position(case: str, invoice: str) -> dict[str, float]:
	"""Where one invoice stands, kept in the facts section 5.12 keeps apart: what procurement certified; what Finance recorded as paid (posted native payments); the cash confirmed settled (only attributable
	evidence counts); the noncash adjustments ERPNext applied to the invoice beyond those payments (an advance set against it, a write-off); and what is still to pay. A credit note standing alone against the
	invoice is its own fact and reduces nothing here (FU-CM-53), and a zero native balance is not cash."""
	row = frappe.get_doc(INVOICE, invoice)
	certified = flt(frappe.db.get_value(CERTIFICATION, {"contract_case": case, "invoice": invoice, "state": "Signed"}, "certified_amount"))
	recorded = sum(flt(p["paid_amount"]) for p in payments(case) if p["invoice"] == invoice and p["docstatus"] == 1)
	native_reduced = 0.0
	credit = 0.0
	if row.native_invoice:
		doc = frappe.db.get_value("Purchase Invoice", row.native_invoice, ["grand_total", "outstanding_amount"], as_dict=True)
		native_reduced = flt(doc.grand_total) - flt(doc.outstanding_amount)
		credit = adapter.credit_against(row.native_invoice)
	cash = settled_amount(invoice)
	adjusted = adjustment.applied_to(invoice)  # an authorised contractual adjustment applied as a native deduction: noncash, never reported as cash
	noncash = max(0.0, native_reduced - recorded) + adjusted
	return {"certified": certified, "recorded": recorded, "cash_confirmed": cash, "unconfirmed": max(0.0, recorded - cash), "noncash": noncash, "adjustment": adjusted, "credit": credit,
		"advance_recovery": adapter.advance_recovered(row.native_invoice) if row.native_invoice else 0.0, "outstanding": max(0.0, certified - recorded - noncash)}


def _settle_advance(doc, case: str, pe, row: dict[str, Any], actor: str, effective_date: str, evidence: str) -> dict[str, Any]:
	"""The independent confirmation that the advance's cash settled (an advance has no accounting invoice and no acceptance: the same independence applies to its maker and certifier)."""
	advance_row = frappe.get_doc("Contract Advance", row["invoice"])
	segregation.settlement_confirmer_independent(actor, makers=[pe.owner], certifiers=[advance_row.certifier] if advance_row.certifier else [])
	guards = preflight.holds(preflight.rules(doc, "RecordFinanceSettlement"), case, "confirm_settlement", row["subject"])
	guards.raise_if_any()
	settlement = records.new(SETTLEMENT, contract_case=case, advance=advance_row.name, native_payment=pe.name, amount=pe.paid_amount, state="Confirmed",
		evidence_json=records.dumps({"evidence": evidence, "native_payment": pe.name, "amount": flt(pe.paid_amount), "recorded_by": actor}), recorder=actor, effective_date=getdate(effective_date), recorded_at=clock.now(), record_version=1)
	confirmed = sum(flt(a) for a in frappe.get_all(SETTLEMENT, filters={"advance": advance_row.name, "state": "Confirmed"}, pluck="amount"))
	records.update(advance_row, state="Paid" if confirmed >= flt(advance_row.certified_amount) - TOLERANCE else advance_row.state, record_version=cint(advance_row.record_version) + 1)
	work.finish(case, command="RecordFinanceSettlement", subject=f"payment {pe.name}", actor=actor)
	work.finish(case, command=work.waiting_command("SaveNativeFinanceDraft", "advance"), actor=actor)
	records.bump(doc, invoice_state="Advance paid")
	events.record(case, "Settlement confirmed", actor, f"Advance payment {pe.name} for {flt(pe.paid_amount):,.2f} confirmed as settled.", settlement=settlement.name, payment=pe.name, advance=advance_row.name)
	return records.summary(doc, settlement=settlement.name, advance=advance_row.name, state=advance_row.state)


def save_advance_payment(case: str, *, advance: str, expected_version: int, idempotency_key: str, actor: str, mode_of_payment: str, paid_from: str, reference_no: str, amount: float | None = None) -> dict[str, Any]:
	"""`SaveNativeFinanceDraft` for a certified advance: the Finance maker's draft native payment against the order. The guard allows no more than was certified; posting is the approver's."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"mode_of_payment": "" if cstr(mode_of_payment).strip() else "Choose how it is paid.", "paid_from": "" if cstr(paid_from).strip() else "Choose the account it is paid from.",
			"reference_no": "" if cstr(reference_no).strip() else "Enter the payment reference."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc("Contract Advance", advance)
		if row.contract_case != case or row.state != "Certified":
			fail("CM_INVOICE", advance=advance, state=row.state, reason="Only a certified advance can be paid.")
		order = formation.native_order(case)
		held = payment_guard.advance_entitlement(order, lock=True)
		wanted = flt(amount) if amount not in (None, "") else held["available"]
		if wanted <= 0 or wanted > held["available"] + TOLERANCE:
			fail("CM_HOLD", reason=f"The contract supports advancing {held['available']:,.2f}.", available=held["available"], requested=wanted, consequence="pay")
		guards = preflight.holds(preflight.rules(doc, "SaveNativeFinanceDraft"), case, "pay", f"advance {row.advance_no}")
		guards.raise_if_any()
		unposted = next((p["name"] for p in payments(case) if p["kind"] == "advance" and p["docstatus"] == 0), "")
		if unposted:
			with _as_user(actor):
				adapter.update_payment_draft(unposted, amount=wanted, mode_of_payment=mode_of_payment, paid_from=paid_from, reference_no=reference_no)
			records.bump(doc)
			return records.summary(doc, advance=advance, payment=unposted, amount=wanted, updated=True)
		number = len([p for p in payments(case, cancelled=True) if p["kind"] == "advance"]) + 1
		intent = intents.record(case, f"payment advance {row.advance_no}", number, "Native payment", "draft", recovery_owner="Finance; technical recovery")
		return records.summary(doc, advance=advance, intent=intent.name, amount=wanted, payment_no=number)

	recorded = records.command("SaveNativeFinanceDraft", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "advance": advance, "mode": mode_of_payment, "from": paid_from, "ref": reference_no, "amount": amount}, body=body, authorise=lambda: authority.require(actor, "Finance preparation"))
	frappe.db.commit()
	if recorded.get("updated"):
		return recorded
	order = formation.native_order(case)
	number = frappe.get_doc("Contract Advance", advance).advance_no

	def executor(identity: str):
		try:
			with _as_user(actor):
				return adapter.advance_draft(order, identity, amount=recorded["amount"], mode_of_payment=mode_of_payment, paid_from=paid_from, reference_no=reference_no), "Payment Entry"
		except frappe.ValidationError as exc:
			raise intents.OwnerRefused(str(exc)) from exc

	result = intents.execute(recorded["intent"], executor, lambda identity: adapter.find_by_identity("Payment Entry", identity), native_doctype="Payment Entry")
	with records.atomic():
		doc = records.lock(case)
		if result["state"] in intents.SETTLED:
			work.finish(case, command="SaveNativeFinanceDraft", subject=f"payment advance {number}", actor=actor)
			work.assign(case, "SubmitNativeFinanceForApproval", "Submit the advance payment for approval.", f"payment {result['reference']}", 1, [actor], role="Finance preparation")
			records.bump(doc)
			events.record(case, "Payment drafted", actor, f"Draft advance payment {result['reference']} prepared for {recorded['amount']:,.2f}.", payment=result["reference"], advance=advance)
		else:
			work.incident(case, "RestoreContractOperation", "Restore the native payment", f"advance {number}", recorded["payment_no"])
	frappe.db.commit()
	if result["state"] not in intents.SETTLED:
		fail("CM_RECONCILE", intent=recorded["intent"], state=result["state"], reason="The advance payment could not be created. Finance can restore it.")
	return records.summary(frappe.get_doc(CASE, case), advance=advance, payment=result["reference"], amount=recorded["amount"])


def record_finance_settlement(case: str, *, payment: str, expected_version: int, idempotency_key: str, actor: str, effective_date: str, evidence: str) -> dict[str, Any]:
	"""`RecordFinanceSettlement`: an independent Finance person confirms that a posted payment settled, with attributable evidence. A posted payment alone is not a settled one."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Finance approval")

	def body() -> dict[str, Any]:
		invalid({"evidence": "" if cstr(evidence).strip() else "Enter the bank or settlement evidence.", "effective_date": "" if cstr(effective_date).strip() else "Enter the settlement date."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		pe, row = _native_entry(case, payment)
		if pe.docstatus != 1:
			fail("CM_INVOICE", payment=payment, reason="The payment has not been posted.")
		if frappe.db.exists(SETTLEMENT, {"native_payment": payment, "state": "Confirmed"}):
			return records.summary(doc, payment=payment, already=True)
		if row["kind"] == "advance":
			return _settle_advance(doc, case, pe, row, actor, effective_date, evidence)
		certifier = frappe.db.get_value(CERTIFICATION, {"contract_case": case, "invoice": row["invoice"], "state": "Signed"}, "certifier")
		segregation.settlement_confirmer_independent(actor, makers=[pe.owner], certifiers=[certifier] if certifier else [])
		guards = preflight.holds(preflight.rules(doc, "RecordFinanceSettlement"), case, "confirm_settlement", row["subject"])
		guards.raise_if_any()
		settlement = records.new(SETTLEMENT, contract_case=case, invoice=row["invoice"], native_payment=payment, amount=pe.paid_amount, state="Confirmed",
			evidence_json=records.dumps({"evidence": evidence, "native_payment": payment, "amount": flt(pe.paid_amount), "recorded_by": actor}), recorder=actor, effective_date=getdate(effective_date), recorded_at=clock.now(), record_version=1)
		invoice = frappe.get_doc(INVOICE, row["invoice"])
		position_now = invoice_position(case, invoice.name)
		whole = position_now["cash_confirmed"] + position_now["noncash"] >= position_now["certified"] - TOLERANCE
		records.update(invoice, state="Paid" if whole else "Partly paid", record_version=cint(invoice.record_version) + 1)
		work.finish(case, command="RecordFinanceSettlement", subject=f"payment {payment}", actor=actor)
		work.finish(case, command=work.waiting_command("SaveNativeFinanceDraft", "finance"), actor=actor)
		records.bump(doc, invoice_state="Paid" if whole else "Partly paid")
		events.record(case, "Settlement confirmed", actor, f"Payment {payment} for {flt(pe.paid_amount):,.2f} confirmed as settled.", settlement=settlement.name, payment=payment)
		if not whole:
			number = 1 + len(payments(case, cancelled=True))
			work.assign(case, "SaveNativeFinanceDraft", f"Prepare payment for the remaining {position_now['outstanding']:,.2f}.", f"payment invoice {invoice.invoice_no}", number, work.holders("Finance preparation"), role="Finance preparation")
			work.assign(case, work.waiting_command("SaveNativeFinanceDraft", "remaining"), f"Following up the remaining {position_now['outstanding']:,.2f}.", f"payment invoice {invoice.invoice_no}", number,
				work.holders("Finance approval"), role="Finance approval", state="Waiting")
		from kentender_contracts.services import closeout

		closeout.offer_completion(case)
		return records.summary(doc, settlement=settlement.name, invoice=invoice.name, state=invoice.state)

	return records.command("RecordFinanceSettlement", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "payment": payment, "date": effective_date, "evidence": evidence}, body=body, authorise=authorise)


def correct_finance_settlement(case: str, *, settlement: str, effective_date: str, evidence: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`CorrectFinanceSettlement`: change the evidenced settlement (its date and evidence; the cash amount is the native payment's and is not editable) without any ledger write. The earlier confirmation
	stays as history, marked corrected, and the new one stands in its place. The same independence applies as to the first confirmation."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"evidence": "" if cstr(evidence).strip() else "Enter the bank or settlement evidence.", "effective_date": "" if cstr(effective_date).strip() else "Enter the settlement date.", "reason": "" if cstr(reason).strip() else "Enter why it is corrected."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		old = frappe.get_doc(SETTLEMENT, settlement)
		if old.contract_case != case or old.state != "Confirmed":
			fail("CM_CHANGED", settlement=settlement, state=old.state)
		pe, row = _native_entry(case, old.native_payment)
		certifier = frappe.db.get_value(CERTIFICATION, {"contract_case": case, "invoice": old.invoice, "state": "Signed"}, "certifier")
		segregation.settlement_confirmer_independent(actor, makers=[pe.owner], certifiers=[certifier] if certifier else [])
		records.update(old, state="Corrected", record_version=cint(old.record_version) + 1)
		new = records.new(SETTLEMENT, contract_case=case, invoice=old.invoice, native_payment=old.native_payment, amount=old.amount, state="Confirmed", corrects=old.name, reason=cstr(reason).strip(),
			evidence_json=records.dumps({"evidence": evidence, "native_payment": old.native_payment, "amount": flt(old.amount), "recorded_by": actor}), recorder=actor, effective_date=getdate(effective_date), recorded_at=clock.now(), record_version=1)
		records.bump(doc)
		events.record(case, "Settlement corrected", actor, f"The settlement of payment {old.native_payment} was corrected: {cstr(reason).strip()}", settlement=new.name, corrects=old.name)
		return records.summary(doc, settlement=new.name, corrects=old.name)

	return records.command("CorrectFinanceSettlement", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "settlement": settlement, "date": effective_date, "evidence": evidence, "reason": reason}, body=body, authorise=lambda: authority.require(actor, "Finance approval"))


def receive_payment_cancelled(native_payment: str, *, actor: str = "") -> dict[str, Any]:
	"""`ReceiveFinanceResult` for a cancelled native payment (service-only): Finance reversed the entry in ERPNext. The cash it settled is reversed in the projection, not erased: the original
	confirmation stays, marked reversed, the invoice's outstanding supported amount reopens and Finance is asked to prepare the payment again (section 5.18). Nothing is written to the ledger."""
	by = actor or "Administrator"
	reopened = []
	for stl in frappe.get_all(SETTLEMENT, filters={"native_payment": native_payment, "state": "Confirmed"}, fields=["name", "contract_case", "invoice", "amount"]):
		case = stl.contract_case
		doc = records.lock(case)
		records.update(frappe.get_doc(SETTLEMENT, stl.name), state="Reversed", reversed_at=clock.now(), reason="The native payment was cancelled.")
		invoice = frappe.get_doc(INVOICE, stl.invoice)
		now = invoice_position(case, invoice.name)
		records.update(invoice, state="Partly paid" if now["cash_confirmed"] > 0 else "Certified", record_version=cint(invoice.record_version) + 1)
		records.bump(doc, invoice_state="Payment reversed")
		number = 1 + len(payments(case, cancelled=True))
		work.assign(case, "SaveNativeFinanceDraft", f"Prepare the payment again: {flt(stl.amount):,.2f} was reversed.", f"payment invoice {invoice.invoice_no}", number, work.holders("Finance preparation"), role="Finance preparation")
		work.assign(case, work.waiting_command("SaveNativeFinanceDraft", "reversed"), f"Following up the reversed payment of {flt(stl.amount):,.2f}.", f"payment invoice {invoice.invoice_no}", number, work.holders("Finance approval"), role="Finance approval", state="Waiting")
		events.record(case, "Settlement reversed", by, f"Payment {native_payment} of {flt(stl.amount):,.2f} was cancelled in ERPNext: the settlement is reversed and the amount is outstanding again.", settlement=stl.name, payment=native_payment)
		reopened.append(stl.name)
	return {"reversed": reopened}
