# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Price Schedule contracts for ITW-08 (Approach C owns qty/unit/evaluated-price)."""

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

STEP_CODE = "PRICE_SCHEDULE"
PRICE_SCHEDULE_STEP_CODE = STEP_CODE
PRICING_BASES = {"SUPPLY", "INSTALL", "RECURRENT", "OTHER"}
MANDATORY_OPTIONAL = {"MANDATORY", "OPTIONAL"}

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
			"line_code": "PL-SUPPLY-001",
			"title": "Core Platform Supply",
			"pricing_basis": "SUPPLY",
			"quantity": 1,
			"unit_of_measure": "LOT",
			"tax_treatment": "STANDARD_VAT",
			"evaluated_price_included": 1,
			"bidder_instruction": "Quote supply price inclusive of delivery.",
			"inventory_item_code": "SYS-CORE-ERP",
			"requirement_ref": "3.1",
			"schedule_ref": "PHASE_1",
			"mandatory_optional": "MANDATORY",
		},
		{
			"line_code": "PL-INSTALL-001",
			"title": "Installation and Commissioning",
			"pricing_basis": "INSTALL",
			"quantity": 1,
			"unit_of_measure": "LOT",
			"tax_treatment": "STANDARD_VAT",
			"evaluated_price_included": 1,
			"bidder_instruction": "Include installation labour and configuration.",
			"inventory_item_code": "INFRA-LAN-001",
			"requirement_ref": "3.3",
			"schedule_ref": "PHASE_2",
			"mandatory_optional": "MANDATORY",
		},
		{
			"line_code": "PL-RECURRENT-001",
			"title": "Annual Support and Maintenance",
			"pricing_basis": "RECURRENT",
			"quantity": 3,
			"unit_of_measure": "YEAR",
			"tax_treatment": "STANDARD_VAT",
			"evaluated_price_included": 1,
			"bidder_instruction": "Provide annual support for the evaluation period.",
			"inventory_item_code": "LIC-SUPPORT-001",
			"requirement_ref": "5.1",
			"schedule_ref": "PH3-SUPPORT",
			"mandatory_optional": "OPTIONAL",
		},
	]
	for display_order, row in enumerate(rows, start=1):
		row["display_order"] = display_order
		row["review_status"] = "APPROVED" if complete else "DRAFT"
	return rows


def _append_item(doc, raw: dict[str, Any]) -> None:
	doc.append(
		"items",
		{
			"line_code": str(raw.get("line_code") or "").strip().upper(),
			"title": str(raw.get("title") or "").strip(),
			"pricing_basis": str(raw.get("pricing_basis") or "SUPPLY").strip(),
			"quantity": float(raw.get("quantity") or 0),
			"unit_of_measure": str(raw.get("unit_of_measure") or "").strip(),
			"tax_treatment": str(raw.get("tax_treatment") or "").strip(),
			"evaluated_price_included": 1 if raw.get("evaluated_price_included") else 0,
			"bidder_instruction": str(raw.get("bidder_instruction") or "").strip(),
			"inventory_item_code": str(raw.get("inventory_item_code") or "").strip().upper(),
			"requirement_ref": str(raw.get("requirement_ref") or "").strip(),
			"schedule_ref": str(raw.get("schedule_ref") or "").strip(),
			"mandatory_optional": str(raw.get("mandatory_optional") or "MANDATORY").strip(),
			"review_status": str(raw.get("review_status") or "DRAFT").strip(),
			"display_order": int(raw.get("display_order") or 0),
		},
	)


