# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Advances (CM-CHG-001 v0.8 sections 5.8, 5.11, 5.12, 19.3 CM-R-07; plan Phase 7; boards D29, D29-H, D29-R).

An advance exists only where the issued tender and the signed agreement provide it, never before signature, at most the profile's cap of the tender price, and only against a verified guarantee for the
advance amount. It has its own route and never an acceptance: the supplier claims it, procurement reviews the clause, the guarantee and the recovery plan and signs the certification, Finance pays it
natively as a payment against the order (a guard allows no more than was certified) and an independent Finance person confirms the cash. It is recovered on later invoices at the issued rate: the recovery is
set against the invoice natively, is a noncash adjustment, and never lets the same advance be recovered twice. The same entitlement is consumed once: an advance of KES 100,000 recovered by KES 80,000 and
KES 20,000 leaves cash of 100,000 + 720,000 + 180,000 = 1,000,000."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, flt, getdate

from kentender_contracts.native import adapter, payment_guard
from kentender_contracts.services import authority, clock, events, evidence, formation, holds, intents, preflight, records, service_principal, signing_flow, work
from kentender_contracts.services.errors import fail, invalid

ADVANCE = "Contract Advance"
SECURITY = "Contract Security"
CASE = "Contract Case"
KIND = "Advance guarantee"
TOLERANCE = 0.005
LIVE = ["in", ["Prepared", "Certified", "Paid"]]


def _terms(case: str) -> dict[str, Any]:
	return records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective"}, "terms_json", order_by="version_no desc") or "{}")


def clause(terms: dict[str, Any]) -> dict[str, Any] | None:
	"""The issued advance clause: `{percent, amount, recovery_per_unit, recovery_line, statement}`, or None when the terms provide none. The amount is the clause's own or its percentage of the contract sum;
	nothing is assumed from an example condition."""
	found = terms.get("advance") or {}
	if not found.get("allowed"):
		return None
	total = flt(terms.get("total"))
	amount = flt(found.get("amount")) or (flt(found.get("percent")) * total / 100 if found.get("percent") else 0.0)
	goods = next((l["line_id"] for l in terms.get("lines", []) if l.get("kind") != "service"), "")
	return {**found, "amount": amount, "percent": flt(found.get("percent")) or (amount * 100 / total if total else 0.0), "recovery_per_unit": flt(found.get("recovery_per_unit")), "recovery_line": found.get("recovery_line") or goods}


def live(case: str):
	name = frappe.db.get_value(ADVANCE, {"contract_case": case, "state": LIVE}, "name", order_by="advance_no desc")
	return frappe.get_doc(ADVANCE, name) if name else None


def guarantee(case: str, *states: str):
	filters: dict[str, Any] = {"contract_case": case, "kind": KIND}
	filters["state"] = ["in", list(states)] if states else ["!=", "Superseded"]
	name = frappe.db.get_value(SECURITY, filters, "name", order_by="version_no desc")
	return frappe.get_doc(SECURITY, name) if name else None


def verified_guarantee(case: str, amount: float):
	"""The verified guarantee that covers `amount` and has not expired, or None."""
	row = guarantee(case, "Verified")
	if row and flt(row.amount) + TOLERANCE >= flt(amount) and getdate(row.expires_on) > getdate(clock.now()):
		return row
	return None


@holds.provider("advance guarantee")
def _unverified(case: str):
	"""CM-R-07: an advance asked for without a verified guarantee that covers it stops its certification, and nothing else."""
	row = frappe.db.get_value(ADVANCE, {"contract_case": case, "state": "Prepared"}, ["advance_no", "amount"], as_dict=True)
	if not row or verified_guarantee(case, row.amount):
		return []
	return [holds.Hold(key="ADVANCE_GUARANTEE_NOT_VERIFIED", kind="Restriction", reason="The advance guarantee has not been verified.", blocks=frozenset({"certify_advance"}), owner="Finance advance custodian",
		clearing="The guarantee for the advance amount is recorded and verified from the issuer's confirmation", scope=(f"advance {row.advance_no}",))]


def _custodian(actor: str) -> None:
	authority.require(actor, "Finance preparation")


def _supplier(case: str, actor: str) -> None:
	from kentender_contracts.services import payment

	payment._claim_authority(case, actor)


