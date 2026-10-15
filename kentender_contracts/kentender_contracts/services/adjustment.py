# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contractual delay adjustment (CM-CHG-001 v0.8 sections 5.7, 5.11 "Damages and overdue interest", 5.19, 7; rule CM-R-12 and legal question LQ-04; plan Phase 8; boards D36, D36-A, D36-S, D36-H, D36-E).

The system **proposes** the exact calculation from the operative rule and the recorded facts; nobody types the figure. The inputs are shown with it: the operative due date (an effective extension moves it; a request
that is not signed does not), the day the last ordered unit was accepted, the count basis, the eligible principal, the rate, the exclusions and the cap. The head of procurement records the causation, the clause the
rate comes from and the supplier's response; the Accounting Officer (an explicit test authority on the synthetic profile, never a universal statutory deduction rule) approves, declines or returns it. An approved
adjustment is applied to the next invoice as a native **deduction** row through a Finance-verified mapping; it is a noncash adjustment, never reported as cash, and it is never a ledger write of ours. Where the route
has no verified mapping the affected payment is held with a named owner, and nothing else is.

A new preparation (an extension became effective, a figure was challenged and re-read) supersedes the earlier one and keeps its inputs, so the old computation stays visible."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, flt, getdate

from kentender_contracts.native import adapter
from kentender_contracts.services import authority, change, clock, events, holds, position, preflight, records, segregation, work
from kentender_contracts.services.errors import Guards, fail, invalid

ADJ = "Contract Adjustment"
CASE = "Contract Case"
ACCEPTANCE = "Contract Acceptance"
MAPPING_FLAG = "kt_cm_deduction_account"
MARKER = "Contract adjustment"


def get(case: str, number: int):
	name = frappe.db.get_value(ADJ, {"contract_case": case, "adjustment_no": number}, "name")
	return frappe.get_doc(ADJ, name) if name else None


def live(case: str):
	"""The adjustment in play: prepared or approved and not yet applied or superseded."""
	name = frappe.db.get_value(ADJ, {"contract_case": case, "state": ["in", ["Submitted", "Returned", "Approved"]]}, "name", order_by="adjustment_no desc")
	return frappe.get_doc(ADJ, name) if name else None


def calculation(row) -> dict[str, Any]:
	return records.loads(row.calculation_json)


def subject_of(row) -> str:
	return f"adjustment {row.adjustment_no}"


def delivery_event(case: str):
	"""The day the last ordered unit was accepted: the actual delivery event the delay is counted to. None while any ordered unit is still to be accepted."""
	now = position.position(case)
	if not now["ordered"] or now["remaining"]:
		return None
	latest = frappe.get_all(ACCEPTANCE, filters={"contract_case": case, "state": "Effective"}, fields=["decision_at"], order_by="decision_at desc", limit=1)
	return getdate(latest[0].decision_at) if latest and latest[0].decision_at else None


def calculate(case: str, *, clause: str = "") -> dict[str, Any]:
	"""The proposed adjustment worked out from the operative terms and the recorded delivery. Raises a field problem while there is nothing to calculate."""
	doc = frappe.get_doc(CASE, case)
	profile = preflight.profile(doc)
	terms = change.operative_terms(case)
	delivery = terms["delivery"]
	event = delivery_event(case)
	if event is None:
		invalid({"delivery": "The delay is calculated when every ordered unit has been accepted."})
	due = getdate(delivery["due"])
	days = max(0, (event - due).days)
	principal = flt(terms["total"])
	rate = profile.parameter("delay_rate_per_day").value
	cap_percent = profile.parameter("delay_cap_percent").value
	daily = round(principal * rate, 2)
	gross = round(daily * days, 2)
	cap = round(principal * cap_percent / 100.0, 2)
	return {"due": str(due), "original_due": delivery.get("original_due") or str(due), "extensions": delivery.get("extensions", []), "event": str(event), "event_basis": "The day the last ordered unit was accepted",
		"days": days, "count_basis": "Calendar days after the due date, up to and including the day of the event", "exclusions": [], "principal": principal, "rate_per_day": rate, "rate_percent": round(rate * 100, 4),
		"daily": daily, "gross": gross, "cap_percent": cap_percent, "cap": cap, "amount": min(gross, cap), "currency": terms.get("currency", "KES"), "clause": cstr(clause).strip()}


