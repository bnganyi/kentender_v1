# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Technical-disclosure System Inventory contracts for ITW-07."""

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

SYSTEM_INVENTORY_STEP_CODE = "SYSTEM_INVENTORY"

INVENTORY_CATEGORIES = (
	"SYSTEMS_IN_SCOPE",
	"INFRASTRUCTURE_ENVIRONMENT",
	"USER_LOCATION_SCOPE",
	"INTEGRATION_POINTS",
	"DATA_MIGRATION_SCOPE",
	"LICENSING_SUPPORT_CONTEXT",
	"SECURITY_ACCESS_CONTEXT",
	"OUT_OF_SCOPE_ITEMS",
)

CATEGORY_LABELS = {
	"SYSTEMS_IN_SCOPE": "Systems in Scope",
	"INFRASTRUCTURE_ENVIRONMENT": "Infrastructure Environment",
	"USER_LOCATION_SCOPE": "User & Location Scope",
	"INTEGRATION_POINTS": "Integration Points",
	"DATA_MIGRATION_SCOPE": "Data Migration Scope",
	"LICENSING_SUPPORT_CONTEXT": "Licensing & Support Context",
	"SECURITY_ACCESS_CONTEXT": "Security & Access Context",
	"OUT_OF_SCOPE_ITEMS": "Out-of-Scope Items",
}

CATEGORY_CODE_PREFIXES = {
	"SYSTEMS_IN_SCOPE": "SYS",
	"INFRASTRUCTURE_ENVIRONMENT": "INFRA",
	"USER_LOCATION_SCOPE": "USR",
	"INTEGRATION_POINTS": "INT",
	"DATA_MIGRATION_SCOPE": "DATA",
	"LICENSING_SUPPORT_CONTEXT": "LIC",
	"SECURITY_ACCESS_CONTEXT": "SEC",
	"OUT_OF_SCOPE_ITEMS": "OOS",
}

PRICING_POLICIES = {"REQUIRED", "OPTIONAL", "NOT_PRICED"}
SCOPE_STATUSES = {"IN_SCOPE", "REFERENCE_ONLY", "OUT_OF_SCOPE"}
CONFIDENTIALITY_LEVELS = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "SECRET"}
REVIEW_STATUSES = {"DRAFT", "NEEDS_REVIEW", "APPROVED", "RETURNED"}
INTEGRATION_REQUIREMENTS = {"", "NONE", "API", "BATCH", "FILE_TRANSFER", "OTHER"}
STABLE_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")


def _json_string_list(value: Any) -> list[str]:
	if value in (None, ""):
		return []
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except (TypeError, ValueError):
			value = [part.strip() for part in value.split(",") if part.strip()]
	if not isinstance(value, list):
		value = [value]
	result: list[str] = []
	for entry in value:
		text = str(entry or "").strip()
		if text and text not in result:
			result.append(text)
	return result


def _json_dump(values: Any) -> str:
	return json.dumps(_json_string_list(values), separators=(",", ":"))


