# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable WORKS demand business codes retained after DIA Demand DocType deletion.

PP2 / journey fixtures historically imported these from ``demand_intake.seeds``.
Demands MVP-1 will redefine demand fixtures; until then callers may reference
these codes for journey/plan constants without importing deleted DIA modules.
"""

from __future__ import annotations

WORKS_DEMAND_CODE = "DEM-MOH-2026-001"
WORKS_DEMAND_ID = WORKS_DEMAND_CODE
WORKS_DEMAND_TITLE = "District Hospital Renovation Works"
IT_DEMAND_CODE = "DEM-MOH-IT-2026-001"
