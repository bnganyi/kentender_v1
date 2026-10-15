# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Termination and its settlement (CM-CHG-001 v0.8 sections 5.7 "Termination", 5.11, 5.21, 7; rule CM-R-16; plan Phase 8; boards D20, D20-P, D20-T, D39-P, D39, D39-C, D39-H).

The head of procurement submits the grounds, the clause, the notice and cure evidence, the legal advice and a recommendation; the financial position is **generated** from the records (the value accepted, the cash
confirmed, what is supported but unpaid, the advance still outstanding, the claims in dispute), never typed. The Accounting Officer, who did not prepare it, approves, declines or returns it. The approved notice
is delivered and the head of procurement records the **actual** delivery with its evidence and the date the termination takes effect; only then does the contract become **Terminated** (no timer invents the
consequence). What had been accepted stays accepted and payable, new delivery stops, and the funding owner is asked, as a durable operation, to reduce the commitment to the supported obligation.

Terminated is neither Completed nor Settled. The head of procurement prepares the settlement from the generated reconciliation and classifies what survives; the Accounting Officer completes it only when every
remaining item is either settled or classified as a named surviving obligation. Completing it is its own dated fact: the lifecycle stays Terminated, and the commitment's closure is requested from the funding
owner and acknowledged separately (`funding_closure.py`)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, flt, getdate

from kentender_contracts.services import advance, authority, change, clock, events, funding_closure, intents, obligations, payment, position, preflight, records, segregation, work
from kentender_contracts.services.errors import Guards, fail, invalid
from kentender_core.services import contract_funding_contract as funding_seam

TERM = "Contract Termination"
CASE = "Contract Case"
INVOICE = "Contract Invoice"
FUNDING_EVENT = "ContractTerminationEffective"
CLOSURE_EVENT = "TerminationSettlementCompleted"
GROUNDS = ("Material non-delivery", "Repeated rejected delivery", "Breach of a fundamental term", "Insolvency of the supplier", "Other ground in the issued terms")
DECISIONS = {"Approve": "Approved", "Decline": "Declined", "Return": "Returned"}


def get(case: str, number: int):
	name = frappe.db.get_value(TERM, {"contract_case": case, "termination_no": number}, "name")
	return frappe.get_doc(TERM, name) if name else None


def live(case: str):
	"""The termination in progress or in force: not declined."""
	name = frappe.db.get_value(TERM, {"contract_case": case, "state": ["not in", ["Declined"]]}, "name", order_by="termination_no desc")
	return frappe.get_doc(TERM, name) if name else None


def subject_of(row) -> str:
	return f"termination {row.termination_no}"


def basis(row) -> dict[str, Any]:
	return records.loads(row.basis_json)


def financials(case: str) -> dict[str, Any]:
	"""The financial position, generated from the records: what was accepted, what cash is confirmed, what is supported but unpaid, the advance outstanding and the claims in dispute."""
	terms = change.operative_terms(case)
	rates = {l["line_id"]: flt(l["rate"]) for l in terms["lines"]}
	now = position.position(case)
	accepted_value = sum(row["accepted"] * rates[lid] for lid, row in now["lines"].items())
	invoices = frappe.get_all(INVOICE, filters={"contract_case": case, "state": ["!=", "Superseded"]}, fields=["name", "state", "claimed_amount"])
	cash = sum(payment.settled_amount(i.name) for i in invoices)
	certified = [payment.invoice_position(case, i.name) for i in invoices if i.state in ("Certified", "Partly paid", "Paid")]
	unpaid = sum(p["outstanding"] for p in certified)
	disputed = sum(flt(i.claimed_amount) for i in invoices if i.state == "Held")
	advance_now = advance.position(case)
	return {"currency": terms.get("currency", "KES"), "contract_value": flt(terms["total"]), "accepted_value": accepted_value, "cash_paid": cash, "supported_unpaid": unpaid, "advance_balance": advance_now["outstanding"],
		"disputed": disputed, "authorised_costs": 0.0, "units_accepted": now["accepted"], "units_ordered": now["ordered"]}


