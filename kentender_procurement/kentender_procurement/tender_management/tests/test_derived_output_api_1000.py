# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-1000 — Whitelisted derived output API (pack §17).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_output_api_1000
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.api.handlers import (
	DERIVED_API_INVALID_OUTPUT_TYPE,
	DERIVED_API_NOT_FOUND,
	DERIVED_API_OUTPUT_NOT_SET,
	std_engine_generate_output,
	std_engine_get_current_output,
	std_engine_get_output,
	std_engine_record_output_consumption,
	std_engine_validate_output_consumption,
)
from kentender_procurement.tender_management.derived_models.consumption.output_consumption import (
	CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER,
)
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)


class TestDerivedOutputApi1000(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			for out_name in frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Generated Output",
					out_name,
					force=True,
					ignore_permissions=True,
				)
			for boq_name in frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Instance BOQ",
					boq_name,
					force=True,
					ignore_permissions=True,
				)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def _minimal_valid_boq_payload(self) -> dict:
		return {
			"header": {"currency": "USD"},
			"bills": [
				{
					"bill_number": "B1",
					"bill_title": "Preliminaries",
					"bill_type": "Standard",
					"order_index": 0,
					"items": [
						{
							"item_number": "1.1",
							"description": "Site clearance",
							"unit": "m2",
							"quantity": 100,
							"item_type": "Normal",
							"supplier_input_mode": "Rate Only",
						},
					],
				},
			],
		}

	def test_1000_invalid_output_type_slug(self) -> None:
		r = std_engine_get_current_output("ANY", "not-a-type")
		self.assertFalse(r["success"])
		self.assertEqual(r["error_code"], DERIVED_API_INVALID_OUTPUT_TYPE)

	def test_1000_get_output_not_found_envelope(self) -> None:
		r = std_engine_get_output("nonexistent-output-code-xyz")
		self.assertFalse(r["success"])
		self.assertEqual(r["error_code"], DERIVED_API_NOT_FOUND)

	def test_1000_get_current_not_set(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-1000 NS"
		doc.tender_reference = "DERIVED1000-NS"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			r = std_engine_get_current_output(si.name, "dem")
			self.assertFalse(r["success"])
			self.assertEqual(r["error_code"], DERIVED_API_OUTPUT_NOT_SET)
		finally:
			self._cleanup_tender(doc.name)

	def test_1000_generate_get_validate_record_flow(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-1000 Flow"
		doc.tender_reference = "DERIVED1000-FLOW"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())

			# Publish so instance pointers and stale flags align (BOQ save may pre-mark DEM stale).
			gen = std_engine_generate_output(si.name, "dem", publish=1)
			self.assertTrue(gen["success"])
			self.assertTrue(gen.get("ok"))
			dem_name = gen["outputs"]["DEM"]

			cur = std_engine_get_current_output(si.name, "DEM")
			self.assertTrue(cur["success"])
			self.assertIn("content_json", cur["output"])
			self.assertEqual(cur["output"]["output_code"], dem_name)
			self.assertEqual(cur["output"]["output_status"], "Published")

			by_code = std_engine_get_output(dem_name)
			self.assertTrue(by_code["success"])
			self.assertEqual(by_code["output"]["output_type"], "DEM")

			val = std_engine_validate_output_consumption(dem_name, "Evaluation", None)
			self.assertTrue(val["success"])
			self.assertTrue(val["allowed"])
			self.assertEqual(val["blockers"], [])

			with patch(
				"kentender_procurement.tender_management.derived_models.consumption.output_consumption.emit_std_instance_event",
			):
				rec = std_engine_record_output_consumption(dem_name, "Evaluation", "EVAL-CTX-1")
			self.assertTrue(rec["success"])
			self.assertTrue(rec["recorded"])
			self.assertEqual(rec["output_code"], dem_name)
		finally:
			self._cleanup_tender(doc.name)

	def test_1000_validate_consumption_wrong_type_envelope(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-1000 WC"
		doc.tender_reference = "DERIVED1000-WC"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dom = std_engine_generate_output(si.name, "dom")
			self.assertTrue(dom["success"])
			dom_name = dom["outputs"]["DOM"]

			val = std_engine_validate_output_consumption(dom_name, "Evaluation", None)
			self.assertTrue(val["success"])
			self.assertFalse(val["allowed"])
			self.assertEqual(val["blockers"][0]["code"], CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER)

			rec = std_engine_record_output_consumption(dom_name, "Evaluation", None)
			self.assertFalse(rec["success"])
			self.assertEqual(rec["error_code"], CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER)
			self.assertIn("message", rec)
		finally:
			self._cleanup_tender(doc.name)
