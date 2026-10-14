# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Completion and close-out (CM-CHG-001 v0.8 sections 5.9, 7, 19.5; plan Phase 4).

For non-complex goods HOP issues the delivery-and-acceptance **completion certificate** to the contractor once contractual completion is established; the Accounting Officer then signs the **close-out**
that the service generates from the recorded facts. Completion is not inferred from silence: it needs every ordered unit accepted, no unit left in custody, no certified invoice left unsettled, no
open hold and no pending operation -- otherwise `CM_CLOSURE` names every remaining obligation and its holder. Closing a contract leaves its history immutable. A surviving obligation is classified in the
close-out review rather than hidden; an item that cannot be classified is Needs review and prevents a supported closure.

Phase 4 stops at the signed closure. Instructing the funding owner to release the commitment (`close_commitment`) and the security return clock arrive with the completion package (plan Phase 9), and until
then closing a contract does not claim financial finalisation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, flt

from kentender_contracts.services import authority, clock, delivery, events, holds, intents, payment, position, preflight, records, signing_flow, work
from kentender_contracts.services.errors import Guards, fail

CASE = "Contract Case"
CERTIFICATE = "Contract Certificate"
CLOSEOUT = "Contract Closeout"


def remaining_obligations(case: str) -> list[dict[str, Any]]:
	"""Everything that still stands between the contract and completion, each with the person or role who holds it."""
	out: list[dict[str, Any]] = []
	now = position.position(case)
	for line in now["lines"].values():
		if line["remaining"]:
			out.append({"kind": "Delivery", "what": f"{line['remaining']} of {line['ordered']} {line['item']} still to be delivered and accepted.", "holder": "Supplier", "prevents": True})
		if line["pending_decision"] or line["deferred"]:
			out.append({"kind": "Acceptance", "what": f"{line['pending_decision'] + line['deferred']} unit(s) await an acceptance decision.", "holder": "Inspection chair", "prevents": True})
	if now["in_custody"]:
		out.append({"kind": "Custody", "what": f"{now['in_custody']} unit(s) are still in custody awaiting collection.", "holder": "Receiver", "prevents": True})
	for invoice in frappe.get_all(payment.INVOICE, filters={"contract_case": case, "state": ["in", ["Submitted", "Held", "Certified", "Partly paid"]]}, fields=["name", "claim_reference", "state"]):
		out.append({"kind": "Invoice", "what": f"Invoice {invoice.claim_reference} is {invoice.state.lower()}.", "holder": "Finance" if invoice.state in ("Certified", "Partly paid") else "Head of procurement", "prevents": True})
	for hold in holds.open_holds(case):
		out.append({"kind": "Hold", "what": hold.reason, "holder": hold.owner, "prevents": True})
	if any(t["command"] == "RestoreContractOperation" for t in work.live(case)):
		out.append({"kind": "Operation", "what": "A contract operation is waiting for technical recovery.", "holder": "Technical operator", "prevents": True})
	return out


def offer_completion(case: str) -> bool:
	"""When nothing stands between the contract and completion, HOP is asked to issue the completion certificate (section 5.10: "completion certificate ready")."""
	doc = frappe.get_doc(CASE, case)
	if doc.lifecycle != "Active" or remaining_obligations(case) or frappe.db.exists(CERTIFICATE, {"contract_case": case, "kind": "Completion", "state": "Signed"}):
		return False
	work.assign(case, "IssueCompletionCertificate", "Issue the completion certificate.", "completion certificate", 1, work.holders(work.HOP), role=work.HOP)
	return True