def supported_obligation(position_now: dict[str, Any]) -> float:
	"""What the contract still owes after termination: the accepted work and the costs authorised under the issued terms. It is not reduced to the certified invoices alone."""
	return round(flt(position_now["accepted_value"]) + flt(position_now["authorised_costs"]), 2)


# -- request, decide -----------------------------------------------------------------------------------------------------------------------
def request(case: str, *, grounds: str, clause: str, recommendation: str, evidence: list[dict[str, Any]], expected_version: int, idempotency_key: str, actor: str, correcting: int = 0,
		funding: list[dict[str, Any]] | None = None) -> dict[str, Any]:
	"""`RequestContractTermination`: the grounds, the clause, the notice and cure evidence, the legal advice and the recommendation, with the generated financial position."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		invalid({"grounds": "" if cstr(grounds).strip() else "Choose the grounds.", "clause": "" if cstr(clause).strip() else "Name the clause the termination relies on.",
			"recommendation": "" if cstr(recommendation).strip() else "Record the recommendation.", "evidence": "" if evidence and all(cstr(e.get("label")).strip() for e in evidence) else "Attach the notice, cure and legal advice evidence."})
		current = live(case)
		returned = get(case, correcting) if correcting else None
		if returned is not None and returned.state != "Returned":
			fail("CM_CHANGED", termination=returned.name, state=returned.state)
		if current is not None and (returned is None or current.name != returned.name):
			fail("CM_CHANGED", reason="A termination of this contract is already in progress.", termination=current.name)
		position_now = financials(case)
		split = _funding_split(case, supported_obligation(position_now), funding)
		parts = {"grounds": cstr(grounds).strip(), "clause": cstr(clause).strip(), "recommendation": cstr(recommendation).strip(), "evidence": evidence, "funding": split, "draft": 1}
		if returned is None:
			number = records.next_number(TERM, {"contract_case": case}, "termination_no")
			row = records.new(TERM, contract_case=case, termination_no=number, state="Requested", grounds=parts["grounds"], basis_json=records.dumps(parts), financial_json=records.dumps(position_now), decision_json=records.dumps({}),
				notice_json=records.dumps({}), settlement_json=records.dumps({}), requested_by=actor, requested_at=clock.now(), record_version=1)
		else:
			row = returned
			parts["draft"] = cint(basis(row).get("draft") or 1) + 1
			records.update(row, state="Requested", grounds=parts["grounds"], basis_json=records.dumps(parts), financial_json=records.dumps(position_now), record_version=cint(row.record_version) + 1)
			work.finish(case, command="RequestContractTermination", subject=subject_of(row), actor=actor)
		work.assign(case, "DecideContractTermination", "Decide the termination request.", subject_of(row), parts["draft"], work.holders("Accounting Officer"), role="Accounting Officer")
		events.record(case, "Termination requested", actor, f"Termination {row.termination_no} requested: {parts['grounds']}.", termination=row.name, clause=parts["clause"])
		records.bump(doc)
		return records.summary(doc, termination=row.name, termination_no=row.termination_no)

	return records.command("RequestContractTermination", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "grounds": grounds, "clause": clause, "recommendation": recommendation,
		"evidence": evidence, "correcting": correcting, "funding": funding or []}, body=body, authorise=authorise)


def _funding_split(case: str, supported: float, given: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
	"""How the supported obligation sits on the sources: the one reservation behind the contract by default, otherwise exactly as named. Never an arbitrary allocation."""
	allocations = change.operative_terms(case).get("funding", {}).get("allocations", [])
	if not given:
		if len(allocations) == 1:
			return [{"reservation": allocations[0]["reservation"], "new_total": supported}]
		invalid({"funding": "Name how each source carries the supported obligation."})
	clean = [{"reservation": cstr(g.get("reservation")), "new_total": round(flt(g.get("new_total")), 2)} for g in given]
	known = {a["reservation"] for a in allocations}
	problem = "" if clean and all(c["reservation"] in known for c in clean) else "Each source named must already fund this contract."
	if not problem and abs(sum(c["new_total"] for c in clean) - supported) > 0.005:
		problem = f"The sources must carry exactly the supported obligation of {supported:,.2f}."
	invalid({"funding": problem})
	return clean


def decide(case: str, *, termination: int, decision: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`DecideContractTermination` / `ReturnContractTermination`: the Accounting Officer approves, declines or returns the request, with a reason. Approval asks the head of procurement to deliver the notice."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Accounting Officer")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, termination)
		if row is None or row.state != "Requested":
			fail("CM_CHANGED", termination=termination, state=row.state if row else "")
		invalid({"decision": "" if decision in DECISIONS else "Choose approve, decline or return.", "reason": "" if cstr(reason).strip() else "Enter the reason for the decision."})
		segregation.preparer_not_decider(actor, [row.requested_by], what="termination request")
		if decision == "Approve":
			guards = preflight.rules(doc, "DecideContractTermination")
			guards.raise_if_any()
		state = DECISIONS[decision]
		draft = cint(basis(row).get("draft") or 1)
		records.update(row, state=state, decision_json=records.dumps({"outcome": state, "reason": cstr(reason).strip(), "by": actor, "at": str(clock.now())}), record_version=cint(row.record_version) + 1)
		work.finish(case, command="DecideContractTermination", subject=subject_of(row), actor=actor)
		if state == "Approved":
			work.assign(case, "RecordTerminationNotice", "Deliver the termination notice.", subject_of(row), draft, work.holders(work.HOP), role=work.HOP)
			work.assign(case, work.waiting_command("RecordTerminationNotice", "delivery"), "Waiting for the termination notice to be delivered.", subject_of(row), draft, [actor], role="Accounting Officer", state="Waiting")
		elif state == "Returned":
			work.assign(case, "RequestContractTermination", "Correct the termination request.", subject_of(row), draft, [row.requested_by], role=work.HOP)
		events.record(case, f"Termination {state.lower()}", actor, f"Termination {row.termination_no} {state.lower()}.", termination=row.name, reason=cstr(reason).strip())
		records.bump(doc)
		return records.summary(doc, termination=row.name, state=state)

	return records.command("DecideContractTermination", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "termination": termination, "decision": decision, "reason": reason},
		body=body, authorise=authorise)


# -- the notice and the effect ------------------------------------------------------------------------------------------------------------
def record_notice(case: str, *, termination: int, delivered_on: str, method: str, reference: str, effective_on: str, evidence: list[dict[str, Any]], expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordTerminationNotice`: the actual delivery of the approved notice, with its evidence and the date the termination takes effect. When that date has come the termination takes effect now; when it has not, the
	notice is recorded and the effect waits, scheduled, for that date."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, termination)
		if row is None or row.state != "Approved":
			fail("CM_CHANGED", termination=termination, state=row.state if row else "")
		problems = {"method": "" if cstr(method).strip() else "Enter how the notice was delivered.", "reference": "" if cstr(reference).strip() else "Enter the delivery reference.",
			"evidence": "" if evidence and all(cstr(e.get("label")).strip() for e in evidence) else "Attach the proof of delivery."}
		try:
			delivered, effective = getdate(delivered_on), getdate(effective_on)
		except Exception:  # noqa: BLE001
			delivered = effective = None
			problems["delivered_on"] = "Enter the delivery date and the date the termination takes effect."
		if delivered and effective and effective < delivered:
			problems["effective_on"] = "The termination cannot take effect before the notice was delivered."
		invalid(problems)
		preflight.rules(doc, "RecordTerminationNotice").raise_if_any()
		notice = {"delivered_on": str(delivered), "method": cstr(method).strip(), "reference": cstr(reference).strip(), "effective_on": str(effective), "evidence": evidence, "recorded_by": actor, "recorded_at": str(clock.now())}
		draft = cint(basis(row).get("draft") or 1)
		records.update(row, state="Notice delivered", notice_json=records.dumps(notice), record_version=cint(row.record_version) + 1)
		work.finish(case, command="RecordTerminationNotice", subject=subject_of(row), actor=actor)
		events.record(case, "Termination notice delivered", actor, f"The termination notice was delivered on {delivered.strftime('%-d %B %Y')} ({notice['method']}); it takes effect on {effective.strftime('%-d %B %Y')}.", termination=row.name, reference=notice["reference"])
		if effective > getdate(clock.now()):
			work.assign(case, "RecordTerminationEffect", "Record that the termination took effect.", subject_of(row), draft, work.holders(work.HOP), role=work.HOP, state="Scheduled")
			records.bump(doc)
			return records.summary(doc, termination=row.name, state="Notice delivered", effective=False)
		_make_effective(doc, row, actor)
		return records.summary(doc, termination=row.name, state="Effective", effective=True)

	recorded = records.command("RecordTerminationNotice", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "termination": termination, "delivered": delivered_on, "method": method,
		"reference": reference, "effective": effective_on, "evidence": evidence}, body=body, authorise=authorise)
	frappe.db.commit()
	if recorded.get("effective"):
		carry_out_effects(case, actor)
	return recorded


def record_effect(case: str, *, termination: int, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordTerminationEffect`: the date the delivered notice names has come; the termination takes effect."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, termination)
		if row is None or row.state != "Notice delivered":
			fail("CM_CHANGED", termination=termination, state=row.state if row else "")
		effective = getdate(records.loads(row.notice_json)["effective_on"])
		if effective > getdate(clock.now()):
			guards = Guards().add("CM_HOLD", hold="effective date", kind="Effective date", reason=f"The termination takes effect on {effective.strftime('%-d %B %Y')}.", holder="Head of procurement function",
				clears_with="The effective date arrives", consequence="RecordTerminationEffect")
			guards.raise_if_any()
		work.finish(case, command="RecordTerminationEffect", subject=subject_of(row), actor=actor)
		_make_effective(doc, row, actor)
		return records.summary(doc, termination=row.name, state="Effective", effective=True)

	recorded = records.command("RecordTerminationEffect", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "termination": termination}, body=body, authorise=authorise)
	frappe.db.commit()
	carry_out_effects(case, actor)
	return recorded


def _make_effective(doc, row, actor: str) -> None:
	"""The termination is in force (the same transaction as its record): the lifecycle is Terminated, what was accepted stays accepted, and the commitment's reduction to the supported obligation is a durable operation."""
	case = doc.name
	now = financials(case)
	supported = supported_obligation(now)
	parts = basis(row)
	records.update(row, state="Effective", effective_at=clock.now(), financial_json=records.dumps({**now, "supported_obligation": supported}), record_version=cint(row.record_version) + 1)
	records.bump(doc, lifecycle="Terminated")
	if supported < flt(now["contract_value"]) - 0.005:
		intents.record(case, subject_of(row), row.termination_no, "Funding adjustment", "effective", recovery_owner="Technical operator; Budget owner")
	obligations.on_termination_effective(case, row.termination_no, clock.now())
	events.record(case, "Termination effective", actor, f"Termination {row.termination_no} took effect; accepted work of {now['accepted_value']:,.2f} stays accepted.", termination=row.name, supported=supported, clause=parts["clause"])
	work.assign(case, "PrepareTerminationSettlement", "Review the reconciled settlement.", subject_of(row), row.termination_no, work.holders(work.HOP), role=work.HOP)


