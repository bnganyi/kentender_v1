# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-002 / LV-R8-BE-02 — PLC-SMOKE-BE-002: journey aggregates Strategy→Tender spine.

Pack §15.1 / tracker §13:

    get_procurement_journey("JRN-MOH-2026-001") returns Strategy, Budget, Demand,
    Planning, STD Readiness, Tender, Opening steps.

Interpreted against WORKS §15: the **material spine through tender publication** is the
first seven ``step_key`` values (``strategy`` … ``tender_publication``); the full journey
response includes all **12** §15 rows through ``contract`` (remaining steps Not Started
at base ``TENDER_PUBLISHED`` — aligned with **R3-013**).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r8_002_plc_smoke_be_002_journey_aggregation

Companion evidence:
docs/prompts/0. usability handoff/R8_002_plc_smoke_be_002_evidence.md
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import (
    upsert_works_master_demand,
)
from kentender_procurement.procurement_planning.seeds.works_master_planning_seed import (
    upsert_works_master_planning,
)
from kentender_procurement.tender_management.seeds.works_master_std_seed import (
    upsert_works_master_std,
)
from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
    upsert_works_master_tender,
)
from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
    load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.journey_aggregate import (
    get_procurement_journey,
)
from kentender_procurement.procurement_lifecycle.works_seed_step_contract import (
    WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"


class TestR8002PlcSmokeBe002JourneyAggregation(IntegrationTestCase):
    """PLC-SMOKE-BE-002 — get_procurement_journey step list after WORKS master PLC load."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        for label, fn in (
            ("Strategy", upsert_works_master_strategy_hierarchy),
            ("Budget", upsert_works_master_budget),
            ("Demand", upsert_works_master_demand),
            ("Planning", upsert_works_master_planning),
            ("STD", upsert_works_master_std),
            ("Tender", upsert_works_master_tender),
        ):
            result = fn()
            assert result.get("ok"), f"{label} seed failed: {result}"

        frappe.db.commit()

    def test_plc_smoke_be_002_get_procurement_journey_step_spine(self):
        """PLC-SMOKE-BE-002 — 12 steps in §15 order; first seven = Strategy→Tender spine."""
        load_out = load_procurement_lifecycle_works_master(
            reset=True,
            checkpoint="TENDER_PUBLISHED",
        )
        self.assertTrue(load_out.get("ok"), msg=f"PLC load failed: {load_out}")
        frappe.db.commit()

        journey = get_procurement_journey(JOURNEY_CODE)
        steps = journey.get("steps") or []
        self.assertEqual(
            len(steps),
            len(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER),
            msg="Expected 12 materialized §15 steps",
        )

        keys = [s.get("step_key") for s in steps]
        self.assertEqual(
            keys,
            list(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER),
            msg="Step keys must match WORKS §15 order (R1-004 contract)",
        )

        # Pack wording: Strategy → … → Tender (through ``tender_publication``).
        strategy_to_tender = WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER[:7]
        self.assertEqual(keys[:7], list(strategy_to_tender))

        # Opening / post-tender spine rows exist (base checkpoint: usually Not Started).
        post_tender = WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER[7:]
        self.assertEqual(keys[7:], list(post_tender))
        self.assertIn("opening_readiness", keys)
        self.assertIn("bid_opening", keys)
