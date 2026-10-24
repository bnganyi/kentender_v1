# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The seam between Requisitions (which coordinates a whole-Tender cancellation recovery) and Tenders (which owns the cancellation)
(REQ-CHG-001 v1.20 §10.3, TPR-CHG-001 v0.21 §7.5: `GetTenderCancellationRecoveryBasis.v1`).

Requisitions sits upstream of Tenders and must not import it, so it asks for the basis here. Tenders registers a provider on
`kt_tender_cancellation_recovery_basis`, a callable returning an object with

    recovery_basis(*, tender, cancellation, recovery_id) -> dict

whose answer carries a `verdict`:

- `positive`    the Tender's current authoritative state supports restoring the allowance: it is cancelled by the recorded cancellation,
                the consumed lineage is what Requisitions registered, and the owners of the pre-award-notification guard and of any
                downstream use find none;
- `negative`    the owners prove the allowance may not be restored (an award was notified, a contract exists, the lineage differs): the
                recovery needs attention and nothing is restored;
- `unavailable` an owner could not be asked or its answer was unknown, stale or in progress: the recovery stays Pending and is retried.

A caller's assertion, a cached projection and a null lookup are never positive. With no provider, or no provider that knows the
cancellation, the answer is `unavailable`: no answer is never a yes. Several providers are asked in turn and the first answer that is
not `unavailable` wins.

Seeds and tests may set `frappe.flags.kt_tender_cancellation_recovery_bases`; `installed()` does it with a clean-up. Nothing else in
production code sets it (`test_cancellation_recovery_seam` fails if it does)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import frappe

HOOK = "kt_tender_cancellation_recovery_basis"
FLAG = "kt_tender_cancellation_recovery_bases"
#: Requisitions registers a reader on this hook so that Budget (which sits upstream of it) can show a held reservation's recovery status.
READER_HOOK = "kt_cancellation_recovery_reader"

POSITIVE = "positive"
NEGATIVE = "negative"
UNAVAILABLE = "unavailable"


def providers() -> list[Any]:
	override = frappe.flags.get(FLAG)
	if override is not None:
		return list(override)
	found = []
	for path in frappe.get_hooks(HOOK) or []:
		try:
			provider = frappe.get_attr(path)()
		except Exception:
			frappe.log_error(title=f"Tender cancellation recovery basis failed to load: {path}")
			continue
		if provider is not None:
			found.append(provider)
	return found


def unavailable(reason: str) -> dict[str, Any]:
	return {"verdict": UNAVAILABLE, "reason": reason, "evidence": []}


def basis(*, tender: str, cancellation: str, recovery_id: str) -> dict[str, Any]:
	"""The Tender owner's verified answer for one recovery, or `unavailable`."""
	last: dict[str, Any] | None = None
	for provider in providers():
		answer = provider.recovery_basis(tender=tender, cancellation=cancellation, recovery_id=recovery_id)
		if not isinstance(answer, dict):
			continue
		if answer.get("verdict") in (POSITIVE, NEGATIVE):
			return answer
		if answer.get("verdict") == UNAVAILABLE:
			last = answer
	return last or unavailable("No Tender owner could be asked for this cancellation.")


def recoveries_of_reservations(reservations: list[str]) -> dict[str, dict[str, Any]]:
	"""For each reservation whose Tender's recovery is not yet complete: its status, the label and explanation of that status and the owner's
	reason. A reservation with no unfinished recovery is absent. With no reader the answer is empty: Budget then shows the reservation as it is,
	which is the truth (it is held), and never an invented status."""
	out: dict[str, dict[str, Any]] = {}
	for path in frappe.get_hooks(READER_HOOK) or []:
		try:
			reader = frappe.get_attr(path)()
			out.update(reader.for_reservations(list(reservations)) if reader is not None else {})
		except Exception:
			frappe.log_error(title=f"Cancellation recovery reader failed: {path}")
	return out


class Static:
	"""A fixed answer for tests: the same answer for every cancellation."""

	def __init__(self, answer: dict[str, Any]):
		self.answer = answer

	def recovery_basis(self, *, tender: str, cancellation: str, recovery_id: str) -> dict[str, Any]:
		return dict(self.answer)


@contextmanager
def installed(*owners: Any) -> Iterator[None]:
	previous = frappe.flags.get(FLAG)
	frappe.flags[FLAG] = list(owners)
	try:
		yield
	finally:
		frappe.flags[FLAG] = previous
