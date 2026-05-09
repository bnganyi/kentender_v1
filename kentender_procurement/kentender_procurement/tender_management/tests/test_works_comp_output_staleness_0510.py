# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0510 — WorksOutputStalenessService + STD_OUTPUTS_STALED audit.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_output_staleness_0510
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
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_OUTPUTS_STALED
from kentender_procurement.tender_management.std_instance.parameter import (
	StdInstanceParameterService,
	parse_outputs_stale_flags,
)
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.output_staleness import (
	WorksOutputStalenessService,
)


class TestWorksCompOutputStaleness0510(IntegrationTestCase):
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
		doc.tender_title = "WORKS-COMP-0510 Test Tender"
		doc.tender_reference = "WORKSCOMP0510-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_std_instances_for_tender(self, tender: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"procurement_tender": tender},
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

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("Procurement Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def _minimal_boq_payload(self) -> dict:
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

	def test_works_comp_0510_parameter_mapping_matches_pack(self) -> None:
		self.assertEqual(
			WorksOutputStalenessService.get_stale_outputs_for_parameter_code("submission_deadline"),
			frozenset({"Bundle", "DSM", "DOM"}),
		)
		self.assertEqual(
			WorksOutputStalenessService.get_stale_outputs_for_parameter_code("tender_security_amount"),
			frozenset({"Bundle", "DSM", "DEM"}),
		)
		self.assertEqual(
			WorksOutputStalenessService.get_stale_outputs_for_parameter_code("site_visit_required"),
			frozenset({"Bundle", "DSM", "DEM", "DCM"}),
		)
		self.assertEqual(
			WorksOutputStalenessService.get_stale_outputs_for_parameter_code("margin_of_preference_applicable"),
			frozenset({"Bundle", "DSM", "DEM"}),
		)
		self.assertEqual(
			WorksOutputStalenessService.get_stale_outputs_for_parameter_code("scc.retention_percentage"),
			frozenset({"Bundle", "DCM"}),
		)
		self.assertEqual(
			WorksOutputStalenessService.get_boq_change_stale_outputs(),
			frozenset({"Bundle", "DSM", "DEM", "DCM"}),
		)

	def test_works_comp_0510_parameter_change_emits_outputs_staled_audit(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			base = frappe.db.count(
				"Audit Event",
				{"event_type": EVT_STDINST_OUTPUTS_STALED, "document_name": si.name},
			)
			StdInstanceParameterService.set_parameter_value(
				si.name,
				"submission_deadline",
				"2026-12-31 10:00:00",
			)
			after = frappe.db.count(
				"Audit Event",
				{"event_type": EVT_STDINST_OUTPUTS_STALED, "document_name": si.name},
			)
			self.assertEqual(after, base + 1)
			inst = frappe.get_doc("Tender STD Instance", si.name)
			flags = parse_outputs_stale_flags(inst)
			self.assertIn("Bundle", flags)
			self.assertIn("DSM", flags)
			self.assertIn("DOM", flags)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0510_boq_save_emits_outputs_staled(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			base = frappe.db.count(
				"Audit Event",
				{"event_type": EVT_STDINST_OUTPUTS_STALED, "document_name": si.name},
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_boq_payload())
			after = frappe.db.count(
				"Audit Event",
				{"event_type": EVT_STDINST_OUTPUTS_STALED, "document_name": si.name},
			)
			# BOQ save may call staleness merge more than once (header / bills / items paths).
			self.assertGreater(after, base, msg=f"expected STD_OUTPUTS_STALED audit rows, base={base} after={after}")
		finally:
			self._delete_tender(tender)

	def test_works_comp_0510_readiness_blocked_when_stale_flags_present(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_boq_payload())
			out = StdInstanceReadinessService.evaluate(si.name, persist=True)
			codes = [b["code"] for b in out.get("blockers") or []]
			self.assertIn("STALE_OUTPUTS_PRESENT", codes)
		finally:
			self._delete_tender(tender)
