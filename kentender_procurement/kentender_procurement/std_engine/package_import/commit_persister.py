# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Transactional persistence for STD package commit imports."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frappe

from kentender_procurement.std_engine.audit.event_service import record_audit_event
from kentender_procurement.std_engine.package_import.import_planner import load_optional_payloads
from kentender_procurement.std_engine.package_import.usage_binding_seeder import (
	seed_usage_bindings_from_smoke_tests,
)
from kentender_procurement.std_engine.package_import.record_mapper import (
	map_clause_record,
	map_evaluation_record,
	map_family_record,
	map_form_record,
	map_parameter_record,
	map_price_schedule_record,
	map_render_block_record,
	map_requirement_record,
	map_rule_record,
	map_section_record,
	map_source_anchor_record,
	map_source_document_record,
	map_version_record,
	package_context_from_inspection,
	importable_source_documents,
)


@dataclass
class CommitStats:
	records_committed: dict[str, int] = field(default_factory=dict)
	import_run_key: str = ""


def persist_package_commit(
	*,
	inspection: PackageInspectionResult,
	zip_path: str | Path,
	pdf_path: str | Path,
	package_sha256: str,
	manifest_hash: str,
	source_document_hash: str,
	dry_report: dict[str, Any],
) -> CommitStats:
	ctx = package_context_from_inspection(inspection)
	optional_payloads = load_optional_payloads(zip_path, inspection.package_root, inspection.files_listed)
	stats = CommitStats()

	_insert_family(inspection.parsed_payloads["family"]["records"][0], stats)
	_insert_version(
		inspection.parsed_payloads["version"]["records"][0],
		ctx,
		inspection=inspection,
		package_sha256=package_sha256,
		manifest_hash=manifest_hash,
		stats=stats,
	)
	_insert_source_documents(
		importable_source_documents(inspection.parsed_payloads.get("source_document")),
		ctx,
		pdf_path=Path(pdf_path),
		source_hash=source_document_hash,
		stats=stats,
	)
	_insert_records(
		"anchors",
		(inspection.parsed_payloads.get("source_anchors") or {}).get("records") or [],
		lambda record: map_source_anchor_record(record, ctx),
		"STD Source Anchor",
		"anchor_key",
		stats,
	)
	_insert_records(
		"sections",
		(inspection.parsed_payloads.get("sections") or {}).get("records") or [],
		lambda record: map_section_record(record, ctx),
		"STD Section",
		"section_key",
		stats,
	)
	_insert_records(
		"clauses",
		(inspection.parsed_payloads.get("clauses") or {}).get("records") or [],
		lambda record: map_clause_record(record, ctx),
		"STD Clause",
		"clause_key",
		stats,
	)
	_insert_records(
		"parameters",
		(optional_payloads.get("parameters") or {}).get("records") or [],
		lambda record: map_parameter_record(record, ctx),
		"STD Parameter",
		"parameter_key",
		stats,
	)
	_insert_records(
		"rules",
		(optional_payloads.get("rules") or {}).get("records") or [],
		lambda record: map_rule_record(record, ctx),
		"STD Rule",
		"rule_key",
		stats,
	)
	_insert_forms(optional_payloads, ctx, stats)
	_insert_records(
		"requirements",
		(optional_payloads.get("requirements") or {}).get("records") or [],
		lambda record: map_requirement_record(record, ctx),
		"STD Requirement Schema",
		"requirement_schema_key",
		stats,
	)
	_insert_records(
		"priceSchedules",
		(optional_payloads.get("price_schedules") or {}).get("records") or [],
		lambda record: map_price_schedule_record(record, ctx),
		"STD Price Schedule Schema",
		"price_schedule_schema_key",
		stats,
	)
	_insert_records(
		"evaluationSchemas",
		(optional_payloads.get("evaluation_schemas") or {}).get("records") or [],
		lambda record: map_evaluation_record(record, ctx),
		"STD Evaluation Schema",
		"evaluation_schema_key",
		stats,
	)
	_insert_records(
		"renderBlocks",
		(optional_payloads.get("render_blocks") or {}).get("records") or [],
		lambda record: map_render_block_record(record, ctx),
		"STD Render Block",
		"render_block_key",
		stats,
	)
	seed_usage_bindings_from_smoke_tests(
		ctx,
		optional_payloads.get("tender_binding_smoke_tests"),
		stats.records_committed,
	)

	validation_run_key = _persist_validation(inspection, ctx.package_id, dry_report, stats)
	_record_commit_audit_events(ctx.package_id, package_sha256, validation_run_key, stats)
	stats.import_run_key = _persist_import_run(
		ctx.package_id,
		dry_report=dry_report,
		stats=stats,
		commit_status="COMMITTED",
	)
	return stats


def _insert_family(record: dict[str, Any], stats: CommitStats) -> None:
	family_code = record["family_code"]
	if frappe.db.exists("STD Family", family_code):
		stats.records_committed["families"] = 0
		return
	frappe.get_doc(map_family_record(record)).insert(ignore_permissions=True)
	stats.records_committed["families"] = 1


