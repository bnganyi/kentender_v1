# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0800 — WorksAddendumSensitivityService.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_addendum_sensitivity_0800
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
from kentender_procurement.tender_management.std_instance.drawing_register import (
	StdInstanceDrawingRegisterService,
	logical_outputs_from_drawing_row,
)
from kentender_procurement.tender_management.std_instance.parameter import PARAMETER_CODE_TO_STALE_OUTPUTS
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
	logical_outputs_from_row,
)
from kentender_procurement.tender_management.works_completion.services.addendum_sensitivity import (
	WorksAddendumSensitivityService,
)
from kentender_procurement.tender_management.works_completion.services.output_staleness import (
	WorksOutputStalenessService,
)


class TestWorksCompAddendumSensitivity0800(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0800 Test Tender"
		doc.tender_reference = "WORKSCOMP0800-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def test_works_comp_0800_submission_opening_match_staleness_service(self) -> None:
		for ct, pc in (
			("submission_deadline", "submission_deadline"),
			("opening_datetime", "opening_datetime"),
		):
			self.assertEqual(
				WorksAddendumSensitivityService.get_works_addendum_impact(ct),
				WorksOutputStalenessService.get_stale_outputs_for_parameter_code(pc),
			)

	def test_works_comp_0800_boq_alias_and_boq_change(self) -> None:
		self.assertEqual(
			WorksAddendumSensitivityService.get_works_addendum_impact("boq"),
			WorksOutputStalenessService.get_boq_change_stale_outputs(),
		)
		self.assertEqual(
			WorksAddendumSensitivityService.get_works_addendum_impact("boq_change"),
			WorksOutputStalenessService.get_boq_change_stale_outputs(),
		)

	def test_works_comp_0800_scc_value_change_union(self) -> None:
		expected: set[str] = set()
		for pc, fs in PARAMETER_CODE_TO_STALE_OUTPUTS.items():
			if pc == "bid_currency" or pc.startswith("scc."):
				expected |= set(fs)
		self.assertEqual(
			WorksAddendumSensitivityService.get_works_addendum_impact("scc_value_change"),
			frozenset(expected),
		)

	def test_works_comp_0800_evaluation_threshold_specific_parameter(self) -> None:
		self.assertEqual(
			WorksAddendumSensitivityService.get_works_addendum_impact(
				"evaluation_threshold",
				"margin_of_preference_applicable",
			),
			WorksOutputStalenessService.get_stale_outputs_for_parameter_code(
				"margin_of_preference_applicable"
			),
		)

	def test_works_comp_0800_specification_change_uses_row_drives(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceWorksRequirementService.set_works_requirement(
				si.name,
				"COMP0800SPEC",
				structured_text="Spec body",
				drives_bundle=True,
				drives_dcm=True,
				ignore_publication_lock=True,
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			row = next(r for r in doc.works_requirements if r.component_code == "COMP0800SPEC")
			self.assertEqual(
				WorksAddendumSensitivityService.get_works_addendum_impact(
					"specification_change",
					"COMP0800SPEC",
					instance_code=si.name,
				),
				logical_outputs_from_row(row),
			)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0800_specification_default_without_row(self) -> None:
		self.assertEqual(
			WorksAddendumSensitivityService.get_works_addendum_impact("specification_change"),
			frozenset({"Bundle", "DSM", "DEM", "DCM"}),
		)

	def test_works_comp_0800_drawing_change_uses_row(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceDrawingRegisterService.set_drawing_row(
				si.name,
				drawing_code="DWG0800",
				revision="A",
				title="Plan",
				file_reference="/files/x.pdf",
				section_code="DRAWINGS",
				ignore_publication_lock=True,
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			row = StdInstanceDrawingRegisterService.find_row(si.name, "DWG0800", "A")
			self.assertIsNotNone(row)
			self.assertEqual(
				WorksAddendumSensitivityService.get_works_addendum_impact(
					"drawing_change",
					"DWG0800|A",
					instance_code=si.name,
				),
				logical_outputs_from_drawing_row(row),
			)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0800_drawing_default_without_instance(self) -> None:
		self.assertEqual(
			WorksAddendumSensitivityService.get_works_addendum_impact("drawing_change"),
			frozenset({"Bundle", "DEM", "DCM"}),
		)

	def test_works_comp_0800_opening_datetime_tracks_staleness_engine(self) -> None:
		got = WorksAddendumSensitivityService.get_works_addendum_impact("opening_datetime")
		self.assertEqual(got, PARAMETER_CODE_TO_STALE_OUTPUTS["opening_datetime"])
		self.assertIn("DSM", got)

	def test_works_comp_0800_unknown_change_type(self) -> None:
		with self.assertRaises(frappe.ValidationError) as ctx:
			WorksAddendumSensitivityService.get_works_addendum_impact("not_a_real_change_type")
		self.assertIn("WORKS_ADDENDUM_IMPACT_UNKNOWN_CHANGE_TYPE", str(ctx.exception))

	def test_works_comp_0800_unknown_evaluation_parameter(self) -> None:
		with self.assertRaises(frappe.ValidationError) as ctx:
			WorksAddendumSensitivityService.get_works_addendum_impact(
				"evaluation_threshold",
				"not_a_parameter_code_xyz",
			)
		self.assertIn("WORKS_ADDENDUM_IMPACT_UNKNOWN_FIELD", str(ctx.exception))
