# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-005 / LV-R8-BE-05 — PLC-SMOKE-BE-005: evidence timeline chronological + no fabrication.

Pack §15.1 / tracker §13:

    Evidence timeline returns base handoffs in chronological lifecycle order.
    Closing/opening readiness events appear only for OPENING_READY or where real
    source records exist.

Uses **R3-015** ``get_journey_evidence_timeline`` after the same PLC path as **R8-001**
(dependencies **LV-R3-015-01**, **LV-R7-001-01**).

For **TENDER_PUBLISHED**, seven ``BASE_HANDOFF_CODES`` handoff cards yield **seven**
timeline events (no ``CLOSECERT`` / ``OPENREADY`` rows; no ``Tender Addendum``-sourced
events unless real addendum records exist — **R3-015** TL-005/TL-006).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r8_005_plc_smoke_be_005_evidence_timeline_order

Companion evidence:
docs/prompts/0. usability handoff/R8_005_plc_smoke_be_005_evidence.md
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import (
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
from kentender_procurement.procurement_lifecycle.evidence_timeline import (
    get_journey_evidence_timeline,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

_REQUIRED_EVENT_KEYS = frozenset(
    {
        "occurred_at",
        "module",
        "event_type",
        "business_label",
        "object_type",
        "object_code",
        "handoff_code",
        "evidence_refs",
        "handoff_status",
        "stale_reason",
        "stale_warning",
        "audit_event_code",
    }
)


class TestR8005PlcSmokeBe005EvidenceTimelineOrder(IntegrationTestCase):
    """PLC-SMOKE-BE-005 — ordered timeline; base checkpoint omits opening/closing."""

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

    def test_plc_smoke_be_005_timeline_order_base_handoffs_only(self):
        """Chronological order; seven base codes; no closing/opening; no fabricated addenda."""
        load_out = load_procurement_lifecycle_works_master(
            reset=True,
            checkpoint="TENDER_PUBLISHED",
        )
        self.assertTrue(load_out.get("ok"), msg=f"PLC load failed: {load_out}")
        frappe.db.commit()

        for oc in OPENING_HANDOFF_CODES:
            self.assertFalse(
                frappe.db.exists("Procurement Handoff Card", oc),
                msg=f"Base checkpoint must not create {oc}",
            )

        timeline = get_journey_evidence_timeline(JOURNEY_CODE)

        stamps = [e["occurred_at"] for e in timeline]
        self.assertEqual(
            stamps,
            sorted(stamps),
            msg="Timeline must be ascending by occurred_at",
        )

        handoff_events = [e for e in timeline if e.get("handoff_code")]
        self.assertEqual(
            [e["handoff_code"] for e in handoff_events],
            list(BASE_HANDOFF_CODES),
            msg="Base lifecycle handoff order STRATREF → … → PUBCERT",
        )
        lifecycle_only = [e for e in timeline if not str(e.get("audit_event_code") or "").strip()]
        self.assertEqual(
            len(lifecycle_only),
            len(handoff_events),
            msg="Non-audit rows must mirror handoffs when no Tender Addendum records exist",
        )
        self.assertEqual(len(lifecycle_only), len(BASE_HANDOFF_CODES))

        addendum_events = [e for e in timeline if e.get("event_type") == "Addendum Issued"]
        self.assertEqual(len(addendum_events), 0, msg=addendum_events)

        for e in timeline:
            missing = _REQUIRED_EVENT_KEYS - set(e.keys())
            self.assertFalse(missing, msg=f"missing keys {missing} in {e!r}")
            hc = e.get("handoff_code") or ""
            self.assertFalse(
                hc.startswith("CLOSECERT-") or hc.startswith("OPENREADY-"),
                msg=f"Unexpected closing/opening handoff in base timeline: {e!r}",
            )

        self.assertEqual(handoff_events[0]["handoff_code"], BASE_HANDOFF_CODES[0])
        self.assertEqual(handoff_events[-1]["handoff_code"], BASE_HANDOFF_CODES[-1])
