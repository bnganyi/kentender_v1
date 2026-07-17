# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Validation Report contracts for ITW-12."""

from __future__ import annotations

import json
import re
from typing import Any

import frappe

from kentender_procurement.it_tender_wizard.services.wizard_instance_service import _get_instance
from kentender_procurement.it_tender_wizard.services.wizard_overview_service import build_configuration_overview
from kentender_procurement.it_tender_wizard.services.wizard_permission_service import (
	PERM_CREATE,
	PERM_VIEW,
	assert_permission,
)
from kentender_procurement.it_tender_wizard.services.wizard_state_guard_service import (
	assert_configuration_editable,
)

STEP_CODE = "VALIDATION_REPORT"
VALIDATION_REPORT_STEP_CODE = STEP_CODE
SEVERITIES = {"BLOCKER", "WARNING", "INFO"}
FINDING_STATUSES = {"OPEN", "RESOLVED"}

STABLE_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")
REVIEW_STATUSES = {"DRAFT", "NEEDS_REVIEW", "APPROVED", "RETURNED"}


def _public_reference(reference: Any) -> dict[str, str]:
	if not isinstance(reference, dict):
		return {"code": "", "name": ""}
	return {
		"code": str(reference.get("code") or "").strip(),
		"name": str(reference.get("name") or "").strip(),
	}


def _latest_validation_counts(instance_name: str) -> tuple[int, int]:
	row = frappe.db.get_value(
		"Wizard Progress Snapshot",
		{"tender_std_instance": instance_name},
		["blocking_findings_count", "warning_findings_count"],
		as_dict=True,
		order_by="creation desc",
	)
	if not row:
		return 0, 0
	return int(row.blocking_findings_count or 0), int(row.warning_findings_count or 0)


def _update_step_status(instance_name: str, *, complete: bool) -> None:
	step_name = frappe.db.get_value(
		"Wizard Step Instance",
		{"tender_std_instance": instance_name, "step_code": STEP_CODE},
	)
	if step_name:
		frappe.db.set_value(
			"Wizard Step Instance",
			step_name,
			"status",
			"COMPLETE" if complete else "IN_PROGRESS",
		)


def _dedupe_docs(doctype: str, instance_name: str) -> str | None:
	rows = frappe.get_all(
		doctype,
		filters={"tender_std_instance": instance_name},
		fields=["name", "modified"],
		order_by="modified desc",
	)
	if not rows:
		return None
	keeper = rows[0]["name"]
	for row in rows[1:]:
		frappe.delete_doc(doctype, row["name"], ignore_permissions=True)
	return keeper


def _overview_context(configuration_id: str, instance_name: str, overview: dict[str, Any]) -> dict[str, Any]:
	blockers, warnings = _latest_validation_counts(instance_name)
	tender_number = (
		frappe.db.get_value(
			"Tender STD TDS",
			{"tender_std_instance": instance_name},
			"tender_number",
		)
		or ""
	).strip()
	return {
		"configuration_id": configuration_id,
		"tender_number": tender_number,
		"title": overview.get("title"),
		"state_label": overview.get("state_label"),
		"completion_percent": overview.get("completion_percent"),
		"planning_package": _public_reference(overview.get("planning_package")),
		"procuring_entity": _public_reference(overview.get("procuring_entity")),
		"method": _public_reference(overview.get("method")),
		"validation": {"blockers": blockers, "warnings": warnings},
	}


def _default_seed_findings(*, complete: bool) -> list[dict[str, Any]]:
	if complete:
		return [
			{
				"finding_code": "VAL-INFO-001",
				"severity": "INFO",
				"message": "All prior configurable steps are complete.",
				"owner_step_code": "VALIDATION_REPORT",
				"owner_screen_route": "it-tender-configuration-validation-report",
				"status": "RESOLVED",
				"display_order": 1,
			}
		]
	return []