# -- the guarantee --------------------------------------------------------------------------------------------------------------------
def record_guarantee(case: str, *, expected_version: int, idempotency_key: str, actor: str, issuer: str, beneficiary: str, reference: str, amount: float, issued_on: str, expires_on: str, attachment: str = "") -> dict[str, Any]:
	"""`RecordContractSecurity` for an advance guarantee: the instrument the supplier supplied, recorded by the Finance advance custodian. A replacement supersedes an earlier unverified one."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		if not clause(_terms(case)):
			fail("CM_RULE", rule="CM-R-07", reason="The issued terms do not provide an advance.")
		problems = {k: ("" if cstr(v).strip() else f"Enter the {label}.") for k, v, label in (("issuer", issuer, "issuer"), ("beneficiary", beneficiary, "beneficiary"), ("reference", reference, "reference"),
			("issued_on", issued_on, "issue date"), ("expires_on", expires_on, "expiry date"))}
		if not problems["issued_on"] and not problems["expires_on"] and getdate(expires_on) <= getdate(issued_on):
			problems["expires_on"] = "The expiry must be after the issue date."
		if flt(amount) <= 0:
			problems["amount"] = "Enter the amount."
		invalid(problems)
		attached = evidence.checked(attachment, actor, field="attachment", required=False)
		for earlier in frappe.get_all(SECURITY, filters={"contract_case": case, "kind": KIND, "state": "Recorded"}, pluck="name"):
			old = frappe.get_doc(SECURITY, earlier)
			records.update(old, state="Superseded")
			work.finish(case, command="VerifyContractSecurity", subject=f"advance guarantee {old.version_no}", state="Superseded", actor=actor)
		version = records.next_number(SECURITY, {"contract_case": case}, "version_no")
		row = records.new(SECURITY, contract_case=case, version_no=version, kind=KIND, state="Recorded", issuer=issuer.strip(), beneficiary=beneficiary.strip(), reference=reference.strip(), amount=flt(amount),
			issued_on=getdate(issued_on), expires_on=getdate(expires_on), attachment=attached["file"] if attached else "", recorded_by=actor, recorded_at=clock.now(), record_version=1)
		records.bump(doc)
		work.finish(case, command="RecordContractSecurity", subject="advance guarantee", actor=actor)
		work.assign(case, "VerifyContractSecurity", "Check the issuer's confirmation of the advance guarantee.", f"advance guarantee {version}", version, work.holders(work.HOP), role=work.HOP)
		events.record(case, "Advance guarantee recorded", actor, f"Advance guarantee {reference.strip()} recorded.", security=row.name, amount=flt(amount))
		return records.summary(doc, security=row.name, security_version=version)

	return records.command("RecordContractSecurity", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "kind": KIND, "issuer": issuer, "beneficiary": beneficiary,
		"reference": reference, "amount": amount, "issued": issued_on, "expires": expires_on}, body=body, authorise=lambda: _custodian(actor))


def verify_guarantee(case: str, *, security: str, expected_version: int, idempotency_key: str, actor: str, confirmation_reference: str, received_on: str, basis: str = "") -> dict[str, Any]:
	"""`VerifyContractSecurity` for an advance guarantee: HOP verifies from the issuer's confirmation. The beneficiary must be the procuring entity and the amount at least the advance asked for."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(SECURITY, security)
		if row.contract_case != case or row.kind != KIND or row.state != "Recorded":
			fail("CM_CHANGED", security=security, state=row.state)
		terms = _terms(case)
		entity = ((terms.get("parties") or {}).get("entity") or {}).get("name", "")
		asked = live(case)
		need = flt(asked.amount) if asked else flt((clause(terms) or {}).get("amount"))
		problems = {"confirmation_reference": "" if cstr(confirmation_reference).strip() else "Enter the issuer's confirmation reference.", "received_on": "" if cstr(received_on).strip() else "Enter when the confirmation was received."}
		if entity and cstr(row.beneficiary).strip().lower() != entity.strip().lower():
			problems["confirmation_reference"] = problems["confirmation_reference"] or f"The beneficiary is {row.beneficiary}, not {entity}."
		if flt(row.amount) + TOLERANCE < need:
			problems["confirmation_reference"] = problems["confirmation_reference"] or f"The amount {flt(row.amount):,.2f} is less than the {need:,.2f} of the advance."
		if getdate(row.expires_on) <= getdate(clock.now()):
			problems["confirmation_reference"] = problems["confirmation_reference"] or "The guarantee has already expired."
		invalid(problems)
		records.update(row, state="Verified", confirmation_reference=confirmation_reference.strip(), confirmation_received_on=getdate(received_on), verification_basis=cstr(basis).strip() or "Issuer confirmation",
			verified_by=actor, verified_at=clock.now(), record_version=cint(row.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="VerifyContractSecurity", subject=f"advance guarantee {row.version_no}", actor=actor)
		events.record(case, "Advance guarantee verified", actor, f"Advance guarantee {row.reference} verified from the issuer's confirmation {confirmation_reference.strip()}.", security=row.name)
		return records.summary(doc, security=row.name)

	return records.command("VerifyContractSecurity", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "security": security, "confirmation": confirmation_reference,
		"received": received_on, "basis": basis}, body=body, authorise=lambda: authority.require(actor, "Head of Procurement Function"))


