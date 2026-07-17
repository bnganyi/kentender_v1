# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Publication Readiness contracts for ITW-15."""

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

STEP_CODE = "PUBLICATION_READINESS"
PUBLICATION_READINESS_STEP_CODE = STEP_CODE

STABLE_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")


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


def _parse_checklist(value: Any) -> list[dict[str, Any]]:
	if value in (None, ""):
		return []
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except (TypeError, ValueError):
			return []
	if not isinstance(value, list):
		return []
	result = []
	for entry in value:
		if not isinstance(entry, dict):
			continue
		result.append(
			{
				"item_code": str(entry.get("item_code") or entry.get("code") or "").strip().upper(),
				"title": str(entry.get("title") or entry.get("label") or "").strip(),
				"confirmed": bool(entry.get("confirmed")),
			}
		)
	return result


def _dump_checklist(value: Any) -> str:
	return json.dumps(_parse_checklist(value), separators=(",", ":"))


def _default_checklist(*, complete: bool) -> list[dict[str, Any]]:
	rows = [
		{"item_code": "PUB-APPROVALS", "title": "All review stages approved", "confirmed": complete},
		{"item_code": "PUB-VALIDATION", "title": "No open blocker findings", "confirmed": complete},
		{"item_code": "PUB-PREVIEW", "title": "Render preview confirmed", "confirmed": complete},
		{"item_code": "PUB-HANDOFF", "title": "Ready for tender publication handoff", "confirmed": complete},
	]
	return rows


def _ensure_publication_readiness_doc(instance_name: str, *, seed_complete: bool | None = None):
	name = _dedupe_docs("Tender STD Publication Readiness", instance_name)
	if name:
		return frappe.get_doc("Tender STD Publication Readiness", name)
	checklist = _default_checklist(complete=bool(seed_complete))
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD Publication Readiness",
			"tender_std_instance": instance_name,
			"readiness_code": STEP_CODE,
			"readiness_title": "Publication Readiness",
			"description": "Confirm readiness for tender publication handoff.",
			"review_status": "APPROVED" if seed_complete else "DRAFT",
			"lock_status": "UNLOCKED",
			"confirmation_checklist_json": _dump_checklist(checklist),
			"package_summary": "Publication readiness checklist for IT tender configuration.",
			"status": "READY" if seed_complete else "DRAFT",
		}
	)
	try:
		doc.insert(ignore_permissions=True)
	except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
		frappe.db.rollback()
		name = _dedupe_docs("Tender STD Publication Readiness", instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD Publication Readiness", name)
	return doc


def _build_payload(configuration_id: str, doc, overview: dict[str, Any]) -> dict[str, Any]:
	checklist = _parse_checklist(doc.confirmation_checklist_json)
	confirmed = sum(1 for item in checklist if item.get("confirmed"))
	payload = _overview_context(configuration_id, doc.tender_std_instance, overview)
	payload.update(
		{
			"readiness_code": str(doc.readiness_code or "").strip(),
			"readiness_title": str(doc.readiness_title or "").strip(),
			"description": str(doc.description or "").strip(),
			"review_status": str(doc.review_status or "").strip(),
			"lock_status": str(doc.lock_status or "").strip(),
			"status": str(doc.status or "").strip(),
			"package_summary": str(doc.package_summary or "").strip(),
			"confirmation_checklist": checklist,
			"mark_publication_ready": str(doc.status or "").strip() == "READY",
			"completion": {
				"completed": confirmed,
				"total": len(checklist),
				"percent": int(round(confirmed / len(checklist) * 100)) if checklist else 0,
			},
		}
	)
	return payload


def get_publication_readiness(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	doc = _ensure_publication_readiness_doc(instance.name)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))


def save_publication_readiness(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	assert_configuration_editable(instance.wizard_state)
	doc = _ensure_publication_readiness_doc(instance.name)
	if str(doc.lock_status or "").strip() != "UNLOCKED":
		frappe.throw(
			f"Publication readiness is locked with status {doc.lock_status}.",
			title="ITW_PUBLICATION_LOCKED",
			exc=frappe.ValidationError,
		)
	if payload.get("confirmation_checklist") is not None or payload.get("confirmation_checklist_json") is not None:
		doc.confirmation_checklist_json = _dump_checklist(
			payload.get("confirmation_checklist")
			if payload.get("confirmation_checklist") is not None
			else payload.get("confirmation_checklist_json")
		)
	if payload.get("package_summary") is not None:
		doc.package_summary = str(payload.get("package_summary") or "").strip()
	if payload.get("status") is not None:
		doc.status = str(payload.get("status") or "").strip()
	if payload.get("readiness_title") is not None:
		doc.readiness_title = str(payload.get("readiness_title") or "").strip()
	if payload.get("description") is not None:
		doc.description = str(payload.get("description") or "").strip()
	if payload.get("review_status") is not None:
		doc.review_status = str(payload.get("review_status") or "").strip()
	if payload.get("mark_ready"):
		doc.status = "READY"
		checklist = _parse_checklist(doc.confirmation_checklist_json)
		for item in checklist:
			item["confirmed"] = True
		doc.confirmation_checklist_json = _dump_checklist(checklist)
		doc.review_status = "APPROVED"
	doc.save(ignore_permissions=True)
	checklist = _parse_checklist(doc.confirmation_checklist_json)
	complete = str(doc.status or "").strip() == "READY" and bool(checklist) and all(
		item.get("confirmed") for item in checklist
	)
	_update_step_status(instance.name, complete=complete)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))
