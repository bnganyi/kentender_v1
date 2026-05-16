# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Integration tests for R3-014 — current stage calculation (cursor pack §9.4 / LV-R3-014-01).

## Coverage

| Test ID | Scenario | Expected outcome |
|---------|----------|-----------------|
| STAGE-001 | WORKS golden scenario (base checkpoint TENDER_PUBLISHED) | current_stage="Tender Published", current_status="Completed", next_action contains "tender closing" |
| STAGE-002 | Pure function — all steps Not Started → first step | current_stage = first step label |
| STAGE-003 | Pure function — single Blocked step → blocker returned | is_blocked=True, current_stage = blocked step |
| STAGE-004 | Pure function — mixed active steps → highest step_order wins | step 7 over step 5 |
| STAGE-005 | Pure function — Handed Off step counted as active | Handed Off step becomes current |
| STAGE-006 | Pure function — next_action falls back to next step when current step has no next_action | correct fallback |
| STAGE-007 | Pure function — empty step list | safe empty response |
| STAGE-008 | update_journey_current_stage — persists values to DB | DB fields updated |
| ERR-001 | Blank journey_code → INVALID_JOURNEY_CODE | ValueError |
| ERR-002 | Unknown journey_code → JOURNEY_NOT_FOUND | DoesNotExistError or ValueError |
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.current_stage_calculator import (
    calculate_current_stage_from_steps,
    calculate_journey_current_stage,
    update_journey_current_stage,
)

_WORKS_JOURNEY_CODE = "JRN-MOH-2026-001"


def _make_step(
    step_key: str,
    label: str,
    step_order: int,
    status_category: str,
    next_action: str = "",
) -> dict:
    return {
        "step_key": step_key,
        "label": label,
        "step_order": step_order,
        "status_category": status_category,
        "next_action": next_action,
    }


