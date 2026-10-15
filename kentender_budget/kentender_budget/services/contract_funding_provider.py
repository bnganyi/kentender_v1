# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget's side of the contract funding seam (CM-CHG-001 v0.8 section 5.14, plan D5; `kentender_core.services.contract_funding_contract`; tracker CM8-507).

When a formed agreement takes effect, Contract Management asks the funding owner, through the core seam, to convert the reservation lineage the Award package carried into commitments. This is that
owner's answer. It is the **one gateway** through which the Contract Management principal is minted (the repository test names it), it converts each allocation with `convert_reservation` under a key
derived from Contract Management's operation identity, and so a retry converts nothing twice (`lookup` reads what an identity already did). It never decides a split: the allocations are the awarded price
mapped to reservations by their owner, and they must add up to the contract amount or the whole request is refused with nothing converted.

A Budget refusal (a reservation that is not open, an amount above what remains, a Closed Budget) is a definitive refusal; anything else propagates, and the caller treats the outcome as unknown and reads
the owner first on its retry."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe

from kentender_budget.services import budget_commitment_contracts as commitments
from kentender_budget.services.budget_idempotency import JOURNAL
from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, service_caller
from kentender_core.services import contract_funding_contract as seam

CONTRACT_EVENT = "ContractEffective"


def _key(identity: str, reservation: str) -> str:
	return f"{identity}#{reservation}"


class Provider:
	def lookup(self, *, identity: str) -> dict[str, Any] | None:
		rows = frappe.get_all(JOURNAL, filters={"idempotency_key": ["like", f"{identity}#%"], "command": "convert_reservation"}, fields=["result"])
		codes, total = [], Decimal("0")
		for row in rows:
			result = frappe.parse_json(row.result) if row.result else {}
			commitment = (result.get("commitment") or {})
			if commitment.get("commitment_code"):
				codes.append(commitment["commitment_code"])
				total += Decimal(str(commitment.get("current_amount") or 0))
		return {"reference": ", ".join(codes), "amount": float(total)} if codes else None

	def convert(self, *, identity: str, contract: str, allocations: list[dict[str, Any]], amount: float) -> dict[str, Any]:
		parts = [(str(a.get("reservation") or "").strip(), Decimal(str(a.get("amount")))) for a in allocations or []]
		if not parts or any(not reservation or part <= 0 for reservation, part in parts):
			raise seam.Refused("The award names no usable funding allocation.")
		if sum((part for _r, part in parts), Decimal("0")) != Decimal(str(amount)):
			raise seam.Refused("The funding allocations do not add up to the contract amount.")
		caller = service_caller(PRINCIPAL_CONTRACT, reference=contract)
		codes = []
		for reservation, part in parts:
			try:
				done = commitments.convert_reservation(reservation, contract, part, _key(identity, reservation), contract_event_id=identity, contract_event_type=CONTRACT_EVENT, caller=caller)
			except (frappe.ValidationError, frappe.PermissionError, frappe.DoesNotExistError) as exc:
				raise seam.Refused(frappe.safe_decode(str(exc))) from exc
			codes.append(done["commitment"]["commitment_code"])
		return {"reference": ", ".join(codes), "amount": float(sum((part for _r, part in parts), Decimal("0")))}


def service() -> Provider:
	return Provider()
