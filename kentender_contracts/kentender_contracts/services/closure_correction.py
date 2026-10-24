# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Close-out correction and reopening (CM-CHG-001 v0.8 sections 5.9, 5.18 last row, 5.21, 7; plan Phase 9; boards D38-P, D38, D38-R, D38-T).

Closed records are immutable history. When evidence shows that a completion fact was wrong, the head of procurement prepares a reasoned correction request naming the closure, the fact and the evidence; the Accounting
Officer, who did not prepare it, **returns** it, **confirms the closure remains valid** with explicit surviving work, or **reopens** the contract. Reopening is a successor decision: the original closure stays, the
lifecycle returns to Active **only for a previously Closed contract**, nothing the funding owner or the native records did is undone, and the head of procurement is asked to put the corrected fact right. A completion rule
that requires the evidence cannot be bypassed by confirming the closure. A Terminated contract is never reopened here: correcting a termination needs its own legal authority and a separate effective record."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_contracts.services import authority, clock, events, final_acceptance, obligations, picker_sources, preflight, records, segregation, work
from kentender_contracts.services.errors import fail, invalid

COR = "Contract Correction"
CLOSEOUT = "Contract Closeout"
CERTIFICATE = "Contract Certificate"
CASE = "Contract Case"
FACTS = ("Certificate delivery", "Final acceptance", "Other completion fact")
#: The facts a completion rule requires evidence for: the closure cannot be confirmed without them.
REQUIRED_FACTS = ("Certificate delivery", "Final acceptance")
DECISIONS = {"Reopen": "Reopened", "Keep": "Kept closed", "Return": "Returned"}


def get(case: str, number: int):
	name = frappe.db.get_value(COR, {"contract_case": case, "correction_no": number}, "name")
	return frappe.get_doc(COR, name) if name else None


def live(case: str):
	name = frappe.db.get_value(COR, {"contract_case": case, "state": ["in", ["Draft", "Submitted", "Returned"]]}, "name", order_by="correction_no desc")
	return frappe.get_doc(COR, name) if name else None


def subject_of(row) -> str:
	return f"correction {row.correction_no}"


def evidence(row) -> list[dict[str, Any]]:
	return records.loads(row.evidence_json, [])


def last_closure(case: str):
	name = frappe.db.get_value(CLOSEOUT, {"contract_case": case, "state": "Closed"}, "name", order_by="version_no desc")
	return frappe.get_doc(CLOSEOUT, name) if name else None


