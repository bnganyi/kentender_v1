# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-008 — ``Tender Required Form`` extensions: submission placeholder, stage, trace (doc 5 §14).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh008

``evidence_policy``, ``respondent_type``, and ``workflow_stage`` remain **Data** fields populated
from ``forms.json`` — doc 5 §14 ``Select/Data`` / WH-008 acceptance “mapped equivalents”.
``link_required_forms_to_submission_components`` orchestration is **WH-009**; ``WORKS-FORM-002`` is **WH-010**.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.officer_tender_config import (
	_officer_required_because_text,
)
from kentender_procurement.tender_management.services import std_template_engine
from kentender_procurement.tender_management.services.std_template_engine import (
	load_sample_config,
	load_sample_lots,
	load_template,
	resolve_required_forms,
	validate_config,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

_EXPECTED_STAGE_OPTIONS = {
	"Bid Submission",
	"Contract Stage",
	"Post-Award",
	"Other",
}


class TestWorksTenderHardeningWh008(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh008_tender_required_form_meta_new_fields(self) -> None:
		meta = frappe.get_meta("Tender Required Form")
		self.assertEqual(meta.istable, 1)

		sc = meta.get_field("submission_component_code")
		self.assertIsNotNone(sc)
		self.assertEqual(sc.fieldtype, "Data")
		self.assertEqual(int(sc.reqd or 0), 0)

		rb = meta.get_field("required_because")
		self.assertIsNotNone(rb)
		self.assertEqual(rb.fieldtype, "Small Text")
		self.assertEqual(int(rb.reqd or 0), 0)

		src = meta.get_field("source_rule_code")
		self.assertIsNotNone(src)
		self.assertEqual(src.fieldtype, "Data")
		self.assertEqual(int(src.reqd or 0), 0)

		st = meta.get_field("stage")
		self.assertIsNotNone(st)
		self.assertEqual(st.fieldtype, "Select")
		self.assertEqual(int(st.reqd or 0), 0)
		self.assertEqual(
			set((st.options or "").strip().split("\n")),
			_EXPECTED_STAGE_OPTIONS,
		)

		rt = meta.get_field("respondent_type")
		self.assertIsNotNone(rt)
		self.assertEqual(rt.fieldtype, "Data")

		ep = meta.get_field("evidence_policy")
		self.assertIsNotNone(ep)
		self.assertEqual(ep.fieldtype, "Data")

	def test_wh008_required_form_row_persists_on_tender(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-008 Tender Required Form Extensions"
		doc.tender_reference = "WH008-RF-001"
		act = "DEFAULT; RULE:RULE_REQUIRE_WORKS_REQUIREMENTS"
		doc.append(
			"required_forms",
			{
				"form_code": "WH008_FORM",
				"form_title": "WH-008 Placeholder Form",
				"display_group": "Core",
				"submission_component_code": "DSM-WH008-RF-001-WH008_FORM",
				"required_because": _officer_required_because_text(act),
				"source_rule_code": "RULE_REQUIRE_WORKS_REQUIREMENTS",
				"workflow_stage": "BID_SUBMISSION",
				"stage": "Bid Submission",
				"respondent_type": "BIDDER_OR_JV",
				"required": 1,
				"activation_source": act,
				"evidence_policy": "STRUCTURED_ONLY",
				"display_order": 10,
				"notes": "WH-008 persistence row",
			},
		)
		doc.insert(ignore_permissions=True)
		try:
			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			self.assertEqual(len(reloaded.required_forms), 1)
			row = reloaded.required_forms[0]
			self.assertEqual(row.form_code, "WH008_FORM")
			self.assertEqual(row.submission_component_code, "DSM-WH008-RF-001-WH008_FORM")
			self.assertEqual(row.stage, "Bid Submission")
			self.assertEqual(row.workflow_stage, "BID_SUBMISSION")
			self.assertEqual(row.source_rule_code, "RULE_REQUIRE_WORKS_REQUIREMENTS")
			self.assertIn("rule", (row.required_because or "").lower())
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh008_resolve_required_forms_dsm_and_stage_mapping(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		self.assertTrue(
			(config.get("TENDER.TENDER_REFERENCE") or "").strip(),
			"sample config must set TENDER.TENDER_REFERENCE for DSM assertions",
		)
		lots = load_sample_lots(template)
		result = validate_config(template, config, lots=lots)
		rows = resolve_required_forms(template, config, validation_result=result)
		self.assertGreater(len(rows), 0)

		tref = std_template_engine._sanitize_tender_reference_for_dsm(
			config.get("TENDER.TENDER_REFERENCE")
		)
		bid_rows = [r for r in rows if r.get("workflow_stage") == "BID_SUBMISSION"]
		self.assertTrue(bid_rows, "expected at least one BID_SUBMISSION form from package")
		for r in bid_rows:
			with self.subTest(form=r.get("form_code")):
				self.assertEqual(r.get("stage"), "Bid Submission")
				fc = str(r.get("form_code") or "").strip().upper()
				self.assertTrue(fc)
				self.assertEqual(
					r.get("submission_component_code"),
					f"DSM-{tref}-{fc}",
				)
				self.assertEqual(
					r.get("required_because"),
					_officer_required_because_text(r.get("activation_source") or ""),
				)

		eval_rows = [r for r in rows if r.get("workflow_stage") == "EVALUATION"]
		self.assertTrue(eval_rows, "expected at least one EVALUATION form from package")
		for r in eval_rows:
			with self.subTest(form=r.get("form_code")):
				self.assertEqual(r.get("stage"), "Other")
				self.assertEqual(r.get("submission_component_code") or "", "")

		contract_rows = [r for r in rows if r.get("workflow_stage") == "CONTRACT_SIGNATURE"]
		if contract_rows:
			for r in contract_rows:
				with self.subTest(form=r.get("form_code")):
					self.assertEqual(r.get("stage"), "Contract Stage")
					self.assertEqual(r.get("submission_component_code") or "", "")