# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-001 / LV-R8-BE-01 — PLC-SMOKE-BE-001: master WORKS seed load (base checkpoint).

Also cited for **§14 G9-009** (Final Acceptance) — base ``TENDER_PUBLISHED`` master seed load + key validator PASS rows.

Pack §15.1 / tracker §13:

    load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")
    creates JRN-MOH-2026-001 and all required base handoff cards. Base checkpoint must
    not materialize CLOSECERT / OPENREADY.

Also asserts **R2-003** checks **VAL-SEED-001** + **VAL-SEED-016–019** PASS (PLC spine /
handoff consistency). Full validator ``ok`` may still FAIL until TM2 publication fixtures
satisfy **VAL-SEED-014/015/020/022**.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r8_001_plc_smoke_be_001_master_seed_load

Companion evidence:
docs/prompts/0. usability handoff/R8_001_plc_smoke_be_001_evidence.md
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
    validate_procurement_lifecycle_works_master_seed,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    BASE_HANDOFF_CODES,
    JOURNEY_CODE,
    OPENING_HANDOFF_CODES,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"


class TestR8001PlcSmokeBe001MasterSeedLoad(IntegrationTestCase):
    """PLC-SMOKE-BE-001 — reset load + structural assertions + validator."""

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

    def test_plc_smoke_be_001_reset_load_base_checkpoint(self):
        """PLC-SMOKE-BE-001 — ``reset=True`` base load creates journey + 7 cards; no opening cards."""
        load_out = load_procurement_lifecycle_works_master(
            reset=True,
            checkpoint="TENDER_PUBLISHED",
        )
        self.assertTrue(
            load_out.get("ok"),
            msg=f"WORKS master PLC load failed: {load_out}",
        )
        frappe.db.commit()

        self.assertTrue(
            frappe.db.exists("Procurement Journey", JOURNEY_CODE),
            msg=f"Expected Procurement Journey {JOURNEY_CODE} after PLC load",
        )

        for hc in BASE_HANDOFF_CODES:
            self.assertTrue(
                frappe.db.exists("Procurement Handoff Card", hc),
                msg=f"Missing base handoff card {hc}",
            )

        for oc in OPENING_HANDOFF_CODES:
            self.assertFalse(
                frappe.db.exists("Procurement Handoff Card", oc),
                msg=f"Base checkpoint must not create opening handoff {oc}",
            )

        val_out = validate_procurement_lifecycle_works_master_seed(checkpoint="TENDER_PUBLISHED")
        self.assertIn("checks", val_out)
        by_id = {c["check_id"]: c for c in val_out["checks"]}
        # PLC-SMOKE-BE-001 focuses on PLC materialization + spine consistency (pack §15.1).
        # Full R2-003 aggregate ``ok`` may still FAIL until TM2 publication fixtures satisfy
        # VAL-SEED-014/015/020/022 on the site (outside this smoke scope).
        for cid in (
            "VAL-SEED-001",
            "VAL-SEED-016",
            "VAL-SEED-017",
            "VAL-SEED-018",
            "VAL-SEED-019",
        ):
            self.assertEqual(
                by_id[cid]["result"],
                "PASS",
                msg=f"{cid}: {by_id.get(cid)}",
            )
