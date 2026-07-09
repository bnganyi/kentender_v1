# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Persist and retrieve STD Import Run records for HTTP + screen 20."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.std_engine.constants import COMMIT_TARGET_STATE_M1


def persist_dry_run_report(report: dict[str, Any]) -> str:
	"""Store a dry-run report as ``STD Import Run`` and return its key."""
	package_id = report.get("package_id") or ""
	hash_suffix = (report.get("package_sha256") or "")[:8].upper()
	import_run_key = f"DRY-{package_id}-{hash_suffix}-{frappe.generate_hash(length=10)}"
	status = report.get("import_readiness") or "UNKNOWN"
	stored_report = dict(report)
	stored_report.update({"run_mode": "DRY_RUN", "status": status})

	frappe.get_doc(
		{
			"doctype": "STD Import Run",
			"import_run_key": import_run_key,
			"package_id": package_id if package_id and frappe.db.exists("STD Version", package_id) else None,
			"run_mode": "DRY_RUN",
			"target_state": report.get("target_state") or COMMIT_TARGET_STATE_M1,
			"status": status,
			"package_sha256": report.get("package_sha256"),
			"manifest_hash": report.get("manifest_hash"),
			"source_document_hash": report.get("source_document_hash"),
			"report_json": json.dumps(stored_report, sort_keys=True, default=str),
		}
	).insert(ignore_permissions=True)
	return import_run_key


def get_import_run_payload(import_run_key: str) -> dict[str, Any]:
	"""Load an import run and return the HTTP read-model payload."""
	if not frappe.db.exists("STD Import Run", import_run_key):
		return {}

	doc = frappe.get_doc("STD Import Run", import_run_key)
	report = json.loads(doc.report_json or "{}")
	return {
		"import_run_key": doc.import_run_key,
		"package_id": doc.package_id,
		"run_mode": doc.run_mode,
		"target_state": doc.target_state,
		"status": doc.status,
		"package_sha256": doc.package_sha256,
		"manifest_hash": doc.manifest_hash,
		"source_document_hash": doc.source_document_hash,
		"report": report,
	}
