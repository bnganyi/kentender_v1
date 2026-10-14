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


def service():
	return Provider() if simulation.enabled() else None
