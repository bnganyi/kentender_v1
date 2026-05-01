# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 2 + Step 3 + Step 4 + Step 5 + Step 6 + Step 7 + Step 8 — package + manifest + sections + fields + rules + forms + sample_tender structural test.

Locks acceptance criteria from:
- ``apps/kentender_v1/docs/prompts/std poc/2. std_works_poc_template_package_structure.md`` (STEP2-AC-001..007)
- ``apps/kentender_v1/docs/prompts/std poc/3. std_works_poc_manifest_specification.md`` (STEP3-AC-001..010 and §9 validation table)
- ``apps/kentender_v1/docs/prompts/std poc/4. std_works_poc_sections_specification.md`` (STEP4-AC-001..014 and §12 validation table)
- ``apps/kentender_v1/docs/prompts/std poc/5. std_works_poc_fields_specification.md`` (STEP5-AC-001..015 and §14 validation table)
- ``apps/kentender_v1/docs/prompts/std poc/6. std_works_poc_rules_specification.md`` (STEP6-AC-001..012 and §17 validation table)
- ``apps/kentender_v1/docs/prompts/std poc/7. std_works_poc_forms_specification.md`` (STEP7-AC-001..015 and §17 validation table)
- ``apps/kentender_v1/docs/prompts/std poc/8. std_works_poc_sample_tender_specification.md`` (STEP8-AC-001..014 and §14 validation table)

Run:
    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_package_skeleton
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from frappe.tests import IntegrationTestCase

PACKAGE_DIR = (
	Path(__file__).resolve().parent.parent
	/ "std_templates"
	/ "ke_ppra_works_building_2022_04_poc"
)

EXPECTED_TEMPLATE_CODE = "KE-PPRA-WORKS-BLDG-2022-04-POC"
EXPECTED_SAMPLE_CODE = "WORKS-WARD-ADMIN-BLOCK-POC"

REQUIRED_JSON_FILES = (
	"manifest.json",
	"sections.json",
	"fields.json",
	"rules.json",
	"forms.json",
	"render_map.json",
	"sample_tender.json",
)

REQUIRED_FILES = REQUIRED_JSON_FILES + ("README.md",)

OTHER_PACKAGE_SKELETONS = {
	"render_map.json": {"render_sections": []},
}

# Step 4 (sections.json) constants
SECTIONS_REQUIRED_TOP_LEVEL_KEYS = (
	"template_code",
	"section_model_version",
	"section_mutability_types",
	"sections",
)

MUTABILITY_TYPE_CODES = (
	"PARAMETERIZED_GENERATED",
	"LOCKED_REPRESENTATIVE_TEXT",
	"CONFIGURABLE_SCHEMA",
	"CONTROLLED_CONFIGURABLE_SCHEMA",
	"STRUCTURED_BIDDER_RESPONSE_SCHEMA",
	"NATIVE_SYSTEM_MODULE",
	"CONTROLLED_PE_AUTHORED_CONTENT",
	"CONTROLLED_ATTACHMENT_REFERENCE",
	"DOWNSTREAM_GENERATED_DOCUMENTS",
)

EXPECTED_SECTIONS_BY_RENDER_ORDER = (
	(10, "COVER"),
	(20, "INVITATION_TO_TENDER"),
	(30, "PART_1_HEADER"),
	(40, "ITT"),
	(50, "TDS"),
	(60, "EVALUATION_QUALIFICATION"),
	(70, "TENDERING_FORMS"),
	(80, "PART_2_HEADER"),
	(90, "BOQ"),
	(100, "SPECIFICATIONS"),
	(110, "DRAWINGS"),
	(120, "PART_3_HEADER"),
	(130, "GCC"),
	(140, "SCC"),
	(150, "CONTRACT_FORMS"),
	(160, "AUDIT_SUMMARY"),
)

SECTION_REQUIRED_KEYS = (
	"section_code",
	"source_section_code",
	"title",
	"part",
	"render_order",
	"mutability",
	"runtime_role",
	"included_in_poc_render",
	"ordinary_user_can_edit",
	"ordinary_user_input_allowed",
	"input_source",
	"output_behavior",
	"source_coverage",
	"poc_treatment",
	"depends_on_fields",
	"activates_forms",
	"notes",
)

LOCKED_SECTION_CODES = (
	"ITT",
	"GCC",
	"PART_1_HEADER",
	"PART_2_HEADER",
	"PART_3_HEADER",
)

MANIFEST_REQUIRED_TOP_LEVEL_KEYS = (
	"template_code",
	"template_name",
	"template_short_name",
	"description",
	"authority",
	"jurisdiction",
	"classification",
	"source_document",
	"versioning",
	"status",
	"applicability",
	"poc_scope",
	"package_files",
	"import_policy",
	"runtime_policy",
	"audit_policy",
	"ownership",
	"notes",
)

# Step 5 (fields.json) constants — spec §6 / §7 / §8 / §9 / §11 / §12 / §14
FIELDS_REQUIRED_TOP_LEVEL_KEYS = (
	"template_code",
	"field_model_version",
	"field_types",
	"field_groups",
	"fields",
)

EXPECTED_FIELD_TYPE_CODES = (
	"TEXT",
	"LONG_TEXT",
	"SELECT",
	"MULTI_SELECT",
	"BOOLEAN",
	"INTEGER",
	"DECIMAL",
	"MONEY",
	"PERCENT",
	"DATE",
	"DATETIME",
	"DURATION_DAYS",
	"DURATION_MONTHS",
	"EMAIL",
	"URL",
	"ORGANIZATION_REF",
	"USER_REF",
	"JSON_OBJECT",
)

EXPECTED_FIELD_GROUP_CODES = (
	"TENDER_IDENTITY",
	"METHOD_PARTICIPATION",
	"DATES_MEETINGS",
	"SECURITIES",
	"ALTERNATIVES_LOTS",
	"QUALIFICATION",
	"WORKS_REQUIREMENTS",
	"CONTRACT_SCC",
	"SYSTEM_AUDIT",
)

EXPECTED_FIELD_GROUP_DISTRIBUTION = {
	"TENDER_IDENTITY": 9,
	"METHOD_PARTICIPATION": 10,
	"DATES_MEETINGS": 11,
	"SECURITIES": 10,
	"ALTERNATIVES_LOTS": 6,
	"QUALIFICATION": 9,
	"WORKS_REQUIREMENTS": 7,
	"CONTRACT_SCC": 9,
	"SYSTEM_AUDIT": 4,
}

FIELD_REQUIRED_KEYS = (
	"field_code",
	"group_code",
	"label",
	"business_question",
	"field_type",
	"required_by_default",
	"default_value",
	"options",
	"section_targets",
	"render_targets",
	"help_text",
	"ordinary_user_editable",
	"poc_required",
	"notes",
)

SELECT_LIKE_FIELD_TYPES = {"SELECT", "MULTI_SELECT"}

EXPECTED_SYSTEM_AUDIT_FIELD_COUNT = 4

# Disallowed keys per spec §13/§14 — guards against rule logic / form schema leakage.
DISALLOWED_FIELD_KEYS_RULE_LOGIC = (
	"if",
	"condition",
	"when",
	"validate",
	"required_when",
	"activates_when",
	"requires_when",
)

DISALLOWED_FIELD_KEYS_FORM_SCHEMA = (
	"form_fields",
	"form_schema",
	"form_definition",
	"bidder_form",
)

FIELD_CODE_FORMAT_PATTERN = r"^[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*$"

# Step 6 (rules.json) constants — spec §6 / §7 / §8 / §9 / §10 / §11 / §15 / §16 / §17
RULES_REQUIRED_TOP_LEVEL_KEYS = (
	"template_code",
	"rule_model_version",
	"rule_types",
	"message_severities",
	"operator_definitions",
	"rules",
)

EXPECTED_RULE_TYPE_CODES = (
	"REQUIRE_FIELD",
	"REQUIRE_CHILD_ROWS",
	"ACTIVATE_FIELD",
	"ACTIVATE_SECTION",
	"ACTIVATE_FORM",
	"DERIVE_FIELD",
	"VALIDATE_DATE_ORDER",
	"VALIDATE_NUMERIC_LIMIT",
	"VALIDATE_ALLOWED_COMBINATION",
	"WARNING_ONLY",
	"INFO_ONLY",
)

EXPECTED_SEVERITY_CODES = ("INFO", "WARNING", "ERROR", "BLOCKER")
BLOCKING_SEVERITIES = {"ERROR", "BLOCKER"}

EXPECTED_OPERATOR_CODES = (
	"EQUALS",
	"NOT_EQUALS",
	"IS_TRUE",
	"IS_FALSE",
	"IS_EMPTY",
	"IS_NOT_EMPTY",
	"GREATER_THAN",
	"GREATER_THAN_OR_EQUALS",
	"LESS_THAN",
	"LESS_THAN_OR_EQUALS",
	"IN",
	"NOT_IN",
)

RULE_REQUIRED_KEYS = (
	"rule_code",
	"rule_type",
	"label",
	"description",
	"enabled",
	"severity",
	"when",
	"then",
	"message",
	"affected_sections",
	"affected_fields",
	"affected_forms",
	"notes",
)

THEN_REQUIRED_KEYS = (
	"require_fields",
	"require_child_rows",
	"activate_fields",
	"activate_sections",
	"activate_forms",
	"derive_fields",
	"validate",
)

EXPECTED_RULE_CODES = (
	"RULE_REQUIRED_CORE_TENDER_IDENTITY",
	"RULE_REQUIRE_METHOD_AND_SCOPE",
	"RULE_INTERNATIONAL_ACTIVATE_FOREIGN_TENDERER_LOCAL_INPUT",
	"RULE_REQUIRE_RESERVED_GROUP",
	"RULE_WARN_MARGIN_OF_PREFERENCE_ON_NATIONAL_TENDER",
	"RULE_REQUIRE_PREQUALIFICATION_REFERENCE",
	"RULE_JV_ACTIVATE_FORM_AND_REQUIRE_MAX_MEMBERS",
	"RULE_WARN_HIGH_JV_MEMBER_COUNT",
	"RULE_REQUIRE_ALTERNATIVE_TENDER_TYPE_AND_SCOPE",
	"RULE_MULTIPLE_LOTS_REQUIRE_LOT_ROWS_AND_METHODS",
	"RULE_SITE_VISIT_REQUIRE_DATE_AND_LOCATION",
	"RULE_PRE_TENDER_MEETING_REQUIRE_DATE_AND_LOCATION",
	"RULE_TENDER_SECURITY_REQUIRE_DETAILS",
	"RULE_TENDER_SECURING_DECLARATION_ACTIVATE_FORM",
	"RULE_TENDER_SECURITY_AMOUNT_LIMIT_2_PERCENT",
	"RULE_REQUIRE_CORE_DATES",
	"RULE_VALIDATE_CLARIFICATION_BEFORE_SUBMISSION",
	"RULE_VALIDATE_OPENING_NOT_BEFORE_SUBMISSION",
	"RULE_REQUIRE_QUALIFICATION_THRESHOLDS",
	"RULE_PERSONNEL_REQUIRED_ACTIVATE_FORM",
	"RULE_EQUIPMENT_REQUIRED_ACTIVATE_FORM",
	"RULE_BENEFICIAL_OWNERSHIP_ACTIVATE_FORM",
	"RULE_REQUIRE_WORKS_REQUIREMENTS",
	"RULE_BOQ_REQUIRE_ROWS",
	"RULE_DAYWORKS_REQUIRE_ROWS",
	"RULE_PROVISIONAL_SUMS_REQUIRE_ROWS",
	"RULE_REQUIRE_CONTRACT_SCC_PARAMETERS",
	"RULE_PERFORMANCE_SECURITY_ACTIVATE_FORM_AND_PERCENTAGE",
	"RULE_ADVANCE_PAYMENT_SECURITY_ACTIVATE_FORM",
	"RULE_RETENTION_MONEY_SECURITY_ACTIVATE_FORM",
	"RULE_REQUIRE_AUDIT_FIELDS",
)

EXPECTED_BLOCKER_CRITICAL_RULE_CODES = (
	"RULE_REQUIRED_CORE_TENDER_IDENTITY",
	"RULE_REQUIRE_METHOD_AND_SCOPE",
	"RULE_TENDER_SECURITY_REQUIRE_DETAILS",
	"RULE_TENDER_SECURITY_AMOUNT_LIMIT_2_PERCENT",
	"RULE_REQUIRE_CORE_DATES",
	"RULE_VALIDATE_CLARIFICATION_BEFORE_SUBMISSION",
	"RULE_VALIDATE_OPENING_NOT_BEFORE_SUBMISSION",
	"RULE_REQUIRE_QUALIFICATION_THRESHOLDS",
	"RULE_BOQ_REQUIRE_ROWS",
	"RULE_REQUIRE_CONTRACT_SCC_PARAMETERS",
	"RULE_REQUIRE_AUDIT_FIELDS",
)

EXPECTED_WARNING_RULE_CODES = frozenset({
	"RULE_WARN_MARGIN_OF_PREFERENCE_ON_NATIONAL_TENDER",
	"RULE_WARN_HIGH_JV_MEMBER_COUNT",
})

EXPECTED_BLOCKER_COUNT = 22
EXPECTED_INFO_COUNT = 7
EXPECTED_WARNING_COUNT = 2

FORWARD_REFERENCED_FORM_CODES = (
	"FORM_OF_TENDER",
	"FORM_CONFIDENTIAL_BUSINESS_QUESTIONNAIRE",
	"FORM_CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION",
	"FORM_SELF_DECLARATION",
	"FORM_TENDER_SECURITY",
	"FORM_TENDER_SECURING_DECLARATION",
	"FORM_JV_INFORMATION",
	"FORM_FOREIGN_TENDERER_LOCAL_INPUT",
	"FORM_ALTERNATIVE_TECHNICAL_PROPOSAL",
	"FORM_TECHNICAL_PROPOSAL",
	"FORM_SIMILAR_EXPERIENCE",
	"FORM_FINANCIAL_CAPACITY",
	"FORM_PERSONNEL_SCHEDULE",
	"FORM_EQUIPMENT_SCHEDULE",
	"FORM_BENEFICIAL_OWNERSHIP_DISCLOSURE",
	"FORM_PERFORMANCE_SECURITY",
	"FORM_ADVANCE_PAYMENT_SECURITY",
	"FORM_RETENTION_MONEY_SECURITY",
)

DISALLOWED_RULE_KEYS_EXEC = (
	"python",
	"exec",
	"eval",
	"code",
	"script",
	"function",
	"lambda",
	"compute",
)

RULE_CODE_FORMAT_PATTERN = r"^[A-Z][A-Z0-9_]*$"

# Step 5 invariants reused for §12 cross-step assertions.
EXPECTED_FIELDS_TOTAL = 75

# Step 7 (forms.json) constants — spec §6 / §7 / §8 / §9 / §10 / §11 / §12 / §13 / §14 / §15 / §17
FORMS_REQUIRED_TOP_LEVEL_KEYS = (
	"template_code",
	"form_model_version",
	"form_categories",
	"respondent_types",
	"workflow_stages",
	"evidence_policies",
	"forms",
)

EXPECTED_FORM_CATEGORY_CODES = (
	"CORE_BID_SUBMISSION",
	"ELIGIBILITY_DECLARATION",
	"SECURITY_INSTRUMENT",
	"PARTICIPATION_STRUCTURE",
	"QUALIFICATION_EVIDENCE",
	"TECHNICAL_PROPOSAL",
	"OWNERSHIP_DISCLOSURE",
	"CONTRACT_SECURITY",
	"DOWNSTREAM_CONTRACT_FORM",
)

EXPECTED_RESPONDENT_TYPE_CODES = (
	"BIDDER",
	"BIDDER_OR_JV",
	"JOINT_VENTURE",
	"FOREIGN_TENDERER",
	"SUCCESSFUL_BIDDER",
	"PROCURING_ENTITY",
	"SYSTEM_GENERATED",
)

EXPECTED_WORKFLOW_STAGE_CODES = (
	"BID_PREPARATION",
	"BID_SUBMISSION",
	"EVALUATION",
	"AWARD",
	"CONTRACT_SIGNATURE",
	"CONTRACT_EXECUTION",
	"POC_CHECKLIST_ONLY",
)

