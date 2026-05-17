# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Integration tests for R3-016 — business readiness summary service (cursor pack §13 / LV-R3-016-01).

## Coverage

| Test ID | Scenario | Expected outcome |
|---------|----------|-----------------|
| BRS-001 | WORKS golden scenario — TND-MOH-2026-001 (all 5 codes present) | status=Ready, 5 PASS checks |
| BRS-002 | Response shape — required keys present | object_type, object_code, summary_label, status, checks, snapshot_ref, technical_details_available |
| BRS-003 | 5 check labels match spec business labels exactly | All 5 business_label values correct |
| BRS-004 | 5 technical labels match Bundle/DSM/DOM/DEM/DCM | All 5 technical_label values correct |
| BRS-005 | 6 lines incl. snapshot — snapshot_ref present | snapshot_ref = PUBSNAP-TND-MOH-2026-001-V2 |
| BRS-006 | technical_refs match spec values (GB/DSM/DOM/DEM/DCM-TND-MOH-2026-001-V2) | All 5 technical_ref values match |
| BRS-007 | technical_details_available = True for WORKS | True when all checks PASS |
| BRS-008 | Blocked scenario — DEM code removed → FAIL on DEM check | status=Blocked, DEM result=FAIL, blocker_code=DEM_MISSING_OR_STALE |
| BRS-009 | Not Assessed scenario — no handoff card exists | status=Not Assessed, all FAIL |
| BRS-010 | is_object_type_supported helper | True for TM2 Tender, False for others |
| ERR-001 | Blank object_type → INVALID_OBJECT_TYPE | ValueError |
| ERR-002 | Blank object_code → INVALID_OBJECT_CODE | ValueError |
| ERR-003 | Unsupported object_type → UNSUPPORTED_OBJECT_TYPE | ValueError |
| ERR-004 | Unknown tender code → OBJECT_NOT_FOUND | DoesNotExistError |
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.business_readiness_summary import (
    get_business_readiness_summary,
    is_object_type_supported,
)

_WORKS_TENDER_CODE = "TND-MOH-2026-001"

# Expected tech ref codes from spec §13 / tracker §R6 Required Technical References
_EXPECTED_TECH_REFS = {
    "Bundle": "GB-TND-MOH-2026-001-V2",
    "DSM": "DSM-TND-MOH-2026-001-V2",
    "DOM": "DOM-TND-MOH-2026-001-V2",
    "DEM": "DEM-TND-MOH-2026-001-V2",
    "DCM": "DCM-TND-MOH-2026-001-V2",
}

# Expected business labels from spec §13
_EXPECTED_BUSINESS_LABELS = [
    "Tender document package ready",
    "Supplier submission checklist ready",
    "Opening register rules ready",
    "Evaluation rules ready",
    "Contract carry-forward terms ready",
]

# Expected technical labels (order matters)
_EXPECTED_TECH_LABELS = ["Bundle", "DSM", "DOM", "DEM", "DCM"]

# Required top-level keys
_REQUIRED_KEYS = {
    "object_type",
    "object_code",
    "summary_label",
    "status",
    "checks",
    "snapshot_ref",
    "technical_details_available",
}

# Required per-check keys for PASS checks
_PASS_CHECK_KEYS = {"business_label", "technical_label", "technical_ref", "result"}

# Required per-check keys for FAIL checks
_FAIL_CHECK_KEYS = {
    "business_label",
    "technical_label",
    "technical_ref",
    "result",
    "blocker_code",
    "owner_module",
    "required_action",
}


