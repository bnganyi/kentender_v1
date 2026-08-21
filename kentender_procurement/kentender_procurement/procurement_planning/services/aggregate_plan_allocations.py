# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-GAP-FR-001 — post-formation aggregate is hard-denied (source selection once)."""

from __future__ import annotations

from typing import Any


def aggregate_plan_allocations(
	*,
	plan_item: str,
	demand: str,
	demand_item: str | None = None,
	allocated_amount: float | None = None,
	aggregation_reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Source Demands are selected once at formation. Later combine is forbidden."""
	return {
		"ok": False,
		"errors": {
			"form": (
				"Source selection happens once. This Plan Item already has its Demand(s). "
				"Add another Demand as a separate Plan Item, or remove this item from the draft."
			)
		},
	}