EXPECTED_EVIDENCE_POLICY_CODES = (
	"STRUCTURED_ONLY",
	"STRUCTURED_WITH_OPTIONAL_EVIDENCE",
	"STRUCTURED_WITH_REQUIRED_EVIDENCE_LATER",
	"ISSUER_VERIFICATION_FUTURE",
	"GENERATED_AFTER_AWARD",
	"POC_CHECKLIST_ONLY",
)

# §14 / §15 — the 18 form codes (must be identical to FORWARD_REFERENCED_FORM_CODES from Step 6 §16)
EXPECTED_FORM_CODES = FORWARD_REFERENCED_FORM_CODES

FORM_REQUIRED_KEYS = (
	"form_code",
	"title",
	"source_reference",
	"category",
	"respondent_type",
	"workflow_stage",
	"default_required",
	"activation_rule_codes",
	"section_targets",
	"evidence_policy",
	"poc_treatment",
	"ordinary_user_can_edit_schema",
	"bidder_upload_replacement_goal",
	"minimum_schema_fields",
	"checklist_display",
	"notes",
)

SCHEMA_FIELD_REQUIRED_KEYS = (
	"field_code",
	"label",
	"field_type",
	"required",
	"description",
)

CHECKLIST_DISPLAY_REQUIRED_KEYS = (
	"display_group",
	"display_order",
	"required_label",
	"not_required_label",
	"show_in_tender_pack_preview",
)

EXPECTED_DISPLAY_GROUPS = (
	"Core Bid Forms",
	"Declarations",
	"Security Forms",
	"Participation Forms",
	"Technical Forms",
	"Qualification Forms",
	"Ownership Forms",
	"Contract Security Forms",
)

# §14 — the 7 always-required forms (the other 11 are conditional on activation rules).
EXPECTED_DEFAULT_REQUIRED_FORMS = frozenset({
	"FORM_OF_TENDER",
	"FORM_CONFIDENTIAL_BUSINESS_QUESTIONNAIRE",
	"FORM_CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION",
	"FORM_SELF_DECLARATION",
	"FORM_TECHNICAL_PROPOSAL",
	"FORM_SIMILAR_EXPERIENCE",
	"FORM_FINANCIAL_CAPACITY",
})

DISALLOWED_FORM_KEYS_WORKFLOW = (
	"submit",
	"upload",
	"portal",
	"signature_payload",
	"encrypt",
	"submission_endpoint",
	"bidder_workflow",
)

FORM_CODE_FORMAT_PATTERN = r"^FORM_[A-Z][A-Z0-9_]*$"

# Step 8 (sample_tender.json) constants — spec §6 / §7 / §8 / §9 / §10 / §11 / §12 / §13 / §14 / §17 / §18
SAMPLE_REQUIRED_TOP_LEVEL_KEYS = (
	"sample_code",
	"sample_name",
	"template_code",
	"sample_status",
	"purpose",
	"tender",
	"configuration",
	"lots",
	"boq",
	"expected_activated_forms",
	"expected_validation_profile",
	"scenario_variants",
	"notes",
)

EXPECTED_SAMPLE_NAME = "Construction of Ward Administration Block"
EXPECTED_SAMPLE_STATUS = "DRAFT_SAMPLE"

EXPECTED_SAMPLE_TENDER_KEYS = (
	"title",
	"reference",
	"procuring_entity",
	"procurement_category",
	"procurement_method",
	"template_code",
)

EXPECTED_BOQ_CATEGORIES = frozenset({
	"PRELIMINARIES",
	"SUBSTRUCTURE",
	"SUPERSTRUCTURE",
	"ROOFING",
	"FINISHES",
	"EXTERNAL_WORKS",
	"DAYWORKS",
	"PROVISIONAL_SUMS",
	"GRAND_SUMMARY",
})

EXPECTED_LOT_COUNT_MIN = 2

EXPECTED_BOQ_ROW_REQUIRED_KEYS = (
	"item_code",
	"lot_code",
	"item_category",
	"description",
	"unit",
	"quantity",
	"rate",
	"amount",
	"is_priced_by_bidder",
)

EXPECTED_LOT_REQUIRED_KEYS = (
	"lot_code",
	"lot_title",
	"description",
	"estimated_value",
	"currency",
)

EXPECTED_ACTIVATED_FORM_CODES = (
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
)

EXPECTED_INACTIVE_FORM_CODES = (
	"FORM_TENDER_SECURING_DECLARATION",
	"FORM_FOREIGN_TENDERER_LOCAL_INPUT",
	"FORM_RETENTION_MONEY_SECURITY",
)

EXPECTED_SCENARIO_VARIANT_CODES = (
	"VARIANT-INTERNATIONAL",
	"VARIANT-TENDER-SECURING-DECLARATION",
	"VARIANT-RESERVED-TENDER",
	"VARIANT-MISSING-SITE-VISIT-DATE",
	"VARIANT-MISSING-ALTERNATIVE-SCOPE",
	"VARIANT-SINGLE-LOT",
	"VARIANT-RETENTION-MONEY-SECURITY",
)

EXPECTED_NEGATIVE_VARIANT_CODES = frozenset({
	"VARIANT-MISSING-SITE-VISIT-DATE",
	"VARIANT-MISSING-ALTERNATIVE-SCOPE",
})

VARIANT_REQUIRED_KEYS = (
	"variant_code",
	"description",
	"configuration_overrides",
	"lot_overrides",
	"boq_overrides",
	"expected_additional_forms",
	"expected_blockers",
)

VARIANT_OPTIONAL_KEYS = ("expected_inactive_forms",)

VALIDATION_PROFILE_REQUIRED_KEYS = (
	"expected_blockers",
	"expected_errors",
	"expected_warnings",
	"expected_inactive_forms",
	"notes",
)

EXPECTED_TENDER_SECURITY_LIMIT_PERCENT = 2.0


def _load_json(name: str) -> dict:
	return json.loads((PACKAGE_DIR / name).read_text(encoding="utf-8"))


class TestStdWorksPocPackageSkeleton(IntegrationTestCase):
	"""Step 2 acceptance: package folder + skeleton files."""

	def test_ac001_package_folder_exists(self) -> None:
		self.assertTrue(
			PACKAGE_DIR.is_dir(),
			f"STEP2-AC-001: expected package folder at {PACKAGE_DIR}",
		)

	def test_ac002_required_files_exist(self) -> None:
		missing = [name for name in REQUIRED_FILES if not (PACKAGE_DIR / name).is_file()]
		self.assertEqual(
			missing,
			[],
			f"STEP2-AC-002: missing required files in package: {missing}",
		)

	def test_ac003_json_files_parse(self) -> None:
		for name in REQUIRED_JSON_FILES:
			with self.subTest(file=name):
				try:
					_load_json(name)
				except json.JSONDecodeError as exc:
					self.fail(f"STEP2-AC-003: {name} is not valid JSON: {exc}")

	def test_ac004_manifest_template_code(self) -> None:
		manifest = _load_json("manifest.json")
		self.assertEqual(
			manifest.get("template_code"),
			EXPECTED_TEMPLATE_CODE,
			"STEP2-AC-004: manifest.json template_code must equal "
			f"{EXPECTED_TEMPLATE_CODE}",
		)

	def test_ac005_sample_template_code_matches_manifest(self) -> None:
		manifest = _load_json("manifest.json")
		sample = _load_json("sample_tender.json")
		self.assertEqual(
			sample.get("template_code"),
			manifest.get("template_code"),
			"STEP2-AC-005: sample_tender.json template_code must equal manifest template_code",
		)
		self.assertEqual(
			sample.get("sample_code"),
			EXPECTED_SAMPLE_CODE,
			f"STEP2-AC-005: sample_tender.json sample_code must equal {EXPECTED_SAMPLE_CODE}",
		)

	def test_ac006_readme_describes_poc_status(self) -> None:
		readme = (PACKAGE_DIR / "README.md").read_text(encoding="utf-8")
		self.assertIn("POC", readme, "STEP2-AC-006: README must mark this as a POC")
		self.assertIn(
			"not a full legal digitization",
			readme,
			"STEP2-AC-006: README must state the package is not a full legal digitization",
		)

	def test_ac007_readme_warns_against_officer_edits(self) -> None:
		readme = (PACKAGE_DIR / "README.md").read_text(encoding="utf-8")
		self.assertIn(
			"Ordinary procurement officers must not edit this package",
			readme,
			"STEP2-AC-007: README must warn that ordinary procurement officers must not edit the package",
		)

	def test_other_files_remain_skeleton(self) -> None:
		"""Negative guard — only manifest.json may be expanded after Step 3.

		sections / fields / rules / forms / render_map / sample_tender stay at
		their Step 2 skeletons until Steps 4–8 expand them.
		"""
		for name, expected in OTHER_PACKAGE_SKELETONS.items():
			with self.subTest(file=name):
				self.assertEqual(
					_load_json(name),
					expected,
					f"{name} must remain at its Step 2 skeleton until its own step expands it",
				)


class TestStdWorksPocManifestStep3(IntegrationTestCase):
	"""Step 3 acceptance: full manifest.json content per spec §6 / §8 / §9 / §13."""

	def setUp(self) -> None:
		self.manifest = _load_json("manifest.json")

	def test_step3_ac001_complete_required_keys(self) -> None:
		missing = [k for k in MANIFEST_REQUIRED_TOP_LEVEL_KEYS if k not in self.manifest]
		self.assertEqual(
			missing,
			[],
			f"STEP3-AC-001: manifest.json missing required top-level keys: {missing}",
		)
		extra = sorted(set(self.manifest.keys()) - set(MANIFEST_REQUIRED_TOP_LEVEL_KEYS))
		self.assertEqual(
			extra,
			[],
			f"STEP3-AC-001: manifest.json has unexpected top-level keys: {extra}",
		)

	def test_step3_ac002_valid_json(self) -> None:
		# _load_json already raises if invalid; this is a redundant safety net.
		try:
			json.loads((PACKAGE_DIR / "manifest.json").read_text(encoding="utf-8"))
		except json.JSONDecodeError as exc:
			self.fail(f"STEP3-AC-002: manifest.json is not valid JSON: {exc}")

	def test_step3_ac003_template_code_exact(self) -> None:
		self.assertEqual(
			self.manifest.get("template_code"),
			EXPECTED_TEMPLATE_CODE,
			f"STEP3-AC-003: template_code must be {EXPECTED_TEMPLATE_CODE}",
		)

	def test_step3_ac004_is_poc_version(self) -> None:
		versioning = self.manifest["versioning"]
		self.assertIs(versioning.get("is_poc_version"), True, "STEP3-AC-004")
		self.assertEqual(
			versioning.get("package_version"),
			"0.1.0-poc",
			"STEP3-AC-004: package_version must be 0.1.0-poc",
		)
		self.assertEqual(versioning.get("source_version_label"), "April 2022")
		self.assertEqual(versioning.get("package_version_date"), "2026-05-01")
		self.assertIsNone(versioning.get("supersedes_template_code"))
		self.assertIsNone(versioning.get("superseded_by_template_code"))

	def test_step3_ac005_not_full_legal_digitization(self) -> None:
		poc = self.manifest["poc_scope"]
		self.assertIs(poc.get("is_full_legal_digitization"), False, "STEP3-AC-005")
		for flag in (
			"includes_full_itt_text",
			"includes_full_gcc_text",
			"includes_full_bidder_submission_workflow",
			"includes_full_evaluation_workflow",
			"includes_pdf_generation",
		):
			with self.subTest(flag=flag):
				self.assertIs(poc.get(flag), False, f"STEP3-AC-005: {flag} must be False")
		self.assertIs(poc.get("uses_representative_locked_text"), True)
		self.assertIsInstance(poc.get("explicit_exclusions"), list)
		self.assertEqual(len(poc["explicit_exclusions"]), 8)

	def test_step3_ac006_source_doc1_april_2022(self) -> None:
		src = self.manifest["source_document"]
		self.assertEqual(src.get("source_document_code"), "DOC. 1", "STEP3-AC-006")
		self.assertEqual(src.get("revision_label"), "Rev April 2022")
		self.assertEqual(src.get("source_pages_known"), 159)
		self.assertIs(src.get("source_file_expected"), True)
		self.assertIsNone(src.get("source_file_hash"))
		self.assertEqual(src.get("source_file_hash_algorithm"), "SHA-256")
		self.assertEqual(src.get("source_title"), "Standard Tender Document for Procurement of Works")
		self.assertEqual(
			src.get("source_subtitle"),
			"Building and Associated Civil Engineering Works",
		)

	def test_step3_ac007_package_files_complete(self) -> None:
		entries = self.manifest["package_files"]
		self.assertEqual(len(entries), 8, "STEP3-AC-007: must list all 8 package files")
		names_by_hash = {e["file_name"]: e["included_in_package_hash"] for e in entries}
		self.assertEqual(
			set(names_by_hash.keys()),
			set(REQUIRED_FILES),
			"STEP3-AC-007: package_files names must match the required file set",
		)
		self.assertIs(
			names_by_hash["README.md"],
			False,
			"STEP3-AC-007: README.md must have included_in_package_hash = False",
		)
		for name in REQUIRED_JSON_FILES:
			with self.subTest(file=name):
				self.assertIs(
					names_by_hash[name],
					True,
					f"STEP3-AC-007: {name} must have included_in_package_hash = True",
				)
		for entry in entries:
			with self.subTest(file=entry["file_name"]):
				self.assertIs(entry.get("required"), True)
				self.assertIsInstance(entry.get("purpose"), str)
				self.assertTrue(entry["purpose"].strip())

	def test_step3_ac008_runtime_blocks_ordinary_user_edits(self) -> None:
		runtime = self.manifest["runtime_policy"]
		self.assertIs(runtime.get("ordinary_user_can_edit_template"), False, "STEP3-AC-008")
		self.assertIs(runtime.get("ordinary_user_can_edit_locked_text"), False, "STEP3-AC-008")
		self.assertIs(
			runtime.get("ordinary_user_can_create_tender_from_template_when_unapproved"),
			False,
		)
		self.assertIs(runtime.get("ordinary_user_configures_tender_only"), True)
		self.assertIs(runtime.get("generated_outputs_are_directly_editable"), False)
		self.assertIs(runtime.get("configuration_must_validate_before_render"), True)
		self.assertIs(runtime.get("block_render_on_blocker_messages"), True, "STEP3-AC-008")

	def test_step3_ac009_import_allowed_tender_creation_blocked(self) -> None:
		status = self.manifest["status"]
		self.assertEqual(status.get("package_status"), "DRAFT_PACKAGE", "STEP3-AC-009")
		self.assertIs(status.get("allowed_for_import"), True, "STEP3-AC-009")
		self.assertIs(status.get("allowed_for_tender_creation"), False, "STEP3-AC-009")
		self.assertIs(status.get("requires_review_before_tender_creation"), True)

	def test_step3_ac010_other_files_unchanged(self) -> None:
		"""STEP3-AC-010: no development outside manifest.json (other files at skeleton)."""
		for name, expected in OTHER_PACKAGE_SKELETONS.items():
			with self.subTest(file=name):
				self.assertEqual(_load_json(name), expected)

	def test_section9_validation_table_extras(self) -> None:
		"""Spec §9 — extra invariants not already covered by an STEP3-AC method."""
		classification = self.manifest["classification"]
		self.assertEqual(classification.get("procurement_category"), "WORKS")
		self.assertEqual(
			classification.get("template_family"),
			"BUILDING_AND_ASSOCIATED_CIVIL_ENGINEERING_WORKS",
		)
		self.assertEqual(classification.get("contract_nature"), "WORKS_CONSTRUCTION")
		self.assertEqual(classification.get("contract_pricing_type"), "ADMEASUREMENT_UNIT_RATE")
		self.assertEqual(classification.get("complexity_level"), "HIGH")

		applicability = self.manifest["applicability"]
		self.assertEqual(
			applicability.get("allowed_procurement_methods"),
			["OPEN_COMPETITIVE_TENDERING", "RESTRICTED_COMPETITIVE_TENDERING"],
		)
		self.assertEqual(
			applicability.get("allowed_tender_scopes"),
			["NATIONAL", "INTERNATIONAL"],
		)
		self.assertEqual(
			applicability.get("allowed_contract_structures"),
			["SINGLE_LOT", "MULTIPLE_LOTS"],
		)
		for flag in (
			"supports_prequalification",
			"supports_reservations",
			"supports_margin_of_preference",
			"supports_alternative_tenders",
			"supports_joint_ventures",
			"supports_boq",
			"supports_dayworks",
			"supports_provisional_sums",
		):
			with self.subTest(flag=flag):
				self.assertIs(applicability.get(flag), True)

		audit = self.manifest["audit_policy"]
		for flag in (
			"record_template_code",
			"record_package_version",
			"record_package_hash",
			"record_source_document_reference",
			"record_configuration_hash",
			"record_generation_timestamp",
			"record_validation_messages",
		):
			with self.subTest(flag=flag):
				self.assertIs(audit.get(flag), True)

		import_policy = self.manifest["import_policy"]
		self.assertEqual(import_policy.get("import_mode"), "UPSERT_BY_TEMPLATE_CODE")
		self.assertEqual(import_policy.get("hash_algorithm"), "SHA-256")
		for flag in (
			"store_package_json",
			"compute_package_hash",
			"validate_required_files",
			"validate_json_syntax",
			"fail_on_missing_required_file",
			"fail_on_template_code_mismatch",
			"create_template_record_if_missing",
			"update_template_record_if_exists",
		):
			with self.subTest(flag=flag):
				self.assertIs(import_policy.get(flag), True)

		authority = self.manifest["authority"]
		self.assertEqual(authority.get("name"), "Public Procurement Regulatory Authority")
		self.assertEqual(authority.get("abbreviation"), "PPRA")
		self.assertEqual(authority.get("country"), "Kenya")

		jurisdiction = self.manifest["jurisdiction"]
		self.assertEqual(jurisdiction.get("country_code"), "KE")
		self.assertEqual(jurisdiction.get("country_name"), "Kenya")
		self.assertIsInstance(jurisdiction.get("legal_framework"), list)
		self.assertEqual(len(jurisdiction["legal_framework"]), 3)

		ownership = self.manifest["ownership"]
		self.assertEqual(ownership.get("business_owner"), "Procurement Product Owner")
		self.assertEqual(ownership.get("technical_owner"), "Frappe Development Team")
		self.assertEqual(len(ownership.get("review_required_from", [])), 3)
		self.assertIs(ownership.get("ordinary_procurement_officer_owner"), False)

		notes = self.manifest["notes"]
		self.assertIsInstance(notes, list)
		self.assertEqual(len(notes), 4)
		for note in notes:
			with self.subTest(note=note):
				self.assertIsInstance(note, str)
				self.assertTrue(note.strip())

		self.assertEqual(
			self.manifest.get("template_name"),
			"PPRA Standard Tender Document for Procurement of Works "
			"\u2014 Building and Associated Civil Engineering Works",
		)
		self.assertEqual(
			self.manifest.get("template_short_name"),
			"PPRA Works STD \u2014 Building and Civil Works",
		)
		description = self.manifest.get("description")
		self.assertIsInstance(description, str)
		self.assertIn(
			"Proof-of-concept",
			description,
			"description must mark the package as a POC representation (spec §7.4)",
		)
		self.assertIn(
			"not a full legal digitization",
			description,
			"description must state it is not a full legal digitization (spec §7.4)",
		)


