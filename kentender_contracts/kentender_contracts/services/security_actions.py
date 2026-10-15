# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Actions on a verified security after the agreement is in force (CM-CHG-001 v0.8 sections 5.20, 7, 19.3 CM-R-09 and LQ-03; plan Phase 8; boards D16, D37, D37-A, D37-P, D37-X).

The security was recorded and verified before signing (`security.py`). From then on it can be **claimed**, **replaced** or **extended**, and **returned**; it is never released because it expired.

* A claim has four facts that are never one: the request (the custodian's grounds, amount and the claimant's mandate), the Accounting Officer's decision, the communication actually delivered to the issuer, and the
  issuer's actual outcome with the proceeds. A request or a decision never means the issuer paid, and cash received is a Finance recovery recorded separately.
* A replacement or an extension is recorded and **verified first**; only then does it supersede the old instrument, and only when the two overlap. Until then the old instrument stays operative and the coverage gap is a
  visible hold, not a release.
* A return needs the Accounting Officer's evidenced final acceptance; the profile's return period runs from that event (not from committee acceptance, payment or warranty expiry), and no claim may be open."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, cint, cstr, flt, getdate

from kentender_contracts.services import authority, clock, events, holds, preflight, records, security, segregation, work
from kentender_contracts.services.errors import fail, invalid

CLAIM = "Contract Security Claim"
SECURITY = "Contract Security"
CASE = "Contract Case"
CERTIFICATE = "Contract Certificate"
DECISIONS = {"Approve": "Approved", "Decline": "Declined", "Return": "Returned"}
OPEN_CLAIM = ("Requested", "Approved", "Communicated")


def get_claim(case: str, number: int):
	name = frappe.db.get_value(CLAIM, {"contract_case": case, "claim_no": number}, "name")
	return frappe.get_doc(CLAIM, name) if name else None


def live_claim(case: str):
	name = frappe.db.get_value(CLAIM, {"contract_case": case, "state": ["in", list(OPEN_CLAIM) + ["Returned"]]}, "name", order_by="claim_no desc")
	return frappe.get_doc(CLAIM, name) if name else None


def subject_of(row) -> str:
	return f"security claim {row.claim_no}"


def operative(case: str):
	"""The performance security in force: the oldest verified one not yet superseded or returned. A verified replacement does not take over until it is recorded as the replacement (`replace`), so there is no moment with no cover."""
	name = frappe.db.get_value(SECURITY, {"contract_case": case, "kind": "Performance security", "state": "Verified"}, "name", order_by="version_no asc")
	return frappe.get_doc(SECURITY, name) if name else None


def _preparer(case: str, actor: str) -> None:
	preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")


