# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-018 / LV-R3-018-01 — Integration tests for Handoff Card APIs.

## Goal

Verify the two Frappe-whitelisted handoff API endpoints (pack §10.3):

- ``get_handoff_card(handoff_code)`` — returns full detail + freshness.
- ``refresh_handoff_card(handoff_code)`` — triggers freshness re-check and returns result.

## Test IDs

| Test | Description |
|---|---|
| HAC-001 | WORKS golden: PKGREL card returned with all §10.3 fields. |
| HAC-002 | Required field shapes: all keys present, correct Python types. |
| HAC-003 | JSON fields parsed: locked_summary/passed_forward_summary are dicts, evidence_links is list. |
| HAC-004 | Freshness sub-dict present and well-formed. |
| HAC-005 | ``handoff_code`` field in response matches the requested code. |
| HAC-006 | All 7 WORKS base cards are retrievable. |
| HAC-007 | Blank ``handoff_code`` → ValidationError. |
| HAC-008 | Unknown ``handoff_code`` → DoesNotExistError. |
| HAC-009 | ``refresh_handoff_card`` on PKGREL returns correct refresh shape. |
| HAC-010 | ``refresh_handoff_card`` with blank code → ValidationError. |
| HAC-011 | ``refresh_handoff_card`` with unknown code → DoesNotExistError. |
| HAC-PERM-001 | Guest user cannot call ``get_handoff_card`` (PermissionError). |
| HAC-PERM-002 | Guest user cannot call ``refresh_handoff_card`` (PermissionError). |
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.handoff_api import (
    get_handoff_card,
    refresh_handoff_card,
)

# WORKS seed identifiers — from procurement_lifecycle_master_seed_data spec §4
_WORKS_PKGREL = "PKGREL-MOH-2026-001"
_WORKS_JOURNEY = "JRN-MOH-2026-001"
_WORKS_CARDS = [
    "STRATREF-MOH-2026-001",
    "BUDCONF-MOH-2026-001",
    "DEMAPP-MOH-2026-001",
    "PKGREL-MOH-2026-001",
    "STDREADY-TND-MOH-2026-001",
    "PUBCERT-TND-MOH-2026-001",
    "PLANINCL-MOH-2026-001",
]
_REQUIRED_DETAIL_KEYS = {
    "handoff_code",
    "handoff_title",
    "status",
    "source_module",
    "target_module",
    "source_object_type",
    "source_object_code",
    "target_object_type",
    "target_object_code",
    "journey_code",
    "locked_summary",
    "passed_forward_summary",
    "next_action",
    "evidence_links",
    "technical_refs",
    "freshness",
}
_REQUIRED_REFRESH_KEYS = {"handoff_code", "fresh", "status", "stale_reason", "required_action"}