def prepare(case: str, *, fact: str, reason: str, evidence_files: list[dict[str, Any]], disposition: str = "Reopen for completion", submit: bool = True, correcting: int = 0, expected_version: int, idempotency_key: str,
		actor: str) -> dict[str, Any]:
	"""`PrepareContractClosureCorrection`: the head of procurement's reasoned request. A draft is saved without an Accounting Officer task; submitting creates the exact decision task."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Head of Procurement Function")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		if doc.lifecycle == "Terminated":
			fail("CM_CHANGED", lifecycle=doc.lifecycle, reason="A termination is not corrected here: it needs its own legal authority and a separate effective record.")
		preflight.lifecycle(doc, "Closed")
		closure = last_closure(case)
		if closure is None:
			fail("CM_CHANGED", reason="There is no close-out to correct.")
		problems = {"fact": "" if fact in FACTS else "Name the completion fact that was wrong."}
		if submit:
			problems.update({"reason": "" if cstr(reason).strip() else "Explain the completion error.", "evidence": "" if evidence_files and all(cstr(e.get("label")).strip() for e in evidence_files) else "Attach the evidence."})
		invalid(problems)
		current = live(case)
		if current is not None and (not correcting or current.correction_no != correcting):
			fail("CM_CHANGED", reason="A correction of this close-out is already in progress.", correction=current.name)
		fields = dict(closeout=closure.name, reason=cstr(reason).strip(), evidence_json=records.dumps(evidence_files or []), disposition=cstr(disposition).strip(), survivors_json=records.dumps({"fact": fact}),
			state="Submitted" if submit else "Draft")
		if current is None:
			number = records.next_number(COR, {"contract_case": case}, "correction_no")
			row = records.new(COR, contract_case=case, correction_no=number, decision_json=records.dumps({}), requested_by=actor, requested_at=clock.now(), record_version=1, **fields)
		else:
			row = current
			records.update(row, record_version=cint(row.record_version) + 1, **fields)
			work.finish(case, command="PrepareContractClosureCorrection", subject=subject_of(row), actor=actor)
		if submit:
			work.assign(case, "ConfirmContractClosure", "Decide the correction.", subject_of(row), cint(row.record_version), work.holders("Accounting Officer"), role="Accounting Officer")
			events.record(case, "Close-out correction submitted", actor, f"Correction {row.correction_no} of the close-out was submitted: {cstr(reason).strip()}", correction=row.name, fact=fact)
		records.bump(doc)
		return records.summary(doc, correction=row.name, correction_no=row.correction_no, state=row.state)

	return records.command("PrepareContractClosureCorrection", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "fact": fact, "reason": reason, "evidence": evidence_files,
		"disposition": disposition, "submit": submit, "correcting": correcting}, body=body, authorise=authorise)


def fact_of(row) -> str:
	return cstr(records.loads(row.survivors_json).get("fact"))


def decide(case: str, *, correction: int, decision: str, reason: str, survivors: list[dict[str, Any]] | None = None, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ReopenContractCloseout` / `ConfirmContractClosure` / `ReturnContractCloseout`: the Accounting Officer reopens, confirms the closure remains valid with explicit surviving work, or returns the request."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Accounting Officer")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = get(case, correction)
		if row is None or row.state != "Submitted":
			fail("CM_CHANGED", correction=correction, state=row.state if row else "")
		if doc.lifecycle == "Terminated":
			fail("CM_CHANGED", lifecycle=doc.lifecycle, reason="A termination is not corrected here.")
		preflight.lifecycle(doc, "Closed")
		invalid({"decision": "" if decision in DECISIONS else "Choose reopen, keep closed or return.", "reason": "" if cstr(reason).strip() else "Enter the reason for the decision."})
		segregation.preparer_not_decider(actor, [row.requested_by], what="correction")
		state = DECISIONS[decision]
		named = [{"kind": cstr(s.get("kind")), "ref": cstr(s.get("ref")), "owner": cstr(s.get("owner")), "due": cstr(s.get("due")), "basis": cstr(s.get("basis")).strip()} for s in survivors or []]
		if decision == "Keep":
			if fact_of(row) in REQUIRED_FACTS:
				fail("CM_RECONCILE", correction=row.name, reason="The completion rule requires this evidence, so the closure cannot be confirmed without it.", fact=fact_of(row))
			invalid({"survivors": "" if named and all(s["kind"] and s["owner"] and s["basis"] for s in named) else "Name each surviving item with its owner and the term that lets it survive."})
			invalid({"survivor_owner": "" if all(picker_sources.eligible_owner(s["owner"]) for s in named) else "Choose a person who holds a contract responsibility as the owner."})
		stamp = {"outcome": state, "reason": cstr(reason).strip(), "by": actor, "at": str(clock.now()), "survivors": named}
		records.update(row, state=state, decision_json=records.dumps(stamp), decided_by=actor, decided_at=clock.now(), record_version=cint(row.record_version) + 1)
		work.finish(case, command="ConfirmContractClosure", subject=subject_of(row), actor=actor)
		if state == "Returned":
			work.assign(case, "PrepareContractClosureCorrection", "Correct the close-out correction request.", subject_of(row), cint(row.record_version), [row.requested_by], role=work.HOP)
		elif state == "Reopened":
			_reopen(doc, row, actor)
		else:
			for s in named:  # explicit surviving work keeps its owner, its due event and the term that lets it survive, as a duty on the contract's obligations
				obligations.open_obligation(case, kind="Other", rule="CM-R-16", trigger_event="Close-out confirmed with surviving work", trigger_at=clock.now(), subject=f"surviving {s['kind'].lower()} {s['ref']}".strip(), owner=s["owner"], due_basis=s["due"] or "On the named due event",
					state="Open", facts={"basis": s["basis"], "correction": row.name})
		events.record(case, f"Close-out correction {state.lower()}", actor, f"Correction {row.correction_no} of the close-out: {state.lower()}.", correction=row.name, reason=cstr(reason).strip())
		records.bump(doc)
		return records.summary(doc, correction=row.name, state=state)

	return records.command("ReopenContractCloseout" if decision == "Reopen" else "ReturnContractCloseout" if decision == "Return" else "ConfirmContractClosure", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "correction": correction, "decision": decision, "reason": reason, "survivors": survivors or []}, body=body, authorise=authorise)


def _reopen(doc, row, actor: str) -> None:
	"""The successor decision: the contract is Active again, the original closure stays as history, and the head of procurement is asked to put right the fact that was wrong. Nothing is restored in funding or in the
	native records."""
	case = doc.name
	records.bump(doc, lifecycle="Active", obligation_state="Reopened")
	fact = fact_of(row)
	certificate = frappe.db.get_value(CERTIFICATE, {"contract_case": case, "kind": "Completion", "state": "Signed"}, "name")
	if fact == "Certificate delivery" and certificate:
		certificate_doc = frappe.get_doc(CERTIFICATE, certificate)
		records.update(certificate_doc, delivery_json=records.dumps({**records.loads(certificate_doc.delivery_json), "withdrawn": {"by": actor, "at": str(clock.now()), "correction": row.name}}), record_version=cint(certificate_doc.record_version) + 1)
		work.assign(case, "ConfirmCertificateDelivery", "Confirm certificate delivery.", f"completion certificate {certificate_doc.subject_version}", cint(certificate_doc.subject_version), work.holders(work.HOP), role=work.HOP)
	elif fact == "Final acceptance":
		accepted = final_acceptance.current(case)
		if accepted is not None:
			records.update(accepted, state="Superseded", record_version=cint(accepted.record_version) + 1)
		final_acceptance.offer(case, actor)
	else:
		if certificate:
			old = frappe.get_doc(CERTIFICATE, certificate)
			records.update(old, state="Superseded", record_version=cint(old.record_version) + 1)
		work.assign(case, "IssueCompletionCertificate", "Issue the completion certificate.", "completion certificate", 1, work.holders(work.HOP), role=work.HOP)
	events.record(case, "Contract reopened", actor, "The contract was reopened; the original close-out stays as history and no funding or native record was restored.", correction=row.name)
