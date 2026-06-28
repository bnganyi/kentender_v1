# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""W6-03 — TDD contract tests for upsert_budget_line.

Covers:
  1. Happy path create  — new line appears in returned payload (no duplicate)
  2. Happy path edit    — budget_line_id passed → existing line updated, count unchanged
  3. budget_line_name   — blank/missing → frappe.ValidationError
  4. amount_allocated   — negative value → frappe.ValidationError
  5. Permission         — non-owner user → frappe.PermissionError
  6. Approved budget    — mutation blocked by _assert_budget_editable_for_builder

Run:
  bench --site kentender.midas.com run-tests \\
    --app kentender_budget \\
    --module kentender_budget.tests.test_budget_line_upsert_api
"""
from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity

from kentender_budget.api.builder import upsert_budget_line


# ── Shared fixture helpers ────────────────────────────────────────────────────

def _make_budget(entity, plan_name, suffix, status="Draft", version_no=1):
    """Return a saved Budget document. Non-Draft status is force-set after insert
    because Budget.before_insert() blocks creation with non-Draft status."""
    doc = frappe.get_doc(
        {
            "doctype": "Budget",
            "budget_name": f"Budget Upsert {suffix}",
            "procuring_entity": entity,
            "fiscal_year": 2026,
            "strategic_plan": plan_name,
            "currency": "KES",
            "total_budget_amount": 1_000_000,
            "version_no": version_no,
            "is_current_version": 1 if version_no == 1 else 0,
            "order_index": 0,
            "effective_date": "2026-01-01",
            "closing_date": "2026-12-31",
            "status": "Draft",
        }
    ).insert(ignore_permissions=True)

    if status != "Draft":
        frappe.db.set_value("Budget", doc.name, "status", status)
        doc.reload()

    return doc


def _make_line(budget_name, entity, suffix, strategic_plan=None, program=None):
    """Return a saved Budget Line document."""
    return frappe.get_doc(
        {
            "doctype": "Budget Line",
            "budget": budget_name,
            "procuring_entity": entity,
            "budget_line_code": f"BL-UP-{suffix}",
            "budget_line_name": f"Existing Line {suffix}",
            "fiscal_year": 2026,
            "currency": "KES",
            "is_active": 1,
            "amount_allocated": 200_000,
            "amount_reserved": 0,
            "amount_committed": 0,
            "amount_consumed": 0,
            "amount_available": 200_000,
            "economic_classification": "Works",
            "line_status": "Active",
            "strategic_plan": strategic_plan,
            "program": program,
        }
    ).insert(ignore_permissions=True)


# ── Test class ────────────────────────────────────────────────────────────────

class TestUpsertBudgetLine(IntegrationTestCase):
    """Contract tests for the upsert_budget_line whitelist API."""

    # ── Fixtures ──────────────────────────────────────────────────────────────

    def setUp(self):
        frappe.set_user("Administrator")
        ensure_currency_kes()
        h = frappe.generate_hash(length=6)
        self._hash = h

        self.entity = ensure_procuring_entity(f"UP_{h}", f"Upsert Test Entity {h}")

        self.plan = frappe.get_doc(
            {
                "doctype": "Strategic Plan",
                "strategic_plan_name": f"Plan UP {h}",
                "procuring_entity": self.entity,
                "start_year": 2026,
                "end_year": 2030,
                "status": "Draft",
            }
        ).insert(ignore_permissions=True)

        self.program = frappe.get_doc(
            {
                "doctype": "Strategy Program",
                "strategic_plan": self.plan.name,
                "program_title": f"Program UP {h}",
                "order_index": 0,
            }
        ).insert(ignore_permissions=True)

        self.budget = _make_budget(self.entity, self.plan.name, h)
        self.existing_line = _make_line(
            self.budget.name, self.entity, h,
            strategic_plan=self.plan.name,
            program=self.program.name,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _line_names_in_payload(self, payload):
        """Return the set of budget_line_name values from the API payload."""
        return {l["budget_line_name"] for l in payload.get("budget_lines", [])}

    def _line_count(self, payload):
        return len(payload.get("budget_lines", []))

    def _find_line_by_name(self, payload, budget_line_name):
        matches = [
            l for l in payload.get("budget_lines", [])
            if l["budget_line_name"] == budget_line_name
        ]
        return matches[0] if matches else None

    # ── 1. Happy path: create ─────────────────────────────────────────────────

    def test_create_new_line_appears_in_payload(self):
        """A create call (no budget_line_id) must add a new entry to budget_lines."""
        before = self._line_count(
            upsert_budget_line(
                budget_name=self.budget.name,
                budget_line_name="New Infrastructure Line",
                amount_allocated=100_000,
                program=self.program.name,
            )
        )
        payload = upsert_budget_line(
            budget_name=self.budget.name,
            budget_line_name="New Infrastructure Line 2",
            amount_allocated=100_000,
            program=self.program.name,
        )
        self.assertIn("New Infrastructure Line 2", self._line_names_in_payload(payload))

    def test_create_returns_full_builder_payload(self):
        """upsert_budget_line must return the complete builder payload (budget + lines + totals)."""
        payload = upsert_budget_line(
            budget_name=self.budget.name,
            budget_line_name="Payload Shape Line",
            amount_allocated=50_000,
            program=self.program.name,
        )
        self.assertIn("budget", payload)
        self.assertIn("budget_lines", payload)
        self.assertIn("totals", payload)

    def test_create_line_has_correct_amount(self):
        """The returned payload must reflect the exact amount_allocated that was passed."""
        payload = upsert_budget_line(
            budget_name=self.budget.name,
            budget_line_name="Amount Check Line",
            amount_allocated=123_456,
            program=self.program.name,
        )
        line = self._find_line_by_name(payload, "Amount Check Line")
        self.assertIsNotNone(line, "Created line must appear in payload")
        self.assertEqual(flt(line["amount_allocated"]), 123_456.0)

    def test_create_zero_allocation_is_accepted(self):
        """Zero amount_allocated is a valid initial state (unallocated line)."""
        payload = upsert_budget_line(
            budget_name=self.budget.name,
            budget_line_name="Zero Allocation Line",
            amount_allocated=0,
            program=self.program.name,
        )
        self.assertIn("Zero Allocation Line", self._line_names_in_payload(payload))

    # ── 2. Happy path: edit ───────────────────────────────────────────────────

    def test_edit_updates_existing_line_no_duplicate(self):
        """Passing budget_line_id must update the line, not create a second one."""
        before_count = self._line_count(
            upsert_budget_line(
                budget_name=self.budget.name,
                budget_line_name=self.existing_line.budget_line_name,
                amount_allocated=self.existing_line.amount_allocated,
                program=self.program.name,
                budget_line_id=self.existing_line.name,
            )
        )
        payload = upsert_budget_line(
            budget_name=self.budget.name,
            budget_line_name="Updated Line Name",
            amount_allocated=999_000,
            program=self.program.name,
            budget_line_id=self.existing_line.name,
        )
        after_count = self._line_count(payload)
        self.assertEqual(before_count, after_count, "Edit must not create a duplicate line")

    def test_edit_reflects_new_values_in_payload(self):
        """After an edit, the updated budget_line_name and amount must appear in the payload."""
        payload = upsert_budget_line(
            budget_name=self.budget.name,
            budget_line_name="Edited Name",
            amount_allocated=777_777,
            program=self.program.name,
            budget_line_id=self.existing_line.name,
        )
        updated = self._find_line_by_name(payload, "Edited Name")
        self.assertIsNotNone(updated, "Updated line must appear under new name")
        self.assertEqual(flt(updated["amount_allocated"]), 777_777.0)

    def test_edit_persists_to_database(self):
        """The change must be committed: re-fetching the doc must reflect the edit."""
        upsert_budget_line(
            budget_name=self.budget.name,
            budget_line_name="Persisted Edit",
            amount_allocated=555_000,
            program=self.program.name,
            budget_line_id=self.existing_line.name,
        )
        doc = frappe.get_doc("Budget Line", self.existing_line.name)
        self.assertEqual(doc.budget_line_name, "Persisted Edit")
        self.assertEqual(flt(doc.amount_allocated), 555_000.0)

    # ── 3. Validation: budget_line_name missing ───────────────────────────────

    def test_blank_budget_line_name_raises_validation_error(self):
        """budget_line_name='  ' (blank) must raise frappe.ValidationError."""
        with self.assertRaises(frappe.ValidationError):
            upsert_budget_line(
                budget_name=self.budget.name,
                budget_line_name="   ",
                amount_allocated=100_000,
            )

    def test_empty_budget_line_name_raises_validation_error(self):
        """budget_line_name='' (empty string) must raise frappe.ValidationError."""
        with self.assertRaises(frappe.ValidationError):
            upsert_budget_line(
                budget_name=self.budget.name,
                budget_line_name="",
                amount_allocated=100_000,
            )

    # ── 4. Validation: negative amount_allocated ──────────────────────────────

    def test_negative_amount_raises_validation_error(self):
        """amount_allocated < 0 must raise frappe.ValidationError."""
        with self.assertRaises(frappe.ValidationError):
            upsert_budget_line(
                budget_name=self.budget.name,
                budget_line_name="Negative Line",
                amount_allocated=-1,
            )

    def test_large_negative_amount_raises_validation_error(self):
        """Ensure no sign bypass: -999_999 must also raise ValidationError."""
        with self.assertRaises(frappe.ValidationError):
            upsert_budget_line(
                budget_name=self.budget.name,
                budget_line_name="Large Negative Line",
                amount_allocated=-999_999,
            )

    # ── 5. Permission: non-owner user ─────────────────────────────────────────

    def test_non_owner_raises_permission_error(self):
        """A user without Budget write permission must receive frappe.PermissionError."""
        # Create a minimal test user with no special roles (only 'All')
        test_email = f"nobudget_{self._hash}@example.com"
        if not frappe.db.exists("User", test_email):
            user = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": test_email,
                    "first_name": "NoBudget",
                    "last_name": "Tester",
                    "send_welcome_email": 0,
                    "roles": [],
                }
            ).insert(ignore_permissions=True)

        try:
            frappe.set_user(test_email)
            with self.assertRaises(frappe.PermissionError):
                upsert_budget_line(
                    budget_name=self.budget.name,
                    budget_line_name="Forbidden Line",
                    amount_allocated=100_000,
                )
        finally:
            frappe.set_user("Administrator")

    # ── 6. Guard: Approved budget ─────────────────────────────────────────────

    def test_approved_budget_blocks_create(self):
        """upsert_budget_line must raise ValidationError if the budget is Approved."""
        approved_budget = _make_budget(
            self.entity, self.plan.name, f"{self._hash}_apr",
            status="Approved", version_no=2,
        )
        with self.assertRaises(frappe.ValidationError):
            upsert_budget_line(
                budget_name=approved_budget.name,
                budget_line_name="Blocked Line",
                amount_allocated=100_000,
            )

    def test_submitted_budget_blocks_create(self):
        """upsert_budget_line must raise ValidationError if the budget is Submitted."""
        submitted_budget = _make_budget(
            self.entity, self.plan.name, f"{self._hash}_sub",
            status="Submitted", version_no=3,
        )
        with self.assertRaises(frappe.ValidationError):
            upsert_budget_line(
                budget_name=submitted_budget.name,
                budget_line_name="Blocked Line",
                amount_allocated=100_000,
            )

    def test_approved_budget_blocks_edit(self):
        """Editing an existing line is also blocked when the budget is Approved."""
        approved_budget = _make_budget(
            self.entity, self.plan.name, f"{self._hash}_apred",
            status="Approved", version_no=4,
        )
        locked_line = _make_line(
            approved_budget.name, self.entity, f"{self._hash}_apred",
            strategic_plan=self.plan.name,
            program=self.program.name,
        )
        with self.assertRaises(frappe.ValidationError):
            upsert_budget_line(
                budget_name=approved_budget.name,
                budget_line_name="Updated Blocked",
                amount_allocated=50_000,
                budget_line_id=locked_line.name,
            )
