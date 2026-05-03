# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-009 — Works tender-stage hardening services (doc 5 §16).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh009

§18 coded validation is **WH-010**; snapshot depth **WH-011**; Desk **WH-012**.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as procurement_tender_controller,
)
from kentender_procurement.tender_management.services import works_tender_hardening as wth
from kentender_procurement.tender_management.services import works_tender_hardening_validation as wtv
from kentender_procurement.tender_management.services.std_template_engine import (
	load_sample_config,
	load_template,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


class TestWorksTenderHardeningWh009(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh009_constants_match_doc_section_15(self) -> None:
		self.assertEqual(wth.HARDENING_STATUS_PASS, "Pass")
		self.assertEqual(wth.SEVERITY_CRITICAL, "Critical")
		self.assertEqual(wth.AREA_BOQ, "BoQ")

	def test_wh009_validate_envelope_shape(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-009 Validate Envelope"
		doc.tender_reference = "WH009-VAL-001"
		cfg = load_sample_config(load_template(TEMPLATE_CODE))
		doc.configuration_json = json.dumps(cfg, sort_keys=True, default=str)
		doc.insert(ignore_permissions=True)
		try:
			out = wtv.validate_works_tender_stage(doc.name)
			for key in (
				"ok",
				"tender",
				"boundary_code",
				"status",
				"critical_count",
				"high_count",
				"medium_count",
				"low_count",
				"info_count",
				"findings",
				"summary",
			):
				self.assertIn(key, out, f"missing envelope key {key}")
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh009_orchestration_populates_children_and_snapshot(self) -> None:
		template = load_template(TEMPLATE_CODE)
		cfg = load_sample_config(template)
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-009 Orchestration"
		doc.tender_reference = "WH009-ORCH-001"
		doc.configuration_json = json.dumps(cfg, sort_keys=True, default=str)
		doc.insert(ignore_permissions=True)
		try:
			out = wth.run_works_tender_stage_hardening(doc.name)
			self.assertIn("steps", out)
			self.assertIn("validation", out)
			self.assertTrue(out.get("snapshot_hash"))

			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			self.assertGreaterEqual(len(reloaded.works_requirements), 10)
			self.assertEqual(len(reloaded.section_attachments), 3)
			self.assertEqual(len(reloaded.derived_model_readiness), 4)
			self.assertGreater(len(reloaded.required_forms), 0)
			self.assertTrue(reloaded.works_hardening_snapshot_hash)
			self.assertTrue(reloaded.works_hardening_checked_at)
			self.assertTrue((reloaded.works_hardening_snapshot_json or "").strip())

			summary = wth.get_works_hardening_summary(doc.name)
			self.assertTrue(summary.get("ok"))
			self.assertIn("counts", summary.get("summary") or {})

			snap = wth.get_works_tender_stage_snapshot(doc.name)
			self.assertEqual(snap.get("hash"), reloaded.works_hardening_snapshot_hash)
			self.assertIsInstance(snap.get("snapshot"), dict)
			self.assertEqual(snap["snapshot"].get("snapshot_type"), "WORKS_TENDER_STAGE_BASELINE")

			find = wth.get_works_hardening_findings(doc.name)
			self.assertTrue(find.get("ok"))
			self.assertIsInstance(find.get("findings"), list)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh009_whitelist_delegates(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-009 Whitelist"
		doc.tender_reference = "WH009-WL-001"
		doc.configuration_json = json.dumps(
			load_sample_config(load_template(TEMPLATE_CODE)), sort_keys=True, default=str
		)
		doc.insert(ignore_permissions=True)
		try:
			r1 = procurement_tender_controller.validate_works_tender_stage(doc.name)
			self.assertIn("status", r1)
			r2 = procurement_tender_controller.get_works_hardening_summary(doc.name)
			self.assertTrue(r2.get("ok"))
			r3 = procurement_tender_controller.get_works_hardening_findings(doc.name)
			self.assertTrue(r3.get("ok"))
			r4 = procurement_tender_controller.get_works_tender_stage_snapshot(doc.name)
			self.assertTrue(r4.get("ok"))
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh009_run_denies_without_write_permission(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-009 Permission"
		doc.tender_reference = "WH009-PERM-001"
		doc.configuration_json = json.dumps(
			load_sample_config(load_template(TEMPLATE_CODE)), sort_keys=True, default=str
		)
		doc.insert(ignore_permissions=True)
		try:
			orig = Document.check_permission

			def _deny_write(self, ptype, *args, **kwargs):
				if ptype == "write":
					raise frappe.PermissionError("no write")
				return orig(self, ptype, *args, **kwargs)

			with patch.object(Document, "check_permission", _deny_write):
				with self.assertRaises(frappe.PermissionError):
					wth.run_works_tender_stage_hardening(doc.name)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
