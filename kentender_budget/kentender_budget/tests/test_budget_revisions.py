# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-08 Budget Revisions — create/list/submit + AC-016 floor."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_budget.services.budget_revision_contracts import (
	create_budget_revision,
	get_budget_revision_create_context,
	list_budget_revisions,
	submit_budget_revision,
)


class TestBudgetRevisions(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def test_list_includes_seeded_draft(self):
		dto = list_budget_revisions("MOH-BUD-0001")
		self.assertEqual(dto["budget"]["code"], "MOH-BUD-0001")
		self.assertEqual(dto["budget"]["status"], "Active")
		self.assertTrue(dto["capabilities"]["can_create"])
		by_code = {r["code"]: r for r in dto["rows"]}
		self.assertIn("BR-MOH-0001", by_code)
		seed = by_code["BR-MOH-0001"]
		self.assertEqual(seed["status"], "Draft")
		self.assertEqual(flt(seed["change_total"]), 25_000_000)
		self.assertEqual(seed["change_total_display"], "+ KES 25,000,000")

	def test_create_context_floors_and_money(self):
		ctx = get_budget_revision_create_context("MOH-BUD-0001")
		self.assertEqual(ctx["budget"]["status"], "Active")
		by_code = {r["code"]: r for r in ctx["lines"]}
		bl = by_code["MOH-BL-0001"]
		self.assertEqual(flt(bl["before_amount"]), 480_000_000)
		self.assertEqual(bl["before_display"], "KES 480,000,000")
		self.assertEqual(flt(bl["reserved"]), 145_000_000)
		self.assertEqual(flt(bl["committed"]), 310_000_000)
		self.assertEqual(flt(bl["floor"]), 455_000_000)
		self.assertEqual(ctx["impact"]["before_display"], "KES 560,000,000")
		self.assertGreaterEqual(ctx["impact"]["affected_demands"], 1)

	def test_create_draft_ok(self):
		result = create_budget_revision(
			{
				"budget": "MOH-BUD-0001",
				"external_approval_reference": "MOF/TEST/REV-01",
				"approval_date": "2027-12-01",
				"effective_date": "2027-12-15",
				"reason": "Test draft uplift",
				"lines": [
					{"budget_line": "MOH-BL-0001", "change_amount": 10_000_000},
					{"budget_line": "MOH-BL-0002", "change_amount": 0},
				],
			}
		)
		self.assertTrue(result.get("ok"), result)
		rev = result["revision"]
		self.assertEqual(rev["status"], "Draft")
		self.assertTrue(str(rev["code"]).startswith("BR-MOH-"))
		self.assertEqual(flt(rev["impact"]["change_total"]), 10_000_000)
		self.assertEqual(rev["impact"]["change_display"], "+ KES 10,000,000")
		self.assertEqual(rev["impact"]["after_display"], "KES 570,000,000")

	def test_ac016_denies_below_floor(self):
		# Floor for MOH-BL-0001 is 455M; before 480M → max reduce 25M.
		result = create_budget_revision(
			{
				"budget": "MOH-BUD-0001",
				"reason": "Illegal cut",
				"lines": [
					{"budget_line": "MOH-BL-0001", "change_amount": -30_000_000},
				],
			}
		)
		self.assertFalse(result.get("ok"))
		self.assertIn("lines", result.get("errors") or {})
		self.assertIn("MOH-BL-0001", result["errors"].get("lines", ""))

	def test_submit_succeeds_without_evidence_and_locks(self):
		saved = create_budget_revision(
			{
				"budget": "MOH-BUD-0001",
				"external_approval_reference": "MOF/TEST/REV-SUB",
				"approval_date": "2027-12-01",
				"effective_date": "2027-12-15",
				"reason": "Submit path",
				"approval_evidence": "",
				"lines": [
					{"budget_line": "MOH-BL-0001", "change_amount": 5_000_000},
				],
			}
		)
		self.assertTrue(saved.get("ok"), saved)
		code = saved["revision"]["code"]

		ok = submit_budget_revision({"revision": code})
		self.assertTrue(ok.get("ok"), ok)
		self.assertEqual(ok["revision"]["status"], "Submitted")
		self.assertEqual(ok["revision"]["submitted_by"], "Administrator")
		self.assertTrue(ok["revision"]["submitted_at"])
		self.assertEqual((ok["revision"].get("approval_evidence") or ""), "")

		# Immutable — cannot edit after submit
		again = create_budget_revision(
			{
				"budget": "MOH-BUD-0001",
				"revision": code,
				"reason": "Try edit",
				"lines": [{"budget_line": "MOH-BL-0001", "change_amount": 1}],
			}
		)
		self.assertFalse(again.get("ok"))
		self.assertIn("status", again.get("errors") or {})

	def test_active_only_create(self):
		result = create_budget_revision(
			{
				"budget": "MOH-BUD-0002",
				"reason": "Not active",
				"lines": [{"budget_line": "MOH-BL-0003", "change_amount": 1_000_000}],
			}
		)
		self.assertFalse(result.get("ok"))
		self.assertIn("budget", result.get("errors") or {})

	def test_pe_scope_denial(self):
		email = "budget.revision.pe.deny@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Revision",
					"last_name": "Deny",
					"send_welcome_email": 0,
					"new_password": "Test@12345",
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Budget Viewer")
		frappe.set_user(email)
		try:
			with self.assertRaises(frappe.PermissionError):
				list_budget_revisions("MOH-BUD-0001")
		finally:
			frappe.set_user("Administrator")
