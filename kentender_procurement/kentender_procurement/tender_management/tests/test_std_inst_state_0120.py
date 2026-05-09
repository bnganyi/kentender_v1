# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0120 — ``StdInstanceStateService`` lifecycle transitions + audit comments.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_std_inst_state_0120
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
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService


class TestStdInstState0120(IntegrationTestCase):
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
		doc.tender_title = "STDINST-0120 Test Tender"
		doc.tender_reference = "STDINST0120-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"procurement_tender": tender_name},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def test_std_inst_0120_apply_transition_happy_path(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			si = StdInstanceStateService.apply_transition(
				si.name,
				"In Configuration",
				ignore_permissions=True,
			)
			self.assertEqual(si.instance_status, "In Configuration")
			comments = frappe.get_all(
				"Comment",
				filters={
					"reference_doctype": "Tender STD Instance",
					"reference_name": si.name,
				},
				pluck="content",
			)
			self.assertTrue(any("Draft" in c and "In Configuration" in c for c in comments))
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0120_cancelled_from_draft(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			si = StdInstanceStateService.apply_transition(si.name, "Cancelled", ignore_permissions=True)
			self.assertEqual(si.instance_status, "Cancelled")
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0120_published_locked_to_draft_denied(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
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
			doc = frappe.get_doc("Tender STD Instance", name)
			doc.instance_status = "Draft"
			with self.assertRaises(frappe.ValidationError):
				doc.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0120_replace_supersession_regression(self) -> None:
		tender = self._minimal_tender()
		try:
			TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			second = TenderStdBindingService.replace_std_instance_through_supersession(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self.assertTrue(second.name)
			cur = TenderStdBindingService.get_current_std_instance_for_tender(tender)
			self.assertIsNotNone(cur)
			self.assertEqual(cur.name, second.name)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0120_terminal_no_transition(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			si = StdInstanceStateService.apply_transition(si.name, "Cancelled", ignore_permissions=True)
			with self.assertRaises(frappe.ValidationError):
				StdInstanceStateService.apply_transition(si.name, "Draft", ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)