def _section_by_code(sections_doc: dict, code: str) -> dict | None:
	for section in sections_doc.get("sections", []):
		if section.get("section_code") == code:
			return section
	return None


class TestStdWorksPocSectionsStep4(IntegrationTestCase):
	"""Step 4 acceptance: full sections.json content per spec §6 / §7 / §8 / §11 / §12 / §16."""

	def setUp(self) -> None:
		self.sections_doc = _load_json("sections.json")
		self.sections = self.sections_doc.get("sections", [])

	def test_step4_ac001_complete_required_top_level_keys(self) -> None:
		missing = [k for k in SECTIONS_REQUIRED_TOP_LEVEL_KEYS if k not in self.sections_doc]
		self.assertEqual(
			missing,
			[],
			f"STEP4-AC-001: sections.json missing required top-level keys: {missing}",
		)
		extra = sorted(set(self.sections_doc.keys()) - set(SECTIONS_REQUIRED_TOP_LEVEL_KEYS))
		self.assertEqual(
			extra,
			[],
			f"STEP4-AC-001: sections.json has unexpected top-level keys: {extra}",
		)

	def test_step4_ac002_valid_json(self) -> None:
		try:
			json.loads((PACKAGE_DIR / "sections.json").read_text(encoding="utf-8"))
		except json.JSONDecodeError as exc:
			self.fail(f"STEP4-AC-002: sections.json is not valid JSON: {exc}")

	def test_step4_ac003_template_code_and_model_version(self) -> None:
		self.assertEqual(
			self.sections_doc.get("template_code"),
			EXPECTED_TEMPLATE_CODE,
			f"STEP4-AC-003: template_code must be {EXPECTED_TEMPLATE_CODE}",
		)
		self.assertEqual(
			self.sections_doc.get("section_model_version"),
			"0.1.0-poc",
			"STEP4-AC-003: section_model_version must be 0.1.0-poc",
		)

	def test_step4_ac004_mutability_types_complete(self) -> None:
		types = self.sections_doc.get("section_mutability_types", [])
		self.assertEqual(
			len(types),
			len(MUTABILITY_TYPE_CODES),
			f"STEP4-AC-004: expected {len(MUTABILITY_TYPE_CODES)} mutability types",
		)
		actual_codes = [t.get("code") for t in types]
		self.assertEqual(
			set(actual_codes),
			set(MUTABILITY_TYPE_CODES),
			"STEP4-AC-004: mutability type codes must match the required set",
		)
		for t in types:
			with self.subTest(code=t.get("code")):
				self.assertIn("code", t)
				self.assertIsInstance(t.get("label"), str)
				self.assertTrue(t["label"].strip())
				self.assertIsInstance(t.get("description"), str)
				self.assertTrue(t["description"].strip())
		used_mutabilities = {s.get("mutability") for s in self.sections}
		unknown = used_mutabilities - set(MUTABILITY_TYPE_CODES)
		self.assertEqual(
			unknown,
			set(),
			f"STEP4-AC-004: sections reference undefined mutability types: {unknown}",
		)

	def test_step4_ac005_required_sections_present(self) -> None:
		self.assertEqual(
			len(self.sections),
			len(EXPECTED_SECTIONS_BY_RENDER_ORDER),
			"STEP4-AC-005: expected exactly 16 sections",
		)
		expected_codes = {code for _, code in EXPECTED_SECTIONS_BY_RENDER_ORDER}
		actual_codes = {s.get("section_code") for s in self.sections}
		self.assertEqual(
			actual_codes,
			expected_codes,
			"STEP4-AC-005: section_code set must match the spec §9 list",
		)

	def test_step4_ac006_unique_section_codes(self) -> None:
		codes = [s.get("section_code") for s in self.sections]
		self.assertEqual(
			len(codes),
			len(set(codes)),
			f"STEP4-AC-006: duplicate section_code values: {codes}",
		)

	def test_step4_ac007_unique_render_orders(self) -> None:
		orders = [s.get("render_order") for s in self.sections]
		self.assertEqual(
			len(orders),
			len(set(orders)),
			f"STEP4-AC-007: duplicate render_order values: {orders}",
		)
		self.assertEqual(
			orders,
			sorted(orders),
			"STEP4-AC-007: render_order values must increase monotonically in array order",
		)
		self.assertEqual(
			tuple((s["render_order"], s["section_code"]) for s in self.sections),
			EXPECTED_SECTIONS_BY_RENDER_ORDER,
			"STEP4-AC-007: (render_order, section_code) sequence must match spec §9",
		)

	def test_step4_ac008_itt_and_gcc_locked(self) -> None:
		for code in ("ITT", "GCC"):
			with self.subTest(section=code):
				section = _section_by_code(self.sections_doc, code)
				self.assertIsNotNone(section, f"STEP4-AC-008: {code} must exist")
				self.assertEqual(section.get("mutability"), "LOCKED_REPRESENTATIVE_TEXT")
				self.assertIs(section.get("ordinary_user_can_edit"), False)
				self.assertIs(section.get("ordinary_user_input_allowed"), False)

	def test_step4_ac009_tds_and_scc_configurable_schema(self) -> None:
		for code in ("TDS", "SCC"):
			with self.subTest(section=code):
				section = _section_by_code(self.sections_doc, code)
				self.assertIsNotNone(section, f"STEP4-AC-009: {code} must exist")
				self.assertEqual(section.get("mutability"), "CONFIGURABLE_SCHEMA")
				self.assertIs(section.get("ordinary_user_can_edit"), False)
				self.assertIs(section.get("ordinary_user_input_allowed"), True)

	def test_step4_ac010_boq_native_module(self) -> None:
		section = _section_by_code(self.sections_doc, "BOQ")
		self.assertIsNotNone(section, "STEP4-AC-010: BOQ must exist")
		self.assertEqual(section.get("mutability"), "NATIVE_SYSTEM_MODULE")

	def test_step4_ac011_tendering_forms_structured_bidder_schema(self) -> None:
		section = _section_by_code(self.sections_doc, "TENDERING_FORMS")
		self.assertIsNotNone(section, "STEP4-AC-011: TENDERING_FORMS must exist")
		self.assertEqual(section.get("mutability"), "STRUCTURED_BIDDER_RESPONSE_SCHEMA")
		self.assertIs(section.get("ordinary_user_can_edit"), False)
		self.assertIs(section.get("ordinary_user_input_allowed"), False)

	def test_step4_ac012_contract_forms_downstream_generated(self) -> None:
		section = _section_by_code(self.sections_doc, "CONTRACT_FORMS")
		self.assertIsNotNone(section, "STEP4-AC-012: CONTRACT_FORMS must exist")
		self.assertEqual(section.get("mutability"), "DOWNSTREAM_GENERATED_DOCUMENTS")

	def test_step4_ac013_audit_summary_generated_section(self) -> None:
		section = _section_by_code(self.sections_doc, "AUDIT_SUMMARY")
		self.assertIsNotNone(section, "STEP4-AC-013: AUDIT_SUMMARY must exist")
		self.assertEqual(section.get("mutability"), "PARAMETERIZED_GENERATED")
		self.assertIs(section.get("included_in_poc_render"), True)
		self.assertIs(section.get("ordinary_user_can_edit"), False)
		self.assertIs(section.get("ordinary_user_input_allowed"), False)
		self.assertIsNone(section.get("source_section_code"))

	def test_step4_ac014_no_other_implementation(self) -> None:
		"""STEP4-AC-014: no development outside sections.json (other files at expected state)."""
		for name, expected in OTHER_PACKAGE_SKELETONS.items():
			with self.subTest(file=name):
				self.assertEqual(_load_json(name), expected)
		manifest = _load_json("manifest.json")
		self.assertEqual(
			set(manifest.keys()),
			set(MANIFEST_REQUIRED_TOP_LEVEL_KEYS),
			"STEP4-AC-014: manifest must remain at Step 3 top-level shape",
		)
		self.assertEqual(manifest.get("template_code"), EXPECTED_TEMPLATE_CODE)

	def test_section_object_required_fields(self) -> None:
		"""Spec §8.1 — every section object must contain all required keys with correct types."""
		for section in self.sections:
			code = section.get("section_code")
			with self.subTest(section=code):
				missing = [k for k in SECTION_REQUIRED_KEYS if k not in section]
				self.assertEqual(
					missing,
					[],
					f"section {code} missing required keys: {missing}",
				)
				self.assertIsInstance(section["section_code"], str)
				self.assertIsInstance(section["title"], str)
				self.assertIsInstance(section["part"], str)
				self.assertIsInstance(section["render_order"], int)
				self.assertIsInstance(section["mutability"], str)
				self.assertIsInstance(section["runtime_role"], str)
				self.assertIsInstance(section["included_in_poc_render"], bool)
				self.assertIsInstance(section["ordinary_user_can_edit"], bool)
				self.assertIsInstance(section["ordinary_user_input_allowed"], bool)
				self.assertIsInstance(section["input_source"], str)
				self.assertIsInstance(section["output_behavior"], str)
				self.assertIsInstance(section["source_coverage"], str)
				self.assertIsInstance(section["poc_treatment"], str)
				self.assertIsInstance(section["depends_on_fields"], list)
				self.assertIsInstance(section["activates_forms"], list)
				self.assertIsInstance(section["notes"], list)
				ssc = section["source_section_code"]
				self.assertTrue(
					ssc is None or isinstance(ssc, str),
					f"source_section_code must be string or null, got {type(ssc).__name__}",
				)

	def test_locked_sections_explicit_set(self) -> None:
		"""Spec §10.1 — ITT, GCC, and the three PART_*_HEADER sections are LOCKED."""
		for code in LOCKED_SECTION_CODES:
			with self.subTest(section=code):
				section = _section_by_code(self.sections_doc, code)
				self.assertIsNotNone(section)
				self.assertEqual(section.get("mutability"), "LOCKED_REPRESENTATIVE_TEXT")
				self.assertIs(section.get("ordinary_user_can_edit"), False)
				self.assertIs(section.get("ordinary_user_input_allowed"), False)

	def test_section12_no_field_or_rule_leakage(self) -> None:
		"""Spec §12 — sections.json must not define field metadata or rule logic."""
		allowed = set(SECTION_REQUIRED_KEYS)
		for section in self.sections:
			code = section.get("section_code")
			with self.subTest(section=code):
				extra = sorted(set(section.keys()) - allowed)
				self.assertEqual(
					extra,
					[],
					f"section {code} contains unexpected keys (possible field/rule leakage): {extra}",
				)


