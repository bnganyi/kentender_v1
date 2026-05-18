# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Integration tests for R3-015 — evidence timeline service (cursor pack §9.5 / LV-R3-015-01).

## Coverage

| Test ID | Scenario | Expected outcome |
|---------|----------|-----------------|
| TL-001 | WORKS golden scenario — 7 events from 7 base handoff cards | ≥7 events, correct order |
| TL-002 | Event shape — required fields present on every event | All required keys present |
| TL-003 | PUBCERT event — occurred_at, event_type, evidence_refs | Matches spec §9.5 example |
| TL-004 | Chronological ordering — earliest event first | occurred_at ascending |
| TL-005 | No-fabrication rule — base checkpoint has no CLOSECERT/OPENREADY events | 0 closing events |
| TL-006 | No-fabrication rule — no addendum events when no Tender Addendum records exist | Addendum events = 0 for base |
| TL-007 | evidence_refs populated from handoff card evidence_links_json | PUBCERT refs include snapshot |
| TL-008 | Empty journey (no steps, no cards) → empty list (no error) | [] |
| ERR-001 | Blank journey_code → INVALID_JOURNEY_CODE | ValueError |
| ERR-002 | Unknown journey_code → JOURNEY_NOT_FOUND | DoesNotExistError |
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.evidence_timeline import (
    get_journey_evidence_timeline,
)

_WORKS_JOURNEY_CODE = "JRN-MOH-2026-001"

