# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Integration tests for R3-017 — Journey APIs (pack §10 / LV-R3-017-01, LV-R3-017-02).

## Coverage

| Test ID | Scenario | Expected outcome |
|---------|----------|-----------------|
| API-001 | list_journeys — shape (items + counts) | Required shape present |
| API-002 | list_journeys — WORKS journey appears in items | JRN-MOH-2026-001 in items |
| API-003 | list_journeys — item shape has all required fields | All pack §10.2 item fields present |
| API-004 | list_journeys — counts shape has all required keys | active/needs_action/blocked/ready_for_handoff/completed |
| API-005 | list_journeys status filter "active" — WORKS journey present | ≥1 active item |
| API-006 | list_journeys search filter matches title substring | hospital → WORKS journey |
| API-007 | list_journeys open_route matches pattern | `/desk/plc-procurement-journey/JRN-MOH-2026-001` (path segment; R4-005) |
| API-008 | get_journey — returns full aggregate for WORKS | journey_code, steps, handoff_cards |
| API-009 | get_journey — blank code raises ValidationError | frappe.ValidationError |
| API-010 | get_journey — unknown code raises DoesNotExistError | DoesNotExistError |
| API-011 | get_journey_by_object — TM2 Tender → WORKS aggregate | journey_code = JRN-MOH-2026-001 |
| API-012 | get_journey_by_object — unsupported type → None | None |
| API-013 | get_journey_steps — returns 12 ordered steps for WORKS | 12 steps in order |
| API-014 | get_journey_steps — blank code raises | frappe.ValidationError |
| API-015 | get_journey_evidence — returns ≥7 events for WORKS | ≥7 events, required keys present |
| API-016 | get_journey_evidence — blank code raises | frappe.ValidationError |
| API-018 | list_journeys(status='needs_action') — category | All "Needs Action" |
| API-019 | list_journeys(status='needs_action', scope='my-work') | Same category guard |
| API-020 | list_journeys(status='blocked') — open blockers | blocker or critical > 0 |
| API-021 | list_journeys(status='ready_for_handoff') — category | All "Ready for Handoff" |
| API-017 | list_journeys — my-work scope returns list (smoke, no error) | No exception |
| PERM-001 | Guest user cannot call list_journeys | frappe.PermissionError |
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.journey_api import (
    get_journey,
    get_journey_by_object,
    get_journey_evidence,
    get_journey_steps,
    list_journeys,
)

_WORKS_JOURNEY_CODE = "JRN-MOH-2026-001"
_WORKS_TENDER_CODE = "TND-MOH-2026-001"

# Required fields per pack §10.2 list item
_REQUIRED_ITEM_KEYS = {
    "journey_code",
    "journey_title",
    "procuring_entity_code",
    "current_stage_label",
    "current_status_category",
    "next_action",
    "blocker_count",
    "critical_blocker_count",
    "primary_object_code",
    "open_route",
}

# Required keys for the counts dict
_REQUIRED_COUNT_KEYS = {
    "active",
    "needs_action",
    "blocked",
    "ready_for_handoff",
    "completed",
}

# Required keys for evidence events
_REQUIRED_EVIDENCE_KEYS = {
    "occurred_at",
    "module",
    "event_type",
    "business_label",
    "object_type",
    "object_code",
    "handoff_code",
    "evidence_refs",
}