def carry_out_effects(case: str, actor: str = "") -> dict[str, Any]:
	"""Carry the commitment's reduction through the funding owner (read first by identity) and any pending closure; each in its own transaction."""
	out = []
	row = live(case)
	if row is not None and row.state in ("Effective", "Settlement prepared", "Settled"):
		name = frappe.db.get_value(intents.INTENT, {"contract_case": case, "operation_kind": "Funding adjustment", "subject": subject_of(row)}, "name")
		if name and frappe.db.get_value(intents.INTENT, name, "state") not in intents.SETTLED:
			split = basis(row)["funding"]

			def executor(identity):
				try:
					done = funding_seam.adjust(identity, contract=case, allocations=split, event_id=f"{case}|{subject_of(row)}", event_type=FUNDING_EVENT)
				except funding_seam.Refused as exc:
					raise intents.OwnerRefused(str(exc)) from exc
				return done["reference"], "Procurement Commitment"

			result = intents.execute(name, executor, lambda identity: (funding_seam.recall(identity) or {}).get("reference"), native_doctype="Procurement Commitment")
			out.append({"kind": "Funding adjustment", **result})
			with records.atomic():
				if result["state"] in intents.SETTLED:
					work.finish(case, command="RestoreContractOperation", subject=subject_of(row), actor=actor)
					events.record(case, "Funding adjustment linked", actor, f"The commitment was reduced to the supported obligation ({result['reference']}).", intent=name)
				else:
					work.incident(case, "RestoreContractOperation", "Restore contract operation", subject_of(row), row.termination_no)
					events.record(case, "Operation pending", actor, f"The commitment's reduction did not complete ({result['state'].lower()}).", intent=name)
			frappe.db.commit()
	out.extend(funding_closure.carry_out(case, actor))
	return {"ok": True, "operations": out}


