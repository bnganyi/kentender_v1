# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1200 — API layer contracts."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api import std_instance as api
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService


class TestStdInstApi1200(IntegrationTestCase):
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
		doc.tender_title = "STDINST-1200 Test Tender"
		doc.tender_reference = f"STDINST1200-{frappe.generate_hash(length=8)}"
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

	def test_std_inst_1200_create_and_get_instance(self) -> None:
		tender = self._minimal_tender()
		try:
			out = api.create_instance(tender, ignore_permissions=True)
			self.assertTrue(out.get("ok"))
			self.assertEqual(out.get("code"), "STD_INSTANCE_CREATED")
			instance = out["instance"]["instance_code"]

			got = api.get_instance(instance)
			self.assertTrue(got.get("ok"))
			self.assertEqual(got.get("code"), "STD_INSTANCE_FETCHED")
			self.assertEqual(got["instance"]["instance_code"], instance)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_1200_endpoint_examples_generate_readiness_snapshot(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			gen = api.generate_outputs(si.name, ["DSM"])
			self.assertTrue(gen.get("ok"))
			self.assertEqual(gen.get("code"), "STD_OUTPUTS_GENERATED")
			self.assertEqual(len(gen.get("outputs") or []), 1)

			rd = api.evaluate_readiness(si.name, persist=True)
			self.assertTrue(rd.get("ok"))
			self.assertEqual(rd.get("code"), "STD_READINESS_EVALUATED")
			self.assertIn("status", rd.get("result") or {})

			snap = api.create_publication_snapshot(si.name, "API snapshot")
			self.assertTrue(snap.get("ok"))
			self.assertEqual(snap.get("code"), "STD_PUBLICATION_SNAPSHOT_CREATED")
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_1200_deterministic_validation_error_for_illegal_state(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			out = api.lock_publication(si.name)
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("code"), "STD_API_VALIDATION_FAILED")
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_1200_deterministic_permission_denied(self) -> None:
		tender = self._minimal_tender()
		try:
			frappe.set_user("Guest")
			out = api.create_instance(tender, ignore_permissions=True)
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("code"), "STD_API_VALIDATION_FAILED")
		finally:
			frappe.set_user("Administrator")
			self._cleanup_tender(tender)

	def test_std_inst_1200_duplicate_constraint_maps_deterministically(self) -> None:
		tender = self._minimal_tender()
		try:
			with patch(
				"kentender_procurement.tender_management.api.std_instance.TenderStdBindingService.create_std_instance_for_tm2_tender",
				side_effect=frappe.DuplicateEntryError("db duplicate"),
			):
				out = api.create_instance(tender, ignore_permissions=True)
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("code"), "STD_API_DUPLICATE_CONSTRAINT")
		finally:
			self._cleanup_tender(tender)