class TestR3017JourneyAPI(IntegrationTestCase):
    """R3-017 / LV-R3-017-01, LV-R3-017-02 — Journey API integration tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Pre-fetch to share across tests
        cls.list_result = list_journeys()

    # -----------------------------------------------------------------------
    # API-001  list_journeys — top-level shape
    # -----------------------------------------------------------------------

    def test_list_journeys_has_items_and_counts(self):
        """API-001: list_journeys returns dict with 'items' list and 'counts' dict."""
        result = self.list_result
        self.assertIsInstance(result, dict, msg=result)
        self.assertIn("items", result, msg=result)
        self.assertIn("counts", result, msg=result)
        self.assertIsInstance(result["items"], list, msg=result)
        self.assertIsInstance(result["counts"], dict, msg=result)

    # -----------------------------------------------------------------------
    # API-002  WORKS journey appears in list
    # -----------------------------------------------------------------------

    def test_works_journey_appears_in_list(self):
        """API-002: JRN-MOH-2026-001 is present in list_journeys items."""
        codes = [item["journey_code"] for item in self.list_result["items"]]
        self.assertIn(_WORKS_JOURNEY_CODE, codes, msg=f"Items: {codes}")

    # -----------------------------------------------------------------------
    # API-003  Item shape — required fields
    # -----------------------------------------------------------------------

    def test_item_shape_has_required_fields(self):
        """API-003: Each item has all required pack §10.2 fields."""
        for item in self.list_result["items"]:
            missing = _REQUIRED_ITEM_KEYS - set(item.keys())
            self.assertFalse(
                missing,
                msg=f"Item missing keys {missing}: {item}",
            )

    def test_works_item_values(self):
        """API-003b: WORKS item has correct core values."""
        works_item = next(
            (i for i in self.list_result["items"] if i["journey_code"] == _WORKS_JOURNEY_CODE),
            None,
        )
        self.assertIsNotNone(works_item, msg="WORKS journey not found in list")
        self.assertEqual(works_item["journey_title"], "District Hospital Renovation Works", msg=works_item)
        self.assertEqual(works_item["procuring_entity_code"], "PE-MOH", msg=works_item)
        self.assertEqual(works_item["current_stage_label"], "Tender Published", msg=works_item)
        self.assertEqual(works_item["primary_object_code"], _WORKS_TENDER_CODE, msg=works_item)
        self.assertEqual(
            works_item["open_route"],
            f"/desk/plc-procurement-journey/{_WORKS_JOURNEY_CODE}",
            msg=works_item,
        )

    # -----------------------------------------------------------------------
    # API-004  Counts shape
    # -----------------------------------------------------------------------

    def test_counts_has_required_keys(self):
        """API-004: counts dict has all required keys from pack §10.2."""
        counts = self.list_result["counts"]
        missing = _REQUIRED_COUNT_KEYS - set(counts.keys())
        self.assertFalse(missing, msg=f"Missing count keys: {missing}")
        for key in _REQUIRED_COUNT_KEYS:
            self.assertIsInstance(counts[key], int, msg=f"counts[{key}] not int: {counts}")

    def test_active_count_at_least_one(self):
        """API-004b: active count is ≥1 (WORKS journey is active)."""
        self.assertGreaterEqual(
            self.list_result["counts"]["active"],
            1,
            msg=f"Counts: {self.list_result['counts']}",
        )

    # -----------------------------------------------------------------------
    # API-005  Status filter "active"
    # -----------------------------------------------------------------------

    def test_status_filter_active_contains_works_journey(self):
        """API-005: list_journeys(status='active') contains WORKS journey."""
        result = list_journeys(status="active")
        codes = [i["journey_code"] for i in result["items"]]
        self.assertIn(_WORKS_JOURNEY_CODE, codes, msg=f"Active items: {codes}")

    # -----------------------------------------------------------------------
    # API-006  Search filter
    # -----------------------------------------------------------------------

    def test_search_filter_matches_title_substring(self):
        """API-006: list_journeys(search='hospital') returns WORKS journey."""
        result = list_journeys(search="hospital")
        codes = [i["journey_code"] for i in result["items"]]
        self.assertIn(_WORKS_JOURNEY_CODE, codes, msg=f"Search items: {codes}")

    def test_search_filter_no_match_returns_empty_or_subset(self):
        """API-006b: list_journeys(search='ZZZZ_NO_MATCH') returns no items."""
        result = list_journeys(search="ZZZZ_NO_MATCH_SENTINEL_STRING")
        self.assertEqual(len(result["items"]), 0, msg=result)

    # -----------------------------------------------------------------------
    # API-007  open_route pattern
    # -----------------------------------------------------------------------

    def test_open_route_matches_pattern(self):
        """API-007: open_route = '/desk/plc-procurement-journey/{journey_code}' (R4-005 path)."""
        works_item = next(
            (i for i in self.list_result["items"] if i["journey_code"] == _WORKS_JOURNEY_CODE),
            None,
        )
        self.assertIsNotNone(works_item)
        self.assertEqual(
            works_item["open_route"],
            f"/desk/plc-procurement-journey/{_WORKS_JOURNEY_CODE}",
            msg=works_item,
        )

    # -----------------------------------------------------------------------
    # API-008  get_journey
    # -----------------------------------------------------------------------

    def test_get_journey_returns_full_aggregate(self):
        """API-008: get_journey(JRN-MOH-2026-001) returns full aggregate."""
        result = get_journey(_WORKS_JOURNEY_CODE)
        self.assertEqual(result["journey_code"], _WORKS_JOURNEY_CODE, msg=result)
        self.assertIn("steps", result, msg=result)
        self.assertIn("handoff_cards", result, msg=result)
        self.assertIn("evidence_summary", result, msg=result)
        self.assertGreater(len(result["steps"]), 0, msg=result)

    # -----------------------------------------------------------------------
    # API-009  get_journey — blank code
    # -----------------------------------------------------------------------

    def test_get_journey_blank_code_raises(self):
        """API-009: get_journey('') raises ValidationError."""
        with self.assertRaises((frappe.ValidationError, ValueError)):
            get_journey("")

    # -----------------------------------------------------------------------
    # API-010  get_journey — unknown code
    # -----------------------------------------------------------------------

    def test_get_journey_unknown_code_raises(self):
        """API-010: get_journey(unknown) raises DoesNotExistError."""
        with self.assertRaises((frappe.DoesNotExistError, ValueError)):
            get_journey("JRN-DOES-NOT-EXIST-9999")

    # -----------------------------------------------------------------------
    # API-011  get_journey_by_object
    # -----------------------------------------------------------------------

    def test_get_journey_by_object_tm2_tender(self):
        """API-011: get_journey_by_object('TM2 Tender', TND-MOH-2026-001) → WORKS journey."""
        result = get_journey_by_object("TM2 Tender", _WORKS_TENDER_CODE)
        self.assertIsNotNone(result, msg="Expected a journey aggregate, got None")
        self.assertEqual(result["journey_code"], _WORKS_JOURNEY_CODE, msg=result)

    # -----------------------------------------------------------------------
    # API-012  get_journey_by_object — unsupported type
    # -----------------------------------------------------------------------

    def test_get_journey_by_object_unknown_object_returns_none(self):
        """API-012: Unsupported/unknown object type returns None (not an error)."""
        result = get_journey_by_object("Strategy Programme", "PROG-DOES-NOT-EXIST")
        self.assertIsNone(result)

    # -----------------------------------------------------------------------
    # API-013  get_journey_steps
    # -----------------------------------------------------------------------

    def test_get_journey_steps_returns_12_ordered_steps(self):
        """API-013: get_journey_steps(WORKS) returns 12 steps in step_order order."""
        steps = get_journey_steps(_WORKS_JOURNEY_CODE)
        self.assertEqual(len(steps), 12, msg=f"Expected 12 steps; got {len(steps)}")
        orders = [s["step_order"] for s in steps]
        self.assertEqual(orders, sorted(orders), msg=f"Steps not ordered: {orders}")

    # -----------------------------------------------------------------------
    # API-014  get_journey_steps — blank code
    # -----------------------------------------------------------------------

    def test_get_journey_steps_blank_code_raises(self):
        """API-014: get_journey_steps('') raises ValidationError."""
        with self.assertRaises((frappe.ValidationError, ValueError)):
            get_journey_steps("")

    # -----------------------------------------------------------------------
    # API-015  get_journey_evidence
    # -----------------------------------------------------------------------

    def test_get_journey_evidence_returns_events(self):
        """API-015: get_journey_evidence(WORKS) returns ≥7 events with required keys."""
        events = get_journey_evidence(_WORKS_JOURNEY_CODE)
        self.assertGreaterEqual(len(events), 7, msg=f"Expected ≥7 events; got {len(events)}")
        for ev in events:
            missing = _REQUIRED_EVIDENCE_KEYS - set(ev.keys())
            self.assertFalse(missing, msg=f"Event missing keys {missing}: {ev}")

    # -----------------------------------------------------------------------
    # API-016  get_journey_evidence — blank code
    # -----------------------------------------------------------------------

    def test_get_journey_evidence_blank_code_raises(self):
        """API-016: get_journey_evidence('') raises ValidationError."""
        with self.assertRaises((frappe.ValidationError, ValueError)):
            get_journey_evidence("")

    def test_status_filter_needs_action_items_are_needs_action_category(self):
        """API-018: list_journeys(status='needs_action') returns only Needs Action rows."""
        result = list_journeys(status="needs_action")
        self.assertIn("items", result)
        for item in result["items"]:
            self.assertEqual(item["current_status_category"], "Needs Action", msg=item)

    def test_status_filter_needs_action_my_work_scope_smoke(self):
        """API-019: list_journeys(status='needs_action', scope='my-work') filters consistently."""
        result = list_journeys(status="needs_action", scope="my-work")
        self.assertIn("items", result)
        for item in result["items"]:
            self.assertEqual(item["current_status_category"], "Needs Action", msg=item)

    def test_status_filter_blocked_items_have_open_blockers(self):
        """API-020: list_journeys(status='blocked') returns only rows with blockers."""
        result = list_journeys(status="blocked")
        self.assertIn("items", result)
        for item in result["items"]:
            bc = int(item.get("blocker_count") or 0)
            cc = int(item.get("critical_blocker_count") or 0)
            self.assertGreater(bc + cc, 0, msg=item)

    def test_status_filter_ready_for_handoff_items_are_ready_category(self):
        """API-021: list_journeys(status='ready_for_handoff') returns only Ready for Handoff rows."""
        result = list_journeys(status="ready_for_handoff")
        self.assertIn("items", result)
        for item in result["items"]:
            self.assertEqual(
                item["current_status_category"],
                "Ready for Handoff",
                msg=item,
            )

    # -----------------------------------------------------------------------
    # API-017  list_journeys my-work scope smoke
    # -----------------------------------------------------------------------

    def test_list_journeys_my_work_scope_no_error(self):
        """API-017: list_journeys(scope='my-work') completes without error."""
        result = list_journeys(scope="my-work")
        self.assertIn("items", result)
        self.assertIn("counts", result)

    # -----------------------------------------------------------------------
    # PERM-001  Guest session denied
    # -----------------------------------------------------------------------

    def test_guest_session_is_denied(self):
        """PERM-001: Calling list_journeys as Guest raises PermissionError."""
        original_user = frappe.session.user
        try:
            frappe.session.user = "Guest"
            with self.assertRaises(frappe.PermissionError):
                list_journeys()
        finally:
            frappe.session.user = original_user
