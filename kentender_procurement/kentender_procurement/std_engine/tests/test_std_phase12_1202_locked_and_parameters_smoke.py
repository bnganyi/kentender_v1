# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CURSOR-1202 — std_engine_works_locked_section_tests + std_engine_works_parameter_tests."""

from __future__ import annotations

import unittest

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.boq_instance_service import add_boq_bill
from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.services.template_version_structure_service import (
	build_std_template_version_structure_tree,
)
from kentender_procurement.std_engine.tests.phase12_smoke_helpers import (
	BUILDING_TEMPLATE_VERSION_CODE,
	doc1_building_seed_loaded,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


@unittest.skipUnless(doc1_building_seed_loaded(), "DOC1 Works Building seed not loaded on this site")
class TestStdEngineWorksLockedSectionTests(IntegrationTestCase):
	def test_itt_section_locked_and_tree_hint(self):
		out = build_std_template_version_structure_tree(BUILDING_TEMPLATE_VERSION_CODE)
		self.assertTrue(out.get("ok"))
		itt = None
		for part in out.get("parts") or []:
			for sec in part.get("sections") or []:
				if str(sec.get("section_code") or "") == "DOC1-WORKS-SECTION-I-ITT":
					itt = sec
					break
			if itt:
				break
		self.assertTrue(itt, msg="ITT section DOC1-WORKS-SECTION-I-ITT missing from structure tree")
		self.assertEqual(itt.get("editability"), "Locked")
		self.assertTrue(itt.get("itt_locked_hint"), msg="ITT locked hint expected for ITT section")

	def test_gcc_section_locked_and_tree_hint(self):
		out = build_std_template_version_structure_tree(BUILDING_TEMPLATE_VERSION_CODE)
		self.assertTrue(out.get("ok"))
		gcc = None
		for part in out.get("parts") or []:
			for sec in part.get("sections") or []:
				if str(sec.get("section_code") or "") == "DOC1-WORKS-SECTION-VIII-GCC":
					gcc = sec
					break
			if gcc:
				break
		self.assertTrue(gcc, msg="GCC section DOC1-WORKS-SECTION-VIII-GCC missing from structure tree")
		self.assertEqual(gcc.get("editability"), "Locked")
		self.assertTrue(gcc.get("gcc_locked_hint"), msg="GCC locked hint expected for GCC section")

	def test_tds_section_parameter_only(self):
		edit = frappe.db.get_value(
			"STD Section Definition",
			{"section_code": "DOC1-WORKS-SECTION-II-TDS"},
			"editability",
		)
		self.assertEqual(edit, "Parameter Only")

	def test_scc_section_parameter_only(self):
		edit = frappe.db.get_value(
			"STD Section Definition",
			{"section_code": "DOC1-WORKS-SECTION-IX-SCC"},
			"editability",
		)
		self.assertEqual(edit, "Parameter Only")


class TestStdEngineWorksParameterTests(_Phase7Fixture):
	"""std_engine_works_parameter_tests — uses PH6 instance fixture (no DOC1 seed required)."""

	_param_code = "STD-PARAM-PH12-REQ"

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if frappe.db.exists("STD Parameter Definition", {"parameter_code": self._param_code}):
			name = frappe.db.get_value("STD Parameter Definition", {"parameter_code": self._param_code}, "name")
			frappe.delete_doc("STD Parameter Definition", name, force=True, ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "STD Parameter Definition",
				"parameter_code": self._param_code,
				"version_code": self.version_code,
				"section_code": self.section_code,
				"label": "Phase12 smoke required parameter",
				"parameter_group": "Smoke",
				"data_type": "String",
				"required": 1,
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in frappe.get_all(
			"STD Instance Parameter Value",
			filters={"instance_code": self.instance_code, "parameter_code": self._param_code},
			pluck="name",
		):
			frappe.delete_doc("STD Instance Parameter Value", name, force=True, ignore_permissions=True)
		pn = frappe.db.get_value("STD Parameter Definition", {"parameter_code": self._param_code}, "name")
		if pn:
			frappe.delete_doc("STD Parameter Definition", pn, force=True, ignore_permissions=True)
		super().tearDown()

	def test_missing_required_parameter_blocks_readiness(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		res = run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		self.assertEqual(res["status"], "Blocked")
		codes = {f["rule_code"] for f in res["findings"]}
		self.assertIn("R_REQUIRED_PARAMETER", codes)
		self.assertTrue(any(self._param_code in (f.get("message") or "") for f in res["findings"]))

	def test_published_instance_boq_mutation_denied(self):
		name = frappe.db.get_value("STD Instance", {"instance_code": self.instance_code}, "name")
		frappe.flags.std_transition_service_context = True
		try:
			frappe.db.set_value("STD Instance", name, "instance_status", "Published Locked")
		finally:
			frappe.flags.std_transition_service_context = False
		try:
			with self.assertRaises(ValidationError) as ctx:
				add_boq_bill(
					self.instance_code,
					{"bill_number": "99", "bill_title": "Blocked", "bill_type": "Work Items", "order_index": 99},
					"Administrator",
				)
			self.assertIn("Published BOQ edit denied", str(ctx.exception))
		finally:
			frappe.db.set_value("STD Instance", name, "instance_status", "Draft")


@unittest.skipUnless(doc1_building_seed_loaded(), "DOC1 Works Building seed not loaded on this site")
class TestStdEngineWorksTenderSecurityDependency(IntegrationTestCase):
	def test_tender_security_dependency_row_exists(self):
		n = frappe.db.count(
			"STD Parameter Dependency",
			{"version_code": BUILDING_TEMPLATE_VERSION_CODE},
		)
		self.assertGreaterEqual(n, 1, msg="Expected at least one STD Parameter Dependency for tender security chain")
