# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The performance security (CM-CHG-001 v0.8 sections 5.3, 5.10, 19.3 CM-R-08; boards D25, D25-R, D25-J).

Where the issued terms require a security, the agreement is not sent for signature until one is **verified**. HOP records the instrument the supplier supplied (issuer, beneficiary, reference, amount,
issue and expiry); the issuer's confirmation is recorded and HOP verifies or rejects it. "A file upload is not verification": a verification needs the issuer's confirmation reference, the date it was
received and the basis, and it checks the beneficiary is the procuring entity and the amount is what the issued terms require. A rejection keeps the instrument and its reason as history and asks the
supplier for a replacement; the next instrument supersedes it. Until one is verified a hold blocks the one consequence that depends on it, a new signing attempt, naming HOP and what clears it; the
supplier sees only their own side (the rejected instrument and that a replacement is awaited). The amount and validity come from the issued terms as supplied by the source handoff, never from a constant of the code."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, flt, getdate

from kentender_contracts.services import clock, events, evidence, holds, parties, preflight, records, work
from kentender_contracts.services.errors import fail, invalid

SECURITY = "Contract Security"
AGREEMENT = "Contract Agreement Version"
CASE = "Contract Case"


def _terms(case: str) -> dict[str, Any]:
	name = frappe.db.get_value(AGREEMENT, {"contract_case": case}, "terms_json", order_by="version_no desc")
	return records.loads(name) if name else {}


def requirement(terms: dict[str, Any]) -> dict[str, Any] | None:
	"""The issued terms' performance security: `{required, percentage?, statement, amount}` (the amount is the percentage of the contract sum), or None when the terms do not require one."""
	found = terms.get("security") or {}
	if not found.get("required"):
		return None
	amount = flt(found.get("amount")) or (flt(found.get("percentage")) * flt(terms.get("total")) / 100 if found.get("percentage") else 0)
	return {**found, "amount": amount}


def latest(case: str):
	name = frappe.db.get_value(SECURITY, {"contract_case": case, "state": ["!=", "Superseded"]}, "name", order_by="version_no desc")
	return frappe.get_doc(SECURITY, name) if name else None


def verified(case: str):
	name = frappe.db.get_value(SECURITY, {"contract_case": case, "state": "Verified"}, "name", order_by="version_no desc")
	return frappe.get_doc(SECURITY, name) if name else None


def ensure_work(case: str, terms: dict[str, Any]) -> None:
	"""When the terms require a security and none is recorded, HOP is asked to record it (idempotent: the same obligation is never made twice)."""
	if requirement(terms) and not latest(case):
		work.assign(case, "RecordContractSecurity", "Record the performance security.", "security 1", 1, work.holders(work.HOP), role=work.HOP)


@holds.provider("security")
def _unverified(case: str):
	"""CM-R-08: a required security that is not verified holds the signing request (and nothing else)."""
	if frappe.db.get_value(CASE, case, "lifecycle") != "Preparing":
		return []
	need = requirement(_terms(case))
	if not need or verified(case):
		return []
	return [holds.Hold(key="SECURITY_REQUIRED_NOT_VERIFIED", kind="Restriction", reason="The performance security required by the issued terms has not been verified.", blocks=frozenset({"new_signing_attempt"}),
		owner="Head of procurement function", clearing="The issuer's confirmation is recorded and the security is verified")]


def _supplier_side(case: str) -> list[str]:
	"""Who on the supplier's side is told: their authorised signatories at the contract's date."""
	return parties.signatories(frappe.db.get_value(CASE, case, "supplier_organisation") or "", clock.now())


def _preparer(actor: str, case: str) -> None:
	preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")