def _default_seed_items(*, complete: bool) -> list[dict[str, Any]]:
	rows = [
		{
			"item_code": "SYS-CORE-ERP",
			"category": "SYSTEMS_IN_SCOPE",
			"title": "Core Finance System",
			"description": "Production ERP requiring controlled data migration and integration.",
			"scope_status": "IN_SCOPE",
			"required_action": "MIGRATE",
			"bidder_consideration": "Provide a migration, reconciliation, and cutover approach.",
			"technical_details": "Version 4.2 production estate.",
			"data_volume": "500 GB",
			"integration_requirement": "API",
			"confidentiality_level": "CONFIDENTIAL",
			"bidder_disclosure_required": 1,
			"pricing_policy": "NOT_PRICED",
			"requirement_refs": ["3.1", "3.2"],
			"schedule_refs": ["PHASE_1", "PH1-REQ"],
			"contract_carry_forward": 1,
		},
		{
			"item_code": "INFRA-LAN-001",
			"category": "INFRASTRUCTURE_ENVIRONMENT",
			"title": "Local Area Network",
			"description": "Head-office network environment supporting the proposed solution.",
			"scope_status": "REFERENCE_ONLY",
			"required_action": "CONNECTIVITY_CHECK",
			"bidder_consideration": "Account for resilient low-latency connectivity.",
			"integration_requirement": "NONE",
			"confidentiality_level": "INTERNAL",
			"pricing_policy": "OPTIONAL",
			"requirement_refs": ["3.3"],
			"schedule_refs": ["PHASE_2"],
			"contract_carry_forward": 1,
		},
		{
			"item_code": "USR-HQ-001",
			"category": "USER_LOCATION_SCOPE",
			"title": "Head Office Users",
			"description": "Concurrent users operating from the primary head office.",
			"scope_status": "IN_SCOPE",
			"required_action": "SUPPORT",
			"confidentiality_level": "INTERNAL",
			"pricing_policy": "REQUIRED",
			"contract_carry_forward": 1,
		},
		{
			"item_code": "INT-LEDGER-API",
			"category": "INTEGRATION_POINTS",
			"title": "General Ledger Interface",
			"description": "Real-time interface for posting validated ledger transactions.",
			"scope_status": "IN_SCOPE",
			"required_action": "INTEGRATE",
			"bidder_consideration": "Provide documented and secured API integration.",
			"integration_requirement": "API",
			"confidentiality_level": "CONFIDENTIAL",
			"bidder_disclosure_required": 1,
			"pricing_policy": "REQUIRED",
			"requirement_refs": ["3.2"],
			"schedule_refs": ["PH2-INTEGRATION"],
			"contract_carry_forward": 1,
		},
		{
			"item_code": "DATA-ASSET-DB",
			"category": "DATA_MIGRATION_SCOPE",
			"title": "Legacy Asset Database",
			"description": "Legacy asset records requiring mapping, cleansing, and reconciliation.",
			"scope_status": "IN_SCOPE",
			"required_action": "MIGRATE",
			"technical_details": "SQL Server 2012 source.",
			"data_volume": "250,000 records",
			"integration_requirement": "BATCH",
			"confidentiality_level": "CONFIDENTIAL",
			"bidder_disclosure_required": 1,
			"pricing_policy": "REQUIRED",
			"schedule_refs": ["PH2-MIGRATION"],
			"contract_carry_forward": 1,
		},
		{
			"item_code": "LIC-SUPPORT-001",
			"category": "LICENSING_SUPPORT_CONTEXT",
			"title": "Platform Licensing and Support Context",
			"description": "Technical licensing footprint and support coverage expected for the solution.",
			"scope_status": "IN_SCOPE",
			"required_action": "DISCLOSE",
			"bidder_consideration": "Describe licensing metrics and support coverage without entering prices.",
			"confidentiality_level": "PUBLIC",
			"pricing_policy": "OPTIONAL",
			"requirement_refs": ["5.1"],
			"schedule_refs": ["PH3-SUPPORT"],
			"contract_carry_forward": 1,
		},
		{
			"item_code": "SEC-ACCESS-001",
			"category": "SECURITY_ACCESS_CONTEXT",
			"title": "Privileged Access Controls",
			"description": "Role-based access, MFA, and privileged administration controls.",
			"scope_status": "IN_SCOPE",
			"required_action": "SECURE",
			"bidder_consideration": "Explain access-control architecture and operational safeguards.",
			"integration_requirement": "API",
			"confidentiality_level": "SECRET",
			"bidder_disclosure_required": 1,
			"pricing_policy": "NOT_PRICED",
			"requirement_refs": ["4.1"],
			"contract_carry_forward": 1,
		},
		{
			"item_code": "OOS-TAPE-001",
			"category": "OUT_OF_SCOPE_ITEMS",
			"title": "External Backup Tape Library",
			"description": "Existing tape library retained as an explicit scope boundary.",
			"scope_status": "OUT_OF_SCOPE",
			"required_action": "NO_BIDDER_ACTION",
			"bidder_consideration": "No bidder action required.",
			"confidentiality_level": "INTERNAL",
			"pricing_policy": "NOT_PRICED",
			"contract_carry_forward": 0,
		},
	]
	for display_order, row in enumerate(rows, start=1):
		row["display_order"] = display_order
		row["review_status"] = "APPROVED" if complete else (
			"NEEDS_REVIEW" if row["confidentiality_level"] in {"CONFIDENTIAL", "SECRET"} else "DRAFT"
		)
	return rows


