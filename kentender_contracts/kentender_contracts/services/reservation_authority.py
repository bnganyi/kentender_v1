# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Which reservations a contract may draw on: Contract Management's answer to Budget (BUD-CHG-001 v1.13 proposal; follow-up FU-CM-59).

Budget converts a reservation into a commitment only when the owner of the contract's funding lineage says the contract's own award names that reservation
(`kentender_core.services.contract_reservation_authority`). Contract Management is that owner: the agreement's terms carry the Award package's **funding lineage** (source S9), which was hashed against
what Award recorded when the material was gathered (`source_package.py`) and is frozen with each signed agreement version. A reservation is awarded to the contract when an effective agreement version's
funding allocations name it.

* a Contract Management case with no allocation on that reservation: **False**. Sharing a supplier, or a Tender reference, is not enough.
* a contract registered independently of a Tender (`funding: {"external": true}`, "Not linked to KenTender Budget"): it names no reservation, so **False** for every one. It never draws on Budget.
* a name that is not a Contract Management case: **None** (this owner does not know it), which Budget refuses as well."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_contracts.services import records

CASE = "Contract Case"
AGREEMENT = "Contract Agreement Version"


def awarded_reservations(case: str) -> set[str]:
	"""The reservations the contract's effective agreement versions name in their funding lineage."""
	found: set[str] = set()
	for terms_json in frappe.get_all(AGREEMENT, filters={"contract_case": case, "state": "Effective"}, pluck="terms_json"):
		funding = (records.loads(terms_json) or {}).get("funding") or {}
		for allocation in funding.get("allocations") or []:
			reservation = str(allocation.get("reservation") or "").strip()
			if reservation:
				found.add(reservation)
	return found


def named_reservations(case: str) -> set[str]:
	"""The reservations the award package of the contract's agreement names, at any stage before it is superseded: a draft, an agreement out for signature or an effective one. A contract is about to
	be signed long before it may draw on them; this is what its award package says, which is enough to ask Budget to revalidate them and nothing more."""
	found: set[str] = set()
	for terms_json in frappe.get_all(AGREEMENT, filters={"contract_case": case, "state": ["in", ["Draft", "Awaiting signatures", "Effective"]]}, pluck="terms_json"):
		for allocation in ((records.loads(terms_json) or {}).get("funding") or {}).get("allocations") or []:
			reservation = str(allocation.get("reservation") or "").strip()
			if reservation:
				found.add(reservation)
	return found


class Authority:
	def authorises(self, *, contract: str, reservation: str) -> bool | None:
		if not contract or not frappe.db.exists(CASE, contract):
			return None
		return str(reservation or "").strip() in awarded_reservations(contract)

	def names(self, *, contract: str, reservation: str) -> bool | None:
		"""May Budget revalidate this reservation for this contract? The award package names it (FU-CM-81); whether the agreement is effective is not asked, because revalidating draws nothing."""
		if not contract or not frappe.db.exists(CASE, contract):
			return None
		return str(reservation or "").strip() in named_reservations(contract)


def service() -> Any:
	return Authority()
