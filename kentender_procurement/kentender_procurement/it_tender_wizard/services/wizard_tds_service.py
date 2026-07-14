# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Data Sheet step payload for ITW-04."""

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

TDS_STEP_CODE = "TDS"
FIELD_TOTAL = 15

FIELD_LABELS = {
	"procuring_entity_address": "Procuring Entity Address",
	"tender_number": "Tender Ref",
	"tender_name": "Tender Name",
	"alternative_tenders_allowed": "Alternative Tenders Allowed",
	"jv_max_members": "JV Members Cap",
	"local_sourcing_preference": "Local Sourcing Preference",
	"submission_deadline_at": "Submission Deadline",
	"opening_at": "Opening Date/Time",
	"clarification_contact_email": "Clarification Contact",
	"electronic_tenders_allowed": "Electronic Tenders Allowed",
	"envelope_marking": "Envelope Marking",
	"tender_security_amount": "Tender Security Amount",
	"tender_validity_days": "Validity (Days)",
	"security_issuer_type": "Issuer Type",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _dedupe_tds_docs(instance_name: str) -> str | None:
	rows = frappe.get_all(
		"Tender STD TDS",
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
		frappe.delete_doc("Tender STD TDS", row["name"], ignore_permissions=True)
	return keeper


def _tds_doc_name(instance_name: str) -> str | None:
	return _dedupe_tds_docs(instance_name)


def _profile_tender_name(instance_name: str) -> str:
	profile_name = frappe.db.get_value("Tender STD Profile", {"tender_std_instance": instance_name})
	if not profile_name:
		return ""
	return (frappe.db.get_value("Tender STD Profile", profile_name, "tender_name") or "").strip()


def _ensure_tds_doc(instance_name: str) -> frappe.model.document.Document:
	name = _tds_doc_name(instance_name)
	if name:
		doc = frappe.get_doc("Tender STD TDS", name)
		if not (doc.tender_name or "").strip():
			prefill = _profile_tender_name(instance_name)
			if prefill:
				doc.tender_name = prefill
				doc.save(ignore_permissions=True)
		return doc
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD TDS",
			"tender_std_instance": instance_name,
			"alternative_tenders_allowed": "NO",
			"envelope_marking": "ELECTRONIC_ONLY",
			"tender_name": _profile_tender_name(instance_name),
		}
	)
	try:
		doc.insert(ignore_permissions=True)
	except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
		frappe.db.rollback()
		name = _tds_doc_name(instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD TDS", name)
	return doc


def _empty_tds_values() -> dict[str, Any]:
	return {
		"procuring_entity_address": "",
		"tender_number": "",
		"tender_name": "",
		"alternative_tenders_allowed": "NO",
		"jv_max_members": None,
		"local_sourcing_preference": "",
		"submission_deadline_at": None,
		"opening_at": None,
		"clarification_contact_email": "",
		"electronic_tenders_allowed": 0,
		"envelope_marking": "ELECTRONIC_ONLY",
		"tender_security_amount": None,
		"tender_validity_days": None,
		"security_issuer_type": "",
	}


def _serialize_tds_values(doc) -> dict[str, Any]:
	if not doc:
		return _empty_tds_values()
	return {
		"procuring_entity_address": (doc.procuring_entity_address or "").strip(),
		"tender_number": (doc.tender_number or "").strip(),
		"tender_name": (doc.tender_name or "").strip(),
		"alternative_tenders_allowed": (doc.alternative_tenders_allowed or "NO").strip(),
		"jv_max_members": doc.jv_max_members,
		"local_sourcing_preference": (doc.local_sourcing_preference or "").strip(),
		"submission_deadline_at": doc.submission_deadline_at,
		"opening_at": doc.opening_at,
		"clarification_contact_email": (doc.clarification_contact_email or "").strip(),
		"electronic_tenders_allowed": int(doc.electronic_tenders_allowed or 0),
		"envelope_marking": (doc.envelope_marking or "ELECTRONIC_ONLY").strip(),
		"tender_security_amount": doc.tender_security_amount,
		"tender_validity_days": doc.tender_validity_days,
		"security_issuer_type": (doc.security_issuer_type or "").strip(),
	}


def compute_tds_completion(values: dict[str, Any]) -> dict[str, Any]:
	missing: list[str] = []
	checks = [
		("procuring_entity_address", bool((values.get("procuring_entity_address") or "").strip())),
		("tender_number", bool((values.get("tender_number") or "").strip())),
		("tender_name", bool((values.get("tender_name") or "").strip())),
		(
			"alternative_tenders_allowed",
			(values.get("alternative_tenders_allowed") or "").strip() in ("YES", "NO"),
		),
		("jv_max_members", values.get("jv_max_members") is not None),
		("local_sourcing_preference", bool((values.get("local_sourcing_preference") or "").strip())),
		("submission_deadline_at", bool(values.get("submission_deadline_at"))),
		("opening_at", bool(values.get("opening_at"))),
		(
			"clarification_contact_email",
			bool(EMAIL_RE.match((values.get("clarification_contact_email") or "").strip()))
			if (values.get("clarification_contact_email") or "").strip()
			else True,
		),
		("electronic_tenders_allowed", values.get("electronic_tenders_allowed") is not None),
		("envelope_marking", bool((values.get("envelope_marking") or "").strip())),
		(
			"tender_security_amount",
			values.get("tender_security_amount") is not None
			and float(values.get("tender_security_amount") or 0) > 0,
		),
		(
			"tender_validity_days",
			values.get("tender_validity_days") is not None and int(values.get("tender_validity_days") or 0) > 0,
		),
		("security_issuer_type", bool((values.get("security_issuer_type") or "").strip())),
	]
	for field_key, ok in checks:
		if not ok:
			missing.append(FIELD_LABELS[field_key])
	completed = FIELD_TOTAL - len(missing)
	return {
		"completed": completed,
		"total": FIELD_TOTAL,
		"missing_fields": missing,
		"percent": int(round((completed / FIELD_TOTAL) * 100)),
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
		{"tender_std_instance": instance_name, "step_code": TDS_STEP_CODE},
	)
	if not step_name:
		return
	status = "COMPLETE" if complete else "IN_PROGRESS"
	frappe.db.set_value("Wizard Step Instance", step_name, "status", status)


def _profile_security_required(instance_name: str) -> bool:
	applicability = frappe.db.get_value(
		"Tender STD Profile",
		{"tender_std_instance": instance_name},
		"tender_security_applicability",
	)
	return bool(applicability and applicability != "NONE")


def _validate_save_payload(instance_name: str, payload: dict[str, Any]) -> None:
	submission = payload.get("submission_deadline_at")
	opening = payload.get("opening_at")
	if not submission:
		frappe.throw("Submission deadline is required.")
	if submission and opening:
		sub_dt = frappe.utils.get_datetime(submission)
		open_dt = frappe.utils.get_datetime(opening)
		if open_dt < sub_dt:
			frappe.throw("Opening date/time cannot be before submission deadline.")
	validity = payload.get("tender_validity_days")
	if validity is not None and int(validity or 0) <= 0:
		frappe.throw("Tender validity days must be greater than zero.")
	amount = payload.get("tender_security_amount")
	if _profile_security_required(instance_name):
		if amount is None or float(amount or 0) <= 0:
			frappe.throw("Tender security amount must be greater than zero when security is required.")
	email = (payload.get("clarification_contact_email") or "").strip()
	if email and not EMAIL_RE.match(email):
		frappe.throw("Clarification contact must be a valid email address.")


def get_tds(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	overview = build_configuration_overview(configuration_id)
	tds_doc = _ensure_tds_doc(instance.name)
	values = _serialize_tds_values(tds_doc)
	completion = compute_tds_completion(values)
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
		"values": values,
		"completion": completion,
	}


def save_tds(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	tds_doc = _ensure_tds_doc(instance.name)
	updates = {
		"procuring_entity_address": (payload.get("procuring_entity_address") or "").strip(),
		"tender_number": (payload.get("tender_number") or "").strip(),
		"tender_name": (payload.get("tender_name") or "").strip(),
		"alternative_tenders_allowed": (payload.get("alternative_tenders_allowed") or "NO").strip() or "NO",
		"jv_max_members": payload.get("jv_max_members"),
		"local_sourcing_preference": (payload.get("local_sourcing_preference") or "").strip() or None,
		"submission_deadline_at": payload.get("submission_deadline_at") or None,
		"opening_at": payload.get("opening_at") or None,
		"clarification_contact_email": (payload.get("clarification_contact_email") or "").strip(),
		"electronic_tenders_allowed": 1 if payload.get("electronic_tenders_allowed") else 0,
		"tender_security_amount": payload.get("tender_security_amount"),
		"tender_validity_days": payload.get("tender_validity_days"),
		"security_issuer_type": (payload.get("security_issuer_type") or "").strip() or None,
	}
	if updates["jv_max_members"] in ("", None):
		updates["jv_max_members"] = None
	else:
		updates["jv_max_members"] = int(updates["jv_max_members"])
	if updates["tender_validity_days"] in ("", None):
		updates["tender_validity_days"] = None
	else:
		updates["tender_validity_days"] = int(updates["tender_validity_days"])
	if updates["tender_security_amount"] in ("", None):
		updates["tender_security_amount"] = None
	else:
		updates["tender_security_amount"] = float(updates["tender_security_amount"])
	_validate_save_payload(instance.name, updates)
	tds_doc.update(updates)
	tds_doc.save(ignore_permissions=True)
	values = _serialize_tds_values(tds_doc)
	completion = compute_tds_completion(values)
	complete = completion["completed"] == FIELD_TOTAL
	_update_step_status(instance.name, complete=complete)
	return get_tds(configuration_id)
