# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Completion and close-out (CM-CHG-001 v0.8 sections 5.9, 7, 19.5; plan Phase 4).

For non-complex goods HOP issues the delivery-and-acceptance **completion certificate** to the contractor once contractual completion is established; the Accounting Officer then signs the **close-out**
that the service generates from the recorded facts. Completion is not inferred from silence: it needs every ordered unit accepted, no unit left in custody, no certified invoice left unsettled, no
open hold and no pending operation -- otherwise `CM_CLOSURE` names every remaining obligation and its holder. Closing a contract leaves its history immutable. A surviving obligation is classified in the
close-out review rather than hidden; an item that cannot be classified is Needs review and prevents a supported closure.

Phase 9 completes the path. Where the issued terms require the Accounting Officer's own **final acceptance** it comes first (`final_acceptance.py`); the head of procurement's completion certificate is then signed
and its **delivery to the contractor** is a further, evidenced fact the head confirms before the close-out review is generated for the Accounting Officer. An unresolved completion defect (an open warranty claim or a delivery
issue) stops completion and close-out and names its holder. Signing the close-out closes the contract and records one durable `Funding closure` operation for the funding owner: contract completion, accounting
settlement and the Budget commitment's closure stay three different facts, and until the owner acknowledges, the contract shows **Funding finalisation pending**. Surviving duties (a running warranty, a security still
held, a publication duty, work a correction kept) are classified in the review rather than hidden; an item that cannot be classified is Needs review and prevents a supported closure."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, flt

from kentender_contracts.services import authority, change, clock, delivery, events, final_acceptance, funding_closure, holds, intents, issues, obligations, payment, position, preflight, records, security_actions, signing_flow, warranty, work
from kentender_contracts.services.errors import Guards, fail, invalid

CASE = "Contract Case"
CERTIFICATE = "Contract Certificate"
CLOSEOUT = "Contract Closeout"
CLOSURE_EVENT = "ContractClosed"
CLOSURE_SUBJECT = "closure contract"


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
	for defect in final_acceptance.unresolved(case):
		out.append({"kind": "Completion defect", "what": defect["what"], "holder": defect["holder"], "prevents": True})
	if final_acceptance.required(case) and not final_acceptance.signed(case):
		out.append({"kind": "Final acceptance", "what": "The Accounting Officer has not recorded the final acceptance.", "holder": "Accounting Officer", "prevents": True})
	certificate = completion_certificate(case)
	if certificate is not None and not delivered(certificate):
		out.append({"kind": "Certificate delivery", "what": "Delivery of the completion certificate to the contractor is not evidenced.", "holder": "Head of procurement", "prevents": True})
	for item in survivors(case)[1]:
		out.append({"kind": "Needs review", "what": item["what"], "holder": item["owner"], "prevents": True})
	return out


# -- the completion certificate and its delivery ------------------------------------------------------------------------------------------
def completion_certificate(case: str):
	name = frappe.db.get_value(CERTIFICATE, {"contract_case": case, "kind": "Completion", "state": "Signed"}, "name", order_by="creation desc")
	return frappe.get_doc(CERTIFICATE, name) if name else None


def delivery_of(certificate) -> dict[str, Any]:
	return records.loads(certificate.delivery_json) if certificate is not None and certificate.get("delivery_json") else {}


def delivered(certificate) -> bool:
	"""The certificate reached the contractor: a delivery date with its evidence, not withdrawn by a correction."""
	found = delivery_of(certificate)
	return bool(found.get("delivered_on")) and not found.get("withdrawn")