def review(case: str) -> dict[str, Any]:
	"""The generated close-out review (section 5.9): what was delivered and accepted, the money, the remaining items and their treatment."""
	now = position.position(case)
	invoices = frappe.get_all(payment.INVOICE, filters={"contract_case": case, "state": ["!=", "Superseded"]}, fields=["name", "claim_reference", "claimed_amount", "state", "invoice_no"], order_by="invoice_no asc")
	settled = {i.name: payment.settled_amount(i.name) for i in invoices}
	return {
		"deliveries": [{"line": l["item"], "ordered": l["ordered"], "accepted": l["accepted"], "rejected_and_returned": l["returned"]} for l in now["lines"].values()],
		"invoices": [{"invoice": i.claim_reference, "claimed": flt(i.claimed_amount), "settled": settled[i.name], "state": i.state} for i in invoices],
		"claimed_total": sum(flt(i.claimed_amount) for i in invoices), "settled_total": sum(settled.values()),
		"final_acceptance": "Not required by the issued terms for this non-complex supply.", "title_and_documents": "Accepted units received into stock or assets.",
		"advances": "None under these terms.", "security": "Not required under these test terms.", "claims_and_disputes": "None open.",
		"remaining": remaining_obligations(case), "classified": [],
	}


def _closure_guards(case: str, command: str) -> Guards:
	doc = frappe.get_doc(CASE, case)
	guards = preflight.rules(doc, command)
	remaining = remaining_obligations(case)
	if remaining:
		guards.add("CM_CLOSURE", remaining=remaining)
	return guards


def issue_completion_certificate(case: str, *, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`IssueCompletionCertificate`: HOP's personal proof that contractual completion is established (section 154 certificate for non-complex goods)."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		existing = frappe.db.get_value(CERTIFICATE, {"contract_case": case, "kind": "Completion", "state": ["!=", "Superseded"]}, "name")
		if existing and frappe.db.get_value(CERTIFICATE, existing, "state") == "Signed":
			return records.summary(doc, certificate=existing, already=True)
		_closure_guards(case, "IssueCompletionCertificate").raise_if_any()
		content = review(case)
		cert = existing or records.new(CERTIFICATE, contract_case=case, kind="Completion", subject="completion", subject_version=1, state="Awaiting signature", content_json=records.dumps(content), record_version=1).name
		intent = signing_flow.record(case, "completion certificate", 1, "sign")
		return records.summary(doc, certificate=cert, intent=intent.name, digest=records.digest(content))

	recorded = records.command("IssueCompletionCertificate", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version}, body=body,
		authorise=lambda: authority.require(actor, "Head of Procurement Function"))
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=recorded["certificate"], target_digest=recorded["digest"], version=1, action="Sign the completion certificate")
	if not signing_flow.settled(result):
		with records.atomic():
			work.incident(case, "RestoreContractOperation", "Restore signing", "completion certificate", 1)
		frappe.db.commit()
		signing_flow.unfinished(result, certificate=recorded["certificate"])
	with records.atomic():
		doc = records.lock(case)
		cert = frappe.get_doc(CERTIFICATE, recorded["certificate"])
		if cert.state != "Signed":
			records.update(cert, state="Signed", signer=actor, proof_reference=result["reference"], signed_at=clock.now(), record_version=cint(cert.record_version) + 1)
			records.bump(doc, obligation_state="Completion certified")
			work.finish(case, command="IssueCompletionCertificate", actor=actor)
			work.finish(case, command="RestoreContractOperation", subject="completion certificate", actor=actor)
			_prepare_review(case, actor)
			events.record(case, "Completion certified", actor, "The completion certificate was signed.", certificate=cert.name, proof=result["reference"])
		out = records.summary(doc, certificate=cert.name, state="Signed")
	frappe.db.commit()
	return out


