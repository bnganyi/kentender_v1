# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-07 — schema read API contract tests (TDD first)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.read import (
	get_std_form,
	get_std_parameter,
	get_std_rule,
	get_std_version_evaluation_schema,
	get_std_version_forms,
	get_std_version_parameters,
	get_std_version_price_schedules,
	get_std_version_render_blocks,
	get_std_version_requirements,
	get_std_version_rules,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path
from kentender_procurement.std_engine.services.envelope import ENVELOPE_KEYS
from kentender_procurement.std_engine.tests.test_be_04_commit_importer import (
	clear_canonical_package_state,
)

SCHEMA_COUNTS = {
	"parameters": 155,
	"rules": 22,
	"forms": 25,
	"requirements": 1,
	"priceSchedules": 6,
	"schemas": 1,
	"renderBlocks": 17,
}

PARAM_TDS_013 = "KE-PPRA-IT-2022-04.parameter.tds.013"
PARAM_TDS_021 = "KE-PPRA-IT-2022-04.parameter.tds.021"
FORM_IT_003 = "KE-PPRA-IT-2022-04.form.it_form_003"
RULE_TDS_021 = "KE-PPRA-IT-2022-04.rule.tds.validation_021"


def _assert_envelope(test_case: IntegrationTestCase, payload: dict) -> None:
	for key in ENVELOPE_KEYS:
		with test_case.subTest(envelope=key):
			test_case.assertIn(key, payload)