def _dedupe_inventory_docs(instance_name: str) -> str | None:
	rows = frappe.get_all(
		"Tender STD System Inventory",
		filters={"tender_std_instance": instance_name},
		fields=["name", "modified"],
		order_by="modified desc",
	)
	if not rows:
		return None
	keeper = rows[0]["name"]
	for row in rows[1:]:
		frappe.delete_doc("Tender STD System Inventory", row["name"], ignore_permissions=True)
	return keeper


def _append_item(doc, raw: dict[str, Any]) -> None:
	doc.append(
		"items",
		{
			"item_code": str(raw.get("item_code") or "").strip().upper(),
			"category": str(raw.get("category") or "").strip(),
			"title": str(raw.get("title") or "").strip(),
			"description": str(raw.get("description") or "").strip(),
			"scope_status": str(raw.get("scope_status") or "IN_SCOPE").strip(),
			"required_action": str(raw.get("required_action") or "").strip(),
			"bidder_consideration": str(raw.get("bidder_consideration") or "").strip(),
			"technical_details": str(raw.get("technical_details") or "").strip(),
			"data_volume": str(raw.get("data_volume") or "").strip(),
			"integration_requirement": str(raw.get("integration_requirement") or "").strip(),
			"confidentiality_level": str(raw.get("confidentiality_level") or "INTERNAL").strip(),
			"bidder_disclosure_required": 1 if raw.get("bidder_disclosure_required") else 0,
			"review_status": str(raw.get("review_status") or "DRAFT").strip(),
			"review_notes": str(raw.get("review_notes") or "").strip(),
			"pricing_policy": str(raw.get("pricing_policy") or "NOT_PRICED").strip(),
			"requirement_refs_json": _json_dump(
				raw.get("requirement_refs")
				if "requirement_refs" in raw
				else raw.get("requirement_refs_json")
			),
			"schedule_refs_json": _json_dump(
				raw.get("schedule_refs") if "schedule_refs" in raw else raw.get("schedule_refs_json")
			),
			"contract_carry_forward": 1 if raw.get("contract_carry_forward") else 0,
			"display_order": int(raw.get("display_order") or 0),
		},
	)


