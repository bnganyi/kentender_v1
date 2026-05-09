# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0500 — ``Tender STD Instance Snapshot``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_std_inst_snapshot_0500
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
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService
from kentender_procurement.tender_management.std_instance.snapshot import (
	StdInstanceSnapshotService,
	assert_final_publication_snapshot_exists,
)


class TestStdInstSnapshot0500(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		for snap_name in frappe.get_all("Tender STD Instance Snapshot", pluck="name"):
			tsi = frappe.db.get_value("Tender STD Instance Snapshot", snap_name, "tender_std_instance")
			if tsi and not frappe.db.exists("Tender STD Instance", tsi):
				frappe.delete_doc(
					"Tender STD Instance Snapshot",
					snap_name,
					force=True,
					ignore_permissions=True,
				)
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-0500 Test Tender"
		doc.tender_reference = "STDINST0500-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"procurement_tender": tender_name},
			pluck="name",
		):
			for snap_name in frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Instance Snapshot",
					snap_name,
					force=True,
					ignore_permissions=True,
				)
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

	def test_std_inst_0500_configuration_snapshot(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			snap = StdInstanceSnapshotService.create_configuration_snapshot(
				si.name,
				"Pre-approval configuration baseline",
			)
			self.assertEqual(snap.snapshot_type, "Configuration")
			self.assertEqual(snap.snapshot_status, "Final")
			self.assertTrue(snap.parameter_values_hash)
			self.assertTrue(snap.complete_instance_hash)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0500_publication_snapshot_and_assert(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			iname = si.name
			for fn in (
				StdInstanceGeneratedOutputService.generate_bundle,
				StdInstanceGeneratedOutputService.generate_dsm,
				StdInstanceGeneratedOutputService.generate_dom,
				StdInstanceGeneratedOutputService.generate_dem,
				StdInstanceGeneratedOutputService.generate_dcm,
			):
				out = fn(iname)
				StdInstanceGeneratedOutputService.publish_output(out.name)

			inst = frappe.get_doc("Tender STD Instance", iname)
			pub = StdInstanceSnapshotService.create_publication_snapshot(
				iname,
				"Tender publication gate",
			)
			self.assertEqual(pub.snapshot_type, "Publication")
			self.assertEqual(pub.ref_bundle_output, inst.current_bundle_output_code)
			self.assertEqual(pub.ref_dsm_output, inst.current_dsm_output_code)
			self.assertEqual(pub.ref_dom_output, inst.current_dom_output_code)
			self.assertEqual(pub.ref_dem_output, inst.current_dem_output_code)
			self.assertEqual(pub.ref_dcm_output, inst.current_dcm_output_code)
			self.assertTrue(pub.boq_hash)

			assert_final_publication_snapshot_exists(iname)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0500_final_snapshot_immutable(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			snap = StdInstanceSnapshotService.create_configuration_snapshot(
				si.name,
				"Lock test",
			)
			doc = frappe.get_doc("Tender STD Instance Snapshot", snap.name)
			doc.parameter_values_hash = "tampered"
			with self.assertRaises(frappe.ValidationError):
				doc.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)
