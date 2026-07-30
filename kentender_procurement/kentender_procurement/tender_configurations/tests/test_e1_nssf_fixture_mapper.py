# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Unit tests: E1 NSSF fixture 09 → CFG service shapes."""

from __future__ import annotations

import unittest

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
	assert_mapped_cfg_enums_valid,
	fixture_09_path,
	load_fixture_09,
	load_schema_10,
	map_all_cfg_blobs,
	map_bidder_response,
	map_price_users_or_qty,
	map_requirement_family,
	schema_10_path,
)
from kentender_procurement.tender_configurations.services.it_requirements import (
	CATEGORIES,
	RESPONSE_FORMATS,
)
from kentender_procurement.tender_configurations.services.tds import ELIGIBLE_TENDERS


class TestE1NssfFixtureMapper(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.fixture = load_fixture_09()
		cls.mapped = map_all_cfg_blobs(cls.fixture)

	def test_fixture_files_exist(self):
		self.assertTrue(fixture_09_path().is_file())
		self.assertTrue(schema_10_path().is_file())

	def test_requirement_count_190(self):
		self.assertEqual(len(self.mapped["it_requirements"]), EXPECTED_REQUIREMENT_COUNT)
		self.assertEqual(self.mapped["counts"]["requirements"], EXPECTED_REQUIREMENT_COUNT)

	def test_price_line_count_22(self):
		self.assertEqual(len(self.mapped["price_schedule"]["items"]), EXPECTED_PRICE_LINE_COUNT)
		self.assertEqual(self.mapped["counts"]["price_lines"], EXPECTED_PRICE_LINE_COUNT)

	def test_evaluation_section_iii_counts(self):
		self.assertEqual(self.mapped["counts"]["prelim"], EXPECTED_PRELIM_COUNT)
		self.assertEqual(self.mapped["counts"]["tech_qual_pass_fail"], EXPECTED_TECH_QUAL_COUNT)
		self.assertEqual(self.mapped["counts"]["tech_scored"], EXPECTED_TECH_SCORE_COUNT)
		self.assertEqual(
			cstr_int(self.mapped["evaluation_setup"]["technical_pass_mark"]),
			EXPECTED_TECH_PASS,
		)
		self.assertEqual(
			cstr_int(self.mapped["evaluation_setup"]["technical_scoring_total"]),
			EXPECTED_TECH_TOTAL,
		)
		scored_marks = sum(
			int(c["marks"])
			for c in self.mapped["evaluation_setup"]["criteria"]
			if c.get("evaluation_basis") == "Scored"
		)
		self.assertEqual(scored_marks, EXPECTED_TECH_TOTAL)

	def test_forms_and_scc_counts(self):
		self.assertEqual(self.mapped["counts"]["forms"], EXPECTED_FORMS_COUNT)
		self.assertEqual(self.mapped["counts"]["scc"], EXPECTED_SCC_COUNT)

	def test_requirement_enums_valid(self):
		for row in self.mapped["it_requirements"]:
			self.assertIn(row["category_label"], CATEGORIES, row["requirement_id"])
			self.assertIn(row["bidder_response_format"], RESPONSE_FORMATS, row["requirement_id"])
			self.assertTrue(row["title"], row["requirement_id"])
			self.assertNotRegex(row["title"], r"^REQ-\d+$")
			# PDF-facing description must not embed audit source_id traces.
			self.assertNotIn("source_id=", row["description"])
			self.assertTrue(row.get("_audit_source_id"), row["requirement_id"])

	def test_family_and_response_mapping(self):
		self.assertEqual(map_requirement_family("Integration Requirements"), "Integration")
		self.assertEqual(
			map_requirement_family("Warranty, Post-Implementation and Annual Maintenance Support Requirements"),
			"Support & Warranty",
		)
		fmt, evid, _ = map_bidder_response("compliance_statement_plus_evidence_upload")
		self.assertEqual(fmt, "Compliance statement")
		self.assertEqual(evid, "Evidence required")

	def test_inventory_disclosable_rows(self):
		inv = self.mapped["system_inventory"]
		self.assertGreaterEqual(len(inv["items"]), 1)
		for item in inv["items"]:
			self.assertEqual(item["disclosure_status_label"], "Safe to disclose")

	def test_schema_10_artifact_keys(self):
		schema = self.mapped["bidder_submission_schema"]
		self.assertIn("sections", schema)
		self.assertIn("submission_policy", schema)
		self.assertIn("_kentender_artifact", schema)
		self.assertEqual(
			schema["_kentender_artifact"].get("kentender_submission_policy"),
			"electronic_only",
		)
		loaded = load_schema_10()
		self.assertIn("sections", loaded)

	def test_official_std_cfg_enumerations(self):
		"""Every Select/YN enum on CFG-01…09 must be an official wizard/STD option."""
		problems = assert_mapped_cfg_enums_valid(self.mapped)
		self.assertEqual(problems, [], problems)
		elig = self.mapped["tds_values"].get("eligible_tenderers")
		self.assertIn(elig, ELIGIBLE_TENDERS)
		self.assertEqual(elig, "Open to all eligible tenderers")

	def test_requirement_titles_not_midword_truncated(self):
		"""Regression: fixture titles must not end mid-word relative to statements."""
		reqs = (
			self.fixture.get("configuration", {})
			.get("CFG-03 IT Requirements", {})
			.get("requirements")
			or []
		)
		bad = []
		for row in reqs:
			title = (row.get("requirement_title") or "").strip()
			stmt = (row.get("requirement_statement") or "").strip()
			if not title or not stmt or not stmt.startswith(title):
				continue
			rest = stmt[len(title) :]
			if title[-1:].isalnum() and rest[:1].isalnum():
				bad.append(row.get("requirement_id"))
		self.assertEqual(bad, [], f"mid-word truncated titles: {bad}")

	def test_price_schedule_units_from_nssf_users_qty(self):
		"""Lump sum / monthly / annual must not be mapped as Users."""
		by_id = {i["item_id"]: i for i in self.mapped["price_schedule"]["items"]}
		self.assertEqual(by_id["PRICE-00"]["unit"], "Users")
		self.assertEqual(by_id["PRICE-00"]["pricing_basis"], "Per user")
		self.assertEqual(by_id["PRICE-07"]["unit"], "Lump sum")
		self.assertEqual(by_id["PRICE-07"]["pricing_basis"], "Lump sum")
		self.assertEqual(by_id["PRICE-15"]["unit"], "Per month")
		self.assertEqual(by_id["PRICE-15"]["pricing_basis"], "Monthly")
		self.assertEqual(by_id["PRICE-16"]["unit"], "Per GB/month")
		self.assertEqual(by_id["PRICE-18"]["unit"], "Annual")
		self.assertEqual(by_id["PRICE-18"]["pricing_basis"], "Annual")

	def test_map_price_users_or_qty_helper(self):
		self.assertEqual(map_price_users_or_qty("5"), ("5", "Users", "Per user"))
		self.assertEqual(map_price_users_or_qty("Lump sum"), ("1", "Lump sum", "Lump sum"))
		self.assertEqual(map_price_users_or_qty("Per month"), ("1", "Per month", "Monthly"))
		self.assertEqual(map_price_users_or_qty("Annual"), ("1", "Annual", "Annual"))

	def test_tds_deadlines_and_indemnity_normalized(self):
		tds = self.mapped["tds_values"]
		self.assertEqual(tds["tender_submission_deadline"], "2027-06-30T11:00")
		self.assertEqual(tds["tender_opening_datetime"], "2027-06-30T11:00")
		self.assertEqual(tds["clarification_deadline"], "2027-06-23T11:00")
		self.assertEqual(tds["professional_indemnity_required"], "Required")
		self.assertEqual(tds["professional_indemnity_amount"], "500000")
		self.assertIn("Upload valid professional indemnity", tds["professional_indemnity_evidence"])
		self.assertEqual(tds.get("opening_notes") or "", "")
		self.assertNotIn("2026-06-30", tds["opening_location"])
		audit = self.mapped["poc_audit_notes"]
		self.assertIn("2026", str(audit.get("source_submission_deadline") or ""))
		self.assertEqual(audit.get("demo_submission_deadline"), "2027-06-30T11:00")

	def test_scc_values_not_placeholders(self):
		rows = self.mapped["contract_values"]["contract_values"]
		blob = " ".join(
			f"{r.get('item_label')} {r.get('value_or_obligation') or r.get('value')}" for r in rows
		).lower()
		for topic in (
			"governing law",
			"scope",
			"commencement",
			"24",
			"payment",
			"source code",
			"subcontract",
			"sla",
			"performance security",
			"warranty",
		):
			self.assertIn(topic, blob, msg=f"missing SCC topic: {topic}")
		for r in rows:
			val = (r.get("value_or_obligation") or r.get("value") or "").strip().lower()
			self.assertNotEqual(val, "as specified")

	def test_digitized_prelim_are_linked_sections_not_uploads(self):
		"""NSSF-GOLD-017 family: FoT / CITD / SD / security never mandatory uploads."""
		prelim = [
			c
			for c in self.mapped["evaluation_setup"]["criteria"]
			if c.get("stage") == "Preliminary"
		]
		self.assertEqual(len(prelim), EXPECTED_PRELIM_COUNT)
		by_id = {c["criterion_id"]: c for c in prelim}
		self.assertNotIn("PRELIM-INDEMNITY-01", by_id)

		expected = {
			"PRELIM-05": "tender_security",
			"PRELIM-06": "form_of_tender",
			"PRELIM-07": "statutory_declarations",
			"PRELIM-08": "statutory_declarations",
		}
		for cid, section in expected.items():
			row = by_id[cid]
			self.assertEqual(row["response_method"], "linked_section", cid)
			self.assertEqual(row["linked_section_key"], section, cid)
			self.assertEqual(row["fulfilment_method"], "electronic_section", cid)
			self.assertEqual(row["owner"], section, cid)

		for cid in ("PRELIM-01", "PRELIM-02", "PRELIM-03", "PRELIM-04", "PRELIM-09"):
			self.assertEqual(by_id[cid]["response_method"], "upload", cid)
			self.assertEqual(by_id[cid]["fulfilment_method"], "tender_evidence", cid)


def cstr_int(val) -> int:
	return int(str(val).strip())
