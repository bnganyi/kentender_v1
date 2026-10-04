# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD template governance — baseline snapshot + hash (doc 7 §13.5, §18, STD-GOV-009).

Persists ``latest_governance_snapshot_*`` on ``STD Template`` and appends ``EVT_SNAPSHOT_GENERATED``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_procurement.tender_management.services.std_template_governance import (
	EVT_SNAPSHOT_GENERATED,
	canonicalize_std_package_payload,
)
from kentender_procurement.tender_management.services.std_template_governance_events import (
	write_std_template_lifecycle_event,
)

ROLE_SYSTEM_MANAGER = "System Manager"
ROLE_STD_TEMPLATE_ADMINISTRATOR = "STD Template Administrator"
ROLE_STD_TEMPLATE_AUDITOR = "STD Template Auditor"
ROLES_SNAPSHOT = frozenset(
	{ROLE_SYSTEM_MANAGER, ROLE_STD_TEMPLATE_ADMINISTRATOR, ROLE_STD_TEMPLATE_AUDITOR}
)


def _guest_blocked() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _assert_can_generate_snapshot() -> None:
	_guest_blocked()
	if frappe.session.user == "Administrator":
		return
	if ROLES_SNAPSHOT.intersection(frappe.get_roles()):
		return
	frappe.throw(_("Not permitted"), frappe.PermissionError)


def _scalar(v: Any) -> Any:
	if v is None:
		return None
	if hasattr(v, "isoformat"):
		return v.isoformat()
	return v


def _pick(doc: Any, keys: tuple[str, ...]) -> dict[str, Any]:
	return {k: _scalar(doc.get(k)) for k in keys}


def _parse_json_field(raw: str | None) -> Any:
	if not raw or not str(raw).strip():
		return None
	try:
		return json.loads(raw)
	except json.JSONDecodeError:
		return {"_parse_error": "invalid_json"}


def _row_get(row: Any, key: str) -> Any:
	if isinstance(row, dict):
		return row.get(key)
	return getattr(row, key, None)


def _lifecycle_events_payload(doc: Any) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for row in sorted(
		doc.get("lifecycle_events") or [],
		key=lambda r: (str(_row_get(r, "event_at") or ""), int(_row_get(r, "idx") or 0)),
	):
		out.append(
			{
				"event_code": _row_get(row, "event_code"),
				"event_type": _row_get(row, "event_type"),
				"event_at": _scalar(_row_get(row, "event_at")),
				"from_status": _row_get(row, "from_status"),
				"to_status": _row_get(row, "to_status"),
				"actor": _row_get(row, "actor"),
			}
		)
	return out


