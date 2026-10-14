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
from kentender_contracts.services import authority, clock, delivery, events, formation, intents, parties, people, position, preflight, records, segregation, signing_flow, work
from kentender_contracts.services.errors import fail, invalid

CASE = "Contract Case"
INVOICE = "Contract Invoice"
CERTIFICATION = "Contract Certification"
SETTLEMENT = "Contract Settlement"
TOLERANCE = 0.005
ACTIVE_INVOICE = ["not in", ["Superseded"]]


def _terms(case: str) -> dict[str, Any]:
	return records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective"}, "terms_json", order_by="version_no desc"))


def _claimed(case: str, exclude: str = "") -> dict[str, int]:
	"""Quantity already claimed per line by claims that still stand (a superseded claim no longer holds its entitlement)."""
	out: dict[str, int] = {}
	for row in frappe.get_all(INVOICE, filters={"contract_case": case, "state": ACTIVE_INVOICE, "name": ["!=", exclude]}, fields=["lines_json"]):
		for line in records.loads(row.lines_json, []):
			out[line["line_id"]] = out.get(line["line_id"], 0) + cint(line["quantity"])
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


def match_claim(case: str, lines: list[dict[str, Any]], *, exclude: str = "") -> dict[str, Any]:
	"""Compare a claim with what the contract supports. Returns the frozen matching: a row per line and an overall outcome (`Supported` or `Needs review`)."""
	terms = _terms(case)
	ordered = {l["line_id"]: l for l in terms["lines"]}
	now = position.position(case)["lines"]
	claimed = _claimed(case, exclude)
	on_receipt = _claimed_on_receipts(case, exclude)
	receipts = delivery.posted_receipts(case)
	rows = []
	value = flt(terms["total"])
	previous_amount = sum(flt(r) for r in frappe.get_all(INVOICE, filters={"contract_case": case, "state": ACTIVE_INVOICE, "name": ["!=", exclude]}, pluck="claimed_amount"))
	for line in lines:
		contract = ordered.get(line["line_id"])
		quantity, rate = cint(line["quantity"]), flt(line.get("rate") if line.get("rate") not in (None, "") else (contract or {}).get("rate"))
		problems = []
		if contract is None:
			problems.append("This line is not in the contract.")
			rows.append({"line_id": line["line_id"], "claimed_quantity": quantity, "eligible_quantity": 0, "claimed_rate": rate, "contract_rate": None, "amount": quantity * rate, "previously_claimed": 0, "receipt": "", "outcome": "Needs review", "reasons": problems})
			continue
		eligible = max(0, now[line["line_id"]]["accepted"] - claimed.get(line["line_id"], 0))
		if quantity <= 0:
			problems.append("The quantity must be above zero.")
		if quantity > eligible:
			problems.append(f"{quantity} claimed but only {eligible} accepted and unclaimed.")
		if abs(rate - flt(contract["rate"])) > TOLERANCE:
			problems.append(f"The price {rate:,.2f} differs from the contract price {flt(contract['rate']):,.2f}.")
		receipt = next((r for r in receipts if _receipt_qty(r) - on_receipt.get(r, 0) >= quantity), "")
		if quantity > 0 and quantity <= eligible and not receipt:
			problems.append("The claim spans more than one receipt.")
		rows.append({"line_id": line["line_id"], "claimed_quantity": quantity, "eligible_quantity": eligible, "claimed_rate": rate, "contract_rate": flt(contract["rate"]), "amount": quantity * rate,
			"previously_claimed": claimed.get(line["line_id"], 0), "receipt": receipt, "outcome": "Needs review" if problems else "Supported", "reasons": problems})
	amount = sum(r["amount"] for r in rows)
	remaining = value - previous_amount
	over = amount > remaining + TOLERANCE
	return {"rows": rows, "amount": amount, "previous_claims": previous_amount, "contract_value": value, "remaining_contractual": remaining,
		"outcome": "Needs review" if over or any(r["outcome"] != "Supported" for r in rows) else "Supported", "exceeds_remaining": over}


def _claim_authority(case: str, actor: str) -> None:
	organisation = frappe.db.get_value(CASE, case, "supplier_organisation")
	segregation.supplier_signs_only_as_signatory(actor, signatories=parties.signatories(organisation, clock.now()), representatives=parties.representatives(organisation, clock.now()), action="claim")


