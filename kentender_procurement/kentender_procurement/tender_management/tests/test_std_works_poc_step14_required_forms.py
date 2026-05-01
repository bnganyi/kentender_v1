# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 14 — required forms checklist generation (hardening).

Covers STEP14-AC-001..012 from the Step 14 specification, plus the §13.1–§13.7
manual-verification scenarios as automated regressions, the §14 ordering table
for the primary sample, the §11 server-method envelope, and the §16 unknown
form-code error path. Pattern follows STD-POC-010..014 — focused module, no
broader test infrastructure.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_step14_required_forms
"""

from __future__ import annotations

import copy
import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as controller,
)
from kentender_procurement.tender_management.services import std_template_engine as engine
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

# §13.1 expected required forms for the primary sample, in display_order.
PRIMARY_SAMPLE_ACTIVATED_FORMS: list[str] = [
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

# §13.1 expected excluded forms.
PRIMARY_SAMPLE_INACTIVE_FORMS: frozenset[str] = frozenset(
	{
		"FORM_TENDER_SECURING_DECLARATION",
		"FORM_FOREIGN_TENDERER_LOCAL_INPUT",
		"FORM_RETENTION_MONEY_SECURITY",
	}
)

# §8.1 default-required forms (from forms.json).
DEFAULT_REQUIRED_FORM_CODES: frozenset[str] = frozenset(
	{
		"FORM_OF_TENDER",
		"FORM_CONFIDENTIAL_BUSINESS_QUESTIONNAIRE",
		"FORM_CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION",
		"FORM_SELF_DECLARATION",
		"FORM_TECHNICAL_PROPOSAL",
		"FORM_SIMILAR_EXPERIENCE",
		"FORM_FINANCIAL_CAPACITY",
	}
)

# §14 expected (display_order, form_code) pairs for the primary sample.
PRIMARY_SAMPLE_DISPLAY_ORDER: list[tuple[int, str]] = [
	(10, "FORM_OF_TENDER"),
	(20, "FORM_CONFIDENTIAL_BUSINESS_QUESTIONNAIRE"),
	(30, "FORM_CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION"),
	(40, "FORM_SELF_DECLARATION"),
	(50, "FORM_TENDER_SECURITY"),
	(70, "FORM_JV_INFORMATION"),
	(90, "FORM_ALTERNATIVE_TECHNICAL_PROPOSAL"),
	(100, "FORM_TECHNICAL_PROPOSAL"),
	(110, "FORM_SIMILAR_EXPERIENCE"),
	(120, "FORM_FINANCIAL_CAPACITY"),
	(130, "FORM_PERSONNEL_SCHEDULE"),
	(140, "FORM_EQUIPMENT_SCHEDULE"),
	(150, "FORM_BENEFICIAL_OWNERSHIP_DISCLOSURE"),
	(160, "FORM_PERFORMANCE_SECURITY"),
	(170, "FORM_ADVANCE_PAYMENT_SECURITY"),
]

EXPECTED_ENVELOPE_KEYS: frozenset[str] = frozenset(
	{
		"ok",
		"message",
		"tender",
		"required_form_count",
		"validation_status",
		"blocks_generation",
		"configuration_hash",
	}
)


class TestStdWorksPocStep14RequiredForms(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

		self.tender = frappe.new_doc("Procurement Tender")
		self.tender.std_template = TEMPLATE_CODE
		self.tender.tender_title = "Step14 Smoke Tender"
		self.tender.tender_reference = "STEP14-SMOKE"
		self.tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		self.tender.tender_scope = "NATIONAL"
		self.tender.insert(ignore_permissions=True)

	def _reload_tender(self):
		return frappe.get_doc("Procurement Tender", self.tender.name)

	def _mutate_config(self, mutator) -> None:
		"""Load primary sample then mutate ``configuration_json`` in place."""
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		cfg = json.loads(tender.configuration_json)
		mutator(cfg)
		tender.configuration_json = json.dumps(cfg, indent=2, sort_keys=True)
		tender.save(ignore_permissions=True)

	# ------------------------------------------------------------------
	# STEP14-AC-001 + AC-002 + AC-009 — primary sample produces the 15
	# expected required forms and excludes the 3 inactive ones.
	# ------------------------------------------------------------------

	def test_step14_ac001_009_primary_sample_produces_expected_15_forms(self) -> None:
		controller.load_sample_tender(self.tender.name)
		result = controller.generate_required_forms(self.tender.name)

		self.assertTrue(result["ok"])
		self.assertEqual(result["required_form_count"], 15)

		tender = self._reload_tender()
		codes = [r.form_code for r in tender.required_forms]
		self.assertEqual(
			codes,
			PRIMARY_SAMPLE_ACTIVATED_FORMS,
			"STEP14-AC-001/002/009: primary sample must yield the §13.1 15 forms in display_order.",
		)
		excluded = set(codes) & PRIMARY_SAMPLE_INACTIVE_FORMS
		self.assertEqual(
			excluded,
			set(),
			f"STEP14-AC-009: primary sample must not include §13.1 excluded forms: {excluded}",
		)

	# ------------------------------------------------------------------
	# STEP14-AC-003 + §13.2 — Tender-Securing Declaration variant.
	# ------------------------------------------------------------------

	def test_step14_ac003_tender_securing_declaration_mutual_exclusion(self) -> None:
		controller.load_sample_variant(
			self.tender.name, "VARIANT-TENDER-SECURING-DECLARATION"
		)
		result = controller.generate_required_forms(self.tender.name)
		self.assertTrue(result["ok"])

		tender = self._reload_tender()
		codes = [r.form_code for r in tender.required_forms]
		self.assertIn("FORM_TENDER_SECURING_DECLARATION", codes)
		self.assertNotIn("FORM_TENDER_SECURITY", codes)

		# Primary sample remains the inverse — §8.3 mutual exclusion holds both ways.
		controller.load_sample_tender(self.tender.name)
		controller.generate_required_forms(self.tender.name)
		tender_primary = self._reload_tender()
		primary_codes = [r.form_code for r in tender_primary.required_forms]
		self.assertIn("FORM_TENDER_SECURITY", primary_codes)
		self.assertNotIn("FORM_TENDER_SECURING_DECLARATION", primary_codes)

	# ------------------------------------------------------------------
	# STEP14-AC-004 + AC-007 — deduplication + idempotency under repeated
	# generation.
	# ------------------------------------------------------------------

	def test_step14_ac004_007_no_duplicates_and_idempotent_under_3_runs(self) -> None:
		controller.load_sample_tender(self.tender.name)

		controller.generate_required_forms(self.tender.name)
		first = self._reload_tender()
		first_codes = [r.form_code for r in first.required_forms]
		first_sources = [r.activation_source for r in first.required_forms]
		first_orders = [r.display_order for r in first.required_forms]
		first_hash = first.configuration_hash

		# AC-004: codes are unique inside a single generation.
		self.assertEqual(
			len(first_codes),
			len(set(first_codes)),
			"STEP14-AC-004: required_forms must contain no duplicate form_code rows.",
		)

		for _ in range(2):
			controller.generate_required_forms(self.tender.name)

		final = self._reload_tender()
		final_codes = [r.form_code for r in final.required_forms]
		final_sources = [r.activation_source for r in final.required_forms]
		final_orders = [r.display_order for r in final.required_forms]

		self.assertEqual(final_codes, first_codes, "STEP14-AC-007: codes stable across 3 runs.")
		self.assertEqual(
			final_sources, first_sources, "STEP14-AC-007: activation_source stable across runs."
		)
		self.assertEqual(
			final_orders, first_orders, "STEP14-AC-007: display_order stable across runs."
		)
		self.assertEqual(
			final.configuration_hash,
			first_hash,
			"STEP14-AC-007: configuration_hash unchanged when configuration is unchanged.",
		)

	# ------------------------------------------------------------------
	# STEP14-AC-005 + §14 — sort tie-breaker on (display_order, form_code).
	# ------------------------------------------------------------------

	def test_step14_ac005_primary_sample_display_order_table(self) -> None:
		controller.load_sample_tender(self.tender.name)
		controller.generate_required_forms(self.tender.name)
		tender = self._reload_tender()
		ordered = [(r.display_order, r.form_code) for r in tender.required_forms]
		self.assertEqual(
			ordered,
			PRIMARY_SAMPLE_DISPLAY_ORDER,
			"STEP14-AC-005: primary sample must match the §14 ordering table.",
		)

	# ------------------------------------------------------------------
	# STEP14-AC-006 — every row carries activation_source and evidence_policy.
	# ------------------------------------------------------------------

	def test_step14_ac006_every_row_has_activation_source_and_evidence_policy(self) -> None:
		controller.load_sample_tender(self.tender.name)
		controller.generate_required_forms(self.tender.name)

		template = engine.load_template(TEMPLATE_CODE)
		forms_component = engine.get_package_component(template, "forms")
		evidence_by_code = {
			f["form_code"]: f.get("evidence_policy")
			for f in forms_component.get("forms") or []
		}

		tender = self._reload_tender()
		self.assertGreater(len(tender.required_forms), 0)
		for row in tender.required_forms:
			with self.subTest(form_code=row.form_code):
				self.assertTrue(
					row.activation_source,
					f"STEP14-AC-006: {row.form_code} must record an activation_source.",
				)
				self.assertEqual(
					row.evidence_policy,
					evidence_by_code[row.form_code],
					f"STEP14-AC-006: {row.form_code} evidence_policy must match forms.json.",
				)
				self.assertEqual(
					int(row.required), 1, "STEP14: required must persist as 1 (Check field)."
				)

	# ------------------------------------------------------------------
	# STEP14-AC-008 + §16 — unknown activated form code raises.
	# ------------------------------------------------------------------

	def test_step14_ac008_unknown_form_code_raises_value_error(self) -> None:
		controller.load_sample_tender(self.tender.name)
		template = engine.load_template(TEMPLATE_CODE)
		mutated_template = copy.deepcopy(template)

		# Inject an in-memory rule that activates a non-existent form code.
		# Spec §16: the engine must NOT silently ignore unknown forms.
		rules_component = mutated_template["package"]["rules"]
		rules_component.setdefault("rules", []).append(
			{
				"rule_code": "RULE_TEST_UNKNOWN_FORM",
				"rule_type": "ACTIVATE_FORM",
				"label": "Test rule for STEP14-AC-008",
				"description": "Step 14 unknown form-code regression.",
				"enabled": True,
				"severity": "INFO",
				"when": {"all": []},
				"then": {
					"require_fields": [],
					"require_child_rows": [],
					"activate_fields": [],
					"activate_sections": [],
					"activate_forms": ["FORM_DOES_NOT_EXIST"],
					"derive_fields": [],
					"validate": [],
				},
				"message": "Test rule activates an unknown form code.",
				"affected_sections": [],
				"affected_fields": [],
				"affected_forms": ["FORM_DOES_NOT_EXIST"],
				"notes": [],
			}
		)

		tender = self._reload_tender()
		config = json.loads(tender.configuration_json)
		validation_result = engine.validate_config(
			mutated_template,
			config,
			lots=[r.as_dict() for r in tender.lots],
			boq_items=[r.as_dict() for r in tender.boq_items],
		)

		self.assertIn(
			"FORM_DOES_NOT_EXIST",
			validation_result["active_forms"],
			"Sanity: validate_config must surface the synthetic activation.",
		)
		with self.assertRaises(ValueError) as ctx:
			engine.resolve_required_forms(
				mutated_template, config, validation_result=validation_result
			)
		self.assertIn(
			"FORM_DOES_NOT_EXIST",
			str(ctx.exception),
			"STEP14-AC-008: error must identify the unknown form code.",
		)

	# ------------------------------------------------------------------
	# STEP14-AC-010 + §13.3 — international variant.
	# ------------------------------------------------------------------

	def test_step14_ac010_international_variant_includes_foreign_form(self) -> None:
		controller.load_sample_variant(self.tender.name, "VARIANT-INTERNATIONAL")
		controller.generate_required_forms(self.tender.name)
		tender = self._reload_tender()
		ordered = [(r.display_order, r.form_code) for r in tender.required_forms]
		self.assertIn(
			(80, "FORM_FOREIGN_TENDERER_LOCAL_INPUT"),
			ordered,
			"§13.3: international variant must include FORM_FOREIGN_TENDERER_LOCAL_INPUT at display_order 80.",
		)
		# Primary forms remain.
		codes = [c for _, c in ordered]
		for default_code in DEFAULT_REQUIRED_FORM_CODES:
			self.assertIn(default_code, codes)

	# ------------------------------------------------------------------
	# STEP14-AC-010 + §13.4 — JV disabled excludes FORM_JV_INFORMATION.
	# ------------------------------------------------------------------

	def test_step14_ac010_jv_disabled_excludes_jv_form(self) -> None:
		def _disable_jv(cfg):
			cfg["PARTICIPATION.JV_ALLOWED"] = False
			cfg["PARTICIPATION.JV_MAX_MEMBERS"] = None

		self._mutate_config(_disable_jv)
		controller.generate_required_forms(self.tender.name)
		tender = self._reload_tender()
		codes = [r.form_code for r in tender.required_forms]
		self.assertNotIn("FORM_JV_INFORMATION", codes)
		# Default forms remain unaffected.
		for default_code in DEFAULT_REQUIRED_FORM_CODES:
			self.assertIn(default_code, codes)

	# ------------------------------------------------------------------
	# STEP14-AC-010 + §13.5 — alternatives disabled excludes alternative form.
	# ------------------------------------------------------------------

	def test_step14_ac010_alternatives_disabled_excludes_alternative_form(self) -> None:
		def _disable_alternatives(cfg):
			cfg["ALTERNATIVES.ALTERNATIVE_TENDERS_ALLOWED"] = False
			cfg["ALTERNATIVES.ALTERNATIVE_TENDER_TYPE"] = None
			cfg["ALTERNATIVES.ALTERNATIVE_SCOPE_DESCRIPTION"] = None

		self._mutate_config(_disable_alternatives)
		controller.generate_required_forms(self.tender.name)
		tender = self._reload_tender()
		codes = [r.form_code for r in tender.required_forms]
		self.assertNotIn("FORM_ALTERNATIVE_TECHNICAL_PROPOSAL", codes)

	# ------------------------------------------------------------------
	# STEP14-AC-010 + §13.6 — retention money security variant.
	# ------------------------------------------------------------------

	def test_step14_ac010_retention_money_security_variant(self) -> None:
		controller.load_sample_variant(
			self.tender.name, "VARIANT-RETENTION-MONEY-SECURITY"
		)
		controller.generate_required_forms(self.tender.name)
		tender = self._reload_tender()
		ordered = [(r.display_order, r.form_code) for r in tender.required_forms]
		self.assertIn(
			(180, "FORM_RETENTION_MONEY_SECURITY"),
			ordered,
			"§13.6: retention variant must include FORM_RETENTION_MONEY_SECURITY at display_order 180.",
		)
		# §13.6: contract security forms after bidder submission forms.
		retention_idx = next(
			i for i, (_, c) in enumerate(ordered) if c == "FORM_RETENTION_MONEY_SECURITY"
		)
		bidder_form_idx = next(
			i for i, (_, c) in enumerate(ordered) if c == "FORM_OF_TENDER"
		)
		self.assertGreater(retention_idx, bidder_form_idx)

	# ------------------------------------------------------------------
	# STEP14-AC-011 + §13.7 — missing site visit date still generates rows
	# but reports blockers.
	# ------------------------------------------------------------------

	def test_step14_ac011_missing_site_visit_blocked_but_rows_generated(self) -> None:
		controller.load_sample_variant(
			self.tender.name, "VARIANT-MISSING-SITE-VISIT-DATE"
		)
		result = controller.generate_required_forms(self.tender.name)

		self.assertTrue(result["blocks_generation"])
		self.assertEqual(result["validation_status"], "Blocked")
		self.assertGreater(result["required_form_count"], 0)

		tender = self._reload_tender()
		self.assertEqual(tender.tender_status, "Validation Failed")
		self.assertGreater(
			len(tender.required_forms),
			0,
			"§13.7: required_forms must still be persisted provisionally.",
		)
		# Validation messages mention the missing site visit field.
		blockers = [
			m
			for m in tender.validation_messages
			if (m.severity or "").upper() == "BLOCKER"
		]
		self.assertGreaterEqual(len(blockers), 1)

	# ------------------------------------------------------------------
	# §11 — server method envelope + persisted validation messages + hash.
	# ------------------------------------------------------------------

	def test_step14_server_method_returns_full_envelope(self) -> None:
		controller.load_sample_tender(self.tender.name)
		result = controller.generate_required_forms(self.tender.name)

		self.assertTrue(EXPECTED_ENVELOPE_KEYS.issubset(set(result.keys())))
		self.assertTrue(result["ok"])
		self.assertEqual(result["validation_status"], "Passed")
		self.assertFalse(result["blocks_generation"])
		self.assertEqual(result["required_form_count"], 15)
		self.assertEqual(result["tender"], self.tender.name)

		tender = self._reload_tender()
		# §11 step 12: configuration_hash persisted on the tender.
		self.assertEqual(tender.configuration_hash, result["configuration_hash"])
		self.assertEqual(tender.validation_status, "Passed")
		self.assertEqual(tender.tender_status, "Validated")
		# §11 step 9: validation_messages refreshed (Passed → 0 messages).
		self.assertEqual(len(tender.validation_messages), 0)

	# ------------------------------------------------------------------
	# §8.4 multi-source activation — DEFAULT + RULE join with ``"; "``.
	# ------------------------------------------------------------------

	def test_step14_multi_source_activation_default_plus_rule(self) -> None:
		controller.load_sample_tender(self.tender.name)
		controller.generate_required_forms(self.tender.name)
		tender = self._reload_tender()
		row = next(
			(r for r in tender.required_forms if r.form_code == "FORM_TECHNICAL_PROPOSAL"),
			None,
		)
		self.assertIsNotNone(row, "FORM_TECHNICAL_PROPOSAL must be in the primary checklist.")
		sources = (row.activation_source or "").split("; ")
		self.assertIn("DEFAULT", sources)
		self.assertIn("RULE:RULE_REQUIRE_WORKS_REQUIREMENTS", sources)
		# §8.4 acceptable format `DEFAULT; RULE_…` — semicolon-space delimiter.
		self.assertEqual(row.activation_source, "DEFAULT; RULE:RULE_REQUIRE_WORKS_REQUIREMENTS")
