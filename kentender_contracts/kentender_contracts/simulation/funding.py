# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract Management's development funding owner (CM-CHG-001 v0.8 plan D5, D17): a stand-in for Budget on the `kt_contract_funding_provider` seam.

It exists so the ordinary thread can convert funding at effectiveness before the real Budget provider is wired in Phase 5 (proof level L1, never package acceptance). It is idempotent on the
operation identity, holds what it converted in `Contract Simulated Funding`, and answers only on a simulation site (`services/simulation.py`). The Contract Test Environment Controls single can
make it fail so the funding-failure recovery is exercised: `funding_outcome` is read from `frappe.flags.kt_cm_funding_fault` (a test sets and clears it)."""

from __future__ import annotations

import frappe

from kentender_contracts.services import clock, records, simulation
from kentender_core.services import contract_funding_contract as seam

LEDGER = "Contract Simulated Funding"


class Provider:
	def lookup(self, *, identity: str):
		row = frappe.db.get_value(LEDGER, {"identity": identity, "outcome": "Converted"}, ["reference", "amount"], as_dict=True)
		return {"reference": row.reference, "amount": row.amount} if row else None

	def convert(self, *, identity: str, contract: str, allocations: list, amount: float):
		held = self.lookup(identity=identity)
		if held:
			return held
		fault = frappe.flags.get("kt_cm_funding_fault")
		if fault == "refuse":
			raise seam.Refused("The reservation behind this contract is no longer available.")
		if fault == "fail":
			raise RuntimeError("The funding owner did not answer.")
		reference = f"SIMCOM-{frappe.generate_hash(length=8).upper()}"
		records.new(LEDGER, identity=identity, contract=contract, amount=amount, reference=reference, outcome="Converted", received_at=clock.now())
		return {"reference": reference, "amount": amount}


	def revalidate(self, *, identity: str, contract: str, allocations: list):
		"""The stand-in's answer when Contract Management asks the funding owner to revalidate the reservations an award names: every reservation can be drawn on, unless a test sets the fault `stale` (a
		reservation that stopped being available between the award and the signing). It moves nothing."""
		stale = frappe.flags.get("kt_cm_funding_fault") == "stale"
		rows = [{"reservation": str(a.get("reservation") or ""), "status": "Needs Attention" if stale else "Active"} for a in allocations or []]
		return {"reservations": rows, "problems": [f"Reservation {r['reservation']} no longer has funding behind it: Budget has marked it as needing attention." for r in rows] if stale else []}

	def recall(self, *, identity: str):
		row = frappe.db.get_value(LEDGER, {"identity": identity, "outcome": ["in", ["Adjusted", "Closed"]]}, ["reference", "amount"], as_dict=True)
		return {"reference": row.reference, "amount": float(row.amount)} if row else None

	def position(self, contract: str) -> dict:
		"""What the stand-in holds for a contract: converted, adjusted to, and whether closed."""
		rows = frappe.get_all(LEDGER, filters={"contract": contract}, fields=["outcome", "amount", "received_at", "reference"], order_by="creation asc")
		total = 0.0
		for r in rows:
			if r.outcome == "Converted":
				total = float(r.amount)
			elif r.outcome == "Adjusted":
				total = float(r.amount)
		return {"amount": total, "closed": any(r.outcome == "Closed" for r in rows)}

	def adjust(self, *, identity: str, contract: str, allocations: list, event_id: str, event_type: str):
		"""Idempotent on the identity: the first call records the supported total, a repeat returns it."""
		held = frappe.db.get_value(LEDGER, {"identity": identity, "outcome": "Adjusted"}, ["reference", "amount"], as_dict=True)
		if held:
			return {"reference": held.reference, "amount": float(held.amount), "before": None, "after": float(held.amount)}
		fault = frappe.flags.get("kt_cm_funding_fault")
		if fault == "refuse":
			raise seam.Refused("The funding owner refused the adjustment.")
		if fault == "fail":
			raise RuntimeError("The funding owner did not answer.")
		now = self.position(contract)
		if now["closed"]:
			raise seam.Refused("A closed commitment can only be decreased.")
		after = sum(float(a["new_total"]) for a in allocations or [])
		if after > now["amount"] and frappe.flags.get("kt_cm_funding_cover") == "none":
			raise seam.Refused("The increase is not covered by the funding available.")
		reference = f"SIMADJ-{frappe.generate_hash(length=8).upper()}"
		records.new(LEDGER, identity=identity, contract=contract, amount=after, reference=reference, outcome="Adjusted", received_at=clock.now())
		return {"reference": reference, "amount": after, "before": now["amount"], "after": after}

	def close(self, *, identity: str, contract: str, final_amount: float, event_id: str, event_type: str, evidence: list):
		held = frappe.db.get_value(LEDGER, {"identity": identity, "outcome": "Closed"}, ["reference", "amount"], as_dict=True)
		if held:
			return {"reference": held.reference, "amount": float(held.amount)}
		fault = frappe.flags.get("kt_cm_funding_fault")
		if fault == "refuse":
			raise seam.Refused("The funding owner refused the closure.")
		if fault == "fail":
			raise RuntimeError("The funding owner did not answer.")
		now = self.position(contract)
		if abs(now["amount"] - float(final_amount)) > 0.005:
			raise seam.Refused(f"The final supported obligation {final_amount:,.2f} is not what the commitment holds ({now['amount']:,.2f}).")
		reference = f"SIMCLS-{frappe.generate_hash(length=8).upper()}"
		records.new(LEDGER, identity=identity, contract=contract, amount=final_amount, reference=reference, outcome="Closed", received_at=clock.now())
		return {"reference": reference, "amount": float(final_amount)}


def service():
	return Provider() if simulation.enabled() else None
