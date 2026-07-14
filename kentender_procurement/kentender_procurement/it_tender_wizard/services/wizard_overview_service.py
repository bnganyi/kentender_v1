# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Configuration overview summary for ITW-02 STD Configuration Overview screen."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.services.wizard_instance_service import (
	_get_instance,
	_reference_triplet,
	_validation_status_label,
	serialize_summary,
)
from kentender_procurement.it_tender_wizard.services.wizard_progress_service import generate_steps_for_instance

SYSTEM_STEP_CODES = frozenset(
	{
		"VALIDATION_REPORT",
		"REVIEW_AND_APPROVAL",
		"RENDER_PREVIEW",
		"PUBLICATION_READINESS",
	}
)

_STEP_STATUS_PRIORITY = {
	"COMPLETE": 4,
	"IN_PROGRESS": 3,
	"INCOMPLETE": 2,
	"NOT_AVAILABLE": 1,
}


def _pick_preferred_step_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
	return max(
		rows,
		key=lambda row: (
			_STEP_STATUS_PRIORITY.get((row.get("status") or "INCOMPLETE").strip(), 0),
			row.get("modified") or row.get("creation") or "",
		),
	)


def _dedupe_wizard_step_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	grouped: dict[str, list[dict[str, Any]]] = {}
	for row in rows:
		code = (row.get("step_code") or "").strip()
		if not code:
			continue
		grouped.setdefault(code, []).append(row)
	deduped: list[dict[str, Any]] = []
	for step_code in sorted(grouped, key=lambda code: grouped[code][0].get("step_order") or 0):
		deduped.append(_pick_preferred_step_row(grouped[step_code]))
	return deduped

OVERVIEW_STEP_CODES = tuple(
	step_code
	for step_code, _order, _title in ws.DEFAULT_WIZARD_STEPS
	if step_code not in {"TENDER_IDENTITY", "STD_CONFIG_OVERVIEW"}
)

CONFIGURABLE_OVERVIEW_STEP_CODES = tuple(
	step_code for step_code in OVERVIEW_STEP_CODES if step_code not in SYSTEM_STEP_CODES
)

STEP_OWNER_ROLE_LABELS = {
	"TENDER_PROFILE": "Procurement Officer",
	"TDS": "Procurement Officer",
	"IT_REQUIREMENTS": "Technical Owner",
	"IMPLEMENTATION_SCHEDULE": "Technical Owner",
	"SYSTEM_INVENTORY": "Technical Owner",
	"PRICE_SCHEDULE": "Procurement Officer",
	"EVALUATION_SETUP": "Procurement Officer",
	"FORMS_AND_EVIDENCE": "Procurement Officer",
	"SCC": "Procurement Officer",
	"VALIDATION_REPORT": "System Auto-Run",
	"REVIEW_AND_APPROVAL": "System Workflow",
	"RENDER_PREVIEW": "System Auto-Run",
	"PUBLICATION_READINESS": "System Auto-Run",
}


def _latest_snapshot(instance_name: str) -> dict[str, Any]:
	row = frappe.db.get_value(
		"Wizard Progress Snapshot",
		{"tender_std_instance": instance_name},
		[
			"blocking_findings_count",
			"warning_findings_count",
			"snapshot_at",
		],
		as_dict=True,
		order_by="creation desc",
	)
	return row or {
		"blocking_findings_count": 0,
		"warning_findings_count": 0,
		"snapshot_at": None,
	}


def list_wizard_steps(instance_name: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Wizard Step Instance",
		filters={"tender_std_instance": instance_name},
		fields=["name", "step_code", "step_order", "step_title", "status", "modified", "creation"],
		order_by="step_order asc, creation asc",
	)
	if not rows:
		generate_steps_for_instance(instance_name)
		rows = frappe.get_all(
			"Wizard Step Instance",
			filters={"tender_std_instance": instance_name},
			fields=["name", "step_code", "step_order", "step_title", "status", "modified", "creation"],
			order_by="step_order asc, creation asc",
		)
	return _dedupe_wizard_step_rows(rows)