class TestStdWorksPocFieldsStep5(IntegrationTestCase):
	"""Step 5 acceptance: full fields.json content per spec §6 / §7 / §8 / §9 / §11 / §12 / §14."""

	def setUp(self) -> None:
		self.fields_doc = _load_json("fields.json")
		self.field_types = self.fields_doc.get("field_types", [])
		self.field_groups = self.fields_doc.get("field_groups", [])
		self.fields = self.fields_doc.get("fields", [])

	def test_step5_ac001_complete_required_top_level_keys(self) -> None:
		missing = [k for k in FIELDS_REQUIRED_TOP_LEVEL_KEYS if k not in self.fields_doc]
		self.assertEqual(
			missing,
			[],
			f"STEP5-AC-001: fields.json missing required top-level keys: {missing}",
		)
		extra = sorted(set(self.fields_doc.keys()) - set(FIELDS_REQUIRED_TOP_LEVEL_KEYS))
		self.assertEqual(
			extra,
			[],
			f"STEP5-AC-001: fields.json has unexpected top-level keys: {extra}",
		)

	def test_step5_ac002_valid_json(self) -> None:
		try:
			json.loads((PACKAGE_DIR / "fields.json").read_text(encoding="utf-8"))
		except json.JSONDecodeError as exc:
			self.fail(f"STEP5-AC-002: fields.json is not valid JSON: {exc}")

	def test_step5_ac003_template_code_and_model_version(self) -> None:
		self.assertEqual(
			self.fields_doc.get("template_code"),
			EXPECTED_TEMPLATE_CODE,
			f"STEP5-AC-003: template_code must be {EXPECTED_TEMPLATE_CODE}",
		)
		self.assertEqual(
			self.fields_doc.get("field_model_version"),
			"0.1.0-poc",
			"STEP5-AC-003: field_model_version must be 0.1.0-poc",
		)

	def test_step5_ac004_all_field_types_defined(self) -> None:
		self.assertEqual(
			len(self.field_types),
			len(EXPECTED_FIELD_TYPE_CODES),
			f"STEP5-AC-004: expected {len(EXPECTED_FIELD_TYPE_CODES)} field types",
		)
		actual_codes = [t.get("code") for t in self.field_types]
		self.assertEqual(
			set(actual_codes),
			set(EXPECTED_FIELD_TYPE_CODES),
			"STEP5-AC-004: field_type codes must match the spec §7 set",
		)
		for ft in self.field_types:
			with self.subTest(code=ft.get("code")):
				self.assertIsInstance(ft.get("code"), str)
				self.assertTrue(ft["code"].strip())
				self.assertIsInstance(ft.get("label"), str)
				self.assertTrue(ft["label"].strip())
				self.assertIsInstance(ft.get("description"), str)
				self.assertTrue(ft["description"].strip())

	def test_step5_ac005_all_field_groups_defined(self) -> None:
		self.assertEqual(
			len(self.field_groups),
			len(EXPECTED_FIELD_GROUP_CODES),
			f"STEP5-AC-005: expected {len(EXPECTED_FIELD_GROUP_CODES)} field groups",
		)
		actual_codes = [g.get("group_code") for g in self.field_groups]
		self.assertEqual(
			set(actual_codes),
			set(EXPECTED_FIELD_GROUP_CODES),
			"STEP5-AC-005: field_group codes must match the spec §8 set",
		)
		for g in self.field_groups:
			with self.subTest(group=g.get("group_code")):
				self.assertIsInstance(g.get("group_code"), str)
				self.assertIsInstance(g.get("label"), str)
				self.assertTrue(g["label"].strip())
				self.assertIsInstance(g.get("render_order"), int)
				self.assertIsInstance(g.get("description"), str)
				self.assertTrue(g["description"].strip())
		render_orders = [g["render_order"] for g in self.field_groups]
		self.assertEqual(
			len(render_orders),
			len(set(render_orders)),
			f"STEP5-AC-005: render_order values must be unique: {render_orders}",
		)
		self.assertEqual(
			render_orders,
			sorted(render_orders),
			"STEP5-AC-005: render_order values must increase monotonically in array order",
		)

	def test_step5_ac006_field_distribution_matches_spec(self) -> None:
		expected_total = sum(EXPECTED_FIELD_GROUP_DISTRIBUTION.values())
		self.assertEqual(
			len(self.fields),
			expected_total,
			f"STEP5-AC-006: expected {expected_total} fields total (spec §11 / §13)",
		)
		actual = Counter(f.get("group_code") for f in self.fields)
		for group_code, expected_count in EXPECTED_FIELD_GROUP_DISTRIBUTION.items():
			with self.subTest(group=group_code):
				self.assertEqual(
					actual.get(group_code, 0),
					expected_count,
					f"STEP5-AC-006: group {group_code} expected {expected_count} fields, "
					f"got {actual.get(group_code, 0)}",
				)

	def test_step5_ac007_unique_field_codes(self) -> None:
		codes = [f.get("field_code") for f in self.fields]
		duplicates = [c for c, n in Counter(codes).items() if n > 1]
		self.assertEqual(
			duplicates,
			[],
			f"STEP5-AC-007: duplicate field_code values: {duplicates}",
		)

	def test_step5_ac008_valid_group_references(self) -> None:
		defined = {g.get("group_code") for g in self.field_groups}
		for f in self.fields:
			code = f.get("field_code")
			with self.subTest(field=code):
				self.assertIn(
					f.get("group_code"),
					defined,
					f"STEP5-AC-008: field {code} references undefined group_code "
					f"{f.get('group_code')!r}",
				)

	def test_step5_ac009_valid_field_type_references(self) -> None:
		defined = {t.get("code") for t in self.field_types}
		for f in self.fields:
			code = f.get("field_code")
			with self.subTest(field=code):
				self.assertIn(
					f.get("field_type"),
					defined,
					f"STEP5-AC-009: field {code} references undefined field_type "
					f"{f.get('field_type')!r}",
				)

	def test_step5_ac010_select_fields_have_options(self) -> None:
		for f in self.fields:
			code = f.get("field_code")
			with self.subTest(field=code):
				self.assertIsInstance(
					f.get("options"),
					list,
					f"STEP5-AC-010: options for {code} must be a list",
				)
				if f.get("field_type") in SELECT_LIKE_FIELD_TYPES:
					self.assertGreater(
						len(f["options"]),
						0,
						f"STEP5-AC-010: select-like field {code} must have non-empty options",
					)

	def test_step5_ac011_system_audit_fields_not_user_editable(self) -> None:
		system_fields = [f for f in self.fields if f.get("group_code") == "SYSTEM_AUDIT"]
		self.assertEqual(
			len(system_fields),
			EXPECTED_SYSTEM_AUDIT_FIELD_COUNT,
			f"STEP5-AC-011: SYSTEM_AUDIT group must have "
			f"{EXPECTED_SYSTEM_AUDIT_FIELD_COUNT} fields",
		)
		for f in system_fields:
			code = f.get("field_code")
			with self.subTest(field=code):
				self.assertTrue(
					code.startswith("SYSTEM."),
					f"STEP5-AC-011: SYSTEM_AUDIT field {code} must use SYSTEM.* prefix",
				)
				self.assertIs(
					f.get("ordinary_user_editable"),
					False,
					f"STEP5-AC-011: SYSTEM_AUDIT field {code} must not be ordinary-user editable",
				)
		# §12 — SECURITY.TENDER_SECURING_DECLARATION_REQUIRED is derived and not user-editable.
		derived = next(
			(f for f in self.fields if f.get("field_code") == "SECURITY.TENDER_SECURING_DECLARATION_REQUIRED"),
			None,
		)
		self.assertIsNotNone(
			derived,
			"STEP5-AC-011: SECURITY.TENDER_SECURING_DECLARATION_REQUIRED must be defined (spec §12)",
		)
		self.assertIs(
			derived.get("ordinary_user_editable"),
			False,
			"STEP5-AC-011: SECURITY.TENDER_SECURING_DECLARATION_REQUIRED must not be "
			"ordinary-user editable (derived per spec §12)",
		)

	def test_step5_ac012_section_targets_valid(self) -> None:
		"""Cross-file (spec §5 / §14): every section_targets entry must exist in sections.json."""
		sections_doc = _load_json("sections.json")
		section_codes = {s.get("section_code") for s in sections_doc.get("sections", [])}
		self.assertEqual(
			len(section_codes),
			len(EXPECTED_SECTIONS_BY_RENDER_ORDER),
			"STEP5-AC-012: sections.json must still expose 16 section codes",
		)
		for f in self.fields:
			code = f.get("field_code")
			with self.subTest(field=code):
				targets = f.get("section_targets")
				self.assertIsInstance(targets, list, f"section_targets for {code} must be a list")
				unknown = [t for t in targets if t not in section_codes]
				self.assertEqual(
					unknown,
					[],
					f"STEP5-AC-012: field {code} references unknown section_targets: {unknown}",
				)

	def test_step5_ac013_no_rule_logic_keys(self) -> None:
		"""STEP5-AC-013: fields.json must not contain conditional validation logic keys."""
		disallowed = set(DISALLOWED_FIELD_KEYS_RULE_LOGIC)
		for f in self.fields:
			code = f.get("field_code")
			with self.subTest(field=code):
				leaked = sorted(set(f.keys()) & disallowed)
				self.assertEqual(
					leaked,
					[],
					f"STEP5-AC-013: field {code} contains disallowed rule-logic keys: {leaked}",
				)

	def test_step5_ac014_no_form_schema_keys(self) -> None:
		"""STEP5-AC-014: fields.json must not embed bidder form schemas."""
		disallowed = set(DISALLOWED_FIELD_KEYS_FORM_SCHEMA)
		for f in self.fields:
			code = f.get("field_code")
			with self.subTest(field=code):
				leaked = sorted(set(f.keys()) & disallowed)
				self.assertEqual(
					leaked,
					[],
					f"STEP5-AC-014: field {code} contains disallowed form-schema keys: {leaked}",
				)

	def test_step5_ac015_no_other_implementation(self) -> None:
		"""STEP5-AC-015: no development outside fields.json (other files at expected state)."""
		for name, expected in OTHER_PACKAGE_SKELETONS.items():
			with self.subTest(file=name):
				self.assertEqual(_load_json(name), expected)
		manifest = _load_json("manifest.json")
		self.assertEqual(
			set(manifest.keys()),
			set(MANIFEST_REQUIRED_TOP_LEVEL_KEYS),
			"STEP5-AC-015: manifest must remain at Step 3 top-level shape",
		)
		self.assertEqual(manifest.get("template_code"), EXPECTED_TEMPLATE_CODE)
		sections_doc = _load_json("sections.json")
		self.assertEqual(
			set(sections_doc.keys()),
			set(SECTIONS_REQUIRED_TOP_LEVEL_KEYS),
			"STEP5-AC-015: sections must remain at Step 4 top-level shape",
		)
		self.assertEqual(
			len(sections_doc.get("sections", [])),
			len(EXPECTED_SECTIONS_BY_RENDER_ORDER),
			"STEP5-AC-015: sections.json must still expose 16 sections",
		)
		self.assertEqual(
			len(sections_doc.get("section_mutability_types", [])),
			len(MUTABILITY_TYPE_CODES),
			"STEP5-AC-015: sections.json must still expose 9 mutability types",
		)

	def test_field_object_required_attributes(self) -> None:
		"""Spec §9.1 — every field object must contain all 14 required attributes with correct types."""
		allowed = set(FIELD_REQUIRED_KEYS)
		for f in self.fields:
			code = f.get("field_code")
			with self.subTest(field=code):
				missing = [k for k in FIELD_REQUIRED_KEYS if k not in f]
				self.assertEqual(missing, [], f"field {code} missing required keys: {missing}")
				extra = sorted(set(f.keys()) - allowed)
				self.assertEqual(
					extra,
					[],
					f"field {code} contains unexpected keys (possible logic/form leakage): {extra}",
				)
				for str_key in (
					"field_code",
					"group_code",
					"label",
					"business_question",
					"field_type",
					"help_text",
				):
					self.assertIsInstance(
						f.get(str_key),
						str,
						f"field {code}: {str_key} must be a string",
					)
					self.assertTrue(
						f[str_key].strip(),
						f"field {code}: {str_key} must be non-empty",
					)
				for bool_key in (
					"required_by_default",
					"ordinary_user_editable",
					"poc_required",
				):
					self.assertIsInstance(
						f.get(bool_key),
						bool,
						f"field {code}: {bool_key} must be bool",
					)
				for list_key in (
					"options",
					"section_targets",
					"render_targets",
					"notes",
				):
					self.assertIsInstance(
						f.get(list_key),
						list,
						f"field {code}: {list_key} must be a list",
					)

	def test_field_code_format(self) -> None:
		"""Spec §10 — every field_code must match DOMAIN.FIELD_NAME upper-snake format."""
		pattern = re.compile(FIELD_CODE_FORMAT_PATTERN)
		for f in self.fields:
			code = f.get("field_code")
			with self.subTest(field=code):
				self.assertIsInstance(code, str)
				self.assertRegex(
					code,
					pattern,
					f"field_code {code!r} must match DOMAIN.FIELD_NAME upper-snake format (spec §10)",
				)

	def test_section_dependencies_satisfied(self) -> None:
		"""Cross-file (spec §5 / §14) — every sections.json depends_on_fields code exists here."""
		sections_doc = _load_json("sections.json")
		field_codes = {f.get("field_code") for f in self.fields}
		all_deps: set[str] = set()
		for section in sections_doc.get("sections", []):
			for dep in section.get("depends_on_fields", []) or []:
				all_deps.add(dep)
		missing = sorted(all_deps - field_codes)
		self.assertEqual(
			missing,
			[],
			"STEP5 cross-file consistency: sections.json depends_on_fields references "
			f"undefined field codes: {missing}",
		)


def _collect_field_refs_in_rule(rule: dict) -> set[str]:
	"""Walk a single rule and return every field code referenced anywhere."""
	refs: set[str] = set()
	for cond in (rule.get("when") or {}).get("all", []) or []:
		if isinstance(cond, dict) and isinstance(cond.get("field"), str):
			refs.add(cond["field"])
	then = rule.get("then") or {}
	for key in ("require_fields", "activate_fields"):
		for code in then.get(key, []) or []:
			if isinstance(code, str):
				refs.add(code)
	for code in rule.get("affected_fields", []) or []:
		if isinstance(code, str):
			refs.add(code)
	for d in then.get("derive_fields", []) or []:
		if isinstance(d, dict) and isinstance(d.get("field"), str):
			refs.add(d["field"])
	for v in then.get("validate", []) or []:
		if isinstance(v, dict):
			for k in (
				"field",
				"base_field",
				"earlier_field",
				"later_field",
				"first_field",
				"second_field",
			):
				val = v.get(k)
				if isinstance(val, str):
					refs.add(val)
	return refs


def _collect_section_refs_in_rule(rule: dict) -> set[str]:
	refs: set[str] = set()
	for code in (rule.get("then") or {}).get("activate_sections", []) or []:
		if isinstance(code, str):
			refs.add(code)
	for code in rule.get("affected_sections", []) or []:
		if isinstance(code, str):
			refs.add(code)
	return refs


def _collect_form_refs_in_rule(rule: dict) -> set[str]:
	refs: set[str] = set()
	for code in (rule.get("then") or {}).get("activate_forms", []) or []:
		if isinstance(code, str):
			refs.add(code)
	for code in rule.get("affected_forms", []) or []:
		if isinstance(code, str):
			refs.add(code)
	return refs


def _walk_disallowed_keys(node, disallowed: set[str], path: list[str], hits: list[str]) -> None:
	if isinstance(node, dict):
		for k, v in node.items():
			if k in disallowed:
				hits.append("/".join(path + [k]))
			_walk_disallowed_keys(v, disallowed, path + [str(k)], hits)
	elif isinstance(node, list):
		for i, item in enumerate(node):
			_walk_disallowed_keys(item, disallowed, path + [str(i)], hits)


