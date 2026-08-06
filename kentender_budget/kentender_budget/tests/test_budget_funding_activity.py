# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-07 Funding Activity service contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_funding_activity import list_funding_activity
from kentender_budget.services.budget_permissions import ensure_budget_roles


class TestBudgetFundingActivity(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def test_list_active_fixture_activity_and_balances(self):
		dto = list_funding_activity("MOH-BUD-2027-2028")
		self.assertEqual(dto["budget"]["code"], "MOH-BUD-2027-2028")
		self.assertEqual(dto["budget"]["status"], "Active")
		self.assertTrue(dto["capabilities"]["read_only"])
		self.assertEqual(dto["capabilities"]["primary_action"], "request_revision")
		self.assertEqual(dto["capabilities"]["primary_label"], "Request revision")

		bal = dto["balances"]
		self.assertEqual(flt(bal["reserved"]), 145_000_000)
		self.assertEqual(flt(bal["committed"]), 310_000_000)
		self.assertEqual(flt(bal["actual"]), 180_000_000)
		self.assertEqual(flt(bal["outstanding"]), 130_000_000)
		self.assertEqual(bal["reserved_display"], "KES 145,000,000")
		self.assertEqual(bal["committed_display"], "KES 310,000,000")
		self.assertEqual(bal["actual_display"], "KES 180,000,000")
		self.assertEqual(bal["outstanding_display"], "KES 130,000,000")
		self.assertEqual(bal["actual_status"], "Stale")

		# Shared site may retain non-fixture test reservations; pack rows must still be present.
		self.assertGreaterEqual(dto["row_count"], 3)
		by_code = {r["code"]: r for r in dto["rows"]}

		rsv = by_code["RSV-MOH-0001"]
		self.assertEqual(rsv["activity_type"], "reservation")
		self.assertEqual(rsv["activity_label"], "Funding reservation")
		self.assertEqual(rsv["source_code"], "DMD-MOH-2027-014")
		self.assertEqual(rsv["source_name"], "National digital health infrastructure upgrade")
		self.assertEqual(flt(rsv["amount"]), 455_000_000)
		self.assertEqual(rsv["amount_display"], "KES 455,000,000")
		self.assertEqual(rsv["status"], "Partially converted")
		self.assertEqual(rsv["related_value"], "KES 145,000,000")
		self.assertEqual(rsv["action_label"], "View reservation")

		com = by_code["COM-MOH-2027-005"]
		self.assertEqual(com["activity_type"], "commitment")
		self.assertEqual(com["source_code"], "CTR-MOH-2027-005")
		self.assertEqual(com["source_name"], "Digital health infrastructure implementation contract")
		self.assertEqual(flt(com["amount"]), 310_000_000)
		self.assertEqual(com["status"], "Active")
		self.assertEqual(com["action_label"], "View contract")

		exp = by_code["EXP-MOH-2027-005-01"]
		self.assertEqual(exp["activity_type"], "actual")
		self.assertEqual(exp["source_name"], "Finance system")
		self.assertEqual(flt(exp["amount"]), 180_000_000)
		self.assertEqual(exp["status"], "Stale")
		self.assertEqual(exp["amount_display"], "KES 180,000,000")
		self.assertNotEqual(exp["amount_display"], "KES 0")
		self.assertEqual(exp["action_label"], "View reconciliation")

	def test_non_double_count_reservation_and_commitment(self):
		dto = list_funding_activity("MOH-BUD-2027-2028")
		by_code = {r["code"]: r for r in dto["rows"]}
		remaining = flt(dto["balances"]["reserved"])
		committed = flt(dto["balances"]["committed"])
		original = flt(by_code["RSV-MOH-0001"]["amount"])
		# Pack §9.3: remaining reserved + commitment = original reservation.
		self.assertEqual(remaining + committed, original)
		self.assertEqual(remaining + committed, 455_000_000)

	def test_no_duplicate_rsv_codes_in_activity_rows(self):
		"""BUD-SUP-005 — Activity projects domain rows only (no audit double-count)."""
		dto = list_funding_activity("MOH-BUD-2027-2028")
		codes = [r["code"] for r in dto["rows"]]
		self.assertEqual(len(codes), len(set(codes)))
		self.assertEqual(codes.count("RSV-MOH-0001"), 1)

	def test_pe_scope_denial(self):
		email = "budget.activity.pe.deny@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Activity",
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
				list_funding_activity("MOH-BUD-2027-2028")
		finally:
			frappe.set_user("Administrator")
