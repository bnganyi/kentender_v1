# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SCC / Contract Carry-Forward contracts for ITW-11."""

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

STEP_CODE = "SCC"
SCC_STEP_CODE = STEP_CODE
CARRY_FORWARD = {"YES", "NO", "CONDITIONAL"}

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


def _default_seed_items(*, complete: bool) -> list[dict[str, Any]]:
	rows = [
		{
			"item_code": "SCC-SLA-001",
			"title": "Support SLA Carry-Forward",
			"carry_forward": "YES",
			"obligation_text": "Agreed support SLA metrics carry into the contract.",
			"contract_location": "SCC Clause 8",
			"acceptance_method": "SIGNED_SCC",
			"source_requirement_code": "5.1",
			"source_phase_code": "PH3-SUPPORT",
			"source_price_line_code": "PL-RECURRENT-001",
		},
		{
			"item_code": "SCC-SEC-001",
			"title": "Security Controls Carry-Forward",
			"carry_forward": "YES",
			"obligation_text": "Privileged access controls remain contractual obligations.",
			"contract_location": "SCC Clause 12",
			"acceptance_method": "SIGNED_SCC",
			"source_requirement_code": "4.1",
		},
		{
			"item_code": "SCC-MIG-001",
			"title": "Migration Acceptance Carry-Forward",
			"carry_forward": "CONDITIONAL",
			"obligation_text": "Migration reconciliation obligations apply when migration is in scope.",
			"contract_location": "SCC Clause 15",
			"acceptance_method": "ACCEPTANCE_CERTIFICATE",
			"source_phase_code": "PH2-MIGRATION",
			"source_price_line_code": "PL-INSTALL-001",
		},
	]
	for display_order, row in enumerate(rows, start=1):
		row["display_order"] = display_order
	return rows


def _append_item(doc, raw: dict[str, Any]) -> None:
	doc.append(
		"items",
		{
			"item_code": str(raw.get("item_code") or "").strip().upper(),
			"title": str(raw.get("title") or "").strip(),
			"carry_forward": str(raw.get("carry_forward") or "YES").strip(),
			"obligation_text": str(raw.get("obligation_text") or "").strip(),
			"contract_location": str(raw.get("contract_location") or "").strip(),
			"acceptance_method": str(raw.get("acceptance_method") or "").strip(),
			"source_requirement_code": str(raw.get("source_requirement_code") or "").strip(),
			"source_phase_code": str(raw.get("source_phase_code") or "").strip(),
			"source_price_line_code": str(raw.get("source_price_line_code") or "").strip(),
			"display_order": int(raw.get("display_order") or 0),
		},
	)


def _ensure_scc_doc(instance_name: str, *, seed_complete: bool | None = None):
	name = _dedupe_docs("Tender STD SCC", instance_name)
	if name:
		return frappe.get_doc("Tender STD SCC", name)
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD SCC",
			"tender_std_instance": instance_name,
			"scc_code": STEP_CODE,
			"scc_title": "SCC / Contract Carry-Forward",
			"description": "Special Conditions of Contract and carry-forward obligations.",
			"review_status": "APPROVED" if seed_complete else "DRAFT",
			"lock_status": "UNLOCKED",
		}
	)
	for row in _default_seed_items(complete=bool(seed_complete)):
		_append_item(doc, row)
	try:
		doc.insert(ignore_permissions=True)
	except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
		frappe.db.rollback()
		name = _dedupe_docs("Tender STD SCC", instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD SCC", name)
	return doc


def _serialize_item(row: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	code = str(row.get("item_code") or "").strip()
	return {
		"item_id": code,
		"item_code": code,
		"title": str(row.get("title") or "").strip(),
		"carry_forward": str(row.get("carry_forward") or "").strip(),
		"obligation_text": str(row.get("obligation_text") or "").strip(),
		"contract_location": str(row.get("contract_location") or "").strip(),
		"acceptance_method": str(row.get("acceptance_method") or "").strip(),
		"source_requirement_code": str(row.get("source_requirement_code") or "").strip(),
		"source_phase_code": str(row.get("source_phase_code") or "").strip(),
		"source_price_line_code": str(row.get("source_price_line_code") or "").strip(),
		"display_order": int(row.get("display_order") or 0),
	}


def _validate_items(items: list[dict[str, Any]]) -> None:
	codes: set[str] = set()
	for raw in items:
		code = str(raw.get("item_code") or "").strip().upper()
		if not code or not STABLE_CODE_PATTERN.fullmatch(code):
			frappe.throw("SCC item code is required and must use uppercase letters, numbers, hyphens, or underscores.")
		if code in codes:
			frappe.throw(f"Duplicate SCC item code: {code}")
		codes.add(code)
		if not str(raw.get("title") or "").strip():
			frappe.throw(f"SCC item {code} requires a title.")
		if str(raw.get("carry_forward") or "").strip() not in CARRY_FORWARD:
			frappe.throw(f"SCC item {code} has an invalid carry_forward value.")


def _item_complete(item: dict[str, Any]) -> bool:
	return bool(
		item.get("item_code")
		and item.get("title")
		and item.get("carry_forward") in CARRY_FORWARD
		and item.get("obligation_text")
	)


def _build_payload(configuration_id: str, doc, overview: dict[str, Any]) -> dict[str, Any]:
	items = [_serialize_item(row.as_dict()) for row in doc.items]
	completed = sum(1 for item in items if _item_complete(item))
	payload = _overview_context(configuration_id, doc.tender_std_instance, overview)
	payload.update(
		{
			"scc_code": str(doc.scc_code or "").strip(),
			"scc_title": str(doc.scc_title or "").strip(),
			"description": str(doc.description or "").strip(),
			"review_status": str(doc.review_status or "").strip(),
			"lock_status": str(doc.lock_status or "").strip(),
			"items": items,
			"completion": {
				"completed": completed,
				"total": len(items),
				"percent": int(round(completed / len(items) * 100)) if items else 0,
			},
		}
	)
	return payload


def get_scc(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	doc = _ensure_scc_doc(instance.name)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))


def save_scc(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	assert_configuration_editable(instance.wizard_state)
	doc = _ensure_scc_doc(instance.name)
	if str(doc.lock_status or "").strip() != "UNLOCKED":
		frappe.throw(
			f"SCC is locked with status {doc.lock_status}.",
			title="ITW_SCC_LOCKED",
			exc=frappe.ValidationError,
		)
	items = list(payload.get("items") or [])
	_validate_items(items)
	doc.set("items", [])
	for row in items:
		_append_item(doc, row)
	if payload.get("scc_title") is not None:
		doc.scc_title = str(payload.get("scc_title") or "").strip()
	if payload.get("description") is not None:
		doc.description = str(payload.get("description") or "").strip()
	if payload.get("review_status") is not None:
		doc.review_status = str(payload.get("review_status") or "").strip()
	doc.save(ignore_permissions=True)
	serialized = [_serialize_item(row.as_dict()) for row in doc.items]
	complete = bool(serialized) and all(_item_complete(item) for item in serialized) and str(doc.review_status) == "APPROVED"
	_update_step_status(instance.name, complete=complete)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))
