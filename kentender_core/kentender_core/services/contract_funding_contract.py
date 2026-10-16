# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published seam between the owner of funding (Budget) and Contract Management (CM-CHG-001 v0.8 section 5.14, plan D5, D7).

Contract Management never writes a funding row. When an agreement takes effect it asks the funding owner, through this seam, to convert the reservation lineage the Award
package carried into a commitment; later phases ask it to adjust and to close. Each owner registers a provider on `kt_contract_funding_provider`, a callable returning a provider
object (or None to decline, for example outside a simulation environment):

    lookup(*, identity)                                  -> {"reference", "amount"} | None
    convert(*, identity, contract, allocations, amount, lineage=None) -> {"reference", "amount"}   (the whole allocation of one award, atomically; raises `Refused` when the owner definitively refuses)
    adjust(*, identity, contract, allocations, event_id, event_type)
                                                         -> {"reference", "amount", "before", "after"}   (optional; each allocation is `{"reservation", "new_total"}`, the supported total of
                                                            that commitment after a lawful variation or termination; raises `Refused`. A commitment already Closed accepts no adjustment from the
                                                            contract service: the funding owner lowers it only through its own approved correction)
    close(*, identity, contract, final_amount, event_id, event_type, evidence)
                                                         -> {"reference", "amount"}   (optional; closes the reconciled commitment once and releases nothing; raises `Refused`)
    recall(*, identity)                                  -> {"reference", "amount"} | None   (optional; what an adjustment or closure already did under an identity, so the caller reads the owner first)
    revalidate(*, identity, contract, allocations)       -> {"reservations": [{"reservation", "status"}], "problems": [plain words]}   (optional; the owner re-reads the exact reservations the contract's award names and
                                                            decides each one's status; it converts, releases and moves nothing. The owner's decision of 16 October 2026: Contract Management may ask this, for its own contract's
                                                            reservations only. Raises `Refused` for a reservation the award does not name; `problems` is empty when every reservation can still be drawn on)

`identity` is Contract Management's operation identity. A provider must be **idempotent on it**: `lookup` answers what it already holds under an identity, and `convert` called again
with the same identity returns that same result and creates nothing more. That is what lets Contract Management read the owner first, link what exists and never convert twice.
With no provider, `convert` raises `Unavailable` and the caller treats the outcome as not done. Tests may set `frappe.flags.kt_contract_funding_providers` to a list of providers."""

from __future__ import annotations

from typing import Any

import frappe

HOOK = "kt_contract_funding_provider"
FUNCTIONS: tuple[str, ...] = ("lookup", "convert")
OPTIONAL: tuple[str, ...] = ("adjust", "close", "recall", "revalidate")


class Refused(Exception):
	"""The funding owner definitively refused: nothing was created and a corrected retry may run."""


class Unavailable(Exception):
	"""No funding owner answered."""


def providers() -> list[Any]:
	override = frappe.flags.get("kt_contract_funding_providers")
	if override is not None:
		return list(override)
	found = []
	for path in frappe.get_hooks(HOOK) or []:
		try:
			provider = frappe.get_attr(path)()
		except Exception:
			frappe.log_error(title=f"Contract funding provider failed to load: {path}")
			continue
		if provider is not None:
			found.append(provider)
	return found


def missing_functions(candidate: Any) -> list[str]:
	return [name for name in FUNCTIONS if not callable(getattr(candidate, name, None))]


def lookup(identity: str) -> dict[str, Any] | None:
	for provider in providers():
		answer = provider.lookup(identity=identity)
		if answer is not None:
			return answer
	return None


def convert(identity: str, *, contract: str, allocations: list[dict[str, Any]], amount: float, lineage: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Ask the funding owner to convert the whole allocation of one award, once. `lineage` is what Contract Management relays exactly as Award supplied it (the award case and decision, the allocation and its
	digest, the package digest and the agreement version); the funding owner has the award's owner verify it (BUD-CHG-001 v1.16 BUD-BR-036). A provider that does not take a lineage is called without it."""
	import inspect

	chosen = providers()
	if not chosen:
		raise Unavailable("No funding owner is installed on this site.")
	provider = chosen[-1]
	takes = "lineage" in inspect.signature(provider.convert).parameters
	extra = {"lineage": lineage} if takes else {}
	return provider.convert(identity=identity, contract=contract, allocations=allocations, amount=amount, **extra)


def adjust(identity: str, *, contract: str, allocations: list[dict[str, Any]], event_id: str, event_type: str) -> dict[str, Any]:
	"""Ask the funding owner to apply a lawful variation or termination: the supported total of each commitment. Idempotent on `identity`."""
	chosen = [p for p in providers() if callable(getattr(p, "adjust", None))]
	if not chosen:
		raise Unavailable("No funding owner able to adjust a commitment is installed on this site.")
	return chosen[-1].adjust(identity=identity, contract=contract, allocations=allocations, event_id=event_id, event_type=event_type)


def close(identity: str, *, contract: str, final_amount: float, event_id: str, event_type: str, evidence: list[str]) -> dict[str, Any]:
	"""Ask the funding owner to close the contract's commitment on a reconciled outcome. Idempotent on `identity`; releases no funds."""
	chosen = [p for p in providers() if callable(getattr(p, "close", None))]
	if not chosen:
		raise Unavailable("No funding owner able to close a commitment is installed on this site.")
	return chosen[-1].close(identity=identity, contract=contract, final_amount=final_amount, event_id=event_id, event_type=event_type, evidence=evidence)


def recall(identity: str) -> dict[str, Any] | None:
	"""What the funding owner already did under an adjustment or closure identity, or None. Lets a retry read the owner first and link what exists."""
	for provider in providers():
		reader = getattr(provider, "recall", None)
		if callable(reader):
			answer = reader(identity=identity)
			if answer is not None:
				return answer
	return None


def revalidate(identity: str, *, contract: str, allocations: list[dict[str, Any]]) -> dict[str, Any] | None:
	"""Ask the funding owner to revalidate the reservations a contract's award names, before a step that depends on them. None when no funding owner on this site can: the caller then goes on as it did before the
	owner offered it, because no owner means nothing to ask. Moves no funds."""
	chosen = [p for p in providers() if callable(getattr(p, "revalidate", None))]
	if not chosen:
		return None
	return chosen[-1].revalidate(identity=identity, contract=contract, allocations=allocations)
