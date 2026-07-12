# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Evaluate whether an STD Version may be activated or bound."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.std_engine.constants import LEGAL_REVIEW_APPROVED


def evaluate_activation_readiness(package_id: str) -> dict[str, Any]:
	"""Return activation readiness derived from live DB state."""
	package_id = (package_id or "").strip()
	if not package_id or not frappe.db.exists("STD Version", package_id):
		frappe.throw(f"STD Version {package_id} not found.", title="STD_VERSION_NOT_FOUND")

	version = frappe.get_doc("STD Version", package_id)
	lifecycle_state = (version.lifecycle_state or "").strip()

	blockers: list[dict[str, str]] = []
	warnings: list[dict[str, str]] = []

	if lifecycle_state == "ACTIVE":
		return _envelope(
			package_id=package_id,
			version=version,
			activation_allowed=True,
			blockers=[],
			warnings=[],
			legal_review_complete=True,
			smoke_pass=True,
			lifecycle_state=lifecycle_state,
		)

	open_activation_blockers = frappe.get_all(
		"STD Validation Finding",
		filters={
			"package_id": package_id,
			"severity": "BLOCKER",
			"status": "OPEN",
			"lifecycle_gate": "ACTIVATION",
		},
		fields=["finding_code", "description", "object_id"],
	)
	for row in open_activation_blockers:
		blockers.append(
			{
				"code": row.get("finding_code") or "",
				"description": row.get("description") or "",
				"objectId": row.get("object_id") or "",
			}
		)

	open_warnings = frappe.get_all(
		"STD Validation Finding",
		filters={
			"package_id": package_id,
			"severity": "WARNING",
			"status": "OPEN",
		},
		fields=["finding_code", "description"],
		limit=20,
	)
	for row in open_warnings:
		warnings.append(
			{
				"code": row.get("finding_code") or "",
				"description": row.get("description") or "",
			}
		)

	legal_review_complete = _legal_review_complete(package_id)
	if not legal_review_complete:
		blockers.append(
			{
				"code": "LEGAL_REVIEW_INCOMPLETE",
				"description": "All verbatim clauses and TDS/SCC parameters must be legal-review approved.",
				"objectId": package_id,
			}
		)

	source_ok = bool(frappe.db.count("STD Source Document", {"package_id": package_id}))
	if not source_ok:
		blockers.append(
			{
				"code": "SOURCE_DOCUMENT_MISSING",
				"description": "Official source PDF must be registered on the STD Version.",
				"objectId": package_id,
			}
		)

	clause_count = frappe.db.count("STD Clause", {"package_id": package_id})
	param_count = frappe.db.count("STD Parameter", {"package_id": package_id})
	smoke_pass = clause_count >= 94 and param_count >= 155 and source_ok
	if not smoke_pass:
		blockers.append(
			{
				"code": "SMOKE_BASELINE_INCOMPLETE",
				"description": f"Expected >=94 clauses and >=155 parameters; found {clause_count}/{param_count}.",
				"objectId": package_id,
			}
		)

	activation_allowed = not blockers
	return _envelope(
		package_id=package_id,
		version=version,
		activation_allowed=activation_allowed,
		blockers=blockers,
		warnings=warnings,
		legal_review_complete=legal_review_complete,
		smoke_pass=smoke_pass,
		lifecycle_state=lifecycle_state,
	)


def sync_activation_flags(package_id: str) -> dict[str, Any]:
	"""Recompute activation_allowed and ui_mode from readiness (unless ACTIVE)."""
	readiness = evaluate_activation_readiness(package_id)
	if readiness.get("lifecycleState") == "ACTIVE":
		return readiness

	activation_allowed = 1 if readiness.get("activationAllowed") else 0
	ui_mode = "READ_ONLY_INSPECTION"
	if activation_allowed:
		ui_mode = "ACTIVE_TEMPLATE"

	frappe.db.set_value(
		"STD Version",
		package_id,
		{
			"activation_allowed": activation_allowed,
			"ui_mode": ui_mode,
		},
		update_modified=False,
	)
	readiness["activationAllowedFlag"] = bool(activation_allowed)
	readiness["uiMode"] = ui_mode
	return readiness


def _legal_review_complete(package_id: str) -> bool:
	pending_clauses = frappe.db.count(
		"STD Clause",
		{"package_id": package_id, "validation_status": ["!=", LEGAL_REVIEW_APPROVED]},
	)
	if pending_clauses:
		return False

	tds_scc_pending = frappe.db.sql(
		"""
		SELECT COUNT(*) FROM `tabSTD Parameter`
		WHERE package_id = %s
		  AND validation_status != %s
		  AND (
			parameter_key LIKE %s
			OR parameter_key LIKE %s
			OR metadata_json LIKE %s
			OR metadata_json LIKE %s
		  )
		""",
		(
			package_id,
			LEGAL_REVIEW_APPROVED,
			"%.parameter.tds.%",
			"%.parameter.scc.%",
			"%TDS-%",
			"%SCC-%",
		),
	)[0][0]
	return int(tds_scc_pending or 0) == 0


def _envelope(
	*,
	package_id: str,
	version,
	activation_allowed: bool,
	blockers: list[dict[str, str]],
	warnings: list[dict[str, str]],
	legal_review_complete: bool,
	smoke_pass: bool,
	lifecycle_state: str,
) -> dict[str, Any]:
	metadata = {}
	if version.metadata_json:
		try:
			metadata = json.loads(version.metadata_json)
		except json.JSONDecodeError:
			metadata = {}
	return {
		"packageId": package_id,
		"versionCode": version.version_code,
		"familyCode": version.family_code,
		"lifecycleState": lifecycle_state,
		"activationAllowed": activation_allowed,
		"activationAllowedFlag": bool(int(version.activation_allowed or 0)),
		"uiMode": version.ui_mode,
		"legalReviewComplete": legal_review_complete,
		"smokePass": smoke_pass,
		"blockers": blockers,
		"warnings": warnings,
		"versionHash": metadata.get("version_hash") or version.package_sha256,
	}
