# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Standard read API envelope for STD Engine."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

import frappe

from kentender_procurement.std_engine.constants import UI_MODE_READ_ONLY_INSPECTION
from kentender_procurement.std_engine.validation.validation_engine import get_validation_summary

ENVELOPE_KEYS = (
	"packageContext",
	"data",
	"pagination",
	"validationSummary",
	"audit",
)


def build_package_context(version: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	lifecycle_state = version.get("lifecycle_state") or ""
	ui_mode = version.get("ui_mode") or UI_MODE_READ_ONLY_INSPECTION
	activation_allowed = bool(int(version.get("activation_allowed") or 0))
	is_immutable = bool(int(version.get("is_immutable") or 0))
	return {
		"familyCode": version.get("family_code"),
		"versionCode": version.get("version_code"),
		"packageId": version.get("package_id"),
		"lifecycleState": lifecycle_state,
		"activationAllowed": activation_allowed,
		"packageQuality": version.get("package_quality"),
		"immutable": is_immutable,
		"uiMode": ui_mode,
		"canEdit": False,
		"canActivate": False,
	}


def build_audit_snapshot(package_id: str | None) -> dict[str, Any]:
	generated_at = datetime.now(timezone.utc).isoformat()
	if not package_id:
		return {"snapshotHash": "", "generatedAt": generated_at, "eventCount": 0}

	events = frappe.get_all(
		"STD Audit Event",
		filters={"package_id": package_id},
		fields=["event_key", "event_type", "occurred_at"],
		order_by="occurred_at desc",
		limit=100,
	)
	payload = [
		{
			"eventKey": row.get("event_key"),
			"eventType": row.get("event_type"),
			"occurredAt": str(row.get("occurred_at") or ""),
		}
		for row in events
	]
	canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
	snapshot_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest() if payload else ""
	return {
		"snapshotHash": snapshot_hash,
		"generatedAt": generated_at,
		"eventCount": len(events),
	}


def build_read_envelope(
	*,
	data: Any,
	package_context: dict[str, Any] | None = None,
	package_id: str | None = None,
	pagination: dict[str, Any] | None = None,
) -> dict[str, Any]:
	resolved_package_id = package_id or (package_context or {}).get("packageId")
	return {
		"packageContext": package_context,
		"data": data,
		"pagination": pagination,
		"validationSummary": get_validation_summary(resolved_package_id or ""),
		"audit": build_audit_snapshot(resolved_package_id),
	}


def build_error_envelope(error_code: str, message: str) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": error_code,
		"message": message,
		"packageContext": None,
		"data": None,
		"pagination": None,
		"validationSummary": {"blockers": 0, "warnings": 0, "info": 0},
		"audit": build_audit_snapshot(None),
	}
