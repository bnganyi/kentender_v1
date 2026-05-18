# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tracker **§12 R7 — Evidence, audit, confidentiality integration** regression bundle.

Maps **R7 / LV-R7-*** acceptance to canonical tests executed in CI:

| Row | Automated evidence |
|---|---|
| **R7-001** | ``test_r3_015_evidence_timeline`` + ``get_journey_evidence_timeline`` (ordering / shape). |
| **R7-002** | This module — seeded base handoffs carry non-empty ``evidence_links`` where WORKS specifies. |
| **R7-003** | ``evidence_timeline`` merges ``TM2 Tender Audit Event`` rows (``.audit_event_code`` set); **PLC-SMOKE-BE-005** isolates lifecycle handoffs from audit lanes. |
| **R7-004** | ``test_r3_011_get_procurement_journey`` (**PUBSNAP** in PUBCERT ``evidence_refs``). |
| **R7-005** | ``test_r8_003`` timeline ``stale_warning`` + Desk ``plc-evidence-timeline-stale-warning`` (**Playwright** LV-R7-005-UI). |
| **R7-006** | ``test_r3_019_permission_filtering`` + ``list_journeys(scope='my-work')`` smoke in ``test_r3_017``. |
| **R7-007** | Python: ``test_r3_020`` / ``test_r8_015``; Desk: Playwright ``procurement_journey_supplier_denied_lv_r7_007.spec``. |
| **R7-008** | Tender evidence export façade import + deterministic denial smoke (delegates breadth to TM2 suites). |

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r7_evidence_audit_confidentiality

"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.evidence_timeline import (
    get_journey_evidence_timeline,
)
from kentender_procurement.procurement_lifecycle.journey_aggregate import (
    get_procurement_journey,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    BASE_HANDOFF_CODES,
    JOURNEY_CODE,
)


class TestR7HandoffEvidenceLinksLV002(IntegrationTestCase):
    """LV-R7-002-01 — WORKS seeded handoffs include evidence link objects."""

    def test_r7_lv_002_seed_base_handoffs_include_evidence_links(self) -> None:
        """Each ``BASE_HANDOFF_CODES`` summary row lists at least one evidence link."""
        result = get_procurement_journey(JOURNEY_CODE)
        cards = result.get("handoff_cards") or []
        codes = {c.get("handoff_code"): c for c in cards if c.get("handoff_code")}
        for hc in BASE_HANDOFF_CODES:
            row = codes.get(hc)
            self.assertIsNotNone(row, msg=f"Missing handoff card {hc}: {cards!r}")
            assert row is not None
            links = row.get("evidence_links") or []
            self.assertGreaterEqual(len(links), 1, msg=f"{hc}: expected ≥1 evidence link object")


class TestR7TimelineAuditPresenceLV003(IntegrationTestCase):
    """Smoke: audits (when seeded for WORKS TM2 tender) populate ``audit_event_code`` lanes."""

    def test_r7_lv_003_audit_lane_present_when_db_has_rows(self) -> None:
        timeline = get_journey_evidence_timeline(JOURNEY_CODE)
        audits = [
            e
            for e in timeline
            if str((e.get("audit_event_code") or "")).strip()
        ]
        if not frappe.db.count("TM2 Tender Audit Event", {"tender_code": "TND-MOH-2026-001"}):
            self.assertEqual(len(audits), 0, msg="Without audit rows timeline must omit audit lanes")
            return
        self.assertGreaterEqual(len(audits), 1, msg=f"Timeline must surface TM2 audits: {timeline}")


class TestR7EvidenceExportCompatibilityLV008(IntegrationTestCase):
    """LV-R7-008-01 — key export façade remains callable (full depth: ``test_p8_02_*``)."""

    def test_r7_lv_008_export_tender_evidence_module_smoke(self) -> None:
        from kentender_procurement.tender_management.services.export_tender_evidence import (
            export_tender_evidence,
        )

        out = export_tender_evidence(
            frappe.session.user,
            "TND-NONEXISTENT-R7-LV008",
            context={},
        )
        self.assertIn("ok", out)
        self.assertFalse(out.get("ok"), msg=out)
