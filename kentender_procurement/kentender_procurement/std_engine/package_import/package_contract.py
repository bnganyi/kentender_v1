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
	"rules/rule_catalog.json",
	"forms/form_catalog.json",
	"forms/form_fields.json",
	"requirements/requirement_schema.json",
	"pricing/price_schedule_catalog.json",
	"evaluation/evaluation_schema.json",
	"rendering/render_blocks.json",
	"tests/validation_smoke_tests.json",
	"tests/tender_binding_smoke_tests.json",
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
	"rules": "rules/rule_catalog.json",
	"forms": "forms/form_catalog.json",
	"form_fields": "forms/form_fields.json",
	"requirements": "requirements/requirement_schema.json",
	"price_schedules": "pricing/price_schedule_catalog.json",
	"evaluation_schemas": "evaluation/evaluation_schema.json",
	"render_blocks": "rendering/render_blocks.json",
	"tender_binding_smoke_tests": "tests/tender_binding_smoke_tests.json",
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