def _ensure_inventory_doc(instance_name: str, *, seed_complete: bool | None = None):
	name = _dedupe_inventory_docs(instance_name)
	if name:
		return frappe.get_doc("Tender STD System Inventory", name)
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD System Inventory",
			"tender_std_instance": instance_name,
			"inventory_code": SYSTEM_INVENTORY_STEP_CODE,
			"inventory_title": "System Inventory",
			"description": "Technical-disclosure inventory; commercial pricing is configured separately.",
			"selected_item_code": "SYS-CORE-ERP",
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
		name = _dedupe_inventory_docs(instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD System Inventory", name)
	return doc


def _serialize_item(row: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	code = str(row.get("item_code") or "").strip()
	return {
		"item_id": code,
		"item_code": code,
		"category": str(row.get("category") or "").strip(),
		"category_label": CATEGORY_LABELS.get(str(row.get("category") or "").strip(), ""),
		"title": str(row.get("title") or "").strip(),
		"description": str(row.get("description") or "").strip(),
		"scope_status": str(row.get("scope_status") or "").strip(),
		"required_action": str(row.get("required_action") or "").strip(),
		"bidder_consideration": str(row.get("bidder_consideration") or "").strip(),
		"technical_details": str(row.get("technical_details") or "").strip(),
		"data_volume": str(row.get("data_volume") or "").strip(),
		"integration_requirement": str(row.get("integration_requirement") or "").strip(),
		"confidentiality_level": str(row.get("confidentiality_level") or "").strip(),
		"bidder_disclosure_required": int(row.get("bidder_disclosure_required") or 0),
		"review_status": str(row.get("review_status") or "").strip(),
		"review_notes": str(row.get("review_notes") or "").strip(),
		"pricing_policy": str(row.get("pricing_policy") or "").strip(),
		"pricing_policy_read_only": True,
		"requirement_refs": _json_string_list(row.get("requirement_refs_json")),
		"schedule_refs": _json_string_list(row.get("schedule_refs_json")),
		"contract_carry_forward": int(row.get("contract_carry_forward") or 0),
		"display_order": int(row.get("display_order") or 0),
	}


def _known_requirement_codes(instance_name: str) -> set[str]:
	return {option["code"] for option in _requirement_options(instance_name)}


def _requirement_options(instance_name: str) -> list[dict[str, str]]:
	parent = frappe.db.get_value("Tender STD IT Requirements", {"tender_std_instance": instance_name})
	if not parent:
		return []
	rows = frappe.get_all(
		"Tender STD Requirement Item",
		filters={"parent": parent, "parenttype": "Tender STD IT Requirements", "parentfield": "items"},
		fields=["requirement_code", "title", "idx"],
		order_by="idx asc",
	)
	return [
		{"id": row.requirement_code, "code": row.requirement_code, "name": row.title}
		for row in rows
		if row.requirement_code
	]


def _known_schedule_codes(instance_name: str) -> set[str]:
	return {option["code"] for option in _schedule_options(instance_name)}


def _schedule_options(instance_name: str) -> list[dict[str, str]]:
	parent = frappe.db.get_value("Tender STD Implementation Schedule", {"tender_std_instance": instance_name})
	if not parent:
		return []
	phases = frappe.get_all(
		"Tender STD Schedule Phase Item",
		filters={"parent": parent, "parenttype": "Tender STD Implementation Schedule", "parentfield": "phases"},
		fields=["phase_code", "title", "idx"],
		order_by="idx asc",
	)
	milestones = frappe.get_all(
		"Tender STD Schedule Milestone Item",
		filters={"parent": parent, "parenttype": "Tender STD Implementation Schedule", "parentfield": "milestones"},
		fields=["milestone_code", "title", "idx"],
		order_by="idx asc",
	)
	return [
		{"id": row.phase_code, "code": row.phase_code, "name": row.title}
		for row in phases
		if row.phase_code
	] + [
		{"id": row.milestone_code, "code": row.milestone_code, "name": row.title}
		for row in milestones
		if row.milestone_code
	]


def _validate_items(instance_name: str, items: list[dict[str, Any]]) -> None:
	codes: set[str] = set()
	known_requirements: set[str] | None = None
	known_schedule: set[str] | None = None
	for raw in items:
		code = str(raw.get("item_code") or "").strip().upper()
		if not code or not STABLE_CODE_PATTERN.fullmatch(code):
			frappe.throw("Inventory item code is required and must use uppercase letters, numbers, hyphens, or underscores.")
		if code in codes:
			frappe.throw(f"Duplicate inventory item code: {code}")
		codes.add(code)
		category = str(raw.get("category") or "").strip()
		if category not in INVENTORY_CATEGORIES:
			frappe.throw(f"Inventory item {code} has an invalid category.")
		for fieldname, label in (
			("title", "title"),
			("description", "description"),
			("required_action", "required action"),
		):
			if not str(raw.get(fieldname) or "").strip():
				frappe.throw(f"Inventory item {code} requires a {label}.")
		if str(raw.get("scope_status") or "").strip() not in SCOPE_STATUSES:
			frappe.throw(f"Inventory item {code} has an invalid scope status.")
		if (
			str(raw.get("scope_status") or "").strip() == "OUT_OF_SCOPE"
			and str(raw.get("required_action") or "").strip() != "NO_BIDDER_ACTION"
		):
			frappe.throw(f"Out-of-scope inventory item {code} cannot require bidder action.")
		if str(raw.get("pricing_policy") or "").strip() not in PRICING_POLICIES:
			frappe.throw(f"Inventory item {code} has an invalid pricing policy.")
		if str(raw.get("confidentiality_level") or "").strip() not in CONFIDENTIALITY_LEVELS:
			frappe.throw(f"Inventory item {code} has an invalid confidentiality level.")
		if str(raw.get("review_status") or "").strip() not in REVIEW_STATUSES:
			frappe.throw(f"Inventory item {code} has an invalid review status.")
		if str(raw.get("integration_requirement") or "").strip() not in INTEGRATION_REQUIREMENTS:
			frappe.throw(f"Inventory item {code} has an invalid integration requirement.")
		requirement_refs = _json_string_list(
			raw.get("requirement_refs")
			if "requirement_refs" in raw
			else raw.get("requirement_refs_json")
		)
		if requirement_refs:
			known_requirements = known_requirements if known_requirements is not None else _known_requirement_codes(instance_name)
			unknown = [ref for ref in requirement_refs if ref not in known_requirements]
			if unknown:
				frappe.throw(f"Inventory item {code} references unknown requirement code(s): {', '.join(unknown)}")
		schedule_refs = _json_string_list(
			raw.get("schedule_refs") if "schedule_refs" in raw else raw.get("schedule_refs_json")
		)
		if schedule_refs:
			known_schedule = known_schedule if known_schedule is not None else _known_schedule_codes(instance_name)
			unknown = [ref for ref in schedule_refs if ref not in known_schedule]
			if unknown:
				frappe.throw(f"Inventory item {code} references unknown schedule code(s): {', '.join(unknown)}")


def _item_complete(item: dict[str, Any]) -> bool:
	return bool(
		item.get("item_code")
		and item.get("category")
		and item.get("title")
		and item.get("description")
		and item.get("required_action")
		and item.get("pricing_policy") in PRICING_POLICIES
		and item.get("review_status") == "APPROVED"
	)


def compute_inventory_completion(items: list[dict[str, Any]]) -> dict[str, Any]:
	total = len(items)
	completed = sum(1 for item in items if _item_complete(item))
	needs_review = sum(1 for item in items if item.get("review_status") in {"DRAFT", "NEEDS_REVIEW", "RETURNED"})
	sensitive_pending = sum(
		1
		for item in items
		if item.get("confidentiality_level") in {"CONFIDENTIAL", "SECRET"}
		and item.get("review_status") != "APPROVED"
	)
	return {
		"completed": completed,
		"total": total,
		"percent": int(round(completed / total * 100)) if total else 0,
		"gaps": {
			"needs_review": needs_review,
			"sensitive_disclosure_pending": sensitive_pending,
		},
	}


def _group_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
	return [
		{
			"category": category,
			"label": CATEGORY_LABELS[category],
			"item_count": sum(1 for item in items if item["category"] == category),
			"items": sorted(
				[item for item in items if item["category"] == category],
				key=lambda item: (item["display_order"], item["item_code"]),
			),
		}
		for category in INVENTORY_CATEGORIES
	]


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
		{"tender_std_instance": instance_name, "step_code": SYSTEM_INVENTORY_STEP_CODE},
	)
	if step_name:
		frappe.db.set_value(
			"Wizard Step Instance",
			step_name,
			"status",
			"COMPLETE" if complete else "IN_PROGRESS",
		)


def _public_reference(reference: Any) -> dict[str, str]:
	if not isinstance(reference, dict):
		return {"code": "", "name": ""}
	return {
		"code": str(reference.get("code") or "").strip(),
		"name": str(reference.get("name") or "").strip(),
	}


def _build_payload(configuration_id: str, doc, overview: dict[str, Any]) -> dict[str, Any]:
	items = [_serialize_item(row.as_dict()) for row in doc.items]
	completion = compute_inventory_completion(items)
	blockers, warnings = _latest_validation_counts(doc.tender_std_instance)
	tender_number = (
		frappe.db.get_value(
			"Tender STD TDS",
			{"tender_std_instance": doc.tender_std_instance},
			"tender_number",
		)
		or ""
	).strip()
	selected_item_code = str(doc.selected_item_code or "").strip() or (
		items[0]["item_code"] if items else ""
	)
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
		"inventory_code": str(doc.inventory_code or "").strip(),
		"inventory_title": str(doc.inventory_title or "").strip(),
		"description": str(doc.description or "").strip(),
		"review_status": str(doc.review_status or "").strip(),
		"lock_status": str(doc.lock_status or "").strip(),
		"selected_item_id": selected_item_code,
		"requirement_options": _requirement_options(doc.tender_std_instance),
		"schedule_options": _schedule_options(doc.tender_std_instance),
		"categories": _group_items(items),
		"completion": completion,
	}


