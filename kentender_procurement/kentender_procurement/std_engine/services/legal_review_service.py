# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Legal reviewer verification actions for verbatim STD packages."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.audit.event_service import record_audit_event
from kentender_procurement.std_engine.validation.validation_engine import ValidationEngine

LEGAL_REVIEWER_ROLE = "ROLE_LEGAL_REVIEWER"
APPROVED_STATUS = "LEGAL_REVIEW_APPROVED"


def _ensure_legal_reviewer() -> None:
	roles = set(frappe.get_roles(frappe.session.user))
	if LEGAL_REVIEWER_ROLE not in roles and "System Manager" not in roles:
		frappe.throw(_("Legal reviewer role required."), frappe.PermissionError)


def _write_audit_event(package_id: str, *, action: str, details: dict[str, Any]) -> None:
	record_audit_event(
		package_id=package_id,
		event_type=action,
		object_type="STD Package",
		object_id=package_id,
		payload=details,
	)


def approve_verbatim_objects(
	package_id: str,
	*,
	clause_keys: list[str] | None = None,
	parameter_keys: list[str] | None = None,
) -> dict[str, Any]:
	_ensure_legal_reviewer()
	package_id = (package_id or "").strip()
	if not package_id:
		raise ValueError("package_id is required")

	approved_clauses = 0
	approved_parameters = 0

	if clause_keys:
		for clause_key in clause_keys:
			if not frappe.db.exists("STD Clause", clause_key):
				continue
			doc = frappe.get_doc("STD Clause", clause_key)
			if doc.package_id != package_id:
				continue
			doc.validation_status = APPROVED_STATUS
			metadata = _parse_metadata(doc.metadata_json)
			metadata["verification_status"] = APPROVED_STATUS
			doc.metadata_json = json.dumps(metadata, sort_keys=True, default=str)
			doc.save(ignore_permissions=True)
			approved_clauses += 1

	if parameter_keys:
		for parameter_key in parameter_keys:
			if not frappe.db.exists("STD Parameter", parameter_key):
				continue
			doc = frappe.get_doc("STD Parameter", parameter_key)
			if doc.package_id != package_id:
				continue
			doc.validation_status = APPROVED_STATUS
			metadata = _parse_metadata(doc.metadata_json)
			metadata["verification_status"] = APPROVED_STATUS
			doc.metadata_json = json.dumps(metadata, sort_keys=True, default=str)
			doc.save(ignore_permissions=True)
			approved_parameters += 1

	_write_audit_event(
		package_id,
		action="LEGAL_REVIEW_APPROVAL",
		details={
			"approvedClauses": approved_clauses,
			"approvedParameters": approved_parameters,
		},
	)
	for finding in frappe.get_all(
		"STD Validation Finding",
		filters={"package_id": package_id, "finding_code": "LEGAL_REVIEW_PENDING", "status": "OPEN"},
		pluck="name",
	):
		frappe.db.set_value("STD Validation Finding", finding, "status", "RESOLVED", update_modified=False)
	result = ValidationEngine().run_for_package(package_id)
	return {
		"package_id": package_id,
		"approved_clauses": approved_clauses,
		"approved_parameters": approved_parameters,
		"validation_summary": result.summary,
	}


def approve_all_pending(package_id: str) -> dict[str, Any]:
	_ensure_legal_reviewer()
	clause_keys = frappe.get_all(
		"STD Clause",
		filters={"package_id": package_id, "validation_status": ["!=", APPROVED_STATUS]},
		pluck="name",
	)
	parameter_keys = frappe.get_all(
		"STD Parameter",
		filters={"package_id": package_id, "validation_status": ["!=", APPROVED_STATUS]},
		pluck="name",
	)
	return approve_verbatim_objects(
		package_id,
		clause_keys=clause_keys,
		parameter_keys=parameter_keys,
	)


def _parse_metadata(raw: str | None) -> dict[str, Any]:
	if not raw:
		return {}
	try:
		parsed = json.loads(raw)
	except json.JSONDecodeError:
		return {}
	return parsed if isinstance(parsed, dict) else {}
