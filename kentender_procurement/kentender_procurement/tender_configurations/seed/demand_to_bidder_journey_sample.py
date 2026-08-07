# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Demand → bidder journey sample — retired with DIA preparatory teardown.

Historically seeded DIA Demand rows plus Tender Configuration walk samples.
Demand Intake DocTypes are deleted; Demands MVP-1 will redefine this pack.

Usage (now a no-op skip):
  bench --site kentender.midas.com execute \\
    kentender_procurement.tender_configurations.seed.demand_to_bidder_journey_sample.run
"""

from __future__ import annotations

from typing import Any

import frappe


def run(*, clear: bool = True) -> dict[str, Any]:
	"""Retired with DIA preparatory teardown — Demands MVP-1 will replace this pack."""
	frappe.only_for(("System Manager", "Administrator"))
	return {
		"ok": False,
		"skipped": True,
		"reason": "DEMAND_MODULE_RETIRED",
		"pack": "demand_to_bidder_journey_sample",
		"message": (
			"Demand Intake retired pending Demands MVP-1 rebuild; "
			"demand→bidder journey sample not loaded."
		),
		"clear": clear,
	}
