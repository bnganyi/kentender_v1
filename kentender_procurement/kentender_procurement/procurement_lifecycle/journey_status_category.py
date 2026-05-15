# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-001 — canonical Procurement Journey **status category** vocabulary (pack §5.3 / tracker R1-001)."""

from __future__ import annotations

from enum import StrEnum


class ProcurementJourneyStatusCategory(StrEnum):
	"""Standard journey status shown on step cards and journey aggregates (non-authoritative per ADR-PLC-002)."""

	NOT_STARTED = "Not Started"
	"""No material work has begun on this step from the buyer’s perspective."""

	IN_PROGRESS = "In Progress"
	"""Work is underway; no blocking issue and no pending approval queue item implied."""

	NEEDS_ACTION = "Needs Action"
	"""Waiting on a person or role (submit, review, correction) before the step can advance."""

	BLOCKED = "Blocked"
	"""Hard stop: dependency, validation, or external gate prevents progress until resolved."""

	READY_FOR_HANDOFF = "Ready for Handoff"
	"""Source module work satisfies local rules; a formal handoff artefact can be produced or consumed."""

	HANDED_OFF = "Handed Off"
	"""Responsibility or record has crossed the module boundary (e.g. package released to tendering)."""

	COMPLETED = "Completed"
	"""This lifecycle step is finished for the journey; no further module action expected here."""

	RETURNED = "Returned"
	"""Sent back to an earlier owner or state for rework (distinct from simple “needs action”)."""

	CANCELLED = "Cancelled"
	"""The path or object will not proceed; terminal for normal progression."""

	SUPERSEDED = "Superseded"
	"""Replaced by a newer record or journey line; retained only for traceability."""

	AUDIT_ONLY = "Audit Only"
	"""Visible for audit/legal trace only; not an active operational lane."""

	STALE = "Stale"
	"""Derived: aggregate or handoff evidence is out of date vs source-of-truth (not a raw DocStatus)."""


JOURNEY_STATUS_CATEGORY_VALUES: frozenset[str] = frozenset(
	member.value for member in ProcurementJourneyStatusCategory
)


def is_valid_journey_status_category(value: str) -> bool:
	return value in JOURNEY_STATUS_CATEGORY_VALUES