class TestBe07SchemaReadApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		clear_canonical_package_state()
		CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()

	@classmethod
	def tearDownClass(cls) -> None:
		clear_canonical_package_state()
		super().tearDownClass()

	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_version_schema_lists_return_counts(self) -> None:
		cases = (
			(get_std_version_parameters, "parameters"),
			(get_std_version_rules, "rules"),
			(get_std_version_forms, "forms"),
			(get_std_version_requirements, "requirements"),
			(get_std_version_price_schedules, "priceSchedules"),
			(get_std_version_render_blocks, "renderBlocks"),
		)
		for api_fn, key in cases:
			with self.subTest(api=key):
				out = api_fn(CANONICAL_PACKAGE_ID)
				_assert_envelope(self, out)
				self.assertEqual(out["data"]["count"], SCHEMA_COUNTS[key])
				self.assertEqual(len(out["data"][key]), SCHEMA_COUNTS[key])
				self.assertEqual(out["packageContext"]["packageId"], CANONICAL_PACKAGE_ID)
				item = out["data"][key][0]
				for field in ("id", "code", "name"):
					self.assertIn(field, item)

	def test_evaluation_schema_list(self) -> None:
		out = get_std_version_evaluation_schema(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["count"], SCHEMA_COUNTS["schemas"])
		self.assertEqual(len(out["data"]["schemas"]), 1)

	def test_parameter_detail(self) -> None:
		out = get_std_parameter(PARAM_TDS_013)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["id"], PARAM_TDS_013)
		self.assertEqual(out["data"]["code"], "tds.013")
		self.assertEqual(out["data"]["name"], "Clarification street address")
		self.assertEqual(out["data"]["fieldType"], "ADDRESS")
		self.assertTrue(out["data"]["required"])
		self.assertEqual(out["data"]["sectionTitle"], "Section II - Tender Data Sheet")

	def test_parameter_detail_resolves_validation_rule_business_codes(self) -> None:
		out = get_std_parameter(PARAM_TDS_021)
		_assert_envelope(self, out)
		self.assertEqual(len(out["data"]["validationRules"]), 1)
		rule = out["data"]["validationRules"][0]
		self.assertEqual(rule["code"], "tds.validation_021")
		self.assertEqual(rule["severity"], "BLOCKER")
		self.assertNotIn("KE-PPRA-IT-2022-04.rule.", rule["code"])

	def test_render_block_list_returns_business_codes(self) -> None:
		out = get_std_version_render_blocks(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		sample = next(item for item in out["data"]["renderBlocks"] if item["code"] == "gcc")
		self.assertEqual(sample["name"], "Section X - General Conditions of Contract")
		self.assertNotIn("KE-PPRA-IT-2022-04.render_block.", sample["code"])

	def test_rule_detail(self) -> None:
		out = get_std_rule(RULE_TDS_021)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["id"], RULE_TDS_021)
		self.assertEqual(out["data"]["code"], "tds.validation_021")
		self.assertEqual(
			out["data"]["name"],
			"Clarification request deadline offset must be populated before tender publication.",
		)
		self.assertEqual(out["data"]["ruleType"], "VALIDATION")
		self.assertEqual(out["data"]["severity"], "BLOCKER")
		self.assertTrue(out["data"]["affectedParameterKeys"])

	def test_form_detail_includes_fields(self) -> None:
		out = get_std_form(FORM_IT_003)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["id"], FORM_IT_003)
		self.assertEqual(out["data"]["code"], "IT-FORM-003")
		self.assertEqual(out["data"]["name"], "Certificate of Independent Tender Determination")
		self.assertEqual(out["data"]["respondentType"], "Tenderer")
		self.assertGreater(len(out["data"]["formFields"]), 0)
		field = out["data"]["formFields"][0]
		for key in ("id", "code", "name", "fieldType"):
			self.assertIn(key, field)
		self.assertEqual(field["code"], "reference")
		self.assertEqual(field["name"], "Reference")

	def test_rule_list_returns_business_codes(self) -> None:
		out = get_std_version_rules(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		sample = next(item for item in out["data"]["rules"] if item["code"] == "tds.validation_021")
		self.assertNotIn("KE-PPRA-IT-2022-04.rule.", sample["code"])

	def test_parameter_list_includes_schema_fields(self) -> None:
		out = get_std_version_parameters(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		sample = next(item for item in out["data"]["parameters"] if item["code"] == "tds.013")
		for field in (
			"fieldType",
			"sectionTitle",
			"required",
			"validationRuleCount",
			"renderBindingCount",
		):
			with self.subTest(field=field):
				self.assertIn(field, sample)
		self.assertEqual(sample["fieldType"], "ADDRESS")
		self.assertTrue(sample["required"])
		self.assertEqual(sample["validationRuleCount"], 1)

	def test_rule_list_includes_schema_fields(self) -> None:
		out = get_std_version_rules(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		sample = next(item for item in out["data"]["rules"] if item["code"] == "tds.validation_021")
		for field in ("ruleType", "severity", "affectedObject", "lifecycleStage", "isActive"):
			with self.subTest(field=field):
				self.assertIn(field, sample)
		self.assertEqual(sample["ruleType"], "VALIDATION")
		self.assertEqual(sample["severity"], "BLOCKER")
		self.assertTrue(sample["isActive"])

	def test_rule_list_returns_summary_kpis(self) -> None:
		out = get_std_version_rules(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		summary = out["data"]["summary"]
		for field in ("total", "blockerRules", "warningRules", "infoRules", "activeRules"):
			with self.subTest(field=field):
				self.assertIn(field, summary)
		self.assertEqual(summary["total"], out["data"]["count"])
		self.assertEqual(summary["total"], SCHEMA_COUNTS["rules"])
		self.assertEqual(summary["blockerRules"], 22)
		self.assertEqual(summary["warningRules"], 0)
		self.assertEqual(summary["activeRules"], SCHEMA_COUNTS["rules"])
		self.assertGreater(out["validationSummary"]["blockers"], 0)

	def test_rule_list_filters_by_parameter_key(self) -> None:
		filtered = get_std_version_rules(CANONICAL_PACKAGE_ID, parameter_key=PARAM_TDS_021)
		full = get_std_version_rules(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, filtered)
		self.assertEqual(filtered["data"]["count"], 1)
		self.assertLess(filtered["data"]["count"], full["data"]["count"])
		self.assertEqual(filtered["data"]["count"], filtered["data"]["summary"]["total"])
		self.assertLess(filtered["data"]["summary"]["total"], full["data"]["summary"]["total"])

	def test_price_schedule_list_returns_design_row_fields(self) -> None:
		out = get_std_version_price_schedules(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["count"], SCHEMA_COUNTS["priceSchedules"])
		summary = out["data"]["summary"]
		self.assertEqual(summary["priceSchedules"], SCHEMA_COUNTS["priceSchedules"])
		self.assertGreaterEqual(summary["totalSummaries"], 2)
		codes = {item["code"] for item in out["data"]["priceSchedules"]}
		self.assertIn("GS-001", codes)
		self.assertIn("COO-001", codes)
		grand_summary = next(item for item in out["data"]["priceSchedules"] if item["code"] == "GS-001")
		for field in (
			"pricingBasis",
			"currencyPolicy",
			"taxPolicy",
			"recurrentCost",
			"formulaRule",
			"evalLinkage",
			"contractCarry",
			"validationStatus",
			"lifecycleState",
		):
			with self.subTest(field=field):
				self.assertIn(field, grand_summary)
				self.assertTrue(grand_summary[field])
		self.assertIn("required", grand_summary)
		self.assertIn("sourceAnchorId", grand_summary)

	def test_form_list_returns_design_row_fields(self) -> None:
		out = get_std_version_forms(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["count"], SCHEMA_COUNTS["forms"])
		item = out["data"]["forms"][0]
		for field in (
			"respondentType",
			"stage",
			"fieldCount",
			"evidenceCount",
			"activationRules",
			"sourceAnchorId",
		):
			with self.subTest(field=field):
				self.assertIn(field, item)

	def test_requirement_list_returns_design_row_fields(self) -> None:
		out = get_std_version_requirements(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["count"], SCHEMA_COUNTS["requirements"])
		item = out["data"]["requirements"][0]
		for field in (
			"category",
			"requirementClass",
			"requirementType",
			"responseRequired",
			"complianceResponseType",
			"evalLinkage",
			"contractCarryForward",
		):
			with self.subTest(field=field):
				self.assertIn(field, item)

	def test_not_found_envelopes(self) -> None:
		missing = get_std_parameter("DOES-NOT-EXIST")
		self.assertEqual(missing["error_code"], "STD_PARAMETER_NOT_FOUND")
		_assert_envelope(self, missing)

		missing_form = get_std_form("DOES-NOT-EXIST")
		self.assertEqual(missing_form["error_code"], "STD_FORM_NOT_FOUND")

		missing_list = get_std_version_parameters("DOES-NOT-EXIST")
		self.assertEqual(missing_list["error_code"], "STD_VERSION_NOT_FOUND")
