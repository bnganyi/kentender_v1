# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A renderer fault for test environments only (BOP-CHG-001 v0.10 §10
negative branch (2); plan D17): while the test controls force it, a package
cannot be rendered, or the renderer gives no answer. Otherwise it stays
silent and the default renderer answers."""

from __future__ import annotations

from kentender_procurement.bid_opening.services import simulation


class FaultRenderer:
	def __init__(self, forced: str):
		self.forced = forced

	def render(self, **_kwargs) -> dict:
		if self.forced == "Unreadable":
			return {"outcome": "Rejected", "reason": "unreadable", "simulation": True}
		return {"outcome": "Indeterminate", "simulation": True}


def service() -> FaultRenderer | None:
	if not simulation.enabled():
		return None
	forced = simulation.controls()["render_outcome"]
	return FaultRenderer(forced) if forced != "Render" else None
