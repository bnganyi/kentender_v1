# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B7 — planning handoff ``configuration_json`` (doc 2 sec. 14–15).

Run:
	bench --site <site> run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_planning_tender_handoff_configuration_b7
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_procurement.tender_management.services.release_procurement_package_to_tender import (
	release_procurement_package_to_tender,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestPlanningTenderHandoffConfigurationB7(_ReleaseProcurementPackageHandoffFixtures):
	def test_b7_release_does_not_call_sample_config_loaders(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		with patch(
			"kentender_procurement.tender_management.services.std_template_engine.load_sample_config"
		) as m_cfg:
			with patch(
				"kentender_procurement.tender_management.services.std_template_engine.populate_sample_tender"
			) as m_pop:
				out = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out.get("ok"), out)
		m_cfg.assert_not_called()
		m_pop.assert_not_called()

	def test_b7_configuration_excludes_sample_demo_strings(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		pkg.reload()

		out = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out.get("ok"), out)
		tn = out.get("tender")
		self.assertTrue(tn)
		self._created.append(("Procurement Tender", tn))

		raw = frappe.db.get_value("Procurement Tender", tn, "configuration_json") or ""
		lower = raw.lower()
		for needle in (
			"county government of kisiwa",
			"mwangaza ward",
			"construction of ward administration block",
		):
			with self.subTest(needle=needle):
				self.assertNotIn(needle, lower, "handoff must not hydrate sample_tender demo copy")
		cfg = json.loads(raw)
		if "DATES.PUBLICATION_DATE" in cfg:
			self.assertNotEqual(cfg.get("DATES.PUBLICATION_DATE"), "2026-06-01")

	def test_b7_inherited_title_reference_and_estimated_cost(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		pkg.reload()

		out = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out.get("ok"), out)
		tn = out["tender"]
		self._created.append(("Procurement Tender", tn))

		cfg = json.loads(frappe.db.get_value("Procurement Tender", tn, "configuration_json") or "{}")
		self.assertEqual(cfg.get("TENDER.TENDER_NAME"), pkg.package_name)
		ref = (pkg.package_code or "").strip() or f"REL-{pkg.name[:12]}"
		self.assertEqual(cfg.get("TENDER.TENDER_REFERENCE"), ref)
		ev = flt(pkg.estimated_value)
		if ev > 0:
			self.assertEqual(cfg.get("TENDER.ESTIMATED_COST"), ev)

	def test_b7_new_tender_validation_and_preview_posture(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		out = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out.get("ok"), out)
		tn = out["tender"]
		self._created.append(("Procurement Tender", tn))

		row = frappe.db.get_value(
			"Procurement Tender",
			tn,
			["validation_status", "generated_tender_pack_html"],
			as_dict=True,
		)
		self.assertEqual(row.validation_status, "Not Validated")
		self.assertFalse((row.generated_tender_pack_html or "").strip())

	def test_b7_procurement_category_follows_template(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		out = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out.get("ok"), out)
		self._created.append(("Procurement Tender", out["tender"]))
		pc = frappe.db.get_value("Procurement Tender", out["tender"], "procurement_category")
		self.assertEqual(pc, "GOODS")
