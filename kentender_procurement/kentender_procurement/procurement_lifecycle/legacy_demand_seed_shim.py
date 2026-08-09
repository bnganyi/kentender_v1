# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Thin compatibility shim — DEM-INT-010.

PP2 / lifecycle callers still import ``upsert_works_master_demand`` and
``DEMAND_TITLE`` from this module. Implementation lives on the MVP Demand
seed; this file only re-exports constants and delegates.
"""

from __future__ import annotations

from kentender_procurement.demands.seeds.works_master_demand import (
	upsert_works_master_demand,
)
from kentender_procurement.procurement_lifecycle.legacy_demand_codes import (
	WORKS_DEMAND_CODE,
	WORKS_DEMAND_ID,
	WORKS_DEMAND_TITLE,
)

# Historical names expected by PP2 / tender tests
DEMAND_ID = WORKS_DEMAND_ID
DEMAND_CODE = WORKS_DEMAND_CODE
DEMAND_TITLE = WORKS_DEMAND_TITLE

__all__ = [
	"DEMAND_CODE",
	"DEMAND_ID",
	"DEMAND_TITLE",
	"upsert_works_master_demand",
]