def map_step_rail_status(
	step: dict[str, Any],
	*,
	all_prior_configurable_complete: bool,
	is_current: bool,
	blockers: int = 0,
	warnings: int = 0,
) -> str:
	step_code = (step.get("step_code") or "").strip()
	raw_status = (step.get("status") or "INCOMPLETE").strip()

	if step_code in SYSTEM_STEP_CODES and not all_prior_configurable_complete:
		return "LOCKED"
	if raw_status == "NOT_AVAILABLE":
		return "LOCKED"
	if blockers:
		return "HAS_BLOCKERS"
	if warnings and raw_status == "COMPLETE":
		return "HAS_WARNINGS"
	if raw_status == "COMPLETE":
		return "COMPLETE"
	if raw_status == "IN_PROGRESS" or is_current:
		return "IN_PROGRESS"
	return "NOT_STARTED"


def _action_label(rail_status: str, is_current: bool) -> str:
	if rail_status == "LOCKED":
		return "Locked"
	if rail_status == "HAS_BLOCKERS":
		return "Fix Issues"
	if rail_status in {"COMPLETE", "HAS_WARNINGS"}:
		return "Review"
	if rail_status == "IN_PROGRESS" or is_current:
		return "Continue"
	return "Start"


def _all_prior_configurable_complete(steps: list[dict[str, Any]], step_code: str) -> bool:
	prior_codes = []
	for row in steps:
		if row["step_code"] == step_code:
			break
		if row["step_code"] not in SYSTEM_STEP_CODES:
			prior_codes.append(row["step_code"])
	if not prior_codes:
		return True
	complete_codes = {
		row["step_code"]
		for row in steps
		if row["status"] == "COMPLETE" and row["step_code"] not in SYSTEM_STEP_CODES
	}
	return all(code in complete_codes for code in prior_codes)


def _derive_overview_completion_percent(wizard_steps: list[dict[str, Any]]) -> int:
	configurable_steps = [
		row for row in wizard_steps if row.get("step_code") in CONFIGURABLE_OVERVIEW_STEP_CODES
	]
	total = len(configurable_steps) or 1
	completed = sum(
		1
		for row in configurable_steps
		if row.get("rail_status") in {"COMPLETE", "HAS_WARNINGS"}
	)
	return int(round((completed / total) * 100))


def _derive_overview_state_label(
	doc,
	wizard_steps: list[dict[str, Any]],
	*,
	derived_completion_percent: int,
) -> str:
	if any(row.get("rail_status") == "HAS_BLOCKERS" for row in wizard_steps):
		return ws.state_label(ws.VALIDATION_FAILED)
	if derived_completion_percent < 100:
		return ws.state_label(ws.IN_CONFIGURATION)
	if doc.wizard_state == ws.READY_FOR_REVIEW:
		return ws.state_label(ws.READY_FOR_REVIEW)
	if doc.wizard_state == ws.RETURNED_FOR_CORRECTION:
		return ws.state_label(ws.RETURNED_FOR_CORRECTION)
	if doc.wizard_state == ws.VALIDATION_FAILED:
		return ws.state_label(ws.VALIDATION_FAILED)
	return ws.state_label(doc.wizard_state)


