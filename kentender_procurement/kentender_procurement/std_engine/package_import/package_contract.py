# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-02 — package file classification contract."""

from __future__ import annotations

# Relative to detected package root inside the zip.
REQUIRED_ANY_IMPORT: tuple[str, ...] = (
	"manifest.json",
	"checksums.json",
)

REQUIRED_VERTICAL_SLICE: tuple[str, ...] = (
	"template/family.json",
	"template/version.json",
	"source/source_document.json",
	"source/source_anchors.json",
	"template/sections.json",
	"template/clauses.json",
)

OPTIONAL_WHEN_PRESENT: tuple[str, ...] = (
	"configuration/parameters.json",
	"configuration/parameter_options.json",
	"rules/rule_catalog.json",
	"rules/rule_bindings.json",
	"rules/rule_test_cases.json",
	"forms/form_catalog.json",
	"forms/form_fields.json",
	"forms/form_sections.json",
	"forms/evidence_requirements.json",
	"requirements/requirement_schema.json",
	"pricing/price_schedule_catalog.json",
	"evaluation/evaluation_schema.json",
	"contract/contract_schema.json",
	"rendering/render_blocks.json",
	"template/clause_fragments.json",
	"tests/validation_smoke_tests.json",
	"tests/tender_binding_smoke_tests.json",
	"tests/smoke_tests.json",
	"tests/sample_tender_instances.json",
	"tests/validation_expectations.json",
	"tests/verbatim_reconciliation.json",
)

SKIPPED_PREFIXES: tuple[str, ...] = (
	"fixtures/nssf_erp/",
)

PARSED_PAYLOAD_KEYS: tuple[str, ...] = (
	"family",
	"version",
	"source_document",
	"source_anchors",
	"sections",
	"clauses",
)

PAYLOAD_PATH_BY_KEY: dict[str, str] = {
	"family": "template/family.json",
	"version": "template/version.json",
	"source_document": "source/source_document.json",
	"source_anchors": "source/source_anchors.json",
	"sections": "template/sections.json",
	"clauses": "template/clauses.json",
}

OPTIONAL_PAYLOAD_PATH_BY_KEY: dict[str, str] = {
	"parameters": "configuration/parameters.json",
	"parameter_options": "configuration/parameter_options.json",
	"rules": "rules/rule_catalog.json",
	"rule_bindings": "rules/rule_bindings.json",
	"rule_test_cases": "rules/rule_test_cases.json",
	"forms": "forms/form_catalog.json",
	"form_fields": "forms/form_fields.json",
	"form_sections": "forms/form_sections.json",
	"evidence_requirements": "forms/evidence_requirements.json",
	"requirements": "requirements/requirement_schema.json",
	"price_schedules": "pricing/price_schedule_catalog.json",
	"evaluation_schemas": "evaluation/evaluation_schema.json",
	"contract_schemas": "contract/contract_schema.json",
	"render_blocks": "rendering/render_blocks.json",
	"clause_fragments": "template/clause_fragments.json",
	"tender_binding_smoke_tests": "tests/tender_binding_smoke_tests.json",
	"smoke_tests": "tests/smoke_tests.json",
	"sample_tender_instances": "tests/sample_tender_instances.json",
	"validation_expectations": "tests/validation_expectations.json",
	"verbatim_reconciliation": "tests/verbatim_reconciliation.json",
}

RECORD_COUNT_KEYS: tuple[str, ...] = (
	"families",
	"versions",
	"sourceDocuments",
	"anchors",
	"sections",
	"clauses",
	"parameters",
	"rules",
	"forms",
	"formFields",
	"requirements",
	"priceSchedules",
	"evaluationSchemas",
	"renderBlocks",
	"usageBindings",
)

SOURCE_DOCUMENT_SKIP_POLICIES: tuple[str, ...] = (
	"DO_NOT_IMPORT",
	"DO_NOT_IMPORT_BY_DEFAULT",
)
