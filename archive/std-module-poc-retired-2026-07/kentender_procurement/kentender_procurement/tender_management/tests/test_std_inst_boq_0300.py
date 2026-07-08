# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0300 — ``Tender STD Instance BOQ`` aggregate.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_std_inst_boq_0300
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
from kentender_procurement.tender_management.std_instance.parameter import parse_outputs_stale_flags
from kentender_procurement.tender_management.std_instance.boq import (
	StdInstanceBoqService,
	get_boq_for_instance,
)
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService


class TestStdInstBoq0300(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		# Remove orphan BOQs left when instance docs were deleted without deleting BOQ first.
		for boq_name in frappe.get_all("Tender STD Instance BOQ", pluck="name"):
			tsi = frappe.db.get_value("Tender STD Instance BOQ", boq_name, "tender_std_instance")
			if tsi and not frappe.db.exists("Tender STD Instance", tsi):
				frappe.delete_doc(
					"Tender STD Instance BOQ",
					boq_name,
					force=True,
					ignore_permissions=True,
				)
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-0300 Test Tender"
		doc.tender_reference = "STDINST0300-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
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
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def test_std_inst_0300_create_add_validate(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			boq = StdInstanceBoqService.create_boq_for_instance(si.name, currency="USD")
			self.assertTrue(boq.name)

			self.assertEqual(get_boq_for_instance(si.name).name, boq.name)

			with self.assertRaises(frappe.ValidationError):
				StdInstanceBoqService.create_boq_for_instance(si.name)

			boq = StdInstanceBoqService.add_bill(
				boq.name,
				"1",
				"Preliminaries",
				"PRE",
				order_index=1,
			)
			bill_code = boq.boq_bills[0].bill_instance_code

			boq = StdInstanceBoqService.add_item(
				boq.name,
				bill_code,
				"1.01",
				"Site clearance",
				"m2",
				100.0,
				item_type="Normal",
			)

			out = StdInstanceBoqService.validate_boq(boq.name)
			self.assertTrue(out["ok"])
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0300_stale_outputs_on_change(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.current_bundle_output_code = "B1"
			doc.current_dem_output_code = "DEM1"
			doc.save(ignore_permissions=True)

			boq = StdInstanceBoqService.create_boq_for_instance(si.name)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			flags = parse_outputs_stale_flags(doc)
			self.assertIn("Bundle", flags)
			self.assertIn("DEM", flags)
			self.assertIsNone(doc.current_bundle_output_code)

			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.current_bundle_output_code = "B2"
			doc.save(ignore_permissions=True)
			StdInstanceBoqService.add_bill(boq.name, "2", "Works", "WK")
			doc = frappe.get_doc("Tender STD Instance", si.name)
			self.assertIsNone(doc.current_bundle_output_code)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0300_instance_publication_lock(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			name = si.name
			boq = StdInstanceBoqService.create_boq_for_instance(name)
			for target in (
				"In Configuration",
				"Ready for Publication",
				"Locked for Approval",
				"Published Locked",
			):
				si = StdInstanceStateService.apply_transition(name, target, ignore_permissions=True)
				name = si.name

			with self.assertRaises(frappe.ValidationError):
				StdInstanceBoqService.add_bill(
					boq.name,
					"9",
					"Late bill",
					"X",
					ignore_boq_publication_lock=False,
				)

			StdInstanceBoqService.add_bill(
				boq.name,
				"9",
				"Late bill",
				"X",
				ignore_boq_publication_lock=True,
			)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0300_update_published_item_denied(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			boq = StdInstanceBoqService.create_boq_for_instance(si.name)
			boq = StdInstanceBoqService.add_bill(boq.name, "1", "A", "T")
			bill_code = boq.boq_bills[0].bill_instance_code
			boq = StdInstanceBoqService.add_item(boq.name, bill_code, "1", "Desc", "m", 10.0)
			item_code = boq.boq_items[0].item_instance_code

			doc = frappe.get_doc("Tender STD Instance BOQ", boq.name)
			doc.boq_items[0].status = "Published"
			doc.save(ignore_permissions=True)

			with self.assertRaises(frappe.ValidationError):
				StdInstanceBoqService.update_item_through_draft(
					boq.name,
					item_code,
					description="Changed",
				)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0300_replace_through_addendum(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			boq = StdInstanceBoqService.create_boq_for_instance(si.name)
			v1 = boq.version_number
			boq = StdInstanceBoqService.replace_boq_through_addendum(si.name, "ADDM-BOQ-1")
			self.assertEqual(int(boq.version_number), int(v1) + 1)
			self.assertEqual(boq.source_addendum_code, "ADDM-BOQ-1")
			self.assertEqual(boq.status, "Draft")
		finally:
			self._cleanup_tender(tender)
