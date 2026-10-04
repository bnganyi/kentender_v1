# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A failing support transport for test environments only (BOP-CHG-001 v0.10
§10 negative branch (6): "The first support notification fails"). While the
test controls force it, delivery fails; otherwise it stays silent and the
Notification Log transport answers."""

from __future__ import annotations

from kentender_procurement.bid_opening.services import simulation


def transport(**_kwargs) -> dict | None:
	if simulation.enabled() and simulation.controls()["notify_outcome"] == "Fail":
		return {"delivered": False, "delivered_to": []}
	return None
