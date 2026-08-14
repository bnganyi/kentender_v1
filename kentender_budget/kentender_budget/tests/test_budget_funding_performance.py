# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-02 Funding Performance — get_funding_performance + export."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.budget_activity_test_fixture import (
	upsert_budget_activity_test_fixture,
)
from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_funding_performance_contracts import (
	DISCLAIMER,
	export_funding_performance,
	get_funding_performance,
)
from kentender_budget.services.budget_permissions import ensure_budget_roles


class TestBudgetFundingPerformance(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def setUp(self):
		upsert_moh_mvp_v1_portfolio()

	def _canonical_coverage(self, dto):
		return [r for r in dto["coverage_rows"] if r.get("budget_code") == "MOH-BUD-2027-2028"]

	def test_moh_strip_totals_full_money(self):
		dto = get_funding_performance()
		canonical = self._canonical_coverage(dto)
		self.assertTrue(canonical)
		self.assertEqual(sum(flt(r["approved"]) for r in canonical), 560_000_000)
		self.assertEqual(sum(flt(r["reserved"]) for r in canonical), 0)
		self.assertEqual(sum(flt(r["committed"]) for r in canonical), 0)
		self.assertEqual(sum(flt(r["available"]) for r in canonical), 560_000_000)
		self.assertGreaterEqual(flt(dto["kpis"]["approved"]), 560_000_000)
		self.assertIn("Ministry of Health", dto["entity"]["name"])
		self.assertTrue(dto["as_at_display"])
		self.assertIn("does not prove", dto["disclaimer"].lower())
		self.assertEqual(dto["disclaimer"], DISCLAIMER)
		self.assertTrue(dto["capabilities"]["can_export"])
		joined = " ".join(r["approved_display"] for r in canonical)
		self.assertNotIn("560M", joined)

	def test_coverage_includes_pack_target_codes(self):
		dto = get_funding_performance()
		codes = {r["target_code"] for r in dto["coverage_rows"]}
		self.assertIn("MOH-TGT-AVAIL-2028", codes)
		self.assertNotIn("MOH-ST-04", codes)
		row = next(r for r in dto["coverage_rows"] if r["target_code"] == "MOH-TGT-AVAIL-2028")
		self.assertIn("KES", row["approved_display"])
		self.assertNotIn("M", row["approved_display"].replace("MOH", ""))
		self.assertEqual(row["action_label"], "View Details")
		joined = " ".join(r["approved_display"] for r in dto["coverage_rows"])
		self.assertNotIn("560M", joined)

	def test_stale_expenditure_exception(self):
		upsert_budget_activity_test_fixture()
		dto = get_funding_performance()
		self.assertGreaterEqual(len(dto["exception_rows"]), 1)
		exc = dto["exception_rows"][0]
		self.assertIn("stale", exc["exception"].lower())
		self.assertTrue(exc["budget_line"])
		self.assertEqual(exc["action"], "review_finance_sync")
		self.assertIn("Review", exc["action_label"])

	def test_filter_by_primary_target(self):
		dto = get_funding_performance(primary_target="MOH-TGT-SKILLS-2029")
		self.assertTrue(dto["coverage_rows"])
		for r in dto["coverage_rows"]:
			self.assertEqual(r["target_code"], "MOH-TGT-SKILLS-2029")
		self.assertEqual(flt(dto["kpis"]["approved"]), 80_000_000)

	def test_filter_by_fiscal_period(self):
		dto = get_funding_performance(fiscal_period="2027/28")
		canonical = self._canonical_coverage(dto)
		self.assertEqual(sum(flt(r["approved"]) for r in canonical), 560_000_000)
		self.assertGreaterEqual(flt(dto["kpis"]["approved"]), 560_000_000)
		empty = get_funding_performance(fiscal_period="2099/00")
		self.assertEqual(flt(empty["kpis"]["approved"]), 0)
		self.assertEqual(empty["coverage_rows"], [])

	def test_export_payload_lineage_and_codes(self):
		exp = export_funding_performance()
		self.assertTrue(exp["lineage"]["as_at_display"])
		self.assertTrue(exp["lineage"]["entity_name"])
		self.assertIn("source_coverage", exp["lineage"])
		codes = {r["target_code"] for r in exp["coverage_rows"]}
		self.assertIn("MOH-TGT-AVAIL-2028", codes)
		canonical = self._canonical_coverage(exp)
		self.assertEqual(sum(flt(r["approved"]) for r in canonical), 560_000_000)

	def test_pe_scope_denial(self):
		email = "budget.perf.pe.deny@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Perf",
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
				get_funding_performance(procuring_entity="PE-MOH")
		finally:
			frappe.set_user("Administrator")
