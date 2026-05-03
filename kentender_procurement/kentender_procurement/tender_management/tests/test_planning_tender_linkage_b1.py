# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning-to-tender B1 — Procurement Tender lineage fields and validate rules.

Run:
	bench --site <site> run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_planning_tender_linkage_b1
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase


class TestPlanningTenderLinkageB1(IntegrationTestCase):
	def test_b1_meta_has_planning_handoff_fields(self) -> None:
		meta = frappe.get_meta("Procurement Tender")
		names = {df.fieldname for df in meta.fields}
		for fn in (
			"procurement_plan",
			"procurement_package",
			"procurement_template",
			"source_package_code",
			"source_package_hash",
			"source_demand_count",
			"source_budget_line_count",
			"source_package_snapshot_json",
		):
			with self.subTest(field=fn):
				self.assertIn(fn, names, f"B1: Procurement Tender must define {fn}")
		self.assertEqual(meta.get_field("procurement_plan").options, "Procurement Plan")
		self.assertEqual(meta.get_field("procurement_package").options, "Procurement Package")
		self.assertEqual(meta.get_field("procurement_template").options, "Procurement Template")
		snap = meta.get_field("source_package_snapshot_json")
		self.assertIsNotNone(snap)
		self.assertEqual(snap.fieldtype, "Code")
		self.assertEqual(snap.options, "JSON")

	def test_b1_plan_mismatch_raises_validation_error(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.procurement_package = "PKG-B1-TEST"
		doc.procurement_plan = "PLAN-WRONG"

		orig = frappe.db.get_value

		def gv(doctype, name, fieldname, *args, **kwargs):
			if (
				doctype == "Procurement Package"
				and name == "PKG-B1-TEST"
				and fieldname == "plan_id"
			):
				return "PLAN-EXPECTED"
			return orig(doctype, name, fieldname, *args, **kwargs)

		with patch.object(frappe.db, "get_value", side_effect=gv):
			with self.assertRaises(frappe.ValidationError):
				doc.validate()

	def test_b1_autofills_procurement_plan_from_package(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.procurement_package = "PKG-B1-AUTO"
		doc.procurement_plan = None

		orig = frappe.db.get_value

		def gv(doctype, name, fieldname, *args, **kwargs):
			if (
				doctype == "Procurement Package"
				and name == "PKG-B1-AUTO"
				and fieldname == "plan_id"
			):
				return "PLAN-AUTOFILLED"
			return orig(doctype, name, fieldname, *args, **kwargs)

		with patch.object(frappe.db, "get_value", side_effect=gv):
			doc.validate()
		self.assertEqual(doc.procurement_plan, "PLAN-AUTOFILLED")

	def test_b1_no_package_skips_lineage_logic(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.procurement_plan = None
		doc.procurement_package = None
		doc.validate()
