# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Signing outside the system, as evidence (CM-CHG-001 v0.8 sections 5.3, 7, 19.4; boards D26, D26-H, D26-E; plan Phase 5, tracker CM8-505).

Where the issued terms permit it, a party may sign a paper or file copy of the agreement outside Contract Management. HOP records each party's evidence (who signed, in what capacity, on what date, and
the exact signed copy) and then **confirms** it; only the confirmation makes the signature, and it is never presented as an electronic signature proof: the signature's method says so and its reference is
the signed copy's own digest. The same checks apply as for an electronic signature: the contract must be out for signature, the method must be permitted by the issued terms, the person must be the one
whose authority the agreement names and who still holds it, and the copy must be the frozen version. A copy that no longer matches the version in force blocks confirmation (D26-H) and nothing is signed."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, getdate

from kentender_contracts.services import authority, clock, events, evidence, formation, formation_rules, holds, parties, people, preflight, records, work
from kentender_contracts.services.errors import fail, invalid

SIGNATURE = "Contract Signature"
CASE = "Contract Case"
METHOD = "Outside signature"
PARTY = {"supplier": "Supplier", "procuring entity": "Entity", "entity": "Entity"}


def permitted(terms: dict[str, Any]) -> tuple[bool, str]:
	signing = terms.get("signing") or {}
	return bool(signing.get("outside_permitted")), cstr(signing.get("basis"))


def party_of(value: str) -> str:
	found = PARTY.get(cstr(value).strip().lower())
	if not found:
		invalid({"party": "Choose the supplier or the procuring entity."})
	return found


def evidence_of(slot) -> dict[str, Any]:
	return records.loads(slot.evidence_json) if slot.get("evidence_json") else {}


def _preparer(actor: str, case: str) -> None:
	preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")


def _identifies(name: str, user: str) -> bool:
	given = cstr(name).strip().lower()
	return bool(given) and given in {cstr(user).lower(), cstr(people.full_name(user)).lower()}


def _signer_in_force(case: str, slot) -> None:
	"""The authority the agreement names must still hold at the time of recording and of confirming."""
	if slot.party == "Supplier":
		organisation = frappe.db.get_value(CASE, case, "supplier_organisation")
		if slot.signer.lower() not in {u.lower() for u in parties.signatories(organisation, clock.now())}:
			fail("CM_SEGREGATION", reason="This person is no longer an authorised signatory of the supplier.", signer=slot.signer)
	else:
		authority.require_capacity(case, slot.signer, "entity signatory")


def record_outside_signature(case: str, *, party: str, expected_version: int, idempotency_key: str, actor: str, signed_by: str, capacity: str, signed_on: str, copy: str, notes: str = "") -> dict[str, Any]:
	"""`RecordOutsideContractSignature`: one party's executed copy, as attributed evidence. Recording again before confirmation replaces the evidence and keeps the earlier in the history."""
	preflight.exists(case)
	which = party_of(party)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Awaiting signatures")
		agreement, slot = formation._slot(case, which)
		if slot is None or slot.state == "Signed":
			fail("CM_CHANGED", reason="This party's signature is already complete.")
		if slot.state == "Pending":
			fail("CM_HOLD", hold="uncertain signature", kind="Pending operation", reason="An electronic signature attempt for this party is still unconfirmed.", holder="Technical operator", clears_with="The attempt is recovered",
				consequence="new_signing_attempt")
		ok, basis = permitted(records.loads(agreement.terms_json))
		if not ok:
			fail("CM_RULE", rule="CM-R-01", name="Formation authority", hold_key="EXECUTION_METHOD_UNSUPPORTED", holder="Head of procurement function", reason="The issued terms do not permit signing outside the system.")
		problems = {
			"signed_by": "" if _identifies(signed_by, slot.signer) else f"This signature is for {people.full_name(slot.signer)}.",
			"capacity": "" if cstr(capacity).strip() else "Enter the capacity.",
			"signed_on": "",
		}
		day = records.day(signed_on)
		if day is None:
			problems["signed_on"] = "Enter the date the copy was signed."
		elif day > getdate(clock.now()):
			problems["signed_on"] = "The date cannot be in the future."
		elif agreement.frozen_at and day < getdate(agreement.frozen_at):
			problems["signed_on"] = "The agreement was not out for signature on that date."
		invalid(problems)
		_signer_in_force(case, slot)
		held = holds.blocking(case, "new_signing_attempt")
		if held:
			fail("CM_HOLD", hold=held[0].key, reason=held[0].reason, holder=held[0].owner, clears_with=held[0].clearing)
		checked = evidence.checked(copy, actor, field="copy")
		earlier = evidence_of(slot)
		entry = {"signed_by": signed_by.strip(), "capacity": capacity.strip(), "notes": cstr(notes).strip(), "file": checked["file"], "name": checked["name"], "digest": checked["digest"],
			"media_type": checked["media_type"], "check_result": checked["check_result"], "agreement_digest": agreement.rendered_digest, "recorded_by": actor, "recorded_at": str(clock.now())}
		if earlier:
			entry["replaces"] = {k: earlier.get(k) for k in ("file", "digest", "recorded_by", "recorded_at")}
		records.update(slot, state="Evidence recorded", signed_on=day, copy_reference=checked["file"], copy_digest=checked["digest"], method=METHOD, evidence_json=records.dumps(entry), record_version=cint(slot.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="RecordOutsideContractSignature", subject=f"outside {which.lower()} agreement {agreement.version_no}", actor=actor)
		_next(case, agreement, actor)
		events.record(case, "Outside signature recorded", actor, f"A signed copy for the {which.lower()} was recorded.", signature=slot.name, digest=checked["digest"])
		return records.summary(doc, signature=slot.name, party=which)

	return records.command("RecordOutsideContractSignature", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "party": which, "by": signed_by, "capacity": capacity, "on": signed_on, "copy": copy, "notes": notes}, body=body, authorise=lambda: _preparer(actor, case))


