# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bind consumers (packages, fixtures, tenders) to STD Versions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.constants import (
	FIXTURE_SOURCE_CONSUMER_BINDING,
	FIXTURE_SOURCE_NSSF_CALIBRATION,
	NSSF_FIXTURE_CODE,
)
from kentender_procurement.std_engine.services.activation_readiness_service import (
	evaluate_activation_readiness,
)


def _site_allows_test_binding() -> bool:
	try:
		site_config = frappe.get_site_config()
	except Exception:
		site_config = {}
	return bool(site_config.get("std_engine_allow_test_binding"))


def assert_version_is_bindable(
	package_id: str,
	*,
	simulate_active_for_test: bool = False,
) -> dict[str, Any]:
	package_id = (package_id or "").strip()
	if not package_id or not frappe.db.exists("STD Version", package_id):
		frappe.throw(_("STD Version not found."), title="STD_VERSION_NOT_FOUND")

	version = frappe.get_doc("STD Version", package_id)
	lifecycle = (version.lifecycle_state or "").strip()
	readiness = evaluate_activation_readiness(package_id)

	if lifecycle == "ACTIVE":
		return {"bindable": True, "mode": "ACTIVE", "readiness": readiness}

	allow_test = _site_allows_test_binding() or bool(simulate_active_for_test)
	if allow_test and readiness.get("activationAllowed"):
		return {"bindable": True, "mode": "TEST_MODE", "readiness": readiness}

	frappe.throw(
		_("STD Version must be ACTIVE or test-mode bindable with readiness gates passed."),
		title="STD_BIND_BLOCKED",
		exc=frappe.ValidationError,
	)


def bind_consumer(
	package_id: str,
	*,
	consumer_type: str,
	consumer_code: str,
	journey_code: str | None = None,
	simulate_active_for_test: bool = False,
	metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
	bindability = assert_version_is_bindable(
		package_id,
		simulate_active_for_test=simulate_active_for_test,
	)
	version = frappe.get_doc("STD Version", package_id)
	consumer_type = (consumer_type or "").strip().upper()
	consumer_code = (consumer_code or "").strip()
	if not consumer_code:
		frappe.throw(_("consumer_code is required."), title="STD_BIND_INVALID")

	binding_key = f"BIND-{consumer_type}-{consumer_code}-{package_id}"
	now = datetime.now(timezone.utc).replace(tzinfo=None)
	version_meta = {}
	if version.metadata_json:
		try:
			version_meta = json.loads(version.metadata_json)
		except json.JSONDecodeError:
			version_meta = {}

	payload = {
		"consumerType": consumer_type,
		"consumerCode": consumer_code,
		"journeyCode": journey_code,
		"bindMode": bindability.get("mode"),
		"versionHash": version_meta.get("version_hash") or version.package_sha256,
		"boundAt": now.isoformat(),
		"boundBy": frappe.session.user,
		**(metadata or {}),
	}

	doc_dict = {
		"doctype": "STD Usage Binding",
		"package_id": package_id,
		"family_code": version.family_code,
		"version_code": version.version_code,
		"binding_key": binding_key,
		"fixture_source": FIXTURE_SOURCE_CONSUMER_BINDING,
		"tender_ref": consumer_code,
		"binding_status": "BOUND",
		"metadata_json": json.dumps(payload, sort_keys=True, default=str),
	}

	if frappe.db.exists("STD Usage Binding", binding_key):
		frappe.db.set_value(
			"STD Usage Binding",
			binding_key,
			{
				"binding_status": "BOUND",
				"metadata_json": doc_dict["metadata_json"],
			},
			update_modified=False,
		)
		action = "updated"
	else:
		frappe.get_doc(doc_dict).insert(ignore_permissions=True)
		action = "created"

	return {
		"ok": True,
		"action": action,
		"bindingKey": binding_key,
		"packageId": package_id,
		"consumerType": consumer_type,
		"consumerCode": consumer_code,
		"bindMode": bindability.get("mode"),
		"versionHash": payload.get("versionHash"),
	}


def bind_nssf_calibration_fixture(
	package_id: str,
	*,
	simulate_active_for_test: bool = False,
) -> dict[str, Any]:
	"""Golden proof CAL-NSSF-002 — bind NSSF fixture to master STD."""
	assert_version_is_bindable(package_id, simulate_active_for_test=simulate_active_for_test)
	if not frappe.db.exists("STD Usage Binding", f"FIXTURE-{NSSF_FIXTURE_CODE}"):
		frappe.throw(
			_("NSSF calibration fixture not loaded. Run nssf_calibration_fixture_loader first."),
			title="NSSF_FIXTURE_MISSING",
		)
	return bind_consumer(
		package_id,
		consumer_type="CALIBRATION_FIXTURE",
		consumer_code=NSSF_FIXTURE_CODE,
		simulate_active_for_test=simulate_active_for_test,
		metadata={
			"fixtureCode": NSSF_FIXTURE_CODE,
			"masterStdVersionCode": package_id,
			"contractId": "CAL-NSSF-002",
		},
	)


def assert_std_template_bindable(required_std_template_version_code: str) -> dict[str, Any]:
	code = (required_std_template_version_code or "").strip()
	return assert_version_is_bindable(code, simulate_active_for_test=_site_allows_test_binding())
