# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-1100 — representative Works completion seed fixture.

Uses ``tender_reference_suffix`` so CI does not depend on site state for
``TND-MOH-2026-001``. Empty suffix keeps the pack default for manual golden runs.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_seed_1100
"""

from __future__ import annotations

import secrets

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import upsert_std_template
from kentender_procurement.tender_management.works_completion.seeds.works_completion_moh_fixture import (
	PACKAGE_CODE,
	_ensure_package_exists,
	run as seed_works_comp_1100_run,
)


class TestWorksCompSeed1100(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")
		_ensure_package_exists()
		self._scrub_tenders_for_package(PACKAGE_CODE)

	def _scrub_tenders_for_package(self, package_code: str) -> None:
		"""Remove tenders on ``package_code`` so planning handoff uniqueness does not break tests."""
		for name in frappe.get_all(
			"Procurement Tender",
			filters={"procurement_package": package_code},
			pluck="name",
		):
			self._cleanup_tender(name)

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

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

	def _suffix(self) -> str:
		return f"CI{secrets.token_hex(5)}"

	def test_works_comp_1100_first_run_then_idempotent(self) -> None:
		sfx = self._suffix()
		out1: dict | None = None
		try:
			out1 = seed_works_comp_1100_run(tender_reference_suffix=sfx)
			self.assertTrue(out1.get("ok"))
			self.assertFalse(out1.get("already_seeded"))
			self.assertEqual(out1.get("instance_status"), "Locked for Approval")
			tn = out1.get("tender_name")
			si = out1.get("std_instance_code")
			self.assertTrue(tn and si)
			self.assertEqual(out1.get("readiness_status"), "Ready")
			lr = out1.get("lock_result") or {}
			self.assertEqual((lr.get("readiness") or {}).get("status"), "Ready")

			snaps = frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={
					"tender_std_instance": si,
					"snapshot_type": "Configuration",
					"snapshot_status": "Final",
				},
				pluck="name",
			)
			self.assertTrue(snaps)
			self.assertIn(out1.get("configuration_snapshot"), snaps)

			out2 = seed_works_comp_1100_run(tender_reference_suffix=sfx)
			self.assertTrue(out2.get("ok"))
			self.assertTrue(out2.get("already_seeded"))
			self.assertEqual(out2.get("std_instance_code"), si)
			self.assertEqual(out2.get("instance_status"), "Locked for Approval")
		finally:
			if out1 and out1.get("tender_name"):
				self._cleanup_tender(str(out1["tender_name"]))

	def test_works_comp_1100_conflict_when_instance_publication_locked(self) -> None:
		sfx = self._suffix()
		tender_name: str | None = None
		try:
			from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE
			from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
			from kentender_procurement.tender_management.works_completion.seeds.works_completion_moh_fixture import (
				_resolve_tender_reference,
			)

			tref = _resolve_tender_reference(sfx)
			doc = frappe.new_doc("Procurement Tender")
			doc.std_template = TEMPLATE_CODE
			doc.tender_title = "WORKS-COMP-1100 conflict probe"
			doc.tender_reference = tref
			doc.procurement_package = PACKAGE_CODE
			doc.insert(ignore_permissions=True)
			tender_name = doc.name

			inst = TenderStdBindingService.create_std_instance_for_tender(
				tender_name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.db.set_value("Tender STD Instance", inst.name, "instance_status", "Published Locked")

			bad = seed_works_comp_1100_run(tender_reference_suffix=sfx)
			self.assertFalse(bad.get("ok"))
			self.assertEqual(bad.get("code"), "WORKS_COMP_1100_STD_INSTANCE_NOT_EDITABLE")
		finally:
			if tender_name:
				self._cleanup_tender(tender_name)
