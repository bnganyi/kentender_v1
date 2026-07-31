# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Integration: E1 NSSF PoC seed counts, schema artifact, STD-locked preview."""

from __future__ import annotations

import json
import unittest

import frappe

from kentender_procurement.tender_configurations.constants import STATUS_APPROVED_FOR_PREVIEW
from kentender_procurement.tender_configurations.seed.e1_nssf_seed import (
	CONFIG_REF,
	PACKAGE_CODE,
	seed_e1_nssf_tender_configuration,
)
from kentender_procurement.tender_configurations.services.bidder_submission_schema import (
	get_bidder_submission_schema,
)
from kentender_procurement.tender_configurations.services.contract_carry_forward import (
	get_carry_forward_bundle,
)
from kentender_procurement.tender_configurations.services.document_preview import (
	generate_document_preview,
)
from kentender_procurement.tender_configurations.services.readiness import (
	run_readiness_check,
)
from kentender_procurement.tender_configurations.services.schema_compiler import (
	SECTION_KEYS,
)
from kentender_procurement.tender_configurations.services.e1_nssf_fixture_mapper import (
	EXPECTED_FORMS_COUNT,
	EXPECTED_PRELIM_COUNT,
	EXPECTED_PRICE_LINE_COUNT,
	EXPECTED_REQUIREMENT_COUNT,
	EXPECTED_SCC_COUNT,
	EXPECTED_TECH_PASS,
	EXPECTED_TECH_QUAL_COUNT,
	EXPECTED_TECH_SCORE_COUNT,
	EXPECTED_TECH_TOTAL,
)


def _parse(raw):
	if not raw:
		return None
	if isinstance(raw, (dict, list)):
		return raw
	return json.loads(raw)


