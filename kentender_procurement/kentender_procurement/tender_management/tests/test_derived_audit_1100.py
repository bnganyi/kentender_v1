# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-1100 — Pack §18 ``DERIVED_MODEL_*`` audit rows on ``Audit Event``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_audit_1100
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial import (
	ManualRuleDenialService,
)
from kentender_procurement.tender_management.derived_models.events.audit import DERIVED_MODEL_ENTITY
from kentender_procurement.tender_management.derived_models.events.codes import (
	ADDENDUM_DERIVED_MODELS_REGENERATED,
	DERIVED_MODEL_CONSUMED,
	DERIVED_MODEL_GENERATED,
	DERIVED_MODEL_GENERATION_REQUESTED,
	MANUAL_SUBMISSION_REQUIREMENT_DENIED,
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
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)


class TestDerivedAudit1100(IntegrationTestCase):
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
			for snap in frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc("Tender STD Instance Snapshot", snap, force=True, ignore_permissions=True)
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

	def _count_derived(self, event_type: str) -> int:
		return frappe.db.count(
			"Audit Event",
			{"event_type": event_type, "entity": DERIVED_MODEL_ENTITY},
		)

	def test_1100_generated_on_insert_draft_output(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-1100 GEN"
		doc.tender_reference = "DERIVED1100-GEN"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			before = self._count_derived(DERIVED_MODEL_GENERATED)
			StdInstanceGeneratedOutputService.generate_bundle(si.name)
			after = self._count_derived(DERIVED_MODEL_GENERATED)
			self.assertGreater(after, before)
		finally:
			self._cleanup_tender(doc.name)

	def test_1100_generation_requested_via_orchestrator(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-1100 REQ"
		doc.tender_reference = "DERIVED1100-REQ"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			before = self._count_derived(DERIVED_MODEL_GENERATION_REQUESTED)
			DerivedModelGenerationService.generate_output(si.name, "DOM")
			after = self._count_derived(DERIVED_MODEL_GENERATION_REQUESTED)
			self.assertGreater(after, before)
		finally:
			self._cleanup_tender(doc.name)

	def test_1100_manual_submission_denial_emits_pack_code(self) -> None:
		before = self._count_derived(MANUAL_SUBMISSION_REQUIREMENT_DENIED)
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_submission_requirement(
				{"requirements": [{"requirement_code": "X", "label": "Bad", "manual_submission_requirement": True}]},
			)
		after = self._count_derived(MANUAL_SUBMISSION_REQUIREMENT_DENIED)
		self.assertGreater(after, before)

	def test_1100_consumption_emits_derived_consumed(self) -> None:
		from kentender_procurement.tender_management.derived_models.consumption.output_consumption import (
			OutputConsumptionService,
		)

		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-1100 CONS"
		doc.tender_reference = "DERIVED1100-CONS"
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
			before = self._count_derived(DERIVED_MODEL_CONSUMED)
			OutputConsumptionService.record_consumption(dsm.name, "Submission", None, None)
			after = self._count_derived(DERIVED_MODEL_CONSUMED)
			self.assertGreater(after, before)
		finally:
			self._cleanup_tender(doc.name)

	def test_1100_addendum_execute_emits_regenerated(self) -> None:
		from unittest.mock import patch

		from kentender_procurement.tender_management.std_instance import addendum as std_addendum

		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-1100 ADD"
		doc.tender_reference = "DERIVED1100-ADD"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			before = self._count_derived(ADDENDUM_DERIVED_MODELS_REGENERATED)
			with patch.object(
				std_addendum.StdAddendumImpactService,
				"analyse_impact",
				return_value={
					"instance": si.name,
					"source_addendum_code": "ADD-1100",
					"affected_outputs": ["Bundle"],
					"requires_supplier_notification": False,
					"requires_addendum_snapshot": True,
					"reasons": [],
				},
			), patch.object(
				std_addendum.StdInstanceSnapshotService,
				"create_addendum_snapshot",
				return_value=type("S", (), {"name": "SNAP-MOCK-1100"})(),
			):
				std_addendum.StdAddendumImpactService.create_regeneration_plan(
					si.name,
					["boq_change"],
					source_addendum_code="ADD-1100",
					execute=True,
					publish_outputs=False,
				)
			after = self._count_derived(ADDENDUM_DERIVED_MODELS_REGENERATED)
			self.assertGreater(after, before)
		finally:
			self._cleanup_tender(doc.name)
