# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Profile step payload for ITW-03."""

from __future__ import annotations

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

PROFILE_STEP_CODE = "TENDER_PROFILE"
REQUIRED_FIELD_TOTAL = 11

REQUIRED_FIELD_LABELS = {
	"tender_name": "Tender Display Title",
	"contract_description": "Tender Description / Scope Summary",
	"lotting_strategy": "Lot Structure",
	"reservation_setting": "Reserved Procurement Setting",
	"tender_security_applicability": "Tender Security Applicability",
	"clarification_contact_email": "Clarification Contact Email",
	"alternative_tenders_allowed": "Alternative Tenders Setting",
	"jv_allowed": "Joint Ventures Setting",
	"pre_tender_meeting_required": "Pre-tender Meeting Setting",
	"language_code": "Submission Language",
	"currency_code": "Currency",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _dedupe_profile_docs(instance_name: str) -> str | None:
	rows = frappe.get_all(
		"Tender STD Profile",
		filters={"tender_std_instance": instance_name},
		fields=["name", "modified"],
		order_by="modified desc",
	)
	if not rows:
		return None
	if len(rows) == 1:
		return rows[0]["name"]
	keeper = rows[0]["name"]
	for row in rows[1:]:
		frappe.delete_doc("Tender STD Profile", row["name"], ignore_permissions=True)
	return keeper


def _profile_doc_name(instance_name: str) -> str | None:
	return _dedupe_profile_docs(instance_name)


def _ensure_profile_doc(instance_name: str) -> frappe.model.document.Document:
	name = _profile_doc_name(instance_name)
	if name:
		return frappe.get_doc("Tender STD Profile", name)
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD Profile",
			"tender_std_instance": instance_name,
			"language_code": "en",
			"currency_code": "KES",
		}
	)
	try:
		doc.insert(ignore_permissions=True)
	except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
		frappe.db.rollback()
		name = _profile_doc_name(instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD Profile", name)
	return doc


def _empty_profile_values() -> dict[str, Any]:
	return {
		"tender_name": "",
		"contract_description": "",
		"clarification_contact_email": "",
		"lotting_strategy": "",
		"reservation_applies": 0,
		"reserved_group_code": "",
		"tender_security_applicability": "",
		"alternative_tenders_allowed": 0,
		"jv_allowed": 0,
		"pre_tender_meeting_required": 0,
		"language_code": "en",
		"currency_code": "KES",
	}


def _serialize_profile_values(doc) -> dict[str, Any]:
	if not doc:
		return _empty_profile_values()
	return {
		"tender_name": (doc.tender_name or "").strip(),
		"contract_description": (doc.contract_description or "").strip(),
		"clarification_contact_email": (doc.clarification_contact_email or "").strip(),
		"lotting_strategy": (doc.lotting_strategy or "").strip(),
		"reservation_applies": int(doc.reservation_applies or 0),
		"reserved_group_code": (doc.reserved_group_code or "").strip(),
		"tender_security_applicability": (doc.tender_security_applicability or "").strip(),
		"alternative_tenders_allowed": int(doc.alternative_tenders_allowed or 0),
		"jv_allowed": int(doc.jv_allowed or 0),
		"pre_tender_meeting_required": int(doc.pre_tender_meeting_required or 0),
		"language_code": (doc.language_code or "en").strip(),
		"currency_code": (doc.currency_code or "KES").strip(),
	}


def _reservation_complete(values: dict[str, Any]) -> bool:
	if values.get("reservation_applies"):
		return bool((values.get("reserved_group_code") or "").strip())
	return True


def compute_profile_completion(values: dict[str, Any]) -> dict[str, Any]:
	missing: list[str] = []
	checks = [
		("tender_name", bool((values.get("tender_name") or "").strip())),
		("contract_description", bool((values.get("contract_description") or "").strip())),
		("lotting_strategy", bool((values.get("lotting_strategy") or "").strip())),
		("reservation_setting", _reservation_complete(values)),
		(
			"tender_security_applicability",
			bool((values.get("tender_security_applicability") or "").strip()),
		),
		(
			"clarification_contact_email",
			bool(EMAIL_RE.match((values.get("clarification_contact_email") or "").strip())),
		),
		("alternative_tenders_allowed", values.get("alternative_tenders_allowed") is not None),
		("jv_allowed", values.get("jv_allowed") is not None),
		("pre_tender_meeting_required", values.get("pre_tender_meeting_required") is not None),
		("language_code", bool((values.get("language_code") or "").strip())),
		("currency_code", bool((values.get("currency_code") or "").strip())),
	]
	for field_key, ok in checks:
		if not ok:
			missing.append(REQUIRED_FIELD_LABELS[field_key])
	completed = REQUIRED_FIELD_TOTAL - len(missing)
	return {
		"completed": completed,
		"total": REQUIRED_FIELD_TOTAL,
		"missing_fields": missing,
		"percent": int(round((completed / REQUIRED_FIELD_TOTAL) * 100)),
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
		{"tender_std_instance": instance_name, "step_code": PROFILE_STEP_CODE},
	)
	if not step_name:
		return
	status = "COMPLETE" if complete else "IN_PROGRESS"
	frappe.db.set_value("Wizard Step Instance", step_name, "status", status)


def get_tender_profile(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	overview = build_configuration_overview(configuration_id)
	profile_doc = _ensure_profile_doc(instance.name)
	values = _serialize_profile_values(profile_doc)
	completion = compute_profile_completion(values)
	blockers, warnings = _latest_validation_counts(instance.name)
	return {
		"configuration_id": configuration_id,
		"title": overview.get("title"),
		"state_label": overview.get("state_label"),
		"completion_percent": overview.get("completion_percent"),
		"planning_package": overview.get("planning_package"),
		"procuring_entity": overview.get("procuring_entity"),
		"method": overview.get("method"),
		"validation": {
			"blockers": blockers,
			"warnings": warnings,
		},
		"std_template_version_label": overview.get("std_template_version_label"),
		"std_template_version_id": overview.get("std_template_version_id"),
		"profile": values,
		"completion": completion,
	}


def save_tender_profile(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	profile_doc = _ensure_profile_doc(instance.name)
	updates = {
		"tender_name": (payload.get("tender_name") or "").strip(),
		"contract_description": (payload.get("contract_description") or "").strip(),
		"clarification_contact_email": (payload.get("clarification_contact_email") or "").strip(),
		"lotting_strategy": (payload.get("lotting_strategy") or "").strip() or None,
		"reservation_applies": 1 if payload.get("reservation_applies") else 0,
		"reserved_group_code": (payload.get("reserved_group_code") or "").strip() or None,
		"tender_security_applicability": (payload.get("tender_security_applicability") or "").strip() or None,
		"alternative_tenders_allowed": 1 if payload.get("alternative_tenders_allowed") else 0,
		"jv_allowed": 1 if payload.get("jv_allowed") else 0,
		"pre_tender_meeting_required": 1 if payload.get("pre_tender_meeting_required") else 0,
	}
	if not updates["reservation_applies"]:
		updates["reserved_group_code"] = "NONE"
	profile_doc.update(updates)
	profile_doc.save(ignore_permissions=True)
	values = _serialize_profile_values(profile_doc)
	completion = compute_profile_completion(values)
	complete = completion["completed"] == REQUIRED_FIELD_TOTAL
	_update_step_status(instance.name, complete=complete)
	if not complete and instance.current_step_code == PROFILE_STEP_CODE:
		frappe.db.set_value(
			"Tender STD Instance",
			instance.name,
			{"current_step_code": PROFILE_STEP_CODE, "current_step_name": "Tender Profile"},
		)
	return get_tender_profile(configuration_id)
