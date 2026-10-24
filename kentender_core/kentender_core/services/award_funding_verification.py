# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published seam between Budget and the owner of an award's funding allocation (AWD-CHG-001 v0.7 section 7.1 `VerifyAwardFundingLineage`; BUD-CHG-001 v1.16 BUD-BR-036).

Budget refuses to turn a reservation into a commitment unless the whole chain matches: the plan source allocation, the exact Requisition Version and drawdown line, the Tender (and lot), the Award and its
version, and the contract. Budget never reads another module's records and never trusts an identifier a browser supplied, so it asks the owner of the award's funding allocation through this seam. Core holds
no domain controller and imports neither Award nor Contract Management: the owner registers a provider on `kt_award_funding_verification`, a callable returning an object (or None to decline):

    verify(*, lineage, contract, allocations, purpose) -> Verification

`lineage` is what Contract Management relayed exactly as Award supplied it: the award case, the allocation and its digest, the package digest and the agreement version. `allocations` is the set Contract
Management is about to convert: `[{"reservation", "amount"}]`. `purpose` names the consequential operation (`convert`). The answer is one of three, and Unknown is never a negative authorisation or a success:

    Verified      the complete current source handoff and Award authority agree; `allocation` is the immutable full payload and `revision` its digest, to be pinned and rechecked under Budget's locks
    Not verified  specific `mismatches` (plain words) and any restriction; nothing may be converted
    Unavailable   the owner could not answer; Budget refuses (fail closed) and the caller may retry

With no provider that answers, Budget gets Unavailable and refuses: no answer is never a yes. Several providers are asked in turn; the first answer that is not None wins.

Seeds and tests may set `frappe.flags.kt_award_funding_verifications` to a list of providers; `installed()`, `verified_for()` and `permit_all()` do it with a clean-up. Nothing else in production code sets it
(a repository test fails if it does)."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

import frappe

HOOK = "kt_award_funding_verification"
FLAG = "kt_award_funding_verifications"

VERIFIED = "Verified"
NOT_VERIFIED = "Not verified"
UNAVAILABLE = "Unavailable"


@dataclass
class Verification:
	status: str
	mismatches: list[str] = field(default_factory=list)
	allocation: dict[str, Any] | None = None
	revision: str = ""

	@property
	def verified(self) -> bool:
		return self.status == VERIFIED

	def as_dict(self) -> dict[str, Any]:
		return {"status": self.status, "mismatches": list(self.mismatches), "allocation": self.allocation, "revision": self.revision}


def providers() -> list[Any]:
	override = frappe.flags.get(FLAG)
	if override is not None:
		return list(override)
	found = []
	for path in frappe.get_hooks(HOOK) or []:
		try:
			provider = frappe.get_attr(path)()
		except Exception:
			frappe.log_error(title=f"Award funding verification failed to load: {path}")
			continue
		if provider is not None:
			found.append(provider)
	return found


def verify(*, lineage: dict[str, Any] | None, contract: str, allocations: list[dict[str, Any]], purpose: str = "convert") -> Verification:
	"""The owner's verification, or Unavailable when no owner answers or the answer cannot be read. Never raises for an owner that cannot answer."""
	for provider in providers():
		try:
			answer = provider.verify(lineage=dict(lineage or {}), contract=contract, allocations=list(allocations or []), purpose=purpose)
		except Exception:
			frappe.log_error(title="Award funding verification failed")
			return Verification(UNAVAILABLE, ["The owner of the award's funding allocation could not answer."])
		if answer is not None:
			return answer if isinstance(answer, Verification) else Verification(**answer)
	return Verification(UNAVAILABLE, ["No owner of an award's funding allocation is installed on this site."])


class Static:
	"""A fixed answer for seeds and tests: each listed contract has exactly the reservations given and the stated allocation; any other contract is Not verified."""

	def __init__(self, awarded: dict[str, list[str]], *, revision: str = "static"):
		self.awarded = {contract: set(reservations) for contract, reservations in awarded.items()}
		self.revision = revision

	def verify(self, *, lineage, contract, allocations, purpose) -> Verification | None:
		if contract not in self.awarded:
			return None
		named = {str(a.get("reservation") or "") for a in allocations}
		if not named or not named <= self.awarded[contract]:
			return Verification(NOT_VERIFIED, [f"Reservation {r} is not one of the reservations awarded to this contract." for r in sorted(named - self.awarded[contract])] or ["No reservation was named."])
		return Verification(VERIFIED, [], {"static": True, "allocations": [dict(a) for a in allocations]}, self.revision)


class PermitAll:
	"""For tests whose subject is not the lineage: every set of allocations is Verified, and the payload echoes what was asked."""

	def verify(self, *, lineage, contract, allocations, purpose) -> Verification:
		return Verification(VERIFIED, [], {"permit_all": True, "allocations": [dict(a) for a in allocations], "lineage": dict(lineage or {})}, "permit-all")


@contextmanager
def installed(*verifiers: Any) -> Iterator[None]:
	previous = frappe.flags.get(FLAG)
	frappe.flags[FLAG] = list(verifiers)
	try:
		yield
	finally:
		frappe.flags[FLAG] = previous


def verified_for(contract: str, *reservations: str):
	"""For a seed that stands in for Contract Management and Award: within the block, `contract` is awarded exactly these reservations and no other contract is known."""
	return installed(Static({contract: list(reservations)}))


def permit_all(testcase) -> None:
	"""Install `PermitAll` for one test case and put the previous setting back afterwards."""
	previous = frappe.flags.get(FLAG)
	frappe.flags[FLAG] = [PermitAll()]
	testcase.addCleanup(lambda: frappe.flags.update({FLAG: previous}))