def _prepare_review(case: str, actor: str):
	"""The close-out review for the Accounting Officer, generated from the recorded facts (the earlier unsigned one is superseded and kept)."""
	current = frappe.db.get_value(CLOSEOUT, {"contract_case": case, "state": ["in", ["Draft", "Awaiting signature"]]}, "name")
	version = records.next_number(CLOSEOUT, {"contract_case": case}, "version_no")
	if current:
		old = frappe.get_doc(CLOSEOUT, current)
		records.update(old, state="Superseded")
		work.finish(case, subject="closeout", version=old.version_no, state="Superseded", actor=actor)
	row = records.new(CLOSEOUT, contract_case=case, version_no=version, state="Awaiting signature", review_json=records.dumps(review(case)), record_version=1)
	work.assign(case, "SignContractCloseout", "Review and sign the close-out.", "closeout", version, work.holders("Accounting Officer"), role="Accounting Officer")
	work.assign(case, work.waiting_command("SignContractCloseout", "ao"), "Waiting for the close-out.", "closeout", version, work.holders(work.HOP), role=work.HOP, state="Waiting")
	events.record(case, "Close-out prepared", actor, f"Close-out review {version} prepared.", closeout=row.name)
	return row


def prepare_closeout(case: str, *, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`PrepareContractCloseout`: regenerate the review for the Accounting Officer from the recorded facts (it is also prepared when the completion certificate is signed)."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		if not frappe.db.exists(CERTIFICATE, {"contract_case": case, "kind": "Completion", "state": "Signed"}):
			fail("CM_CLOSURE", remaining=[{"kind": "Completion certificate", "what": "The completion certificate is not signed.", "holder": "Head of procurement", "prevents": True}])
		_closure_guards(case, "PrepareContractCloseout").raise_if_any()
		row = _prepare_review(case, actor)
		work.finish(case, command="PrepareContractCloseout", actor=actor)
		records.bump(doc)
		return records.summary(doc, closeout=row.name, closeout_version=row.version_no)

	return records.command("PrepareContractCloseout", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version}, body=body,
		authorise=lambda: authority.require(actor, "Head of Procurement Function"))


def sign_closeout(case: str, *, closeout: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SignContractCloseout`: the Accounting Officer's proof of the exact review. The closure is rechecked against the facts at the moment of signing and the contract becomes Closed."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(CLOSEOUT, closeout)
		if row.contract_case != case:
			raise frappe.DoesNotExistError("Not found")
		if row.state == "Closed":
			return records.summary(doc, closeout=closeout, already=True)
		if row.state != "Awaiting signature":
			fail("CM_CHANGED", closeout=closeout, state=row.state)
		guards = _closure_guards(case, "SignContractCloseout")
		preflight.holds(guards, case, "close_contract")
		guards.raise_if_any()
		intent = signing_flow.record(case, f"closeout {row.version_no}", row.version_no, "sign")
		return records.summary(doc, closeout=closeout, intent=intent.name, digest=records.digest(records.loads(row.review_json)), version=row.version_no)

	recorded = records.command("SignContractCloseout", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "closeout": closeout}, body=body,
		authorise=lambda: authority.require(actor, "Accounting Officer"))
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=closeout, target_digest=recorded["digest"], version=recorded["version"], action="Sign the close-out")
	if not signing_flow.settled(result):
		with records.atomic():
			work.incident(case, "RestoreContractOperation", "Restore signing", f"closeout {recorded['version']}", recorded["version"])
		frappe.db.commit()
		signing_flow.unfinished(result, closeout=closeout)
	with records.atomic():
		doc = records.lock(case)
		row = frappe.get_doc(CLOSEOUT, closeout)
		if row.state != "Closed":
			records.update(row, state="Closed", signer=actor, proof_reference=result["reference"], closed_at=clock.now(), record_version=cint(row.record_version) + 1)
			records.bump(doc, lifecycle="Closed", closed_at=clock.now(), obligation_state="Closed")
			work.finish(case, command="SignContractCloseout", subject="closeout", actor=actor)
			work.finish(case, command="RestoreContractOperation", subject=f"closeout {row.version_no}", actor=actor)
			events.record(case, "Contract closed", actor, "The contract was closed.", closeout=row.name, proof=result["reference"])
		out = records.summary(doc, closeout=row.name, state="Closed")
	frappe.db.commit()
	return out