def _claim_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
	clean = [{"line_id": cstr(l.get("line_id")), "quantity": cint(l.get("quantity")), "rate": l.get("rate")} for l in lines or []]
	invalid({"lines": "" if clean and all(l["line_id"] for l in clean) else "Name the lines and quantities you are claiming."})
	return clean


def submit_invoice(case: str, *, expected_version: int, idempotency_key: str, actor: str, claim_reference: str, invoice_date: str, lines: list[dict[str, Any]], successor_of: str = "") -> dict[str, Any]:
	"""`SubmitContractInvoice` / `CorrectContractInvoice` (with `successor_of`): record the claim and its automatic matching; a supported claim then gets its native invoice."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		invalid({"claim_reference": "" if cstr(claim_reference).strip() else "Enter your invoice number.", "invoice_date": "" if cstr(invoice_date).strip() else "Enter the invoice date."})
		clean = _claim_lines(lines)
		earlier = None
		if successor_of:
			earlier = frappe.get_doc(INVOICE, successor_of)
			if earlier.contract_case != case or earlier.state != "Held":
				fail("CM_CHANGED", invoice=successor_of, state=earlier.state)
		same = frappe.db.get_value(INVOICE, {"contract_case": case, "claim_reference": claim_reference.strip(), "state": ACTIVE_INVOICE, "name": ["!=", successor_of or ""]}, "name")
		if same:
			fail("CM_DUPLICATE", invoice=same, claim_reference=claim_reference, reason="An invoice with this number is already recorded for this contract.")
		match = match_claim(case, clean, exclude=successor_of)
		number = records.next_number(INVOICE, {"contract_case": case}, "invoice_no")
		held = match["outcome"] != "Supported"
		stored = [{**l, "receipt": r["receipt"], "amount": r["amount"]} for l, r in zip(clean, match["rows"])]
		row = records.new(INVOICE, contract_case=case, invoice_no=number, claim_reference=claim_reference.strip(), invoice_date=getdate(invoice_date), received_at=clock.now(), claimed_amount=match["amount"],
			state="Held" if held else "Submitted", lines_json=records.dumps(stored), matching_json=records.dumps(match), successor_of=successor_of or None, submitted_by=actor, record_version=1)
		if earlier:
			records.update(earlier, state="Superseded", record_version=cint(earlier.record_version) + 1)
			work.finish(case, subject=f"invoice {earlier.invoice_no}", state="Superseded", actor=actor)
		records.bump(doc, invoice_state="Invoice held for review" if held else "Invoice submitted")
		subject = f"invoice {number}"
		if held:
			work.assign(case, "RequestInvoiceCorrection", "Review the invoice: it does not match what the contract supports.", subject, 1, work.holders(work.HOP), role=work.HOP)
			work.assign(case, work.waiting_command("RequestInvoiceCorrection", "supplier"), "Waiting for the invoice review.", subject, 1, [actor], role="Supplier Representative", state="Waiting")
		else:
			intents.record(case, subject, 1, "Native invoice", "native", recovery_owner="Finance; technical recovery")
			work.assign(case, "SignContractCertification", "Review the invoice and sign the certification.", subject, 1, work.holders(work.HOP), role=work.HOP)
			work.assign(case, work.waiting_command("SignContractCertification", "procurement"), "Waiting for the certification.", subject, 1, [actor], role="Supplier Representative", state="Waiting")
		events.record(case, "Invoice submitted" if not successor_of else "Invoice corrected", actor, f"Invoice {claim_reference} for {match['amount']:,.2f} {'held for review' if held else 'matched'}.", invoice=row.name,
			outcome=match["outcome"], successor_of=successor_of)
		return records.summary(doc, invoice=row.name, invoice_no=number, matching=match["outcome"], state=row.state)

	recorded = records.command("CorrectContractInvoice" if successor_of else "SubmitContractInvoice", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "claim": claim_reference, "date": invoice_date, "lines": lines, "successor_of": successor_of}, body=body, authorise=lambda: _claim_authority(case, actor))
	frappe.db.commit()
	if recorded["state"] == "Submitted":
		_carry_out_native_invoice(case, recorded["invoice"], actor)
	return records.summary(frappe.get_doc(CASE, case), **{k: v for k, v in recorded.items() if k not in ("ok", "contract", "lifecycle", "record_version")})


def _carry_out_native_invoice(case: str, invoice: str, actor: str) -> dict[str, Any]:
	row = frappe.get_doc(INVOICE, invoice)
	intent = frappe.db.get_value(intents.INTENT, {"operation_identity": intents.identity(case, f"invoice {row.invoice_no}", 1, "Native invoice", "native")}, "name")
	line = records.loads(row.lines_json)[0]

	def executor(identity: str):
		try:
			return adapter.invoice_receipt(line["receipt"], identity, bill_no=row.claim_reference, bill_date=str(row.invoice_date), qty=line["quantity"]), "Purchase Invoice"
		except frappe.ValidationError as exc:
			raise intents.OwnerRefused(str(exc)) from exc

	result = intents.execute(intent, executor, lambda identity: adapter.find_by_identity("Purchase Invoice", identity), native_doctype="Purchase Invoice")
	with records.atomic():
		if result["state"] in intents.SETTLED:
			records.update(frappe.get_doc(INVOICE, invoice), native_invoice=result["reference"])
			work.finish(case, command="RestoreContractOperation", subject=f"invoice {row.invoice_no}", actor=actor)
			events.record(case, "Native invoice linked", actor, f"Native invoice {result['reference']} created for invoice {row.claim_reference}.", invoice=invoice, native=result["reference"])
		else:
			work.incident(case, "RestoreContractOperation", "Restore the native invoice", f"invoice {row.invoice_no}", 1)
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
		cert = frappe.db.get_value(CERTIFICATION, {"contract_case": case, "invoice": invoice, "state": ["!=", "Superseded"]}, "name")
		if not cert:
			cert = records.new(CERTIFICATION, contract_case=case, invoice=invoice, state="Awaiting signature", matching_json=row.matching_json, certified_amount=match["amount"], certifier=actor,
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
			work.assign(case, "SaveNativeFinanceDraft", "Prepare the invoice and the payment.", subject, 1, work.holders("Finance preparation"), role="Finance preparation")
			work.assign(case, work.waiting_command("SaveNativeFinanceDraft", "finance"), "Waiting for Finance.", subject, 1, work.holders(work.HOP), role=work.HOP, state="Waiting")
			events.record(case, "Certification signed", actor, f"Invoice {row.claim_reference} certified for {recorded['amount']:,.2f}.", certification=cert.name, proof=result["reference"])
		out = records.summary(doc, invoice=invoice, certification=cert.name, state="Certified")
	frappe.db.commit()
	return out


# -- Finance --------------------------------------------------------------------------------------------------------------------------
class _as_user:
	def __init__(self, user: str):
		self.user = user

	def __enter__(self):
		self.previous = frappe.session.user
		frappe.set_user(self.user)

	def __exit__(self, *exc):
		frappe.set_user(self.previous)


def payments(case: str) -> list[dict[str, Any]]:
	out = []
	for invoice in frappe.get_all(INVOICE, filters={"contract_case": case, "state": ACTIVE_INVOICE, "native_invoice": ["is", "set"]}, fields=["name", "native_invoice", "invoice_no"]):
		for pe in frappe.get_all("Payment Entry Reference", filters={"reference_doctype": "Purchase Invoice", "reference_name": invoice.native_invoice}, pluck="parent"):
			doc = frappe.db.get_value("Payment Entry", pe, ["name", "docstatus", "workflow_state", "paid_amount", "owner", "reference_no", "posting_date"], as_dict=True)
			if doc.docstatus < 2:
				out.append({**doc, "invoice": invoice.name, "invoice_no": invoice.invoice_no, "native_invoice": invoice.native_invoice})
	return out


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
		held = payment_guard.entitlement(row.native_invoice, lock=True)
		wanted = flt(amount) if amount not in (None, "") else held["available"]
		if wanted <= 0 or wanted > held["available"] + TOLERANCE:
			fail("CM_HOLD", reason=f"The contract supports paying {held['available']:,.2f} on this invoice.", available=held["available"], requested=wanted, consequence="pay")
		guards = preflight.holds(preflight.rules(doc, "SaveNativeFinanceDraft"), case, "pay", f"invoice {row.invoice_no}")
		guards.raise_if_any()
		number = frappe.db.count(SETTLEMENT, {"contract_case": case, "invoice": invoice}) + len([p for p in payments(case) if p["invoice"] == invoice]) + 1
		intent = intents.record(case, f"payment invoice {row.invoice_no}", number, "Native payment", "draft", recovery_owner="Finance; technical recovery")
		return records.summary(doc, invoice=invoice, intent=intent.name, amount=wanted, payment_no=number)

	recorded = records.command("SaveNativeFinanceDraft", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "invoice": invoice, "mode": mode_of_payment, "from": paid_from, "ref": reference_no, "amount": amount}, body=body,
		authorise=lambda: authority.require(actor, "Finance preparation"))
	frappe.db.commit()
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
			work.finish(case, command="SaveNativeFinanceDraft", subject=f"invoice {row.invoice_no}", actor=actor)
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
		guards = preflight.holds(preflight.rules(doc, "SubmitNativeFinanceForApproval"), case, "pay", f"invoice {row['invoice_no']}")
		guards.raise_if_any()
		with _as_user(actor):
			apply_workflow(frappe.get_doc("Payment Entry", payment), "Submit for approval")
		work.finish(case, command="SubmitNativeFinanceForApproval", subject=f"payment {payment}", actor=actor)
		work.assign(case, "ApproveNativeFinanceRecord", "Approve the payment.", f"payment {payment}", 1, work.holders("Finance approval"), role="Finance approval")
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
		guards = preflight.holds(preflight.rules(doc, "ApproveNativeFinanceRecord"), case, "pay", f"invoice {row['invoice_no']}")
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
	return sum(flt(a) for a in frappe.get_all(SETTLEMENT, filters={"invoice": invoice, "state": "Confirmed"}, pluck="amount"))


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
		certifier = frappe.db.get_value(CERTIFICATION, {"contract_case": case, "invoice": row["invoice"], "state": "Signed"}, "certifier")
		segregation.settlement_confirmer_independent(actor, makers=[pe.owner], certifiers=[certifier] if certifier else [])
		guards = preflight.holds(preflight.rules(doc, "RecordFinanceSettlement"), case, "confirm_settlement", f"invoice {row['invoice_no']}")
		guards.raise_if_any()
		settlement = records.new(SETTLEMENT, contract_case=case, invoice=row["invoice"], native_payment=payment, amount=pe.paid_amount, state="Confirmed", evidence_json=records.dumps({"evidence": evidence}),
			recorder=actor, effective_date=getdate(effective_date), recorded_at=clock.now(), record_version=1)
		invoice = frappe.get_doc(INVOICE, row["invoice"])
		certified = flt(frappe.db.get_value(CERTIFICATION, {"contract_case": case, "invoice": invoice.name, "state": "Signed"}, "certified_amount"))
		whole = settled_amount(invoice.name) + flt(pe.paid_amount) >= certified - TOLERANCE
		records.update(invoice, state="Paid" if whole else "Partly paid", record_version=cint(invoice.record_version) + 1)
		work.finish(case, command="RecordFinanceSettlement", subject=f"payment {payment}", actor=actor)
		work.finish(case, command=work.waiting_command("SaveNativeFinanceDraft", "finance"), actor=actor)
		records.bump(doc, invoice_state="Paid" if whole else "Partly paid")
		events.record(case, "Settlement confirmed", actor, f"Payment {payment} for {flt(pe.paid_amount):,.2f} confirmed as settled.", settlement=settlement.name, payment=payment)
		if not whole:
			work.assign(case, "SaveNativeFinanceDraft", "Prepare the next payment of this invoice.", f"invoice {invoice.invoice_no}", 1 + frappe.db.count(SETTLEMENT, {"invoice": invoice.name}), work.holders("Finance preparation"), role="Finance preparation")
		from kentender_contracts.services import closeout

		closeout.offer_completion(case)
		return records.summary(doc, settlement=settlement.name, invoice=invoice.name, state=invoice.state)

	return records.command("RecordFinanceSettlement", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "payment": payment, "date": effective_date, "evidence": evidence}, body=body, authorise=authorise)