# -- the claim and its certification --------------------------------------------------------------------------------------------------------
def recovery_text(found: dict[str, Any]) -> str:
	return f"KES {flt(found['recovery_per_unit']):,.0f} for each unit accepted and invoiced" if found.get("recovery_per_unit") else "As the issued terms state"


def prepare_advance(case: str, *, expected_version: int, idempotency_key: str, actor: str, claim_reference: str, amount: float) -> dict[str, Any]:
	"""`PrepareContractAdvance`: the supplier's claim for the advance the issued terms provide. It is refused where the terms provide none, before signature, above the clause or the profile's cap, or while
	another advance stands; the guarantee is checked by the certification, which waits for it with a named holder. Never an acceptance."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		found = clause(_terms(case))
		if not found:
			fail("CM_RULE", rule="CM-R-07", reason="The issued terms do not provide an advance, so none can be claimed.")
		cap = flt(preflight.profile(doc).parameter("advance_cap_percent").value)
		if found["percent"] - cap > TOLERANCE:
			fail("CM_RULE", rule="CM-R-07", reason=f"The advance ({found['percent']:g}% of the contract sum) is more than the {cap:g}% the law allows.")
		invalid({"claim_reference": "" if cstr(claim_reference).strip() else "Enter your advance claim number.", "amount": "" if flt(amount) > 0 else "Enter the amount."})
		if flt(amount) - flt(found["amount"]) > TOLERANCE:
			fail("CM_INVOICE", reason=f"The advance the issued terms provide is {flt(found['amount']):,.2f}; {flt(amount):,.2f} is more.", allowed=flt(found["amount"]), requested=flt(amount))
		if live(case):
			fail("CM_DUPLICATE", advance=live(case).name, reason="An advance has already been claimed under this contract.")
		guards = preflight.rules(doc, "PrepareContractAdvance")
		guards.raise_if_any()
		number = records.next_number(ADVANCE, {"contract_case": case}, "advance_no")
		row = records.new(ADVANCE, contract_case=case, advance_no=number, claim_reference=claim_reference.strip(), state="Prepared", amount=flt(amount), percent=found["percent"], clause_json=records.dumps(found),
			recovery_json=records.dumps({"per_unit": found["recovery_per_unit"], "line_id": found["recovery_line"]}), submitted_by=actor, received_at=clock.now(), record_version=1)
		records.bump(doc)
		subject = f"advance {number}"
		work.assign(case, "SignAdvanceCertification", "Review the advance and its guarantee.", subject, 1, work.holders(work.HOP), role=work.HOP)
		work.assign(case, work.waiting_command("SignAdvanceCertification", "procurement"), "Waiting for the advance to be reviewed.", subject, 1, [actor], role="Supplier Representative", state="Waiting")
		if not verified_guarantee(case, flt(amount)):
			work.assign(case, "RecordContractSecurity", "Record the advance guarantee.", "advance guarantee", 1, work.holders("Finance preparation"), role="Finance preparation")
		events.record(case, "Advance claimed", actor, f"Advance {claim_reference.strip()} for {flt(amount):,.2f} claimed.", advance=row.name, amount=flt(amount))
		return records.summary(doc, advance=row.name, advance_no=number)

	return records.command("PrepareContractAdvance", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "claim": claim_reference, "amount": amount}, body=body,
		authorise=lambda: _supplier(case, actor))


def sign_advance_certification(case: str, *, advance: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SignAdvanceCertification`: procurement's personal proof that the issued clause, a verified guarantee and the recovery plan support this advance. Finance follows only after it."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(ADVANCE, advance)
		if row.contract_case != case:
			raise frappe.DoesNotExistError("Not found")
		if row.state == "Certified" or row.state == "Paid":
			return records.summary(doc, advance=advance, already=True)
		if row.state != "Prepared":
			fail("CM_CHANGED", advance=advance, state=row.state)
		guards = preflight.rules(doc, "SignAdvanceCertification")
		preflight.holds(guards, case, "certify_advance", f"advance {row.advance_no}")
		guards.raise_if_any()
		intent = signing_flow.record(case, f"certification advance {row.advance_no}", 1, "sign")
		digest = records.digest({"advance": advance, "amount": flt(row.amount), "clause": records.loads(row.clause_json), "guarantee": verified_guarantee(case, row.amount).name, "recovery": records.loads(row.recovery_json)})
		return records.summary(doc, advance=advance, intent=intent.name, digest=digest, amount=flt(row.amount), advance_no=row.advance_no, guarantee=verified_guarantee(case, row.amount).name)

	recorded = records.command("SignAdvanceCertification", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "advance": advance}, body=body,
		authorise=lambda: authority.require(actor, "Head of Procurement Function"))
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=recorded["advance"], target_digest=recorded["digest"], version=1, action="Sign the advance certification")
	if not signing_flow.settled(result):
		with records.atomic():
			work.incident(case, "RestoreContractOperation", "Restore signing", f"certification advance {recorded['advance_no']}", 1)
		frappe.db.commit()
		signing_flow.unfinished(result, advance=recorded["advance"])
	with records.atomic():
		doc = records.lock(case)
		row = frappe.get_doc(ADVANCE, advance)
		if row.state == "Prepared":
			records.update(row, state="Certified", certified_amount=flt(row.amount), certifier=actor, proof_reference=result["reference"], certified_at=clock.now(), guarantee=recorded["guarantee"], record_version=cint(row.record_version) + 1)
			order = formation.native_order(case)
			adapter.certify_advance(order, flt(row.amount))
			records.bump(doc, invoice_state="Advance certified")
			subject = f"advance {row.advance_no}"
			work.finish(case, command="SignAdvanceCertification", subject=subject, actor=actor)
			work.finish(case, command="RestoreContractOperation", subject=f"certification advance {row.advance_no}", actor=actor)
			work.assign(case, "SaveNativeFinanceDraft", "Prepare the advance payment.", f"payment advance {row.advance_no}", 1, work.holders("Finance preparation"), role="Finance preparation")
			work.assign(case, work.waiting_command("SaveNativeFinanceDraft", "advance"), "Waiting for Finance.", subject, 1, work.holders(work.HOP), role=work.HOP, state="Waiting")
			events.record(case, "Advance certified", actor, f"Advance {row.claim_reference} certified for {flt(row.amount):,.2f}.", advance=row.name, proof=result["reference"])
		out = records.summary(doc, advance=advance, state="Certified")
	frappe.db.commit()
	return out


# -- recovery -------------------------------------------------------------------------------------------------------------------------
def advance_entry(case: str):
	"""The posted native payment that advanced the money, or None while it is not posted."""
	from kentender_contracts.services import payment

	return next((p for p in payment.payments(case) if p.get("kind") == "advance" and p["docstatus"] == 1), None)


def recovered(case: str, *, excluding: str = "") -> float:
	"""What invoices of the contract have already set off against the advance: the native advance allocated on each of their invoices."""
	total = 0.0
	for row in frappe.get_all("Contract Invoice", filters={"contract_case": case, "state": ["not in", ["Superseded", "Set aside"]], "native_invoice": ["is", "set"], "name": ["!=", excluding or ""]}, fields=["native_invoice"]):
		total += adapter.advance_recovered(row.native_invoice)
	return total


def recovery_plan(case: str, invoice) -> dict[str, Any] | None:
	"""What an invoice recovers of the advance, and the cash that remains: the issued rate for each unit of the recovery line the invoice claims, never more than the advance still holds. None when no advance
	has been paid. Used where procurement certifies (so the signer sees it) and again where Finance sets it against the invoice (so the same advance is never recovered twice)."""
	row = live(invoice.contract_case)
	entry = advance_entry(invoice.contract_case)
	if not row or not entry:
		return None
	plan = records.loads(row.recovery_json)
	lines = records.loads(invoice.lines_json, [])
	units = sum(cint(l["quantity"]) for l in lines if l["line_id"] == plan.get("line_id"))
	paid = flt(entry["paid_amount"])
	left = max(0.0, paid - recovered(invoice.contract_case, excluding=invoice.name))
	recovery = min(flt(plan.get("per_unit")) * units, left)
	claimed = flt(invoice.claimed_amount)
	return {"advance": row.name, "payment": entry["name"], "paid": paid, "rate": flt(plan.get("per_unit")), "units": units, "recovery": recovery, "cash": max(0.0, claimed - recovery), "remaining": max(0.0, left - recovery)}


def position(case: str) -> dict[str, Any]:
	"""The advance as the contract stands: certified, paid, recovered and still outstanding (visible on termination and at close-out)."""
	row = live(case)
	entry = advance_entry(case)
	if not row:
		return {"advance": "", "certified": 0.0, "paid": 0.0, "recovered": 0.0, "outstanding": 0.0}
	paid = flt(entry["paid_amount"]) if entry else 0.0
	got = recovered(case)
	return {"advance": row.name, "certified": flt(row.certified_amount), "paid": paid, "recovered": got, "outstanding": max(0.0, paid - got)}