# -- prepare and decide ------------------------------------------------------------------------------------------------------------------------
def on_delivery_complete(case: str, actor: str = "") -> bool:
	"""Every ordered unit has been accepted: when that was after the operative due date and the rule is verified, the head of procurement is asked to review the proposed adjustment (the calculation is the system's)."""
	doc = frappe.get_doc(CASE, case)
	if live(case) is not None or preflight.rules(doc, "PrepareContractAdjustment") or frappe.db.exists(ADJ, {"contract_case": case}):
		return False
	try:
		figures = calculate(case)
	except Exception:  # noqa: BLE001 - nothing to calculate yet
		return False
	if not figures["days"]:
		return False
	work.assign(case, "PrepareContractAdjustment", "Review the proposed adjustment.", "adjustment", 1, work.holders(work.HOP), role=work.HOP)
	events.record(case, "Delay noticed", actor, f"Delivery completed {figures['days']} day(s) after the due date; an adjustment of {figures['amount']:,.2f} is proposed for review.", days=figures["days"], amount=figures["amount"])
	return True


def on_due_changed(case: str, actor: str = "") -> None:
	"""An extension took effect: a proposal made on the earlier due date is read again, because the earlier computation no longer stands."""
	earlier = live(case)
	if earlier is not None and earlier.state == "Submitted":
		work.assign(case, "PrepareContractAdjustment", "The due date changed; review the proposed adjustment again.", "adjustment", 2, work.holders(work.HOP), role=work.HOP)


def prepare(case: str, *, causation: str, clause: str, supplier_response: str = "", recommendation: str = "", expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`PrepareContractAdjustment`: record the causation, the clause and the supplier's response against the calculation, and hold the proposal for the Accounting Officer's decision."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		invalid({"causation": "" if cstr(causation).strip() else "Record the cause of the delay.", "clause": "" if cstr(clause).strip() else "Name the clause the rate comes from."})
		preflight.rules(doc, "PrepareContractAdjustment").raise_if_any()
		holds.require(case, "vary_contract")
		figures = calculate(case, clause=clause)
		if not figures["days"]:
			invalid({"delivery": "Delivery was not late, so there is nothing to adjust."})
		earlier = live(case)
		if earlier is not None and earlier.state == "Approved":
			fail("CM_CHANGED", reason="An approved adjustment is waiting to be applied to an invoice.", adjustment=earlier.name)
		number = records.next_number(ADJ, {"contract_case": case}, "adjustment_no")
		prior = None
		if earlier is not None:
			prior = {"adjustment": earlier.name, "amount": flt(earlier.amount), "days": calculation(earlier)["days"], "due": calculation(earlier)["due"], "calculation": calculation(earlier)}
			records.update(earlier, state="Superseded", record_version=cint(earlier.record_version) + 1)
			work.finish(case, command="DecideContractAdjustment", subject=subject_of(earlier), state="Superseded", actor=actor)
		row = records.new(ADJ, contract_case=case, adjustment_no=number, kind="Delay", state="Submitted", calculation_json=records.dumps({**figures, "recommendation": cstr(recommendation).strip(), **({"prior": prior} if prior else {})}), causation=cstr(causation).strip(),
			supplier_response=cstr(supplier_response).strip(), decision_json=records.dumps({}), amount=figures["amount"], prepared_by=actor, prepared_at=clock.now(), supersedes=prior["adjustment"] if prior else None, record_version=1)
		for stale in ("adjustment",):
			work.finish(case, command="PrepareContractAdjustment", subject=stale, actor=actor)
		work.assign(case, "DecideContractAdjustment", "Decide the proposed delay adjustment.", subject_of(row), 1, work.holders("Accounting Officer"), role="Accounting Officer")
		events.record(case, "Adjustment prepared", actor, f"A delay adjustment of {figures['amount']:,.2f} was proposed ({figures['days']} days).", adjustment=row.name, days=figures["days"], amount=figures["amount"])
		records.bump(doc)
		return records.summary(doc, adjustment=row.name, adjustment_no=number, amount=figures["amount"], days=figures["days"])

	return records.command("PrepareContractAdjustment", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "causation": causation, "clause": clause, "response": supplier_response, "recommendation": recommendation},
		body=body, authorise=authorise)


