# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""TDD contract tests for the Budget Revision API (api/revision.py).

Covers:
  1. request_revision — creates Draft revision with version_no+1 and copies lines
  2. request_revision — on non-Active budget throws ValidationError
  3. submit_revision  — transitions Draft → Submitted
  4. return_revision  — transitions Submitted → Draft, sets rejection_reason
  5. approve_revision — revision → Active, predecessor → Revised (atomic)
  6. approve_revision — blocked if a line is reduced below reserved+committed
  7. cancel_revision  — on Submitted budget throws
  8. get_revision_diff — returns predecessor totals and line diffs

Run:
  bench --site kentender.midas.com run-tests \\
    --app kentender_budget \\
    --module kentender_budget.tests.test_budget_revision_api
"""
from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity

from kentender_budget.api.revision import (
    approve_revision,
    cancel_revision,
    get_revision_diff,
    request_revision,
    return_revision,
    submit_revision,
)


# ── Shared fixture helpers ────────────────────────────────────────────────────

def _make_strategic_plan(entity, suffix):
    plan = frappe.get_doc({
        "doctype": "Strategic Plan",
        "strategic_plan_name": f"Revision Test Plan {suffix}",
        "procuring_entity": entity,
        "start_year": 2026,
        "end_year": 2030,
        "status": "Draft",
    }).insert(ignore_permissions=True)
    return plan


def _make_program(plan_name, suffix):
    return frappe.get_doc({
        "doctype": "Strategy Program",
        "strategic_plan": plan_name,
        "program_title": f"Revision Test Program {suffix}",
        "order_index": 0,
    }).insert(ignore_permissions=True)


def _make_budget(entity, plan_name, suffix, status="Active", version_no=1):
    """Return a saved Budget in the requested status. Bypasses before_insert Draft constraint."""
    name_candidate = f"BUDGET-REV-{suffix}"
    if frappe.db.exists("Budget", name_candidate):
        frappe.delete_doc("Budget", name_candidate, ignore_permissions=True, force=True)

    doc = frappe.get_doc({
        "doctype": "Budget",
        "budget_name": f"Revision Test Budget {suffix}",
        "procuring_entity": entity,
        "fiscal_year": 2026,
        "strategic_plan": plan_name,
        "currency": "KES",
        "total_budget_amount": 1_000_000,
        "version_no": version_no,
        "is_current_version": 1,
        "order_index": 0,
        "effective_date": "2026-01-01",
        "closing_date": "2026-12-31",
        "status": "Draft",
    }).insert(ignore_permissions=True)

    if status != "Draft":
        frappe.db.set_value("Budget", doc.name, "status", status)
        doc.reload()

    return doc


def _add_line(budget_doc, suffix, amount_allocated=200_000, reserved=0, committed=0, program=None):
    """Insert and return a Budget Line for the given budget."""
    line = frappe.get_doc({
        "doctype": "Budget Line",
        "budget": budget_doc.name,
        "procuring_entity": budget_doc.procuring_entity,
        "budget_line_code": f"BL-REV-{suffix}",
        "budget_line_name": f"Revision Line {suffix}",
        "fiscal_year": 2026,
        "currency": "KES",
        "strategic_plan": budget_doc.strategic_plan,
        "program": program,
        "is_active": 1,
        "amount_allocated": amount_allocated,
        "amount_reserved": reserved,
        "amount_committed": committed,
        "amount_consumed": 0,
        "amount_available": amount_allocated - reserved - committed,
        "economic_classification": "Works",
        "line_status": "Active",
    }).insert(ignore_permissions=True)
    return line


# ── Test class ────────────────────────────────────────────────────────────────

class TestBudgetRevisionApi(IntegrationTestCase):
    """Contract tests for the budget revision lifecycle API."""

    # ── Fixtures ──────────────────────────────────────────────────────────────

    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        h = frappe.generate_hash(length=6)
        self.h = h
        self.entity = ensure_procuring_entity(f"ENT-REV-{h}", f"Revision Test Entity {h}")
        self.plan = _make_strategic_plan(self.entity, h)
        self.program = _make_program(self.plan.name, h)

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    # ── Helper ────────────────────────────────────────────────────────────────

    def _active_budget_with_lines(self):
        b = _make_budget(self.entity, self.plan.name, self.h, status="Active")
        _add_line(b, f"{self.h}-L1", amount_allocated=300_000, program=self.program.name)
        _add_line(b, f"{self.h}-L2", amount_allocated=200_000, program=self.program.name)
        return b

    # ── Test 1: request_revision creates Draft revision with version_no+1 ─────

    def test_01_request_revision_creates_draft_with_incremented_version(self):
        """Happy path: creates a Draft revision with version_no+1 and copies lines."""
        active = self._active_budget_with_lines()
        original_version = active.version_no or 1

        result = request_revision(active.name)

        self.assertIn("name", result)
        rev = frappe.get_doc("Budget", result["name"])

        self.assertEqual(rev.status, "Draft")
        self.assertEqual(rev.supersedes_budget, active.name)
        self.assertEqual((rev.version_no or 1), original_version + 1)

        # Lines copied
        rev_lines = frappe.get_all(
            "Budget Line", filters={"budget": rev.name, "is_active": 1}, fields=["name"]
        )
        self.assertEqual(len(rev_lines), 2, "Both lines must be copied to the revision")

    # ── Test 2: request_revision on non-Active budget throws ──────────────────

    def test_02_request_revision_on_draft_budget_throws(self):
        """request_revision must reject non-Active budgets."""
        draft_budget = _make_budget(self.entity, self.plan.name, f"{self.h}d", status="Draft")
        with self.assertRaises(frappe.ValidationError):
            request_revision(draft_budget.name)

    # ── Test 3: submit_revision transitions Draft → Submitted ─────────────────

    def test_03_submit_revision_transitions_to_submitted(self):
        """submit_revision moves a Draft revision to Submitted."""
        active = _make_budget(self.entity, self.plan.name, f"{self.h}s", status="Active")
        res = request_revision(active.name)
        rev_name = res["name"]

        result = submit_revision(rev_name)

        self.assertEqual(result["status"], "Submitted")
        self.assertEqual(frappe.db.get_value("Budget", rev_name, "status"), "Submitted")

    # ── Test 4: return_revision transitions Submitted → Draft ─────────────────

    def test_04_return_revision_transitions_to_draft_with_reason(self):
        """return_revision sends a Submitted revision back to Draft with a reason."""
        active = _make_budget(self.entity, self.plan.name, f"{self.h}r", status="Active")
        res = request_revision(active.name)
        rev_name = res["name"]
        submit_revision(rev_name)

        result = return_revision(rev_name, reason="Missing documentation")

        self.assertEqual(result["status"], "Draft")
        stored_reason = frappe.db.get_value("Budget", rev_name, "rejection_reason")
        self.assertEqual(stored_reason, "Missing documentation")

    # ── Test 5: approve_revision → revision Active, predecessor Revised ────────

    def test_05_approve_revision_promotes_revision_and_locks_predecessor(self):
        """approve_revision atomically sets revision→Active and predecessor→Revised."""
        active = self._active_budget_with_lines()
        res = request_revision(active.name)
        rev_name = res["name"]
        submit_revision(rev_name)

        result = approve_revision(rev_name)

        self.assertEqual(result["status"], "Active")
        self.assertEqual(result["predecessor"], active.name)

        # Revision is now Active
        self.assertEqual(frappe.db.get_value("Budget", rev_name, "status"), "Active")
        # Predecessor is now Revised
        self.assertEqual(frappe.db.get_value("Budget", active.name, "status"), "Revised")
        # Predecessor is no longer current version
        self.assertEqual(frappe.db.get_value("Budget", active.name, "is_current_version"), 0)

    # ── Test 6: approve_revision blocked when line below obligations ───────────

    def test_06_approve_revision_blocked_when_line_below_reserved_plus_committed(self):
        """approve_revision must throw if a revision line's allocation < reserved+committed."""
        active = _make_budget(self.entity, self.plan.name, f"{self.h}g", status="Active")
        _add_line(active, f"{self.h}g-L1", amount_allocated=500_000, program=self.program.name)
        res = request_revision(active.name)
        rev_name = res["name"]

        # Force the copied line's allocation down below its obligations using set_value
        rev_line = frappe.get_all(
            "Budget Line", filters={"budget": rev_name, "is_active": 1}, fields=["name"], limit=1
        )[0]
        frappe.db.set_value("Budget Line", rev_line.name, {
            "amount_allocated": 50_000,
            "amount_reserved": 200_000,
            "amount_committed": 0,
        })

        submit_revision(rev_name)
        with self.assertRaises(frappe.ValidationError):
            approve_revision(rev_name)

    # ── Test 7: cancel_revision on Submitted throws ───────────────────────────

    def test_07_cancel_revision_on_submitted_throws(self):
        """cancel_revision must reject Submitted revisions (only Draft can be cancelled)."""
        active = _make_budget(self.entity, self.plan.name, f"{self.h}c", status="Active")
        res = request_revision(active.name)
        rev_name = res["name"]
        submit_revision(rev_name)

        with self.assertRaises(frappe.ValidationError):
            cancel_revision(rev_name)

    # ── Test 8: get_revision_diff returns predecessor totals and line diffs ────

    def test_08_get_revision_diff_returns_before_after_comparison(self):
        """get_revision_diff must return predecessor totals and line-level diffs."""
        active = self._active_budget_with_lines()
        res = request_revision(active.name)
        rev_name = res["name"]

        diff = get_revision_diff(rev_name)

        self.assertTrue(diff["is_revision"])
        self.assertEqual(diff["predecessor_name"], active.name)
        self.assertIn("predecessor", diff)
        self.assertIn("revision", diff)
        self.assertIn("line_diffs", diff)
        self.assertGreater(len(diff["line_diffs"]), 0)
        # Predecessor and revision totals should match (no changes yet)
        self.assertAlmostEqual(diff["predecessor"]["allocated"], diff["revision"]["allocated"], places=2)
