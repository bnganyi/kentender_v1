# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-013 — ``aggregate_procurement_journey_steps`` service tests.

## Tests

1. **STEP-TEST-R3-013-001** — Ordered step list: WORKS scenario returns 12 steps in
   ``step_order`` ascending; ``step_key`` sequence matches
   ``WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER``.

2. **STEP-TEST-R3-013-002** — Required field shapes: every step dict contains the
   mandatory §6.2 keys with correct Python types (``step_order`` int, ``blocker_count``
   int, ``status_category`` non-empty string, etc.).

3. **STEP-TEST-R3-013-003** — First seven steps completed or handed off; last five are
   ``Not Started`` at the base ``TENDER_PUBLISHED`` checkpoint.

4. **STEP-TEST-R3-013-004** — Empty journey: a journey with no child rows returns ``[]``
   without raising.

5. **STEP-TEST-R3-013-005** — Missing journey raises ``DoesNotExistError`` with title
   ``JOURNEY_NOT_FOUND``; blank ``journey_code`` raises ``ValueError`` with code
   ``INVALID_JOURNEY_CODE``.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_013_aggregate_journey_steps
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
from kentender_procurement.procurement_lifecycle.journey_step_aggregator import (
    aggregate_procurement_journey_steps,
)
from kentender_procurement.procurement_lifecycle.works_seed_step_contract import (
    WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# §9.3 / §15 — canonical 12-step labels for display order validation
_STEP_ORDER_12 = list(range(1, 13))

# First 7 steps should be "done" at base TENDER_PUBLISHED checkpoint.
_COMPLETED_STATUSES = {"Completed", "Handed Off", "Ready for Handoff"}

# Last 5 steps (indices 7–11) should be Not Started at base checkpoint.
_NOT_STARTED_STEP_INDICES = list(range(7, 12))


class TestR3013AggregateJourneySteps(IntegrationTestCase):
    """R3-013 — Step aggregation service tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Ensure WORKS master seed prerequisites are present (idempotent)
        for label, fn in (
            ("Strategy", upsert_works_master_strategy_hierarchy),
            ("Budget", upsert_works_master_budget),
            ("Demand", upsert_works_master_demand),
            ("Planning", upsert_works_master_planning),
            ("STD", upsert_works_master_std),
            ("Tender", upsert_works_master_tender),
        ):
            result = fn()
            assert result.get("ok"), f"{label} prerequisite failed: {result}"

        # Materialize journey + steps at base TENDER_PUBLISHED checkpoint
        plc_result = load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")
        assert plc_result.get("ok"), f"PLC base seed failed: {plc_result}"
        frappe.db.commit()

    # ------------------------------------------------------------------
    # STEP-TEST-R3-013-001 — Ordered step list
    # ------------------------------------------------------------------
    def test_001_steps_ordered_and_key_sequence_matches_works_contract(self):
        """Steps returned in step_order ascending; step_key sequence matches WORKS contract."""
        steps = aggregate_procurement_journey_steps(JOURNEY_CODE)

        self.assertEqual(
            len(steps), 12,
            f"Expected 12 steps for WORKS base seed; got {len(steps)}",
        )

        # step_order values must be strictly [1, 2, ..., 12]
        actual_orders = [s["step_order"] for s in steps]
        self.assertEqual(actual_orders, _STEP_ORDER_12, "step_order must be 1–12 ascending")

        # step_key sequence must match WORKS seed contract exactly
        actual_keys = [s["step_key"] for s in steps]
        expected_keys = list(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER)
        self.assertEqual(
            actual_keys, expected_keys,
            f"step_key sequence mismatch:\n  got:      {actual_keys}\n  expected: {expected_keys}",
        )

    # ------------------------------------------------------------------
    # STEP-TEST-R3-013-002 — Required field shapes
    # ------------------------------------------------------------------
    def test_002_required_field_shapes_per_spec_6_2(self):
        """Every step contains required §6.2 keys with correct Python types."""
        steps = aggregate_procurement_journey_steps(JOURNEY_CODE)
        self.assertTrue(steps, "Steps list must not be empty")

        required_str_fields = {"step_key", "label", "status_category", "owner_module"}
        required_int_fields = {"step_order", "blocker_count"}

        for i, step in enumerate(steps):
            for field in required_str_fields:
                self.assertIn(field, step, f"Step {i}: missing field {field!r}")
                self.assertIsInstance(
                    step[field], str,
                    f"Step {i} field {field!r}: expected str, got {type(step[field]).__name__}",
                )
                self.assertTrue(
                    step[field].strip(),
                    f"Step {i} field {field!r}: must not be blank",
                )
            for field in required_int_fields:
                self.assertIn(field, step, f"Step {i}: missing field {field!r}")
                self.assertIsInstance(
                    step[field], int,
                    f"Step {i} field {field!r}: expected int, got {type(step[field]).__name__}",
                )
                self.assertGreaterEqual(step[field], 0, f"Step {i} field {field!r}: must be >= 0")

            # Optional fields must be None or the correct type
            if step.get("last_action_at") is not None:
                self.assertIsInstance(step["last_action_at"], str, f"Step {i}: last_action_at must be str when set")
            if step.get("blockers_json") is not None:
                self.assertIsInstance(step["blockers_json"], (dict, list), f"Step {i}: blockers_json must be dict or list")

    # ------------------------------------------------------------------
    # STEP-TEST-R3-013-003 — Status categories at base checkpoint
    # ------------------------------------------------------------------
    def test_003_first_seven_complete_last_five_not_started(self):
        """Steps 1–7 are completed/handed-off; steps 8–12 are Not Started (base checkpoint)."""
        steps = aggregate_procurement_journey_steps(JOURNEY_CODE)
        self.assertEqual(len(steps), 12)

        # First 7 steps (index 0–6) should be "done"
        for i, step in enumerate(steps[:7]):
            self.assertIn(
                step["status_category"],
                _COMPLETED_STATUSES,
                f"Step {i + 1} ({step['step_key']!r}) expected completed status, "
                f"got {step['status_category']!r}",
            )

        # Last 5 steps (index 7–11) should be Not Started
        for i, step in enumerate(steps[7:], start=8):
            self.assertEqual(
                step["status_category"],
                "Not Started",
                f"Step {i} ({step['step_key']!r}) expected 'Not Started' at base checkpoint, "
                f"got {step['status_category']!r}",
            )

    # ------------------------------------------------------------------
    # STEP-TEST-R3-013-004 — Empty journey
    # ------------------------------------------------------------------
    def test_004_empty_journey_returns_empty_list(self):
        """A journey with no child rows returns an empty list without raising."""
        # Create a bare journey with no step rows
        bare_code = "JRN-TEST-R3013-EMPTY"
        if not frappe.db.exists("Procurement Journey", bare_code):
            doc = frappe.get_doc({
                "doctype": "Procurement Journey",
                "name": bare_code,
                "journey_code": bare_code,
                "journey_title": "R3-013 empty test journey",
                "procuring_entity_code": _PE_CODE,
                "procuring_entity_name": _PE_DISPLAY,
                "fiscal_year": "2026",
                "status": "Active",
                "current_stage_key": "strategy",
                "current_stage_label": "Strategy Priority",
                "current_status_category": "Not Started",
                "current_owner_module": "Strategy",
                "blocker_count": 0,
                "critical_blocker_count": 0,
            })
            doc.flags.ignore_permissions = True
            doc.flags.ignore_mandatory = True
            doc.insert()
            frappe.db.commit()

        steps = aggregate_procurement_journey_steps(bare_code)
        self.assertEqual(steps, [], "Empty journey must return []")

        # Cleanup
        frappe.delete_doc("Procurement Journey", bare_code, force=True, ignore_permissions=True)
        frappe.db.commit()

    # ------------------------------------------------------------------
    # STEP-TEST-R3-013-005 — Error handling
    # ------------------------------------------------------------------
    def test_005_missing_journey_raises_does_not_exist_error(self):
        """Non-existent journey_code raises DoesNotExistError (JOURNEY_NOT_FOUND)."""
        with self.assertRaises(frappe.DoesNotExistError):
            aggregate_procurement_journey_steps("JRN-DOES-NOT-EXIST-R3013")

    def test_005b_blank_journey_code_raises_value_error(self):
        """Blank journey_code raises ValueError (INVALID_JOURNEY_CODE)."""
        for bad_input in ("", "  ", None):
            with self.subTest(input=repr(bad_input)):
                with self.assertRaises((ValueError, TypeError)):
                    aggregate_procurement_journey_steps(bad_input)  # type: ignore[arg-type]