# -- the settlement -------------------------------------------------------------------------------------------------------------------------
def reconciliation(case: str, row) -> dict[str, Any]:
	"""The generated reconciliation of an effective termination: every fact Finance and procurement reconcile, and the items that still stand between the termination and its settlement."""
	now = financials(case)
	supported = supported_obligation(now)
	remaining = []
	if now["supported_unpaid"] > 0.005:
		remaining.append({"kind": "Liability", "ref": "supported unpaid", "what": f"{now['supported_unpaid']:,.2f} is supported and not yet paid.", "holder": "Finance approval"})
	if now["advance_balance"] > 0.005:
		remaining.append({"kind": "Advance recovery", "ref": "advance", "what": f"{now['advance_balance']:,.2f} of the advance is not recovered.", "holder": "Finance"})
	if now["disputed"] > 0.005:
		remaining.append({"kind": "Dispute", "ref": "claims in dispute", "what": f"{now['disputed']:,.2f} is claimed and in dispute.", "holder": "Head of procurement function"})
	adjust = frappe.db.get_value(intents.INTENT, {"contract_case": case, "operation_kind": "Funding adjustment", "subject": subject_of(row)}, "state")
	budget = "Not needed" if adjust is None else "Acknowledged" if adjust in intents.SETTLED else "Pending"
	if budget == "Pending":
		remaining.append({"kind": "Budget decrease", "ref": "commitment", "what": "The commitment's reduction is not acknowledged by the funding owner.", "holder": "Budget owner"})
	return {**now, "supported_obligation": supported, "unperformed_balance": max(0.0, now["contract_value"] - supported), "budget_decrease": budget, "remaining": remaining}


