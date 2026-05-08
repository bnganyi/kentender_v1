# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD template governance — package validation + findings persistence (doc 7 §13.2, §14.3, §15, STD-GOV-006).

Wraps ``run_package_validation`` (Admin Step 4 / ``std_package_validation``) and maps checks to
governance findings, ``STD Template.validation_findings`` child rows, and ``latest_validation_*``
fields. Emits ``EVT_VALIDATION_STARTED`` / ``EVT_VALIDATION_COMPLETED`` (single ``save``).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_procurement.tender_management.services.std_package_validation import (
	run_package_validation,
)
from kentender_procurement.tender_management.services.std_template_governance import (
	EVT_VALIDATION_COMPLETED,
	EVT_VALIDATION_STARTED,
	STATUS_VALIDATED,
	STATUS_VALIDATION_FAILED,
	VALIDATION_BLOCKED,
	VALIDATION_FAILED,
	VALIDATION_PASS,
	VALIDATION_PASS_WARNINGS,
)
from kentender_procurement.tender_management.services.std_template_governance_events import (
	write_std_template_lifecycle_event,
)


def _new_validation_run_id() -> str:
	return f"STD-VAL-{frappe.generate_hash(length=12)}"


def _assert_can_run_std_template_validation() -> None:
	"""Doc 7 §14.3 / doc 3 matrix — site Administrator, System Manager, STD Template Administrator."""
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if frappe.session.user == "Administrator":
		return
	roles = frappe.get_roles()
	if "System Manager" in roles:
		return
	if "STD Template Administrator" in roles:
		return
	frappe.throw(_("Not permitted"), frappe.PermissionError)


class _PackagePayloadDocView:
	"""Minimal ``STD Template``-shaped view for ``run_package_validation`` without a DB row."""

	__slots__ = ("name", "template_code", "template_name", "package_json", "package_hash")

	def __init__(self, payload: dict[str, Any]) -> None:
		manifest = payload.get("manifest") if isinstance(payload.get("manifest"), dict) else {}
		self.template_code = str(manifest.get("template_code") or "")
		self.name = self.template_code or "STD-VALIDATION-STUB"
		self.template_name = str(manifest.get("template_name") or "")
		self.package_hash = str(payload.get("package_hash") or "")
		self.package_json = json.dumps(payload, ensure_ascii=False)


def clear_std_template_validation_findings(doc: Any) -> None:
	"""Remove all rows from ``validation_findings`` on the in-memory document (caller saves)."""
	rows = list(doc.get("validation_findings") or [])
	for row in rows:
		doc.remove(row)


def write_std_template_validation_findings(doc: Any, run_id: str, findings: list[dict[str, Any]]) -> None:
	"""Append governance validation finding rows (caller saves)."""
	for raw in findings:
		row = {
			"run_id": run_id,
			"finding_code": str(raw.get("finding_code") or "UNKNOWN"),
			"severity": str(raw.get("severity") or "Info"),
			"area": str(raw.get("area") or "PACKAGE")[:140],
			"message": str(raw.get("message") or "")[:140],
			"source_path": (str(raw["source_path"])[:140] if raw.get("source_path") else None),
			"resolution_hint": (
				str(raw["resolution_hint"])[:140] if raw.get("resolution_hint") else None
			),
			"blocks_approval": 1 if raw.get("blocks_approval") else 0,
			"blocks_activation": 1 if raw.get("blocks_activation") else 0,
			"payload_json": raw.get("payload_json"),
		}
		doc.append("validation_findings", row)


