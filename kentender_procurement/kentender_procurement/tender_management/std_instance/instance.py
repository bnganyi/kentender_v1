# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Instance root aggregate — tender-specific realization of an active STD Template Version.

STDINST-0100. One current instance per tender; created only from Tender context.

The Frappe document ``name`` is the canonical **instance code** (naming series ``STDINST-.#####``).
"""

from __future__ import annotations

# Pack §5 / doc 1 §6.1 — instance lifecycle (order matches Select options in DocType)
INSTANCE_STATUSES: tuple[str, ...] = (
	"Draft",
	"In Configuration",
	"Validation Blocked",
	"Ready for Publication",
	"Locked for Approval",
	"Published Locked",
	"Addendum Pending",
	"Addendum Regenerated",
	"Superseded",
	"Cancelled",
)

# When an instance is in one of these statuses, the tender may hold another (new) instance.
INSTANCE_STATUS_RELEASES_SLOT: frozenset[str] = frozenset({"Superseded", "Cancelled"})

# Minimal readiness vocabulary (refine in STDINST-0700)
READINESS_STATUSES: tuple[str, ...] = (
	"Not Ready",
	"Ready",
	"Blocked",
)

INSTANCE_STATUS_OPTIONS: str = "\n".join(INSTANCE_STATUSES)
READINESS_STATUS_OPTIONS: str = "\n".join(READINESS_STATUSES)


def is_valid_instance_status(value: str | None) -> bool:
	return bool(value) and value in INSTANCE_STATUSES


def is_valid_readiness_status(value: str | None) -> bool:
	return bool(value) and value in READINESS_STATUSES


def instance_status_occupies_tender_slot(status: str | None) -> bool:
	"""True if this status counts as the single active STD Instance for the tender."""
	if not status:
		return False
	return status not in INSTANCE_STATUS_RELEASES_SLOT
