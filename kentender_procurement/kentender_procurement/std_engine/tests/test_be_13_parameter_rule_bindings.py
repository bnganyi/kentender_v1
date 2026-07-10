# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-13 — parameter↔rule bindings and price schedule business code contracts."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path
from kentender_procurement.std_engine.services.schema_read_service import (
	_price_schedule_business_code,
	_resolve_price_schedule_semantic_key,
	get_std_parameter,
	get_std_version_parameters,
	get_std_version_price_schedules,
)
from kentender_procurement.std_engine.tests.test_be_04_commit_importer import (
	clear_canonical_package_state,
)

PARAM_TDS_013 = "KE-PPRA-IT-2022-04.parameter.tds.013"
PARAM_TDS_021 = "KE-PPRA-IT-2022-04.parameter.tds.021"
RULE_TDS_013 = "KE-PPRA-IT-2022-04.rule.tds.validation_013"
RULE_TDS_021 = "KE-PPRA-IT-2022-04.rule.tds.validation_021"


class TestBe13ParameterRuleBindings(IntegrationTestCase):
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

	def test_tds_parameters_have_validation_rule_keys_in_metadata(self) -> None:
		meta = json.loads(
			frappe.db.get_value("STD Parameter", PARAM_TDS_013, "metadata_json") or "{}"
		)
		self.assertIn(RULE_TDS_013, meta.get("validation_rule_keys") or [])

		meta_021 = json.loads(
			frappe.db.get_value("STD Parameter", PARAM_TDS_021, "metadata_json") or "{}"
		)
		self.assertEqual(meta_021.get("validation_rule_keys"), [RULE_TDS_021])

	def test_parameter_list_exposes_validation_rule_count(self) -> None:
		out = get_std_version_parameters(CANONICAL_PACKAGE_ID)
		sample = next(item for item in out["data"]["parameters"] if item["code"] == "tds.021")
		self.assertEqual(sample["validationRuleCount"], 1)

	def test_parameter_detail_resolves_bound_validation_rules(self) -> None:
		out = get_std_parameter(PARAM_TDS_021)
		self.assertEqual(len(out["data"]["validationRules"]), 1)
		rule = out["data"]["validationRules"][0]
		self.assertEqual(rule["code"], "tds.validation_021")
		self.assertEqual(rule["severity"], "BLOCKER")

	def test_price_schedule_business_code_maps_it_price_codes(self) -> None:
		self.assertEqual(_resolve_price_schedule_semantic_key("IT-PRICE-01"), "GRAND_SUMMARY_COST_TABLE")
		self.assertEqual(_price_schedule_business_code("IT-PRICE-01", ""), "GS-001")
		self.assertEqual(_price_schedule_business_code("IT-PRICE-06", ""), "COO-001")

	def test_price_schedule_list_returns_profiles_for_it_price_codes(self) -> None:
		out = get_std_version_price_schedules(CANONICAL_PACKAGE_ID)
		grand_summary = next(item for item in out["data"]["priceSchedules"] if item["code"] == "GS-001")
		self.assertEqual(grand_summary["name"], "Grand Summary Cost Table")
		self.assertEqual(grand_summary["pricingBasis"], "Aggregated Total")
		self.assertEqual(grand_summary["formulaRule"], "Summation of Sub-Schedules")
		self.assertNotIn("KE-PPRA-IT-2022-04.price_schedule.", grand_summary["code"])
