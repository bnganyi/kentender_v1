# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Budget financial control engine — unit / integration tests.

Covers: snapshot, reserve, release, convert_to_commitment, record_consumption,
        revision guards (line-level and budget-level), and the Planning
        funding-check endpoint.

Run:
  bench --site kentender.midas.com run-tests \\
    --app kentender_budget \\
    --module kentender_budget.tests.test_budget_service
"""
from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


# ── Test fixture factory ───────────────────────────────────────────────────────

def _make_line(
    allocated: float = 1_000_000.0,
    reserved: float = 0.0,
    committed: float = 0.0,
    consumed: float = 0.0,
) -> tuple:
    """Create a minimal Budget + Budget Line for a test; return (budget, line) docs."""
    ensure_currency_kes()
    h = frappe.generate_hash(length=6)
    entity = ensure_procuring_entity(f"BS-{h}", f"Budget Service Test {h}")
    plan = frappe.get_doc({
        "doctype": "Strategic Plan",
        "strategic_plan_name": f"Plan-BS-{h}",
        "procuring_entity": entity,
        "start_year": 2026, "end_year": 2030,
        "status": "Draft", "version_no": 1, "is_current_version": 1,
    }).insert(ignore_permissions=True)
    prog = frappe.get_doc({
        "doctype": "Strategy Program",
        "strategic_plan": plan.name,
        "program_title": f"Prog-BS-{h}",
        "order_index": 1,
    }).insert(ignore_permissions=True)
    budget = frappe.get_doc({
        "doctype": "Budget",
        "budget_name": f"BUD-BS-{h}",
        "procuring_entity": entity,
        "fiscal_year": 2026,
        "strategic_plan": plan.name,
        "currency": "KES",
        "total_budget_amount": allocated,
        "version_no": 1, "is_current_version": 1, "order_index": 0,
    }).insert(ignore_permissions=True)
    line = frappe.get_doc({
        "doctype": "Budget Line",
        "budget_line_code": f"BL-BS-{h}",
        "budget_line_name": f"Line-BS-{h}",
        "budget": budget.name,
        "procuring_entity": entity,
        "fiscal_year": 2026,
        "amount_allocated": allocated,
        "amount_reserved": reserved,
        "amount_committed": committed,
        "amount_consumed": consumed,
        "currency": "KES",
        "strategic_plan": plan.name,
        "program": prog.name,
        "is_active": 1,
    }).insert(ignore_permissions=True)
    return budget, line


class TestBudgetServiceSnapshot(IntegrationTestCase):
    """snapshot() returns correct balance tuple."""

    def setUp(self):
        frappe.set_user("Administrator")
        _bud, self.line = _make_line(
            allocated=500_000, reserved=100_000, committed=50_000, consumed=25_000
        )

    def test_snapshot_formula(self):
        from kentender_budget.services.budget_service import snapshot
        snap = snapshot(self.line.name)
        self.assertAlmostEqual(snap.allocated, 500_000, places=2)
        self.assertAlmostEqual(snap.reserved, 100_000, places=2)
        self.assertAlmostEqual(snap.committed, 50_000, places=2)
        self.assertAlmostEqual(snap.consumed, 25_000, places=2)
        # available = 500k − 100k − 50k − 25k = 325k
        self.assertAlmostEqual(snap.available, 325_000, places=2)

    def test_snapshot_currency(self):
        from kentender_budget.services.budget_service import snapshot
        snap = snapshot(self.line.name)
        self.assertEqual(snap.currency, "KES")


class TestBudgetServiceReserve(IntegrationTestCase):
    """reserve() creates a Budget Reservation and decrements available."""

    def setUp(self):
        frappe.set_user("Administrator")
        _bud, self.line = _make_line(allocated=1_000_000)

    def test_reserve_reduces_available(self):
        from kentender_budget.services.budget_service import reserve, snapshot
        before = snapshot(self.line.name).available
        result = reserve(
            self.line.name, "Demand", f"DEM-SVC-{frappe.generate_hash(6)}",
            400_000, actor="Administrator",
        )
        self.assertTrue(result["ok"], result)
        after = snapshot(self.line.name).available
        self.assertAlmostEqual(after, before - 400_000, places=2)

    def test_reserve_returns_reservation_id(self):
        from kentender_budget.services.budget_service import reserve
        result = reserve(
            self.line.name, "Demand", f"DEM-SVC-{frappe.generate_hash(6)}",
            200_000, actor="Administrator",
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["reservation_id"])

    def test_reserve_blocks_overdraft(self):
        from kentender_budget.services.budget_service import reserve
        result = reserve(
            self.line.name, "Demand", f"DEM-SVC-{frappe.generate_hash(6)}",
            2_000_000,  # exceeds allocated
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "INSUFFICIENT_BUDGET")

    def test_reserve_rejects_duplicate_active_for_same_source(self):
        from kentender_budget.services.budget_service import reserve
        src = f"DEM-DUP-{frappe.generate_hash(6)}"
        first = reserve(self.line.name, "Demand", src, 100_000)
        self.assertTrue(first["ok"])
        second = reserve(self.line.name, "Demand", src, 50_000)
        self.assertFalse(second["ok"])
        self.assertEqual(second["error_code"], "DUPLICATE_ACTIVE_RESERVATION")

    def test_reserve_inactive_line_blocked(self):
        from kentender_budget.services.budget_service import reserve
        frappe.db.set_value("Budget Line", self.line.name, "is_active", 0)
        try:
            result = reserve(
                self.line.name, "Demand", f"DEM-SVC-{frappe.generate_hash(6)}", 100_000
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["error_code"], "BUDGET_LINE_INACTIVE")
        finally:
            frappe.db.set_value("Budget Line", self.line.name, "is_active", 1)


class TestBudgetServiceRelease(IntegrationTestCase):
    """release() restores available and marks reservation Released."""

    def setUp(self):
        frappe.set_user("Administrator")
        _bud, self.line = _make_line(allocated=1_000_000)
        from kentender_budget.services.budget_service import reserve
        res = reserve(
            self.line.name, "Demand", f"DEM-REL-{frappe.generate_hash(6)}",
            300_000, actor="Administrator",
        )
        self.reservation_id = res["data"]["reservation_id"]

    def test_release_restores_available(self):
        from kentender_budget.services.budget_service import release, snapshot
        before = snapshot(self.line.name).available
        result = release(self.reservation_id, reason="Test cleanup", actor="Administrator")
        self.assertTrue(result["ok"], result)
        after = snapshot(self.line.name).available
        self.assertAlmostEqual(after, before + 300_000, places=2)

    def test_release_marks_reservation_released(self):
        from kentender_budget.services.budget_service import release
        release(self.reservation_id, reason="Test cleanup", actor="Administrator")
        name = frappe.db.get_value(
            "Budget Reservation", {"reservation_id": self.reservation_id}, "name"
        )
        status = frappe.db.get_value("Budget Reservation", name, "status")
        self.assertEqual(status, "Released")

    def test_release_requires_reason(self):
        from kentender_budget.services.budget_service import release
        result = release(self.reservation_id, reason="")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "RELEASE_REASON_REQUIRED")

    def test_double_release_blocked(self):
        from kentender_budget.services.budget_service import release
        first = release(self.reservation_id, reason="First", actor="Administrator")
        self.assertTrue(first["ok"])
        second = release(self.reservation_id, reason="Second", actor="Administrator")
        self.assertFalse(second["ok"])
        self.assertEqual(second["error_code"], "RESERVATION_NOT_ACTIVE")


class TestBudgetServiceConvertToCommitment(IntegrationTestCase):
    """convert_to_commitment() moves reserved→committed on Budget Line."""

    def setUp(self):
        frappe.set_user("Administrator")
        _bud, self.line = _make_line(allocated=1_000_000)
        from kentender_budget.services.budget_service import reserve
        res = reserve(
            self.line.name, "Demand", f"DEM-COM-{frappe.generate_hash(6)}",
            600_000, actor="Administrator",
        )
        self.reservation_id = res["data"]["reservation_id"]

    def test_convert_moves_reserved_to_committed(self):
        from kentender_budget.services.budget_service import convert_to_commitment, snapshot
        snap_before = snapshot(self.line.name)
        result = convert_to_commitment(
            self.reservation_id,
            commitment_amount=580_000,
            commitment_source_doctype="Contract",
            commitment_source_docname=f"CONT-{frappe.generate_hash(6)}",
            actor="Administrator",
        )
        self.assertTrue(result["ok"], result)
        snap_after = snapshot(self.line.name)
        # reserved should drop by 600k (full reservation)
        self.assertAlmostEqual(snap_after.reserved, snap_before.reserved - 600_000, places=2)
        # committed should rise by 580k (contract value, may differ from reservation)
        self.assertAlmostEqual(snap_after.committed, snap_before.committed + 580_000, places=2)
        # available freed by the delta (600k - 580k = 20k returned)
        self.assertAlmostEqual(snap_after.available, snap_before.available + 20_000, places=2)

    def test_convert_full_amount_no_slack(self):
        from kentender_budget.services.budget_service import convert_to_commitment, snapshot
        snap_before = snapshot(self.line.name)
        result = convert_to_commitment(
            self.reservation_id, commitment_amount=600_000, actor="Administrator"
        )
        self.assertTrue(result["ok"], result)
        snap_after = snapshot(self.line.name)
        self.assertAlmostEqual(snap_after.reserved, snap_before.reserved - 600_000, places=2)
        self.assertAlmostEqual(snap_after.committed, snap_before.committed + 600_000, places=2)
        self.assertAlmostEqual(snap_after.available, snap_before.available, places=2)

    def test_convert_marks_reservation_converted(self):
        from kentender_budget.services.budget_service import convert_to_commitment
        convert_to_commitment(
            self.reservation_id, commitment_amount=600_000, actor="Administrator"
        )
        name = frappe.db.get_value(
            "Budget Reservation", {"reservation_id": self.reservation_id}, "name"
        )
        status = frappe.db.get_value("Budget Reservation", name, "status")
        self.assertEqual(status, "Converted")

    def test_convert_non_active_reservation_blocked(self):
        from kentender_budget.services.budget_service import convert_to_commitment, release
        release(self.reservation_id, reason="Pre-released", actor="Administrator")
        result = convert_to_commitment(
            self.reservation_id, commitment_amount=600_000, actor="Administrator"
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "RESERVATION_NOT_ACTIVE")

    def test_convert_commitment_exceeds_reservation_blocked(self):
        from kentender_budget.services.budget_service import convert_to_commitment
        # commitment_amount > reservation amount → should be blocked
        result = convert_to_commitment(
            self.reservation_id, commitment_amount=700_000, actor="Administrator"
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "COMMITMENT_EXCEEDS_RESERVATION")


class TestBudgetServiceRecordConsumption(IntegrationTestCase):
    """record_consumption() increments consumed and decrements committed."""

    def setUp(self):
        frappe.set_user("Administrator")
        _bud, self.line = _make_line(allocated=1_000_000)
        from kentender_budget.services.budget_service import reserve, convert_to_commitment
        res = reserve(
            self.line.name, "Demand", f"DEM-CON-{frappe.generate_hash(6)}",
            800_000, actor="Administrator",
        )
        self.reservation_id = res["data"]["reservation_id"]
        convert_to_commitment(
            self.reservation_id, commitment_amount=800_000, actor="Administrator"
        )

    def test_consumption_increments_consumed_decrements_committed(self):
        from kentender_budget.services.budget_service import record_consumption, snapshot
        snap_before = snapshot(self.line.name)
        result = record_consumption(
            self.line.name, amount=200_000,
            source_doctype="Payment",
            source_docname=f"PAY-{frappe.generate_hash(6)}",
            actor="Administrator",
        )
        self.assertTrue(result["ok"], result)
        snap_after = snapshot(self.line.name)
        self.assertAlmostEqual(snap_after.consumed, snap_before.consumed + 200_000, places=2)
        self.assertAlmostEqual(snap_after.committed, snap_before.committed - 200_000, places=2)
        # available unchanged (committed→consumed is internal)
        self.assertAlmostEqual(snap_after.available, snap_before.available, places=2)

    def test_consumption_exceeding_committed_blocked(self):
        from kentender_budget.services.budget_service import record_consumption
        result = record_consumption(
            self.line.name, amount=900_000  # > committed 800k
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "CONSUMPTION_EXCEEDS_COMMITTED")

    def test_consumption_zero_blocked(self):
        from kentender_budget.services.budget_service import record_consumption
        result = record_consumption(self.line.name, amount=0)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "INVALID_AMOUNT")


class TestBudgetRevisionGuards(IntegrationTestCase):
    """Revision guards block allocation reductions below obligations."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.budget, self.line = _make_line(allocated=1_000_000)
        from kentender_budget.services.budget_service import reserve, convert_to_commitment
        h = frappe.generate_hash(6)
        res = reserve(self.line.name, "Demand", f"DEM-GRD-{h}", 300_000)
        self.reservation_id = res["data"]["reservation_id"]
        convert_to_commitment(
            self.reservation_id, commitment_amount=300_000, actor="Administrator"
        )

    def test_line_reduction_below_committed_blocked(self):
        """Budget Line: reducing amount_allocated below committed+consumed raises."""
        from kentender_budget.services.budget_guards import assert_line_reduction_safe
        # committed = 300k, consumed = 0; new_alloc = 200k → blocked
        with self.assertRaises(frappe.exceptions.ValidationError):
            assert_line_reduction_safe(self.line.name, new_allocated=200_000)

    def test_line_reduction_to_safe_level_allowed(self):
        """Budget Line: reducing to level still >= obligations is allowed."""
        from kentender_budget.services.budget_guards import assert_line_reduction_safe
        # committed = 300k; new_alloc = 350k → OK
        assert_line_reduction_safe(self.line.name, new_allocated=350_000)

    def test_budget_total_reduction_below_obligations_blocked(self):
        """Budget: reducing total_budget_amount below sum of line obligations raises."""
        from kentender_budget.services.budget_guards import assert_budget_total_reduction_safe
        # Line has 300k committed; trying to set budget total to 100k → blocked
        with self.assertRaises(frappe.exceptions.ValidationError):
            assert_budget_total_reduction_safe(self.budget.name, new_total=100_000)

    def test_budget_total_reduction_to_safe_level_allowed(self):
        """Budget: reducing total to level still >= obligations is allowed."""
        from kentender_budget.services.budget_guards import assert_budget_total_reduction_safe
        assert_budget_total_reduction_safe(self.budget.name, new_total=400_000)


