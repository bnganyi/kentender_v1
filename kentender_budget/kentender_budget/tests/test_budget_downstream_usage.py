# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-10 / BUD-CHG-001 §12 `get_funding_lineage` service contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.budget_activity_test_fixture import (
	TEST_CONTRACT_CODE,
	TEST_DEMAND_CODE,
	TEST_PLAN_ITEM_CODE,
	TEST_RSV_CODE,
	TEST_TENDER_CODE,
	upsert_budget_activity_test_fixture,
)
from kentender_budget.services.budget_downstream_contracts import get_funding_lineage
from kentender_budget.services.budget_permissions import ensure_budget_roles


class TestBudgetDownstreamUsage(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_budget_activity_test_fixture()

	def test_list_seeded_lineage_row_pack_93(self):
		dto = get_funding_lineage("MOH-BUD-2027-2028")
		self.assertEqual(dto["budget"]["code"], "MOH-BUD-2027-2028")
		self.assertTrue(dto["capabilities"]["read_only"])
		self.assertEqual(dto["capabilities"]["primary_action"], "request_revision")
		self.assertEqual(dto["capabilities"]["primary_label"], "Request revision")
		self.assertGreaterEqual(dto["row_count"], 1)
		row = next(r for r in dto["rows"] if r["code"] == TEST_RSV_CODE)
		self.assertEqual(row["demand_code"], TEST_DEMAND_CODE)
		self.assertEqual(row["plan_item_code"], TEST_PLAN_ITEM_CODE)
		self.assertEqual(row["tender_code"], TEST_TENDER_CODE)
		self.assertEqual(row["contract_code"], TEST_CONTRACT_CODE)
		self.assertEqual(flt(row["reserved_balance"]), 145_000_000)
		self.assertEqual(flt(row["commitment"]), 310_000_000)
		self.assertEqual(row["reserved_balance_display"], "KES 145,000,000")
		self.assertEqual(row["commitment_display"], "KES 310,000,000")
		self.assertNotIn("145M", row["reserved_balance_display"])
		self.assertEqual(row["status"], "Partially converted")
		self.assertEqual(row["action_label"], "View reservation")
		# Pack §9.3: remaining reserved + commitment = original reservation.
		self.assertEqual(flt(row["reserved_balance"]) + flt(row["commitment"]), 455_000_000)

	def test_empty_budget_without_reservations(self):
		dto = get_funding_lineage("MOH-BUD-0002")
		self.assertEqual(dto["budget"]["code"], "MOH-BUD-0002")
		self.assertEqual(dto["row_count"], 0)
		self.assertEqual(dto["rows"], [])

	def test_pe_scope_denial(self):
		email = "budget.downstream.pe.deny@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Downstream",
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
				get_funding_lineage("MOH-BUD-2027-2028")
		finally:
			frappe.set_user("Administrator")
