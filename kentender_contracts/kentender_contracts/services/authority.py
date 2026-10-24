# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who may act (CM-CHG-001 v0.8 §6, §6.2, §6.2.1; plan D11; tracker CM8-310).

Authority is an active `User Responsibility Assignment` resolved by AUTH at the moment of the action, never remembered. For the capacities that act
on one contract (an inspector, a technical certifier, an entity signatory, an AO's representative for final acceptance) it also needs a **contract-specific
subject binding**: an effective appointment or written mandate that Contract Management owns. The binding only **supplements** the registered responsibility:
an assignment alone grants no contract access, and an appointment alone grants nothing, because "appointments supplement the required registered
responsibility, enabled identity and coarse framework permission; they are not a new AUTH scope type or a substitute role" (§6.2).

The appointment and mandate records belong to the packages that create them; each registers its provider here with `binding(capacity)`. Until it does,
the answer is **no**: nothing is invented from a task or a fixture. A refusal says which half is missing and who provisions it, so a screen can show the
missing assignment and its administrator rather than a bare denial (§6.2.1 last paragraph)."""

from __future__ import annotations

from typing import Any, Callable

from kentender_contracts.services import people
from kentender_contracts.services.errors import fail

#: capacity -> the registered responsibility it additionally requires (§6.2, §6.2.1)
CAPACITY_RESPONSIBILITY: dict[str, str] = {
	"inspector": "Contract inspection",
	"technical certifier": "Technical certification",
	"entity signatory": "Entity contract signing",
	"final acceptance representative": "Contract inspection",
}
PROVISIONED_BY = "System setup, by a System Manager"

Provider = Callable[[str, str, Any], "dict[str, Any] | None"]  # (case, user, at) -> evidence of the effective appointment or mandate, or None
BINDINGS: dict[str, Provider] = {}
#: A reader needs only that the appointment exists ("even when declaration pending", §6.2), so a package may register a wider provider for reading.
#: Where none is registered the action provider also answers for reading: an effective appointment is certainly readable.
READ_BINDINGS: dict[str, Provider] = {}


def binding(capacity: str, *, read: bool = False) -> Callable[[Provider], Provider]:
	if capacity not in CAPACITY_RESPONSIBILITY:
		raise ValueError(f"{capacity!r} is not a capacity bound to an appointment or mandate.")

	def register(fn: Provider) -> Provider:
		(READ_BINDINGS if read else BINDINGS)[capacity] = fn
		return fn

	return register


def _default(capacity: str, *, read: bool = False):
	"""The binding Contract Management itself owns (`bindings.py`), used when no other provider is registered for the capacity."""
	from kentender_contracts.services import bindings

	return (bindings.READ if read else bindings.ACT).get(capacity)


def readable_binding(case: str, user: str, capacity: str, *, at=None) -> dict[str, Any] | None:
	"""Evidence that this person has an appointment or mandate on this contract that lets them read it, or None. Does not check the responsibility."""
	provider = READ_BINDINGS.get(capacity) or BINDINGS.get(capacity) or _default(capacity, read=True)
	return provider(case, user, at) if provider else None


def require(user: str, business_role: str, *, organisation_unit: str = "", at=None) -> None:
	"""The user holds this registered responsibility now (at this unit for an Organisation Unit one). A technical account never does."""
	if not people.holds(user, business_role, organisation_unit, at=at):
		fail("CM_AUTHORITY", missing="responsibility", responsibility=business_role, organisation_unit=organisation_unit or None, provisioned_by=PROVISIONED_BY)


def require_capacity(case: str, user: str, capacity: str, *, at=None) -> dict[str, Any]:
	"""The responsibility **and** the exact effective appointment or mandate for this contract. Returns the binding's evidence."""
	responsibility = CAPACITY_RESPONSIBILITY[capacity]
	require(user, responsibility, at=at)
	provider = BINDINGS.get(capacity) or _default(capacity)
	found = provider(case, user, at) if provider else None
	if not found:
		fail("CM_AUTHORITY", missing="appointment", capacity=capacity, responsibility=responsibility, reason="No effective appointment or mandate is recorded for this person on this contract. An assignment alone grants no contract access.",
			provisioned_by="Head of procurement function recommends; Accounting Officer appoints")
	return found
