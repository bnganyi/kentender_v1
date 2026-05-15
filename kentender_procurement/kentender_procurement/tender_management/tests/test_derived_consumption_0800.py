# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0800 — ``OutputConsumptionService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_consumption_0800
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_procurement.tender_management.derived_models.common.versioning import (
	DerivedOutputVersioningService,
)
from kentender_procurement.tender_management.derived_models.consumption.output_consumption import (
	CODE_OUTPUT_NOT_FOUND,
	CODE_OUTPUT_NOT_LINKED_TO_SNAPSHOT,
	CODE_OUTPUT_STALE,
	CODE_OUTPUT_SUPERSEDED,
	CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER,
	CODE_PUBLICATION_REQUIRES_PUBLISHED,
	OutputConsumptionService,
)
from kentender_procurement.tender_management.derived_models.orchestration import (
	DerivedModelGenerationService,
)
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_OUTPUT_CONSUMED
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)


class TestDerivedConsumption0800(IntegrationTestCase):
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

	def _final_snapshot(self, si_name: str, tender: str) -> str:
		inst = frappe.get_doc("Tender STD Instance", si_name)
		snap = frappe.new_doc("Tender STD Instance Snapshot")
		snap.tender_std_instance = si_name
		snap.procurement_tender = tender
		snap.snapshot_type = "Configuration"
		snap.snapshot_reason = "DERIVED-0800"
		snap.snapshot_status = "Final"
		snap.source_template_version_code = inst.template_version_code or "TV"
		snap.parameter_values_hash = "pv"
		snap.works_requirements_hash = "wr"
		snap.attachments_hash = "at"
		snap.boq_hash = "bq"
		snap.complete_instance_hash = "ci"
		snap.created_by = frappe.session.user
		snap.created_at = now_datetime()
		snap.insert(ignore_permissions=True)
		return snap.name

	def test_derived_0800_get_current_submission_allows_published_dsm(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0800 DSM"
		doc.tender_reference = "DERIVED0800-DSM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dsm = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			StdInstanceGeneratedOutputService.publish_output(dsm.name)

			res = OutputConsumptionService.get_current_output_for_consumer(si.name, "Submission")
			self.assertTrue(res.get("allowed"))
			self.assertEqual(res.get("output_status"), "Published")
			self.assertEqual(res.get("blockers"), [])
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0800_submission_cannot_consume_dem(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0800 Wrong Type"
		doc.tender_reference = "DERIVED0800-WT"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dem = StdInstanceGeneratedOutputService.generate_dem(si.name)
			StdInstanceGeneratedOutputService.publish_output(dem.name)

			res = OutputConsumptionService.validate_consumption(dem.name, "Submission", None)
			self.assertFalse(res.get("allowed"))
			self.assertEqual(res["blockers"][0]["code"], CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0800_evaluation_cannot_consume_dom(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0800 DOM"
		doc.tender_reference = "DERIVED0800-DOM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dom = StdInstanceGeneratedOutputService.generate_dom(si.name)
			StdInstanceGeneratedOutputService.publish_output(dom.name)

			res = OutputConsumptionService.validate_consumption(dom.name, "Evaluation", None)
			self.assertFalse(res.get("allowed"))
			self.assertEqual(res["blockers"][0]["code"], CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0800_stale_denied(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0800 Stale"
		doc.tender_reference = "DERIVED0800-STALE"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dsm = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			pub = StdInstanceGeneratedOutputService.publish_output(dsm.name)
			DerivedOutputVersioningService.markStale(pub.name, reason="test")

			res = OutputConsumptionService.validate_consumption(pub.name, "Submission", None)
			self.assertFalse(res.get("allowed"))
			self.assertEqual(res["blockers"][0]["code"], CODE_OUTPUT_STALE)
			self.assertEqual(res.get("output_status"), "Stale")
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0800_superseded_denied_without_historical(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0800 Super"
		doc.tender_reference = "DERIVED0800-SUP"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			d1 = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			StdInstanceGeneratedOutputService.publish_output(d1.name)
			d2 = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			StdInstanceGeneratedOutputService.publish_output(d2.name)

			old = frappe.get_doc("Tender STD Generated Output", d1.name)
			self.assertEqual(old.output_status, "Superseded")

			res = OutputConsumptionService.validate_consumption(d1.name, "Submission", None)
			self.assertFalse(res.get("allowed"))
			self.assertEqual(res["blockers"][0]["code"], CODE_OUTPUT_SUPERSEDED)

			ok = OutputConsumptionService.validate_consumption(d1.name, "Submission", "HISTORICAL")
			self.assertTrue(ok.get("allowed"))
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0800_publication_requires_published_bundle(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0800 Pub"
		doc.tender_reference = "DERIVED0800-PUB"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			inst0 = frappe.get_doc("Tender STD Instance", si.name)
			inst0.outputs_stale_flags = ""
			inst0.save(ignore_permissions=True)
			out = DerivedModelGenerationService.generate_output(si.name, "Bundle", publish=False)
			bundle_name = (out.get("outputs") or {}).get("Bundle")
			self.assertTrue(bundle_name)
			row = frappe.get_doc("Tender STD Generated Output", bundle_name)
			self.assertEqual(row.output_status, "Current")

			res = OutputConsumptionService.validate_consumption(bundle_name, "Publication", None)
			self.assertFalse(res.get("allowed"))
			self.assertEqual(res["blockers"][0]["code"], CODE_PUBLICATION_REQUIRES_PUBLISHED)

			pub = StdInstanceGeneratedOutputService.publish_output(bundle_name)
			ok = OutputConsumptionService.validate_consumption(pub.name, "Publication", None)
			self.assertTrue(ok.get("allowed"))
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0800_contract_requires_final_snapshot(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0800 Contract"
		doc.tender_reference = "DERIVED0800-CON"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dcm = StdInstanceGeneratedOutputService.generate_dcm(si.name)
			DerivedOutputVersioningService.markCurrent(dcm.name)
			pub = StdInstanceGeneratedOutputService.publish_output(dcm.name)

			res = OutputConsumptionService.validate_consumption(pub.name, "Contract", None)
			self.assertFalse(res.get("allowed"))
			self.assertEqual(res["blockers"][0]["code"], CODE_OUTPUT_NOT_LINKED_TO_SNAPSHOT)

			snap = self._final_snapshot(si.name, doc.name)
			dcm2 = StdInstanceGeneratedOutputService.generate_dcm(si.name)
			pub2 = DerivedOutputVersioningService.markPublished(dcm2.name, snapshot_code=snap)

			ok = OutputConsumptionService.validate_consumption(pub2.name, "Contract", None)
			self.assertTrue(ok.get("allowed"))
			self.assertEqual(ok.get("snapshot_code"), snap)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0800_record_consumption_audits_when_allowed(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0800 Record"
		doc.tender_reference = "DERIVED0800-REC"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dsm = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			pub = StdInstanceGeneratedOutputService.publish_output(dsm.name)

			with patch(
				"kentender_procurement.tender_management.derived_models.consumption.output_consumption.emit_std_instance_event"
			) as m:
				rec = OutputConsumptionService.record_consumption(
					pub.name,
					"Submission",
					None,
					"test.actor@example.com",
				)
				self.assertTrue(rec.get("ok"))
				m.assert_called_once()
				args, kwargs = m.call_args
				self.assertEqual(args[0], EVT_STDINST_OUTPUT_CONSUMED)
				self.assertEqual(kwargs.get("performed_by"), "test.actor@example.com")

			with self.assertRaises(frappe.ValidationError):
				OutputConsumptionService.record_consumption(pub.name, "Evaluation", None, "Administrator")
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0800_output_not_found_envelope(self) -> None:
		res = OutputConsumptionService.validate_consumption("STD-OUT-NONEXISTENT", "Submission", None)
		self.assertFalse(res.get("allowed"))
		self.assertEqual(res["blockers"][0]["code"], CODE_OUTPUT_NOT_FOUND)
