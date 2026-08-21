# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT demand supplement — retired with DIA preparatory teardown.

Historically created ``DEM-MOH-IT-2026-001``. Demand Intake DocTypes are deleted;
Demands MVP-1 will reintroduce fixtures. Callers should treat this as a no-op skip.
"""

from __future__ import annotations

from typing import Any


def upsert_it_demand_supplement() -> dict[str, Any]:
	return {
		"ok": True,
		"skipped": True,
		"reason": "DEMAND_MODULE_RETIRED",
		"message": (
			"IT Demand supplement skipped — Demand Intake retired pending Demands MVP-1."
		),
	}