class TestFundingCheckEndpoint(IntegrationTestCase):
    """check_package_funding returns correct sufficiency response for Planning."""

    def setUp(self):
        frappe.set_user("Administrator")
        _bud, self.line = _make_line(allocated=2_000_000)

    def test_sufficient_funding(self):
        from kentender_budget.api.funding_check import check_package_funding
        result = check_package_funding(
            budget_line_id=self.line.name,
            amount=500_000,
        )
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertTrue(data["is_sufficient"])
        self.assertAlmostEqual(data["amount_available"], 2_000_000, places=2)
        self.assertAlmostEqual(data["shortfall"], 0.0, places=2)

    def test_insufficient_funding(self):
        from kentender_budget.api.funding_check import check_package_funding
        result = check_package_funding(
            budget_line_id=self.line.name,
            amount=5_000_000,
        )
        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertFalse(data["is_sufficient"])
        self.assertGreater(data["shortfall"], 0)

    def test_funding_check_with_active_reservation(self):
        """Available should reflect existing reservations."""
        from kentender_budget.services.budget_service import reserve
        from kentender_budget.api.funding_check import check_package_funding
        reserve(
            self.line.name, "Demand", f"DEM-FC-{frappe.generate_hash(6)}",
            1_800_000, actor="Administrator",
        )
        # only 200k left; 500k request is now insufficient
        result = check_package_funding(self.line.name, 500_000)
        self.assertTrue(result["ok"])
        self.assertFalse(result["data"]["is_sufficient"])

    def test_funding_check_inactive_line_blocked(self):
        from kentender_budget.api.funding_check import check_package_funding
        frappe.db.set_value("Budget Line", self.line.name, "is_active", 0)
        try:
            result = check_package_funding(self.line.name, 100_000)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error_code"], "BUDGET_LINE_INACTIVE")
        finally:
            frappe.db.set_value("Budget Line", self.line.name, "is_active", 1)

    def test_funding_check_with_source_reference(self):
        """Passing source context is accepted and reflected in response."""
        from kentender_budget.api.funding_check import check_package_funding
        result = check_package_funding(
            budget_line_id=self.line.name,
            amount=300_000,
            source_doctype="Procurement Package",
            source_docname=f"PKG-FC-{frappe.generate_hash(6)}",
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["is_sufficient"])