class TestR3016BusinessReadinessSummary(IntegrationTestCase):
    """R3-016 / LV-R3-016-01 — business readiness summary tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.result = get_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)

    # -----------------------------------------------------------------------
    # BRS-001  WORKS golden scenario — all 5 PASS, status=Ready
    # -----------------------------------------------------------------------

    def test_works_golden_scenario_status_ready(self):
        """BRS-001: WORKS tender → status=Ready, all 5 checks PASS."""
        self.assertEqual(self.result["status"], "Ready", msg=self.result)
        self.assertEqual(len(self.result["checks"]), 5, msg=self.result)
        for check in self.result["checks"]:
            self.assertEqual(check["result"], "PASS", msg=check)

    # -----------------------------------------------------------------------
    # BRS-002  Response shape
    # -----------------------------------------------------------------------

    def test_response_shape_has_required_keys(self):
        """BRS-002: All required top-level keys present."""
        missing = _REQUIRED_KEYS - set(self.result.keys())
        self.assertFalse(missing, msg=f"Missing keys: {missing}. Result: {self.result}")
        self.assertEqual(self.result["object_type"], "TM2 Tender", msg=self.result)
        self.assertEqual(self.result["object_code"], _WORKS_TENDER_CODE, msg=self.result)
        self.assertEqual(self.result["summary_label"], "Tender document readiness", msg=self.result)
        self.assertIsInstance(self.result["checks"], list, msg=self.result)

    # -----------------------------------------------------------------------
    # BRS-003  Business labels match spec exactly
    # -----------------------------------------------------------------------

    def test_five_business_labels_match_spec(self):
        """BRS-003: All 5 business_label values match spec §13 exactly (PLC-SMOKE-BE-004)."""
        actual_labels = [c["business_label"] for c in self.result["checks"]]
        self.assertEqual(actual_labels, _EXPECTED_BUSINESS_LABELS, msg=self.result)

    # -----------------------------------------------------------------------
    # BRS-004  Technical labels = Bundle/DSM/DOM/DEM/DCM
    # -----------------------------------------------------------------------

    def test_five_technical_labels_correct(self):
        """BRS-004: technical_label values are Bundle, DSM, DOM, DEM, DCM in order."""
        actual_labels = [c["technical_label"] for c in self.result["checks"]]
        self.assertEqual(actual_labels, _EXPECTED_TECH_LABELS, msg=self.result)

    # -----------------------------------------------------------------------
    # BRS-005  Snapshot ref present (6th line)
    # -----------------------------------------------------------------------

    def test_snapshot_ref_present(self):
        """BRS-005: snapshot_ref contains PUBSNAP-TND-MOH-2026-001-V2 (6th line per LV-R3-016-01)."""
        self.assertEqual(
            self.result["snapshot_ref"],
            "PUBSNAP-TND-MOH-2026-001-V2",
            msg=self.result,
        )

    # -----------------------------------------------------------------------
    # BRS-006  Technical refs match spec
    # -----------------------------------------------------------------------

    def test_technical_refs_match_spec_values(self):
        """BRS-006: Each PASS check's technical_ref matches expected spec value."""
        by_label = {c["technical_label"]: c for c in self.result["checks"]}
        for tech_label, expected_ref in _EXPECTED_TECH_REFS.items():
            with self.subTest(tech_label=tech_label):
                check = by_label.get(tech_label)
                self.assertIsNotNone(check, msg=f"{tech_label} check missing")
                self.assertEqual(check["technical_ref"], expected_ref, msg=check)

    # -----------------------------------------------------------------------
    # BRS-007  technical_details_available = True
    # -----------------------------------------------------------------------

    def test_technical_details_available_true_when_all_pass(self):
        """BRS-007: technical_details_available=True when all 5 checks PASS."""
        self.assertTrue(self.result["technical_details_available"], msg=self.result)

    # -----------------------------------------------------------------------
    # BRS-008  Blocked scenario — patch PUBCERT to remove DEM code
    # -----------------------------------------------------------------------

    def test_blocked_when_dem_code_missing(self):
        """BRS-008: If DEM code is absent → DEM check FAIL, status=Blocked, correct blocker_code."""
        pubcert_code = f"PUBCERT-{_WORKS_TENDER_CODE}"

        # Save original technical_refs_json
        original = frappe.db.get_value(
            "Procurement Handoff Card", pubcert_code, "technical_refs_json"
        )
        original_refs = json.loads(original) if original else {}

        # Patch: remove dem_output_code
        patched_refs = {k: v for k, v in original_refs.items() if k != "dem_output_code"}
        frappe.db.set_value(
            "Procurement Handoff Card",
            pubcert_code,
            "technical_refs_json",
            json.dumps(patched_refs),
            update_modified=False,
        )
        frappe.db.commit()

        try:
            result = get_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)
            self.assertEqual(result["status"], "Blocked", msg=result)
            by_label = {c["technical_label"]: c for c in result["checks"]}
            dem_check = by_label.get("DEM")
            self.assertIsNotNone(dem_check, msg="DEM check missing")
            self.assertEqual(dem_check["result"], "FAIL", msg=dem_check)
            self.assertIsNone(dem_check["technical_ref"], msg=dem_check)
            self.assertEqual(dem_check["blocker_code"], "DEM_MISSING_OR_STALE", msg=dem_check)
            self.assertEqual(dem_check["owner_module"], "STD Engine", msg=dem_check)
            self.assertIn("required_action", dem_check, msg=dem_check)
            ubm = dem_check.get("user_blocker_message")
            self.assertIsInstance(ubm, str, msg=dem_check)
            self.assertGreater(len(ubm.strip()), 10, msg=dem_check)
            self.assertNotIn("DEM_MISSING_OR_STALE", ubm, msg=dem_check)
            self.assertIn("Evaluation", ubm, msg=dem_check)
            # Other checks still PASS
            for tech in ("Bundle", "DSM", "DOM", "DCM"):
                self.assertEqual(by_label[tech]["result"], "PASS", msg=by_label[tech])
        finally:
            # Restore
            frappe.db.set_value(
                "Procurement Handoff Card",
                pubcert_code,
                "technical_refs_json",
                original,
                update_modified=False,
            )
            frappe.db.commit()

    # -----------------------------------------------------------------------
    # BRS-009  Not Assessed scenario — no handoff card
    # -----------------------------------------------------------------------

    def test_not_assessed_when_no_handoff_card(self):
        """BRS-009: If no PUBCERT or STDREADY card exists → status=Not Assessed, all FAIL."""
        # Create a dummy TM2 Tender (no handoff cards)
        dummy_tender_code = "TND-TEST-R3016-NOCARD-001"

        if not frappe.db.exists("TM2 Tender", {"tender_code": dummy_tender_code}):
            frappe.db.sql(
                """INSERT INTO `tabTM2 Tender`
                   (name, tender_code, status, docstatus, idx, is_active,
                    planning_handoff_source_demand_count,
                    planning_handoff_source_budget_line_count,
                    estimated_value_internal)
                   VALUES (%s, %s, 'Draft', 0, 0, 1, 0, 0, 0)
                """,
                (dummy_tender_code, dummy_tender_code),
            )
            frappe.db.commit()

        try:
            result = get_business_readiness_summary("TM2 Tender", dummy_tender_code)
            self.assertEqual(result["status"], "Not Assessed", msg=result)
            self.assertEqual(len(result["checks"]), 5, msg=result)
            for check in result["checks"]:
                self.assertEqual(check["result"], "FAIL", msg=check)
                self.assertIsNone(check["technical_ref"], msg=check)
                self.assertIn("blocker_code", check, msg=check)
            self.assertFalse(result["technical_details_available"], msg=result)
        finally:
            frappe.db.sql(
                "DELETE FROM `tabTM2 Tender` WHERE name=%s", (dummy_tender_code,)
            )
            frappe.db.commit()

    # -----------------------------------------------------------------------
    # BRS-010  is_object_type_supported helper
    # -----------------------------------------------------------------------

    def test_is_object_type_supported(self):
        """BRS-010: TM2 Tender is supported; other types are not."""
        self.assertTrue(is_object_type_supported("TM2 Tender"))
        self.assertFalse(is_object_type_supported("Procurement Package"))
        self.assertFalse(is_object_type_supported("Demand"))
        self.assertFalse(is_object_type_supported(""))
        self.assertFalse(is_object_type_supported(None))  # type: ignore[arg-type]

    # -----------------------------------------------------------------------
    # ERR-001  Blank object_type
    # -----------------------------------------------------------------------

    def test_blank_object_type_raises(self):
        """ERR-001: Blank or None object_type → INVALID_OBJECT_TYPE ValueError."""
        for bad in ("", "   ", None):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError, TypeError)):
                    get_business_readiness_summary(bad, _WORKS_TENDER_CODE)  # type: ignore

    # -----------------------------------------------------------------------
    # ERR-002  Blank object_code
    # -----------------------------------------------------------------------

    def test_blank_object_code_raises(self):
        """ERR-002: Blank or None object_code → INVALID_OBJECT_CODE ValueError."""
        for bad in ("", "   ", None):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError, TypeError)):
                    get_business_readiness_summary("TM2 Tender", bad)  # type: ignore

    # -----------------------------------------------------------------------
    # ERR-003  Unsupported object_type
    # -----------------------------------------------------------------------

    def test_unsupported_object_type_raises(self):
        """ERR-003: Unsupported object_type → UNSUPPORTED_OBJECT_TYPE ValueError."""
        with self.assertRaises(ValueError) as ctx:
            get_business_readiness_summary("Demand", "DEM-MOH-2026-001")
        self.assertIn("UNSUPPORTED_OBJECT_TYPE", str(ctx.exception))

    # -----------------------------------------------------------------------
    # ERR-004  Unknown tender code
    # -----------------------------------------------------------------------

    def test_unknown_tender_code_raises(self):
        """ERR-004: Unknown tender code → OBJECT_NOT_FOUND DoesNotExistError."""
        with self.assertRaises((frappe.DoesNotExistError, ValueError)):
            get_business_readiness_summary("TM2 Tender", "TND-DOES-NOT-EXIST-9999")
