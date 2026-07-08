# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0100 — Tender STD Instance aggregate persistence and validation.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_std_inst_aggregate_0100
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.instance import (
	instance_status_occupies_tender_slot,
)


class TestStdInstAggregate0100(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tm2_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-0100 Test Tender"
		doc.tender_reference = "STDINST0100-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("TM2 Tender", name):
			frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)

	def _new_std_instance(self, tender_name: str, *, tender_context: bool = True):
		si = frappe.new_doc("Tender STD Instance")
		si.tm2_tender = tender_name
		si.template_version_code = "STDTV-WORKS-BUILDING-REV-APR-2022"
		si.applicability_profile_code = "WORKS-PROFILE-BUILDING-CIVIL-REV-APR-2022"
		si.procurement_category = "WORKS"
		si.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		si.instance_status = "Draft"
		si.readiness_status = "Not Ready"
		si.created_from_tender_context = 1 if tender_context else 0
		return si

	def test_std_inst_0100_insert_happy_path(self) -> None:
		tender = self._minimal_tm2_tender()
		si_name = None
		try:
			si = self._new_std_instance(tender)
			si.insert(ignore_permissions=True)
			si_name = si.name
			self.assertTrue(si.name.startswith("STDINST-"))
			row = frappe.db.get_value(
				"Tender STD Instance",
				si_name,
				["tm2_tender", "instance_status", "created_from_tender_context"],
				as_dict=True,
			)
			self.assertEqual(row.tm2_tender, tender)
			self.assertEqual(row.instance_status, "Draft")
			self.assertEqual(row.created_from_tender_context, 1)
		finally:
			if si_name and frappe.db.exists("Tender STD Instance", si_name):
				frappe.delete_doc("Tender STD Instance", si_name, force=True, ignore_permissions=True)
			self._delete_tender(tender)

	def test_std_inst_0100_rejects_without_tender_context(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = self._new_std_instance(tender, tender_context=False)
			with self.assertRaises(frappe.ValidationError):
				si.insert(ignore_permissions=True)
		finally:
			self._delete_tender(tender)

	def test_std_inst_0100_rejects_second_active_instance_same_tender(self) -> None:
		tender = self._minimal_tm2_tender()
		first_name = None
		try:
			si1 = self._new_std_instance(tender)
			si1.insert(ignore_permissions=True)
			first_name = si1.name
			si2 = self._new_std_instance(tender)
			with self.assertRaises(frappe.ValidationError):
				si2.insert(ignore_permissions=True)
		finally:
			if first_name and frappe.db.exists("Tender STD Instance", first_name):
				frappe.delete_doc("Tender STD Instance", first_name, force=True, ignore_permissions=True)
			self._delete_tender(tender)

	def test_std_inst_0100_tm2_tender_immutable(self) -> None:
		t_a = self._minimal_tm2_tender()
		t_b = self._minimal_tm2_tender()
		first_name = None
		try:
			si = self._new_std_instance(t_a)
			si.insert(ignore_permissions=True)
			first_name = si.name
			si.tm2_tender = t_b
			with self.assertRaises(frappe.ValidationError):
				si.save(ignore_permissions=True)
		finally:
			if first_name and frappe.db.exists("Tender STD Instance", first_name):
				frappe.delete_doc("Tender STD Instance", first_name, force=True, ignore_permissions=True)
			self._delete_tender(t_a)
			self._delete_tender(t_b)

	def test_std_inst_0100_second_instance_after_superseded(self) -> None:
		tender = self._minimal_tm2_tender()
		first_name = None
		second_name = None
		try:
			si1 = self._new_std_instance(tender)
			si1.insert(ignore_permissions=True)
			first_name = si1.name
			si1.instance_status = "Superseded"
			si1.save(ignore_permissions=True)

			si2 = self._new_std_instance(tender)
			si2.insert(ignore_permissions=True)
			second_name = si2.name
			self.assertNotEqual(second_name, first_name)
		finally:
			for nm in (second_name, first_name):
				if nm and frappe.db.exists("Tender STD Instance", nm):
					frappe.delete_doc("Tender STD Instance", nm, force=True, ignore_permissions=True)
			self._delete_tender(tender)

	def test_std_inst_0100_invalid_instance_status(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = self._new_std_instance(tender)
			si.instance_status = "Not A Real Status"
			with self.assertRaises(frappe.ValidationError):
				si.insert(ignore_permissions=True)
		finally:
			self._delete_tender(tender)

	def test_slot_helper_superseded_releases(self) -> None:
		self.assertFalse(instance_status_occupies_tender_slot("Superseded"))
		self.assertFalse(instance_status_occupies_tender_slot("Cancelled"))
		self.assertTrue(instance_status_occupies_tender_slot("Draft"))

	def test_std_inst_0100_active_slot_column_tracks_status(self) -> None:
		tender = self._minimal_tm2_tender()
		first_name = None
		try:
			si = self._new_std_instance(tender)
			si.insert(ignore_permissions=True)
			first_name = si.name
			slot = frappe.db.get_value("Tender STD Instance", si.name, "active_tender_slot")
			self.assertEqual(slot, tender)

			si.instance_status = "Superseded"
			si.save(ignore_permissions=True)
			slot_after = frappe.db.get_value("Tender STD Instance", si.name, "active_tender_slot")
			self.assertFalse(slot_after)
		finally:
			if first_name and frappe.db.exists("Tender STD Instance", first_name):
				frappe.delete_doc("Tender STD Instance", first_name, force=True, ignore_permissions=True)
			self._delete_tender(tender)