def unclassified(recon: dict[str, Any], classified: list[dict[str, Any]]) -> list[dict[str, Any]]:
	named = {(c["kind"], c["ref"]) for c in classified}
	return [r for r in recon["remaining"] if (r["kind"], r["ref"]) not in named]


def prepare_settlement(case: str, *, termination: int, finance_reference: str, classified: list[dict[str, Any]] | None = None, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`PrepareTerminationSettlement`: the head of procurement reviews the generated reconciliation, names Finance's reconciliation and classifies what survives, then submits it for completion."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Terminated")
		row = get(case, termination)
		if row is None or row.state not in ("Effective", "Settlement prepared"):
			fail("CM_CHANGED", termination=termination, state=row.state if row else "")
		invalid({"finance_reference": "" if cstr(finance_reference).strip() else "Enter Finance's reconciliation reference."})
		survivors = [{"kind": cstr(c.get("kind")), "ref": cstr(c.get("ref")), "basis": cstr(c.get("basis")).strip()} for c in classified or []]
		invalid({"classified": "" if all(s["basis"] for s in survivors) else "Name the clause that lets each surviving item survive."})
		recon = reconciliation(case, row)
		records.update(row, state="Settlement prepared", settlement_json=records.dumps({"reconciliation": recon, "finance_reference": cstr(finance_reference).strip(), "classified": survivors, "prepared_by": actor, "prepared_at": str(clock.now())}),
			record_version=cint(row.record_version) + 1)
		work.finish(case, command="PrepareTerminationSettlement", subject=subject_of(row), actor=actor)
		work.assign(case, "CompleteTerminationSettlement", "Review the settlement record.", subject_of(row), row.termination_no, work.holders("Accounting Officer"), role="Accounting Officer")
		events.record(case, "Termination settlement prepared", actor, f"The settlement of termination {row.termination_no} was prepared from reconciliation {cstr(finance_reference).strip()}.", termination=row.name)
		records.bump(doc)
		return records.summary(doc, termination=row.name, remaining=len(unclassified(recon, survivors)))

	return records.command("PrepareTerminationSettlement", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "termination": termination, "reference": finance_reference,
		"classified": classified or []}, body=body, authorise=authorise)