class TestStdWorksPocRulesStep6(IntegrationTestCase):
	"""Step 6 acceptance: full rules.json content per spec §6 / §7 / §8 / §9 / §10 / §11 / §15 / §16 / §17."""

	def setUp(self) -> None:
		self.rules_doc = _load_json("rules.json")
		self.rule_types = self.rules_doc.get("rule_types", [])
		self.severities = self.rules_doc.get("message_severities", [])
		self.operators = self.rules_doc.get("operator_definitions", [])
		self.rules = self.rules_doc.get("rules", [])

	def test_step6_ac001_complete_required_top_level_keys(self) -> None:
		missing = [k for k in RULES_REQUIRED_TOP_LEVEL_KEYS if k not in self.rules_doc]
		self.assertEqual(
			missing,
			[],
			f"STEP6-AC-001: rules.json missing required top-level keys: {missing}",
		)
		extra = sorted(set(self.rules_doc.keys()) - set(RULES_REQUIRED_TOP_LEVEL_KEYS))
		self.assertEqual(
			extra,
			[],
			f"STEP6-AC-001: rules.json has unexpected top-level keys: {extra}",
		)

	def test_step6_ac002_valid_json(self) -> None:
		try:
			json.loads((PACKAGE_DIR / "rules.json").read_text(encoding="utf-8"))
		except json.JSONDecodeError as exc:
			self.fail(f"STEP6-AC-002: rules.json is not valid JSON: {exc}")

	def test_step6_ac003_template_code_and_model_version(self) -> None:
		self.assertEqual(
			self.rules_doc.get("template_code"),
			EXPECTED_TEMPLATE_CODE,
			f"STEP6-AC-003: template_code must be {EXPECTED_TEMPLATE_CODE}",
		)
		self.assertEqual(
			self.rules_doc.get("rule_model_version"),
			"0.1.0-poc",
			"STEP6-AC-003: rule_model_version must be 0.1.0-poc",
		)

	def test_step6_ac004_all_rule_types_defined(self) -> None:
		self.assertEqual(
			len(self.rule_types),
			len(EXPECTED_RULE_TYPE_CODES),
			f"STEP6-AC-004: expected {len(EXPECTED_RULE_TYPE_CODES)} rule types",
		)
		actual_codes = [t.get("code") for t in self.rule_types]
		self.assertEqual(
			set(actual_codes),
			set(EXPECTED_RULE_TYPE_CODES),
			"STEP6-AC-004: rule_type codes must match the spec §7 set",
		)
		for rt in self.rule_types:
			with self.subTest(code=rt.get("code")):
				self.assertIsInstance(rt.get("code"), str)
				self.assertTrue(rt["code"].strip())
				self.assertIsInstance(rt.get("label"), str)
				self.assertTrue(rt["label"].strip())
				self.assertIsInstance(rt.get("description"), str)
				self.assertTrue(rt["description"].strip())

	def test_step6_ac005_all_severities_defined(self) -> None:
		self.assertEqual(
			len(self.severities),
			len(EXPECTED_SEVERITY_CODES),
			f"STEP6-AC-005: expected {len(EXPECTED_SEVERITY_CODES)} severities",
		)
		by_code = {s.get("code"): s for s in self.severities}
		self.assertEqual(
			set(by_code.keys()),
			set(EXPECTED_SEVERITY_CODES),
			"STEP6-AC-005: severity codes must match INFO/WARNING/ERROR/BLOCKER",
		)
		for s in self.severities:
			with self.subTest(code=s.get("code")):
				self.assertIsInstance(s.get("code"), str)
				self.assertIsInstance(s.get("label"), str)
				self.assertTrue(s["label"].strip())
				self.assertIsInstance(s.get("blocks_generation"), bool)
		self.assertIs(by_code["ERROR"]["blocks_generation"], True, "ERROR must block generation")
		self.assertIs(by_code["BLOCKER"]["blocks_generation"], True, "BLOCKER must block generation")
		self.assertIs(by_code["INFO"]["blocks_generation"], False, "INFO must not block generation")
		self.assertIs(
			by_code["WARNING"]["blocks_generation"],
			False,
			"WARNING must not block generation",
		)

	def test_step6_ac006_all_operators_defined(self) -> None:
		self.assertEqual(
			len(self.operators),
			len(EXPECTED_OPERATOR_CODES),
			f"STEP6-AC-006: expected {len(EXPECTED_OPERATOR_CODES)} operators",
		)
		actual_codes = [o.get("code") for o in self.operators]
		self.assertEqual(
			set(actual_codes),
			set(EXPECTED_OPERATOR_CODES),
			"STEP6-AC-006: operator codes must match the spec §9 set",
		)
		for op in self.operators:
			with self.subTest(code=op.get("code")):
				self.assertIsInstance(op.get("code"), str)
				self.assertIsInstance(op.get("description"), str)
				self.assertTrue(op["description"].strip())

	def test_step6_ac007_required_scenario_rules_present(self) -> None:
		actual_codes = {r.get("rule_code") for r in self.rules}
		self.assertEqual(
			actual_codes,
			set(EXPECTED_RULE_CODES),
			"STEP6-AC-007: rule_code set must match the spec §15 list exactly",
		)
		self.assertEqual(
			len(self.rules),
			len(EXPECTED_RULE_CODES),
			f"STEP6-AC-007: expected {len(EXPECTED_RULE_CODES)} rules total",
		)

	def test_step6_ac008_blocker_severity_for_critical(self) -> None:
		by_code = {r.get("rule_code"): r for r in self.rules}
		for rule_code in EXPECTED_BLOCKER_CRITICAL_RULE_CODES:
			with self.subTest(rule=rule_code):
				rule = by_code.get(rule_code)
				self.assertIsNotNone(rule, f"STEP6-AC-008: rule {rule_code} must exist")
				self.assertEqual(
					rule.get("severity"),
					"BLOCKER",
					f"STEP6-AC-008: critical rule {rule_code} must use BLOCKER severity",
				)
		blocker_count = sum(1 for r in self.rules if r.get("severity") == "BLOCKER")
		self.assertEqual(
			blocker_count,
			EXPECTED_BLOCKER_COUNT,
			f"STEP6-AC-008: expected {EXPECTED_BLOCKER_COUNT} BLOCKER rules total, got {blocker_count}",
		)

	def test_step6_ac009_warning_severity_for_review(self) -> None:
		by_code = {r.get("rule_code"): r for r in self.rules}
		for rule_code in EXPECTED_WARNING_RULE_CODES:
			with self.subTest(rule=rule_code):
				rule = by_code.get(rule_code)
				self.assertIsNotNone(rule, f"STEP6-AC-009: rule {rule_code} must exist")
				self.assertEqual(
					rule.get("severity"),
					"WARNING",
					f"STEP6-AC-009: review-only rule {rule_code} must use WARNING severity",
				)
		warning_count = sum(1 for r in self.rules if r.get("severity") == "WARNING")
		self.assertEqual(
			warning_count,
			EXPECTED_WARNING_COUNT,
			f"STEP6-AC-009: expected {EXPECTED_WARNING_COUNT} WARNING rules total, got {warning_count}",
		)
		info_count = sum(1 for r in self.rules if r.get("severity") == "INFO")
		self.assertEqual(
			info_count,
			EXPECTED_INFO_COUNT,
			f"STEP6-AC-009: expected {EXPECTED_INFO_COUNT} INFO rules total, got {info_count}",
		)

	def test_step6_ac010_form_codes_for_step7_reconciliation(self) -> None:
		self.assertEqual(
			len(FORWARD_REFERENCED_FORM_CODES),
			18,
			"STEP6-AC-010: §16 forward-reference list must have 18 form codes",
		)
		self.assertEqual(
			len(set(FORWARD_REFERENCED_FORM_CODES)),
			len(FORWARD_REFERENCED_FORM_CODES),
			"STEP6-AC-010: §16 forward-reference list must have unique codes",
		)
		used: set[str] = set()
		for rule in self.rules:
			used |= _collect_form_refs_in_rule(rule)
		unknown = sorted(used - set(FORWARD_REFERENCED_FORM_CODES))
		self.assertEqual(
			unknown,
			[],
			f"STEP6-AC-010: rules reference form codes outside §16 list: {unknown}",
		)

	def test_step6_ac011_no_executable_logic_keys(self) -> None:
		disallowed = set(DISALLOWED_RULE_KEYS_EXEC)
		hits: list[str] = []
		_walk_disallowed_keys(self.rules, disallowed, [], hits)
		self.assertEqual(
			hits,
			[],
			f"STEP6-AC-011: rules.json contains disallowed executable-logic keys at: {hits}",
		)

	def test_step6_ac012_no_other_implementation(self) -> None:
		"""STEP6-AC-012: no development outside rules.json (other files at expected state)."""
		for name, expected in OTHER_PACKAGE_SKELETONS.items():
			with self.subTest(file=name):
				self.assertEqual(_load_json(name), expected)
		manifest = _load_json("manifest.json")
		self.assertEqual(
			set(manifest.keys()),
			set(MANIFEST_REQUIRED_TOP_LEVEL_KEYS),
			"STEP6-AC-012: manifest must remain at Step 3 top-level shape",
		)
		self.assertEqual(manifest.get("template_code"), EXPECTED_TEMPLATE_CODE)
		sections_doc = _load_json("sections.json")
		self.assertEqual(
			set(sections_doc.keys()),
			set(SECTIONS_REQUIRED_TOP_LEVEL_KEYS),
			"STEP6-AC-012: sections must remain at Step 4 top-level shape",
		)
		self.assertEqual(
			len(sections_doc.get("sections", [])),
			len(EXPECTED_SECTIONS_BY_RENDER_ORDER),
			"STEP6-AC-012: sections.json must still expose 16 sections",
		)
		self.assertEqual(
			len(sections_doc.get("section_mutability_types", [])),
			len(MUTABILITY_TYPE_CODES),
			"STEP6-AC-012: sections.json must still expose 9 mutability types",
		)
		fields_doc = _load_json("fields.json")
		self.assertEqual(
			set(fields_doc.keys()),
			set(FIELDS_REQUIRED_TOP_LEVEL_KEYS),
			"STEP6-AC-012: fields must remain at Step 5 top-level shape",
		)
		self.assertEqual(
			len(fields_doc.get("fields", [])),
			EXPECTED_FIELDS_TOTAL,
			f"STEP6-AC-012: fields.json must still expose {EXPECTED_FIELDS_TOTAL} fields",
		)
		self.assertEqual(
			len(fields_doc.get("field_groups", [])),
			len(EXPECTED_FIELD_GROUP_CODES),
			"STEP6-AC-012: fields.json must still expose 9 field groups",
		)
		self.assertEqual(
			len(fields_doc.get("field_types", [])),
			len(EXPECTED_FIELD_TYPE_CODES),
			"STEP6-AC-012: fields.json must still expose 18 field types",
		)

	def test_rule_object_required_attributes(self) -> None:
		"""Spec §10.1 — every rule object must contain the 14 required attributes with correct types."""
		allowed = set(RULE_REQUIRED_KEYS)
		then_required = set(THEN_REQUIRED_KEYS)
		for rule in self.rules:
			code = rule.get("rule_code")
			with self.subTest(rule=code):
				missing = [k for k in RULE_REQUIRED_KEYS if k not in rule]
				self.assertEqual(missing, [], f"rule {code} missing required keys: {missing}")
				extra = sorted(set(rule.keys()) - allowed)
				self.assertEqual(
					extra,
					[],
					f"rule {code} contains unexpected top-level keys: {extra}",
				)
				for str_key in (
					"rule_code",
					"rule_type",
					"label",
					"description",
					"severity",
					"message",
				):
					self.assertIsInstance(
						rule.get(str_key),
						str,
						f"rule {code}: {str_key} must be a string",
					)
					self.assertTrue(
						rule[str_key].strip(),
						f"rule {code}: {str_key} must be non-empty",
					)
				self.assertIsInstance(rule.get("enabled"), bool, f"rule {code}: enabled must be bool")
				self.assertIsInstance(rule.get("when"), dict, f"rule {code}: when must be dict")
				self.assertIsInstance(rule.get("then"), dict, f"rule {code}: then must be dict")
				for list_key in ("affected_sections", "affected_fields", "affected_forms", "notes"):
					self.assertIsInstance(
						rule.get(list_key),
						list,
						f"rule {code}: {list_key} must be a list",
					)
				self.assertIn(
					"all",
					rule["when"],
					f"rule {code}: when must contain 'all' key (spec §11)",
				)
				self.assertIsInstance(
					rule["when"]["all"],
					list,
					f"rule {code}: when.all must be a list",
				)
				then = rule["then"]
				missing_then = [k for k in THEN_REQUIRED_KEYS if k not in then]
				self.assertEqual(
					missing_then,
					[],
					f"rule {code}: then missing required keys: {missing_then}",
				)
				extra_then = sorted(set(then.keys()) - then_required)
				self.assertEqual(
					extra_then,
					[],
					f"rule {code}: then contains unexpected keys: {extra_then}",
				)

	def test_rule_code_format_and_uniqueness(self) -> None:
		"""Spec §10 — rule_codes must be uppercase snake-case and unique across the file."""
		pattern = re.compile(RULE_CODE_FORMAT_PATTERN)
		codes = [r.get("rule_code") for r in self.rules]
		duplicates = sorted({c for c in codes if codes.count(c) > 1})
		self.assertEqual(duplicates, [], f"duplicate rule_code values: {duplicates}")
		for code in codes:
			with self.subTest(rule=code):
				self.assertIsInstance(code, str)
				self.assertRegex(
					code,
					pattern,
					f"rule_code {code!r} must match uppercase snake-case (spec §10)",
				)

	def test_valid_rule_type_and_severity_references(self) -> None:
		"""Spec §17 — every rule references a valid rule_type and severity."""
		valid_types = set(EXPECTED_RULE_TYPE_CODES)
		valid_sevs = set(EXPECTED_SEVERITY_CODES)
		for rule in self.rules:
			code = rule.get("rule_code")
			with self.subTest(rule=code):
				self.assertIn(
					rule.get("rule_type"),
					valid_types,
					f"rule {code} has unknown rule_type {rule.get('rule_type')!r}",
				)
				self.assertIn(
					rule.get("severity"),
					valid_sevs,
					f"rule {code} has unknown severity {rule.get('severity')!r}",
				)

	def test_when_all_condition_shape(self) -> None:
		"""Spec §11 — every when.all condition has field/operator (+ optional value)."""
		field_pattern = re.compile(FIELD_CODE_FORMAT_PATTERN)
		valid_ops = set(EXPECTED_OPERATOR_CODES)
		for rule in self.rules:
			code = rule.get("rule_code")
			conds = (rule.get("when") or {}).get("all", [])
			with self.subTest(rule=code):
				self.assertIsInstance(conds, list)
				for i, cond in enumerate(conds):
					with self.subTest(condition_index=i):
						self.assertIsInstance(
							cond,
							dict,
							f"rule {code} condition[{i}] must be an object",
						)
						field = cond.get("field")
						self.assertIsInstance(
							field,
							str,
							f"rule {code} condition[{i}] field must be a string",
						)
						self.assertRegex(
							field,
							field_pattern,
							f"rule {code} condition[{i}] field {field!r} must match "
							"DOMAIN.FIELD_NAME format",
						)
						op = cond.get("operator")
						self.assertIn(
							op,
							valid_ops,
							f"rule {code} condition[{i}] uses unknown operator {op!r}",
						)

	def test_valid_field_references_in_rules(self) -> None:
		"""Spec §17 + §5 — every field reference must exist in fields.json (75 codes)."""
		fields_doc = _load_json("fields.json")
		field_codes = {f.get("field_code") for f in fields_doc.get("fields", [])}
		self.assertEqual(
			len(field_codes),
			EXPECTED_FIELDS_TOTAL,
			f"cross-file: fields.json must still expose {EXPECTED_FIELDS_TOTAL} field codes",
		)
		for rule in self.rules:
			code = rule.get("rule_code")
			refs = _collect_field_refs_in_rule(rule)
			with self.subTest(rule=code):
				unknown = sorted(refs - field_codes)
				self.assertEqual(
					unknown,
					[],
					f"rule {code} references unknown field codes: {unknown}",
				)

	def test_valid_section_references_in_rules(self) -> None:
		"""Spec §17 + §5 — every section reference must exist in sections.json (16 codes)."""
		sections_doc = _load_json("sections.json")
		section_codes = {s.get("section_code") for s in sections_doc.get("sections", [])}
		self.assertEqual(
			len(section_codes),
			len(EXPECTED_SECTIONS_BY_RENDER_ORDER),
			"cross-file: sections.json must still expose 16 section codes",
		)
		for rule in self.rules:
			code = rule.get("rule_code")
			refs = _collect_section_refs_in_rule(rule)
			with self.subTest(rule=code):
				unknown = sorted(refs - section_codes)
				self.assertEqual(
					unknown,
					[],
					f"rule {code} references unknown section codes: {unknown}",
				)

	def test_require_child_rows_shape(self) -> None:
		"""Spec §14 — every require_child_rows entry has child_table / minimum_rows / condition_label."""
		valid_ops = set(EXPECTED_OPERATOR_CODES)
		for rule in self.rules:
			code = rule.get("rule_code")
			rows = (rule.get("then") or {}).get("require_child_rows", [])
			if not rows:
				continue
			with self.subTest(rule=code):
				self.assertIsInstance(rows, list)
				for i, row in enumerate(rows):
					with self.subTest(child_row_index=i):
						self.assertIsInstance(row, dict)
						self.assertIsInstance(row.get("child_table"), str)
						self.assertTrue(
							row["child_table"].strip(),
							f"rule {code} child_rows[{i}].child_table must be non-empty",
						)
						self.assertIsInstance(row.get("minimum_rows"), int)
						self.assertGreater(
							row["minimum_rows"],
							0,
							f"rule {code} child_rows[{i}].minimum_rows must be positive",
						)
						self.assertIsInstance(row.get("condition_label"), str)
						self.assertTrue(
							row["condition_label"].strip(),
							f"rule {code} child_rows[{i}].condition_label must be non-empty",
						)
						if "row_filter" in row:
							rf = row["row_filter"]
							self.assertIsInstance(rf, dict)
							self.assertIsInstance(rf.get("field"), str)
							self.assertTrue(rf["field"].strip())
							self.assertIn(
								rf.get("operator"),
								valid_ops,
								f"rule {code} child_rows[{i}].row_filter.operator "
								f"{rf.get('operator')!r} must be a defined operator",
							)
							self.assertIn("value", rf, "row_filter must include 'value'")


