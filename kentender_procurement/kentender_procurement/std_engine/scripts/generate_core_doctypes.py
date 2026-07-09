#!/usr/bin/env python3
"""One-shot generator for BE-01 STD Engine DocTypes. Run from bench context if needed."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "doctype"
MODULE = "STD Engine"

LIFECYCLE_OPTIONS = "\n".join(
	[
		"DRAFT",
		"STRUCTURING",
		"INTERNAL_REVIEW",
		"LEGAL_REVIEW",
		"PROCUREMENT_REVIEW",
		"APPROVED",
		"ACTIVE",
		"SUPERSEDED",
		"ARCHIVED",
	]
)

PERMS = [
	{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1},
	{"role": "Auditor", "read": 1, "write": 0, "create": 0, "delete": 0, "report": 1},
]


def _data(name, label, **kw):
	return {"fieldname": name, "fieldtype": "Data", "label": label, **kw}


def _link(name, label, options, **kw):
	return {"fieldname": name, "fieldtype": "Link", "label": label, "options": options, **kw}


def _check(name, label, **kw):
	return {"fieldname": name, "fieldtype": "Check", "label": label, **kw}


def _select(name, label, options, **kw):
	return {"fieldname": name, "fieldtype": "Select", "label": label, "options": options, **kw}


def _long(name, label, **kw):
	return {"fieldname": name, "fieldtype": "Long Text", "label": label, **kw}


def _code(name, label, **kw):
	return {"fieldname": name, "fieldtype": "Code", "label": label, "options": "JSON", **kw}


def _dt(name, label, **kw):
	return {"fieldname": name, "fieldtype": "Datetime", "label": label, **kw}


def _int(name, label, **kw):
	return {"fieldname": name, "fieldtype": "Int", "label": label, **kw}


def package_context(*, reqd_package: bool = True):
	return [
		_link("package_id", "Package", "STD Version", reqd=1 if reqd_package else 0, in_list_view=1, search_index=1),
		_link("family_code", "Family Code", "STD Family", reqd=1, search_index=1),
		_data("version_code", "Version Code", reqd=1, search_index=1),
	]


def object_identity():
	return [
		_data("object_key", "Object Key", reqd=1, search_index=1),
		_data("title", "Title", in_list_view=1),
		_data("description", "Description"),
		_data("validation_status", "Validation Status", search_index=1),
		_link("source_anchor", "Source Anchor", "STD Source Anchor"),
		_data("content_hash", "Content Hash"),
		_code("metadata_json", "Metadata JSON"),
	]


def base_doc(name, fields, *, autoname, istable=0, track_changes=1, editable_grid=0):
	return {
		"actions": [],
		"allow_rename": 0,
		"autoname": autoname,
		"creation": "2026-07-09 12:00:00.000000",
		"doctype": "DocType",
		"engine": "InnoDB",
		"field_order": [f["fieldname"] for f in fields],
		"fields": fields,
		"istable": istable,
		"editable_grid": editable_grid,
		"links": [],
		"modified": "2026-07-09 12:00:00.000000",
		"modified_by": "Administrator",
		"module": MODULE,
		"name": name,
		"owner": "Administrator",
		"permissions": [] if istable else PERMS,
		"sort_field": "modified",
		"sort_order": "DESC",
		"states": [],
		"track_changes": track_changes,
	}


SPECS = {
	"std_family": {
		"name": "STD Family",
		"class": "STDFamily",
		"autoname": "field:family_code",
		"fields": [
			_data("family_code", "Family Code", reqd=1, unique=1, in_list_view=1, search_index=1),
			_data("family_name", "Family Name", reqd=1, in_list_view=1),
			_data("authority_code", "Authority Code", reqd=1),
			_data("procurement_category", "Procurement Category", reqd=1),
			_code("metadata_json", "Metadata JSON"),
		],
	},
	"std_version": {
		"name": "STD Version",
		"class": "STDVersion",
		"autoname": "field:package_id",
		"fields": [
			_data("package_id", "Package ID", reqd=1, unique=1, in_list_view=1, search_index=1),
			_link("family_code", "Family Code", "STD Family", reqd=1, in_list_view=1, search_index=1),
			_data("version_code", "Version Code", reqd=1, search_index=1),
			_data("version_label", "Version Label"),
			_select("lifecycle_state", "Lifecycle State", LIFECYCLE_OPTIONS, reqd=1, default="DRAFT", in_list_view=1),
			_check("activation_allowed", "Activation Allowed", default="0"),
			_select("ui_mode", "UI Mode", "READ_ONLY_INSPECTION\nEDITABLE_DRAFT", default="READ_ONLY_INSPECTION", reqd=1),
			_check("is_immutable", "Is Immutable", default="0"),
			_data("package_sha256", "Package SHA-256"),
			_data("manifest_hash", "Manifest Hash"),
			_data("package_quality", "Package Quality"),
			_data("validation_status", "Validation Status", default="OPEN"),
			_data("source_authority", "Source Authority"),
			_code("metadata_json", "Metadata JSON"),
		],
	},
	"std_source_document": {
		"name": "STD Source Document",
		"class": "STDSourceDocument",
		"autoname": "field:source_document_key",
		"fields": [
			*package_context(),
			_data("source_document_key", "Source Document Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			_data("filename", "Filename", reqd=1),
			_data("source_hash", "Source Hash", reqd=1),
			_data("file_path", "File Path"),
			_data("source_role", "Source Role"),
			_int("page_count", "Page Count"),
			_code("metadata_json", "Metadata JSON"),
		],
	},
	"std_source_anchor": {
		"name": "STD Source Anchor",
		"class": "STDSourceAnchor",
		"autoname": "field:anchor_key",
		"fields": [
			*package_context(),
			_data("anchor_key", "Anchor Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			_link("source_document", "Source Document", "STD Source Document", reqd=1),
			_data("section_ref", "Section Ref"),
			_data("clause_ref", "Clause Ref"),
			_int("page_from", "Page From"),
			_int("page_to", "Page To"),
			_data("anchor_hash", "Anchor Hash"),
			_code("metadata_json", "Metadata JSON"),
		],
	},
	"std_section": {
		"name": "STD Section",
		"class": "STDSection",
		"autoname": "field:section_key",
		"fields": [
			*package_context(),
			_data("section_key", "Section Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			*object_identity(),
			_data("section_number", "Section Number"),
			_link("parent_section", "Parent Section", "STD Section"),
		],
	},
	"std_clause": {
		"name": "STD Clause",
		"class": "STDClause",
		"autoname": "field:clause_key",
		"fields": [
			*package_context(),
			_data("clause_key", "Clause Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			_link("section", "Section", "STD Section", reqd=1, search_index=1),
			*object_identity(),
			_long("clause_text", "Clause Text"),
		],
	},
	"std_parameter": {
		"name": "STD Parameter",
		"class": "STDParameter",
		"autoname": "field:parameter_key",
		"fields": [*package_context(), _data("parameter_key", "Parameter Key", reqd=1, unique=1, in_list_view=1, search_index=1), *object_identity()],
	},
	"std_rule": {
		"name": "STD Rule",
		"class": "STDRule",
		"autoname": "field:rule_key",
		"fields": [*package_context(), _data("rule_key", "Rule Key", reqd=1, unique=1, in_list_view=1, search_index=1), *object_identity()],
	},
	"std_form_schema": {
		"name": "STD Form Schema",
		"class": "STDFormSchema",
		"autoname": "field:form_key",
		"fields": [
			*package_context(),
			_data("form_key", "Form Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			*object_identity(),
			{"fieldname": "form_fields", "fieldtype": "Table", "label": "Form Fields", "options": "STD Form Field"},
		],
	},
	"std_form_field": {
		"name": "STD Form Field",
		"class": "STDFormField",
		"autoname": "hash",
		"istable": 1,
		"editable_grid": 1,
		"fields": [
			_data("field_key", "Field Key", reqd=1, in_list_view=1),
			_data("field_label", "Field Label", reqd=1),
			_data("field_type", "Field Type", reqd=1),
			_check("is_required", "Is Required", default="0"),
			_int("display_order", "Display Order"),
			_code("field_schema_json", "Field Schema JSON"),
		],
	},
	"std_requirement_schema": {
		"name": "STD Requirement Schema",
		"class": "STDRequirementSchema",
		"autoname": "field:requirement_schema_key",
		"fields": [
			*package_context(),
			_data("requirement_schema_key", "Requirement Schema Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			*object_identity(),
		],
	},
	"std_price_schedule_schema": {
		"name": "STD Price Schedule Schema",
		"class": "STDPriceScheduleSchema",
		"autoname": "field:price_schedule_schema_key",
		"fields": [
			*package_context(),
			_data("price_schedule_schema_key", "Price Schedule Schema Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			*object_identity(),
		],
	},
	"std_evaluation_schema": {
		"name": "STD Evaluation Schema",
		"class": "STDEvaluationSchema",
		"autoname": "field:evaluation_schema_key",
		"fields": [
			*package_context(),
			_data("evaluation_schema_key", "Evaluation Schema Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			*object_identity(),
		],
	},
	"std_render_block": {
		"name": "STD Render Block",
		"class": "STDRenderBlock",
		"autoname": "field:render_block_key",
		"fields": [
			*package_context(),
			_data("render_block_key", "Render Block Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			*object_identity(),
		],
	},
	"std_validation_run": {
		"name": "STD Validation Run",
		"class": "STDValidationRun",
		"autoname": "field:run_key",
		"fields": [
			_link("package_id", "Package", "STD Version", reqd=1, search_index=1),
			_data("run_key", "Run Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			_data("run_type", "Run Type", reqd=1),
			_data("status", "Status", reqd=1, in_list_view=1),
			_dt("started_at", "Started At"),
			_dt("completed_at", "Completed At"),
			_code("summary_json", "Summary JSON"),
		],
	},
	"std_validation_finding": {
		"name": "STD Validation Finding",
		"class": "STDValidationFinding",
		"autoname": "field:finding_key",
		"fields": [
			_link("package_id", "Package", "STD Version", reqd=1, search_index=1),
			_data("finding_key", "Finding Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			_link("validation_run", "Validation Run", "STD Validation Run", reqd=1),
			_select("severity", "Severity", "BLOCKER\nWARNING\nINFO", reqd=1, in_list_view=1),
			_data("finding_code", "Finding Code", reqd=1),
			_data("object_type", "Object Type", reqd=1),
			_data("object_id", "Object ID", reqd=1),
			_long("description", "Description", reqd=1),
			_long("suggested_fix", "Suggested Fix"),
			_data("lifecycle_gate", "Lifecycle Gate", reqd=1),
			_select("status", "Status", "OPEN\nASSIGNED\nREMEDIATED_IN_DRAFT\nWAIVED_WITH_APPROVAL\nRESOLVED", reqd=1, default="OPEN"),
		],
	},
	"std_audit_event": {
		"name": "STD Audit Event",
		"class": "STDAuditEvent",
		"autoname": "field:event_key",
		"fields": [
			_link("package_id", "Package", "STD Version", search_index=1),
			_data("event_key", "Event Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			_data("event_type", "Event Type", reqd=1, in_list_view=1),
			_data("object_type", "Object Type", reqd=1),
			_data("object_id", "Object ID", reqd=1),
			_link("actor", "Actor", "User"),
			_dt("occurred_at", "Occurred At", reqd=1),
			_code("payload_json", "Payload JSON"),
		],
	},
	"std_usage_binding": {
		"name": "STD Usage Binding",
		"class": "STDUsageBinding",
		"autoname": "field:binding_key",
		"fields": [
			*package_context(),
			_data("binding_key", "Binding Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			_data("fixture_source", "Fixture Source"),
			_data("tender_ref", "Tender Ref"),
			_data("binding_status", "Binding Status"),
			_code("metadata_json", "Metadata JSON"),
		],
	},
	"std_import_run": {
		"name": "STD Import Run",
		"class": "STDImportRun",
		"autoname": "field:import_run_key",
		"fields": [
			_data("import_run_key", "Import Run Key", reqd=1, unique=1, in_list_view=1, search_index=1),
			_link("package_id", "Package", "STD Version", search_index=1),
			_select("run_mode", "Run Mode", "DRY_RUN\nCOMMIT", reqd=1, in_list_view=1),
			_select("target_state", "Target State", LIFECYCLE_OPTIONS, reqd=1, default="DRAFT"),
			_data("status", "Status", reqd=1, in_list_view=1),
			_data("package_sha256", "Package SHA-256"),
			_data("manifest_hash", "Manifest Hash"),
			_data("source_document_hash", "Source Document Hash"),
			_code("report_json", "Report JSON"),
		],
	},
}

CONTROLLER_TEMPLATE = '''# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document

{extra_imports}

class {class_name}(Document):
{body}
'''

VERSION_BODY = '''
\tdef validate(self) -> None:
\t\tfrom kentender_procurement.std_engine.doctype.validators import validate_lifecycle_state

\t\tvalidate_lifecycle_state(self.lifecycle_state)
'''

DEFAULT_BODY = "\n\tpass\n"


def write_doctype(folder: str, spec: dict) -> None:
	path = ROOT / folder
	path.mkdir(parents=True, exist_ok=True)
	doc = base_doc(
		spec["name"],
		spec["fields"],
		autoname=spec["autoname"],
		istable=spec.get("istable", 0),
		editable_grid=spec.get("editable_grid", 0),
	)
	(path / f"{folder}.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
	(path / "__init__.py").write_text("", encoding="utf-8")
	extra = ""
	body = DEFAULT_BODY
	if folder == "std_version":
		body = VERSION_BODY
	py = CONTROLLER_TEMPLATE.format(class_name=spec["class"], extra_imports=extra, body=body)
	(path / f"{folder}.py").write_text(py, encoding="utf-8")


def main() -> None:
	ROOT.mkdir(parents=True, exist_ok=True)
	(ROOT / "__init__.py").write_text("", encoding="utf-8")
	for folder, spec in SPECS.items():
		write_doctype(folder, spec)
	print(f"Generated {len(SPECS)} DocTypes under {ROOT}")


if __name__ == "__main__":
	main()
