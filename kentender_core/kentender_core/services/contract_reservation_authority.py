# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Which reservations a contract may draw on (BUD-CHG-001 v1.13 proposal; follow-up FU-CM-59).

Budget owns the money and refuses by default. When the contract service asks it to convert a reservation, Budget cannot work out from the request alone that the reservation belongs to the
funding source the contract was awarded on: sharing a supplier, or a Tender reference, proves nothing. So Budget asks the owner of the contract's funding lineage through this seam, and converts
only on a clear yes. The owner registers a provider on `kt_contract_reservation_authority`, a callable returning an object (or None to decline, for example where the owner is not installed):

    authorises(*, contract, reservation) -> True | False | None

`True`: the contract's award names this reservation. `False`: the owner knows the contract and this reservation is not one of its own. `None`: this owner does not know the contract. With no
provider, or no provider that knows the contract, `authorises` answers None and Budget refuses: no answer is never a yes. Several providers are asked in turn and the first answer that is not
None wins.

Seeds and tests may set `frappe.flags.kt_contract_reservation_authorities` to a list of providers; `installed()` and `permit_all()` do it with a clean-up. Nothing else in production code
sets it (`test_budget_contract_reservation_authority` fails if it does)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable, Iterator

import frappe

HOOK = "kt_contract_reservation_authority"
FLAG = "kt_contract_reservation_authorities"


def providers() -> list[Any]:
	override = frappe.flags.get(FLAG)
	if override is not None:
		return list(override)
	found = []
	for path in frappe.get_hooks(HOOK) or []:
		try:
			provider = frappe.get_attr(path)()
		except Exception:
			frappe.log_error(title=f"Contract reservation authority failed to load: {path}")
			continue
		if provider is not None:
			found.append(provider)
	return found


def authorises(contract: str, reservation: str) -> bool | None:
	"""Does the owner of `contract`'s funding lineage say the contract may draw on `reservation`? None when no owner knows the contract."""
	for provider in providers():
		answer = provider.authorises(contract=contract, reservation=reservation)
		if answer is not None:
			return bool(answer)
	return None


class Static:
	"""A fixed answer for seeds and tests: each named contract may draw on exactly the reservations listed; any other contract is unknown."""

	def __init__(self, allowed: dict[str, Iterable[str]]):
		self.allowed = {contract: set(reservations) for contract, reservations in allowed.items()}

	def authorises(self, *, contract: str, reservation: str) -> bool | None:
		if contract not in self.allowed:
			return None
		return reservation in self.allowed[contract]


class PermitAll:
	"""For tests whose subject is not the lineage: every contract may draw on every reservation."""

	def authorises(self, *, contract: str, reservation: str) -> bool | None:
		return True


@contextmanager
def installed(*authorities: Any) -> Iterator[None]:
	previous = frappe.flags.get(FLAG)
	frappe.flags[FLAG] = list(authorities)
	try:
		yield
	finally:
		frappe.flags[FLAG] = previous


def awarded(contract: str, *reservations: str):
	"""For a seed that stands in for Contract Management: within the block, `contract` is awarded exactly these reservations and no other contract is known."""
	return installed(Static({contract: reservations}))


def permit_all(testcase) -> None:
	"""Install `PermitAll` for one test case and put the previous setting back afterwards."""
	previous = frappe.flags.get(FLAG)
	frappe.flags[FLAG] = [PermitAll()]
	testcase.addCleanup(lambda: frappe.flags.update({FLAG: previous}))
