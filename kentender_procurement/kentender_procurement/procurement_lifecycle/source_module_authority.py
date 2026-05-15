# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-010 — source module authority (ADR-PLC-002, NG-002, PLC-CURSOR-003).

**Procurement Journey** and **Procurement Handoff Card** are navigation / evidence
aggregates. They must **not** overwrite workflow or legal state on owning DocTypes.

This module holds **pure helpers** for R3 stale/conflict handling: recommendations and
handoff-only field patches. Any transition that marks a handoff **Stale** must apply
changes **only** to the handoff document (or dedicated PLC tables), never to Demand,
Procurement Package, TM2 Tender, etc.
"""

from __future__ import annotations

from typing import Final

# DocTypes that own binding workflow / legal state for PLC spine objects (non-exhaustive;
# extend when new source modules join the journey).
AUTHORITATIVE_SOURCE_DOCTYPES: Final[frozenset[str]] = frozenset(
	("Demand", "Procurement Package", "TM2 Tender")
)

# Handoff statuses where we still surface source drift as a stale recommendation (ADR-PLC-002).
_STATUSES_ELIGIBLE_FOR_STALE_ON_DRIFT: Final[frozenset[str]] = frozenset(
	(
		"Draft",
		"Ready",
		"Handed Off",
		"Consumed",
		"Blocked",
		"Returned",
		"Audit Only",
	)
)


def recommend_handoff_stale_for_source_fingerprint_drift(
	*,
	handoff_status: str,
	snapshot_fingerprint: str | None,
	live_fingerprint: str | None,
) -> str | None:
	"""Return a ``stale_reason`` string to store **on the handoff**, or ``None``.

	Callers persist **only** onto ``Procurement Handoff Card`` (e.g. ``status='Stale'``,
	``stale_reason``). This function performs **no** database I/O and never touches source
	DocTypes — LV-R1-010-01 “stale detection does not mutate source”.
	"""
	status = (handoff_status or "").strip()
	if status == "Stale":
		return None
	if status not in _STATUSES_ELIGIBLE_FOR_STALE_ON_DRIFT:
		return None
	if snapshot_fingerprint is None or live_fingerprint is None:
		return None
	if snapshot_fingerprint == live_fingerprint:
		return None
	return "source_module_state_changed_since_handoff"


def handoff_fields_for_stale_mark(*, stale_reason: str) -> dict[str, str]:
	"""Return a **handoff-only** field map for marking stale (R3 services use with ``db_set`` on handoff)."""
	return {"status": "Stale", "stale_reason": (stale_reason or "").strip() or "stale"}
