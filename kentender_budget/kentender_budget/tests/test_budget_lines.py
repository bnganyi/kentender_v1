# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-04 / BUD-UI-05 Budget Lines + Line Editor service contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_line_contracts import (
	get_budget_line,
	list_budget_lines,
	save_budget_line,
)
from kentender_budget.services.budget_permissions import ensure_budget_roles


class TestBudgetLines(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def test_list_active_fixture_two_lines(self):
		dto = list_budget_lines("MOH-BUD-0001")
		self.assertEqual(dto["budget"]["code"], "MOH-BUD-0001")
		self.assertEqual(dto["budget"]["status"], "Active")
		self.assertEqual(dto["line_count"], 2)
		self.assertEqual(len(dto["lines"]), 2)
		self.assertFalse(dto["capabilities"]["can_edit_lines"])
		self.assertEqual(dto["capabilities"]["primary_action"], "request_revision")

		by_code = {r["code"]: r for r in dto["lines"]}
		l1 = by_code["MOH-BL-0001"]
		self.assertEqual(l1["title"], "Digital clinical systems infrastructure")
		self.assertEqual(flt(l1["approved"]), 480_000_000)
		self.assertEqual(flt(l1["reserved"]), 145_000_000)
		self.assertEqual(flt(l1["committed"]), 310_000_000)
		self.assertEqual(flt(l1["available"]), 25_000_000)
		self.assertEqual(l1["approved_display"], "KES 480,000,000")
		self.assertEqual(l1["actual_display"], "KES 180,000,000")
		self.assertEqual(l1["actual_freshness"], "Stale")
		self.assertEqual(l1["status_label"], "Needs attention")
		self.assertEqual(l1["action"], "review")
		self.assertEqual(l1["primary_target_code"], "MOH-TGT-0001")

		l2 = by_code["MOH-BL-0002"]
		self.assertEqual(l2["title"], "Digital health technical capability")
		self.assertEqual(flt(l2["approved"]), 80_000_000)
		self.assertEqual(l2["actual_display"], "Unknown")
		self.assertEqual(l2["actual_freshness"], "Unknown")
		self.assertEqual(l2["status_label"], "Complete")
		self.assertIn("No commitments", l2["attention"])
		self.assertEqual(l2["action"], "view")

	def test_get_line_editor_dto_and_pvc(self):
		line = get_budget_line("MOH-BL-0001")
		self.assertEqual(line["code"], "MOH-BL-0001")
		self.assertEqual(line["external_financial_line_reference"], "HLTH-INF-2027-004")
		self.assertEqual(line["classification"], "Capital expenditure")
		self.assertTrue(line["capabilities"]["read_only"])
		self.assertFalse(line["capabilities"]["can_save"])
		self.assertEqual(len(line["supporting_targets"]), 1)
		self.assertEqual(line["supporting_targets"][0]["code"], "MOH-TGT-0002")
		self.assertTrue(line["supporting_targets"][0]["reason"])
		self.assertEqual(len(line["value_treatments"]), 4)
		codes = {t["code"] for t in line["value_treatments"]}
		self.assertEqual(codes, {"PVO-EFT-01", "PVO-ECO-01", "PVO-RES-01", "PVO-SUS-02"})
		eco = next(t for t in line["value_treatments"] if t["code"] == "PVO-ECO-01")
		self.assertEqual(eco["treatment"], "Dedicated allocation")
		self.assertEqual(flt(eco["dedicated_amount"]), 40_000_000)
		self.assertEqual(flt(line["dedicated_total"]), 40_000_000)
		self.assertEqual(flt(line["not_dedicated"]), 440_000_000)

	def test_active_save_denied(self):
		with self.assertRaises(frappe.PermissionError):
			save_budget_line(
				{
					"budget": "MOH-BUD-0001",
					"line": "MOH-BL-0001",
					"title": "Should not save",
					"organisational_owner": "Head, ICT Infrastructure",
					"classification": "Capital expenditure",
					"funding_source_type": "Exchequer",
					"funding_source_name": "Government of Kenya Development Budget",
					"approved_amount": 480_000_000,
					"primary_target": {"code": "MOH-TGT-0001", "name": "Target"},
					"value_treatments": [],
				}
			)

	def test_draft_save_dedicated_over_approved_fails(self):
		pe = self.seed["procuring_entity"]
		# Isolate a Draft budget for edit tests.
		for name in frappe.get_all(
			"Budget",
			filters={
				"procuring_entity": pe,
				"fiscal_period": "2046/47",
				"status": ["in", ["Draft", "Submitted", "Returned", "Active"]],
			},
			pluck="name",
		):
			for ln in frappe.get_all("Budget Line", filters={"budget": name}, pluck="name"):
				frappe.delete_doc("Budget Line", ln, force=True, ignore_permissions=True)
			frappe.delete_doc("Budget", name, force=True, ignore_permissions=True)

		draft = frappe.get_doc(
			{
				"doctype": "Budget",
				"generated_reference": "MOH-BUD-TEST-LINES",
				"title": "Draft lines edit test",
				"procuring_entity": pe,
				"fiscal_period": "2046/47",
				"start_date": "2046-07-01",
				"end_date": "2047-06-30",
				"currency": "KES",
				"budget_owner": "Budget Officer",
				"registration_source": "Direct capture",
				"authoritative_reference": "MOH-TEST-LINES",
				"approval_date": "2046-06-01",
				"external_approved_total": 100_000_000,
				"approval_evidence": "/files/test.pdf",
				"status": "Draft",
			}
		)
		draft.insert(ignore_permissions=True)

		result = save_budget_line(
			{
				"budget": draft.generated_reference,
				"title": "Over dedicated line",
				"organisational_owner": "Head, ICT",
				"classification": "Capital expenditure",
				"funding_source_type": "Exchequer",
				"funding_source_name": "Exchequer",
				"approved_amount": 50_000_000,
				"primary_target": {
					"code": "MOH-TGT-0001",
					"name": "Availability target",
				},
				"value_treatments": [
					{
						"code": "PVO-ECO-01",
						"name": "Whole-life cost",
						"requirement_level": "Required",
						"treatment": "Dedicated allocation",
						"dedicated_amount": 60_000_000,
						"rationale": "Too much",
					}
				],
			}
		)
		self.assertFalse(result["ok"])
		self.assertIn("dedicated_total", result["errors"])

	def _ensure_draft_budget(self, pe: str, code: str = "MOH-BUD-TEST-LINES") -> str:
		name = frappe.db.get_value("Budget", {"generated_reference": code}, "name")
		if name:
			doc = frappe.get_doc("Budget", name)
			if doc.status != "Draft":
				frappe.db.set_value("Budget", name, "status", "Draft")
			return code
		frappe.get_doc(
			{
				"doctype": "Budget",
				"generated_reference": code,
				"title": "Draft lines edit test",
				"procuring_entity": pe,
				"fiscal_period": "2046/47",
				"start_date": "2046-07-01",
				"end_date": "2047-06-30",
				"currency": "KES",
				"budget_owner": "Budget Officer",
				"registration_source": "Direct capture",
				"authoritative_reference": "MOH-TEST-LINES",
				"approval_date": "2046-06-01",
				"external_approved_total": 100_000_000,
				"approval_evidence": "/files/test.pdf",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		return code

	def test_draft_save_round_trip(self):
		pe = self.seed["procuring_entity"]
		budget_code = self._ensure_draft_budget(pe)

		result = save_budget_line(
			{
				"budget": budget_code,
				"title": "Editable draft line",
				"organisational_owner": "Head, ICT",
				"classification": "Services",
				"funding_source_type": "Exchequer",
				"funding_source_name": "Exchequer",
				"approved_amount": 50_000_000,
				"primary_target": {
					"code": "MOH-TGT-0001",
					"name": "Availability target",
				},
				"supporting_targets": [],
				"value_treatments": [
					{
						"code": "PVO-EFT-01",
						"name": "Efficiency",
						"requirement_level": "Required",
						"treatment": "Embedded in line",
						"dedicated_amount": 0,
						"rationale": "Included",
					},
					{
						"code": "PVO-ECO-01",
						"name": "Whole-life cost",
						"requirement_level": "Required",
						"treatment": "Dedicated allocation",
						"dedicated_amount": 10_000_000,
						"rationale": "Dedicated slice",
					},
				],
			}
		)
		self.assertTrue(result.get("ok"), result)
		line = result["line"]
		self.assertTrue(line["code"].startswith("MOH-BL-"))
		self.assertNotEqual(line["code"], "MOH-BL-0001")
		self.assertEqual(line["title"], "Editable draft line")
		self.assertEqual(len(line["supporting_targets"]), 0)
		self.assertEqual(line.get("primary_target_code") or (line.get("primary_target") or {}).get("code"), "MOH-TGT-0001")
		self.assertEqual(flt(line["dedicated_total"]), 10_000_000)
		self.assertTrue(line["capabilities"]["can_save"])

	def test_pe_scope_denial(self):
		email = "bud.viewer.lines@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "BudLines",
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			)
			user.insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		user.add_roles("Budget Viewer")
		# No PE permission → scoped list should fail.
		frappe.db.delete("User Permission", {"user": email, "allow": "Procuring Entity"})
		frappe.set_user(email)
		try:
			with self.assertRaises(frappe.PermissionError):
				list_budget_lines("MOH-BUD-0001")
		finally:
			frappe.set_user("Administrator")