def survivors(case: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	"""What outlives the closure, each with its owner, its due event and the term that lets it survive (classified), and what no term explains (unclassified: Needs review, and it prevents a supported closure)."""
	classified: list[dict[str, Any]] = []
	unclassified: list[dict[str, Any]] = []
	today = clock.now().date()
	ends = [e for e in (warranty.warranty_ends(case, u) for u, row in position.position(case)["units"].items() if row["status"] == "Accepted") if e]
	if ends and max(ends) > today:
		classified.append({"kind": "Warranty", "ref": "Warranty", "owner": issues.owner_of(case), "due": str(max(ends)), "basis": "The issued warranty term"})
	held = security_actions.operative(case)
	if held is not None:
		due = security_actions.return_due(case)
		classified.append({"kind": "Performance security", "ref": cstr(held.reference), "owner": next(iter(work.holders(work.HOP)), ""), "due": str(due) if due else "On the Accounting Officer's final acceptance", "basis": "The issued security term"})
	for row in obligations.all_for(case):
		if row.state not in ("Open", "Needs review") or row.kind == "Progress report" or (row.kind == "Security action" and held is not None):
			continue
		item = {"kind": row.kind, "ref": row.subject, "owner": row.owner_user, "due": str(row.due_at.date()) if row.due_at else cstr(row.due_basis), "basis": cstr(obligations.detail(row).get("basis") or row.rule)}
		if row.kind == "Other" and row.state == "Needs review":
			unclassified.append({**item, "what": f"{row.subject}: no term explains this surviving duty."})
		else:
			classified.append(item)
	return classified, unclassified


def funding_state(case: str) -> str:
	"""The commitment's closure in plain words: the three truthful states."""
	return {"Acknowledged": "Commitment closed by the funding owner", "Pending": "Funding finalisation pending", "Not requested": "Not requested"}[funding_closure.status(case, CLOSURE_SUBJECT)]


def offer_completion(case: str) -> bool:
	"""When nothing stands between the contract and completion, HOP is asked to issue the completion certificate (section 5.10: "completion certificate ready")."""
	doc = frappe.get_doc(CASE, case)
	if doc.lifecycle != "Active" or frappe.db.exists(CERTIFICATE, {"contract_case": case, "kind": "Completion", "state": "Signed"}):
		return False
	if final_acceptance.required(case) and not final_acceptance.signed(case):
		return final_acceptance.offer(case)  # the Accounting Officer's own acceptance comes first; the head of procurement is asked once it is recorded
	if remaining_obligations(case):
		return False
	work.assign(case, "IssueCompletionCertificate", "Issue the completion certificate.", "completion certificate", 1, work.holders(work.HOP), role=work.HOP)
	return True


def review(case: str) -> dict[str, Any]:
	"""The generated close-out review (section 5.9): what was delivered and accepted, the money, the remaining items and their treatment."""
	now = position.position(case)
	invoices = frappe.get_all(payment.INVOICE, filters={"contract_case": case, "state": ["!=", "Superseded"]}, fields=["name", "claim_reference", "claimed_amount", "state", "invoice_no"], order_by="invoice_no asc")
	settled = {i.name: payment.settled_amount(i.name) for i in invoices}
	accepted = final_acceptance.current(case)
	classified, _ = survivors(case)
	held = security_actions.operative(case)
	return {
		"deliveries": [{"line": l["item"], "ordered": l["ordered"], "accepted": l["accepted"], "rejected_and_returned": l["returned"]} for l in now["lines"].values()],
		"invoices": [{"invoice": i.claim_reference, "claimed": flt(i.claimed_amount), "settled": settled[i.name], "state": i.state} for i in invoices],
		"claimed_total": sum(flt(i.claimed_amount) for i in invoices), "settled_total": sum(settled.values()),
		"final_acceptance": f"Recorded on {frappe.utils.getdate(accepted.signed_at).strftime('%-d %B %Y')}" if accepted is not None and accepted.state == "Signed" else "Not required by the issued terms",
		"title_and_documents": "Accepted units received into stock or assets.", "advances": "None under these terms.",
		"security": ("Held until its return is recorded" if held is not None and held.state != "Returned" else "Returned" if held is not None else "Not required by the issued terms"),
		"claims_and_disputes": "None open.", "remaining": remaining_obligations(case), "classified": classified,
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
			work.assign(case, "ConfirmCertificateDelivery", "Confirm certificate delivery.", f"completion certificate {cert.subject_version}", cint(cert.subject_version), work.holders(work.HOP), role=work.HOP)
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


def confirm_certificate_delivery(case: str, *, certificate: str, delivered_on: str, method: str, reference: str = "", evidence: list[dict[str, Any]], expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ConfirmCertificateDelivery`: the head of procurement records that the signed certificate reached the contractor, with the day, the way and the proof. Signing is not delivery; only this fact lets the close-out review
	be generated, and the review is generated from it."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = frappe.get_doc(CERTIFICATE, certificate)
		if row.contract_case != case or row.kind != "Completion" or row.state != "Signed":
			fail("CM_CHANGED", certificate=certificate, state=row.state)
		if delivered(row):
			return records.summary(doc, certificate=row.name, already=True)
		problems = {"method": "" if cstr(method).strip() else "Say how the certificate was delivered.", "evidence": "" if evidence and all(cstr(e.get("label")).strip() for e in evidence) else "Attach the proof of delivery."}
		day = records.day(delivered_on)
		problems["delivered_on"] = "Enter the day the certificate was delivered." if day is None else "" if day <= clock.now().date() else "The delivery date cannot be in the future."
		invalid(problems)
		earlier = delivery_of(row)
		found = {"delivered_on": str(day), "method": cstr(method).strip(), "reference": cstr(reference).strip(), "evidence": evidence, "by": actor, "at": str(clock.now()), **({"previous": [earlier]} if earlier else {})}
		records.update(row, delivery_json=records.dumps(found), record_version=cint(row.record_version) + 1)
		work.finish(case, command="ConfirmCertificateDelivery", subject=f"completion certificate {row.subject_version}", actor=actor)
		events.record(case, "Certificate delivered", actor, f"The completion certificate was delivered to the contractor on {day.strftime('%-d %B %Y')}.", certificate=row.name)
		review_row = _prepare_review(case, actor)
		records.bump(doc)
		return records.summary(doc, certificate=row.name, closeout=review_row.name, closeout_version=review_row.version_no)

	return records.command("ConfirmCertificateDelivery", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "certificate": certificate, "on": delivered_on, "method": method, "reference": reference,
		"evidence": evidence}, body=body, authorise=lambda: authority.require(actor, "Head of Procurement Function"))


def return_review(case: str, *, stage: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ReturnContractCloseout`: the Accounting Officer sends the final acceptance or the close-out review back with a reason. The review is superseded and kept; the head of procurement, who prepared the completion, is asked to
	put the evidence right and send it back."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		invalid({"stage": "" if stage in ("final acceptance", "close-out") else "Say what is being returned.", "reason": "" if cstr(reason).strip() else "Enter the reason for returning it."})
		if stage == "final acceptance":
			if final_acceptance.signed(case) or not final_acceptance.required(case):
				fail("CM_CHANGED", reason="There is no final acceptance waiting to be returned.")
			work.finish(case, command="SignFinalContractAcceptance", subject=final_acceptance.SUBJECT, actor=actor)
			title = "Correct the final acceptance evidence and send it back."
		else:
			name = frappe.db.get_value(CLOSEOUT, {"contract_case": case, "state": "Awaiting signature"}, "name")
			if not name:
				fail("CM_CHANGED", reason="There is no close-out review waiting to be returned.")
			row = frappe.get_doc(CLOSEOUT, name)
			records.update(row, state="Superseded", record_version=cint(row.record_version) + 1)
			work.finish(case, subject="closeout", version=row.version_no, state="Superseded", actor=actor)
			title = "Correct the close-out review and send it back."
		work.assign(case, "PrepareContractCloseout", title, f"{stage} return", 1, work.holders(work.HOP), role=work.HOP)
		events.record(case, "Completion returned", actor, f"The {stage} was returned for correction: {cstr(reason).strip()}", stage=stage)
		records.bump(doc)
		return records.summary(doc, returned=stage)

	return records.command("ReturnContractCloseout", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "stage": stage, "reason": reason}, body=body,
		authorise=lambda: authority.require(actor, "Accounting Officer"))


def prepare_closeout(case: str, *, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`PrepareContractCloseout`: regenerate the review for the Accounting Officer from the recorded facts (it is also prepared when the completion certificate is signed)."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		if final_acceptance.required(case) and not final_acceptance.signed(case) and completion_certificate(case) is None:
			final_acceptance.offer(case)  # a returned final acceptance goes back to the Accounting Officer once the head of procurement has put the evidence right
			work.finish(case, command="PrepareContractCloseout", actor=actor)
			records.bump(doc)
			return records.summary(doc, resent="final acceptance")
		if completion_certificate(case) is None:
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
			if funding_closure.status(case, CLOSURE_SUBJECT) != "Acknowledged":  # a contract reopened and closed again keeps the one acknowledged closure
				funding_closure.request(case, subject=CLOSURE_SUBJECT, version=1, final_amount=flt(change.operative_terms(case).get("total")), event_type=CLOSURE_EVENT, evidence=[row.name], actor=actor)
		out = records.summary(doc, closeout=row.name, state="Closed")
	frappe.db.commit()
	funding_closure.carry_out(case, actor)  # the owner acknowledges separately; a closure it has not acknowledged is shown as pending, and never undoes the closing
	return out
