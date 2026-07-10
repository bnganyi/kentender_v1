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
	"parameters": 51,
	"rules": 22,
	"forms": 18,
	"requirements": 1,
	"priceSchedules": 6,
	"schemas": 1,
	"renderBlocks": 14,
}


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
		parameter_key = frappe.get_all(
			"STD Parameter",
			filters={
				"package_id": CANONICAL_PACKAGE_ID,
				"title": "Address for clarifications",
			},
			pluck="name",
			limit=1,
		)[0]
		out = get_std_parameter(parameter_key)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["id"], parameter_key)
		self.assertEqual(out["data"]["code"], "tds.clarification_address")
		self.assertEqual(out["data"]["name"], "Address for clarifications")
		self.assertEqual(out["data"]["fieldType"], "LONG_TEXT")
		self.assertTrue(out["data"]["required"])
		self.assertEqual(out["data"]["sectionTitle"], "Section II - Tender Data Sheet")

	def test_parameter_detail_resolves_validation_rule_business_codes(self) -> None:
		parameter_key = frappe.get_all(
			"STD Parameter",
			filters={
				"package_id": CANONICAL_PACKAGE_ID,
				"title": "Clarification deadline before submission",
			},
			pluck="name",
			limit=1,
		)[0]
		out = get_std_parameter(parameter_key)
		_assert_envelope(self, out)
		self.assertEqual(len(out["data"]["validationRules"]), 1)
		rule = out["data"]["validationRules"][0]
		self.assertEqual(rule["code"], "tds.clarification_deadline_before_submission")
		self.assertEqual(rule["severity"], "BLOCKER")
		self.assertNotIn("KE-PPRA-IT-2022-04.rule.", rule["code"])

	def test_render_block_list_returns_business_codes(self) -> None:
		out = get_std_version_render_blocks(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		sample = next(item for item in out["data"]["renderBlocks"] if item["code"] == "gcc")
		self.assertEqual(sample["name"], "Section X - General Conditions of Contract")
		self.assertNotIn("KE-PPRA-IT-2022-04.render_block.", sample["code"])

	def test_rule_detail(self) -> None:
		rule_key = frappe.get_all(
			"STD Rule",
			filters={
				"package_id": CANONICAL_PACKAGE_ID,
				"title": "Clarification deadline must fall before tender submission deadline.",
			},
			pluck="name",
			limit=1,
		)[0]
		out = get_std_rule(rule_key)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["id"], rule_key)
		self.assertEqual(out["data"]["code"], "tds.clarification_deadline_before_submission")
		self.assertEqual(
			out["data"]["name"],
			"Clarification deadline must fall before tender submission deadline.",
		)
		self.assertEqual(out["data"]["ruleType"], "VALIDATION")
		self.assertEqual(out["data"]["severity"], "BLOCKER")
		self.assertTrue(out["data"]["affectedParameterKeys"])

	def test_form_detail_includes_fields(self) -> None:
		form_key = frappe.get_all(
			"STD Form Schema",
			filters={
				"package_id": CANONICAL_PACKAGE_ID,
				"title": "Certificate of Independent Tender Determination",
			},
			pluck="name",
			limit=1,
		)[0]
		out = get_std_form(form_key)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["id"], form_key)
		self.assertEqual(out["data"]["code"], "CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION")
		self.assertEqual(out["data"]["name"], "Certificate of Independent Tender Determination")
		self.assertEqual(out["data"]["respondentType"], "TENDERER")
		self.assertGreater(len(out["data"]["formFields"]), 0)
		field = out["data"]["formFields"][0]
		for key in ("id", "code", "name", "fieldType"):
			self.assertIn(key, field)
		self.assertEqual(field["code"], "DECLARANT_NAME")

	def test_rule_list_returns_business_codes(self) -> None:
		out = get_std_version_rules(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		sample = next(
			item
			for item in out["data"]["rules"]
			if item["code"] == "tds.clarification_deadline_before_submission"
		)
		self.assertNotIn("KE-PPRA-IT-2022-04.rule.", sample["code"])

	def test_parameter_list_includes_schema_fields(self) -> None:
		out = get_std_version_parameters(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		sample = next(
			item for item in out["data"]["parameters"] if item["code"] == "tds.clarification_address"
		)
		for field in (
			"fieldType",
			"sectionTitle",
			"required",
			"validationRuleCount",
			"renderBindingCount",
		):
			with self.subTest(field=field):
				self.assertIn(field, sample)
		self.assertEqual(sample["fieldType"], "LONG_TEXT")
		self.assertTrue(sample["required"])

	def test_rule_list_includes_schema_fields(self) -> None:
		out = get_std_version_rules(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		sample = next(
			item
			for item in out["data"]["rules"]
			if item["code"] == "tds.clarification_deadline_before_submission"
		)
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
		self.assertEqual(summary["blockerRules"], 19)
		self.assertEqual(summary["warningRules"], 3)
		self.assertEqual(summary["activeRules"], SCHEMA_COUNTS["rules"])
		self.assertGreater(out["validationSummary"]["blockers"], 0)

	def test_rule_list_filters_by_parameter_key(self) -> None:
		parameter_key = frappe.get_all(
			"STD Parameter",
			filters={
				"package_id": CANONICAL_PACKAGE_ID,
				"title": "Clarification deadline before submission",
			},
			pluck="name",
			limit=1,
		)[0]
		filtered = get_std_version_rules(CANONICAL_PACKAGE_ID, parameter_key=parameter_key)
		full = get_std_version_rules(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, filtered)
		self.assertGreater(filtered["data"]["count"], 0)
		self.assertLess(filtered["data"]["count"], full["data"]["count"])
		self.assertEqual(filtered["data"]["count"], filtered["data"]["summary"]["total"])
		self.assertLess(filtered["data"]["summary"]["total"], full["data"]["summary"]["total"])

	def test_not_found_envelopes(self) -> None:
		missing = get_std_parameter("DOES-NOT-EXIST")
		self.assertEqual(missing["error_code"], "STD_PARAMETER_NOT_FOUND")
		_assert_envelope(self, missing)

		missing_form = get_std_form("DOES-NOT-EXIST")
		self.assertEqual(missing_form["error_code"], "STD_FORM_NOT_FOUND")

		missing_list = get_std_version_parameters("DOES-NOT-EXIST")
		self.assertEqual(missing_list["error_code"], "STD_VERSION_NOT_FOUND")
