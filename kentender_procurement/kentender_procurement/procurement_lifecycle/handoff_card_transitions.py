# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-008 / LV-R1-008-01 — **Procurement Handoff Card** status transition helpers.

Vocabulary matches cursor pack §6.3 / ``handoff_card_status.HANDOFF_CARD_STATUS_VALUES``.

The transition graph is **non-authoritative** (ADR-PLC-002): services (R3) may enforce it when
mutating handoffs; Desk/API may still persist legacy rows until backfilled. Rules are
**conservative** — happy path ``Draft → Ready → Handed Off → Consumed``, with explicit
branches for blockers, returns, supersession, audit freeze, staleness, and cancellation.

If product later tightens or loosens edges, change **only** ``ALLOWED_HANDOFF_STATUS_TRANSITIONS``
and extend tests.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from kentender_procurement.procurement_lifecycle.handoff_card_status import HANDOFF_CARD_STATUS_VALUES


class HandoffCardStatus(StrEnum):
	"""StrEnum mirror of pack §6.3 labels (single source for typed call sites)."""

	DRAFT = "Draft"
	READY = "Ready"
	HANDED_OFF = "Handed Off"
	CONSUMED = "Consumed"
	BLOCKED = "Blocked"
	RETURNED = "Returned"
	SUPERSEDED = "Superseded"
	CANCELLED = "Cancelled"
	AUDIT_ONLY = "Audit Only"
	STALE = "Stale"


# Adjacency: from_status -> legal to_status (excluding no-op; see ``assert_valid_handoff_status_transition``).
ALLOWED_HANDOFF_STATUS_TRANSITIONS: Final[dict[str, frozenset[str]]] = {
	"Draft": frozenset({"Ready", "Blocked", "Cancelled"}),
	"Ready": frozenset({"Handed Off", "Blocked", "Cancelled", "Returned", "Stale"}),
	"Handed Off": frozenset(
		{"Consumed", "Blocked", "Returned", "Stale", "Superseded", "Cancelled", "Audit Only"}
	),
	"Consumed": frozenset({"Stale", "Audit Only"}),
	"Blocked": frozenset({"Ready", "Returned", "Cancelled"}),
	"Returned": frozenset({"Draft", "Ready", "Cancelled"}),
	"Stale": frozenset({"Draft", "Ready", "Cancelled", "Superseded"}),
	# Terminals: only no-op (handled before graph lookup).
	"Cancelled": frozenset(),
	"Superseded": frozenset(),
	"Audit Only": frozenset(),
}


def _assert_known(status: str, *, label: str) -> None:
	if status not in HANDOFF_CARD_STATUS_VALUES:
		raise ValueError(f"{label} must be a standard handoff status, got {status!r}")


def can_handoff_status_transition(from_status: str, to_status: str) -> bool:
	"""Return whether ``to_status`` is allowed from ``from_status`` (no-op allowed)."""
	try:
		assert_valid_handoff_status_transition(from_status, to_status)
	except ValueError:
		return False
	return True


def assert_valid_handoff_status_transition(from_status: str, to_status: str) -> None:
	"""Raise ``ValueError`` if ``from_status → to_status`` is not permitted.

	No-op transitions (``from_status == to_status``) are always allowed for idempotent writes.
	"""
	_from = (from_status or "").strip()
	_to = (to_status or "").strip()
	_assert_known(_from, label="from_status")
	_assert_known(_to, label="to_status")
	if _from == _to:
		return
	allowed = ALLOWED_HANDOFF_STATUS_TRANSITIONS.get(_from)
	if allowed is None:
		raise ValueError(f"No transition rules defined for from_status={_from!r}")
	if _to not in allowed:
		raise ValueError(f"Illegal handoff status transition {_from!r} → {_to!r}")


def allowed_next_handoff_statuses(from_status: str) -> frozenset[str]:
	"""Return the set of statuses reachable in one step from ``from_status`` (excluding no-op)."""
	_from = (from_status or "").strip()
	_assert_known(_from, label="from_status")
	return ALLOWED_HANDOFF_STATUS_TRANSITIONS.get(_from, frozenset())


def assert_transition_graph_well_formed() -> None:
	"""Integrity check: graph keys/values ⊆ vocabulary (call from tests)."""
	if set(ALLOWED_HANDOFF_STATUS_TRANSITIONS) != HANDOFF_CARD_STATUS_VALUES:
		raise AssertionError(
			"ALLOWED_HANDOFF_STATUS_TRANSITIONS keys must equal HANDOFF_CARD_STATUS_VALUES exactly"
		)
	for src, targets in ALLOWED_HANDOFF_STATUS_TRANSITIONS.items():
		for t in targets:
			if t not in HANDOFF_CARD_STATUS_VALUES:
				raise AssertionError(f"Unknown target {t!r} from {src!r}")
			if t == src:
				raise AssertionError(f"Self-loop must not appear in graph: {src!r}")