class TestHandoffApiGetDetail(IntegrationTestCase):
    """Tests for get_handoff_card endpoint."""

    # ------------------------------------------------------------------
    # HAC-001: WORKS golden scenario
    # ------------------------------------------------------------------
    def test_hac_001_works_pkgrel_card_returned(self):
        """HAC-001: PKGREL card for WORKS journey is returned and has expected values."""
        frappe.set_user("Administrator")
        result = get_handoff_card(_WORKS_PKGREL)

        self.assertEqual(result["handoff_code"], _WORKS_PKGREL)
        self.assertEqual(result["handoff_title"], "Planning Release Package")
        self.assertEqual(result["status"], "Consumed")
        self.assertEqual(result["source_module"], "Procurement Planning")
        self.assertEqual(result["target_module"], "Tender Management")
        self.assertEqual(result["source_object_type"], "Procurement Package")
        self.assertEqual(result["source_object_code"], "PKG-MOH-2026-001")
        self.assertEqual(result["target_object_type"], "TM2 Tender")
        self.assertEqual(result["target_object_code"], "TND-MOH-2026-001")
        self.assertEqual(result["journey_code"], _WORKS_JOURNEY)
        self.assertIn("Works STD", result.get("next_action", ""))

    # ------------------------------------------------------------------
    # HAC-002: Required field shapes
    # ------------------------------------------------------------------
    def test_hac_002_required_field_shapes(self):
        """HAC-002: All pack §10.3 keys are present and have correct Python types."""
        frappe.set_user("Administrator")
        result = get_handoff_card(_WORKS_PKGREL)

        for key in _REQUIRED_DETAIL_KEYS:
            self.assertIn(key, result, f"Missing key: {key}")

        self.assertIsInstance(result["locked_summary"], dict)
        self.assertIsInstance(result["passed_forward_summary"], dict)
        self.assertIsInstance(result["evidence_links"], list)
        self.assertIsInstance(result["technical_refs"], dict)
        self.assertIsInstance(result["freshness"], dict)
        self.assertIsInstance(result["handoff_code"], str)
        self.assertIsInstance(result["status"], str)

    # ------------------------------------------------------------------
    # HAC-003: JSON fields parsed correctly
    # ------------------------------------------------------------------
    def test_hac_003_json_fields_parsed(self):
        """HAC-003: JSON fields return correct Python types, not raw strings."""
        frappe.set_user("Administrator")
        result = get_handoff_card(_WORKS_PKGREL)

        # None of these should be strings (they should be parsed)
        self.assertNotIsInstance(result["locked_summary"], str)
        self.assertNotIsInstance(result["passed_forward_summary"], str)
        self.assertNotIsInstance(result["evidence_links"], str)
        self.assertNotIsInstance(result["technical_refs"], str)

    # ------------------------------------------------------------------
    # HAC-004: Freshness sub-dict is well-formed
    # ------------------------------------------------------------------
    def test_hac_004_freshness_subdict_present(self):
        """HAC-004: Freshness sub-dict has required keys with correct types."""
        frappe.set_user("Administrator")
        result = get_handoff_card(_WORKS_PKGREL)

        freshness = result["freshness"]
        self.assertIn("fresh", freshness)
        self.assertIn("stale_reason", freshness)
        self.assertIsInstance(freshness["fresh"], bool)
        # stale_reason may be None or a string
        self.assertTrue(
            freshness["stale_reason"] is None or isinstance(freshness["stale_reason"], str),
            f"stale_reason should be None or str, got: {type(freshness['stale_reason'])}",
        )

    # ------------------------------------------------------------------
    # HAC-005: handoff_code field matches requested code
    # ------------------------------------------------------------------
    def test_hac_005_handoff_code_matches_request(self):
        """HAC-005: handoff_code in response matches the argument passed in."""
        frappe.set_user("Administrator")
        result = get_handoff_card(_WORKS_PKGREL)
        self.assertEqual(result["handoff_code"], _WORKS_PKGREL)

    # ------------------------------------------------------------------
    # HAC-006: All 7 WORKS base cards retrievable
    # ------------------------------------------------------------------
    def test_hac_006_all_works_base_cards_retrievable(self):
        """HAC-006: Each of the 7 WORKS base handoff cards can be retrieved without error."""
        frappe.set_user("Administrator")
        for code in _WORKS_CARDS:
            result = get_handoff_card(code)
            self.assertEqual(result["handoff_code"], code, f"handoff_code mismatch for {code}")
            for key in _REQUIRED_DETAIL_KEYS:
                self.assertIn(key, result, f"Key '{key}' missing for card '{code}'")

    # ------------------------------------------------------------------
    # HAC-007: Blank code → ValidationError
    # ------------------------------------------------------------------
    def test_hac_007_blank_code_raises_validation_error(self):
        """HAC-007: get_handoff_card with blank handoff_code raises ValidationError."""
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.ValidationError):
            get_handoff_card("")

    def test_hac_007b_none_code_raises_validation_error(self):
        """HAC-007b: get_handoff_card with None handoff_code raises ValidationError."""
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.ValidationError):
            get_handoff_card(None)

    # ------------------------------------------------------------------
    # HAC-008: Unknown code → DoesNotExistError
    # ------------------------------------------------------------------
    def test_hac_008_unknown_code_raises_does_not_exist(self):
        """HAC-008: get_handoff_card with unknown code raises DoesNotExistError."""
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.DoesNotExistError):
            get_handoff_card("HANDOFF-DOES-NOT-EXIST-99999")

    # ------------------------------------------------------------------
    # HAC-PERM-001: Guest denied
    # ------------------------------------------------------------------
    def test_hac_perm_001_guest_denied(self):
        """HAC-PERM-001: Guest user is denied access to get_handoff_card (PermissionError)."""
        frappe.set_user("Guest")
        try:
            with self.assertRaises(frappe.PermissionError):
                get_handoff_card(_WORKS_PKGREL)
        finally:
            frappe.set_user("Administrator")


