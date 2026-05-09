# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0300 — WorksBoqCompletionService.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_boq_0300
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

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


class TestWorksCompBoq0300(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_procurement_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0300 Test Tender"
		doc.tender_reference = "WORKSCOMP0300-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_std_instances_for_tender(self, tender: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"procurement_tender": tender},
			pluck="name",
		):
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

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("Procurement Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def _codes(self, out: dict) -> list[str]:
		return [b["code"] for b in out.get("blockers") or []]

	def _minimal_valid_payload(self) -> dict:
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

	def test_works_comp_0300_zero_quantity_normal_fails_validation(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			p = self._minimal_valid_payload()
			p["bills"][0]["items"][0]["quantity"] = 0
			with self.assertRaises(frappe.ValidationError):
				WorksBoqCompletionService.save_boq(si.name, p)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0300_validate_missing_boq(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = WorksBoqCompletionService.validate_boq(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("BOQ_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0300_save_validate_happy_path(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_payload())
			out = WorksBoqCompletionService.validate_boq(si.name)
			self.assertTrue(out["valid"], out)
			boq = frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": si.name},
				pluck="name",
			)
			self.assertEqual(len(boq), 1)
			doc = frappe.get_doc("Tender STD Instance BOQ", boq[0])
			self.assertEqual(len(doc.boq_bills or []), 1)
			self.assertEqual(len(doc.boq_items or []), 1)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0300_duplicate_item_number_blocked(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			p = self._minimal_valid_payload()
			p["bills"][0]["items"].append(
				{
					"item_number": "1.1",
					"description": "Other scope",
					"unit": "m2",
					"quantity": 50,
					"item_type": "Normal",
					"supplier_input_mode": "Rate Only",
				}
			)
			with self.assertRaises(frappe.ValidationError):
				WorksBoqCompletionService.save_boq(si.name, p)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0300_prohibited_field_throws(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			p = self._minimal_valid_payload()
			p["header"]["supplier_rate"] = 99
			with self.assertRaises(frappe.ValidationError):
				WorksBoqCompletionService.save_boq(si.name, p)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0300_import_boq_delegates(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.import_boq(si.name, {"boq": self._minimal_valid_payload()})
			out = WorksBoqCompletionService.validate_boq(si.name)
			self.assertTrue(out["valid"], out)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0300_import_csv_format(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			csv_text = "item_number,description,unit,quantity\n2.1,CSV row,m2,50\n"
			WorksBoqCompletionService.import_boq(si.name, {"format": "csv", "csv_text": csv_text})
			out = WorksBoqCompletionService.validate_boq(si.name)
			self.assertTrue(out["valid"], out)
			boq = frappe.get_all("Tender STD Instance BOQ", filters={"tender_std_instance": si.name}, pluck="name")
			self.assertTrue(boq)
			full = frappe.get_doc("Tender STD Instance BOQ", boq[0])
			descs = [(r.description or "") for r in (full.boq_items or [])]
			self.assertTrue(any("CSV row" in d for d in descs))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0300_get_boq_summary(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			summary = WorksBoqCompletionService.get_boq_summary(si.name)
			self.assertFalse(summary.get("has_boq"))
			self.assertEqual(summary.get("bill_count"), 0)

			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_payload())
			summary2 = WorksBoqCompletionService.get_boq_summary(si.name)
			self.assertTrue(summary2.get("has_boq"))
			self.assertEqual(summary2.get("bill_count"), 1)
			self.assertEqual(summary2.get("item_count"), 1)
			self.assertIn("header", summary2)
			self.assertIn("validation", summary2)
			self.assertTrue(summary2["validation"]["valid"])
		finally:
			self._delete_tender(tender)
