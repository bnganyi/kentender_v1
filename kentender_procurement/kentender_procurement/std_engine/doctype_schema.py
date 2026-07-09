# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Engine core DocType registry — BE-01 schema contract for tests."""

from __future__ import annotations

from kentender_procurement.std_engine.constants import (
	FRAPPE_MODULE,
	LIFECYCLE_STATES,
	UI_MODE_READ_ONLY_INSPECTION,
)

CORE_DOCTYPES: tuple[str, ...] = (
	"STD Family",
	"STD Version",
	"STD Source Document",
	"STD Source Anchor",
	"STD Section",
	"STD Clause",
	"STD Parameter",
	"STD Rule",
	"STD Form Schema",
	"STD Form Field",
	"STD Requirement Schema",
	"STD Price Schedule Schema",
	"STD Evaluation Schema",
	"STD Render Block",
	"STD Validation Run",
	"STD Validation Finding",
	"STD Audit Event",
	"STD Usage Binding",
	"STD Import Run",
)

PACKAGE_CONTEXT_FIELDS: tuple[str, ...] = (
	"package_id",
	"family_code",
	"version_code",
)

OBJECT_IDENTITY_FIELDS: tuple[str, ...] = (
	"object_key",
	"title",
	"content_hash",
	"metadata_json",
)

STD_VERSION_REQUIRED_FIELDS: tuple[str, ...] = (
	"package_id",
	"family_code",
	"version_code",
	"lifecycle_state",
	"activation_allowed",
	"ui_mode",
	"is_immutable",
	"package_sha256",
	"manifest_hash",
	"package_quality",
	"validation_status",
)

STD_IMPORT_RUN_REQUIRED_FIELDS: tuple[str, ...] = (
	"import_run_key",
	"package_id",
	"run_mode",
	"target_state",
	"status",
	"package_sha256",
	"manifest_hash",
	"source_document_hash",
	"report_json",
)

STD_VALIDATION_FINDING_REQUIRED_FIELDS: tuple[str, ...] = (
	"finding_key",
	"package_id",
	"validation_run",
	"severity",
	"finding_code",
	"object_type",
	"object_id",
	"description",
	"status",
	"lifecycle_gate",
)

CHILD_TABLE_DOCTYPES: frozenset[str] = frozenset({"STD Form Field"})

def lifecycle_select_options() -> str:
	return "\n".join(LIFECYCLE_STATES)


def ui_mode_select_options() -> str:
	return UI_MODE_READ_ONLY_INSPECTION
