# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-005 / LV-R1-005-02 — canonical **handoff card** status vocabulary (cursor pack §6.3).

Distinct from **Procurement Journey** step ``status_category`` (R1-001 journey aggregate labels).
Handoff cards use this vocabulary for workflow/evidence cards; transition rules live in
``handoff_card_transitions`` (R1-008 / LV-R1-008-01).
"""

from __future__ import annotations

from typing import Final

# Cursor pack §6.3 "Required Handoff Status Values" — exact spelling for DocType Select + validation.
HANDOFF_CARD_STATUS_VALUES: Final[frozenset[str]] = frozenset(
	{
		"Draft",
		"Ready",
		"Handed Off",
		"Consumed",
		"Blocked",
		"Returned",
		"Superseded",
		"Cancelled",
		"Audit Only",
		"Stale",
	}
)

HANDOFF_CARD_STATUS_OPTIONS: Final[str] = "\n".join(
	(
		"Draft",
		"Ready",
		"Handed Off",
		"Consumed",
		"Blocked",
		"Returned",
		"Superseded",
		"Cancelled",
		"Audit Only",
		"Stale",
	)
)


def is_valid_handoff_card_status(value: str) -> bool:
	return value in HANDOFF_CARD_STATUS_VALUES
