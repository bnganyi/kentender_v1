# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Skip stubs replacing deleted ``demand_intake.seeds.works_master_demand_seed``.

Callers that still import ``upsert_works_master_demand`` / ``DEMAND_TITLE`` get
constants plus an explicit skip once Demand DocType is gone (or always, since
the seed implementation was deleted with DIA preparatory teardown).
"""

from __future__ import annotations

from unittest import SkipTest

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live

from kentender_procurement.procurement_lifecycle.legacy_demand_codes import (
	WORKS_DEMAND_CODE,
	WORKS_DEMAND_ID,
	WORKS_DEMAND_TITLE,
)

# Historical names expected by PP2 / tender tests
DEMAND_ID = WORKS_DEMAND_ID
DEMAND_CODE = WORKS_DEMAND_CODE
DEMAND_TITLE = WORKS_DEMAND_TITLE


def upsert_works_master_demand() -> dict:
	"""Former DIA WORKS demand seed — retired; tests must skip."""
	if not demand_consumers_live():
		raise SkipTest(
			"Demand Intake retired pending Demands MVP-1 rebuild "
			"(docs/mvp-1/03_demands/05_Demands_Teardown_Dependency_Inventory.md)."
		)
	raise SkipTest(
		"works_master_demand_seed deleted with DIA preparatory teardown; "
		"Demands MVP-1 seed not yet available."
	)
