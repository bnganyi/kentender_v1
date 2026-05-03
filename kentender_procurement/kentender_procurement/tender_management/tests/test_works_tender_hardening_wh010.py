# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-010 — doc 5 §18 validation + §17.1 aggregation (``works_tender_hardening_validation``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh010
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import works_tender_hardening as wth
from kentender_procurement.tender_management.services import works_tender_hardening_validation as wtv
from kentender_procurement.tender_management.services.works_tender_hardening_validation_checks import (
	validate_works_boq_checks,
)
from kentender_procurement.tender_management.services.std_template_engine import (
	load_sample_config,
	load_template,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


class TestWorksTenderHardeningWh010(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh010_aggregate_status_section_17_1(self) -> None:
		self.assertEqual(
			wtv._aggregate_status([], service_failed=False),
			wtv.HARDENING_STATUS_PASS,
		)
		self.assertEqual(
			wtv._aggregate_status(
				[{"severity": wtv.SEVERITY_INFO, "finding_code": "X"}],
				service_failed=False,
			),
			wtv.HARDENING_STATUS_PASS,
		)
		self.assertEqual(
			wtv._aggregate_status(
				[{"severity": wtv.SEVERITY_HIGH, "finding_code": "X"}],
				service_failed=False,
			),
			wtv.HARDENING_STATUS_WARNING,
		)
		self.assertEqual(
			wtv._aggregate_status(
				[{"severity": wtv.SEVERITY_CRITICAL, "finding_code": "X"}],
				service_failed=False,
			),
			wtv.HARDENING_STATUS_BLOCKED,
		)
		self.assertEqual(
			wtv._aggregate_status(
				[{"severity": wtv.SEVERITY_CRITICAL, "finding_code": "X"}],
				service_failed=True,
			),
			wtv.HARDENING_STATUS_FAILED,
		)

	def test_wh010_service_exception_marks_failed(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-010 SVC"
		doc.tender_reference = "WH010-SVC-001"
		doc.configuration_json = json.dumps(
			load_sample_config(load_template(TEMPLATE_CODE)), sort_keys=True, default=str
		)
		doc.insert(ignore_permissions=True)
		try:
			with patch.object(
				wtv,
				"validate_audit",
				side_effect=RuntimeError("simulated audit failure"),
			):
				out = wtv.validate_works_tender_stage(doc.name)
			self.assertEqual(out.get("status"), wtv.HARDENING_STATUS_FAILED)
			self.assertFalse(out.get("ok"))
			codes = [f.get("finding_code") for f in out.get("findings") or []]
			self.assertIn("WORKS-SVC-001", codes)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh010_works_req_001_missing_scope(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-010 REQ001"
		doc.tender_reference = "WH010-REQ-001"
		doc.configuration_json = json.dumps(
			load_sample_config(load_template(TEMPLATE_CODE)), sort_keys=True, default=str
		)
		doc.insert(ignore_permissions=True)
		try:
			wth.initialize_works_requirements(doc.name)
			doc = frappe.get_doc("Procurement Tender", doc.name)
			for row in list(doc.works_requirements):
				if row.component_code == "WRK_SCOPE":
					doc.remove(row)
					break
			doc.save(ignore_permissions=True)
			out = wtv.validate_works_tender_stage(doc.name)
			codes = [f.get("finding_code") for f in out.get("findings") or []]
			self.assertIn("WORKS-REQ-001", codes)
			self.assertEqual(out.get("status"), wtv.HARDENING_STATUS_BLOCKED)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh010_boq_003_missing_bill_code(self) -> None:
		"""§18.3 WORKS-BOQ-003 via in-memory doc (BoQ ``bill_code`` is mandatory on save)."""
		doc = frappe.new_doc("Procurement Tender")
		doc.configuration_json = json.dumps({"WORKS.BOQ_REQUIRED": True}, sort_keys=True)
		doc.append(
			"boq_items",
			{
				"item_code": "T-001",
				"item_category": "PRELIMINARIES",
				"description": "Test",
				"unit": "m",
				"quantity": 1,
				"bill_code": "",
				"bill_title": "Bill",
				"item_number": "1",
				"boq_code": "BOQ-T",
				"boq_version": "V1",
				"quantity_locked": 1,
				"formula_type": "Measured",
				"allow_supplier_amount_edit": 0,
				"supplier_rate_editable": 0,
				"boq_row_status": "Active",
			},
		)
		codes = [f.get("finding_code") for f in validate_works_boq_checks(doc)]
		self.assertIn("WORKS-BOQ-003", codes)

	def test_wh010_lot_002_duplicate_lot_codes(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-010 LOT002"
		doc.tender_reference = "WH010-LOT-002"
		doc.configuration_json = json.dumps(
			load_sample_config(load_template(TEMPLATE_CODE)), sort_keys=True, default=str
		)
		doc.og_lots_multiple_lots_enabled = 1
		doc.insert(ignore_permissions=True)
		try:
			doc = frappe.get_doc("Procurement Tender", doc.name)
			for lc in ("LOT-DUP", "LOT-DUP"):
				doc.append(
					"lots",
					{
						"lot_code": lc,
						"lot_title": "Dup test",
						"lot_status": "Draft",
					},
				)
			doc.save(ignore_permissions=True)
			out = wtv.validate_works_tender_stage(doc.name)
			codes = [f.get("finding_code") for f in out.get("findings") or []]
			self.assertIn("WORKS-LOT-002", codes)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh010_model_001_missing_submission_row(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-010 MODEL001"
		doc.tender_reference = "WH010-MOD-001"
		doc.configuration_json = json.dumps(
			load_sample_config(load_template(TEMPLATE_CODE)), sort_keys=True, default=str
		)
		doc.insert(ignore_permissions=True)
		try:
			wth.initialize_derived_model_readiness(doc.name)
			doc = frappe.get_doc("Procurement Tender", doc.name)
			for row in list(doc.derived_model_readiness):
				if row.model_type == "Submission":
					doc.remove(row)
					break
			doc.save(ignore_permissions=True)
			out = wtv.validate_works_tender_stage(doc.name)
			codes = [f.get("finding_code") for f in out.get("findings") or []]
			self.assertIn("WORKS-MODEL-001", codes)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh010_audit_001_missing_package(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-010 AUD001"
		doc.tender_reference = "WH010-AUD-001"
		doc.configuration_json = json.dumps(
			load_sample_config(load_template(TEMPLATE_CODE)), sort_keys=True, default=str
		)
		doc.insert(ignore_permissions=True)
		try:
			out = wtv.validate_works_tender_stage(doc.name)
			codes = [f.get("finding_code") for f in out.get("findings") or []]
			self.assertIn("WORKS-AUDIT-001", codes)
			summary = (out.get("summary") or {})
			self.assertIn("audit_status", summary)
			self.assertTrue(summary.get("legacy_lockout_checked"))
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh010_orchestration_primary_seed_no_critical(self) -> None:
		template = load_template(TEMPLATE_CODE)
		cfg = load_sample_config(template)
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-010 Orch Critical"
		doc.tender_reference = "WH010-ORCH-CRIT"
		doc.configuration_json = json.dumps(cfg, sort_keys=True, default=str)
		doc.insert(ignore_permissions=True)
		try:
			out = wth.run_works_tender_stage_hardening(doc.name)
			val = out.get("validation") or {}
			self.assertEqual(val.get("critical_count"), 0, msg=f"findings={val.get('findings')}")
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