def _insert_version(
	record: dict[str, Any],
	ctx,
	*,
	inspection: PackageInspectionResult,
	package_sha256: str,
	manifest_hash: str,
	stats: CommitStats,
) -> None:
	if frappe.db.exists("STD Version", ctx.package_id):
		stats.records_committed["versions"] = 0
		return
	frappe.get_doc(
		map_version_record(
			record,
			ctx,
			package_sha256=package_sha256,
			manifest_hash=manifest_hash,
			inspection=inspection,
		)
	).insert(ignore_permissions=True)
	stats.records_committed["versions"] = 1


def _insert_source_documents(
	records: list[dict[str, Any]],
	ctx,
	*,
	pdf_path: Path,
	source_hash: str,
	stats: CommitStats,
) -> None:
	committed = 0
	for record in records:
		key = record["source_document_key"]
		if frappe.db.exists("STD Source Document", key):
			continue
		frappe.get_doc(
			map_source_document_record(record, ctx, pdf_path=pdf_path, source_hash=source_hash)
		).insert(ignore_permissions=True)
		record_audit_event(
			package_id=ctx.package_id,
			event_type="SOURCE_DOCUMENT_REGISTERED",
			object_type="STD Source Document",
			object_id=key,
			payload={"filename": pdf_path.name, "source_hash": source_hash},
		)
		committed += 1
	stats.records_committed["sourceDocuments"] = committed


def _insert_records(
	count_key: str,
	records: list[dict[str, Any]],
	mapper,
	doctype: str,
	name_field: str,
	stats: CommitStats,
) -> None:
	committed = 0
	for record in records:
		doc_dict = mapper(record)
		name = doc_dict[name_field]
		if frappe.db.exists(doctype, name):
			continue
		frappe.get_doc(doc_dict).insert(ignore_permissions=True)
		committed += 1
	stats.records_committed[count_key] = committed


def _insert_forms(optional_payloads: dict[str, Any], ctx, stats: CommitStats) -> None:
	forms = (optional_payloads.get("forms") or {}).get("records") or []
	fields = (optional_payloads.get("form_fields") or {}).get("records") or []
	fields_by_form: dict[str, list[dict[str, Any]]] = defaultdict(list)
	for field in fields:
		fields_by_form[field["form_key"]].append(field)

	committed_forms = 0
	committed_fields = 0
	for form in forms:
		form_key = form["form_key"]
		if frappe.db.exists("STD Form Schema", form_key):
			continue
		form_fields = fields_by_form.get(form_key, [])
		frappe.get_doc(map_form_record(form, ctx, form_fields=form_fields)).insert(ignore_permissions=True)
		committed_forms += 1
		committed_fields += len(form_fields)
	stats.records_committed["forms"] = committed_forms
	stats.records_committed["formFields"] = committed_fields


def _persist_validation(
	inspection: PackageInspectionResult,
	package_id: str,
	dry_report: dict[str, Any],
	stats: CommitStats,
) -> str:
	from kentender_procurement.std_engine.validation.validation_engine import ValidationEngine

	result = ValidationEngine().run_for_package(
		package_id,
		dry_report=dry_report,
		inspection=inspection,
		run_type="IMPORT_POST_COMMIT",
		db_checks_enabled=True,
	)
	return result.run_key


def _record_commit_audit_events(
	package_id: str,
	package_sha256: str,
	validation_run_key: str,
	stats: CommitStats,
) -> None:
	record_audit_event(
		package_id=package_id,
		event_type="PACKAGE_IMPORT_COMMITTED",
		object_type="STD Version",
		object_id=package_id,
		payload={
			"package_sha256": package_sha256,
			"records_committed": stats.records_committed,
			"validation_run_key": validation_run_key,
		},
		event_key=f"{package_id}.PACKAGE_IMPORT_COMMITTED.{package_sha256[:8].upper()}",
	)


def _persist_import_run(
	package_id: str,
	*,
	dry_report: dict[str, Any],
	stats: CommitStats,
	commit_status: str,
) -> str:
	hash_suffix = dry_report["package_sha256"][:8].upper()
	unique_suffix = frappe.generate_hash(length=10)
	import_run_key = f"COMMIT-{package_id}-{hash_suffix}-{unique_suffix}"
	report = dict(dry_report)
	report.update(
		{
			"commit_status": commit_status,
			"records_committed": stats.records_committed,
			"run_mode": "COMMIT",
		}
	)
	frappe.get_doc(
		{
			"doctype": "STD Import Run",
			"import_run_key": import_run_key,
			"package_id": package_id,
			"run_mode": "COMMIT",
			"target_state": dry_report.get("target_state"),
			"status": commit_status,
			"package_sha256": dry_report.get("package_sha256"),
			"manifest_hash": dry_report.get("manifest_hash"),
			"source_document_hash": dry_report.get("source_document_hash"),
			"report_json": json.dumps(report, sort_keys=True, default=str),
		}
	).insert(ignore_permissions=True)
	return import_run_key