def decide(case: str, *, adjustment: str, decision: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`DecideContractAdjustment`: approve, decline or return the proposal with a reason. The figure is the proposal's: the Accounting Officer cannot edit it, and never the person who prepared it."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Accounting Officer")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = frappe.get_doc(ADJ, adjustment)
		if row.contract_case != case:
			raise frappe.DoesNotExistError("Not found")
		if row.state != "Submitted":
			fail("CM_CHANGED", adjustment=adjustment, state=row.state)
		invalid({"decision": "" if decision in change.DECISIONS else "Choose approve, decline or return.", "reason": "" if cstr(reason).strip() else "Enter the reason for the decision."})
		segregation.preparer_not_decider(actor, [row.prepared_by], what="adjustment")
		if decision != "Return":
			preflight.rules(doc, "DecideContractAdjustment", {"automatic_deduction"}).raise_if_any()
		state = change.DECISIONS[decision]
		records.update(row, state=state, decision_json=records.dumps({"outcome": state, "reason": cstr(reason).strip(), "by": actor, "at": str(clock.now())}), decided_by=actor, decided_at=clock.now(), record_version=cint(row.record_version) + 1)
		work.finish(case, command="DecideContractAdjustment", subject=subject_of(row), actor=actor)
		if state == "Returned":
			work.assign(case, "PrepareContractAdjustment", "Correct the delay adjustment.", subject_of(row), 1, work.holders(work.HOP), role=work.HOP)
		events.record(case, f"Adjustment {state.lower()}", actor, f"The delay adjustment of {flt(row.amount):,.2f} was {state.lower()}.", adjustment=row.name, reason=cstr(reason).strip())
		records.bump(doc)
		return records.summary(doc, adjustment=row.name, state=state)

	return records.command("DecideContractAdjustment", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "adjustment": adjustment, "decision": decision, "reason": reason},
		body=body, authorise=authorise)


# -- applying an approved adjustment to an invoice -----------------------------------------------------------------------------------------
def pending_application(case: str) -> list[Any]:
	return [frappe.get_doc(ADJ, n) for n in frappe.get_all(ADJ, filters={"contract_case": case, "state": "Approved"}, pluck="name", order_by="adjustment_no asc")]


def applied_to(invoice: str) -> float:
	"""The noncash adjustment applied to one invoice."""
	return sum(flt(a) for a in frappe.get_all(ADJ, filters={"invoice": invoice, "state": "Applied"}, pluck="amount"))


def mapping_problems() -> list[str]:
	"""Why the native deduction mapping cannot be used (empty when it is verified): the account Finance names for contractual deductions must exist, be a ledger account and be enabled."""
	account = cstr(frappe.conf.get(MAPPING_FLAG)).strip()
	if not account:
		return ["Finance has not named the account for contractual deductions."]
	found = frappe.db.get_value("Account", account, ["is_group", "disabled", "root_type"], as_dict=True)
	if not found:
		return [f"The deduction account {account} does not exist."]
	if found.is_group or found.disabled:
		return [f"The deduction account {account} cannot be posted to."]
	return []


@holds.provider("adjustment")
def _unmapped_deduction(case: str) -> list[holds.Hold]:
	"""An approved adjustment has no route into the native invoice until Finance verifies the mapping: payment waits, nothing else does (section 5.19)."""
	if not pending_application(case) or not mapping_problems():
		return []
	owner = next(iter(work.holders("Finance preparation")), "Finance")
	return [holds.Hold(key="adjustment mapping", kind="Correction", reason="The native deduction mapping is unverified.", blocks=frozenset({"pay"}), owner=owner,
		clearing="Finance names and verifies the account for contractual deductions", scope=())]


def apply_to_native(case: str, invoice: str, native_invoice: str) -> list[str]:
	"""Add each approved adjustment to the native draft invoice as a Deduct row through the verified mapping, once. Returns the adjustments applied."""
	if mapping_problems():
		return []
	account = cstr(frappe.conf.get(MAPPING_FLAG)).strip()
	applied = []
	for row in pending_application(case):
		pi = frappe.get_doc("Purchase Invoice", native_invoice)
		marker = f"{MARKER} {row.name}"
		if pi.docstatus != 0:
			break
		if not any(cstr(t.description) == marker for t in pi.taxes):
			pi.append("taxes", {"category": "Total", "add_deduct_tax": "Deduct", "charge_type": "Actual", "account_head": account, "description": marker, "tax_amount": flt(row.amount), "cost_center": pi.cost_center})
			pi.save(ignore_permissions=True)
			adapter.reduce_certified(native_invoice, flt(row.amount))
		records.update(row, state="Applied", invoice=invoice, record_version=cint(row.record_version) + 1)
		events.record(case, "Adjustment applied", "", f"The delay adjustment of {flt(row.amount):,.2f} was applied to the invoice as a native deduction.", adjustment=row.name, invoice=invoice, native=native_invoice)
		applied.append(row.name)
	return applied
