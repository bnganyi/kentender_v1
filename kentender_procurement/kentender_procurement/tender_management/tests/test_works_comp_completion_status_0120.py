# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0120 — get_completion_status summary.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_completion_status_0120
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
from kentender_procurement.tender_management.works_completion.services.completion_status import (
	STAGE_CODES_ORDER,
	get_completion_status,
)


class TestWorksCompCompletionStatus0120(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_procurement_tender(self, **kwargs) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0120 Test Tender"
		doc.tender_reference = "TND-WORKSCOMP-0120"
		for k, v in kwargs.items():
			doc.set(k, v)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_std_instances_for_tender(self, tender: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("Procurement Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_works_comp_0120_shape_and_stage_order(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = get_completion_status(si.name)
			self.assertIn("instance_code", out)
			self.assertIn("tender_code", out)
			self.assertIn("overall_status", out)
			self.assertIn("stages", out)
			self.assertIn("outputs", out)
			self.assertIn("readiness_status", out)
			self.assertEqual(len(out["stages"]), len(STAGE_CODES_ORDER))
			self.assertEqual([s["stage_code"] for s in out["stages"]], list(STAGE_CODES_ORDER))
			for k in ("bundle", "dsm", "dom", "dem", "dcm"):
				self.assertIn(k, out["outputs"])
		finally:
			self._delete_tender(tender)

	def test_works_comp_0120_tender_code_uses_reference(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = get_completion_status(si.name)
			self.assertEqual(out["tender_code"], "TND-WORKSCOMP-0120")
		finally:
			self._delete_tender(tender)

	def test_works_comp_0120_evaluate_does_not_persist_readiness(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			before = frappe.db.get_value("Tender STD Instance", si.name, "readiness_status")
			get_completion_status(si.name)
			get_completion_status(si.name)
			after = frappe.db.get_value("Tender STD Instance", si.name, "readiness_status")
			self.assertEqual(before, after)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0120_outputs_all_missing_initially(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = get_completion_status(si.name)
			for _k, v in out["outputs"].items():
				self.assertEqual(v, "Missing")
		finally:
			self._delete_tender(tender)

	def test_works_comp_0120_outputs_stale_flags(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.db.set_value(
				"Tender STD Instance",
				si.name,
				"outputs_stale_flags",
				json.dumps(["Bundle", "DOM"], sort_keys=True),
			)
			out = get_completion_status(si.name)
			self.assertEqual(out["outputs"]["bundle"], "Stale")
			self.assertEqual(out["outputs"]["dom"], "Stale")
		finally:
			self._delete_tender(tender)

	def test_works_comp_0120_missing_instance_payload(self) -> None:
		out = get_completion_status("NONEXISTENT-STDINST-0120")
		self.assertEqual(out["overall_status"], "Blocked")
		self.assertEqual(out["readiness_status"], "Blocked")
		self.assertEqual(out["tender_code"], "")
		ctx_stage = next(s for s in out["stages"] if s["stage_code"] == "CONTEXT")
		self.assertEqual(ctx_stage["status"], "Blocked")

	def test_works_comp_0120_context_blocked_overall_blocked(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.db.set_value("Tender STD Instance", si.name, "procurement_category", "GOODS")
			out = get_completion_status(si.name)
			self.assertEqual(out["overall_status"], "Blocked")
			ctx_stage = next(s for s in out["stages"] if s["stage_code"] == "CONTEXT")
			self.assertEqual(ctx_stage["status"], "Blocked")
			self.assertGreater(ctx_stage["critical_blockers"], 0)
		finally:
			self._delete_tender(tender)
