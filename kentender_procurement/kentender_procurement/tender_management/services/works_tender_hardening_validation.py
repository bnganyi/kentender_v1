# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 5 §16.2 / §17 / §18 — works tender-stage validation (WH-010).

Returns structured envelopes, persists aggregate status + JSON, and writes
``hardening_findings`` child rows when ``findings`` is non-empty.
"""

from __future__ import annotations

import json
import traceback
from typing import Any, Callable

import frappe
from frappe.model.document import Document

from kentender_procurement.tender_management.services.works_tender_hardening_validation_checks import (
	validate_audit_checks,
	validate_derived_model_readiness_checks,
	validate_legacy_lockout_checks,
	validate_lot_boq_linkage_checks,
	validate_required_forms_hardening_checks,
	validate_section_attachments_checks,
	validate_works_boq_checks,
	validate_works_requirements_checks,
)

# Doc 5 §15 / §17 — align with ``works_tender_hardening`` (avoid import cycle).
HARDENING_STATUS_NOT_CHECKED = "Not Checked"
HARDENING_STATUS_PASS = "Pass"
HARDENING_STATUS_WARNING = "Warning"
HARDENING_STATUS_BLOCKED = "Blocked"
HARDENING_STATUS_FAILED = "Failed"
HARDENING_STATUS_DEFERRED = "Deferred"

SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"
SEVERITY_MEDIUM = "Medium"
SEVERITY_LOW = "Low"
SEVERITY_INFO = "Info"

BOUNDARY_CODE_DEFAULT = "XMV-BND-002"


def _empty_area_result() -> dict[str, Any]:
	return {"ok": True, "findings": [], "status": HARDENING_STATUS_PASS, "service_failed": False}


def _status_from_findings(findings: list[dict[str, Any]]) -> str:
	if not findings:
		return HARDENING_STATUS_PASS
	if any(f.get("severity") == SEVERITY_CRITICAL for f in findings):
		return HARDENING_STATUS_BLOCKED
	if any(f.get("severity") != SEVERITY_INFO for f in findings):
		return HARDENING_STATUS_WARNING
	return HARDENING_STATUS_PASS


def validate_works_requirements(tender_doc: Document) -> dict[str, Any]:
	fs = validate_works_requirements_checks(tender_doc)
	return {"ok": True, "findings": fs, "status": _status_from_findings(fs), "service_failed": False}


def validate_section_attachments(tender_doc: Document) -> dict[str, Any]:
	fs = validate_section_attachments_checks(tender_doc)
	return {"ok": True, "findings": fs, "status": _status_from_findings(fs), "service_failed": False}


def validate_works_boq(tender_doc: Document) -> dict[str, Any]:
	fs = validate_works_boq_checks(tender_doc)
	return {"ok": True, "findings": fs, "status": _status_from_findings(fs), "service_failed": False}


def validate_lot_boq_linkage(tender_doc: Document) -> dict[str, Any]:
	fs = validate_lot_boq_linkage_checks(tender_doc)
	return {"ok": True, "findings": fs, "status": _status_from_findings(fs), "service_failed": False}


def validate_required_forms_hardening(tender_doc: Document) -> dict[str, Any]:
	fs = validate_required_forms_hardening_checks(tender_doc)
	return {"ok": True, "findings": fs, "status": _status_from_findings(fs), "service_failed": False}


def validate_derived_model_readiness(tender_doc: Document) -> dict[str, Any]:
	fs = validate_derived_model_readiness_checks(tender_doc)
	return {"ok": True, "findings": fs, "status": _status_from_findings(fs), "service_failed": False}


def validate_audit(tender_doc: Document) -> dict[str, Any]:
	fs = validate_audit_checks(tender_doc)
	return {"ok": True, "findings": fs, "status": _status_from_findings(fs), "service_failed": False}


def validate_legacy_lockout(tender_doc: Document) -> dict[str, Any]:
	fs, legacy_checked = validate_legacy_lockout_checks(tender_doc)
	return {
		"ok": True,
		"findings": fs,
		"status": _status_from_findings(fs),
		"service_failed": False,
		"legacy_lockout_checked": legacy_checked,
	}


def _aggregate_status(findings: list[dict[str, Any]], *, service_failed: bool) -> str:
	if service_failed:
		return HARDENING_STATUS_FAILED
	if not findings:
		return HARDENING_STATUS_PASS
	has_crit = any(f.get("severity") == SEVERITY_CRITICAL for f in findings)
	if has_crit:
		return HARDENING_STATUS_BLOCKED
	non_info = [f for f in findings if f.get("severity") != SEVERITY_INFO]
	if non_info:
		return HARDENING_STATUS_WARNING
	return HARDENING_STATUS_PASS


def _count_by_severity(findings: list[dict[str, Any]]) -> dict[str, int]:
	out = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
	for f in findings:
		s = f.get("severity") or ""
		if s == SEVERITY_CRITICAL:
			out["critical"] += 1
		elif s == SEVERITY_HIGH:
			out["high"] += 1
		elif s == SEVERITY_MEDIUM:
			out["medium"] += 1
		elif s == SEVERITY_LOW:
			out["low"] += 1
		elif s == SEVERITY_INFO:
			out["info"] += 1
	return out


def _persist_hardening_findings(tender_doc: Document, findings: list[dict[str, Any]]) -> None:
	tender_doc.set("hardening_findings", [])
	for f in findings:
		tender_doc.append(
			"hardening_findings",
			{
				"finding_code": f.get("finding_code") or "UNKNOWN",
				"severity": f.get("severity") or SEVERITY_INFO,
				"area": f.get("area") or "Works Requirements",
				"message": f.get("message") or "",
				"source_object": f.get("source_object") or "",
				"resolution_hint": f.get("resolution_hint") or "",
				"blocks_transition": 1 if f.get("blocks_transition") else 0,
				"blocking_for": f.get("blocking_for") or "",
			},
		)


def _service_finding(area_key: str, exc: BaseException) -> dict[str, Any]:
	return {
		"finding_code": "WORKS-SVC-001",
		"severity": SEVERITY_HIGH,
		"area": "Audit",
		"message": f"Validation sub-step {area_key} raised a service exception: {exc!s}.",
		"source_object": area_key,
		"resolution_hint": "See Error Log / server traceback for full stack.",
		"blocks_transition": False,
		"blocking_for": "",
		"_service_exception": True,
	}


def _run_area(
	tender_doc: Document, area_key: str, fn: Callable[[Document], dict[str, Any]]
) -> dict[str, Any]:
	try:
		return fn(tender_doc)
	except Exception as exc:
		frappe.log_error(title=f"works_tender_hardening_validation:{area_key}", message=traceback.format_exc())
		fsvc = _service_finding(area_key, exc)
		return {
			"ok": False,
			"findings": [fsvc],
			"status": HARDENING_STATUS_FAILED,
			"service_failed": True,
		}


def _findings_for_envelope(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for f in findings:
		d = dict(f)
		d.pop("_service_exception", None)
		if "blocks_transition" in d:
			d["blocks_transition"] = bool(d.get("blocks_transition"))
		out.append(d)
	return out


def validate_works_tender_stage(tender_name: str) -> dict[str, Any]:
	"""Run §18 validators, persist summary fields + JSON, return §17-shaped envelope."""
	if not tender_name:
		frappe.throw(frappe._("tender_name is required."), frappe.ValidationError)
	tender_doc = frappe.get_doc("Procurement Tender", tender_name)
	tender_doc.check_permission("write")

	areas: tuple[tuple[str, Callable[[Document], dict[str, Any]]], ...] = (
		("works_requirements", validate_works_requirements),
		("section_attachments", validate_section_attachments),
		("works_boq", validate_works_boq),
		("lot_boq_linkage", validate_lot_boq_linkage),
		("required_forms", validate_required_forms_hardening),
		("derived_models", validate_derived_model_readiness),
		("audit", validate_audit),
		("legacy_lockout", validate_legacy_lockout),
	)
	all_findings: list[dict[str, Any]] = []
	summary: dict[str, Any] = {}
	service_failed = False
	legacy_lockout_checked = False

	for key, fn in areas:
		part = _run_area(tender_doc, key, fn)
		if part.get("service_failed"):
			service_failed = True
		fs = part.get("findings") or []
		all_findings.extend(fs)
		summary[f"{key}_status"] = part.get("status") or HARDENING_STATUS_PASS
		if key == "legacy_lockout":
			legacy_lockout_checked = bool(part.get("legacy_lockout_checked"))

	overall = _aggregate_status(all_findings, service_failed=service_failed)
	counts = _count_by_severity(all_findings)

	if all_findings:
		_persist_hardening_findings(tender_doc, all_findings)
	else:
		tender_doc.set("hardening_findings", [])

	tender_doc.works_hardening_status = overall
	tender_doc.works_requirements_status = summary.get(
		"works_requirements_status", HARDENING_STATUS_PASS
	)
	tender_doc.attachments_status = summary.get(
		"section_attachments_status", HARDENING_STATUS_PASS
	)
	tender_doc.boq_hardening_status = summary.get("works_boq_status", HARDENING_STATUS_PASS)
	tender_doc.derived_models_status = summary.get(
		"derived_models_status", HARDENING_STATUS_PASS
	)

	envelope_summary: dict[str, Any] = {
		"works_requirements_status": tender_doc.works_requirements_status,
		"attachments_status": tender_doc.attachments_status,
		"boq_hardening_status": tender_doc.boq_hardening_status,
		"derived_models_status": tender_doc.derived_models_status,
		"forms_status": summary.get("required_forms_status", HARDENING_STATUS_PASS),
		"lot_linkage_status": summary.get("lot_boq_linkage_status", HARDENING_STATUS_PASS),
		"audit_status": summary.get("audit_status", HARDENING_STATUS_PASS),
		"legacy_lockout_checked": legacy_lockout_checked,
		"snapshot_hash": getattr(tender_doc, "works_hardening_snapshot_hash", None) or "",
	}

	envelope = {
		"ok": overall not in (HARDENING_STATUS_FAILED, HARDENING_STATUS_BLOCKED),
		"tender": tender_doc.name,
		"boundary_code": BOUNDARY_CODE_DEFAULT,
		"status": overall,
		"critical_count": counts["critical"],
		"high_count": counts["high"],
		"medium_count": counts["medium"],
		"low_count": counts["low"],
		"info_count": counts["info"],
		"findings": _findings_for_envelope(all_findings),
		"summary": envelope_summary,
	}
	tender_doc.works_hardening_validation_json = json.dumps(
		envelope, indent=2, sort_keys=True, default=str
	)
	tender_doc.save()

	return envelope
