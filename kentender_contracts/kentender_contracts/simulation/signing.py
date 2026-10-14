# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract Management's signing simulation provider (plan D8, FU-CM-49), on the `kt_trust_signing_services` hook.

It stands in for an external trust service so a Contract Management site can sign in tests and demonstrations. It is **not** an
electronic signature and issues no certificate. It answers only when the site is a simulation environment (`services/simulation.py`) and only for the consumer `contracts` (`serves`), so it can never answer another module's request.

It behaves as a provider must: **idempotent on the correlation identity** (the same identity returns the same proof, never a
second one) and able to **reconcile** (what does it hold under an identity). Faults are switched on the Contract Test Environment
Controls single: *Unavailable* is a provider that never received the request (nothing held); *Indeterminate* is a lost reply, where the
provider did sign and held the proof but the caller saw no answer (so only `reconcile` finds it); *Rejected* is a refusal it holds."""

from __future__ import annotations

import frappe

from kentender_contracts.services import clock, records, simulation
from kentender_core.services.command_write_guard import command_write

LEDGER = "Contract Simulated Signature"
CONTROLS = "Contract Test Environment Controls"
METHOD = "Contract Management simulation"
VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE = "Accepted/Verified", "Rejected", "Unavailable", "Indeterminate"


def enabled() -> bool:
	return simulation.enabled()


def fault() -> str:
	return frappe.db.get_single_value(CONTROLS, "signing_outcome") or ""


class ContractSigningSimulation:
	serves = ("contracts",)

	def attest(self, *, member: str, target_id: str, target_digest: str, minutes_version: str, action: str, correlation_id: str) -> dict:
		held = self._held(correlation_id)
		if held:
			if (held.signer, held.target_digest) != (member, target_digest):
				return {"outcome": REJECTED, "method": METHOD, "proof_reference": "", "detail": "This correlation identity was already used for a different signer or document."}
			return self._answer(held)
		mode = fault()
		if mode == UNAVAILABLE:
			return {"outcome": UNAVAILABLE, "method": METHOD, "proof_reference": ""}
		outcome = REJECTED if mode == REJECTED else VERIFIED
		with command_write("Contract Management"):
			held = records.new(LEDGER, correlation_id=correlation_id, signer=member, target_digest=target_digest, outcome=outcome,
				proof_reference=f"CMSIM-{frappe.generate_hash(length=10).upper()}" if outcome == VERIFIED else "", received_at=clock.now())
		frappe.db.commit()
		if mode == INDETERMINATE:
			return {"outcome": INDETERMINATE, "method": METHOD, "proof_reference": ""}  # signed and held, reply lost
		return self._answer(held)

	def reconcile(self, correlation_id: str) -> dict:
		held = self._held(correlation_id)
		return {"known": True, **self._answer(held)} if held else {"known": False}

	@staticmethod
	def _held(correlation_id: str):
		name = frappe.db.get_value(LEDGER, {"correlation_id": correlation_id}, "name")
		return frappe.get_doc(LEDGER, name) if name else None

	@staticmethod
	def _answer(held) -> dict:
		return {"outcome": held.outcome, "method": METHOD, "proof_reference": held.proof_reference or "", "signed_at": str(held.received_at)}


def service():
	return ContractSigningSimulation() if enabled() else None