# Required fields on every event (pack §9.5)
_REQUIRED_EVENT_KEYS = {
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


class TestR3015EvidenceTimeline(IntegrationTestCase):
    """R3-015 / LV-R3-015-01 — evidence timeline service tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.timeline = get_journey_evidence_timeline(_WORKS_JOURNEY_CODE)

    # -----------------------------------------------------------------------
    # TL-001  WORKS golden scenario — at least 7 events
    # -----------------------------------------------------------------------

    def test_works_base_has_at_least_seven_events(self):
        """TL-001: Base WORKS seed has 7 handoff cards → at least 7 timeline events."""
        self.assertGreaterEqual(
            len(self.timeline),
            7,
            msg=f"Expected >= 7 events; got {len(self.timeline)}: {[e['handoff_code'] for e in self.timeline]}",
        )

    # -----------------------------------------------------------------------
    # TL-002  Event shape — required keys
    # -----------------------------------------------------------------------

    def test_every_event_has_required_keys(self):
        """TL-002: Every event dict contains all required pack §9.5 keys."""
        for i, event in enumerate(self.timeline):
            with self.subTest(i=i, event_type=event.get("event_type", "?")):
                missing = _REQUIRED_EVENT_KEYS - set(event.keys())
                self.assertFalse(
                    missing,
                    msg=f"Event {i} missing keys: {missing}. Event: {event}",
                )
                # evidence_refs must be a list
                self.assertIsInstance(event["evidence_refs"], list, msg=event)
                # occurred_at must be non-empty string
                self.assertIsInstance(event["occurred_at"], str, msg=event)
                self.assertTrue(event["occurred_at"], msg=f"Event {i} has empty occurred_at")

    # -----------------------------------------------------------------------
    # TL-003  PUBCERT event matches spec §9.5 example
    # -----------------------------------------------------------------------

    def test_pubcert_event_shape(self):
        """TL-003: PUBCERT event matches spec §9.5 example values."""
        pubcert = next(
            (e for e in self.timeline if e["handoff_code"] == "PUBCERT-TND-MOH-2026-001"),
            None,
        )
        self.assertIsNotNone(pubcert, msg="PUBCERT-TND-MOH-2026-001 not found in timeline")

        self.assertEqual(pubcert["event_type"], "Tender Published", msg=pubcert)
        self.assertEqual(pubcert["module"], "Tender Management", msg=pubcert)
        self.assertIn("Publication Certificate", pubcert["business_label"], msg=pubcert)
        self.assertEqual(pubcert["object_type"], "TM2 Tender", msg=pubcert)
        self.assertEqual(pubcert["object_code"], "TND-MOH-2026-001", msg=pubcert)
        # occurred_at should match the seed generated_at for PUBCERT: 2026-05-01T10:03:00
        self.assertTrue(
            pubcert["occurred_at"].startswith("2026-05-01"),
            msg=f"PUBCERT occurred_at expected to be on 2026-05-01; got {pubcert['occurred_at']}",
        )
        # evidence_refs includes the publication snapshot
        self.assertIn("PUBSNAP-TND-MOH-2026-001-V2", pubcert["evidence_refs"], msg=pubcert)

    # -----------------------------------------------------------------------
    # TL-004  Chronological ordering
    # -----------------------------------------------------------------------

    def test_events_ordered_chronologically(self):
        """TL-004: Events are returned in ascending occurred_at order."""
        timestamps = [e["occurred_at"] for e in self.timeline]
        self.assertEqual(
            timestamps,
            sorted(timestamps),
            msg=f"Events not in ascending order: {timestamps}",
        )

    def test_first_event_is_strategy(self):
        """TL-004b: STRATREF (earliest, 2026-01-15) is the first event."""
        first = self.timeline[0]
        self.assertEqual(
            first["handoff_code"],
            "STRATREF-MOH-2026-001",
            msg=f"Expected STRATREF first; got {first}",
        )
        self.assertTrue(
            first["occurred_at"].startswith("2026-01"),
            msg=first,
        )

    def test_last_handoff_event_is_pubcert(self):
        """TL-004c: PUBCERT (latest handoff, 2026-05-01) is the last handoff-sourced event."""
        handoff_events = [e for e in self.timeline if e["handoff_code"]]
        last_handoff = handoff_events[-1]
        self.assertEqual(
            last_handoff["handoff_code"],
            "PUBCERT-TND-MOH-2026-001",
            msg=f"Expected PUBCERT as last handoff event; got {last_handoff}",
        )

    # -----------------------------------------------------------------------
    # TL-005  No-fabrication — base has no closing/opening events
    # -----------------------------------------------------------------------

    def test_no_closing_opening_events_in_base_checkpoint(self):
        """TL-005: CLOSECERT and OPENREADY handoff codes absent from base timeline."""
        closing_events = [
            e for e in self.timeline
            if e.get("handoff_code") and (
                e["handoff_code"].startswith("CLOSECERT-")
                or e["handoff_code"].startswith("OPENREADY-")
            )
        ]
        self.assertEqual(
            len(closing_events),
            0,
            msg=f"Base timeline should have no closing/opening events; found: {closing_events}",
        )

    # -----------------------------------------------------------------------
    # TL-006  No addendum events in base (no real Tender Addendum for TND-MOH-2026-001)
    # -----------------------------------------------------------------------

    def test_no_addendum_events_when_no_addendum_records(self):
        """TL-006: No 'Addendum Issued' events when Tender Addendum records don't exist."""
        addendum_events = [
            e for e in self.timeline if e.get("event_type") == "Addendum Issued"
        ]
        # The base WORKS seed does not create a real Tender Addendum DocType record
        # (only references ADD-TND-MOH-2026-001-01 in PUBCERT evidence links).
        # Verify no fabricated addendum events appear.
        self.assertEqual(
            len(addendum_events),
            0,
            msg=f"Base should have 0 addendum events (no real Tender Addendum records); found: {addendum_events}",
        )

    # -----------------------------------------------------------------------
    # TL-007  evidence_refs populated from evidence_links_json
    # -----------------------------------------------------------------------

    def test_stratref_evidence_refs_contain_objective(self):
        """TL-007a: STRATREF evidence_refs contains the Strategy Objective code."""
        stratref = next(
            (e for e in self.timeline if e["handoff_code"] == "STRATREF-MOH-2026-001"),
            None,
        )
        self.assertIsNotNone(stratref)
        self.assertIn("OBJ-MOH-HOSP-RENOV", stratref["evidence_refs"], msg=stratref)

    def test_pkgrel_evidence_refs_contain_package_and_tender(self):
        """TL-007b: PKGREL evidence_refs contains both the Package and the Tender codes."""
        pkgrel = next(
            (e for e in self.timeline if e["handoff_code"] == "PKGREL-MOH-2026-001"),
            None,
        )
        self.assertIsNotNone(pkgrel)
        self.assertIn("PKG-MOH-2026-001", pkgrel["evidence_refs"], msg=pkgrel)
        self.assertIn("TND-MOH-2026-001", pkgrel["evidence_refs"], msg=pkgrel)

    # -----------------------------------------------------------------------
    # TL-008  Empty journey (no handoff cards) → empty list
    # -----------------------------------------------------------------------

    def test_journey_with_no_cards_returns_empty_list(self):
        """TL-008: A journey with no handoff cards returns [] without error."""
        # The WORKS journey always has cards, so we use an approach where we
        # verify the function handles an empty card set gracefully by looking at
        # a fresh (non-existent in DB) isolated test — use WORKS journey and
        # verify it returns a list (not an error) which already covers the code path.
        # We test the actual empty-list path via a freshly inserted bare-minimum journey.

        bare_code = "JRN-TEST-R3015-EMPTY-001"
        if not frappe.db.exists("Procurement Journey", bare_code):
            frappe.get_doc(
                {
                    "doctype": "Procurement Journey",
                    "name": bare_code,
                    "journey_code": bare_code,
                    "journey_title": "R3-015 Empty Test Journey",
                    "procuring_entity_code": "PE-MOH",
                    "procurement_category": "Works",
                    "procurement_method": "Open Tender",
                    "fiscal_year": "2026/2027",
                    "current_stage_key": "strategy",
                    "current_stage_label": "Strategy Priority",
                    "current_status_category": "Not Started",
                    "current_owner_module": "Strategy",
                    "blocker_count": 0,
                    "critical_blocker_count": 0,
                    "is_master_seed": 0,
                }
            ).insert(ignore_permissions=True)

        try:
            result = get_journey_evidence_timeline(bare_code)
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 0)
        finally:
            if frappe.db.exists("Procurement Journey", bare_code):
                frappe.delete_doc("Procurement Journey", bare_code, force=True)

    # -----------------------------------------------------------------------
    # ERR-001  Blank journey_code
    # -----------------------------------------------------------------------

    def test_blank_journey_code_raises(self):
        """ERR-001: Blank or whitespace journey_code → INVALID_JOURNEY_CODE ValueError."""
        for bad in ("", "   ", None):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError, TypeError)):
                    get_journey_evidence_timeline(bad)  # type: ignore[arg-type]

    # -----------------------------------------------------------------------
    # ERR-002  Unknown journey_code
    # -----------------------------------------------------------------------

    def test_unknown_journey_code_raises(self):
        """ERR-002: Unknown journey code → DoesNotExistError (JOURNEY_NOT_FOUND)."""
        with self.assertRaises((frappe.DoesNotExistError, ValueError)):
            get_journey_evidence_timeline("JRN-DOES-NOT-EXIST-9999")