def _append_finding(doc, raw: dict[str, Any]) -> None:
	doc.append(
		"findings",
		{
			"finding_code": str(raw.get("finding_code") or "").strip().upper(),
			"severity": str(raw.get("severity") or "WARNING").strip(),
			"message": str(raw.get("message") or "").strip(),
			"owner_step_code": str(raw.get("owner_step_code") or "").strip(),
			"owner_screen_route": str(raw.get("owner_screen_route") or "").strip(),
			"status": str(raw.get("status") or "OPEN").strip(),
			"display_order": int(raw.get("display_order") or 0),
		},
	)


def _ensure_validation_report_doc(instance_name: str, *, seed_complete: bool | None = None):
	name = _dedupe_docs("Tender STD Validation Report", instance_name)
	if name:
		return frappe.get_doc("Tender STD Validation Report", name)
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD Validation Report",
			"tender_std_instance": instance_name,
			"report_code": STEP_CODE,
			"report_title": "Validation Report",
			"description": "Validation findings derived from prior wizard steps.",
			"review_status": "APPROVED" if seed_complete else "DRAFT",
			"lock_status": "UNLOCKED",
		}
	)
	for row in _default_seed_findings(complete=bool(seed_complete)):
		_append_finding(doc, row)
	try:
		doc.insert(ignore_permissions=True)
	except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
		frappe.db.rollback()
		name = _dedupe_docs("Tender STD Validation Report", instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD Validation Report", name)
	return doc


def _serialize_finding(row: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	code = str(row.get("finding_code") or "").strip()
	return {
		"finding_id": code,
		"finding_code": code,
		"severity": str(row.get("severity") or "").strip(),
		"message": str(row.get("message") or "").strip(),
		"owner_step_code": str(row.get("owner_step_code") or "").strip(),
		"owner_screen_route": str(row.get("owner_screen_route") or "").strip(),
		"status": str(row.get("status") or "").strip(),
		"display_order": int(row.get("display_order") or 0),
	}


def _derive_findings(instance_name: str) -> list[dict[str, Any]]:
	"""Best-effort findings from incomplete prior steps and inventory/price gaps."""
	findings: list[dict[str, Any]] = []
	order = 1

	def add(code: str, severity: str, message: str, step: str, route: str) -> None:
		nonlocal order
		findings.append(
			{
				"finding_code": code,
				"severity": severity,
				"message": message,
				"owner_step_code": step,
				"owner_screen_route": route,
				"status": "OPEN",
				"display_order": order,
			}
		)
		order += 1

	prior = (
		("SYSTEM_INVENTORY", "it-tender-configuration-system-inventory", "System Inventory"),
		("PRICE_SCHEDULE", "it-tender-configuration-price-schedule", "Price Schedule"),
		("EVALUATION_SETUP", "it-tender-configuration-evaluation-setup", "Evaluation Setup"),
		("FORMS_AND_EVIDENCE", "it-tender-configuration-forms-and-evidence", "Forms and Evidence"),
		("SCC", "it-tender-configuration-scc", "SCC"),
	)
	for step_code, route, label in prior:
		status = frappe.db.get_value(
			"Wizard Step Instance",
			{"tender_std_instance": instance_name, "step_code": step_code},
			"status",
		)
		if status != "COMPLETE":
			add(
				f"VAL-{step_code}-INCOMPLETE",
				"BLOCKER",
				f"{label} is not complete.",
				step_code,
				route,
			)

	# Inventory gaps: items needing review
	inv_name = frappe.db.get_value("Tender STD System Inventory", {"tender_std_instance": instance_name})
	if inv_name:
		pending = frappe.get_all(
			"Tender STD Inventory Item",
			filters={
				"parent": inv_name,
				"parenttype": "Tender STD System Inventory",
				"review_status": ("in", ["DRAFT", "NEEDS_REVIEW", "RETURNED"]),
			},
			fields=["item_code"],
			limit=20,
		)
		for row in pending:
			add(
				f"VAL-INV-{row.item_code}",
				"WARNING",
				f"Inventory item {row.item_code} still needs review.",
				"SYSTEM_INVENTORY",
				"it-tender-configuration-system-inventory",
			)

		# REQUIRED pricing_policy inventory items without a price line
		required = frappe.get_all(
			"Tender STD Inventory Item",
			filters={
				"parent": inv_name,
				"parenttype": "Tender STD System Inventory",
				"pricing_policy": "REQUIRED",
			},
			fields=["item_code"],
		)
		price_name = frappe.db.get_value("Tender STD Price Schedule", {"tender_std_instance": instance_name})
		linked: set[str] = set()
		if price_name:
			linked = {
				str(r.inventory_item_code or "").strip().upper()
				for r in frappe.get_all(
					"Tender STD Price Line",
					filters={"parent": price_name, "parenttype": "Tender STD Price Schedule"},
					fields=["inventory_item_code"],
				)
				if r.inventory_item_code
			}
		for row in required:
			code = str(row.item_code or "").strip().upper()
			if code and code not in linked:
				add(
					f"VAL-PRICE-MISSING-{code}",
					"BLOCKER",
					f"Inventory item {code} has REQUIRED pricing_policy but no price line.",
					"PRICE_SCHEDULE",
					"it-tender-configuration-price-schedule",
				)

	return findings


def _validate_findings(items: list[dict[str, Any]]) -> None:
	codes: set[str] = set()
	for raw in items:
		code = str(raw.get("finding_code") or "").strip().upper()
		if not code or not STABLE_CODE_PATTERN.fullmatch(code):
			frappe.throw("Finding code is required and must use uppercase letters, numbers, hyphens, or underscores.")
		if code in codes:
			frappe.throw(f"Duplicate finding code: {code}")
		codes.add(code)
		if not str(raw.get("message") or "").strip():
			frappe.throw(f"Finding {code} requires a message.")
		if str(raw.get("severity") or "").strip() not in SEVERITIES:
			frappe.throw(f"Finding {code} has an invalid severity.")
		if str(raw.get("status") or "").strip() not in FINDING_STATUSES:
			frappe.throw(f"Finding {code} has an invalid status.")


def _build_payload(configuration_id: str, doc, overview: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
	open_blockers = sum(1 for f in findings if f["severity"] == "BLOCKER" and f["status"] == "OPEN")
	open_warnings = sum(1 for f in findings if f["severity"] == "WARNING" and f["status"] == "OPEN")
	payload = _overview_context(configuration_id, doc.tender_std_instance, overview)
	payload.update(
		{
			"report_code": str(doc.report_code or "").strip(),
			"report_title": str(doc.report_title or "").strip(),
			"description": str(doc.description or "").strip(),
			"review_status": str(doc.review_status or "").strip(),
			"lock_status": str(doc.lock_status or "").strip(),
			"findings": findings,
			"summary": {
				"open_blockers": open_blockers,
				"open_warnings": open_warnings,
				"total": len(findings),
			},
		}
	)
	return payload


def get_validation_report(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	doc = _ensure_validation_report_doc(instance.name)
	findings = [_serialize_finding(row.as_dict()) for row in doc.findings]
	if not findings:
		findings = [_serialize_finding(row) for row in _derive_findings(instance.name)]
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id), findings)


def save_validation_report(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	assert_configuration_editable(instance.wizard_state)
	doc = _ensure_validation_report_doc(instance.name)
	if str(doc.lock_status or "").strip() != "UNLOCKED":
		frappe.throw(
			f"Validation report is locked with status {doc.lock_status}.",
			title="ITW_VALIDATION_LOCKED",
			exc=frappe.ValidationError,
		)
	items = list(payload.get("findings") or [])
	if not items:
		items = _derive_findings(instance.name)
	_validate_findings(items)
	doc.set("findings", [])
	for row in items:
		_append_finding(doc, row)
	if payload.get("report_title") is not None:
		doc.report_title = str(payload.get("report_title") or "").strip()
	if payload.get("description") is not None:
		doc.description = str(payload.get("description") or "").strip()
	if payload.get("review_status") is not None:
		doc.review_status = str(payload.get("review_status") or "").strip()
	doc.save(ignore_permissions=True)
	findings = [_serialize_finding(row.as_dict()) for row in doc.findings]
	open_blockers = sum(1 for f in findings if f["severity"] == "BLOCKER" and f["status"] == "OPEN")
	complete = open_blockers == 0 and str(doc.review_status) == "APPROVED"
	_update_step_status(instance.name, complete=complete)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id), findings)
