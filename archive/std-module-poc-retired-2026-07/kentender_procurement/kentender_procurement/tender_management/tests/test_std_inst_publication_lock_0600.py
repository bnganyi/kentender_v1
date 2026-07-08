# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0600 — publication/approval lock service."""

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
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.publication_lock import StdPublicationLockService
from kentender_procurement.tender_management.std_instance.snapshot import StdInstanceSnapshotService
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService


class TestStdInstPublicationLock0600(IntegrationTestCase):
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
		doc.tender_title = "STDINST-0600 Test Tender"
		doc.tender_reference = "STDINST0600-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

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
				frappe.delete_doc("Tender STD Instance Snapshot", snap_name, force=True, ignore_permissions=True)
			for out_name in frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc("Tender STD Generated Output", out_name, force=True, ignore_permissions=True)
			for boq_name in frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc("Tender STD Instance BOQ", boq_name, force=True, ignore_permissions=True)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def _prepare_publication_ready_instance(self, instance_name: str) -> None:
		for fn in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			out = fn(instance_name)
			StdInstanceGeneratedOutputService.publish_output(out.name)
		StdInstanceSnapshotService.create_publication_snapshot(instance_name, "Publication lock test snapshot")

	def test_std_inst_0600_lock_for_approval_sets_metadata(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			si = StdInstanceStateService.apply_transition(si.name, "In Configuration", ignore_permissions=True)
			si = StdInstanceStateService.apply_transition(si.name, "Ready for Publication", ignore_permissions=True)
			locked = StdPublicationLockService.lock_for_approval(si.name)
			self.assertEqual(locked.instance_status, "Locked for Approval")
			self.assertTrue(locked.locked_for_approval_at)
			self.assertTrue(locked.locked_for_approval_by)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0600_assert_editable_denies_locked_for_approval(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			si = StdInstanceStateService.apply_transition(si.name, "In Configuration", ignore_permissions=True)
			si = StdInstanceStateService.apply_transition(si.name, "Ready for Publication", ignore_permissions=True)
			StdPublicationLockService.lock_for_approval(si.name)

			with self.assertRaises(frappe.ValidationError):
				StdPublicationLockService.assert_editable(si.name, operation_label="change inputs")
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0600_lock_for_publication_requires_snapshot(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			si = StdInstanceStateService.apply_transition(si.name, "In Configuration", ignore_permissions=True)
			si = StdInstanceStateService.apply_transition(si.name, "Ready for Publication", ignore_permissions=True)
			StdPublicationLockService.lock_for_approval(si.name)

			with self.assertRaises(frappe.ValidationError):
				StdPublicationLockService.lock_for_publication(si.name)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0600_lock_for_publication_sets_metadata(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			si = StdInstanceStateService.apply_transition(si.name, "In Configuration", ignore_permissions=True)
			si = StdInstanceStateService.apply_transition(si.name, "Ready for Publication", ignore_permissions=True)
			self._prepare_publication_ready_instance(si.name)
			StdPublicationLockService.lock_for_approval(si.name)
			locked = StdPublicationLockService.lock_for_publication(si.name)

			self.assertEqual(locked.instance_status, "Published Locked")
			self.assertTrue(locked.published_locked_at)
			self.assertTrue(locked.published_locked_by)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0600_published_mutation_requires_addendum(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			si = StdInstanceStateService.apply_transition(si.name, "In Configuration", ignore_permissions=True)
			si = StdInstanceStateService.apply_transition(si.name, "Ready for Publication", ignore_permissions=True)
			self._prepare_publication_ready_instance(si.name)
			StdPublicationLockService.lock_for_approval(si.name)
			StdPublicationLockService.lock_for_publication(si.name)

			with self.assertRaisesRegex(frappe.ValidationError, "addendum workflow"):
				StdInstanceParameterService.set_parameter_value(
					si.name,
					"submission_deadline",
					"2026-12-31",
				)
		finally:
			self._cleanup_tender(tender)