def _build_snapshot_dict(doc: Any, snapshot_type: str) -> dict[str, Any]:
	"""Assemble doc 7 §18 top-level keys (deterministic key order via ``canonicalize``)."""
	std_template = _pick(
		doc,
		(
			"template_code",
			"template_title",
			"template_name",
			"template_short_name",
			"authority",
			"country",
			"procurement_category",
			"procurement_method_profile",
			"template_family",
			"version_label",
			"template_version",
			"package_version",
			"is_governed_version",
			"status",
			"allowed_for_import",
			"allowed_for_tender_creation",
			"imported_at",
			"imported_by",
		),
	)

	source_authority = _pick(
		doc,
		(
			"source_authority",
			"source_document_code",
			"source_file_name",
			"source_file_hash",
			"source_document_title",
			"source_effective_date",
			"source_url",
			"source_notes",
			"import_source_type",
			"import_batch_id",
		),
	)

	package = _pick(
		doc,
		(
			"package_hash",
			"package_hash_algorithm",
			"package_size_bytes",
			"package_file_reference",
			"canonicalization_version",
			"payload_locked",
		),
	)
	package["package_json"] = _parse_json_field(doc.get("package_json"))
	package["manifest_json"] = _parse_json_field(doc.get("manifest_json"))

	lifecycle = _pick(
		doc,
		(
			"lifecycle_status",
			"previous_lifecycle_status",
			"status_changed_at",
			"status_changed_by",
			"status_reason",
			"is_suspended",
			"is_historical",
			"suspended_by",
			"suspended_at",
			"suspension_reason",
			"reinstated_by",
			"reinstated_at",
			"reinstatement_reason",
			"retired_by",
			"retired_at",
			"retirement_reason",
		),
	)

	validation = _pick(
		doc,
		(
			"latest_validation_status",
			"latest_validation_run_id",
			"latest_validation_at",
			"latest_validation_by",
			"latest_validation_package_hash",
			"latest_validation_result_json",
			"critical_finding_count",
			"warning_finding_count",
			"info_finding_count",
			"validation_is_current",
		),
	)

	approval = _pick(
		doc,
		(
			"submitted_for_approval_by",
			"submitted_for_approval_at",
			"submission_comment",
			"reviewed_by",
			"reviewed_at",
			"review_comment",
			"approved_by",
			"approved_at",
			"approval_decision",
			"approval_comments",
			"approval_validation_run_id",
			"approval_package_hash",
			"approval_override_used",
			"approval_override_reason",
		),
	)

	activation = _pick(
		doc,
		(
			"activated_by",
			"activated_at",
			"activation_reason",
			"activation_approval_reference",
			"activation_package_hash",
			"active_from",
			"active_until",
		),
	)

	versioning = _pick(
		doc,
		(
			"supersedes_template",
			"superseded_by_template",
			"superseded_by",
			"superseded_at",
			"supersession_reason",
			"supersession_effective_date",
			"is_default_active_version",
			"active_profile_key",
		),
	)

	usage = _pick(
		doc,
		(
			"tender_usage_count",
			"first_used_at",
			"last_used_at",
			"locked_due_to_usage",
			"mutation_blocked",
			"delete_blocked",
		),
	)
	usage["usage_summary"] = _parse_json_field(doc.get("usage_summary_json"))

	technical_summary: dict[str, Any] = {
		"governance_notes": _pick(
			doc,
			(
				"governance_notes",
				"correction_notes",
				"internal_admin_notes",
				"legal_review_notes",
			),
		),
		"validation_findings_count": len(doc.get("validation_findings") or []),
		"template_usage_count": len(doc.get("template_usage") or []),
	}

	return {
		"snapshot_type": snapshot_type,
		"snapshot_version": "V1",
		"generated_at": now_datetime().isoformat(),
		"generated_by": frappe.session.user,
		"std_template": std_template,
		"source_authority": source_authority,
		"package": package,
		"lifecycle": lifecycle,
		"validation": validation,
		"approval": approval,
		"activation": activation,
		"versioning": versioning,
		"usage": usage,
		"mappings": [],
		"events": _lifecycle_events_payload(doc),
		"technical_summary": technical_summary,
	}


def _snapshot_hash(snapshot: dict[str, Any]) -> str:
	body = canonicalize_std_package_payload(snapshot)
	return hashlib.sha256(body.encode("utf-8")).hexdigest()


def generate_std_template_governance_snapshot(
	std_template: str,
	snapshot_type: str = "STD_TEMPLATE_GOVERNANCE_BASELINE",
) -> dict[str, Any]:
	"""Build §18 JSON, SHA-256 hash, persist on ``STD Template``, emit ``EVT_SNAPSHOT_GENERATED``."""
	_assert_can_generate_snapshot()
	doc = frappe.get_doc("STD Template", std_template)

	snapshot = _build_snapshot_dict(doc, snapshot_type=snapshot_type)
	snap_hash = _snapshot_hash(snapshot)
	snap_json = canonicalize_std_package_payload(snapshot)

	doc.latest_governance_snapshot_json = snap_json
	doc.latest_governance_snapshot_hash = snap_hash
	doc.latest_governance_snapshot_at = now_datetime()
	doc.latest_governance_snapshot_by = frappe.session.user

	write_std_template_lifecycle_event(
		doc,
		EVT_SNAPSHOT_GENERATED,
		"governance",
		{
			"snapshot_type": snapshot_type,
			"snapshot_hash": snap_hash,
		},
		from_status=doc.lifecycle_status,
		save=False,
	)
	doc.save(ignore_permissions=True)

	return {
		"ok": True,
		"std_template": doc.name,
		"snapshot_type": snapshot_type,
		"snapshot_hash": snap_hash,
		"snapshot": snapshot,
	}