def _ensure_price_schedule_doc(instance_name: str, *, seed_complete: bool | None = None):
	name = _dedupe_docs("Tender STD Price Schedule", instance_name)
	if name:
		return frappe.get_doc("Tender STD Price Schedule", name)
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD Price Schedule",
			"tender_std_instance": instance_name,
			"schedule_code": STEP_CODE,
			"schedule_title": "Price Schedule",
			"description": "Commercial price lines; quantity and evaluated-price ownership lives here (Approach C).",
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
		name = _dedupe_docs("Tender STD Price Schedule", instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD Price Schedule", name)
	return doc


def _serialize_item(row: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	code = str(row.get("line_code") or "").strip()
	return {
		"line_id": code,
		"line_code": code,
		"title": str(row.get("title") or "").strip(),
		"pricing_basis": str(row.get("pricing_basis") or "").strip(),
		"quantity": float(row.get("quantity") or 0),
		"unit_of_measure": str(row.get("unit_of_measure") or "").strip(),
		"tax_treatment": str(row.get("tax_treatment") or "").strip(),
		"evaluated_price_included": int(row.get("evaluated_price_included") or 0),
		"bidder_instruction": str(row.get("bidder_instruction") or "").strip(),
		"inventory_item_code": str(row.get("inventory_item_code") or "").strip(),
		"requirement_ref": str(row.get("requirement_ref") or "").strip(),
		"schedule_ref": str(row.get("schedule_ref") or "").strip(),
		"mandatory_optional": str(row.get("mandatory_optional") or "").strip(),
		"review_status": str(row.get("review_status") or "").strip(),
		"display_order": int(row.get("display_order") or 0),
	}


def _validate_items(items: list[dict[str, Any]]) -> None:
	codes: set[str] = set()
	for raw in items:
		code = str(raw.get("line_code") or "").strip().upper()
		if not code or not STABLE_CODE_PATTERN.fullmatch(code):
			frappe.throw("Price line code is required and must use uppercase letters, numbers, hyphens, or underscores.")
		if code in codes:
			frappe.throw(f"Duplicate price line code: {code}")
		codes.add(code)
		if not str(raw.get("title") or "").strip():
			frappe.throw(f"Price line {code} requires a title.")
		if str(raw.get("pricing_basis") or "").strip() not in PRICING_BASES:
			frappe.throw(f"Price line {code} has an invalid pricing basis.")
		if str(raw.get("mandatory_optional") or "").strip() not in MANDATORY_OPTIONAL:
			frappe.throw(f"Price line {code} has an invalid mandatory/optional value.")
		if str(raw.get("review_status") or "").strip() not in REVIEW_STATUSES:
			frappe.throw(f"Price line {code} has an invalid review status.")
		try:
			qty = float(raw.get("quantity") or 0)
		except (TypeError, ValueError):
			frappe.throw(f"Price line {code} requires a numeric quantity.")
		if qty < 0:
			frappe.throw(f"Price line {code} quantity cannot be negative.")


def _item_complete(item: dict[str, Any]) -> bool:
	return bool(
		item.get("line_code")
		and item.get("title")
		and item.get("pricing_basis") in PRICING_BASES
		and float(item.get("quantity") or 0) > 0
		and item.get("unit_of_measure")
		and item.get("review_status") == "APPROVED"
	)


def _build_payload(configuration_id: str, doc, overview: dict[str, Any]) -> dict[str, Any]:
	items = [_serialize_item(row.as_dict()) for row in doc.items]
	completed = sum(1 for item in items if _item_complete(item))
	payload = _overview_context(configuration_id, doc.tender_std_instance, overview)
	payload.update(
		{
			"schedule_code": str(doc.schedule_code or "").strip(),
			"schedule_title": str(doc.schedule_title or "").strip(),
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


def get_price_schedule(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	doc = _ensure_price_schedule_doc(instance.name)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))


def save_price_schedule(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	assert_configuration_editable(instance.wizard_state)
	doc = _ensure_price_schedule_doc(instance.name)
	if str(doc.lock_status or "").strip() != "UNLOCKED":
		frappe.throw(
			f"Price schedule is locked with status {doc.lock_status}.",
			title="ITW_PRICE_SCHEDULE_LOCKED",
			exc=frappe.ValidationError,
		)
	items = list(payload.get("items") or [])
	_validate_items(items)
	doc.set("items", [])
	for row in items:
		_append_item(doc, row)
	if payload.get("schedule_title") is not None:
		doc.schedule_title = str(payload.get("schedule_title") or "").strip()
	if payload.get("description") is not None:
		doc.description = str(payload.get("description") or "").strip()
	if payload.get("review_status") is not None:
		doc.review_status = str(payload.get("review_status") or "").strip()
	doc.save(ignore_permissions=True)
	serialized = [_serialize_item(row.as_dict()) for row in doc.items]
	complete = bool(serialized) and all(_item_complete(item) for item in serialized)
	_update_step_status(instance.name, complete=complete)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))
