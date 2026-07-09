# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Governance read-model queries — validation, audit, bindings, import runs, version diff."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.std_engine.services.envelope import (
	build_error_envelope,
	build_package_context,
	build_read_envelope,
)
from kentender_procurement.std_engine.services.import_run_service import get_import_run_payload
from kentender_procurement.std_engine.services.read_service import _load_version, _parse_metadata
from kentender_procurement.std_engine.services.usage_kpi_service import build_usage_kpi_summary
from kentender_procurement.std_engine.validation.validation_engine import get_validation_summary

VERSION_DIFF_STUB_REASON = "SINGLE_VERSION_ONLY"


def get_std_version_validation_report(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	run_key = f"VAL-{package_id}"
	run_row = None
	if frappe.db.exists("STD Validation Run", run_key):
		run_row = frappe.get_doc("STD Validation Run", run_key).as_dict()

	findings = frappe.get_all(
		"STD Validation Finding",
		filters={"package_id": package_id},
		fields=[
			"finding_key",
			"finding_code",
			"severity",
			"object_type",
			"object_id",
			"description",
			"suggested_fix",
			"lifecycle_gate",
			"status",
		],
		order_by="severity asc, finding_code asc",
	)

	summary = get_validation_summary(package_id)
	return build_read_envelope(
		data={
			"validationRun": _map_validation_run(run_row, summary),
			"findings": [_map_finding(row) for row in findings],
			"count": len(findings),
			"summary": summary,
		},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def get_std_version_audit_log(
	package_id: str,
	*,
	limit: int = 100,
	offset: int = 0,
) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	limit = max(1, min(int(limit or 100), 500))
	offset = max(0, int(offset or 0))
	total = frappe.db.count("STD Audit Event", {"package_id": package_id})
	rows = frappe.get_all(
		"STD Audit Event",
		filters={"package_id": package_id},
		fields=[
			"event_key",
			"event_type",
			"object_type",
			"object_id",
			"actor",
			"occurred_at",
			"payload_json",
		],
		order_by="occurred_at desc, event_key asc",
		limit=limit,
		start=offset,
	)

	return build_read_envelope(
		data={
			"events": [_map_audit_event(row) for row in rows],
			"count": len(rows),
		},
		package_context=build_package_context(version),
		package_id=package_id,
		pagination={"total": total, "limit": limit, "offset": offset},
	)


def get_std_version_usage_bindings(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	rows = frappe.get_all(
		"STD Usage Binding",
		filters={"package_id": package_id},
		fields=[
			"binding_key",
			"fixture_source",
			"tender_ref",
			"binding_status",
			"metadata_json",
		],
		order_by="binding_key asc",
	)
	return build_read_envelope(
		data={
			"bindings": [_map_usage_binding(row) for row in rows],
			"count": len(rows),
			"usageKpis": build_usage_kpi_summary(version),
		},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def get_std_version_import_runs(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	rows = frappe.get_all(
		"STD Import Run",
		filters={"package_id": package_id},
		fields=[
			"import_run_key",
			"run_mode",
			"status",
			"target_state",
			"package_sha256",
			"modified",
		],
		order_by="modified desc",
	)
	return build_read_envelope(
		data={
			"importRuns": [_map_import_run_summary(row) for row in rows],
			"count": len(rows),
		},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def get_std_import_run(import_run_key: str) -> dict[str, Any]:
	key = (import_run_key or "").strip()
	if not key:
		return build_error_envelope("STD_IMPORT_RUN_NOT_FOUND", "import_run_key is required")

	payload = get_import_run_payload(key)
	if not payload:
		return build_error_envelope("STD_IMPORT_RUN_NOT_FOUND", f"Import run not found: {key}")

	package_id = payload.get("package_id")
	version = _load_version(package_id) if package_id else None
	package_context = build_package_context(version) if version else None
	return build_read_envelope(
		data={"importRun": payload},
		package_context=package_context,
		package_id=package_id,
	)


def get_std_version_diff(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	other_versions = frappe.get_all(
		"STD Version",
		filters={"family_code": version.family_code, "package_id": ["!=", package_id]},
		fields=["package_id", "version_code", "lifecycle_state"],
		order_by="modified desc",
	)
	compare_available = len(other_versions) > 0
	return build_read_envelope(
		data={
			"compareAvailable": compare_available,
			"reason": None if compare_available else VERSION_DIFF_STUB_REASON,
			"message": (
				"Select a second version to compare."
				if compare_available
				else "Version comparison requires a second imported package."
			),
			"currentVersion": {
				"packageId": version.package_id,
				"versionCode": version.version_code,
				"lifecycleState": version.lifecycle_state,
			},
			"comparisonVersions": [
				{
					"packageId": row.package_id,
					"versionCode": row.version_code,
					"lifecycleState": row.lifecycle_state,
				}
				for row in other_versions
			],
		},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def _require_version(package_id: str) -> tuple[Any, dict[str, Any] | None]:
	code = (package_id or "").strip()
	version = _load_version(code)
	if not version:
		return None, build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {code}")
	return version, None


def _map_validation_run(run_row: dict[str, Any] | None, summary: dict[str, int]) -> dict[str, Any] | None:
	if not run_row:
		return None
	run_summary = summary
	if run_row.get("summary_json"):
		try:
			parsed = json.loads(run_row["summary_json"])
			if isinstance(parsed, dict):
				run_summary = {
					"blockers": int(parsed.get("blockers") or 0),
					"warnings": int(parsed.get("warnings") or 0),
					"info": int(parsed.get("info") or 0),
				}
		except json.JSONDecodeError:
			pass
	return {
		"runKey": run_row.get("run_key"),
		"runType": run_row.get("run_type"),
		"status": run_row.get("status"),
		"startedAt": str(run_row.get("started_at") or ""),
		"completedAt": str(run_row.get("completed_at") or ""),
		"summary": run_summary,
	}


def _map_finding(row: frappe._dict) -> dict[str, Any]:
	return {
		"id": row.get("finding_key"),
		"code": row.get("finding_code"),
		"name": row.get("description"),
		"severity": row.get("severity"),
		"objectType": row.get("object_type"),
		"objectId": row.get("object_id"),
		"description": row.get("description"),
		"suggestedFix": row.get("suggested_fix"),
		"lifecycleGate": row.get("lifecycle_gate"),
		"status": row.get("status"),
	}


def _map_audit_event(row: frappe._dict) -> dict[str, Any]:
	return {
		"id": row.get("event_key"),
		"code": row.get("event_type"),
		"name": row.get("object_id"),
		"eventType": row.get("event_type"),
		"objectType": row.get("object_type"),
		"objectId": row.get("object_id"),
		"actor": row.get("actor"),
		"occurredAt": str(row.get("occurred_at") or ""),
		"payload": _parse_metadata(row.get("payload_json")),
	}


def _map_usage_binding(row: frappe._dict) -> dict[str, Any]:
	metadata = _parse_metadata(row.get("metadata_json"))
	display_title = metadata.get("displayTitle") or row.get("tender_ref") or row.get("binding_key")
	category = metadata.get("category") or row.get("tender_ref") or row.get("binding_key")
	return {
		"id": row.get("binding_key"),
		"code": category,
		"name": display_title,
		"fixtureSource": row.get("fixture_source"),
		"tenderRef": row.get("tender_ref"),
		"bindingStatus": row.get("binding_status"),
		"metadata": metadata,
	}


def _map_import_run_summary(row: frappe._dict) -> dict[str, Any]:
	return {
		"id": row.get("import_run_key"),
		"code": row.get("run_mode"),
		"name": row.get("status"),
		"runMode": row.get("run_mode"),
		"status": row.get("status"),
		"targetState": row.get("target_state"),
		"packageSha256": row.get("package_sha256"),
		"modifiedAt": str(row.get("modified") or ""),
	}
