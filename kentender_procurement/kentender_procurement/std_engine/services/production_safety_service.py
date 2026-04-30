from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.exceptions import ValidationError

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.tender_evaluation_guard_service import (
	check_manual_evaluation_criteria_permission,
)
from kentender_procurement.std_engine.services.tender_opening_guard_service import check_manual_opening_field_permission
from kentender_procurement.std_engine.services.tender_submission_guard_service import (
	check_manual_submission_requirement_permission,
)
from kentender_procurement.std_engine.tests.phase12_smoke_helpers import (
	DOC1_SOURCE_DOCUMENT_CODE,
	doc1_building_seed_loaded,
)


def _is_truthy(value: Any) -> bool:
	return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _check_feature_flag_default_reviewed() -> tuple[bool, str, dict[str, Any]]:
	raw = frappe.conf.get("std_engine_v2_enabled")
	passed = raw is not None
	return (
		passed,
		"std_engine_v2_enabled is explicitly configured." if passed else "std_engine_v2_enabled is not explicitly configured.",
		{"flag_value": raw},
	)


def _check_active_doc1_template_exists() -> tuple[bool, str, dict[str, Any]]:
	row = frappe.db.get_value(
		"STD Template Version",
		{
			"source_document_code": DOC1_SOURCE_DOCUMENT_CODE,
			"version_status": "Active",
			"is_current_active_version": 1,
		},
		["name", "version_code"],
		as_dict=True,
	)
	passed = bool(row and row.get("version_code"))
	return (
		passed,
		"Active DOC1 template version found." if passed else "No active DOC1 template version found.",
		{"version_code": (row or {}).get("version_code")},
	)


def _check_no_legacy_upload_as_source_when_v2() -> tuple[bool, str, dict[str, Any]]:
	if not _is_truthy(frappe.conf.get("std_engine_v2_enabled")):
		return True, "STD v2 flag disabled; legacy upload-as-source check not applicable.", {"rows": []}
	rows = frappe.get_all(
		"STD Tender Binding",
		filters={
			"std_instance_code": ("is", "set"),
			"std_outputs_current": 0,
		},
		fields=["tender_code", "std_instance_code", "std_outputs_current"],
		limit=25,
	)
	passed = len(rows) == 0
	return (
		passed,
		"No legacy upload-as-source signal found for STD-v2 tender bindings."
		if passed
		else "Some STD-v2 tender bindings do not have current generated outputs.",
		{"rows": rows},
	)


def _check_manual_downstream_rules_disabled() -> tuple[bool, str, dict[str, Any]]:
	binding = frappe.db.get_value(
		"STD Tender Binding",
		{"std_instance_code": ("is", "set")},
		["tender_code", "std_instance_code"],
		as_dict=True,
	)
	if not binding or not binding.get("tender_code"):
		return True, "No STD tender binding found; guard checks not applicable.", {"checked_tender_code": None}
	tender_code = str(binding.get("tender_code"))
	sub = check_manual_submission_requirement_permission(tender_code=tender_code, actor="Administrator")
	opn = check_manual_opening_field_permission(tender_code=tender_code, actor="Administrator")
	evalp = check_manual_evaluation_criteria_permission(tender_code=tender_code, actor="Administrator")
	passed = (not sub.get("allowed")) and (not opn.get("allowed")) and (not evalp.get("allowed"))
	return (
		passed,
		"Manual downstream rule creation is blocked for STD-backed tenders."
		if passed
		else "One or more manual downstream guard checks returned allowed=True.",
		{
			"checked_tender_code": tender_code,
			"submission_guard": sub,
			"opening_guard": opn,
			"evaluation_guard": evalp,
		},
	)


def _check_audit_append_only_verified() -> tuple[bool, str, dict[str, Any]]:
	probe_code = f"STD-SAFETY-{frappe.generate_hash(length=8).upper()}"
	resp = record_std_audit_event(
		event_type="SAFETY_CHECK_PROBE",
		object_type="STD_INSTANCE",
		object_code=probe_code,
		actor="Administrator",
		reason="production safety append-only probe",
	)
	doc = frappe.get_doc("STD Audit Event", {"audit_event_code": resp["audit_event_code"]})
	update_blocked = False
	delete_blocked = False
	try:
		doc.reason = "probe-edit"
		doc.save(ignore_permissions=True)
	except ValidationError:
		update_blocked = True
	try:
		frappe.delete_doc("STD Audit Event", doc.name, force=True, ignore_permissions=True)
	except ValidationError:
		delete_blocked = True
	passed = update_blocked and delete_blocked
	return (
		passed,
		"STD audit append-only behavior verified." if passed else "STD audit append-only probe failed.",
		{
			"audit_event_code": resp.get("audit_event_code"),
			"update_blocked": update_blocked,
			"delete_blocked": delete_blocked,
		},
	)


def _check_seed_package_loaded() -> tuple[bool, str, dict[str, Any]]:
	passed = bool(doc1_building_seed_loaded())
	return (
		passed,
		"Canonical DOC1 seed package is loaded." if passed else "Canonical DOC1 seed package is missing.",
		{"source_document_code": DOC1_SOURCE_DOCUMENT_CODE},
	)


def _check_smoke_tests(smoke_tests_passed: bool | None) -> tuple[bool, str, dict[str, Any]]:
	passed = bool(smoke_tests_passed)
	return (
		passed,
		"Smoke tests are marked as passing." if passed else "Smoke tests are not marked as passing for this run.",
		{"smoke_tests_passed": bool(smoke_tests_passed)},
	)


def build_std_production_safety_report(smoke_tests_passed: bool | None = None, actor: str | None = None) -> dict[str, Any]:
	"""STD-CURSOR-1302 production preflight report."""
	actor = actor or frappe.session.user
	check_rows: list[dict[str, Any]] = []

	def add_row(check_key: str, fn):
		passed, message, details = fn()
		check_rows.append({"check_key": check_key, "passed": bool(passed), "message": str(message), "details": details or {}})

	add_row("seed_package_loaded", _check_seed_package_loaded)
	add_row("smoke_tests_pass", lambda: _check_smoke_tests(smoke_tests_passed))
	add_row("feature_flag_default_reviewed", _check_feature_flag_default_reviewed)
	add_row("active_doc1_template_exists", _check_active_doc1_template_exists)
	add_row("no_legacy_upload_as_source_when_v2", _check_no_legacy_upload_as_source_when_v2)
	add_row("manual_downstream_rules_disabled", _check_manual_downstream_rules_disabled)
	add_row("audit_append_only_verified", _check_audit_append_only_verified)

	overall_pass = all(bool(row.get("passed")) for row in check_rows)
	record_std_audit_event(
		event_type="SAFETY_CHECK_RUN",
		object_type="STD_INSTANCE",
		object_code="STD-PRODUCTION-SAFETY",
		actor=actor,
		new_state="PASS" if overall_pass else "FAIL",
		reason=_("STD production safety report generated."),
		metadata={"overall_pass": overall_pass, "checks": check_rows},
	)
	return {"ok": True, "overall_pass": overall_pass, "checks": check_rows}