class TestE1NssfSeed(unittest.TestCase):
	"""Uses unittest.TestCase so bench --module does not pull unrelated FrappeTestCase suites."""

	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		cls.seed = seed_e1_nssf_tender_configuration(clear=True)
		cls.cfg_id = cls.seed["configuration_id"]

	def test_stable_ids(self):
		self.assertEqual(self.cfg_id, CONFIG_REF)
		self.assertEqual(self.seed["package_code"], PACKAGE_CODE)
		self.assertTrue(frappe.db.exists("Tender Configuration", CONFIG_REF))
		self.assertTrue(frappe.db.exists("Procurement Package", PACKAGE_CODE))

	def test_db_requirement_and_price_counts(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		reqs = _parse(doc.it_requirements)
		self.assertIsInstance(reqs, list)
		self.assertEqual(len(reqs), EXPECTED_REQUIREMENT_COUNT)
		price = _parse(doc.price_schedule)
		self.assertEqual(len(price.get("items") or []), EXPECTED_PRICE_LINE_COUNT)

	def test_db_evaluation_totals(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		ev = _parse(doc.evaluation_setup)
		criteria = ev.get("criteria") or []
		prelim = [c for c in criteria if c.get("stage") == "Preliminary"]
		tech_pf = [
			c
			for c in criteria
			if c.get("stage") == "Technical" and c.get("evaluation_basis") == "Pass/Fail"
		]
		tech_sc = [
			c
			for c in criteria
			if c.get("stage") == "Technical" and c.get("evaluation_basis") == "Scored"
		]
		self.assertEqual(len(prelim), EXPECTED_PRELIM_COUNT)
		self.assertEqual(len(tech_pf), EXPECTED_TECH_QUAL_COUNT)
		self.assertEqual(len(tech_sc), EXPECTED_TECH_SCORE_COUNT)
		self.assertEqual(int(ev.get("technical_pass_mark") or 0), EXPECTED_TECH_PASS)
		marks = sum(int(c.get("marks") or 0) for c in tech_sc)
		self.assertEqual(marks, EXPECTED_TECH_TOTAL)

	def test_forms_and_scc_persisted(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		forms = _parse(doc.forms_and_evidence)
		items = forms.get("submission_items") or []
		form_rows = [i for i in items if str(i.get("item_id") or "").startswith("FORM-")]
		self.assertEqual(len(form_rows), EXPECTED_FORMS_COUNT)
		cv = _parse(doc.contract_values)
		all_cv = [v for v in (cv.get("contract_values") or []) if isinstance(v, dict)]
		# Fixture SCC-* rows plus readiness-bound STD rows (payment/warranty/SLA, etc.).
		scc = [
			v
			for v in all_cv
			if str(v.get("contract_value_id") or "").startswith("SCC-")
		]
		self.assertGreaterEqual(len(scc), EXPECTED_SCC_COUNT)
		bound_pids = {
			str(v.get("readiness_parameter_id") or "").strip()
			for v in all_cv
			if str(v.get("readiness_parameter_id") or "").strip()
		}
		self.assertTrue({"payment", "warranty", "performance_security"} <= bound_pids, bound_pids)

	def test_std_version_bound(self):
		from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
		from kentender_procurement.std_engine.services.form_locked_text import (
			inventory_form_locked_text,
		)

		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.std_version, CANONICAL_PACKAGE_ID)
		self.assertEqual(doc.std_family_key, "IT")
		self.assertEqual(
			frappe.db.get_value("STD Version", doc.std_version, "lifecycle_state"),
			"ACTIVE",
		)
		inv = inventory_form_locked_text(doc.std_version)
		self.assertTrue(inv.get("complete"), inv)

	def test_bidder_submission_schema_artifact(self):
		out = get_bidder_submission_schema(self.cfg_id)
		self.assertTrue(out["has_schema"])
		schema = out["schema"]
		self.assertIn("sections", schema)
		self.assertTrue(schema.get("submission_policy"))
		self.assertEqual(schema.get("compiled_from"), "tender_configuration_cfg")
		self.assertTrue(schema.get("schema_hash"))
		keys = [s.get("key") for s in (schema.get("sections") or [])]
		for key in SECTION_KEYS:
			self.assertIn(key, keys)
		sections = schema.get("sections") or []
		matrix = next(
			(s for s in sections if s.get("key") == "technical_compliance_matrix"),
			None,
		)
		self.assertIsNotNone(matrix)
		self.assertEqual(len(matrix.get("requirements") or []), EXPECTED_REQUIREMENT_COUNT)
		price_sec = next((s for s in sections if s.get("key") == "price_schedule"), None)
		self.assertIsNotNone(price_sec)
		self.assertEqual(len(price_sec.get("price_lines") or []), EXPECTED_PRICE_LINE_COUNT)

	def test_readiness_has_zero_blockers(self):
		report = run_readiness_check(self.cfg_id)
		self.assertEqual(int(report.get("blocker_count") or 0), 0, report.get("findings"))
		self.assertEqual(int(report.get("warning_count") or 0), 0, report.get("findings"))
		self.assertEqual(report.get("overall_result"), "Ready for Review")

	def test_tds_select_values_match_official_options(self):
		from kentender_procurement.tender_configurations.services.tds import (
			ELIGIBLE_TENDERS,
			get_configuration_tds,
		)

		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		raw = _parse(doc.tds_values) or {}
		api = get_configuration_tds(self.cfg_id)
		self.assertIn(raw.get("eligible_tenderers"), ELIGIBLE_TENDERS)
		miss = []
		for key, opts in (api.get("options") or {}).items():
			val = raw.get(key)
			if val and opts and val not in opts:
				miss.append(f"{key}={val!r}")
		self.assertEqual(miss, [], miss)

	def test_carry_forward_bundle(self):
		bundle = get_carry_forward_bundle(self.cfg_id)
		self.assertEqual(bundle.get("source"), "CFG-09")
		self.assertGreaterEqual(len(bundle.get("payment_milestones") or []), 6)
		self.assertAlmostEqual(float(bundle.get("payment_percentage_total") or 0), 100.0, places=1)
		self.assertTrue(
			bundle.get("performance_security")
			or bundle.get("warranty")
			or bundle.get("categories")
		)

	def test_preview_std_locked_and_full_matrices(self):
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			"status",
			STATUS_APPROVED_FOR_PREVIEW,
		)
		frappe.db.commit()
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(
			gen.get("preview_status"),
			"Generated",
			msg=str(gen.get("generation_block") or gen.get("render_exception")),
		)
		html = gen.get("preview_html") or ""
		self.assertTrue(html)
		self.assertNotIn("Readiness issue:", html)
		self.assertNotIn("Fixture locked", html)
		self.assertNotIn("generation_blocked", html)
		self.assertNotRegex(html, r">REQ-\d+<")
		# STD Engine locked sections
		self.assertIn('id="sec-itt"', html)
		self.assertIn('id="sec-gcc"', html)
		self.assertIn('id="sec-forms"', html)
		self.assertIn('id="sec-contract_forms"', html)
		self.assertTrue(gen.get("render_hashes", {}).get("itt"))
		self.assertTrue(gen.get("render_hashes", {}).get("gcc"))
		self.assertTrue(gen.get("render_hashes", {}).get("forms"))
		# Official PPRA locked text — not fixture sample
		self.assertIn("scope of tender", html.lower())
		self.assertNotIn("tenderer shall prepare the tender in accordance", html.lower())
		self.assertNotIn("Source NSSF", html)
		self.assertNotIn("PoC submission deadline", html)
		self.assertNotIn("Confirm Yes/No, cite reference", html)
		self.assertNotIn("Notes to the Procuring Entity", html)
		self.assertNotIn("demo_submission_deadline", html)
		self.assertNotIn(">As specified<", html)
		self.assertIn("Professional indemnity cover", html)
		self.assertIn("KES 500,000", html)
		self.assertIn("Upload valid professional indemnity cover", html)
		self.assertIn("30 June 2027", html)
		self.assertNotIn("30 June 2026", html)
		self.assertIn("Laws of Kenya", html)
		self.assertIn("Per month", html)
		self.assertIn("Per GB/month", html)
		self.assertIn("kt-preview-table", html)
		self.assertIn("Requirement ID", html)
		# Audit/diagnostics stay outside bidder HTML.
		report = gen.get("render_validation_report") or {}
		self.assertEqual(report.get("report_type"), "Render Validation / Audit Report")
		self.assertFalse(report.get("bidder_facing"))
		self.assertIn("poc_audit_notes", report)
		self.assertNotIn("Render Validation", html)
		# Honest E1 matrices (cap lifted)
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		sample_titles = [
			r.get("title")
			for r in (_parse(doc.it_requirements) or [])[:5]
			if r.get("title")
		]
		found = sum(1 for t in sample_titles if t and t in html)
		self.assertGreaterEqual(found, 3, "expected multiple requirement titles in preview")
		# Count requirement-ish headings roughly via known first ids' titles
		req_ids = [r.get("requirement_id") for r in (_parse(doc.it_requirements) or [])]
		self.assertEqual(len(req_ids), EXPECTED_REQUIREMENT_COUNT)
		# Price / inventory presence
		price_name = (_parse(doc.price_schedule).get("items") or [{}])[0].get("item_name")
		if price_name:
			self.assertIn(price_name, html)
		inv = _parse(doc.system_inventory)
		inv_title = (inv.get("items") or [{}])[0].get("item_title")
		if inv_title:
			self.assertIn(inv_title, html)

	def test_seed_idempotent(self):
		again = seed_e1_nssf_tender_configuration(clear=True)
		self.assertEqual(again["configuration_id"], CONFIG_REF)
		doc = frappe.get_doc("Tender Configuration", CONFIG_REF)
		self.assertEqual(len(_parse(doc.it_requirements)), EXPECTED_REQUIREMENT_COUNT)
