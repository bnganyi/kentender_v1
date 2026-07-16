# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender STD instance lifecycle for dashboard."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import frappe

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.services.std_core_adapter import (
	get_active_it_std_version_id,
	resolve_std_version,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.it_tender_wizard.services.wizard_audit_service import record_event
from kentender_procurement.it_tender_wizard.services.wizard_permission_service import (
	PERM_CREATE,
	PERM_DELETE_DRAFT,
	PERM_VIEW,
	assert_permission,
)
from kentender_procurement.it_tender_wizard.services.wizard_progress_service import (
	compute_progress,
	create_progress_snapshot,
	generate_steps_for_instance,
)
from kentender_procurement.it_tender_wizard.services.wizard_state_guard_service import (
	assert_deletable,
	assert_std_version_immutable,
)


def _next_instance_code() -> str:
	last = frappe.db.sql(
		"""
		SELECT instance_code FROM `tabTender STD Instance`
		WHERE instance_code LIKE 'ITCFG-%'
		ORDER BY creation DESC LIMIT 1
		"""
	)
	if not last:
		return "ITCFG-000001"
	try:
		seq = int(str(last[0][0]).split("-")[-1])
	except (TypeError, ValueError, IndexError):
		seq = 0
	return f"ITCFG-{seq + 1:06d}"


def _reference_triplet(
	entity_id: str | None,
	code: str | None,
	name: str | None,
) -> dict[str, str | None]:
	return {"id": entity_id, "code": code, "name": name}


def _validation_status_label(status: str, blockers: int, warnings: int) -> str:
	if blockers:
		return "FAILED"
	if warnings:
		return "HAS_WARNINGS"
	if status in ("PASSED", "PASSED_WITH_WARNINGS"):
		return status
	return status or "NOT_RUN"


def resolve_next_action(state: str, blockers: int) -> tuple[str, str]:
	"""Map wizard state to Screen 01 next-action codes/labels."""
	state = (state or "").strip()
	if state == ws.VALIDATION_FAILED or blockers > 0:
		return "fix_blockers", "Fix Blockers"
	if state == ws.READY_FOR_REVIEW:
		return "submit_for_review", "Submit for Review"
	if state == ws.APPROVED_FOR_TENDER_CREATION:
		return "open_preview", "Open Preview"
	if state in (ws.BOUND_TO_TENDER, ws.PUBLISHED):
		return "open_in_tm", "Open in Tender Management"
	return "continue_setup", "Continue Setup"


def serialize_list_item(doc) -> dict[str, Any]:
	blockers = int(frappe.db.get_value(
		"Wizard Progress Snapshot",
		{"tender_std_instance": doc.name},
		"blocking_findings_count",
		order_by="creation desc",
	) or 0)
	warnings = int(frappe.db.get_value(
		"Wizard Progress Snapshot",
		{"tender_std_instance": doc.name},
		"warning_findings_count",
		order_by="creation desc",
	) or 0)
	owner_name = frappe.db.get_value("User", doc.owner_user, "full_name") if doc.owner_user else None
	overdue = bool(doc.due_at and doc.due_at < date.today() and doc.wizard_state in ws.OVERDUE_ELIGIBLE_STATES)
	next_action, next_action_label = resolve_next_action(doc.wizard_state, blockers)
	last_updated = None
	if doc.modified:
		last_updated = (
			doc.modified.strftime("%Y-%m-%d %H:%M")
			if hasattr(doc.modified, "strftime")
			else str(doc.modified)
		)
	return {
		"id": doc.name,
		"configuration_id": doc.instance_code,
		"code": doc.instance_code,
		"name": doc.instance_title,
		"tender_ref": doc.instance_code,
		"tender_title": doc.instance_title,
		"planning_package_ref": doc.planning_package_code or "",
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
		"procuring_entity_name": doc.procuring_entity_name or "",
		"method": _reference_triplet(
			doc.procurement_method_code,
			doc.procurement_method_code,
			doc.procurement_method_name,
		),
		"procurement_method_label": doc.procurement_method_name or "",
		"state": doc.wizard_state,
		"wizard_state": doc.wizard_state,
		"state_label": ws.state_label(doc.wizard_state),
		"wizard_state_label": ws.state_label(doc.wizard_state),
		"validation": {
			"status": _validation_status_label(doc.current_validation_status, blockers, warnings),
			"blockers": blockers,
			"warnings": warnings,
		},
		"blocker_count": blockers,
		"warning_count": warnings,
		"completion_percent": int(doc.completion_percent or 0),
		"progress_percent": int(doc.completion_percent or 0),
		"current_step": {
			"code": doc.current_step_code,
			"name": doc.current_step_name,
		},
		"owner": {"id": doc.owner_user, "name": owner_name or doc.owner_user},
		"owner_name": owner_name or doc.owner_user or "",
		"last_updated": last_updated,
		"last_updated_at": last_updated,
		"next_action": next_action,
		"next_action_label": next_action_label,
		"overdue": overdue,
	}


def serialize_summary(doc) -> dict[str, Any]:
	return {
		"configuration_id": doc.instance_code,
		"title": doc.instance_title,
		"state": doc.wizard_state,
		"std_template_version_id": doc.std_version,
		"std_template_version_label": doc.std_package_code,
		"procurement_entity_id": doc.procuring_entity_id,
		"procurement_plan_item_id": doc.procurement_plan_item_id,
		"bound_tender_id": doc.bound_tender_id,
		"completion_percent": int(doc.completion_percent or 0),
		"validation_status": doc.current_validation_status,
		"initiation_source": doc.initiation_source,
		"created_at": str(doc.creation),
		"updated_at": str(doc.modified),
	}


# Synthetic tender shells for dashboard create when Procurement Tender rows are absent.
_DASHBOARD_SHELL_FIXTURES: tuple[dict[str, str], ...] = (
	{
		"id": "SHELL-ITW-SERVER-001",
		"code": "SHELL-ITW-SERVER-001",
		"name": "Server Procurement",
		"planning_package_ref": "PP-ICT-SHELL-010",
		"procuring_entity_id": "PE-NATIONAL-TREASURY",
		"procuring_entity_name": "National Treasury",
		"procurement_method_code": "OPEN_NATIONAL",
		"procurement_method_label": "Open Tender",
	},
	{
		"id": "SHELL-ITW-CLOUD-001",
		"code": "SHELL-ITW-CLOUD-001",
		"name": "Cloud Migration",
		"planning_package_ref": "PP-ICT-SHELL-090",
		"procuring_entity_id": "PE-MIN-ICT",
		"procuring_entity_name": "Ministry of ICT",
		"procurement_method_code": "RFP",
		"procurement_method_label": "RFP",
	},
)


def list_eligible_tender_shells() -> list[dict[str, Any]]:
	"""Return tender shells eligible for Start Configuration (Screen 01 create modal)."""
	assert_permission(PERM_VIEW)
	shells: list[dict[str, Any]] = []
	if frappe.db.exists("DocType", "Procurement Tender"):
		try:
			rows = frappe.get_all(
				"Procurement Tender",
				fields=["name"],
				order_by="modified desc",
				limit_page_length=50,
			)
			for row in rows:
				code = (row.name or "").strip()
				if not code:
					continue
				shells.append(
					{
						"id": row.name,
						"code": code,
						"name": code,
						"planning_package_ref": "",
						"procuring_entity_id": "",
						"procuring_entity_name": "",
						"procurement_method_code": "",
						"procurement_method_label": "",
					}
				)
		except Exception:
			shells = []
	if not shells:
		shells = [dict(item) for item in _DASHBOARD_SHELL_FIXTURES]
	return shells


def get_create_configuration_context(
	*,
	tender_id: str | None = None,
	std_version_id: str | None = None,
	plan_item_id: str | None = None,
) -> dict[str, Any]:
	"""Payload for Screen 01 create modal: shells + active STD package."""
	assert_permission(PERM_VIEW)
	active_id = (std_version_id or "").strip() or get_active_it_std_version_id() or CANONICAL_PACKAGE_ID
	std_meta: dict[str, Any] = {}
	try:
		std_meta = resolve_std_version(active_id)
	except Exception:
		std_meta = {
			"package_id": active_id,
			"version_label": active_id,
			"version_code": active_id,
		}
	shells = list_eligible_tender_shells()
	preselect = (tender_id or "").strip()
	return {
		"shells": shells,
		"active_std_package": {
			"id": std_meta.get("package_id") or active_id,
			"code": std_meta.get("version_code") or active_id,
			"name": std_meta.get("version_label") or std_meta.get("package_id") or active_id,
		},
		"preselect_tender_id": preselect,
		"plan_item_id": (plan_item_id or "").strip(),
	}


def create_configuration(payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	std_template_version_id = (payload.get("std_template_version_id") or "").strip()
	if not std_template_version_id:
		frappe.throw("std_template_version_id is required.")

	std_meta = resolve_std_version(std_template_version_id)
	title = (payload.get("title") or "New IT Tender Configuration").strip()
	initiation_source = (payload.get("initiation_source") or ws.INITIATION_DASHBOARD).strip()
	if payload.get("tender_id") or payload.get("procurement_plan_item_id"):
		initiation_source = ws.INITIATION_PLANNING

	instance_code = _next_instance_code()
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD Instance",
			"instance_code": instance_code,
			"instance_title": title,
			"wizard_state": ws.DRAFT,
			"std_version": std_meta["package_id"],
			"std_package_code": std_meta["version_code"] or std_meta["package_id"],
			"package_hash": std_meta.get("package_hash"),
			"procuring_entity_id": payload.get("procuring_entity_id"),
			"procuring_entity_name": payload.get("procuring_entity_name"),
			"procurement_plan_item_id": payload.get("procurement_plan_item_id"),
			"planning_package_code": payload.get("planning_package_code"),
			"planning_package_name": payload.get("planning_package_name"),
			"procurement_method_code": payload.get("procurement_method_code"),
			"procurement_method_name": payload.get("procurement_method_name"),
			"bound_tender_id": payload.get("tender_id"),
			"initiation_source": initiation_source,
			"current_validation_status": "NOT_RUN",
			"owner_user": frappe.session.user,
			"metadata_json": json.dumps(
				{
					"create_payload": {
						k: payload.get(k)
						for k in (
							"tender_id",
							"procurement_plan_item_id",
							"procuring_entity_id",
						)
					}
				},
				sort_keys=True,
			),
		}
	)
	doc.insert(ignore_permissions=True)
	generate_steps_for_instance(doc.name)
	progress = compute_progress(doc.name)
	doc.completion_percent = progress["completion_percent"]
	doc.current_step_code = progress["current_step_code"]
	doc.current_step_name = progress["current_step_name"]
	doc.save(ignore_permissions=True)
	create_progress_snapshot(doc.name, wizard_state=doc.wizard_state)
	audit_id = record_event(
		"wizard_instance_created",
		tender_std_instance=doc.name,
		object_id=doc.instance_code,
		metadata={"initiation_source": initiation_source},
	)
	return {
		"summary": serialize_summary(doc),
		"audit_event_id": audit_id,
		"section_statuses": [
			{"section_key": "tender_identity", "status": "INCOMPLETE"},
			{"section_key": "tds", "status": "INCOMPLETE"},
			{"section_key": "requirements", "status": "INCOMPLETE"},
		],
	}


