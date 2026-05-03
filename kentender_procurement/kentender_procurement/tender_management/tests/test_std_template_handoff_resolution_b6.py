# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B6 — STD template handoff resolution (doc 2 sec. 12.1–12.2).

Run:
	bench --site <site> run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_std_template_handoff_resolution_b6
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	filter_std_names_for_planning_category,
	resolve_std_template_for_handoff,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestStdTemplateHandoffResolutionB6(_ReleaseProcurementPackageHandoffFixtures):
	def test_b6_default_std_template_short_circuits_mapping(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		doc = frappe.get_doc("Procurement Package", pkg.name)
		res = resolve_std_template_for_handoff(doc)
		self.assertEqual(res.path, "default_std_template")
		self.assertEqual(res.std_name, TEMPLATE_CODE)

	def test_b6_ambiguous_mapping_fail_closed(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		tpl = self._mk_template()
		frappe.db.set_value("Procurement Template", tpl.name, "default_std_template", None)
		pkg = self._mk_package(plan.name, tpl.name)
		doc = frappe.get_doc("Procurement Package", pkg.name)
		with patch(
			"kentender_procurement.tender_management.services.std_template_handoff_resolution.filter_std_names_for_planning_category",
			return_value=["STD-CAND-A", "STD-CAND-B"],
		):
			res = resolve_std_template_for_handoff(doc)
		self.assertTrue(res.is_ambiguous)
		self.assertIsNone(res.std_name)
		self.assertEqual(res.ambiguous_candidates, ("STD-CAND-A", "STD-CAND-B"))

	def test_b6_works_poc_fallback_when_mapping_empty(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		tpl = self._mk_template()
		frappe.db.set_value("Procurement Template", tpl.name, "default_std_template", None)
		frappe.db.set_value("Procurement Template", tpl.name, "category", "Works")
		pkg = self._mk_package(plan.name, tpl.name)
		frappe.db.set_value("Procurement Package", pkg.name, "procurement_method", "Open Tender")
		frappe.db.set_value("Procurement Package", pkg.name, "contract_type", "Fixed Price")
		doc = frappe.get_doc("Procurement Package", pkg.name)
		with patch(
			"kentender_procurement.tender_management.services.std_template_handoff_resolution.filter_std_names_for_planning_category",
			return_value=[],
		):
			res = resolve_std_template_for_handoff(doc)
		self.assertEqual(res.path, "works_poc_fallback")
		self.assertEqual(res.std_name, TEMPLATE_CODE)

	def test_b6_goods_no_default_no_fallback_is_unresolved(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		tpl = self._mk_template()
		frappe.db.set_value("Procurement Template", tpl.name, "default_std_template", None)
		pkg = self._mk_package(plan.name, tpl.name)
		doc = frappe.get_doc("Procurement Package", pkg.name)
		res = resolve_std_template_for_handoff(doc)
		self.assertEqual(res.path, "unresolved")
		self.assertIsNone(res.std_name)

	def test_b6_invalid_default_link_detected(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		tpl = self._mk_template()
		frappe.db.set_value("Procurement Template", tpl.name, "default_std_template", "STD-NOT-THERE-999")
		frappe.db.commit()
		try:
			pkg = self._mk_package(plan.name, tpl.name)
			doc = frappe.get_doc("Procurement Package", pkg.name)
			res = resolve_std_template_for_handoff(doc)
			self.assertEqual(res.path, "invalid_default")
			self.assertEqual(res.invalid_default_link, "STD-NOT-THERE-999")
			self.assertIsNone(res.std_name)
		finally:
			frappe.db.set_value("Procurement Template", tpl.name, "default_std_template", TEMPLATE_CODE)
			frappe.db.commit()


class TestStdTemplateHandoffResolutionB6Unit(IntegrationTestCase):
	def test_filter_excludes_works_std_for_goods_planning_category(self) -> None:
		upsert_std_template()
		names = [TEMPLATE_CODE]
		goods_filtered = filter_std_names_for_planning_category(names, "Goods")
		self.assertEqual(goods_filtered, [])
		works_filtered = filter_std_names_for_planning_category(names, "Works")
		self.assertEqual(works_filtered, [TEMPLATE_CODE])
