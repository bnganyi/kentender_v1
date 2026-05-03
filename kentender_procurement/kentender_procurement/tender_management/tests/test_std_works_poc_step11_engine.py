# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 11 — template engine service tests.

Covers STEP11-AC-001..014 from the Step 11 specification, plus §11 message
shape, §12 rule-handling details, §14 status mapping, §17 error handling,
§18 transaction discipline, and §16 persistence-no-save guarantees. Spec
§22 defers a "full automated test suite"; the workspace TDD gate still
requires regression evidence, so this focused test module extends the
**STD-POC-004..011** pattern (see **STD-POC-012**).

Run:
    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_step11_engine
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_engine
from kentender_procurement.tender_management.services.std_template_engine import (
	BLOCKING_SEVERITIES,
	SEVERITY_TO_STATUS,
	SUPPORTED_CHILD_TABLES,
	SUPPORTED_OPERATORS,
	SUPPORTED_RULE_TYPES,
	VALID_TEMPLATE_COMPONENTS,
	apply_config_to_tender_doc,
	build_render_context,
	build_validation_message_rows,
	evaluate_condition,
	get_package_component,
	hash_config,
	initialize_config,
	load_sample_boq_rows,
	load_sample_config,
	load_sample_lots,
	load_template,
	populate_sample_tender,
	resolve_active_sections,
	resolve_required_forms,
	rule_applies,
	validate_config,
	write_required_forms_to_tender,
	write_validation_to_tender,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

REQUIRED_FUNCTIONS = (
	"load_template",
	"get_package_component",
	"initialize_config",
	"load_sample_config",
	"load_sample_lots",
	"load_sample_boq_rows",
	"hash_config",
	"evaluate_condition",
	"rule_applies",
	"validate_config",
	"resolve_active_sections",
	"resolve_required_forms",
	"build_validation_message_rows",
	"build_render_context",
	"apply_config_to_tender_doc",
	"populate_sample_tender",
	"write_validation_to_tender",
	"write_required_forms_to_tender",
)

EXPECTED_VALIDATION_KEYS = {
	"ok",
	"status",
	"blocks_generation",
	"messages",
	"active_fields",
	"active_sections",
	"active_forms",
	"required_fields",
	"configuration_hash",
}

EXPECTED_RENDER_CONTEXT_KEYS = {
	"template",
	"manifest",
	"configuration",
	"active_sections",
	"lots",
	"boq_items",
	"required_forms",
	"validation",
	"audit",
}

EXPECTED_REQUIRED_FORM_ROW_KEYS = {
	"form_code",
	"form_title",
	"display_group",
	"workflow_stage",
	"stage",
	"respondent_type",
	"required",
	"activation_source",
	"evidence_policy",
	"display_order",
	"notes",
	"submission_component_code",
	"required_because",
	"source_rule_code",
}

PRIMARY_SAMPLE_ACTIVATED_FORMS = [
	"FORM_OF_TENDER",
	"FORM_CONFIDENTIAL_BUSINESS_QUESTIONNAIRE",
	"FORM_CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION",
	"FORM_SELF_DECLARATION",
	"FORM_TENDER_SECURITY",
	"FORM_JV_INFORMATION",
	"FORM_ALTERNATIVE_TECHNICAL_PROPOSAL",
	"FORM_TECHNICAL_PROPOSAL",
	"FORM_SIMILAR_EXPERIENCE",
	"FORM_FINANCIAL_CAPACITY",
	"FORM_PERSONNEL_SCHEDULE",
	"FORM_EQUIPMENT_SCHEDULE",
	"FORM_BENEFICIAL_OWNERSHIP_DISCLOSURE",
	"FORM_PERFORMANCE_SECURITY",
	"FORM_ADVANCE_PAYMENT_SECURITY",
]

PRIMARY_SAMPLE_INACTIVE_FORMS = {
	"FORM_TENDER_SECURING_DECLARATION",
	"FORM_FOREIGN_TENDERER_LOCAL_INPUT",
	"FORM_RETENTION_MONEY_SECURITY",
}

DEFAULT_REQUIRED_FORM_CODES = {
	"FORM_OF_TENDER",
	"FORM_CONFIDENTIAL_BUSINESS_QUESTIONNAIRE",
	"FORM_CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION",
	"FORM_SELF_DECLARATION",
	"FORM_TECHNICAL_PROPOSAL",
	"FORM_SIMILAR_EXPERIENCE",
	"FORM_FINANCIAL_CAPACITY",
}

SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class TestStdWorksPocStep11Engine(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		# Ensure the STD Template record exists in this transaction.
		upsert_std_template()

	# ------------------------------------------------------------------
	# STEP11-AC-001..002 — module + public API surface
	# ------------------------------------------------------------------

	def test_step11_ac001_module_exists(self) -> None:
		self.assertTrue(
			std_template_engine.__file__.endswith(
				"tender_management/services/std_template_engine.py"
			),
			"STEP11-AC-001: engine must live at tender_management/services/std_template_engine.py",
		)

	def test_step11_ac002_required_public_functions_exist(self) -> None:
		for name in REQUIRED_FUNCTIONS:
			with self.subTest(function=name):
				self.assertTrue(
					hasattr(std_template_engine, name),
					f"STEP11-AC-002: engine must expose {name}",
				)
				self.assertTrue(
					callable(getattr(std_template_engine, name)),
					f"STEP11-AC-002: {name} must be callable",
				)

	# ------------------------------------------------------------------
	# STEP11-AC-003 — load_template and get_package_component
	# ------------------------------------------------------------------

	def test_step11_ac003_load_template_loads_package(self) -> None:
		template = load_template(TEMPLATE_CODE)
		self.assertEqual(set(template.keys()), {"doc", "package", "template_code", "package_hash"})
		self.assertEqual(template["template_code"], TEMPLATE_CODE)
		self.assertIsNotNone(SHA256_HEX_PATTERN.match(template["package_hash"]))
		self.assertGreaterEqual(
			set(template["package"].keys()),
			VALID_TEMPLATE_COMPONENTS,
		)

		with self.assertRaises(frappe.DoesNotExistError):
			load_template("BOGUS-TEMPLATE-DOES-NOT-EXIST")

	def test_get_package_component_validates_name(self) -> None:
		template = load_template(TEMPLATE_CODE)
		manifest = get_package_component(template, "manifest")
		self.assertIsInstance(manifest, dict)
		self.assertEqual(manifest["template_code"], TEMPLATE_CODE)

		with self.assertRaises(ValueError) as ctx:
			get_package_component(template, "bogus_component")
		self.assertIn("bogus_component", str(ctx.exception))

	# ------------------------------------------------------------------
	# STEP11-AC-004 — initialize_config
	# ------------------------------------------------------------------

	def test_step11_ac004_initialize_config_uses_defaults(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = initialize_config(template)
		field_codes = {
			f["field_code"]
			for f in template["package"]["fields"]["fields"]
			if isinstance(f, dict) and f.get("field_code")
		}
		self.assertEqual(len(field_codes), 75)
		self.assertGreaterEqual(set(config.keys()), field_codes)

		self.assertEqual(config["SYSTEM.TEMPLATE_CODE"], TEMPLATE_CODE)
		self.assertEqual(config["SYSTEM.PACKAGE_VERSION"], "0.1.0-poc")
		self.assertIsNotNone(SHA256_HEX_PATTERN.match(config["SYSTEM.PACKAGE_HASH"]))
		self.assertIsNone(config["SYSTEM.CONFIGURATION_HASH"])

		# default_value passthrough — TENDER fields default to None per fields.json
		self.assertIsNone(config["TENDER.PROCURING_ENTITY_NAME"])
		# Select fields with a default value pass through unchanged
		self.assertEqual(config["METHOD.PROCUREMENT_METHOD"], "OPEN_COMPETITIVE_TENDERING")
		self.assertEqual(config["METHOD.TENDER_SCOPE"], "NATIONAL")

	# ------------------------------------------------------------------
	# STEP11-AC-005..006 — sample config + variant overrides
	# ------------------------------------------------------------------

	def test_step11_ac005_load_sample_config_returns_full_dict(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		self.assertEqual(len(config), 75)
		self.assertEqual(config["TENDER.TENDER_NAME"], "Construction of Ward Administration Block")
		self.assertEqual(config["METHOD.TENDER_SCOPE"], "NATIONAL")

		# Mutating the returned dict must not affect future calls (deep copy).
		config["TENDER.TENDER_NAME"] = "MUTATED"
		fresh = load_sample_config(template)
		self.assertEqual(fresh["TENDER.TENDER_NAME"], "Construction of Ward Administration Block")

	def test_step11_ac006_variant_overrides_applied(self) -> None:
		template = load_template(TEMPLATE_CODE)

		international = load_sample_config(template, variant_code="VARIANT-INTERNATIONAL")
		self.assertEqual(international["METHOD.TENDER_SCOPE"], "INTERNATIONAL")
		self.assertTrue(international["PARTICIPATION.FOREIGN_TENDERER_LOCAL_INPUT_RULE_APPLICABLE"])
		# Primary sample still NATIONAL after the variant call (no mutation).
		self.assertEqual(load_sample_config(template)["METHOD.TENDER_SCOPE"], "NATIONAL")

		single_lot = load_sample_lots(template, variant_code="VARIANT-SINGLE-LOT")
		self.assertEqual(len(single_lot), 1)
		self.assertEqual(single_lot[0]["lot_code"], "LOT-001")
		self.assertEqual(len(load_sample_lots(template)), 2)

		# Empty boq_overrides → primary BoQ rows
		single_lot_boq = load_sample_boq_rows(template, variant_code="VARIANT-SINGLE-LOT")
		self.assertEqual(len(single_lot_boq), 9)

		with self.assertRaises(ValueError) as ctx:
			load_sample_config(template, variant_code="VARIANT-DOES-NOT-EXIST")
		self.assertIn("VARIANT-DOES-NOT-EXIST", str(ctx.exception))

	# ------------------------------------------------------------------
	# STEP11-AC-007 — deterministic config hash (§13)
	# ------------------------------------------------------------------

	def test_step11_ac007_hash_config_is_deterministic(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		first = hash_config(config)
		second = hash_config(config)
		self.assertEqual(first, second, "STEP11-AC-007: hash must be deterministic")
		self.assertIsNotNone(SHA256_HEX_PATTERN.match(first))

		# Order-insensitive thanks to sort_keys.
		reordered = {k: config[k] for k in reversed(list(config))}
		self.assertEqual(hash_config(reordered), first)

		# Mutation changes the hash.
		mutated = dict(config)
		mutated["TENDER.TENDER_NAME"] = "Different"
		self.assertNotEqual(hash_config(mutated), first)

	# ------------------------------------------------------------------
	# STEP11-AC-008 — REQUIRE_FIELD with boolean / numeric edge cases (§12.1)
	# ------------------------------------------------------------------

	def test_step11_ac008_require_field_blocker(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		lots = load_sample_lots(template)
		boq_items = load_sample_boq_rows(template)

		# Primary sample passes cleanly — sanity check before the mutation.
		clean = validate_config(template, config, lots=lots, boq_items=boq_items)
		self.assertEqual(clean["status"], "Passed")
		self.assertFalse(clean["blocks_generation"])
		self.assertEqual(clean["messages"], [])

		# Mutate to remove a required core identity field.
		mutated = dict(config)
		mutated["TENDER.PROCURING_ENTITY_NAME"] = ""
		result = validate_config(template, mutated, lots=lots, boq_items=boq_items)
		self.assertTrue(result["blocks_generation"])
		self.assertEqual(result["status"], "Blocked")
		blocker_codes = {
			m["rule_code"] for m in result["messages"] if m["severity"] == "BLOCKER"
		}
		self.assertIn("RULE_REQUIRED_CORE_TENDER_IDENTITY", blocker_codes)
		fields_in_messages = {
			m["affected_field"] for m in result["messages"] if m.get("affected_field")
		}
		self.assertIn("TENDER.PROCURING_ENTITY_NAME", fields_in_messages)

		# §12.1: boolean False and numeric 0 are not "empty" — rules requiring
		# present fields with these values must still pass.
		zero_config = dict(config)
		zero_config["CONTRACT.RETENTION_PERCENTAGE"] = 0
		zero_config["WORKS.DRAWINGS_REQUIRED"] = False
		result2 = validate_config(template, zero_config, lots=lots, boq_items=boq_items)
		blocker_fields_2 = {
			m["affected_field"] for m in result2["messages"] if m["severity"] == "BLOCKER"
		}
		self.assertNotIn("CONTRACT.RETENTION_PERCENTAGE", blocker_fields_2)
		self.assertNotIn("WORKS.DRAWINGS_REQUIRED", blocker_fields_2)

	# ------------------------------------------------------------------
	# STEP11-AC-009 — REQUIRE_CHILD_ROWS
	# ------------------------------------------------------------------

	def test_step11_ac009_require_child_rows_blocker(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		lots = load_sample_lots(template)

		# No BoQ rows at all → BoQ + dayworks + provisional sums all block.
		result = validate_config(template, config, lots=lots, boq_items=[])
		blocker_codes = {
			m["rule_code"] for m in result["messages"] if m["severity"] == "BLOCKER"
		}
		self.assertIn("RULE_BOQ_REQUIRE_ROWS", blocker_codes)
		self.assertIn("RULE_DAYWORKS_REQUIRE_ROWS", blocker_codes)
		self.assertIn("RULE_PROVISIONAL_SUMS_REQUIRE_ROWS", blocker_codes)

		# Add a single non-DAYWORKS BoQ row → BoQ rule passes but dayworks +
		# provisional sums still block (row_filter not satisfied).
		one_boq_row = [
			{
				"item_code": "BQ-X",
				"lot_code": "LOT-001",
				"item_category": "PRELIMINARIES",
				"description": "x",
				"unit": "Item",
				"quantity": 1,
			}
		]
		result2 = validate_config(template, config, lots=lots, boq_items=one_boq_row)
		blocker_codes2 = {
			m["rule_code"] for m in result2["messages"] if m["severity"] == "BLOCKER"
		}
		self.assertNotIn("RULE_BOQ_REQUIRE_ROWS", blocker_codes2)
		self.assertIn("RULE_DAYWORKS_REQUIRE_ROWS", blocker_codes2)

	# ------------------------------------------------------------------
	# STEP11-AC-010 — VALIDATE_DATE_ORDER
	# ------------------------------------------------------------------

	def test_step11_ac010_validate_date_order(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		lots = load_sample_lots(template)
		boq_items = load_sample_boq_rows(template)

		# Push clarification deadline past submission → BLOCKER.
		bad = dict(config)
		bad["DATES.CLARIFICATION_DEADLINE"] = "2026-07-01T17:00:00"  # after submission
		result = validate_config(template, bad, lots=lots, boq_items=boq_items)
		blocker_codes = {
			m["rule_code"] for m in result["messages"] if m["severity"] == "BLOCKER"
		}
		self.assertIn("RULE_VALIDATE_CLARIFICATION_BEFORE_SUBMISSION", blocker_codes)

		# Opening exactly equal to submission is allowed (FIELD_ON_OR_AFTER_FIELD).
		equal_dates = dict(config)
		equal_dates["DATES.OPENING_DATETIME"] = config["DATES.SUBMISSION_DEADLINE"]
		result2 = validate_config(template, equal_dates, lots=lots, boq_items=boq_items)
		opening_blockers = {
			m["rule_code"]
			for m in result2["messages"]
			if m["severity"] == "BLOCKER"
			and m["rule_code"] == "RULE_VALIDATE_OPENING_NOT_BEFORE_SUBMISSION"
		}
		self.assertEqual(opening_blockers, set())

	# ------------------------------------------------------------------
	# STEP11-AC-011 — VALIDATE_NUMERIC_LIMIT
	# ------------------------------------------------------------------

	def test_step11_ac011_validate_numeric_limit(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		lots = load_sample_lots(template)
		boq_items = load_sample_boq_rows(template)

		# Primary sample (1.5%) passes.
		result_ok = validate_config(template, config, lots=lots, boq_items=boq_items)
		ok_codes = {m["rule_code"] for m in result_ok["messages"]}
		self.assertNotIn("RULE_TENDER_SECURITY_AMOUNT_LIMIT_2_PERCENT", ok_codes)

		# 2.5% of estimated cost → BLOCKER.
		over = dict(config)
		over["SECURITY.TENDER_SECURITY_AMOUNT"] = 2_500_000
		result = validate_config(template, over, lots=lots, boq_items=boq_items)
		blocker_codes = {
			m["rule_code"] for m in result["messages"] if m["severity"] == "BLOCKER"
		}
		self.assertIn("RULE_TENDER_SECURITY_AMOUNT_LIMIT_2_PERCENT", blocker_codes)

	# ------------------------------------------------------------------
	# STEP11-AC-012 — resolve_required_forms (default + activated)
	# ------------------------------------------------------------------

	def test_step11_ac012_resolve_required_forms_primary_sample(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		lots = load_sample_lots(template)
		boq_items = load_sample_boq_rows(template)
		result = validate_config(template, config, lots=lots, boq_items=boq_items)
		rows = resolve_required_forms(template, config, validation_result=result)

		codes_in_order = [row["form_code"] for row in rows]
		self.assertEqual(
			codes_in_order,
			PRIMARY_SAMPLE_ACTIVATED_FORMS,
			"STEP11-AC-012: primary sample must yield the 15 expected_activated_forms in display_order",
		)

		# Inactive forms must not appear.
		codes_set = set(codes_in_order)
		self.assertEqual(
			codes_set & PRIMARY_SAMPLE_INACTIVE_FORMS,
			set(),
			"STEP11-AC-012: inactive forms must not appear in required forms",
		)

		# Each row carries the 10 §10.12 keys with sane types.
		for row in rows:
			with self.subTest(form_code=row["form_code"]):
				self.assertEqual(set(row.keys()), EXPECTED_REQUIRED_FORM_ROW_KEYS)
				self.assertTrue(row["required"])
				sources = (row["activation_source"] or "").split("; ")
				if row["form_code"] in DEFAULT_REQUIRED_FORM_CODES:
					# Step 14 §8.4: a default-required form may also be activated
					# by a rule (e.g. FORM_TECHNICAL_PROPOSAL). Require DEFAULT
					# in the joined activation-source list.
					self.assertIn("DEFAULT", sources)
				else:
					self.assertTrue(
						any(s.startswith("RULE:") for s in sources),
						f"non-default form {row['form_code']} must record its activation rule",
					)

	# ------------------------------------------------------------------
	# STEP11-AC-013 — active sections + render context
	# ------------------------------------------------------------------

	def test_step11_ac013_resolve_active_sections_and_render_context(self) -> None:
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		lots = load_sample_lots(template)
		boq_items = load_sample_boq_rows(template)
		result = validate_config(template, config, lots=lots, boq_items=boq_items)

		sections = resolve_active_sections(template, config, validation_result=result)
		self.assertGreaterEqual(len(sections), 16)
		render_orders = [s["render_order"] for s in sections]
		self.assertEqual(render_orders, sorted(render_orders))

		required_forms = resolve_required_forms(template, config, validation_result=result)
		ctx = build_render_context(
			template,
			config,
			lots=lots,
			boq_items=boq_items,
			validation_result=result,
			required_forms=required_forms,
		)
		self.assertEqual(set(ctx.keys()), EXPECTED_RENDER_CONTEXT_KEYS)
		self.assertEqual(ctx["audit"]["template_code"], TEMPLATE_CODE)
		self.assertEqual(ctx["audit"]["configuration_hash"], result["configuration_hash"])
		self.assertEqual(len(ctx["lots"]), 2)
		self.assertEqual(len(ctx["boq_items"]), 9)
		self.assertEqual(len(ctx["required_forms"]), 15)
		self.assertEqual(ctx["validation"]["status"], "Passed")

	# ------------------------------------------------------------------
	# STEP11-AC-014 — no downstream implementation in this module
	# ------------------------------------------------------------------

	def test_step11_ac014_no_downstream_implementation(self) -> None:
		# Engine itself must not persist tender records in this test (count
		# diff vs. pre-test baseline; tolerates ambient site state from
		# manual UI testing on the same site).
		baseline = frappe.db.count("Procurement Tender")
		self.assertEqual(frappe.db.count("Procurement Tender"), baseline)

		# Source code must not contain whitelist decorator, HTML/PDF helpers, or wkhtmltopdf hooks.
		source = Path(std_template_engine.__file__).read_text(encoding="utf-8")
		for forbidden in ("@frappe.whitelist", "<html", "wkhtmltopdf", "pdfkit"):
			with self.subTest(forbidden=forbidden):
				self.assertNotIn(
					forbidden,
					source,
					f"STEP11-AC-014: engine must not include {forbidden!r}",
				)

	# ------------------------------------------------------------------
	# §11 + §14 — validation status mapping
	# ------------------------------------------------------------------

	def test_validation_status_mapping_table(self) -> None:
		self.assertEqual(SEVERITY_TO_STATUS[None], "Passed")
		self.assertEqual(SEVERITY_TO_STATUS["INFO"], "Passed")
		self.assertEqual(SEVERITY_TO_STATUS["WARNING"], "Passed With Warnings")
		self.assertEqual(SEVERITY_TO_STATUS["ERROR"], "Failed")
		self.assertEqual(SEVERITY_TO_STATUS["BLOCKER"], "Blocked")
		self.assertEqual(BLOCKING_SEVERITIES, {"ERROR", "BLOCKER"})

	def test_validate_config_status_with_warnings(self) -> None:
		# Trigger RULE_WARN_HIGH_JV_MEMBER_COUNT (WARNING_ONLY).
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		config["PARTICIPATION.MAX_JV_MEMBERS"] = 7
		lots = load_sample_lots(template)
		boq_items = load_sample_boq_rows(template)
		result = validate_config(template, config, lots=lots, boq_items=boq_items)
		self.assertEqual(result["status"], "Passed With Warnings")
		self.assertFalse(result["blocks_generation"])
		warning_codes = {m["rule_code"] for m in result["messages"] if m["severity"] == "WARNING"}
		self.assertIn("RULE_WARN_HIGH_JV_MEMBER_COUNT", warning_codes)

	# ------------------------------------------------------------------
	# §10.8 / §12.1 — operator coverage
	# ------------------------------------------------------------------

	def test_evaluate_condition_operators(self) -> None:
		cfg = {
			"S": "value",
			"N": 10,
			"B_FALSE": False,
			"ZERO": 0,
			"EMPTY_LIST": [],
			"NONE": None,
		}
		# EQUALS / NOT_EQUALS
		self.assertTrue(evaluate_condition({"field": "S", "operator": "EQUALS", "value": "value"}, cfg))
		self.assertFalse(evaluate_condition({"field": "S", "operator": "EQUALS", "value": "x"}, cfg))
		self.assertTrue(evaluate_condition({"field": "S", "operator": "NOT_EQUALS", "value": "x"}, cfg))

		# IS_TRUE / IS_FALSE
		self.assertTrue(evaluate_condition({"field": "B_FALSE", "operator": "IS_FALSE"}, cfg))
		self.assertFalse(evaluate_condition({"field": "ZERO", "operator": "IS_FALSE"}, cfg))

		# IS_EMPTY / IS_NOT_EMPTY — booleans/zero are NOT empty (§12.1)
		self.assertTrue(evaluate_condition({"field": "NONE", "operator": "IS_EMPTY"}, cfg))
		self.assertTrue(evaluate_condition({"field": "EMPTY_LIST", "operator": "IS_EMPTY"}, cfg))
		self.assertFalse(evaluate_condition({"field": "B_FALSE", "operator": "IS_EMPTY"}, cfg))
		self.assertFalse(evaluate_condition({"field": "ZERO", "operator": "IS_EMPTY"}, cfg))
		self.assertTrue(evaluate_condition({"field": "B_FALSE", "operator": "IS_NOT_EMPTY"}, cfg))
		self.assertTrue(evaluate_condition({"field": "ZERO", "operator": "IS_NOT_EMPTY"}, cfg))

		# Numeric comparisons
		self.assertTrue(evaluate_condition({"field": "N", "operator": "GREATER_THAN", "value": 5}, cfg))
		self.assertTrue(evaluate_condition({"field": "N", "operator": "GREATER_THAN_OR_EQUALS", "value": 10}, cfg))
		self.assertTrue(evaluate_condition({"field": "N", "operator": "LESS_THAN", "value": 11}, cfg))
		self.assertTrue(evaluate_condition({"field": "N", "operator": "LESS_THAN_OR_EQUALS", "value": 10}, cfg))

		# IN / NOT_IN
		self.assertTrue(evaluate_condition({"field": "S", "operator": "IN", "value": ["value", "other"]}, cfg))
		self.assertTrue(evaluate_condition({"field": "S", "operator": "NOT_IN", "value": ["x", "y"]}, cfg))

	def test_rule_applies_respects_enabled_flag(self) -> None:
		cfg = {"X": True}
		rule_yes = {
			"enabled": True,
			"when": {"all": [{"field": "X", "operator": "IS_TRUE"}]},
		}
		rule_disabled = {
			"enabled": False,
			"when": {"all": [{"field": "X", "operator": "IS_TRUE"}]},
		}
		rule_unconditional = {"enabled": True, "when": {"all": []}}
		self.assertTrue(rule_applies(rule_yes, cfg))
		self.assertFalse(rule_applies(rule_disabled, cfg))
		self.assertTrue(rule_applies(rule_unconditional, cfg))

	# ------------------------------------------------------------------
	# §17 — error handling for unsupported declarations
	# ------------------------------------------------------------------

	def test_unsupported_operator_raises(self) -> None:
		with self.assertRaises(ValueError) as ctx:
			evaluate_condition({"field": "X", "operator": "BOGUS"}, {"X": 1})
		self.assertIn("BOGUS", str(ctx.exception))

	def _fake_template_with_extra_rule(self, extra_rule: dict) -> dict:
		template = load_template(TEMPLATE_CODE)
		fake = {
			"doc": template["doc"],
			"template_code": template["template_code"],
			"package_hash": template["package_hash"],
			"package": copy.deepcopy(template["package"]),
		}
		fake["package"]["rules"]["rules"].append(extra_rule)
		return fake

	def test_unsupported_rule_type_raises(self) -> None:
		template = self._fake_template_with_extra_rule(
			{
				"rule_code": "RULE_BOGUS_TYPE",
				"rule_type": "BOGUS_RULE_TYPE",
				"enabled": True,
				"severity": "BLOCKER",
				"when": {"all": []},
				"then": {},
			}
		)
		with self.assertRaises(ValueError) as ctx:
			validate_config(template, {}, lots=[], boq_items=[])
		self.assertIn("BOGUS_RULE_TYPE", str(ctx.exception))

	def test_unknown_child_table_raises(self) -> None:
		template = self._fake_template_with_extra_rule(
			{
				"rule_code": "RULE_BOGUS_CHILD",
				"rule_type": "REQUIRE_CHILD_ROWS",
				"enabled": True,
				"severity": "BLOCKER",
				"when": {"all": []},
				"then": {
					"require_child_rows": [
						{"child_table": "Tender Bogus", "minimum_rows": 1}
					]
				},
			}
		)
		with self.assertRaises(ValueError) as ctx:
			validate_config(template, {}, lots=[], boq_items=[])
		self.assertIn("Tender Bogus", str(ctx.exception))
		self.assertIn(sorted(SUPPORTED_CHILD_TABLES)[0], str(ctx.exception))

	# ------------------------------------------------------------------
	# §10.13 — validation message rows shape
	# ------------------------------------------------------------------

	def test_build_validation_message_rows_shape(self) -> None:
		fake_result = {
			"messages": [
				{
					"severity": "BLOCKER",
					"rule_code": "R",
					"message": "msg",
					"affected_field": "F",
					"affected_section": "S",
					"affected_form": None,
					"blocks_generation": True,
					"resolution_hint": "fix",
					"details": {"k": 1},
				}
			]
		}
		rows = build_validation_message_rows(fake_result)
		self.assertEqual(len(rows), 1)
		row = rows[0]
		self.assertEqual(
			set(row.keys()),
			{
				"severity",
				"rule_code",
				"message",
				"affected_field",
				"affected_section",
				"affected_form",
				"blocks_generation",
				"resolution_hint",
				"details_json",
			},
		)
		self.assertEqual(row["severity"], "BLOCKER")
		self.assertEqual(row["blocks_generation"], 1)
		self.assertEqual(json.loads(row["details_json"]), {"k": 1})

	# ------------------------------------------------------------------
	# §16 — persistence helpers must not save / commit
	# ------------------------------------------------------------------

	def test_persistence_helpers_no_save(self) -> None:
		# Pre-test baseline — tolerates ambient site state from manual UI testing.
		baseline_count = frappe.db.count("Procurement Tender")
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		lots = load_sample_lots(template)
		boq_items = load_sample_boq_rows(template)
		result = validate_config(template, config, lots=lots, boq_items=boq_items)
		required_forms = resolve_required_forms(template, config, validation_result=result)

		tender_doc = frappe.new_doc("Procurement Tender")
		tender_doc.std_template = TEMPLATE_CODE

		populate_sample_tender(tender_doc)
		self.assertEqual(tender_doc.tender_title, "Construction of Ward Administration Block")
		self.assertEqual(tender_doc.tender_reference, "CGK/WKS/OT/001/2026")
		self.assertEqual(tender_doc.template_code, TEMPLATE_CODE)
		self.assertEqual(tender_doc.template_version, "0.1.0-poc")
		self.assertEqual(tender_doc.procurement_method, "OPEN_COMPETITIVE_TENDERING")
		self.assertEqual(tender_doc.tender_scope, "NATIONAL")
		self.assertEqual(len(tender_doc.lots), 2)
		self.assertEqual(len(tender_doc.boq_items), 9)
		self.assertTrue(tender_doc.configuration_json)
		# JSON parses back to the same configuration.
		round_trip = json.loads(tender_doc.configuration_json)
		self.assertEqual(round_trip["TENDER.TENDER_NAME"], config["TENDER.TENDER_NAME"])

		write_validation_to_tender(tender_doc, result)
		self.assertEqual(tender_doc.validation_status, "Passed")
		self.assertEqual(tender_doc.configuration_hash, result["configuration_hash"])
		self.assertIsNotNone(tender_doc.last_validated_at)
		# Primary sample yields no messages.
		self.assertEqual(len(tender_doc.validation_messages), 0)

		write_required_forms_to_tender(tender_doc, required_forms)
		self.assertEqual(len(tender_doc.required_forms), 15)
		self.assertEqual(
			[r.form_code for r in tender_doc.required_forms],
			PRIMARY_SAMPLE_ACTIVATED_FORMS,
		)

		# No record persisted: helpers do not save / commit (count diff = 0).
		self.assertEqual(frappe.db.count("Procurement Tender"), baseline_count)

	def test_apply_config_to_tender_doc_writes_summary_fields(self) -> None:
		# Pre-test baseline — tolerates ambient site state from manual UI testing.
		baseline_count = frappe.db.count("Procurement Tender")
		template = load_template(TEMPLATE_CODE)
		config = load_sample_config(template)
		tender_doc = frappe.new_doc("Procurement Tender")
		tender_doc.std_template = TEMPLATE_CODE
		apply_config_to_tender_doc(tender_doc, config)
		self.assertEqual(tender_doc.template_code, TEMPLATE_CODE)
		self.assertEqual(tender_doc.template_version, "0.1.0-poc")
		self.assertEqual(tender_doc.procurement_method, "OPEN_COMPETITIVE_TENDERING")
		self.assertEqual(tender_doc.tender_scope, "NATIONAL")
		self.assertEqual(tender_doc.procurement_category, "WORKS")
		self.assertTrue(tender_doc.configuration_json)
		# apply_config_to_tender_doc must not persist (count diff = 0).
		self.assertEqual(frappe.db.count("Procurement Tender"), baseline_count)

	# ------------------------------------------------------------------
	# Sanity check on supported vocabularies
	# ------------------------------------------------------------------

	def test_supported_vocabularies_match_rules_json(self) -> None:
		template = load_template(TEMPLATE_CODE)
		rules = template["package"]["rules"]
		operator_codes = {op["code"] for op in rules.get("operator_definitions") or []}
		rule_type_codes = {rt["code"] for rt in rules.get("rule_types") or []}
		self.assertEqual(operator_codes, set(SUPPORTED_OPERATORS))
		self.assertEqual(rule_type_codes, set(SUPPORTED_RULE_TYPES))
