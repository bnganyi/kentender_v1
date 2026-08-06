# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-10 Downstream Usage service contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_downstream_contracts import (
	get_budget_usage,
	list_downstream_usage,
)
from kentender_budget.services.budget_permissions import ensure_budget_roles


class TestBudgetDownstreamUsage(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def test_list_seeded_lineage_row_pack_93(self):
		dto = list_downstream_usage("MOH-BUD-0001")
		self.assertEqual(dto["budget"]["code"], "MOH-BUD-0001")
		self.assertTrue(dto["capabilities"]["read_only"])
		self.assertEqual(dto["capabilities"]["primary_action"], "request_revision")
		self.assertEqual(dto["capabilities"]["primary_label"], "Request revision")
		self.assertEqual(dto["row_count"], 1)

		row = dto["rows"][0]
		self.assertEqual(row["code"], "RSV-MOH-0001")
		self.assertEqual(row["demand_code"], "DMD-MOH-2027-014")
		self.assertEqual(row["plan_item_code"], "PPI-MOH-2027-021")
		self.assertEqual(row["tender_code"], "TND-MOH-2027-008")
		self.assertEqual(row["contract_code"], "CTR-MOH-2027-005")
		self.assertEqual(flt(row["reserved_balance"]), 145_000_000)
		self.assertEqual(flt(row["commitment"]), 310_000_000)
		self.assertEqual(row["reserved_balance_display"], "KES 145,000,000")
		self.assertEqual(row["commitment_display"], "KES 310,000,000")
		self.assertNotIn("145M", row["reserved_balance_display"])
		self.assertEqual(row["status"], "Partially converted")
		self.assertEqual(row["action_label"], "View reservation")
		# Pack §9.3: remaining reserved + commitment = original reservation.
		self.assertEqual(flt(row["reserved_balance"]) + flt(row["commitment"]), 455_000_000)

	def test_get_budget_usage_alias(self):
		a = list_downstream_usage("MOH-BUD-0001")
		b = get_budget_usage("MOH-BUD-0001")
		self.assertEqual(a["row_count"], b["row_count"])
		self.assertEqual(a["rows"][0]["code"], b["rows"][0]["code"])

	def test_empty_budget_without_reservations(self):
		dto = list_downstream_usage("MOH-BUD-0002")
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
				list_downstream_usage("MOH-BUD-0001")
		finally:
			frappe.set_user("Administrator")