def record_security(case: str, *, expected_version: int, idempotency_key: str, actor: str, issuer: str, beneficiary: str, reference: str, amount: float, issued_on: str, expires_on: str,
		attachment: str = "") -> dict[str, Any]:
	"""`RecordContractSecurity`: the instrument the supplier supplied. A replacement supersedes an earlier unverified one and the earlier is kept."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		replacing = doc.lifecycle in ("Active", "Terminated") and verified(case) is not None  # a replacement or an extension of the instrument in force; it supersedes the old one only once verified (`security_actions`)
		preflight.lifecycle(doc, "Active", "Terminated") if replacing else preflight.lifecycle(doc, "Preparing")
		need = requirement(_terms(case))
		if not need:
			fail("CM_CHANGED", reason="The issued terms do not require a performance security.")
		problems = {k: ("" if cstr(v).strip() else f"Enter the {label}.") for k, v, label in (("issuer", issuer, "issuer"), ("beneficiary", beneficiary, "beneficiary"), ("reference", reference, "reference"),
			("issued_on", issued_on, "issue date"), ("expires_on", expires_on, "expiry date"))}
		if not problems["issued_on"] and not problems["expires_on"] and getdate(expires_on) <= getdate(issued_on):
			problems["expires_on"] = "The expiry must be after the issue date."
		if flt(amount) <= 0:
			problems["amount"] = "Enter the amount."
		invalid(problems)
		attached = evidence.checked(attachment, actor, field="attachment", required=False)
		for earlier in frappe.get_all(SECURITY, filters={"contract_case": case, "state": "Recorded"}, pluck="name"):
			old = frappe.get_doc(SECURITY, earlier)
			records.update(old, state="Superseded")
			work.finish(case, command="VerifyContractSecurity", subject=f"security {old.version_no}", state="Superseded", actor=actor)
		version = records.next_number(SECURITY, {"contract_case": case}, "version_no")
		row = records.new(SECURITY, contract_case=case, version_no=version, kind="Performance security", state="Recorded", issuer=issuer.strip(), beneficiary=beneficiary.strip(), reference=reference.strip(),
			amount=flt(amount), issued_on=getdate(issued_on), expires_on=getdate(expires_on), attachment=attached["file"] if attached else "", recorded_by=actor, recorded_at=clock.now(), record_version=1)
		records.bump(doc)
		work.finish(case, command="RecordContractSecurity", actor=actor)  # the request, and the supplier's waiting item for a replacement
		work.assign(case, "VerifyContractSecurity", "Check the issuer's confirmation.", f"security {version}", version, work.holders(work.HOP), role=work.HOP)
		work.assign(case, work.waiting_command("VerifyContractSecurity", "supplier"), "Waiting for the security to be verified.", f"security {version}", version, _supplier_side(case), role="Authorised signatory", state="Waiting")
		events.record(case, "Security recorded", actor, f"Performance security {reference.strip()} recorded.", security=row.name, amount=flt(amount))
		return records.summary(doc, security=row.name, security_version=version)

	return records.command("RecordContractSecurity", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "issuer": issuer, "beneficiary": beneficiary, "reference": reference, "amount": amount, "issued": issued_on, "expires": expires_on}, body=body, authorise=lambda: _preparer(actor, case))


def verify_security(case: str, *, security: str, expected_version: int, idempotency_key: str, actor: str, confirmation_reference: str, received_on: str, basis: str = "") -> dict[str, Any]:
	"""`VerifyContractSecurity`: HOP verifies from the issuer's confirmation. The beneficiary must be the procuring entity and the amount what the issued terms require."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(SECURITY, security)
		if row.contract_case != case or row.state != "Recorded":
			fail("CM_CHANGED", security=security, state=row.state)
		terms = _terms(case)
		need = requirement(terms) or {"amount": 0}
		entity = ((terms.get("parties") or {}).get("entity") or {}).get("name", "")
		problems = {"confirmation_reference": "" if cstr(confirmation_reference).strip() else "Enter the issuer's confirmation reference.", "received_on": "" if cstr(received_on).strip() else "Enter when the confirmation was received."}
		if entity and cstr(row.beneficiary).strip().lower() != entity.strip().lower():
			problems["confirmation_reference"] = problems["confirmation_reference"] or f"The beneficiary is {row.beneficiary}, not {entity}."
		if flt(row.amount) + 0.005 < flt(need["amount"]):
			problems["confirmation_reference"] = problems["confirmation_reference"] or f"The amount {flt(row.amount):,.2f} is less than the {flt(need['amount']):,.2f} the issued terms require."
		if getdate(row.expires_on) <= getdate(clock.now()):
			problems["confirmation_reference"] = problems["confirmation_reference"] or "The security has already expired."
		invalid(problems)
		records.update(row, state="Verified", confirmation_reference=confirmation_reference.strip(), confirmation_received_on=getdate(received_on), verification_basis=cstr(basis).strip() or "Issuer confirmation",
			verified_by=actor, verified_at=clock.now(), record_version=cint(row.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="VerifyContractSecurity", subject=f"security {row.version_no}", actor=actor)
		if doc.lifecycle in ("Active", "Terminated") and any(name != row.name for name in frappe.get_all(SECURITY, filters={"contract_case": case, "kind": "Performance security", "state": "Verified"}, pluck="name")):
			work.assign(case, "RecordSecurityAction", "Record the replacement security.", f"security {row.version_no}", row.version_no, work.holders(work.HOP), role=work.HOP)  # verified first, then it supersedes the old one
		events.record(case, "Security verified", actor, f"Performance security {row.reference} verified from the issuer's confirmation {confirmation_reference.strip()}.", security=row.name)
		return records.summary(doc, security=row.name)

	return records.command("VerifyContractSecurity", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "security": security, "confirmation": confirmation_reference, "received": received_on, "basis": basis}, body=body, authorise=lambda: _preparer(actor, case))


def reject_security(case: str, *, security: str, expected_version: int, idempotency_key: str, actor: str, reason: str) -> dict[str, Any]:
	"""`RejectContractSecurity`: the instrument and its reason are kept; the supplier is asked for a replacement and HOP for the next record."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"reason": "" if cstr(reason).strip() else "Enter the reason."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(SECURITY, security)
		if row.contract_case != case or row.state != "Recorded":
			fail("CM_CHANGED", security=security, state=row.state)
		records.update(row, state="Rejected", rejection_reason=reason.strip(), verified_by=actor, verified_at=clock.now(), record_version=cint(row.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="VerifyContractSecurity", subject=f"security {row.version_no}", actor=actor)
		nxt = row.version_no + 1
		work.assign(case, "RecordContractSecurity", "Record the replacement performance security.", f"security {nxt}", nxt, work.holders(work.HOP), role=work.HOP)
		work.assign(case, work.waiting_command("RecordContractSecurity", "supplier"), "Supply a replacement security.", f"security {nxt}", nxt, _supplier_side(case), role="Authorised signatory", state="Waiting")
		events.record(case, "Security rejected", actor, f"Performance security {row.reference} rejected: {reason.strip()}", security=row.name)
		return records.summary(doc, security=row.name)

	return records.command("RejectContractSecurity", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "security": security, "reason": reason}, body=body,
		authorise=lambda: _preparer(actor, case))