def _unsigned(case: str, agreement):
	return frappe.get_all(SIGNATURE, filters={"contract_case": case, "agreement_version": agreement.version_no, "state": ["!=", "Signed"]}, fields=["name", "party", "state", "sequence"], order_by="sequence asc")


def _next(case: str, agreement, actor: str) -> None:
	"""Once every party still to sign has evidence, HOP is asked to confirm it; until then HOP is asked for the other party's copy."""
	pending = _unsigned(case, agreement)
	if pending and all(s.state == "Evidence recorded" for s in pending):
		work.finish(case, command="RecordOutsideContractSignature", actor=actor)
		work.assign(case, "ConfirmOutsideSignatureEvidence", "Check the signed agreement.", f"outside agreement {agreement.version_no}", agreement.version_no, work.holders(work.HOP), role=work.HOP)
		return
	for s in pending:
		if s.state != "Evidence recorded":
			work.assign(case, "RecordOutsideContractSignature", f"Record the {s.party.lower()}'s signed agreement.", f"outside {s.party.lower()} agreement {agreement.version_no}", agreement.version_no,
				work.holders(work.HOP), role=work.HOP)


def confirm_outside_signature(case: str, *, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ConfirmOutsideSignatureEvidence`: the parties and the signed version are checked, then each recorded party's signature is made. The agreement is in force when the last one is."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Awaiting signatures")
		agreement = formation.current_agreement(case, "Awaiting signatures")
		pending = _unsigned(case, agreement)
		absent = [s.party for s in pending if s.state != "Evidence recorded"]
		if not pending or absent:
			fail("CM_CHANGED", reason=f"The {absent[0].lower()}'s signed copy has not been recorded." if absent else "There is nothing to confirm.")
		terms = records.loads(agreement.terms_json)
		if not permitted(terms)[0]:
			fail("CM_RULE", rule="CM-R-01", name="Formation authority", hold_key="EXECUTION_METHOD_UNSUPPORTED", holder="Head of procurement function", reason="The issued terms do not permit signing outside the system.")
		differs = [s.party for s in (frappe.get_doc(SIGNATURE, p.name) for p in pending) if evidence_of(s).get("agreement_digest") != agreement.rendered_digest]
		if differs:
			fail("CM_SOURCE", reason=f"The signed copies do not match agreement {agreement.version_no}.", parties=differs, agreement=agreement.version_no)
		guards = formation_rules.at_commit(terms, clock.now())
		if guards:
			fail("CM_HOLD", **guards[0])
		for p in pending:
			_signer_in_force(case, frappe.get_doc(SIGNATURE, p.name))
		events.record(case, "Outside signature evidence confirmed", actor, "The signed copies were checked and confirmed.", parties=[p.party for p in pending])
		return records.summary(doc, agreement=agreement.name, parties=[p.party for p in pending], slots=[p.name for p in pending])

	recorded = records.command("ConfirmOutsideSignatureEvidence", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version}, body=body, authorise=lambda: _preparer(actor, case))
	frappe.db.commit()
	last = {}
	slots = recorded.get("slots") or [s.name for s in frappe.get_all(SIGNATURE, filters={"contract_case": case, "state": "Evidence recorded"}, fields=["name"], order_by="sequence asc")]
	for name in slots:
		slot = frappe.get_doc(SIGNATURE, name)
		last = formation._apply_signature(case, slot.name, f"OUTSIDE-{cstr(slot.copy_digest)[:16]}", actor, METHOD, next_task=len(slots) == 1)
	work.finish(case, command="ConfirmOutsideSignatureEvidence", actor=actor)
	frappe.db.commit()
	return {**recorded, **last}