def get_configuration_summary(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	from kentender_procurement.it_tender_wizard.services.wizard_overview_service import (
		build_configuration_overview,
	)

	return build_configuration_overview(configuration_id)


def list_configurations(
	*,
	state: str | None = None,
	states: str | None = None,
	procurement_entity_id: str | None = None,
	procurement_method_code: str | None = None,
	overdue_only: bool | int | None = None,
	q: str | None = None,
	page: int = 1,
	page_size: int = 25,
) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	filters: dict[str, Any] = {}
	if state and not states:
		filters["wizard_state"] = state
	if procurement_entity_id:
		filters["procuring_entity_id"] = procurement_entity_id
	if procurement_method_code:
		filters["procurement_method_code"] = procurement_method_code

	rows = frappe.get_all(
		"Tender STD Instance",
		filters=filters,
		fields=["name"],
		order_by="modified desc",
	)
	if states:
		state_list = [item.strip() for item in states.split(",") if item.strip()]
		if state_list:
			rows = [
				row
				for row in rows
				if frappe.db.get_value("Tender STD Instance", row.name, "wizard_state") in state_list
			]
	if overdue_only:
		rows = [row for row in rows if _is_overdue_instance(row.name)]
	if q:
		q_lower = q.strip().lower()
		rows = [
			row
			for row in rows
			if _matches_query(row.name, q_lower)
		]

	total = len(rows)
	page = max(1, int(page or 1))
	page_size = max(1, min(100, int(page_size or 25)))
	start = (page - 1) * page_size
	page_rows = rows[start : start + page_size]
	items = [serialize_list_item(frappe.get_doc("Tender STD Instance", row.name)) for row in page_rows]
	return {
		"items": items,
		"total": total,
		"page": page,
		"page_size": page_size,
	}


def _matches_query(instance_name: str, q_lower: str) -> bool:
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	blob = " ".join(
		filter(
			None,
			[
				doc.instance_code,
				doc.instance_title,
				doc.planning_package_code,
				doc.procuring_entity_name,
			],
		)
	).lower()
	return q_lower in blob


def _is_overdue_instance(instance_name: str) -> bool:
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	overdue = bool(
		doc.due_at and doc.due_at < frappe.utils.getdate() and doc.wizard_state in ws.OVERDUE_ELIGIBLE_STATES
	)
	return overdue


def delete_draft_configuration(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_DELETE_DRAFT)
	doc = _get_instance(configuration_id)
	assert_deletable(doc.wizard_state)
	audit_id = record_event(
		"wizard_instance_deleted",
		tender_std_instance=doc.name,
		object_id=doc.instance_code,
	)
	frappe.delete_doc("Tender STD Instance", doc.name, ignore_permissions=True, force=True)
	return {"deleted": True, "configuration_id": configuration_id, "audit_event_id": audit_id}


def _get_instance(configuration_id: str):
	configuration_id = (configuration_id or "").strip()
	if frappe.db.exists("Tender STD Instance", configuration_id):
		return frappe.get_doc("Tender STD Instance", configuration_id)
	if frappe.db.exists("Tender STD Instance", {"instance_code": configuration_id}):
		name = frappe.db.get_value("Tender STD Instance", {"instance_code": configuration_id})
		return frappe.get_doc("Tender STD Instance", name)
	frappe.throw(f"Configuration not found: {configuration_id}", frappe.DoesNotExistError)


def assert_instance_std_version_immutable(instance_name: str, new_version: str) -> None:
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	assert_std_version_immutable(doc.std_version, new_version)