def _evidence(value: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
	return [{"label": cstr(e.get("label")).strip(), "file": cstr(e.get("file")).strip()} for e in value or [] if cstr(e.get("label")).strip()]


# -- the claim ----------------------------------------------------------------------------------------------------------------------------
def request_claim(case: str, *, grounds: str, amount: float, recipient: str, mandate: str, evidence: list[dict[str, Any]], expected_version: int, idempotency_key: str, actor: str, correcting: int = 0) -> dict[str, Any]:
	"""`RequestSecurityClaim`: the custodian's grounds, the amount (never above the instrument), the recipient and the claimant's mandate, with the evidence the claim rests on."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active", "Terminated")
		instrument = operative(case)
		if instrument is None:
			fail("CM_CHANGED", reason="There is no verified performance security to claim on.")
		problems = {"grounds": "" if cstr(grounds).strip() else "State the grounds.", "mandate": "" if cstr(mandate).strip() else "Name the claimant's authority.",
			"evidence": "" if _evidence(evidence) else "Attach the evidence the claim rests on."}
		if flt(amount) <= 0:
			problems["amount"] = "Enter the amount claimed."
		elif flt(amount) > flt(instrument.amount) + 0.005:
			problems["amount"] = f"The claim cannot exceed the instrument's {flt(instrument.amount):,.2f}."
		invalid(problems)
		if getdate(instrument.expires_on) < getdate(clock.now()):
			fail("CM_HOLD", hold="security expired", kind="Instrument", reason=f"The instrument expired on {getdate(instrument.expires_on).strftime('%-d %B %Y')}; a claim must be made while it is in force.", holder="Head of procurement function",
				clears_with="A replacement or extension is verified", consequence="RequestSecurityClaim")
		current = live_claim(case)
		returned = get_claim(case, correcting) if correcting else None
		if returned is not None and returned.state != "Returned":
			fail("CM_CHANGED", claim=returned.name, state=returned.state)
		if current is not None and (returned is None or current.name != returned.name):
			fail("CM_CHANGED", reason="A claim on this security is already in progress.", claim=current.name)
		parts = dict(security=instrument.name, grounds=cstr(grounds).strip(), amount=flt(amount), mandate=cstr(mandate).strip(), recipient=cstr(recipient).strip() or instrument.issuer, evidence_json=records.dumps(_evidence(evidence)))
		if returned is None:
			number = records.next_number(CLAIM, {"contract_case": case}, "claim_no")
			row = records.new(CLAIM, contract_case=case, claim_no=number, state="Requested", decision_json=records.dumps({}), communication_json=records.dumps({}), outcome_json=records.dumps({}), prepared_by=actor, prepared_at=clock.now(),
				record_version=1, **parts)
		else:
			row = returned
			records.update(row, state="Requested", record_version=cint(row.record_version) + 1, **parts)
			work.finish(case, command="RequestSecurityClaim", subject=subject_of(row), actor=actor)
		work.assign(case, "DecideSecurityClaim", "Decide the security claim.", subject_of(row), cint(row.record_version), work.holders("Accounting Officer"), role="Accounting Officer")
		events.record(case, "Security claim requested", actor, f"A claim of {flt(amount):,.2f} on {instrument.reference} was requested.", claim=row.name, security=instrument.name)
		records.bump(doc)
		return records.summary(doc, claim=row.name, claim_no=row.claim_no)

	return records.command("RequestSecurityClaim", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "grounds": grounds, "amount": amount, "recipient": recipient, "mandate": mandate,
		"evidence": evidence, "correcting": correcting}, body=body, authorise=lambda: _preparer(case, actor))


def decide_claim(case: str, *, claim: int, decision: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`DecideSecurityClaim`: the Accounting Officer approves, declines or returns the exact claim with a reason. The decision gives no cash status and the amount is the request's."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active", "Terminated")
		row = get_claim(case, claim)
		if row is None or row.state != "Requested":
			fail("CM_CHANGED", claim=claim, state=row.state if row else "")
		invalid({"decision": "" if decision in DECISIONS else "Choose approve, decline or return.", "reason": "" if cstr(reason).strip() else "Enter the reason for the decision."})
		segregation.preparer_not_decider(actor, [row.prepared_by], what="claim")
		state = DECISIONS[decision]
		records.update(row, state=state, decision_json=records.dumps({"outcome": state, "reason": cstr(reason).strip(), "by": actor, "at": str(clock.now())}), record_version=cint(row.record_version) + 1)
		work.finish(case, command="DecideSecurityClaim", subject=subject_of(row), actor=actor)
		if state == "Approved":
			work.assign(case, "RecordSecurityClaimCommunication", "Send the approved claim to the issuer.", subject_of(row), cint(row.record_version), work.holders(work.HOP), role=work.HOP)
		elif state == "Returned":
			work.assign(case, "RequestSecurityClaim", "Correct the security claim.", subject_of(row), cint(row.record_version), [row.prepared_by], role=work.HOP)
		events.record(case, f"Security claim {state.lower()}", actor, f"Security claim {row.claim_no} {state.lower()}.", claim=row.name, reason=cstr(reason).strip())
		records.bump(doc)
		return records.summary(doc, claim=row.name, state=state)

	return records.command("DecideSecurityClaim", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "claim": claim, "decision": decision, "reason": reason},
		body=body, authorise=lambda: authority.require(actor, "Accounting Officer"))


def record_communication(case: str, *, claim: int, sent_on: str, channel: str, reference: str, evidence: list[dict[str, Any]], expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordSecurityClaimCommunication`: the claim as actually delivered to the issuer, with its evidence. Only now is the issuer's response awaited."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = get_claim(case, claim)
		if row is None or row.state != "Approved":
			fail("CM_CHANGED", claim=claim, state=row.state if row else "")
		try:
			day = getdate(sent_on)
		except Exception:  # noqa: BLE001
			day = None
		invalid({"sent_on": "" if day else "Enter the day the claim was delivered.", "channel": "" if cstr(channel).strip() else "Enter how it was delivered.", "reference": "" if cstr(reference).strip() else "Enter the delivery reference.",
			"evidence": "" if _evidence(evidence) else "Attach the proof of delivery."})
		records.update(row, state="Communicated", communication_json=records.dumps({"sent_on": str(day), "channel": cstr(channel).strip(), "reference": cstr(reference).strip(), "evidence": _evidence(evidence), "by": actor, "at": str(clock.now())}),
			record_version=cint(row.record_version) + 1)
		work.finish(case, command="RecordSecurityClaimCommunication", subject=subject_of(row), actor=actor)
		work.assign(case, "RecordSecurityClaimOutcome", f"{row.recipient} must respond to the approved claim; communication delivered {day.strftime('%-d %b %Y')}.", subject_of(row), cint(row.record_version), work.holders(work.HOP), role=work.HOP, state="Waiting")
		events.record(case, "Security claim communicated", actor, f"Claim {row.claim_no} was delivered to {row.recipient} on {day.strftime('%-d %B %Y')}.", claim=row.name, reference=cstr(reference).strip())
		records.bump(doc)
		return records.summary(doc, claim=row.name, state="Communicated")

	return records.command("RecordSecurityClaimCommunication", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "claim": claim, "sent": sent_on, "channel": channel, "reference": reference,
		"evidence": evidence}, body=body, authorise=lambda: _preparer(case, actor))


def record_outcome(case: str, *, claim: int, issuer_reference: str, outcome_on: str, evidence: list[dict[str, Any]], proceeds: float, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordSecurityClaimOutcome`: what the issuer actually did, with its reference, date, evidence and the proceeds. A cash receipt is Finance's recovery and confirmation, recorded separately."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = get_claim(case, claim)
		if row is None or row.state != "Communicated":
			fail("CM_CHANGED", claim=claim, state=row.state if row else "")
		try:
			day = getdate(outcome_on)
		except Exception:  # noqa: BLE001
			day = None
		problems = {"issuer_reference": "" if cstr(issuer_reference).strip() else "Enter the issuer's reference.", "outcome_on": "" if day else "Enter the date of the outcome.", "evidence": "" if _evidence(evidence) else "Attach the issuer's outcome."}
		if flt(proceeds) < 0 or flt(proceeds) > flt(row.amount) + 0.005:
			problems["proceeds"] = f"The proceeds are between 0 and the claim of {flt(row.amount):,.2f}."
		invalid(problems)
		records.update(row, state="Outcome recorded", outcome_json=records.dumps({"issuer_reference": cstr(issuer_reference).strip(), "on": str(day), "evidence": _evidence(evidence), "proceeds": flt(proceeds), "by": actor, "at": str(clock.now())}),
			record_version=cint(row.record_version) + 1)
		work.finish(case, command="RecordSecurityClaimOutcome", subject=subject_of(row), actor=actor)
		events.record(case, "Security claim outcome recorded", actor, f"{row.recipient} answered claim {row.claim_no} (their reference {cstr(issuer_reference).strip()}): {flt(proceeds):,.2f} proceeds. A cash receipt is recorded by Finance separately.", claim=row.name, proceeds=flt(proceeds))
		records.bump(doc)
		return records.summary(doc, claim=row.name, state="Outcome recorded", proceeds=flt(proceeds))

	return records.command("RecordSecurityClaimOutcome", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "claim": claim, "reference": issuer_reference, "on": outcome_on,
		"evidence": evidence, "proceeds": proceeds}, body=body, authorise=lambda: _preparer(case, actor))


# -- replacing and extending ----------------------------------------------------------------------------------------------------------------
def replace(case: str, *, security_name: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordSecurityAction` (Replace / Extend): a replacement that has been **verified** supersedes the instrument in force, but only if the two overlap; a gap in coverage is a held issue and the old one stays operative."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active", "Terminated")
		new = frappe.get_doc(SECURITY, security_name)
		old = operative(case)
		if new.contract_case != case or new.kind != "Performance security" or new.state != "Verified":
			fail("CM_CHANGED", security=security_name, state=new.state, reason="Only a verified instrument can replace the one in force.")
		if old is None or old.name == new.name:
			fail("CM_CHANGED", reason="There is no other instrument in force to replace.")
		if flt(new.amount) + 0.005 < flt(old.amount):
			invalid({"amount": f"The replacement's {flt(new.amount):,.2f} is less than the {flt(old.amount):,.2f} it replaces."})
		if getdate(new.issued_on) > getdate(old.expires_on):
			fail("CM_HOLD", hold="security coverage gap", kind="Instrument", reason=f"The replacement starts on {getdate(new.issued_on).strftime('%-d %B %Y')}, after the instrument in force expires on {getdate(old.expires_on).strftime('%-d %B %Y')}.",
				holder="Head of procurement function", clears_with="A replacement that overlaps the instrument in force is verified", consequence="RecordSecurityAction")
		records.update(old, state="Superseded", record_version=cint(old.record_version) + 1)
		work.finish(case, command="RecordSecurityAction", subject=f"security {new.version_no}", actor=actor)
		events.record(case, "Security replaced", actor, f"Security {new.reference} replaced {old.reference} (expiry {getdate(old.expires_on).strftime('%-d %B %Y')} to {getdate(new.expires_on).strftime('%-d %B %Y')}).", old=old.name, new=new.name)
		records.bump(doc)
		return records.summary(doc, security=new.name, replaced=old.name)

	return records.command("RecordSecurityAction", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "action": "Replace", "security": security_name}, body=body, authorise=lambda: _preparer(case, actor))


# -- return -----------------------------------------------------------------------------------------------------------------------------------
def final_acceptance(case: str) -> dict[str, Any] | None:
	"""The Accounting Officer's evidenced final acceptance: the event the return clock starts from. None until it is recorded."""
	name = frappe.db.get_value(CERTIFICATE, {"contract_case": case, "kind": "Final acceptance", "state": "Signed"}, "name", order_by="creation desc")
	if not name:
		return None
	row = frappe.get_doc(CERTIFICATE, name)
	return {"certificate": name, "at": row.signed_at, "on": getdate(row.signed_at)}


def return_due(case: str):
	"""The last day for returning the security: the profile's days after the final acceptance. None until there is a final acceptance."""
	found = final_acceptance(case)
	if found is None:
		return None
	days = preflight.profile(frappe.get_doc(CASE, case)).parameter("security_return_days").value
	return add_days(found["on"], cint(days))


def on_final_acceptance(case: str, actor: str = "") -> None:
	"""The Accounting Officer's final acceptance was evidenced: the security's return is a duty with a verified due date (the profile's days after it), and the custodian is asked to record it."""
	from kentender_contracts.services import obligations

	instrument = operative(case)
	due = return_due(case)
	if instrument is None or due is None:
		return
	obligations.open_obligation(case, kind="Security action", rule="CM-R-09", trigger_event="Final acceptance recorded", trigger_at=final_acceptance(case)["at"], subject=f"security {instrument.version_no} return",
		owner=next(iter(work.holders(work.HOP)), ""), due_at=due, due_basis="The profile's days after the Accounting Officer's evidenced final acceptance", state="Open", recipient=instrument.issuer)
	work.assign(case, "RecordSecurityAction", "Record the security return.", f"security {instrument.version_no} return", 1, work.holders(work.HOP), role=work.HOP, due=due, due_verified=True)


def record_return(case: str, *, returned_on: str, evidence: list[dict[str, Any]], expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordSecurityAction` (Authorise return / Record return): after the evidenced final acceptance, with no claim open, the custodian records the actual return with its bank or issuer discharge. Expiry releases nothing."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active", "Closed", "Terminated")
		instrument = operative(case)
		if instrument is None:
			fail("CM_CHANGED", reason="There is no performance security in force to return.")
		accepted = final_acceptance(case)
		if accepted is None:
			fail("CM_HOLD", hold="FINAL_ACCEPTANCE_NOT_EVIDENCED", kind="Rule", reason="The Accounting Officer's final acceptance has not been recorded; the security is not returned on expiry or on committee acceptance.",
				holder="Accounting Officer", clears_with="The final acceptance is evidenced", consequence="RecordSecurityAction")
		guards = preflight.rules(doc, "RecordSecurityAction")
		guards.raise_if_any()
		open_claim = live_claim(case)
		if open_claim is not None and open_claim.state != "Declined":
			fail("CM_HOLD", hold="security claim open", kind="Claim", reason="A claim on this security is still in progress.", holder="Head of procurement function", clears_with="The claim is declined or its outcome is recorded", consequence="RecordSecurityAction")
		try:
			day = getdate(returned_on)
		except Exception:  # noqa: BLE001
			day = None
		invalid({"returned_on": "" if day else "Enter the return date.", "evidence": "" if _evidence(evidence) else "Attach the discharge evidence."})
		if day < accepted["on"]:
			invalid({"returned_on": "The security cannot be returned before the final acceptance."})
		records.update(instrument, state="Returned", return_json=records.dumps({"on": str(day), "evidence": _evidence(evidence), "by": actor, "at": str(clock.now()), "final_acceptance": str(accepted["on"]), "due": str(return_due(case))}),
			record_version=cint(instrument.record_version) + 1)
		work.finish(case, command="RecordSecurityAction", subject=f"security {instrument.version_no} return", actor=actor)
		from kentender_contracts.services import obligations

		obligations.satisfy(case, "Security action", f"security {instrument.version_no} return", f"Returned on {day.strftime('%-d %B %Y')}")
		events.record(case, "Security returned", actor, f"Security {instrument.reference} was returned on {day.strftime('%-d %B %Y')}.", security=instrument.name)
		records.bump(doc)
		return records.summary(doc, security=instrument.name, state="Returned")

	return records.command("RecordSecurityAction", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "action": "Return", "on": returned_on, "evidence": evidence}, body=body,
		authorise=lambda: _preparer(case, actor))