def _serialize_overview_steps(
	doc,
	steps: list[dict[str, Any]],
	snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
	current_code = (doc.current_step_code or "").strip()
	overview_rows = [row for row in steps if row["step_code"] in OVERVIEW_STEP_CODES]
	result = []
	for row in overview_rows:
		is_current = row["step_code"] == current_code
		all_prior_complete = _all_prior_configurable_complete(steps, row["step_code"])
		blockers = 0
		warnings = 0
		if is_current:
			warnings = int(snapshot.get("warning_findings_count") or 0)
			blockers = int(snapshot.get("blocking_findings_count") or 0)
		rail_status = map_step_rail_status(
			row,
			all_prior_configurable_complete=all_prior_complete,
			is_current=is_current,
			blockers=blockers,
			warnings=warnings,
		)
		result.append(
			{
				"step_code": row["step_code"],
				"step_order": row["step_order"],
				"step_title": row["step_title"],
				"rail_status": rail_status,
				"is_current": is_current,
				"blockers": blockers,
				"warnings": warnings,
				"owner_role_label": STEP_OWNER_ROLE_LABELS.get(row["step_code"], "Procurement Officer"),
				"action_label": _action_label(rail_status, is_current),
			}
		)
	return result


def build_configuration_overview(configuration_id: str) -> dict[str, Any]:
	doc = _get_instance(configuration_id)
	snapshot = _latest_snapshot(doc.name)
	blockers = int(snapshot.get("blocking_findings_count") or 0)
	warnings = int(snapshot.get("warning_findings_count") or 0)
	owner_name = frappe.db.get_value("User", doc.owner_user, "full_name") if doc.owner_user else None
	steps = list_wizard_steps(doc.name)
	wizard_steps = _serialize_overview_steps(doc, steps, snapshot)
	derived_completion_percent = _derive_overview_completion_percent(wizard_steps)
	derived_state_label = _derive_overview_state_label(
		doc,
		wizard_steps,
		derived_completion_percent=derived_completion_percent,
	)
	current_step = {
		"code": doc.current_step_code,
		"name": doc.current_step_name,
	}
	next_required = next(
		(
			{"step_code": row["step_code"], "step_title": row["step_title"]}
			for row in wizard_steps
			if row.get("is_current")
		),
		None,
	)
	if not next_required:
		next_required = next(
			(
				{"step_code": row["step_code"], "step_title": row["step_title"]}
				for row in wizard_steps
				if row["rail_status"] in {"IN_PROGRESS", "HAS_BLOCKERS"}
				and row["step_code"] not in SYSTEM_STEP_CODES
			),
			None,
		)
	if not next_required:
		next_required = next(
			(
				{"step_code": row["step_code"], "step_title": row["step_title"]}
				for row in wizard_steps
				if row["rail_status"] == "NOT_STARTED"
				and row["step_code"] not in SYSTEM_STEP_CODES
			),
			current_step if current_step.get("code") else None,
		)
	audit_count = frappe.db.count("Wizard Audit Event", {"tender_std_instance": doc.name})
	last_audit = frappe.db.get_value(
		"Wizard Audit Event",
		{"tender_std_instance": doc.name},
		"event_type",
		order_by="creation desc",
	)
	package_hash = (doc.package_hash or "").strip()
	if package_hash and len(package_hash) > 12:
		package_hash_display = package_hash[:8] + "..."
	else:
		package_hash_display = package_hash or None

	payload = serialize_summary(doc)
	payload.update(
		{
			"state_label": derived_state_label,
			"completion_percent": derived_completion_percent,
			"instance_completion_percent": int(doc.completion_percent or 0),
			"instance_state_label": ws.state_label(doc.wizard_state),
			"planning_package": _reference_triplet(
				doc.procurement_plan_item_id,
				doc.planning_package_code,
				doc.planning_package_name,
			),
			"procuring_entity": _reference_triplet(
				doc.procuring_entity_id,
				doc.procuring_entity_id,
				doc.procuring_entity_name,
			),
			"method": _reference_triplet(
				doc.procurement_method_code,
				doc.procurement_method_code,
				doc.procurement_method_name,
			),
			"validation": {
				"status": _validation_status_label(doc.current_validation_status, blockers, warnings),
				"blockers": blockers,
				"warnings": warnings,
				"last_run_at": str(snapshot.get("snapshot_at")) if snapshot.get("snapshot_at") else None,
			},
			"current_step": current_step,
			"next_required_action": next_required,
			"owner": {
				"id": doc.owner_user,
				"name": owner_name or doc.owner_user,
				"role_label": "Procurement Officer",
			},
			"governance": {
				"package_hash": package_hash_display,
				"package_hash_full": doc.package_hash,
				"audit_event_count": audit_count,
				"last_audit_event_type": last_audit,
				"std_binding_code": doc.std_package_code,
				"review_track": "Technical Review",
			},
			"wizard_steps": wizard_steps,
		}
	)
	return payload
