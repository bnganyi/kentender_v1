# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Load NSSF ERP calibration fixture as tender-instance data only (CAL-NSSF-001)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import frappe

from kentender_procurement.std_engine.constants import (
	CANONICAL_PACKAGE_ID,
	FIXTURE_SOURCE_NSSF_CALIBRATION,
	NSSF_FIXTURE_CODE,
	NSSF_TENDER_REF,
)
from kentender_procurement.std_engine.paths import kentender_v1_root


def sample_data_dir() -> Path:
	return kentender_v1_root() / "docs" / "std-prod-impl" / "NSSF-Calibration" / "sample_data"


def load_nssf_calibration_fixture(*, force_reload: bool = False) -> dict[str, Any]:
	"""Import NSSF fixture metadata without creating master STD records."""
	frappe.set_user("Administrator")
	binding_key = f"FIXTURE-{NSSF_FIXTURE_CODE}"
	if frappe.db.exists("STD Usage Binding", binding_key) and not force_reload:
		return {
			"ok": True,
			"action": "existing",
			"bindingKey": binding_key,
			"fixtureCode": NSSF_FIXTURE_CODE,
		}

	manifest = _read_json(sample_data_dir() / "fixture_manifest.json")
	tds_values = _read_json(sample_data_dir() / "tds_values.json")
	requirements = _read_json(sample_data_dir() / "requirement_items.json")

	if not frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID):
		frappe.throw(
			f"Master STD {CANONICAL_PACKAGE_ID} must be imported before NSSF fixture load.",
			title="MASTER_STD_MISSING",
		)

	master = frappe.get_doc("STD Version", CANONICAL_PACKAGE_ID)
	payload = {
		"fixtureCode": NSSF_FIXTURE_CODE,
		"fixtureType": manifest.get("fixture_type"),
		"tenderRef": NSSF_TENDER_REF,
		"masterStdVersionCode": CANONICAL_PACKAGE_ID,
		"masterStdFamilyCode": master.family_code,
		"activationAllowed": False,
		"tdsValues": tds_values.get("records") or [],
		"requirementItems": requirements.get("records") or [],
		"contractId": "CAL-NSSF-001",
	}

	doc_dict = {
		"doctype": "STD Usage Binding",
		"package_id": CANONICAL_PACKAGE_ID,
		"family_code": master.family_code,
		"version_code": master.version_code,
		"binding_key": binding_key,
		"fixture_source": FIXTURE_SOURCE_NSSF_CALIBRATION,
		"tender_ref": NSSF_TENDER_REF,
		"binding_status": "FIXTURE_LOADED",
		"metadata_json": json.dumps(payload, sort_keys=True, default=str),
	}

	if frappe.db.exists("STD Usage Binding", binding_key):
		frappe.db.set_value(
			"STD Usage Binding",
			binding_key,
			{
				"binding_status": "FIXTURE_LOADED",
				"metadata_json": doc_dict["metadata_json"],
			},
			update_modified=False,
		)
		action = "reloaded"
	else:
		frappe.get_doc(doc_dict).insert(ignore_permissions=True)
		action = "created"

	frappe.db.commit()
	return {
		"ok": True,
		"action": action,
		"bindingKey": binding_key,
		"fixtureCode": NSSF_FIXTURE_CODE,
		"tenderRef": NSSF_TENDER_REF,
		"masterStdVersionCode": CANONICAL_PACKAGE_ID,
	}


def run(**kwargs: object) -> None:
	result = load_nssf_calibration_fixture(force_reload=bool(kwargs.get("force_reload", False)))
	print(json.dumps(result, indent=2, default=str))


def _read_json(path: Path) -> dict[str, Any]:
	if not path.is_file():
		frappe.throw(f"Missing NSSF sample data file: {path}", title="NSSF_SAMPLE_DATA_MISSING")
	with path.open(encoding="utf-8") as handle:
		return json.load(handle)
