# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Build insert/skip/fail plans from package inspection without DB writes."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import frappe

from kentender_procurement.std_engine.constants import COMMIT_TARGET_STATE_M1
from kentender_procurement.std_engine.package_import.package_contract import (
	OPTIONAL_PAYLOAD_PATH_BY_KEY,
	PAYLOAD_PATH_BY_KEY,
	RECORD_COUNT_KEYS,
	SOURCE_DOCUMENT_SKIP_POLICIES,
)
from kentender_procurement.std_engine.package_import.package_reader import PackageInspectionResult


@dataclass
class InsertPlan:
	record_counts: dict[str, int] = field(default_factory=dict)
	records_planned_insert: int = 0
	records_planned_skip: int = 0
	records_planned_fail: int = 0
	entity_actions: dict[str, dict[str, int]] = field(default_factory=dict)
	validation_warnings: list[str] = field(default_factory=list)
	validation_blockers: list[str] = field(default_factory=list)
	target_state: str = COMMIT_TARGET_STATE_M1


def build_insert_plan(
	inspection: PackageInspectionResult,
	*,
	package_sha256: str,
	optional_payloads: dict[str, Any] | None = None,
) -> InsertPlan:
	optional_payloads = optional_payloads or {}
	record_counts = _build_record_counts(inspection, optional_payloads)
	warnings = _collect_anchor_warnings(inspection)
	warnings.extend(_collect_skipped_source_document_warnings(inspection))

	blockers: list[str] = []
	version_conflict = _resolve_version_conflict(inspection.package_id, package_sha256)
	if version_conflict == "HASH_CONFLICT":
		blockers.append(
			f"STD Version {inspection.package_id} already exists with a different package_sha256"
		)

	plan = InsertPlan(
		record_counts=record_counts,
		validation_warnings=warnings,
		validation_blockers=blockers,
	)

	if version_conflict == "IDEMPOTENT_SKIP":
		_add_idempotent_skip_actions(plan)
		return plan

	_add_insert_actions(plan, record_counts, version_conflict == "HASH_CONFLICT")
	return plan


def load_optional_payloads(
	zip_path: str | Path,
	package_root: str,
	files_listed: list[str],
) -> dict[str, Any]:
	payloads: dict[str, Any] = {}
	with zipfile.ZipFile(zip_path, "r") as zf:
		for key, relative_path in OPTIONAL_PAYLOAD_PATH_BY_KEY.items():
			if relative_path not in files_listed:
				continue
			raw = zf.read(package_root + relative_path)
			payloads[key] = json.loads(raw.decode("utf-8"))
	return payloads


def _build_record_counts(
	inspection: PackageInspectionResult,
	optional_payloads: dict[str, Any],
) -> dict[str, int]:
	payloads = inspection.parsed_payloads
	counts = {
		"families": _record_len(payloads.get("family")),
		"versions": _record_len(payloads.get("version")),
		"sourceDocuments": _importable_source_document_count(payloads.get("source_document")),
		"anchors": _record_len(payloads.get("source_anchors")),
		"sections": _record_len(payloads.get("sections")),
		"clauses": _record_len(payloads.get("clauses")),
		"parameters": _record_len(optional_payloads.get("parameters")),
		"rules": _record_len(optional_payloads.get("rules")),
		"forms": _record_len(optional_payloads.get("forms")),
		"formFields": _record_len(optional_payloads.get("form_fields")),
		"requirements": _record_len(optional_payloads.get("requirements")),
		"priceSchedules": _record_len(optional_payloads.get("price_schedules")),
		"evaluationSchemas": _record_len(optional_payloads.get("evaluation_schemas")),
		"renderBlocks": _record_len(optional_payloads.get("render_blocks")),
		"usageBindings": _record_len(optional_payloads.get("tender_binding_smoke_tests")),
	}
	return {key: counts[key] for key in RECORD_COUNT_KEYS}


def _importable_source_document_count(payload: dict[str, Any] | None) -> int:
	if not payload:
		return 0
	records = payload.get("records") or []
	return sum(1 for record in records if not _should_skip_source_document(record))


def _should_skip_source_document(record: dict[str, Any]) -> bool:
	policy = str(record.get("import_policy") or "")
	return policy in SOURCE_DOCUMENT_SKIP_POLICIES


def _collect_skipped_source_document_warnings(inspection: PackageInspectionResult) -> list[str]:
	payload = inspection.parsed_payloads.get("source_document") or {}
	records = payload.get("records") or []
	warnings: list[str] = []
	for record in records:
		if not _should_skip_source_document(record):
			continue
		key = record.get("source_document_key") or record.get("source_document_id") or "unknown"
		policy = record.get("import_policy") or "DO_NOT_IMPORT"
		warnings.append(f"Source document skipped ({policy}): {key}")
	return warnings


def _collect_anchor_warnings(inspection: PackageInspectionResult) -> list[str]:
	clauses = (inspection.parsed_payloads.get("clauses") or {}).get("records") or []
	anchors = (inspection.parsed_payloads.get("source_anchors") or {}).get("records") or []
	anchor_keys = {
		str(record.get("source_anchor_key") or record.get("anchor_key") or "")
		for record in anchors
	}
	warnings: list[str] = []
	for clause in clauses:
		anchor_key = str(clause.get("source_anchor_key") or "")
		if not anchor_key:
			clause_key = clause.get("clause_key") or clause.get("clause_id") or "unknown"
			warnings.append(f"Clause missing source_anchor_key: {clause_key}")
			continue
		if anchor_key not in anchor_keys:
			clause_key = clause.get("clause_key") or clause.get("clause_id") or "unknown"
			warnings.append(f"Clause references missing source anchor ({anchor_key}): {clause_key}")
	return warnings


def _resolve_version_conflict(package_id: str, package_sha256: str) -> str | None:
	if not package_id:
		return None
	if not frappe.db.exists("STD Version", package_id):
		return None
	existing_hash = frappe.db.get_value("STD Version", package_id, "package_sha256") or ""
	if existing_hash == package_sha256:
		return "IDEMPOTENT_SKIP"
	return "HASH_CONFLICT"


def _add_idempotent_skip_actions(plan: InsertPlan) -> None:
	for key, count in plan.record_counts.items():
		plan.entity_actions[key] = {"insert": 0, "skip": count, "fail": 0}
		plan.records_planned_skip += count


def _add_insert_actions(
	plan: InsertPlan,
	record_counts: dict[str, int],
	version_conflict: bool,
) -> None:
	for key, count in record_counts.items():
		if version_conflict and key == "versions":
			plan.entity_actions[key] = {"insert": 0, "skip": 0, "fail": count}
			plan.records_planned_fail += count
			continue
		plan.entity_actions[key] = {"insert": count, "skip": 0, "fail": 0}
		plan.records_planned_insert += count


def _record_len(payload: dict[str, Any] | None) -> int:
	if not payload:
		return 0
	records = payload.get("records")
	return len(records) if isinstance(records, list) else 0