def get_system_inventory(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	doc = _ensure_inventory_doc(instance.name)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))


def _flatten_category_payload(payload: dict[str, Any]) -> list[dict[str, Any]] | None:
	if payload.get("items") is not None:
		return list(payload.get("items") or [])
	if payload.get("categories") is None:
		return None
	return [
		item
		for group in payload.get("categories") or []
		for item in group.get("items") or []
	]


def _generate_item_code(doc, selected: dict[str, Any]) -> str:
	category = str(selected.get("category") or "").strip()
	prefix = CATEGORY_CODE_PREFIXES.get(category, "INV")
	slug = re.sub(r"[^A-Z0-9]+", "-", str(selected.get("title") or "").strip().upper()).strip("-")
	base = f"{prefix}-{slug or 'ITEM'}"[:120].rstrip("-")
	existing = {str(row.item_code or "").strip() for row in doc.items}
	candidate = base
	suffix = 2
	while candidate in existing:
		candidate = f"{base}-{suffix}"
		suffix += 1
	return candidate


def save_system_inventory(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	assert_configuration_editable(instance.wizard_state)
	doc = _ensure_inventory_doc(instance.name)
	if str(doc.lock_status or "").strip() != "UNLOCKED":
		frappe.throw(
			f"System inventory is locked with status {doc.lock_status}.",
			title="ITW_INVENTORY_LOCKED",
			exc=frappe.ValidationError,
		)
	items = _flatten_category_payload(payload)
	if items is None:
		selected = dict(payload.get("selected_item") or {})
		if not selected:
			items = [row.as_dict() for row in doc.items]
		else:
			selected_id = str(payload.get("selected_item_id") or selected.get("item_code") or "").strip().upper()
			if not selected_id:
				selected_id = _generate_item_code(doc, selected)
				selected["item_code"] = selected_id
			incoming_code = str(selected.get("item_code") or selected_id).strip().upper()
			if incoming_code != selected_id:
				frappe.throw("Inventory item code is immutable during selected-item updates.")
			existing = {str(row.item_code or "").strip(): row.as_dict() for row in doc.items}
			if selected_id in existing:
				existing[selected_id].update(selected)
			else:
				existing[selected_id] = {**selected, "item_code": selected_id}
			items = list(existing.values())
	_validate_items(instance.name, items)
	doc.set("items", [])
	for row in items:
		_append_item(doc, row)
	if payload.get("inventory_title") is not None:
		doc.inventory_title = str(payload.get("inventory_title") or "").strip()
	if payload.get("description") is not None:
		doc.description = str(payload.get("description") or "").strip()
	if payload.get("review_status") is not None:
		doc.review_status = str(payload.get("review_status") or "").strip()
	if payload.get("selected_item_id") or payload.get("selected_item", {}).get("item_code"):
		doc.selected_item_code = str(
			payload.get("selected_item_id") or payload.get("selected_item", {}).get("item_code") or ""
		).strip().upper()
	doc.save(ignore_permissions=True)
	serialized = [_serialize_item(row.as_dict()) for row in doc.items]
	completion = compute_inventory_completion(serialized)
	complete = bool(serialized) and completion["completed"] == completion["total"]
	_update_step_status(instance.name, complete=complete)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))
