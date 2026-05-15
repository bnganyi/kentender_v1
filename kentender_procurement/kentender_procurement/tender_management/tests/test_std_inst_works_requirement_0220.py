# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0220 — structured Works Requirements on ``Tender STD Instance``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_std_inst_works_requirement_0220
"""

from __future__ import annotations

import json

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
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)


class TestStdInstWorksRequirement0220(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-0220 Test Tender"
		doc.tender_reference = "STDINST0220-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def test_std_inst_0220_set_and_upsert(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceWorksRequirementService.set_works_requirement(
				si.name,
				"WR-COMP-1",
				structured_text="Scope text",
				requirement_status="In Progress",
				ignore_publication_lock=False,
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual(len(doc.works_requirements), 1)
			self.assertEqual(doc.works_requirements[0].component_code, "WR-COMP-1")

			StdInstanceWorksRequirementService.set_works_requirement(
				si.name,
				"WR-COMP-1",
				structured_text="Updated scope",
				requirement_status="Complete",
				ignore_publication_lock=False,
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual(len(doc.works_requirements), 1)
			self.assertEqual(doc.works_requirements[0].structured_text, "Updated scope")
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0220_validate_attachment_blocking(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceWorksRequirementService.set_works_requirement(
				si.name,
				"WR-COMP-ATT",
				attachment_required=True,
				attachment_status="Missing",
				ignore_publication_lock=False,
			)
			out = StdInstanceWorksRequirementService.validate_works_requirements(si.name)
			self.assertFalse(out["ok"])
			self.assertIn("WR-COMP-ATT", out["blocking"])
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0220_stale_outputs_on_drives_change(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			name = si.name
			doc = frappe.get_doc("Tender STD Instance", name)
			doc.readiness_status = "Ready"
			doc.current_bundle_output_code = "B-1"
			doc.current_dem_output_code = "DEM-1"
			doc.current_dcm_output_code = "DCM-1"
			doc.save(ignore_permissions=True)

			StdInstanceWorksRequirementService.set_works_requirement(
				name,
				"WR-STALE",
				structured_text="v1",
				drives_bundle=True,
				drives_dem=True,
				drives_dcm=True,
				ignore_publication_lock=False,
			)
			StdInstanceWorksRequirementService.set_works_requirement(
				name,
				"WR-STALE",
				structured_text="v2",
				drives_bundle=True,
				drives_dem=True,
				drives_dcm=True,
				ignore_publication_lock=False,
			)
			doc = frappe.get_doc("Tender STD Instance", name)
			flags = parse_outputs_stale_flags(doc)
			self.assertIn("Bundle", flags)
			self.assertIn("DEM", flags)
			self.assertIn("DCM", flags)
			self.assertEqual(doc.readiness_status, "Blocked")
			self.assertIsNone(doc.current_bundle_output_code)
			raw = (doc.outputs_stale_flags or "").strip()
			self.assertIsInstance(json.loads(raw), list)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0220_publication_instance_lock(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			name = si.name
			for target in (
				"In Configuration",
				"Ready for Publication",
				"Locked for Approval",
				"Published Locked",
			):
				si = StdInstanceStateService.apply_transition(name, target, ignore_permissions=True)
				name = si.name
			with self.assertRaises(frappe.ValidationError):
				StdInstanceWorksRequirementService.set_works_requirement(
					name,
					"WR-PUB",
					structured_text="x",
					ignore_publication_lock=False,
				)
			StdInstanceWorksRequirementService.set_works_requirement(
				name,
				"WR-PUB",
				structured_text="x",
				ignore_publication_lock=True,
			)
			doc = frappe.get_doc("Tender STD Instance", name)
			self.assertTrue(any(r.component_code == "WR-PUB" for r in doc.works_requirements))
		finally:
			self._cleanup_tender(tender)