class TestStdWorksPocFormsStep7(IntegrationTestCase):
	"""Step 7 acceptance: full forms.json content per spec §6 / §7 / §8 / §9 / §10 / §11 / §12 / §13 / §14 / §15 / §17."""

	def setUp(self) -> None:
		self.forms_doc = _load_json("forms.json")
		self.categories = self.forms_doc.get("form_categories", [])
		self.respondent_types = self.forms_doc.get("respondent_types", [])
		self.workflow_stages = self.forms_doc.get("workflow_stages", [])
		self.evidence_policies = self.forms_doc.get("evidence_policies", [])
		self.forms = self.forms_doc.get("forms", [])

	def test_step7_ac001_complete_required_top_level_keys(self) -> None:
		missing = [k for k in FORMS_REQUIRED_TOP_LEVEL_KEYS if k not in self.forms_doc]
		self.assertEqual(
			missing,
			[],
			f"STEP7-AC-001: forms.json missing required top-level keys: {missing}",
		)
		extra = sorted(set(self.forms_doc.keys()) - set(FORMS_REQUIRED_TOP_LEVEL_KEYS))
		self.assertEqual(
			extra,
			[],
			f"STEP7-AC-001: forms.json has unexpected top-level keys: {extra}",
		)

	def test_step7_ac002_valid_json(self) -> None:
		try:
			json.loads((PACKAGE_DIR / "forms.json").read_text(encoding="utf-8"))
		except json.JSONDecodeError as exc:
			self.fail(f"STEP7-AC-002: forms.json is not valid JSON: {exc}")

	def test_step7_ac003_template_code_and_model_version(self) -> None:
		self.assertEqual(
			self.forms_doc.get("template_code"),
			EXPECTED_TEMPLATE_CODE,
			f"STEP7-AC-003: template_code must be {EXPECTED_TEMPLATE_CODE}",
		)
		self.assertEqual(
			self.forms_doc.get("form_model_version"),
			"0.1.0-poc",
			"STEP7-AC-003: form_model_version must be 0.1.0-poc",
		)

	def test_step7_ac004_all_form_categories_defined(self) -> None:
		self.assertEqual(
			len(self.categories),
			len(EXPECTED_FORM_CATEGORY_CODES),
			f"STEP7-AC-004: expected {len(EXPECTED_FORM_CATEGORY_CODES)} form categories",
		)
		actual_codes = [c.get("code") for c in self.categories]
		self.assertEqual(
			set(actual_codes),
			set(EXPECTED_FORM_CATEGORY_CODES),
			"STEP7-AC-004: form_category codes must match the spec §7 set",
		)
		for cat in self.categories:
			with self.subTest(code=cat.get("code")):
				for key in ("code", "label", "description"):
					self.assertIsInstance(cat.get(key), str, f"category.{key} must be string")
					self.assertTrue(cat[key].strip(), f"category.{key} must be non-empty")

	def test_step7_ac005_all_respondent_types_defined(self) -> None:
		self.assertEqual(
			len(self.respondent_types),
			len(EXPECTED_RESPONDENT_TYPE_CODES),
			f"STEP7-AC-005: expected {len(EXPECTED_RESPONDENT_TYPE_CODES)} respondent types",
		)
		actual_codes = [r.get("code") for r in self.respondent_types]
		self.assertEqual(
			set(actual_codes),
			set(EXPECTED_RESPONDENT_TYPE_CODES),
			"STEP7-AC-005: respondent_type codes must match the spec §8 set",
		)
		for rt in self.respondent_types:
			with self.subTest(code=rt.get("code")):
				for key in ("code", "label", "description"):
					self.assertIsInstance(rt.get(key), str, f"respondent_type.{key} must be string")
					self.assertTrue(rt[key].strip(), f"respondent_type.{key} must be non-empty")

	def test_step7_ac006_all_workflow_stages_defined(self) -> None:
		self.assertEqual(
			len(self.workflow_stages),
			len(EXPECTED_WORKFLOW_STAGE_CODES),
			f"STEP7-AC-006: expected {len(EXPECTED_WORKFLOW_STAGE_CODES)} workflow stages",
		)
		actual_codes = [w.get("code") for w in self.workflow_stages]
		self.assertEqual(
			set(actual_codes),
			set(EXPECTED_WORKFLOW_STAGE_CODES),
			"STEP7-AC-006: workflow_stage codes must match the spec §9 set",
		)
		for ws in self.workflow_stages:
			with self.subTest(code=ws.get("code")):
				for key in ("code", "label", "description"):
					self.assertIsInstance(ws.get(key), str, f"workflow_stage.{key} must be string")
					self.assertTrue(ws[key].strip(), f"workflow_stage.{key} must be non-empty")

	def test_step7_ac007_all_evidence_policies_defined(self) -> None:
		self.assertEqual(
			len(self.evidence_policies),
			len(EXPECTED_EVIDENCE_POLICY_CODES),
			f"STEP7-AC-007: expected {len(EXPECTED_EVIDENCE_POLICY_CODES)} evidence policies",
		)
		actual_codes = [e.get("code") for e in self.evidence_policies]
		self.assertEqual(
			set(actual_codes),
			set(EXPECTED_EVIDENCE_POLICY_CODES),
			"STEP7-AC-007: evidence_policy codes must match the spec §10 set",
		)
		for ep in self.evidence_policies:
			with self.subTest(code=ep.get("code")):
				for key in ("code", "label", "description"):
					self.assertIsInstance(ep.get(key), str, f"evidence_policy.{key} must be string")
					self.assertTrue(ep[key].strip(), f"evidence_policy.{key} must be non-empty")

	def test_step7_ac008_step6_form_references_reconciled(self) -> None:
		"""STEP7-AC-008: every form referenced by Step 6 rules.json exists here, and the 18-form set matches §16 exactly."""
		rules_doc = _load_json("rules.json")
		referenced: set[str] = set()
		for rule in rules_doc.get("rules", []):
			referenced |= _collect_form_refs_in_rule(rule)
		defined_codes = {f.get("form_code") for f in self.forms}
		unknown = sorted(referenced - defined_codes)
		self.assertEqual(
			unknown,
			[],
			f"STEP7-AC-008: rules.json references undefined form codes: {unknown}",
		)
		self.assertEqual(
			defined_codes,
			set(EXPECTED_FORM_CODES),
			"STEP7-AC-008: forms.form_code set must equal Step 6 §16 forward-reference set exactly",
		)
		self.assertEqual(
			len(self.forms),
			len(EXPECTED_FORM_CODES),
			f"STEP7-AC-008: expected {len(EXPECTED_FORM_CODES)} forms total, got {len(self.forms)}",
		)

	def test_step7_ac009_unique_form_codes(self) -> None:
		codes = [f.get("form_code") for f in self.forms]
		duplicates = sorted({c for c in codes if codes.count(c) > 1})
		self.assertEqual(duplicates, [], f"STEP7-AC-009: duplicate form_code values: {duplicates}")
		self.assertEqual(
			len(set(codes)),
			len(EXPECTED_FORM_CODES),
			f"STEP7-AC-009: expected {len(EXPECTED_FORM_CODES)} unique form codes",
		)

	def test_step7_ac010_minimum_schema_fields_present(self) -> None:
		schema_required = set(SCHEMA_FIELD_REQUIRED_KEYS)
		for form in self.forms:
			code = form.get("form_code")
			schema = form.get("minimum_schema_fields")
			with self.subTest(form=code):
				self.assertIsInstance(
					schema,
					list,
					f"STEP7-AC-010: form {code} minimum_schema_fields must be a list",
				)
				self.assertGreater(
					len(schema),
					0,
					f"STEP7-AC-010: form {code} minimum_schema_fields must be non-empty",
				)
				for i, sf in enumerate(schema):
					with self.subTest(schema_field_index=i):
						self.assertIsInstance(sf, dict)
						missing = [k for k in SCHEMA_FIELD_REQUIRED_KEYS if k not in sf]
						self.assertEqual(
							missing,
							[],
							f"STEP7-AC-010: form {code} schema field [{i}] missing keys: {missing}",
						)
						extra = sorted(set(sf.keys()) - schema_required)
						self.assertEqual(
							extra,
							[],
							f"STEP7-AC-010: form {code} schema field [{i}] has unexpected keys: {extra}",
						)
						self.assertIsInstance(sf.get("field_code"), str)
						self.assertTrue(sf["field_code"].strip())
						self.assertIsInstance(sf.get("label"), str)
						self.assertTrue(sf["label"].strip())
						self.assertIsInstance(sf.get("field_type"), str)
						self.assertTrue(sf["field_type"].strip())
						self.assertIsInstance(sf.get("required"), bool)
						self.assertIsInstance(sf.get("description"), str)
						self.assertTrue(sf["description"].strip())

	def test_step7_ac011_checklist_display_present(self) -> None:
		checklist_required = set(CHECKLIST_DISPLAY_REQUIRED_KEYS)
		display_orders: list[int] = []
		for form in self.forms:
			code = form.get("form_code")
			cd = form.get("checklist_display")
			with self.subTest(form=code):
				self.assertIsInstance(
					cd,
					dict,
					f"STEP7-AC-011: form {code} checklist_display must be an object",
				)
				missing = [k for k in CHECKLIST_DISPLAY_REQUIRED_KEYS if k not in cd]
				self.assertEqual(
					missing,
					[],
					f"STEP7-AC-011: form {code} checklist_display missing keys: {missing}",
				)
				extra = sorted(set(cd.keys()) - checklist_required)
				self.assertEqual(
					extra,
					[],
					f"STEP7-AC-011: form {code} checklist_display has unexpected keys: {extra}",
				)
				self.assertIn(
					cd.get("display_group"),
					EXPECTED_DISPLAY_GROUPS,
					f"STEP7-AC-011: form {code} display_group {cd.get('display_group')!r} not in §13 groups",
				)
				do = cd.get("display_order")
				self.assertIsInstance(do, int, f"display_order must be int, got {type(do).__name__}")
				self.assertGreater(do, 0, "display_order must be positive")
				self.assertIsInstance(cd.get("required_label"), str)
				self.assertTrue(cd["required_label"].strip())
				self.assertIsInstance(cd.get("not_required_label"), str)
				self.assertTrue(cd["not_required_label"].strip())
				self.assertIsInstance(cd.get("show_in_tender_pack_preview"), bool)
				display_orders.append(do)
		self.assertEqual(
			len(display_orders),
			len(set(display_orders)),
			f"STEP7-AC-011: display_order values must be unique across forms: {display_orders}",
		)
		self.assertEqual(
			display_orders,
			sorted(display_orders),
			"STEP7-AC-011: display_order must be strictly increasing in array order",
		)
		self.assertEqual(
			display_orders,
			list(range(10, 10 * (len(self.forms) + 1), 10)),
			f"STEP7-AC-011: display_order must be 10, 20, ..., {10 * len(self.forms)}",
		)

	def test_step7_ac012_schema_not_user_editable(self) -> None:
		for form in self.forms:
			code = form.get("form_code")
			with self.subTest(form=code):
				self.assertIs(
					form.get("ordinary_user_can_edit_schema"),
					False,
					f"STEP7-AC-012: form {code} ordinary_user_can_edit_schema must be False",
				)

	def test_step7_ac013_bidder_upload_replacement_goal(self) -> None:
		for form in self.forms:
			code = form.get("form_code")
			with self.subTest(form=code):
				self.assertIs(
					form.get("bidder_upload_replacement_goal"),
					True,
					f"STEP7-AC-013: form {code} bidder_upload_replacement_goal must be True",
				)

	def test_step7_ac014_no_workflow_implementation_keys(self) -> None:
		disallowed = set(DISALLOWED_FORM_KEYS_WORKFLOW)
		hits: list[str] = []
		_walk_disallowed_keys(self.forms, disallowed, [], hits)
		self.assertEqual(
			hits,
			[],
			f"STEP7-AC-014: forms.json contains disallowed workflow/portal keys at: {hits}",
		)

	def test_step7_ac015_no_other_implementation(self) -> None:
		"""STEP7-AC-015: no development outside forms.json (other files at expected state)."""
		for name, expected in OTHER_PACKAGE_SKELETONS.items():
			with self.subTest(file=name):
				self.assertEqual(_load_json(name), expected)
		manifest = _load_json("manifest.json")
		self.assertEqual(
			set(manifest.keys()),
			set(MANIFEST_REQUIRED_TOP_LEVEL_KEYS),
			"STEP7-AC-015: manifest must remain at Step 3 top-level shape",
		)
		self.assertEqual(manifest.get("template_code"), EXPECTED_TEMPLATE_CODE)
		sections_doc = _load_json("sections.json")
		self.assertEqual(
			set(sections_doc.keys()),
			set(SECTIONS_REQUIRED_TOP_LEVEL_KEYS),
			"STEP7-AC-015: sections must remain at Step 4 top-level shape",
		)
		self.assertEqual(
			len(sections_doc.get("sections", [])),
			len(EXPECTED_SECTIONS_BY_RENDER_ORDER),
			"STEP7-AC-015: sections.json must still expose 16 sections",
		)
		self.assertEqual(
			len(sections_doc.get("section_mutability_types", [])),
			len(MUTABILITY_TYPE_CODES),
			"STEP7-AC-015: sections.json must still expose 9 mutability types",
		)
		fields_doc = _load_json("fields.json")
		self.assertEqual(
			set(fields_doc.keys()),
			set(FIELDS_REQUIRED_TOP_LEVEL_KEYS),
			"STEP7-AC-015: fields must remain at Step 5 top-level shape",
		)
		self.assertEqual(
			len(fields_doc.get("fields", [])),
			EXPECTED_FIELDS_TOTAL,
			f"STEP7-AC-015: fields.json must still expose {EXPECTED_FIELDS_TOTAL} fields",
		)
		self.assertEqual(
			len(fields_doc.get("field_groups", [])),
			len(EXPECTED_FIELD_GROUP_CODES),
			"STEP7-AC-015: fields.json must still expose 9 field groups",
		)
		self.assertEqual(
			len(fields_doc.get("field_types", [])),
			len(EXPECTED_FIELD_TYPE_CODES),
			"STEP7-AC-015: fields.json must still expose 18 field types",
		)
		rules_doc = _load_json("rules.json")
		self.assertEqual(
			set(rules_doc.keys()),
			set(RULES_REQUIRED_TOP_LEVEL_KEYS),
			"STEP7-AC-015: rules must remain at Step 6 top-level shape",
		)
		self.assertEqual(
			len(rules_doc.get("rules", [])),
			len(EXPECTED_RULE_CODES),
			f"STEP7-AC-015: rules.json must still expose {len(EXPECTED_RULE_CODES)} rules",
		)
		self.assertEqual(
			len(rules_doc.get("rule_types", [])),
			len(EXPECTED_RULE_TYPE_CODES),
			"STEP7-AC-015: rules.json must still expose 11 rule types",
		)
		self.assertEqual(
			len(rules_doc.get("message_severities", [])),
			len(EXPECTED_SEVERITY_CODES),
			"STEP7-AC-015: rules.json must still expose 4 severities",
		)
		self.assertEqual(
			len(rules_doc.get("operator_definitions", [])),
			len(EXPECTED_OPERATOR_CODES),
			"STEP7-AC-015: rules.json must still expose 12 operators",
		)

	def test_form_object_required_attributes(self) -> None:
		"""Spec §11.1 — every form object must contain the 16 required attributes with correct types."""
		allowed = set(FORM_REQUIRED_KEYS)
		for form in self.forms:
			code = form.get("form_code")
			with self.subTest(form=code):
				missing = [k for k in FORM_REQUIRED_KEYS if k not in form]
				self.assertEqual(missing, [], f"form {code} missing required keys: {missing}")
				extra = sorted(set(form.keys()) - allowed)
				self.assertEqual(
					extra,
					[],
					f"form {code} contains unexpected top-level keys: {extra}",
				)
				for str_key in (
					"form_code",
					"title",
					"source_reference",
					"category",
					"respondent_type",
					"workflow_stage",
					"evidence_policy",
					"poc_treatment",
				):
					self.assertIsInstance(
						form.get(str_key),
						str,
						f"form {code}: {str_key} must be a string",
					)
					self.assertTrue(
						form[str_key].strip(),
						f"form {code}: {str_key} must be non-empty",
					)
				for bool_key in (
					"default_required",
					"ordinary_user_can_edit_schema",
					"bidder_upload_replacement_goal",
				):
					self.assertIsInstance(
						form.get(bool_key),
						bool,
						f"form {code}: {bool_key} must be bool",
					)
				for list_key in (
					"activation_rule_codes",
					"section_targets",
					"minimum_schema_fields",
					"notes",
				):
					self.assertIsInstance(
						form.get(list_key),
						list,
						f"form {code}: {list_key} must be a list",
					)
				self.assertIsInstance(
					form.get("checklist_display"),
					dict,
					f"form {code}: checklist_display must be a dict",
				)

	def test_form_code_format_and_uniqueness(self) -> None:
		"""Spec §17 — every form_code must match FORM_<UPPER_SNAKE> and be unique."""
		pattern = re.compile(FORM_CODE_FORMAT_PATTERN)
		codes = [f.get("form_code") for f in self.forms]
		duplicates = sorted({c for c in codes if codes.count(c) > 1})
		self.assertEqual(duplicates, [], f"duplicate form_code values: {duplicates}")
		for code in codes:
			with self.subTest(form=code):
				self.assertIsInstance(code, str)
				self.assertRegex(
					code,
					pattern,
					f"form_code {code!r} must match FORM_<UPPER_SNAKE> (spec §17)",
				)

	def test_valid_category_respondent_stage_evidence_references(self) -> None:
		"""Spec §17 — every form's category / respondent_type / workflow_stage / evidence_policy must be defined."""
		valid_categories = set(EXPECTED_FORM_CATEGORY_CODES)
		valid_respondents = set(EXPECTED_RESPONDENT_TYPE_CODES)
		valid_stages = set(EXPECTED_WORKFLOW_STAGE_CODES)
		valid_policies = set(EXPECTED_EVIDENCE_POLICY_CODES)
		for form in self.forms:
			code = form.get("form_code")
			with self.subTest(form=code):
				self.assertIn(
					form.get("category"),
					valid_categories,
					f"form {code} has unknown category {form.get('category')!r}",
				)
				self.assertIn(
					form.get("respondent_type"),
					valid_respondents,
					f"form {code} has unknown respondent_type {form.get('respondent_type')!r}",
				)
				self.assertIn(
					form.get("workflow_stage"),
					valid_stages,
					f"form {code} has unknown workflow_stage {form.get('workflow_stage')!r}",
				)
				self.assertIn(
					form.get("evidence_policy"),
					valid_policies,
					f"form {code} has unknown evidence_policy {form.get('evidence_policy')!r}",
				)

	def test_valid_section_targets(self) -> None:
		"""Spec §17 + §5 — every form's section_targets entries must exist in sections.json (16 codes)."""
		sections_doc = _load_json("sections.json")
		section_codes = {s.get("section_code") for s in sections_doc.get("sections", [])}
		self.assertEqual(
			len(section_codes),
			len(EXPECTED_SECTIONS_BY_RENDER_ORDER),
			"cross-file: sections.json must expose 16 section codes",
		)
		for form in self.forms:
			code = form.get("form_code")
			targets = form.get("section_targets") or []
			with self.subTest(form=code):
				unknown = sorted(set(targets) - section_codes)
				self.assertEqual(
					unknown,
					[],
					f"form {code} references unknown section codes: {unknown}",
				)

	def test_valid_activation_rule_codes(self) -> None:
		"""Spec §17 + §5 — every activation_rule_codes entry must exist in rules.json (31 codes); empty list iff default_required."""
		rules_doc = _load_json("rules.json")
		rule_codes = {r.get("rule_code") for r in rules_doc.get("rules", [])}
		self.assertEqual(
			len(rule_codes),
			len(EXPECTED_RULE_CODES),
			f"cross-file: rules.json must expose {len(EXPECTED_RULE_CODES)} rule codes",
		)
		for form in self.forms:
			code = form.get("form_code")
			activation = form.get("activation_rule_codes") or []
			with self.subTest(form=code):
				unknown = sorted(set(activation) - rule_codes)
				self.assertEqual(
					unknown,
					[],
					f"form {code} references unknown activation rule codes: {unknown}",
				)
				if not activation:
					self.assertIs(
						form.get("default_required"),
						True,
						f"form {code} has no activation rules so must be default_required = True",
					)

	def test_default_required_forms_match_spec_section14(self) -> None:
		"""Spec §14 — exactly 7 forms have default_required = True; the other 11 have False."""
		actual_required = {f.get("form_code") for f in self.forms if f.get("default_required") is True}
		self.assertEqual(
			actual_required,
			set(EXPECTED_DEFAULT_REQUIRED_FORMS),
			"§14: default_required = True set must match the 7 always-required forms",
		)
		actual_optional = {f.get("form_code") for f in self.forms if f.get("default_required") is False}
		expected_optional = set(EXPECTED_FORM_CODES) - set(EXPECTED_DEFAULT_REQUIRED_FORMS)
		self.assertEqual(
			actual_optional,
			expected_optional,
			"§14: default_required = False set must match the 11 conditional forms",
		)
		self.assertEqual(
			len(actual_required),
			7,
			f"§14: expected 7 default_required forms, got {len(actual_required)}",
		)
		self.assertEqual(
			len(actual_optional),
			11,
			f"§14: expected 11 conditional forms, got {len(actual_optional)}",
		)

	def test_minimum_schema_field_types_valid(self) -> None:
		"""Spec §12 (soft cross-file invariant) — every minimum_schema_fields[].field_type ⊆ fields.json field-type codes."""
		fields_doc = _load_json("fields.json")
		valid_types = {ft.get("code") for ft in fields_doc.get("field_types", [])}
		self.assertEqual(
			len(valid_types),
			len(EXPECTED_FIELD_TYPE_CODES),
			"cross-file: fields.json must expose 18 field-type codes",
		)
		for form in self.forms:
			code = form.get("form_code")
			schema = form.get("minimum_schema_fields") or []
			with self.subTest(form=code):
				for i, sf in enumerate(schema):
					ft = sf.get("field_type")
					self.assertIn(
						ft,
						valid_types,
						f"form {code} schema field [{i}] uses unknown field_type {ft!r} "
						"(must be one of fields.json field_types)",
					)