def return_settlement(case: str, *, termination: int, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ReturnContractTermination` for a prepared settlement: the Accounting Officer sends it back to the head of procurement with the reason; the termination stays in force and the settlement is prepared again."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Terminated")
		row = get(case, termination)
		if row is None or row.state != "Settlement prepared":
			fail("CM_CHANGED", termination=termination, state=row.state if row else "")
		invalid({"reason": "" if cstr(reason).strip() else "Enter why the settlement is returned."})
		prepared = records.loads(row.settlement_json)
		records.update(row, state="Effective", settlement_json=records.dumps({**prepared, "returned": {"by": actor, "reason": cstr(reason).strip(), "at": str(clock.now())}}), record_version=cint(row.record_version) + 1)
		work.finish(case, command="CompleteTerminationSettlement", subject=subject_of(row), actor=actor)
		work.assign(case, "PrepareTerminationSettlement", "Correct the settlement.", subject_of(row), row.termination_no, work.holders(work.HOP), role=work.HOP)
		events.record(case, "Termination settlement returned", actor, f"The settlement of termination {row.termination_no} was returned: {cstr(reason).strip()}", termination=row.name)
		records.bump(doc)
		return records.summary(doc, termination=row.name, state="Effective")

	return records.command("ReturnContractTermination", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "termination": termination, "reason": reason, "stage": "settlement"},
		body=body, authorise=lambda: authority.require(actor, "Accounting Officer"))


def complete_settlement(case: str, *, termination: int, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`CompleteTerminationSettlement`: the Accounting Officer completes the settlement only if every remaining item is settled or classified as a named surviving obligation. It records its own date and keeps the
	lifecycle Terminated; the commitment's closure is requested from the funding owner and acknowledged separately."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Accounting Officer")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Terminated")
		row = get(case, termination)
		if row is None or row.state != "Settlement prepared":
			fail("CM_CHANGED", termination=termination, state=row.state if row else "")
		invalid({"reason": "" if cstr(reason).strip() else "Enter the reason for completing the settlement."})
		segregation.preparer_not_decider(actor, [records.loads(row.settlement_json).get("prepared_by")], what="settlement")
		prepared = records.loads(row.settlement_json)
		recon = reconciliation(case, row)  # read again: the settlement is judged on the facts now, not on the day it was prepared
		open_items = unclassified(recon, prepared["classified"])
		if open_items:
			fail("CM_CLOSURE", remaining=[{"kind": i["kind"], "what": i["what"], "holder": i["holder"]} for i in open_items])
		records.update(row, state="Settled", settlement_json=records.dumps({**prepared, "reconciliation": recon, "completed_by": actor, "completed_at": str(clock.now()), "reason": cstr(reason).strip()}),
			record_version=cint(row.record_version) + 1)
		work.finish(case, command="CompleteTerminationSettlement", subject=subject_of(row), actor=actor)
		funding_closure.request(case, subject=f"closure {subject_of(row)}", version=row.termination_no, final_amount=recon["supported_obligation"], event_type=CLOSURE_EVENT, evidence=[prepared["finance_reference"]], actor=actor)
		events.record(case, "Termination settlement completed", actor, f"The settlement of termination {row.termination_no} was completed; the contract stays Terminated.", termination=row.name)
		records.bump(doc)
		return records.summary(doc, termination=row.name, state="Settled")

	recorded = records.command("CompleteTerminationSettlement", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "termination": termination, "reason": reason}, body=body, authorise=authorise)
	frappe.db.commit()
	funding_closure.carry_out(case, actor)
	return recorded
