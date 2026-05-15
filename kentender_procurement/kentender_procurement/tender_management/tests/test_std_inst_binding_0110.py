# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0110 — TenderStdBindingService (TM2 Tender).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_std_inst_binding_0110
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_governance import STATUS_IMPORTED
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestStdInstBinding0110(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _mk_tm2_with_std_template(self) -> str:
		plan = self._mk_plan()
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tc = f"TND-STD0110-{frappe.generate_hash(length=6)}"
		doc = frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_code": tc,
				"tender_title": "STDINST-0110 Test TM2",
				"procurement_package": pkg.name,
				"procurement_plan": plan.name,
				"procurement_category": "Works",
				"procurement_method": "Open Tender",
				"tender_visibility": "Public",
				"std_template": TEMPLATE_CODE,
			}
		).insert(ignore_permissions=True)
		self._created.append(("TM2 Tender", doc.name))
		return doc.name

	def _delete_std_instances_for_tm2(self, tm2_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)

	def test_std_inst_0110_create_and_get_current(self) -> None:
		tm2 = self._mk_tm2_with_std_template()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tm2,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self.assertTrue(si.name)
			self.assertEqual(si.created_from_tender_context, 1)
			self.assertEqual((si.tm2_tender or "").strip(), tm2)
			cur = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2)
			self.assertIsNotNone(cur)
			self.assertEqual(cur.name, si.name)
		finally:
			self._delete_std_instances_for_tm2(tm2)

	def test_std_inst_0110_duplicate_create_denied(self) -> None:
		tm2 = self._mk_tm2_with_std_template()
		try:
			TenderStdBindingService.create_std_instance_for_tm2_tender(
				tm2,
				ignore_permissions=True,
				record_template_usage=False,
			)
			with self.assertRaises(frappe.ValidationError):
				TenderStdBindingService.create_std_instance_for_tm2_tender(
					tm2,
					ignore_permissions=True,
					record_template_usage=False,
				)
		finally:
			self._delete_std_instances_for_tm2(tm2)

	def test_std_inst_0110_missing_tender(self) -> None:
		with self.assertRaises(frappe.DoesNotExistError):
			TenderStdBindingService.create_std_instance_for_tm2_tender(
				"NONEXISTENT-TM2-STDINST0110",
				ignore_permissions=True,
				record_template_usage=False,
			)

	def test_std_inst_0110_inactive_template_denied(self) -> None:
		tm2 = self._mk_tm2_with_std_template()
		try:
			frappe.db.set_value("STD Template", TEMPLATE_CODE, "lifecycle_status", STATUS_IMPORTED)
			with self.assertRaises(frappe.ValidationError):
				TenderStdBindingService.create_std_instance_for_tm2_tender(
					tm2,
					ignore_permissions=True,
					record_template_usage=False,
				)
			out = TenderStdBindingService.validate_tm2_tender_std_binding(tm2)
			self.assertFalse(out.get("ok"))
			self.assertFalse(out.get("eligible"))
			self.assertTrue(out.get("reasons"))
		finally:
			seed_std_template_governance_for_existing_works_poc(force_mode="active")
			self._delete_std_instances_for_tm2(tm2)

	def test_std_inst_0110_validate_shape_ok(self) -> None:
		tm2 = self._mk_tm2_with_std_template()
		try:
			out = TenderStdBindingService.validate_tm2_tender_std_binding(tm2)
			self.assertIn("ok", out)
			self.assertIn("eligible", out)
			self.assertIn("current_std_instance", out)
			self.assertEqual(out["tm2_tender"], tm2)
			self.assertEqual(out["std_template"], TEMPLATE_CODE)
		finally:
			self._delete_std_instances_for_tm2(tm2)

	def test_std_inst_0110_replace_through_supersession(self) -> None:
		tm2 = self._mk_tm2_with_std_template()
		old_name = None
		new_name = None
		try:
			first = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tm2,
				ignore_permissions=True,
				record_template_usage=False,
			)
			old_name = first.name
			second = TenderStdBindingService.replace_std_instance_through_supersession_for_tm2(
				tm2,
				ignore_permissions=True,
				record_template_usage=False,
			)
			new_name = second.name
			self.assertNotEqual(old_name, new_name)

			cur = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2)
			self.assertIsNotNone(cur)
			self.assertEqual(cur.name, new_name)

			sup = frappe.db.get_value(
				"Tender STD Instance",
				old_name,
				["instance_status", "superseded_by_instance_code"],
				as_dict=True,
			)
			self.assertEqual(sup.instance_status, "Superseded")
			self.assertEqual(sup.superseded_by_instance_code, new_name)
		finally:
			for nm in (new_name, old_name):
				if nm and frappe.db.exists("Tender STD Instance", nm):
					frappe.delete_doc("Tender STD Instance", nm, force=True, ignore_permissions=True)

	def test_std_inst_0110_created_instance_has_active_slot_key(self) -> None:
		tm2 = self._mk_tm2_with_std_template()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tm2,
				ignore_permissions=True,
				record_template_usage=False,
			)
			slot = frappe.db.get_value("Tender STD Instance", si.name, "active_tender_slot")
			self.assertEqual(slot, tm2)
		finally:
			self._delete_std_instances_for_tm2(tm2)
