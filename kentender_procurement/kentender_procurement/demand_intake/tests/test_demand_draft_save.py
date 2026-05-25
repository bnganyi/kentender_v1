# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Draft save — title-only contract without ignore_mandatory (UI refactor §24.1)."""

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demand_intake.services.readiness import (
	assert_draft_save,
	evaluate_draft_save,
)


class TestDemandDraftSave(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		self._demand_names: list[str] = []

	def tearDown(self):
		if getattr(self, "_skipped_no_demand", False):
			return
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)

	def test_evaluate_draft_save_title_only(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		doc = frappe.get_doc({"doctype": "Demand", "title": "Draft only"})
		out = evaluate_draft_save(doc)
		self.assertTrue(out["ready"])
		assert_draft_save(doc)

	def test_insert_title_only_without_ignore_mandatory(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		doc = frappe.get_doc({"doctype": "Demand", "title": f"Title only {frappe.generate_hash(length=4)}"})
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		self.assertEqual(doc.status, "Draft")
		self.assertTrue((doc.title or "").strip())
		self.assertFalse(doc.budget_line)
		self.assertFalse(doc.requesting_department)

	def test_insert_without_title_fails(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		doc = frappe.get_doc({"doctype": "Demand"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)