def _check_to_persisted_finding(check: dict[str, Any]) -> dict[str, Any] | None:
	"""Map one engine ``checks[]`` row to a governance finding dict, or ``None`` to skip."""
	st = check.get("status")
	if st in ("PASSED", "SKIPPED"):
		return None

	if st in ("BLOCKED", "FAILED"):
		severity = "Critical"
	elif st == "WARNING":
		severity = "Warning"
	else:
		severity = "Info"

	blocks = 1 if severity == "Critical" else 0
	details = check.get("details") if isinstance(check.get("details"), dict) else {}
	payload_json: str | None
	try:
		payload_json = json.dumps(details, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
	except TypeError:
		payload_json = None

	return {
		"finding_code": str(check.get("check_code") or "UNKNOWN"),
		"severity": severity,
		"area": str(check.get("category") or "PACKAGE_STRUCTURE")[:140],
		"message": str(check.get("message") or check.get("label") or "")[:140],
		"source_path": str(check.get("reference") or "")[:140] or None,
		"resolution_hint": None,
		"blocks_approval": blocks,
		"blocks_activation": blocks,
		"payload_json": payload_json,
	}


def _findings_from_engine_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for check in checks:
		row = _check_to_persisted_finding(check)
		if row:
			out.append(row)
	return out


def _governance_validation_status(
	engine_ok: bool, overall: str, findings: list[dict[str, Any]]
) -> str:
	critical = sum(1 for f in findings if f.get("severity") == "Critical")
	if critical or overall in ("FAILED", "BLOCKED") or not engine_ok:
		if overall == "BLOCKED" and not critical:
			return VALIDATION_BLOCKED
		return VALIDATION_FAILED
	if overall == "PASSED_WITH_WARNINGS" or any(f.get("severity") == "Warning" for f in findings):
		return VALIDATION_PASS_WARNINGS
	return VALIDATION_PASS


def _public_findings_snapshot(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
	return [
		{
			"finding_code": f.get("finding_code"),
			"severity": f.get("severity"),
			"area": f.get("area"),
			"message": f.get("message"),
			"blocks_approval": bool(f.get("blocks_approval")),
			"blocks_activation": bool(f.get("blocks_activation")),
		}
		for f in findings
	]


def validate_std_template_package_payload(package_payload: Any) -> dict[str, Any]:
	"""Validate a package dict (or JSON string) and return doc 7 §15 envelope (no DB writes).

	Uses ``run_package_validation`` with a lightweight doc view so existing Admin Step 4 checks
	reuse without requiring an ``STD Template`` database row.
	"""
	run_id = _new_validation_run_id()
	package_hash = ""

	if isinstance(package_payload, (bytes, bytearray)):
		package_payload = bytes(package_payload).decode("utf-8")

	if isinstance(package_payload, str):
		try:
			package_payload = json.loads(package_payload)
		except json.JSONDecodeError as exc:
			return _synthetic_payload_error(run_id, package_hash, str(exc))

	if not isinstance(package_payload, dict):
		return _synthetic_payload_error(run_id, package_hash, "package_payload must be a JSON object")

	if not package_payload:
		return _synthetic_payload_error(run_id, package_hash, "package payload is empty")

	package_hash = str(package_payload.get("package_hash") or "")
	stub = _PackagePayloadDocView(package_payload)
	engine = run_package_validation(stub, package_payload)
	findings = _findings_from_engine_checks(engine.get("checks") or [])
	status = _governance_validation_status(
		bool(engine.get("ok")), str(engine.get("overall_status") or ""), findings
	)
	critical_count = sum(1 for f in findings if f.get("severity") == "Critical")
	warning_count = sum(1 for f in findings if f.get("severity") == "Warning")
	info_count = sum(1 for f in findings if f.get("severity") == "Info")
	ok = status in (VALIDATION_PASS, VALIDATION_PASS_WARNINGS)

	return {
		"ok": ok,
		"run_id": run_id,
		"status": status,
		"critical_count": critical_count,
		"warning_count": warning_count,
		"info_count": info_count,
		"findings": _public_findings_snapshot(findings),
		"package_hash": str(engine.get("package_hash") or package_hash),
	}


def _synthetic_payload_error(run_id: str, package_hash: str, message: str) -> dict[str, Any]:
	findings = [
		{
			"finding_code": "STD-PKG-012",
			"severity": "Critical",
			"area": "PACKAGE_STRUCTURE",
			"message": message[:140],
			"blocks_approval": True,
			"blocks_activation": True,
		}
	]
	return {
		"ok": False,
		"run_id": run_id,
		"status": VALIDATION_FAILED,
		"critical_count": 1,
		"warning_count": 0,
		"info_count": 0,
		"findings": findings,
		"package_hash": package_hash,
	}


def run_std_template_validation(std_template: str) -> dict[str, Any]:
	"""Run governance validation for ``std_template`` (doc 7 §14.3): events, findings, fields, save.

	Returns the §15 envelope plus ``std_template`` and final ``lifecycle_status``.
	"""
	_assert_can_run_std_template_validation()
	doc = frappe.get_doc("STD Template", std_template)
	run_id = _new_validation_run_id()
	from_status = doc.get("lifecycle_status") or ""

	try:
		package = json.loads(doc.package_json or "{}")
	except json.JSONDecodeError as exc:
		package = None
		parse_error = str(exc)
	else:
		parse_error = ""

	if not isinstance(package, dict):
		msg = (parse_error or "package_json is not a JSON object")[:140]
		findings_rows = [
			{
				"finding_code": "STD-PKG-012",
				"severity": "Critical",
				"area": "PACKAGE_STRUCTURE",
				"message": msg,
				"source_path": "STD Template.package_json",
				"resolution_hint": None,
				"blocks_approval": 1,
				"blocks_activation": 1,
				"payload_json": None,
			}
		]
		gov = {
			"ok": False,
			"run_id": run_id,
			"status": VALIDATION_FAILED,
			"critical_count": 1,
			"warning_count": 0,
			"info_count": 0,
			"findings": _public_findings_snapshot(findings_rows),
			"package_hash": str(doc.get("package_hash") or ""),
		}
	else:
		engine = run_package_validation(doc, package)
		findings_rows = _findings_from_engine_checks(engine.get("checks") or [])
		status = _governance_validation_status(
			bool(engine.get("ok")), str(engine.get("overall_status") or ""), findings_rows
		)
		critical_count = sum(1 for f in findings_rows if f.get("severity") == "Critical")
		warning_count = sum(1 for f in findings_rows if f.get("severity") == "Warning")
		info_count = sum(1 for f in findings_rows if f.get("severity") == "Info")
		ok = status in (VALIDATION_PASS, VALIDATION_PASS_WARNINGS)
		gov = {
			"ok": ok,
			"run_id": run_id,
			"status": status,
			"critical_count": critical_count,
			"warning_count": warning_count,
			"info_count": info_count,
			"findings": _public_findings_snapshot(findings_rows),
			"package_hash": str(engine.get("package_hash") or doc.get("package_hash") or ""),
		}

	new_lifecycle = STATUS_VALIDATED if gov["ok"] else STATUS_VALIDATION_FAILED

	write_std_template_lifecycle_event(
		doc,
		EVT_VALIDATION_STARTED,
		"validation",
		{"validation_run_id": run_id, "run_id": run_id},
		from_status=from_status,
		save=False,
	)

	clear_std_template_validation_findings(doc)
	write_std_template_validation_findings(doc, run_id, findings_rows)

	doc.latest_validation_run_id = run_id
	doc.latest_validation_at = now_datetime()
	doc.latest_validation_by = frappe.session.user
	doc.latest_validation_status = gov["status"]
	doc.latest_validation_package_hash = str(doc.get("package_hash") or gov.get("package_hash") or "")
	doc.latest_validation_result_json = json.dumps(gov, ensure_ascii=False, default=str)
	doc.critical_finding_count = int(gov["critical_count"])
	doc.warning_finding_count = int(gov["warning_count"])
	doc.info_finding_count = int(gov["info_count"])
	doc.validation_is_current = 1
	doc.lifecycle_status = new_lifecycle

	write_std_template_lifecycle_event(
		doc,
		EVT_VALIDATION_COMPLETED,
		"validation",
		{
			"validation_run_id": run_id,
			"run_id": run_id,
			"status": gov["status"],
			"ok": gov["ok"],
		},
		from_status=from_status,
		to_status=new_lifecycle,
		save=False,
	)

	doc.save()

	out = dict(gov)
	out["std_template"] = doc.name
	out["lifecycle_status"] = doc.lifecycle_status
	return out
