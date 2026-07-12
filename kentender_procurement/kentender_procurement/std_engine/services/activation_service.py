# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Promote an STD Version to ACTIVE after readiness gates pass."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.audit.event_service import record_audit_event
from kentender_procurement.std_engine.constants import UI_MODE_ACTIVE_TEMPLATE
from kentender_procurement.std_engine.services.activation_readiness_service import (
	evaluate_activation_readiness,
	sync_activation_flags,
)
from kentender_procurement.std_engine.services.workflow_service import assert_transition_allowed


def activate_version(package_id: str) -> dict[str, Any]:
	"""Promote package to ACTIVE when readiness gates pass."""
	frappe.only_for(("System Manager", "Administrator"))
	package_id = (package_id or "").strip()
	if not package_id or not frappe.db.exists("STD Version", package_id):
		frappe.throw(_("STD Version not found."), title="STD_VERSION_NOT_FOUND")

	version = frappe.get_doc("STD Version", package_id)
	if (version.lifecycle_state or "").strip() == "ACTIVE":
		return _active_envelope(version)

	_assert_not_calibration_fixture(package_id)
	readiness = sync_activation_flags(package_id)
	if not readiness.get("activationAllowed"):
		frappe.throw(
			_("Activation blocked: unresolved readiness gate(s)."),
			title="STD_ACTIVATION_BLOCKED",
			exc=frappe.ValidationError,
		)

	assert_transition_allowed(package_id, "ACTIVE")
	version_hash = _compute_version_hash(package_id)
	now = datetime.now(timezone.utc).replace(tzinfo=None)

	metadata = _parse_metadata(version.metadata_json)
	metadata["version_hash"] = version_hash
	metadata["activated_at"] = now.isoformat()
	metadata["activated_by"] = frappe.session.user

	frappe.db.set_value(
		"STD Version",
		package_id,
		{
			"lifecycle_state": "ACTIVE",
			"activation_allowed": 1,
			"ui_mode": UI_MODE_ACTIVE_TEMPLATE,
			"is_immutable": 1,
			"metadata_json": json.dumps(metadata, sort_keys=True, default=str),
		},
		update_modified=False,
	)

	record_audit_event(
		package_id=package_id,
		event_type="STD_VERSION_ACTIVATED",
		object_type="STD Version",
		object_id=package_id,
		payload={"versionHash": version_hash, "activatedBy": frappe.session.user},
	)

	version.reload()
	return _active_envelope(version)


def assert_not_calibration_fixture_target(package_id: str) -> None:
	_assert_not_calibration_fixture(package_id)


def _assert_not_calibration_fixture(package_id: str) -> None:
	if frappe.db.exists(
		"STD Usage Binding",
		{
			"binding_key": f"FIXTURE-{package_id}",
			"fixture_source": "NSSF_CALIBRATION_FIXTURE",
		},
	):
		return
	binding = frappe.db.get_value(
		"STD Usage Binding",
		{"tender_ref": package_id, "fixture_source": "NSSF_CALIBRATION_FIXTURE"},
		"name",
	)
	if binding:
		frappe.throw(
			_("Calibration fixtures cannot be activated as master STD versions."),
			title="STD_FIXTURE_ACTIVATION_BLOCKED",
		)


def _compute_version_hash(package_id: str) -> str:
	import hashlib

	parts = [
		package_id,
		frappe.db.get_value("STD Version", package_id, "package_sha256") or "",
		str(frappe.db.count("STD Clause", {"package_id": package_id})),
		str(frappe.db.count("STD Parameter", {"package_id": package_id})),
	]
	return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _active_envelope(version) -> dict[str, Any]:
	metadata = _parse_metadata(version.metadata_json)
	readiness = evaluate_activation_readiness(version.package_id)
	return {
		"ok": True,
		"packageId": version.package_id,
		"lifecycleState": version.lifecycle_state,
		"activationAllowed": True,
		"uiMode": version.ui_mode,
		"versionHash": metadata.get("version_hash"),
		"readiness": readiness,
	}


def _parse_metadata(raw: str | None) -> dict[str, Any]:
	if not raw:
		return {}
	try:
		parsed = json.loads(raw)
	except json.JSONDecodeError:
		return {}
	return parsed if isinstance(parsed, dict) else {}
