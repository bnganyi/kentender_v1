# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-016 / LV-R8-BE-06 — PLC-SMOKE-BE-006: optional-opening checkpoint hygiene.

Pack §15.1 **PLC-SMOKE-BE-006** / rectification Cursor pack §15.1:

    Base ``TENDER_PUBLISHED`` PLC load must not fabricate ``CLOSECERT`` /
    ``OPENREADY`` master handoffs, wire journey spine rows into optional closing/opening
    handoff linkage, or flip the journey header into the ``OPENING_READY`` profile.

**OPENING_READY** remains an explicit checkpoint (tests elsewhere); this smoke asserts
base isolation after the **same prerequisite chain** as **R8-001**.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r8_016_plc_smoke_be_006_optional_opening_seed_hygiene

Companion evidence:
docs/prompts/0. usability handoff/R8_016_plc_smoke_be_006_evidence.md
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
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    BASE_HANDOFF_CODES,
    JOURNEY_CODE,
    OPENING_HANDOFF_CODES,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_loader import (
    JOURNEY_HEADER_STAGE_KEY,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"


class TestR8016PlcSmokeBe006OptionalOpeningSeedHygiene(IntegrationTestCase):
    """PLC-SMOKE-BE-006 — base checkpoint remains free of optional opening artefacts."""

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

    def test_plc_smoke_be_006_base_no_opening_handoffs_or_journey_profile_drift(self):
        """Base ``TENDER_PUBLISHED`` reset load: PLC omits CLOSECERT/OPENREADY artefacts."""
        load_out = load_procurement_lifecycle_works_master(
            reset=True,
            checkpoint="TENDER_PUBLISHED",
        )
        self.assertTrue(load_out.get("ok"), msg=f"PLC load failed: {load_out}")
        frappe.db.commit()

        self.assertEqual(
            load_out.get("created_or_updated", {}).get("handoff_cards"),
            len(BASE_HANDOFF_CODES),
            msg="Base checkpoint must materialise exactly the seven §16 base cards",
        )

        for oc in OPENING_HANDOFF_CODES:
            self.assertFalse(
                frappe.db.exists("Procurement Handoff Card", oc),
                msg=f"Base checkpoint must not create opening handoff {oc}",
            )

        j = frappe.get_doc("Procurement Journey", JOURNEY_CODE)
        self.assertEqual(
            (j.opening_readiness_ref or "").strip(),
            "",
            msg="Journey header must not reference opening readiness at base checkpoint",
        )
        self.assertEqual(
            (j.current_stage_key or "").strip(),
            JOURNEY_HEADER_STAGE_KEY,
            msg="Journey header stage must remain tender_published at base checkpoint",
        )

        by_key = {row.step_key: row for row in (j.steps or [])}
        for sk in ("tender_closing", "opening_readiness"):
            row = by_key.get(sk)
            self.assertIsNotNone(row, msg=f"Missing journey step {sk}")
            hc = (row.handoff_code or "").strip()
            self.assertNotIn(
                hc,
                OPENING_HANDOFF_CODES,
                msg=f"Step {sk} must not carry optional opening handoff_code (got {hc!r})",
            )
            soc = (row.source_object_code or "").strip()
            self.assertFalse(
                soc.startswith("CLS-TND") or soc.startswith("ORR-TND"),
                msg=f"Step {sk} must not fabricate CLS/ORR source codes (got {soc!r})",
            )