class TestR3014CurrentStageCalculator(IntegrationTestCase):
    """R3-014 / LV-R3-014-01 — current stage calculation tests."""

    # -----------------------------------------------------------------------
    # STAGE-001  WORKS golden scenario
    # -----------------------------------------------------------------------

    def test_works_golden_scenario(self):
        """STAGE-001: WORKS master at base checkpoint → expected stage from pack §9.4."""
        result = calculate_journey_current_stage(_WORKS_JOURNEY_CODE)

        # Spec §9.4: "Tender Published" / "Completed"
        self.assertEqual(result["current_stage"], "Tender Published", msg=result)
        self.assertEqual(result["current_stage_key"], "tender_publication", msg=result)
        self.assertEqual(result["current_status"], "Completed", msg=result)
        self.assertFalse(result["is_blocked"], msg=result)
        self.assertIsNone(result["blocked_step_key"], msg=result)

        # next_action should reference tender closing (step 7 stores "Await tender closing")
        next_action = result["next_action"]
        self.assertIsInstance(next_action, str, msg=result)
        self.assertIn("tender closing", next_action.lower(), msg=result)

    # -----------------------------------------------------------------------
    # STAGE-002  Pure function — all steps Not Started
    # -----------------------------------------------------------------------

    def test_pure_all_not_started_returns_first_step(self):
        """STAGE-002: All steps Not Started → first step is current stage."""
        steps = [
            _make_step("strategy", "Strategic Priority", 1, "Not Started", "Align strategy"),
            _make_step("budget", "Funding Available", 2, "Not Started", "Confirm budget"),
        ]
        result = calculate_current_stage_from_steps(steps)

        self.assertEqual(result["current_stage"], "Strategic Priority")
        self.assertEqual(result["current_stage_key"], "strategy")
        self.assertEqual(result["current_status"], "Not Started")
        self.assertFalse(result["is_blocked"])
        self.assertIsNone(result["blocked_step_key"])

    # -----------------------------------------------------------------------
    # STAGE-003  Pure function — blocked step
    # -----------------------------------------------------------------------

    def test_pure_blocked_step_is_prioritised(self):
        """STAGE-003: First blocked step wins regardless of other active steps."""
        steps = [
            _make_step("strategy", "Strategic Priority", 1, "Completed"),
            _make_step("budget", "Funding Available", 2, "Blocked", "Resolve budget block"),
            _make_step("demand", "Need Approved", 3, "Completed"),
        ]
        result = calculate_current_stage_from_steps(steps)

        self.assertEqual(result["current_stage"], "Funding Available")
        self.assertEqual(result["current_stage_key"], "budget")
        self.assertEqual(result["current_status"], "Blocked")
        self.assertTrue(result["is_blocked"])
        self.assertEqual(result["blocked_step_key"], "budget")
        self.assertEqual(result["next_action"], "Resolve budget block")

    # -----------------------------------------------------------------------
    # STAGE-004  Pure function — highest active step_order wins
    # -----------------------------------------------------------------------

    def test_pure_highest_step_order_wins(self):
        """STAGE-004: Step with highest step_order in _ACTIVE_STATUSES is current."""
        steps = [
            _make_step("strategy", "Strategic Priority", 1, "Completed"),
            _make_step("budget", "Funding Available", 2, "Completed"),
            _make_step("demand", "Need Approved", 3, "In Progress", "Approve demand"),
            _make_step("planning", "Procurement Planned", 4, "Not Started"),
        ]
        result = calculate_current_stage_from_steps(steps)

        self.assertEqual(result["current_stage"], "Need Approved")
        self.assertEqual(result["current_stage_key"], "demand")
        self.assertEqual(result["current_status"], "In Progress")
        self.assertFalse(result["is_blocked"])

    # -----------------------------------------------------------------------
    # STAGE-005  Pure function — Handed Off counts as active
    # -----------------------------------------------------------------------

    def test_pure_handed_off_counts_as_active(self):
        """STAGE-005: A Handed Off step is an active step; Completed steps after it
        override it only if at a higher step_order."""
        steps = [
            _make_step("strategy", "Strategic Priority", 1, "Completed"),
            _make_step("package_release", "Package Released", 2, "Handed Off", "Hand off package"),
            _make_step("std_readiness", "Tender Document Ready", 3, "Not Started"),
        ]
        result = calculate_current_stage_from_steps(steps)

        self.assertEqual(result["current_stage"], "Package Released")
        self.assertEqual(result["current_stage_key"], "package_release")
        self.assertEqual(result["current_status"], "Handed Off")

    def test_pure_completed_after_handed_off_wins(self):
        """STAGE-005b: Completed at higher step_order overrides lower Handed Off."""
        steps = [
            _make_step("package_release", "Package Released", 1, "Handed Off"),
            _make_step("std_readiness", "Tender Document Ready", 2, "Completed", "Publish tender"),
        ]
        result = calculate_current_stage_from_steps(steps)

        self.assertEqual(result["current_stage"], "Tender Document Ready")
        self.assertEqual(result["current_status"], "Completed")

    # -----------------------------------------------------------------------
    # STAGE-006  Pure function — next_action fallback to following step
    # -----------------------------------------------------------------------

    def test_pure_next_action_fallback_to_following_step(self):
        """STAGE-006: When current step has no next_action, fall back to following step."""
        steps = [
            _make_step("strategy", "Strategic Priority", 1, "Completed", ""),  # no next_action
            _make_step("budget", "Funding Available", 2, "Not Started", "Confirm budget funding"),
        ]
        result = calculate_current_stage_from_steps(steps)

        self.assertEqual(result["current_stage"], "Strategic Priority")
        # Fallback: step 2's next_action
        self.assertEqual(result["next_action"], "Confirm budget funding")

    def test_pure_next_action_uses_current_step_when_set(self):
        """STAGE-006b: When current step has next_action, it takes priority."""
        steps = [
            _make_step("strategy", "Strategic Priority", 1, "Completed", "Await budget confirmation"),
            _make_step("budget", "Funding Available", 2, "Not Started", "Confirm budget funding"),
        ]
        result = calculate_current_stage_from_steps(steps)

        self.assertEqual(result["next_action"], "Await budget confirmation")

    # -----------------------------------------------------------------------
    # STAGE-007  Pure function — empty steps
    # -----------------------------------------------------------------------

    def test_pure_empty_step_list_returns_safe_response(self):
        """STAGE-007: Empty step list → safe empty response, not an error."""
        result = calculate_current_stage_from_steps([])

        self.assertEqual(result["current_stage"], "")
        self.assertEqual(result["current_stage_key"], "")
        self.assertEqual(result["current_status"], "Not Started")
        self.assertFalse(result["is_blocked"])
        self.assertIsNone(result["blocked_step_key"])

    # -----------------------------------------------------------------------
    # STAGE-008  update_journey_current_stage persists to DB
    # -----------------------------------------------------------------------

    def test_update_persists_computed_values_to_db(self):
        """STAGE-008: update_journey_current_stage writes back to Procurement Journey."""
        result = update_journey_current_stage(_WORKS_JOURNEY_CODE)

        db_stage = frappe.db.get_value(
            "Procurement Journey",
            _WORKS_JOURNEY_CODE,
            ["current_stage_label", "current_stage_key", "current_status_category", "next_action"],
            as_dict=True,
        )

        self.assertEqual(db_stage.current_stage_label, result["current_stage"])
        self.assertEqual(db_stage.current_stage_key, result["current_stage_key"])
        self.assertEqual(db_stage.current_status_category, result["current_status"])
        # next_action may be truncated by text field; just check DB is non-empty if result is
        if result["next_action"]:
            self.assertTrue(db_stage.next_action, msg="DB next_action should be non-empty")

    # -----------------------------------------------------------------------
    # ERR-001  Blank journey_code
    # -----------------------------------------------------------------------

    def test_blank_journey_code_raises(self):
        """ERR-001: Blank or whitespace journey_code → INVALID_JOURNEY_CODE ValueError."""
        for bad in ("", "   ", None):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError, TypeError)):
                    calculate_journey_current_stage(bad)  # type: ignore[arg-type]

    # -----------------------------------------------------------------------
    # ERR-002  Unknown journey_code
    # -----------------------------------------------------------------------

    def test_unknown_journey_code_raises(self):
        """ERR-002: Unknown journey code → DoesNotExistError or ValueError (JOURNEY_NOT_FOUND)."""
        with self.assertRaises((frappe.DoesNotExistError, ValueError)):
            calculate_journey_current_stage("JRN-DOES-NOT-EXIST-9999")
