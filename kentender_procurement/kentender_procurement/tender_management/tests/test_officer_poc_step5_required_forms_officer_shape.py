# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — Officer step 5 required forms UX.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_officer_poc_step5_required_forms_officer_shape
"""

from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.tender_management.services.officer_tender_config import (
	get_officer_required_forms_checklist_preview,
	shape_officer_required_forms_checklist,
)
from kentender_procurement.tender_management.services.std_template_loader import upsert_std_template


def _primary_configuration() -> dict:
	repo = Path(__file__).resolve().parents[4]
	path = (
		repo
		/ "kentender_procurement"
		/ "kentender_procurement"
		/ "tender_management"
		/ "std_templates"
		/ "ke_ppra_works_building_2022_04_poc"
		/ "sample_tender.json"
	)
	data = json.loads(path.read_text(encoding="utf-8"))
	return dict(data["configuration"])


class TestOfficerPocStep5RequiredFormsShapeUnit(UnitTestCase):
	def test_shape_maps_activation_sources_to_plain_language(self) -> None:
		engine_rows = [
			{
				"form_code": "FORM_OF_TENDER",
				"form_title": "Form of Tender",
				"display_group": "Tendering Forms",
				"required": 1,
				"activation_source": "DEFAULT",
				"respondent_type": "BIDDER",
				"workflow_stage": "BID_SUBMISSION",
				"evidence_policy": "STRUCTURED_RESPONSE",
				"display_order": 10,
			},
			{
				"form_code": "FORM_TECHNICAL_PROPOSAL",
				"form_title": "Technical Proposal",
				"display_group": "Tendering Forms",
				"required": 1,
				"activation_source": "DEFAULT; RULE:RULE_REQUIRE_WORKS_REQUIREMENTS",
				"respondent_type": "BIDDER",
				"workflow_stage": "BID_SUBMISSION",
				"evidence_policy": "STRUCTURED_RESPONSE",
				"display_order": 100,
			},
		]
		out = shape_officer_required_forms_checklist(engine_rows)
		self.assertEqual(out["count"], 2)
		self.assertIn("default for this procurement category", out["rows"][0]["required_because"].lower())
		self.assertIn("rule", out["rows"][1]["required_because"].lower())


class TestOfficerPocStep5RequiredFormsPreviewIntegration(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def test_primary_configuration_yields_15_officer_rows(self) -> None:
		cfg = _primary_configuration()
		preview = get_officer_required_forms_checklist_preview(cfg)
		self.assertEqual(preview["count"], 15)
		self.assertIn(
			preview["validation_status"],
			("Passed", "Passed With Warnings", "Blocked"),
		)
		codes = [r["form_code"] for r in preview["rows"]]
		self.assertIn("FORM_OF_TENDER", codes)
		self.assertIn("FORM_TECHNICAL_PROPOSAL", codes)
		for row in preview["rows"]:
			self.assertTrue(row.get("form_title"))
			self.assertTrue(row.get("required_because"))