class TestStdWorksPocSampleTenderStep8(IntegrationTestCase):
	"""Step 8 acceptance: full sample_tender.json content per spec §6 / §7 / §8 / §9 / §10 / §11 / §12 / §13 / §14 / §17 / §18."""

	def setUp(self) -> None:
		self.sample = _load_json("sample_tender.json")
		self.tender = self.sample.get("tender", {})
		self.configuration = self.sample.get("configuration", {})
		self.lots = self.sample.get("lots", [])
		self.boq = self.sample.get("boq", {})
		self.boq_rows = self.boq.get("rows", []) if isinstance(self.boq, dict) else []
		self.activated_forms = self.sample.get("expected_activated_forms", [])
		self.profile = self.sample.get("expected_validation_profile", {})
		self.variants = self.sample.get("scenario_variants", [])

	def test_step8_ac001_complete_required_top_level_keys(self) -> None:
		missing = [k for k in SAMPLE_REQUIRED_TOP_LEVEL_KEYS if k not in self.sample]
		self.assertEqual(
			missing,
			[],
			f"STEP8-AC-001: sample_tender.json missing required top-level keys: {missing}",
		)
		extra = sorted(set(self.sample.keys()) - set(SAMPLE_REQUIRED_TOP_LEVEL_KEYS))
		self.assertEqual(
			extra,
			[],
			f"STEP8-AC-001: sample_tender.json has unexpected top-level keys: {extra}",
		)

	def test_step8_ac002_valid_json(self) -> None:
		try:
			json.loads((PACKAGE_DIR / "sample_tender.json").read_text(encoding="utf-8"))
		except json.JSONDecodeError as exc:
			self.fail(f"STEP8-AC-002: sample_tender.json is not valid JSON: {exc}")

	def test_step8_ac003_template_code_exact(self) -> None:
		self.assertEqual(
			self.sample.get("template_code"),
			EXPECTED_TEMPLATE_CODE,
			f"STEP8-AC-003: template_code must be {EXPECTED_TEMPLATE_CODE}",
		)
		self.assertEqual(
			self.tender.get("template_code"),
			EXPECTED_TEMPLATE_CODE,
			"STEP8-AC-003: tender.template_code must equal the package template_code",
		)
		self.assertEqual(
			self.configuration.get("SYSTEM.TEMPLATE_CODE"),
			EXPECTED_TEMPLATE_CODE,
			"STEP8-AC-003: configuration.SYSTEM.TEMPLATE_CODE must equal the package template_code",
		)

	def test_step8_ac004_sample_code_exact(self) -> None:
		self.assertEqual(
			self.sample.get("sample_code"),
			EXPECTED_SAMPLE_CODE,
			f"STEP8-AC-004: sample_code must be {EXPECTED_SAMPLE_CODE}",
		)

	def test_step8_ac005_primary_sample_is_ward_admin_block(self) -> None:
		self.assertEqual(
			self.sample.get("sample_name"),
			EXPECTED_SAMPLE_NAME,
			f"STEP8-AC-005: sample_name must be {EXPECTED_SAMPLE_NAME!r}",
		)
		self.assertEqual(
			self.tender.get("title"),
			EXPECTED_SAMPLE_NAME,
			f"STEP8-AC-005: tender.title must be {EXPECTED_SAMPLE_NAME!r}",
		)
		self.assertEqual(
			self.configuration.get("TENDER.TENDER_NAME"),
			EXPECTED_SAMPLE_NAME,
			f"STEP8-AC-005: configuration.TENDER.TENDER_NAME must be {EXPECTED_SAMPLE_NAME!r}",
		)
		self.assertEqual(
			self.sample.get("sample_status"),
			EXPECTED_SAMPLE_STATUS,
			f"STEP8-AC-005: sample_status must be {EXPECTED_SAMPLE_STATUS!r}",
		)
		purpose = self.sample.get("purpose")
		self.assertIsInstance(purpose, str, "STEP8-AC-005: purpose must be a string")
		self.assertTrue(purpose.strip(), "STEP8-AC-005: purpose must be non-empty")

	def test_step8_ac006_configuration_uses_fields_json(self) -> None:
		fields_doc = _load_json("fields.json")
		field_codes = {f.get("field_code") for f in fields_doc.get("fields", [])}
		self.assertEqual(
			len(field_codes),
			EXPECTED_FIELDS_TOTAL,
			f"cross-file: fields.json must expose {EXPECTED_FIELDS_TOTAL} field codes",
		)
		config_keys = set(self.configuration.keys())
		missing = sorted(field_codes - config_keys)
		self.assertEqual(
			missing,
			[],
			f"STEP8-AC-006: configuration is missing field codes: {missing}",
		)
		extras = sorted(config_keys - field_codes)
		self.assertEqual(
			extras,
			[],
			f"STEP8-AC-006: configuration uses unknown field codes: {extras}",
		)
		missing_tender = [k for k in EXPECTED_SAMPLE_TENDER_KEYS if k not in self.tender]
		self.assertEqual(
			missing_tender,
			[],
			f"STEP8-AC-006: tender object missing required keys: {missing_tender}",
		)
		extra_tender = sorted(set(self.tender.keys()) - set(EXPECTED_SAMPLE_TENDER_KEYS))
		self.assertEqual(
			extra_tender,
			[],
			f"STEP8-AC-006: tender object has unexpected keys: {extra_tender}",
		)
		self.assertEqual(
			self.tender.get("procurement_method"),
			self.configuration.get("METHOD.PROCUREMENT_METHOD"),
			"STEP8-AC-006: tender.procurement_method must equal configuration METHOD.PROCUREMENT_METHOD",
		)
		self.assertEqual(
			self.tender.get("procurement_category"),
			"WORKS",
			"STEP8-AC-006: tender.procurement_category must be WORKS",
		)

	def test_step8_ac007_at_least_two_lots(self) -> None:
		self.assertIsInstance(self.lots, list, "STEP8-AC-007: lots must be a list")
		self.assertGreaterEqual(
			len(self.lots),
			EXPECTED_LOT_COUNT_MIN,
			f"STEP8-AC-007: must have at least {EXPECTED_LOT_COUNT_MIN} lots",
		)
		lot_pattern = re.compile(r"^LOT-\d{3}$")
		seen_codes: list[str] = []
		for i, lot in enumerate(self.lots):
			with self.subTest(lot_index=i):
				self.assertIsInstance(lot, dict, f"lot[{i}] must be an object")
				missing = [k for k in EXPECTED_LOT_REQUIRED_KEYS if k not in lot]
				self.assertEqual(missing, [], f"lot[{i}] missing required keys: {missing}")
				extra = sorted(set(lot.keys()) - set(EXPECTED_LOT_REQUIRED_KEYS))
				self.assertEqual(extra, [], f"lot[{i}] has unexpected keys: {extra}")
				code = lot.get("lot_code")
				self.assertIsInstance(code, str)
				self.assertRegex(
					code,
					lot_pattern,
					f"lot[{i}].lot_code {code!r} must match LOT-NNN",
				)
				self.assertIsInstance(lot.get("lot_title"), str)
				self.assertTrue(lot["lot_title"].strip())
				self.assertIsInstance(lot.get("description"), str)
				self.assertTrue(lot["description"].strip())
				self.assertIsInstance(lot.get("estimated_value"), int)
				self.assertGreater(lot["estimated_value"], 0)
				self.assertEqual(lot.get("currency"), "KES")
				seen_codes.append(code)
		duplicates = sorted({c for c in seen_codes if seen_codes.count(c) > 1})
		self.assertEqual(duplicates, [], f"STEP8-AC-007: duplicate lot_code values: {duplicates}")

	def test_step8_ac008_representative_boq_rows(self) -> None:
		self.assertIsInstance(self.boq, dict, "STEP8-AC-008: boq must be an object")
		self.assertEqual(self.boq.get("currency"), "KES")
		self.assertEqual(self.boq.get("pricing_mode"), "UNIT_RATE")
		self.assertIsInstance(self.boq_rows, list)
		self.assertGreaterEqual(
			len(self.boq_rows),
			len(EXPECTED_BOQ_CATEGORIES),
			f"STEP8-AC-008: boq.rows must include at least {len(EXPECTED_BOQ_CATEGORIES)} representative rows",
		)
		lot_codes = {lot.get("lot_code") for lot in self.lots}
		for i, row in enumerate(self.boq_rows):
			with self.subTest(boq_row_index=i):
				self.assertIsInstance(row, dict)
				missing = [k for k in EXPECTED_BOQ_ROW_REQUIRED_KEYS if k not in row]
				self.assertEqual(missing, [], f"boq.rows[{i}] missing keys: {missing}")
				extra = sorted(set(row.keys()) - set(EXPECTED_BOQ_ROW_REQUIRED_KEYS))
				self.assertEqual(extra, [], f"boq.rows[{i}] has unexpected keys: {extra}")
				self.assertIsInstance(row.get("item_code"), str)
				self.assertTrue(row["item_code"].strip())
				self.assertIsInstance(row.get("item_category"), str)
				self.assertTrue(row["item_category"].strip())
				if row.get("item_category") == "GRAND_SUMMARY":
					self.assertIsNone(
						row.get("lot_code"),
						"GRAND_SUMMARY row must have lot_code = null",
					)
				else:
					self.assertIn(
						row.get("lot_code"),
						lot_codes,
						f"boq.rows[{i}].lot_code {row.get('lot_code')!r} must reference a defined lot",
					)
				self.assertIsInstance(row.get("description"), str)
				self.assertTrue(row["description"].strip())
				self.assertIsInstance(row.get("unit"), str)
				self.assertTrue(row["unit"].strip())
				self.assertIsInstance(row.get("quantity"), int)
				self.assertIsInstance(row.get("is_priced_by_bidder"), bool)

	def test_step8_ac009_dayworks_and_provisional_sums_present(self) -> None:
		categories = {row.get("item_category") for row in self.boq_rows}
		self.assertIn(
			"DAYWORKS",
			categories,
			"STEP8-AC-009: boq.rows must include at least one DAYWORKS row",
		)
		self.assertIn(
			"PROVISIONAL_SUMS",
			categories,
			"STEP8-AC-009: boq.rows must include at least one PROVISIONAL_SUMS row",
		)
		missing_categories = sorted(EXPECTED_BOQ_CATEGORIES - categories)
		self.assertEqual(
			missing_categories,
			[],
			f"STEP8-AC-009: boq.rows missing required §10 categories: {missing_categories}",
		)

	def test_step8_ac010_expected_activated_forms_declared(self) -> None:
		forms_doc = _load_json("forms.json")
		form_codes = {f.get("form_code") for f in forms_doc.get("forms", [])}
		self.assertEqual(
			len(form_codes),
			len(EXPECTED_FORM_CODES),
			f"cross-file: forms.json must expose {len(EXPECTED_FORM_CODES)} form codes",
		)
		self.assertIsInstance(self.activated_forms, list)
		self.assertEqual(
			len(self.activated_forms),
			len(EXPECTED_ACTIVATED_FORM_CODES),
			f"STEP8-AC-010: expected {len(EXPECTED_ACTIVATED_FORM_CODES)} activated forms, got {len(self.activated_forms)}",
		)
		self.assertEqual(
			set(self.activated_forms),
			set(EXPECTED_ACTIVATED_FORM_CODES),
			"STEP8-AC-010: expected_activated_forms must match the spec §11 set exactly",
		)
		unknown_active = sorted(set(self.activated_forms) - form_codes)
		self.assertEqual(
			unknown_active,
			[],
			f"STEP8-AC-010: expected_activated_forms references unknown form codes: {unknown_active}",
		)
		profile = self.profile
		self.assertIsInstance(profile, dict, "STEP8-AC-010: expected_validation_profile must be a dict")
		missing = [k for k in VALIDATION_PROFILE_REQUIRED_KEYS if k not in profile]
		self.assertEqual(
			missing,
			[],
			f"STEP8-AC-010: expected_validation_profile missing required keys: {missing}",
		)
		extra = sorted(set(profile.keys()) - set(VALIDATION_PROFILE_REQUIRED_KEYS))
		self.assertEqual(
			extra,
			[],
			f"STEP8-AC-010: expected_validation_profile has unexpected keys: {extra}",
		)
		self.assertEqual(profile.get("expected_blockers"), 0)
		self.assertEqual(profile.get("expected_errors"), 0)
		self.assertEqual(profile.get("expected_warnings"), 0)
		inactive = profile.get("expected_inactive_forms", [])
		self.assertEqual(
			set(inactive),
			set(EXPECTED_INACTIVE_FORM_CODES),
			"STEP8-AC-010: expected_inactive_forms must match the spec §11 inactive set",
		)
		unknown_inactive = sorted(set(inactive) - form_codes)
		self.assertEqual(
			unknown_inactive,
			[],
			f"STEP8-AC-010: expected_inactive_forms references unknown form codes: {unknown_inactive}",
		)
		self.assertTrue(
			set(self.activated_forms).isdisjoint(set(inactive)),
			"STEP8-AC-010: expected_activated_forms and expected_inactive_forms must be disjoint",
		)
		self.assertIsInstance(profile.get("notes"), list)
		self.assertGreater(len(profile["notes"]), 0)

	def test_step8_ac011_required_scenario_variants_declared(self) -> None:
		fields_doc = _load_json("fields.json")
		field_codes = {f.get("field_code") for f in fields_doc.get("fields", [])}
		forms_doc = _load_json("forms.json")
		form_codes = {f.get("form_code") for f in forms_doc.get("forms", [])}
		self.assertIsInstance(self.variants, list)
		self.assertEqual(
			len(self.variants),
			len(EXPECTED_SCENARIO_VARIANT_CODES),
			f"STEP8-AC-011: expected {len(EXPECTED_SCENARIO_VARIANT_CODES)} scenario variants",
		)
		actual_codes = [v.get("variant_code") for v in self.variants]
		self.assertEqual(
			set(actual_codes),
			set(EXPECTED_SCENARIO_VARIANT_CODES),
			"STEP8-AC-011: variant codes must match the spec §12 set exactly",
		)
		duplicates = sorted({c for c in actual_codes if actual_codes.count(c) > 1})
		self.assertEqual(duplicates, [], f"STEP8-AC-011: duplicate variant codes: {duplicates}")
		allowed = set(VARIANT_REQUIRED_KEYS) | set(VARIANT_OPTIONAL_KEYS)
		for variant in self.variants:
			code = variant.get("variant_code")
			with self.subTest(variant=code):
				missing = [k for k in VARIANT_REQUIRED_KEYS if k not in variant]
				self.assertEqual(missing, [], f"variant {code} missing required keys: {missing}")
				extra = sorted(set(variant.keys()) - allowed)
				self.assertEqual(extra, [], f"variant {code} has unexpected keys: {extra}")
				self.assertIsInstance(variant.get("description"), str)
				self.assertTrue(variant["description"].strip())
				overrides = variant.get("configuration_overrides")
				self.assertIsInstance(overrides, dict)
				unknown_fields = sorted(set(overrides.keys()) - field_codes)
				self.assertEqual(
					unknown_fields,
					[],
					f"variant {code} configuration_overrides references unknown fields: {unknown_fields}",
				)
				self.assertIsInstance(variant.get("lot_overrides"), list)
				self.assertIsInstance(variant.get("boq_overrides"), dict)
				additional = variant.get("expected_additional_forms") or []
				self.assertIsInstance(additional, list)
				unknown_add = sorted(set(additional) - form_codes)
				self.assertEqual(
					unknown_add,
					[],
					f"variant {code} expected_additional_forms references unknown forms: {unknown_add}",
				)
				if "expected_inactive_forms" in variant:
					inactive = variant.get("expected_inactive_forms") or []
					self.assertIsInstance(inactive, list)
					unknown_inactive = sorted(set(inactive) - form_codes)
					self.assertEqual(
						unknown_inactive,
						[],
						f"variant {code} expected_inactive_forms references unknown forms: {unknown_inactive}",
					)
				self.assertIsInstance(variant.get("expected_blockers"), int)
				self.assertGreaterEqual(variant["expected_blockers"], 0)

	def test_step8_ac012_negative_variants_declare_expected_blockers(self) -> None:
		by_code = {v.get("variant_code"): v for v in self.variants}
		for code in EXPECTED_NEGATIVE_VARIANT_CODES:
			with self.subTest(variant=code):
				variant = by_code.get(code)
				self.assertIsNotNone(variant, f"STEP8-AC-012: variant {code} must exist")
				self.assertGreaterEqual(
					variant.get("expected_blockers", 0),
					1,
					f"STEP8-AC-012: negative variant {code} must declare expected_blockers >= 1",
				)
		positives = set(EXPECTED_SCENARIO_VARIANT_CODES) - EXPECTED_NEGATIVE_VARIANT_CODES
		for code in positives:
			with self.subTest(variant=code):
				variant = by_code.get(code)
				self.assertIsNotNone(variant)
				self.assertEqual(
					variant.get("expected_blockers"),
					0,
					f"STEP8-AC-012: positive variant {code} must declare expected_blockers = 0",
				)

	def test_step8_ac013_no_new_template_artefacts(self) -> None:
		fields_doc = _load_json("fields.json")
		field_codes = {f.get("field_code") for f in fields_doc.get("fields", [])}
		forms_doc = _load_json("forms.json")
		form_codes = {f.get("form_code") for f in forms_doc.get("forms", [])}
		unknown_fields = sorted(set(self.configuration.keys()) - field_codes)
		self.assertEqual(
			unknown_fields,
			[],
			f"STEP8-AC-013: configuration introduces new field codes: {unknown_fields}",
		)
		unknown_active = sorted(set(self.activated_forms) - form_codes)
		self.assertEqual(
			unknown_active,
			[],
			f"STEP8-AC-013: expected_activated_forms introduces new form codes: {unknown_active}",
		)
		unknown_inactive = sorted(set(self.profile.get("expected_inactive_forms", []) or []) - form_codes)
		self.assertEqual(
			unknown_inactive,
			[],
			f"STEP8-AC-013: expected_inactive_forms introduces new form codes: {unknown_inactive}",
		)
		disallowed_top_level_keys = {
			"field_types",
			"field_groups",
			"fields",
			"rules",
			"rule_types",
			"forms",
			"form_categories",
			"sections",
			"section_mutability_types",
		}
		leaks = sorted(disallowed_top_level_keys & set(self.sample.keys()))
		self.assertEqual(
			leaks,
			[],
			f"STEP8-AC-013: sample_tender.json leaks template-schema keys: {leaks}",
		)

	def test_step8_ac014_no_other_implementation(self) -> None:
		"""STEP8-AC-014: no development outside sample_tender.json (other files at expected state)."""
		for name, expected in OTHER_PACKAGE_SKELETONS.items():
			with self.subTest(file=name):
				self.assertEqual(_load_json(name), expected)
		manifest = _load_json("manifest.json")
		self.assertEqual(
			set(manifest.keys()),
			set(MANIFEST_REQUIRED_TOP_LEVEL_KEYS),
			"STEP8-AC-014: manifest must remain at Step 3 top-level shape",
		)
		self.assertEqual(manifest.get("template_code"), EXPECTED_TEMPLATE_CODE)
		sections_doc = _load_json("sections.json")
		self.assertEqual(
			set(sections_doc.keys()),
			set(SECTIONS_REQUIRED_TOP_LEVEL_KEYS),
			"STEP8-AC-014: sections must remain at Step 4 top-level shape",
		)
		self.assertEqual(
			len(sections_doc.get("sections", [])),
			len(EXPECTED_SECTIONS_BY_RENDER_ORDER),
			"STEP8-AC-014: sections.json must still expose 16 sections",
		)
		self.assertEqual(
			len(sections_doc.get("section_mutability_types", [])),
			len(MUTABILITY_TYPE_CODES),
			"STEP8-AC-014: sections.json must still expose 9 mutability types",
		)
		fields_doc = _load_json("fields.json")
		self.assertEqual(
			set(fields_doc.keys()),
			set(FIELDS_REQUIRED_TOP_LEVEL_KEYS),
			"STEP8-AC-014: fields must remain at Step 5 top-level shape",
		)
		self.assertEqual(
			len(fields_doc.get("fields", [])),
			EXPECTED_FIELDS_TOTAL,
			f"STEP8-AC-014: fields.json must still expose {EXPECTED_FIELDS_TOTAL} fields",
		)
		self.assertEqual(
			len(fields_doc.get("field_groups", [])),
			len(EXPECTED_FIELD_GROUP_CODES),
			"STEP8-AC-014: fields.json must still expose 9 field groups",
		)
		self.assertEqual(
			len(fields_doc.get("field_types", [])),
			len(EXPECTED_FIELD_TYPE_CODES),
			"STEP8-AC-014: fields.json must still expose 18 field types",
		)
		rules_doc = _load_json("rules.json")
		self.assertEqual(
			set(rules_doc.keys()),
			set(RULES_REQUIRED_TOP_LEVEL_KEYS),
			"STEP8-AC-014: rules must remain at Step 6 top-level shape",
		)
		self.assertEqual(
			len(rules_doc.get("rules", [])),
			len(EXPECTED_RULE_CODES),
			f"STEP8-AC-014: rules.json must still expose {len(EXPECTED_RULE_CODES)} rules",
		)
		self.assertEqual(
			len(rules_doc.get("rule_types", [])),
			len(EXPECTED_RULE_TYPE_CODES),
			"STEP8-AC-014: rules.json must still expose 11 rule types",
		)
		self.assertEqual(
			len(rules_doc.get("message_severities", [])),
			len(EXPECTED_SEVERITY_CODES),
			"STEP8-AC-014: rules.json must still expose 4 severities",
		)
		self.assertEqual(
			len(rules_doc.get("operator_definitions", [])),
			len(EXPECTED_OPERATOR_CODES),
			"STEP8-AC-014: rules.json must still expose 12 operators",
		)
		forms_doc = _load_json("forms.json")
		self.assertEqual(
			set(forms_doc.keys()),
			set(FORMS_REQUIRED_TOP_LEVEL_KEYS),
			"STEP8-AC-014: forms must remain at Step 7 top-level shape",
		)
		self.assertEqual(
			len(forms_doc.get("forms", [])),
			len(EXPECTED_FORM_CODES),
			"STEP8-AC-014: forms.json must still expose 18 forms",
		)
		self.assertEqual(
			len(forms_doc.get("form_categories", [])),
			len(EXPECTED_FORM_CATEGORY_CODES),
			"STEP8-AC-014: forms.json must still expose 9 categories",
		)
		self.assertEqual(
			len(forms_doc.get("respondent_types", [])),
			len(EXPECTED_RESPONDENT_TYPE_CODES),
			"STEP8-AC-014: forms.json must still expose 7 respondent types",
		)
		self.assertEqual(
			len(forms_doc.get("workflow_stages", [])),
			len(EXPECTED_WORKFLOW_STAGE_CODES),
			"STEP8-AC-014: forms.json must still expose 7 workflow stages",
		)
		self.assertEqual(
			len(forms_doc.get("evidence_policies", [])),
			len(EXPECTED_EVIDENCE_POLICY_CODES),
			"STEP8-AC-014: forms.json must still expose 6 evidence policies",
		)

	def test_section14_tender_security_amount_within_2_percent(self) -> None:
		amount = self.configuration.get("SECURITY.TENDER_SECURITY_AMOUNT")
		estimated = self.configuration.get("TENDER.ESTIMATED_COST")
		self.assertIsInstance(amount, int, "tender security amount must be int")
		self.assertIsInstance(estimated, int, "estimated cost must be int")
		self.assertGreater(estimated, 0)
		limit = (EXPECTED_TENDER_SECURITY_LIMIT_PERCENT / 100.0) * estimated
		self.assertLessEqual(
			amount,
			limit,
			f"§14: tender security amount {amount} must be <= 2% of estimated cost ({limit})",
		)

	def test_section14_core_dates_logically_ordered(self) -> None:
		from datetime import datetime

		clarification = datetime.fromisoformat(self.configuration["DATES.CLARIFICATION_DEADLINE"])
		submission = datetime.fromisoformat(self.configuration["DATES.SUBMISSION_DEADLINE"])
		opening = datetime.fromisoformat(self.configuration["DATES.OPENING_DATETIME"])
		self.assertLess(
			clarification,
			submission,
			"§14: clarification deadline must be before submission deadline",
		)
		self.assertGreater(
			opening,
			submission,
			"§14: opening date/time must be after submission deadline",
		)

	def test_section14_publication_before_submission(self) -> None:
		from datetime import date, datetime

		publication = date.fromisoformat(self.configuration["DATES.PUBLICATION_DATE"])
		submission = datetime.fromisoformat(self.configuration["DATES.SUBMISSION_DEADLINE"]).date()
		self.assertLess(
			publication,
			submission,
			"§14: publication date must be before submission deadline",
		)

	def test_section14_site_visit_and_pre_tender_meeting_before_submission(self) -> None:
		from datetime import datetime

		site_visit = datetime.fromisoformat(self.configuration["DATES.SITE_VISIT_DATE"])
		pre_tender = datetime.fromisoformat(self.configuration["DATES.PRE_TENDER_MEETING_DATE"])
		submission = datetime.fromisoformat(self.configuration["DATES.SUBMISSION_DEADLINE"])
		self.assertLess(site_visit, submission, "§14: site visit date must be before submission deadline")
		self.assertLess(
			pre_tender,
			submission,
			"§14: pre-tender meeting date must be before submission deadline",
		)

	def test_section14_tender_validity_days_positive(self) -> None:
		validity = self.configuration.get("DATES.TENDER_VALIDITY_DAYS")
		self.assertIsInstance(validity, int, "DATES.TENDER_VALIDITY_DAYS must be int")
		self.assertEqual(validity, 120, "§14: tender validity days must equal the §8 sample value")

	def test_lot_codes_referenced_by_boq(self) -> None:
		lot_codes = {lot.get("lot_code") for lot in self.lots}
		for i, row in enumerate(self.boq_rows):
			with self.subTest(boq_row_index=i):
				lot_code = row.get("lot_code")
				if lot_code is None:
					self.assertEqual(
						row.get("item_category"),
						"GRAND_SUMMARY",
						f"boq.rows[{i}] has lot_code = null but is not GRAND_SUMMARY",
					)
				else:
					self.assertIn(
						lot_code,
						lot_codes,
						f"boq.rows[{i}].lot_code {lot_code!r} must reference a defined lot",
					)

	def test_variant_overrides_reference_known_fields_and_forms(self) -> None:
		"""Spec §14 + §12 — focused regression check that variant overrides do not introduce new artefacts."""
		fields_doc = _load_json("fields.json")
		field_codes = {f.get("field_code") for f in fields_doc.get("fields", [])}
		forms_doc = _load_json("forms.json")
		form_codes = {f.get("form_code") for f in forms_doc.get("forms", [])}
		all_override_keys: set[str] = set()
		all_form_refs: set[str] = set()
		for variant in self.variants:
			overrides = variant.get("configuration_overrides") or {}
			all_override_keys |= set(overrides.keys())
			for key in ("expected_additional_forms", "expected_inactive_forms"):
				all_form_refs |= set(variant.get(key) or [])
		unknown_fields = sorted(all_override_keys - field_codes)
		self.assertEqual(
			unknown_fields,
			[],
			f"variant configuration_overrides reference unknown field codes: {unknown_fields}",
		)
		unknown_forms = sorted(all_form_refs - form_codes)
		self.assertEqual(
			unknown_forms,
			[],
			f"variant expected forms reference unknown form codes: {unknown_forms}",
		)
