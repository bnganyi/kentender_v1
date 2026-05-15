# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1000 — authorization assertions and wiring."""

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
from kentender_procurement.tender_management.std_instance.authorization import StdAuthorizationService
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.publication_lock import StdPublicationLockService
from kentender_procurement.tender_management.std_instance.snapshot import StdInstanceSnapshotService
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService


class TestStdInstAuthorization1000(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _ensure_role(self, role: str) -> None:
		if not frappe.db.exists("Role", role):
			doc = frappe.new_doc("Role")
			doc.role_name = role
			doc.insert(ignore_permissions=True)

	def _ensure_user_with_roles(self, email: str, roles: list[str]) -> str:
		for role in roles:
			self._ensure_role(role)
		if not frappe.db.exists("User", email):
			u = frappe.new_doc("User")
			u.email = email
			u.first_name = email.split("@")[0]
			u.user_type = "System User"
			u.enabled = 1
			u.new_password = "Test@1234"
			u.send_welcome_email = 0
			u.insert(ignore_permissions=True)
		user_doc = frappe.get_doc("User", email)
		user_doc.add_roles(*roles)
		return email

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-1000 Test Tender"
		doc.tender_reference = f"STDINST1000-{frappe.generate_hash(length=8)}"
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
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def _prepare_publication_ready_instance(self, instance_name: str) -> None:
		for fn in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			out = fn(instance_name, ignore_generated_output_lock=True)
			StdInstanceGeneratedOutputService.publish_output(out.name)
		StdInstanceSnapshotService.create_publication_snapshot(instance_name, "STDINST-1000 auth snapshot")

	def test_std_inst_1000_create_allowed_and_denied_by_role(self) -> None:
		officer = self._ensure_user_with_roles("stdinst1000-officer@example.test", ["Procurement Officer"])
		tender = self._minimal_tender()
		try:
			frappe.set_user("Guest")
			with self.assertRaises(frappe.ValidationError):
				TenderStdBindingService.create_std_instance_for_tm2_tender(
					tender, ignore_permissions=True, record_template_usage=False
				)

			frappe.set_user(officer)
			doc = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			self.assertTrue(doc.name)
		finally:
			frappe.set_user("Administrator")
			self._cleanup_tender(tender)

	def test_std_inst_1000_draft_edit_allowed_for_assistant_denied_for_unauthorized(self) -> None:
		assistant = self._ensure_user_with_roles(
			"stdinst1000-assistant@example.test", ["Procurement Assistant"]
		)
		observer = self._ensure_user_with_roles("stdinst1000-observer@example.test", ["Auditor"])
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			frappe.set_user(assistant)
			doc = StdInstanceParameterService.set_parameter_value(
				si.name,
				"submission_deadline",
				"2026-12-31",
			)
			self.assertTrue(doc.name)

			frappe.set_user(observer)
			with self.assertRaises(frappe.ValidationError):
				StdInstanceParameterService.set_parameter_value(
					si.name,
					"submission_deadline",
					"2027-01-01",
				)
		finally:
			frappe.set_user("Administrator")
			self._cleanup_tender(tender)

	def test_std_inst_1000_output_generation_denied_for_unauthorized_user(self) -> None:
		observer = self._ensure_user_with_roles("stdinst1000-output-observer@example.test", ["Auditor"])
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			frappe.set_user(observer)
			with self.assertRaises(frappe.ValidationError):
				StdInstanceGeneratedOutputService.generate_dsm(si.name)
		finally:
			frappe.set_user("Administrator")
			self._cleanup_tender(tender)

	def test_std_inst_1000_publication_denied_for_non_publisher_role(self) -> None:
		officer = self._ensure_user_with_roles("stdinst1000-nonpublisher@example.test", ["Procurement Officer"])
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			si = StdInstanceStateService.apply_transition(si.name, "In Configuration", ignore_permissions=True)
			si = StdInstanceStateService.apply_transition(si.name, "Ready for Publication", ignore_permissions=True)
			self._prepare_publication_ready_instance(si.name)
			frappe.set_user(officer)
			with self.assertRaises(frappe.ValidationError):
				StdPublicationLockService.lock_for_publication(si.name)
		finally:
			frappe.set_user("Administrator")
			self._cleanup_tender(tender)

	def test_std_inst_1000_published_mutation_denied_with_addendum_message(self) -> None:
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
				StdAuthorizationService.assert_can_mutate_published(si.name)
		finally:
			frappe.set_user("Administrator")
			self._cleanup_tender(tender)
