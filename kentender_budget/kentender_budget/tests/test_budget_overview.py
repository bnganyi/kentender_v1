# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-03 Budget Overview service contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_contracts import get_budget_overview, register_budget
from kentender_budget.services.budget_permissions import ensure_budget_roles


class TestBudgetOverview(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def test_active_fixture_funding_totals(self):
		ov = get_budget_overview("MOH-BUD-0001")
		self.assertEqual(ov["code"], "MOH-BUD-0001")
		self.assertEqual(ov["status"], "Active")
		self.assertEqual(ov["status_label"], "Active")
		totals = ov["totals"]
		self.assertEqual(flt(totals["approved"]), 560_000_000)
		self.assertEqual(flt(totals["reserved"]), 145_000_000)
		self.assertEqual(flt(totals["committed"]), 310_000_000)
		self.assertEqual(flt(totals["available"]), 105_000_000)
		self.assertEqual(flt(totals["actual"]), 180_000_000)
		self.assertEqual(flt(totals["outstanding"]), 130_000_000)
		self.assertEqual(totals["approved_display"], "KES 560M")
		self.assertEqual(totals["reserved_display"], "KES 145M")
		self.assertEqual(totals["committed_display"], "KES 310M")
		self.assertEqual(totals["available_display"], "KES 105M")
		self.assertEqual(totals["actual_display"], "KES 180M")
		self.assertEqual(totals["outstanding_display"], "KES 130M")
		bar = ov["utilization_bar"]
		self.assertAlmostEqual(bar["reserved_pct"] + bar["committed_pct"] + bar["available_pct"], 100.0, places=1)
		self.assertIn("stale", (ov.get("attention") or {}).get("text", "").lower())

	def test_draft_without_lines_shows_registered_approved(self):
		pe = self.seed["procuring_entity"]
		for name in frappe.get_all(
			"Budget",
			filters={
				"procuring_entity": pe,
				"fiscal_period": "2045/46",
				"status": ["in", ["Draft", "Submitted", "Returned", "Active"]],
			},
			pluck="name",
		):
			frappe.delete_doc("Budget", name, force=True, ignore_permissions=True)

		email = "bud.officer.ov@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "BudOv",
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			)
			user.insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		user.add_roles("Budget Officer")
		frappe.db.delete("User Permission", {"user": email, "allow": "Procuring Entity"})
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": email,
				"allow": "Procuring Entity",
				"for_value": pe,
				"is_default": 1,
			}
		).insert(ignore_permissions=True)

		frappe.set_user(email)
		result = register_budget(
			{
				"title": "Overview draft FY 2045/46",
				"fiscal_period": "2045/46",
				"currency": "KES",
				"budget_owner": "Director, Finance and Accounts",
				"authoritative_reference": "MOH-FIN-BUD-OV-2045",
				"approval_date": "2045-06-15",
				"external_approved_total": "100000",
				"approval_evidence": "",
			}
		)
		self.assertTrue(result.get("ok"), result)
		code = result["budget"]["code"]
		budget_id = result["budget"]["id"]
		self.addCleanup(
			lambda: frappe.delete_doc("Budget", budget_id, force=True, ignore_permissions=True)
			if frappe.db.exists("Budget", budget_id)
			else None
		)

		frappe.set_user("Administrator")
		ov = get_budget_overview(code)
		self.assertEqual(ov["status"], "Draft")
		self.assertEqual(flt(ov["totals"]["approved"]), 100_000)
		self.assertEqual(ov["totals"]["approved_display"], "KES 100,000")
		self.assertEqual(flt(ov["totals"]["reserved"]), 0)
		self.assertEqual(flt(ov["totals"]["committed"]), 0)
		self.assertEqual(flt(ov["totals"]["available"]), 100_000)
		self.assertEqual(flt(ov["totals"]["actual"]), 0)
		self.assertEqual(ov["capabilities"]["primary_action"], "open_lines")

	def test_active_capabilities_request_revision(self):
		ov = get_budget_overview("MOH-BUD-0001")
		self.assertEqual(ov["capabilities"]["primary_action"], "request_revision")
		self.assertTrue(ov["capabilities"]["view_funding_performance"])

	def test_missing_budget_throws(self):
		with self.assertRaises(frappe.DoesNotExistError):
			get_budget_overview("NO-SUCH-BUD-9999")

	def test_pe_scope_denial(self):
		from kentender_core.seeds._common import ensure_procuring_entity

		other_pe = ensure_procuring_entity("PE-OV-OTHER", "Overview Other Entity")
		email = "bud.viewer.ov.deny@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "BudDeny",
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			)
			user.insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		user.add_roles("Budget Viewer")
		frappe.db.delete("User Permission", {"user": email, "allow": "Procuring Entity"})
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": email,
				"allow": "Procuring Entity",
				"for_value": other_pe,
				"is_default": 1,
			}
		).insert(ignore_permissions=True)

		frappe.set_user(email)
		self.addCleanup(lambda: frappe.set_user("Administrator"))
		with self.assertRaises(frappe.PermissionError):
			get_budget_overview("MOH-BUD-0001")
