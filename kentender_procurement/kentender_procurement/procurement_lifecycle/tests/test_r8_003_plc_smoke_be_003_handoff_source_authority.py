# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-003 / LV-R8-BE-03 — PLC-SMOKE-BE-003: handoff cannot override source (stale on drift).

Also satisfies **§14 G9-006** (Final Acceptance) — *Source authority preserved* / NG-002.

Pack §15.1 / ADR-PLC-002 / tracker §13:

    If source package state changes after handoff, handoff card becomes Stale and
    source module remains authoritative.

Uses existing **R3-010** ``validate_handoff_card_freshness`` (handoff-only DB writes;
source DocTypes never modified by that service — **R1-010**).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r8_003_plc_smoke_be_003_handoff_source_authority

Companion evidence:
docs/prompts/0. usability handoff/R8_003_plc_smoke_be_003_evidence.md
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
from kentender_procurement.procurement_lifecycle.evidence_timeline import (
    get_journey_evidence_timeline,
)
from kentender_procurement.procurement_lifecycle.handoff_freshness import (
    validate_handoff_card_freshness,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

_PKG_CODE = "PKG-MOH-2026-001"
_PKGREL_CODE = "PKGREL-MOH-2026-001"
_ALT_METHOD = "Restricted Tender"


class TestR8003PlcSmokeBe003HandoffSourceAuthority(IntegrationTestCase):
    """PLC-SMOKE-BE-003 — PKGREL + package mutation → stale card; package stays authoritative."""

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

    def test_plc_smoke_be_003_pkgrel_stale_when_package_changes_source_kept(self):
        """Mutate PKG source only → PKGREL marked Stale; Procurement Package keeps new method."""
        load_out = load_procurement_lifecycle_works_master(
            reset=True,
            checkpoint="TENDER_PUBLISHED",
        )
        self.assertTrue(load_out.get("ok"), msg=f"PLC load failed: {load_out}")
        frappe.db.commit()

        self.assertTrue(
            frappe.db.exists("Procurement Handoff Card", _PKGREL_CODE),
            msg=f"Expected handoff card {_PKGREL_CODE}",
        )
        pkg_name = frappe.db.get_value(
            "Procurement Package", {"package_code": _PKG_CODE}, "name"
        )
        self.assertIsNotNone(pkg_name, msg="WORKS Procurement Package must exist")

        orig_method = frappe.db.get_value("Procurement Package", pkg_name, "procurement_method")
        self.assertEqual(
            orig_method,
            "Open Tender",
            msg="WORKS master package must start as Open Tender for this smoke",
        )

        hc_name = frappe.db.get_value(
            "Procurement Handoff Card", {"handoff_code": _PKGREL_CODE}, "name"
        )
        self.assertIsNotNone(hc_name)

        try:
            frappe.db.set_value(
                "Procurement Package",
                pkg_name,
                "procurement_method",
                _ALT_METHOD,
                update_modified=True,
            )
            frappe.db.commit()

            result = validate_handoff_card_freshness(_PKGREL_CODE)
            self.assertFalse(
                result.get("fresh"),
                msg=f"Expected stale freshness after source drift; got {result!r}",
            )
            self.assertEqual(result.get("status"), "Stale")
            self.assertIsNotNone(result.get("stale_reason"))

            self.assertEqual(
                frappe.db.get_value("Procurement Package", pkg_name, "procurement_method"),
                _ALT_METHOD,
                msg="Source module must retain material change (handoff does not override).",
            )
            self.assertEqual(
                frappe.db.get_value("Procurement Handoff Card", hc_name, "status"),
                "Stale",
            )

            pkgrel_evt = next(
                (
                    e
                    for e in get_journey_evidence_timeline(JOURNEY_CODE)
                    if e.get("handoff_code") == _PKGREL_CODE
                ),
                None,
            )
            self.assertIsNotNone(pkgrel_evt, msg="PKGREL row must remain in lifecycle timeline")
            assert pkgrel_evt is not None
            self.assertTrue(pkgrel_evt.get("stale_warning"), msg=pkgrel_evt)
            self.assertTrue(str(pkgrel_evt.get("stale_reason") or "").strip())
        finally:
            frappe.db.set_value(
                "Procurement Package",
                pkg_name,
                "procurement_method",
                orig_method,
                update_modified=True,
            )
            frappe.db.set_value(
                "Procurement Handoff Card",
                hc_name,
                {"status": "Consumed", "stale_reason": None},
                update_modified=False,
            )
            frappe.db.commit()
