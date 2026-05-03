# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-011 — doc 5 §23 snapshot depth + doc 4 §17.2 audit fields (``works_tender_snapshot``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh011
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import works_tender_hardening as wth
from kentender_procurement.tender_management.services.works_tender_snapshot import build_snapshot
from kentender_procurement.tender_management.services.std_template_engine import (
	load_sample_config,
	load_template,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

_SECTION23_TOP_KEYS = frozenset(
	{
		"snapshot_type",
		"snapshot_version",
		"tender",
		"planning_lineage",
		"std_binding",
		"configuration",
		"works_requirements",
		"section_attachments",
		"lots",
		"boq",
		"required_forms",
		"derived_model_readiness",
		"validation",
		"preview",
		"generated_at",
		"generated_by",
	}
)


class TestWorksTenderHardeningWh011(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh011_orchestration_snapshot_has_section_23_keys_and_enrichment(self) -> None:
		template = load_template(TEMPLATE_CODE)
		cfg = load_sample_config(template)
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-011 Orch"
		doc.tender_reference = "WH011-ORCH-001"
		doc.configuration_json = json.dumps(cfg, sort_keys=True, default=str)
		doc.insert(ignore_permissions=True)
		try:
			wth.run_works_tender_stage_hardening(doc.name)
			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			payload = json.loads(reloaded.works_hardening_snapshot_json or "{}")
			self.assertEqual(_SECTION23_TOP_KEYS, set(payload.keys()))
			self.assertEqual(payload.get("snapshot_type"), "WORKS_TENDER_STAGE_BASELINE")

			val = payload.get("validation") or {}
			self.assertIsInstance(val, dict)
			self.assertIn("present", val)
			self.assertIn("finding_codes", val)
			self.assertIn("validation_json_sha256", val)
			self.assertIn("required_forms_count", val)
			self.assertIn("required_forms_codes", val)
			self.assertTrue(val.get("present"))
			self.assertIsInstance(val.get("required_forms_codes"), list)

			prev = payload.get("preview") or {}
			self.assertIn("configuration_hash", prev)
			self.assertIn("source_package_hash", prev)
			self.assertIn("package_hash", prev)
			self.assertIn("works_hardening_validation_json_len", prev)
			self.assertIn("generated_tender_pack_html_len", prev)

			lin = payload.get("planning_lineage") or {}
			self.assertIn("source_demand_count", lin)
			self.assertIn("source_budget_line_count", lin)

			boq = payload.get("boq") or {}
			self.assertIn("bills", boq)
			self.assertIn("items_content_sha256", boq)
			items = boq.get("items") or []
			distinct_bills = len({str(r.get("bill_code") or "").strip() for r in items})
			self.assertEqual(len(boq.get("bills") or []), distinct_bills)
			self.assertTrue((boq.get("items_content_sha256") or "").strip())

			hdr = payload.get("tender") or {}
			self.assertIn("configuration_hash", hdr)
			self.assertIn("works_hardening_checked_at", hdr)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh011_bills_grouping_deterministic(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-011 Bills"
		doc.tender_reference = "WH011-BILLS-1"
		doc.insert(ignore_permissions=True)
		try:
			doc.append(
				"boq_items",
				{
					"item_code": "Z-ITEM",
					"item_category": "PRELIMINARIES",
					"description": "Z",
					"unit": "m",
					"quantity": 1,
					"bill_code": "BILL-B",
					"bill_title": "Bill B",
					"item_number": "2",
					"boq_code": "BOQ-X",
					"boq_version": "V1",
					"quantity_locked": 1,
					"formula_type": "Measured",
					"allow_supplier_amount_edit": 0,
					"supplier_rate_editable": 0,
					"boq_row_status": "Active",
				},
			)
			doc.append(
				"boq_items",
				{
					"item_code": "A-ITEM",
					"item_category": "PRELIMINARIES",
					"description": "A",
					"unit": "m",
					"quantity": 2,
					"bill_code": "BILL-A",
					"bill_title": "Bill A",
					"item_number": "1",
					"boq_code": "BOQ-X",
					"boq_version": "V1",
					"quantity_locked": 1,
					"formula_type": "Measured",
					"allow_supplier_amount_edit": 0,
					"supplier_rate_editable": 0,
					"boq_row_status": "Active",
				},
			)
			p1 = build_snapshot(doc)
			p2 = build_snapshot(doc)
			bills1 = p1["boq"]["bills"]
			bills2 = p2["boq"]["bills"]
			self.assertEqual([b["bill_code"] for b in bills1], [b["bill_code"] for b in bills2])
			self.assertEqual([b["bill_code"] for b in bills1], ["BILL-A", "BILL-B"])
			self.assertEqual(p1["boq"]["items_content_sha256"], p2["boq"]["items_content_sha256"])
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