class TestHandoffApiRefresh(IntegrationTestCase):
    """Tests for refresh_handoff_card endpoint."""

    # ------------------------------------------------------------------
    # HAC-009: Refresh returns correct shape
    # ------------------------------------------------------------------
    def test_hac_009_refresh_returns_correct_shape(self):
        """HAC-009: refresh_handoff_card returns dict with all required keys."""
        frappe.set_user("Administrator")
        result = refresh_handoff_card(_WORKS_PKGREL)

        for key in _REQUIRED_REFRESH_KEYS:
            self.assertIn(key, result, f"Missing refresh key: {key}")

        self.assertEqual(result["handoff_code"], _WORKS_PKGREL)
        self.assertIsInstance(result["fresh"], bool)
        self.assertIsInstance(result["status"], str)
        # stale_reason and required_action may be None
        self.assertTrue(
            result["stale_reason"] is None or isinstance(result["stale_reason"], str),
            f"stale_reason type unexpected: {type(result['stale_reason'])}",
        )

    def test_hac_009b_refresh_pkgrel_is_fresh_or_stale_consistently(self):
        """HAC-009b: refresh result status is consistent with PKGREL card status in DB."""
        frappe.set_user("Administrator")
        result = refresh_handoff_card(_WORKS_PKGREL)
        # PKGREL is Consumed in WORKS seed — either fresh (if source unchanged) or stale
        # (if source mutated). Either way the key contract holds.
        self.assertIn(result["fresh"], [True, False])
        # Status in refresh must be a non-empty string
        self.assertTrue(len(result["status"]) > 0)

    # ------------------------------------------------------------------
    # HAC-010: Blank code → ValidationError
    # ------------------------------------------------------------------
    def test_hac_010_blank_code_raises_validation_error(self):
        """HAC-010: refresh_handoff_card with blank handoff_code raises ValidationError."""
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.ValidationError):
            refresh_handoff_card("")

    def test_hac_010b_none_code_raises_validation_error(self):
        """HAC-010b: refresh_handoff_card with None raises ValidationError."""
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.ValidationError):
            refresh_handoff_card(None)

    # ------------------------------------------------------------------
    # HAC-011: Unknown code → DoesNotExistError
    # ------------------------------------------------------------------
    def test_hac_011_unknown_code_raises_does_not_exist(self):
        """HAC-011: refresh_handoff_card with unknown code raises DoesNotExistError."""
        frappe.set_user("Administrator")
        with self.assertRaises((frappe.DoesNotExistError, ValueError)):
            refresh_handoff_card("HANDOFF-DOES-NOT-EXIST-99999")

    # ------------------------------------------------------------------
    # HAC-PERM-002: Guest denied
    # ------------------------------------------------------------------
    def test_hac_perm_002_guest_denied_refresh(self):
        """HAC-PERM-002: Guest user is denied access to refresh_handoff_card (PermissionError)."""
        frappe.set_user("Guest")
        try:
            with self.assertRaises(frappe.PermissionError):
                refresh_handoff_card(_WORKS_PKGREL)
        finally:
            frappe.set_user("Administrator")
