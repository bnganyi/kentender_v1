# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Idempotent E1 NSSF PoC seed: fixture 09 → TCFG-E1-NSSF-ERP + schema 10 artifact."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, nowdate

from kentender_procurement.procurement_planning.pp2_constants import PKG_APPROVED
from kentender_procurement.tender_configurations.constants import (
	STATUS_APPROVED_FOR_PREVIEW,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	steps_state_all_complete,
)
from kentender_procurement.tender_configurations.services.e1_nssf_fixture_mapper import (
	map_all_cfg_blobs,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
)
from kentender_procurement.tender_configurations.services.schema_compiler import (
	compile_schema_from_mapped,
)

SEED_PREFIX = "TCFG-E1-NSSF"
PACKAGE_CODE = f"{SEED_PREFIX}-PKG"
CONFIG_REF = f"{SEED_PREFIX}-ERP"
PE_CODE = f"{SEED_PREFIX}-PE"


def _clear_seed() -> None:
	# Clear PoC electronic bids first (link to configuration)
	if frappe.db.exists("DocType", "Electronic Bid Submission"):
		bid_names = frappe.get_all(
			"Electronic Bid Submission",
			filters={"configuration": ("like", f"{SEED_PREFIX}%")},
			pluck="name",
		)
		for bid in bid_names:
			frappe.delete_doc("Electronic Bid Submission", bid, force=True, ignore_permissions=True)

	config_names = set(
		frappe.get_all(
			"Tender Configuration",
			filters={"configuration_ref": ("like", f"{SEED_PREFIX}%")},
			pluck="name",
		)
	)
	config_names |= set(
		frappe.get_all(
			"Tender Configuration",
			filters={"procurement_package": ("like", f"{SEED_PREFIX}%")},
			pluck="name",
		)
	)
	config_names |= set(
		frappe.get_all(
			"Tender Configuration",
			filters={"procurement_package_ref": ("like", f"{SEED_PREFIX}%")},
			pluck="name",
		)
	)
	for name in config_names:
		frappe.delete_doc("Tender Configuration", name, force=True, ignore_permissions=True)

	if frappe.db.exists("Procurement Package", PACKAGE_CODE):
		frappe.delete_doc("Procurement Package", PACKAGE_CODE, force=True, ignore_permissions=True)


def _ensure_pe(entity_name: str) -> str:
	if not frappe.db.exists("Procuring Entity", PE_CODE):
		try:
			frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": PE_CODE,
					"entity_name": entity_name or "NSSF Staff Pension Scheme",
				}
			).insert(ignore_permissions=True, ignore_mandatory=True)
		except Exception:
			existing = frappe.get_all("Procuring Entity", limit=1, pluck="name")
			return existing[0] if existing else PE_CODE
	else:
		frappe.db.set_value(
			"Procuring Entity",
			PE_CODE,
			{"entity_name": entity_name or "NSSF Staff Pension Scheme"},
		)
	return PE_CODE


def _insert_package(*, title: str, entity: str) -> str:
	if frappe.db.exists("Procurement Package", PACKAGE_CODE):
		frappe.db.set_value(
			"Procurement Package",
			PACKAGE_CODE,
			{
				"package_name": title,
				"status": PKG_APPROVED,
				"procurement_method": "Open Tender",
				"procuring_entity_code": entity,
				"required_std_category": "Information Technology",
				"procurement_category": "Services",
				"is_active": 1,
				"approved_at": nowdate(),
			},
		)
		return PACKAGE_CODE

	doc = frappe.get_doc(
		{
			"doctype": "Procurement Package",
			"package_code": PACKAGE_CODE,
			"package_name": title,
			"status": PKG_APPROVED,
			"procurement_method": "Open Tender",
			"contract_type": "Fixed Price",
			"procuring_entity_code": entity,
			"required_std_category": "Information Technology",
			"procurement_category": "Services",
			"currency": "KES",
			"is_active": 1,
			"approved_at": nowdate(),
			"method_override_flag": 0,
		}
	)
	doc.flags.ignore_validate = True
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	frappe.db.set_value(
		"Procurement Package",
		doc.name,
		{
			"status": PKG_APPROVED,
			"approved_at": nowdate(),
			"package_code": PACKAGE_CODE,
			"is_active": 1,
		},
	)
	return doc.name


def _insert_config(
	*,
	package_name: str,
	title: str,
	std_version: str,
	entity_code: str,
	entity_name: str,
	short_scope_summary: str,
	configuration_note: str,
) -> str:
	if frappe.db.exists("Tender Configuration", CONFIG_REF):
		frappe.delete_doc("Tender Configuration", CONFIG_REF, force=True, ignore_permissions=True)

	doc = frappe.get_doc(
		{
			"doctype": "Tender Configuration",
			"configuration_ref": CONFIG_REF,
			"tender_title": title,
			"status": STATUS_APPROVED_FOR_PREVIEW,
			"procurement_package": package_name,
			"procurement_package_ref": PACKAGE_CODE,
			"package_title": title,
			"procuring_entity_name": entity_name,
			"procuring_entity_code": entity_code,
			"procurement_method": "Open Tender",
			"std_family_key": "IT",
			"std_family_label": "Information Technology",
			"std_version": std_version,
			"std_document_label": "IT Standard Tender Document — April 2022",
			"short_scope_summary": short_scope_summary,
			"lot_structure": "Single lot",
			"configuration_note": configuration_note,
			"blocker_count": 0,
			"warning_count": 0,
			"steps_state": steps_state_all_complete(),
			"approval_date": nowdate(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _apply_cfg_blobs(
	configuration_id: str,
	mapped: dict[str, Any],
	*,
	std_version: str,
) -> dict[str, Any]:
	"""Persist mapped CFG blobs + compiled bidder schema."""
	schema = compile_schema_from_mapped(
		mapped,
		configuration_id=configuration_id,
		std_version=std_version,
	)
	# AUDIT_ONLY — never rendered into bidder-facing preview HTML/PDF.
	artifact = schema.setdefault("_kentender_artifact", {})
	if isinstance(artifact, dict):
		artifact["poc_audit_notes"] = mapped.get("poc_audit_notes") or {}
	values: dict[str, Any] = {
		"tds_values": json.dumps(mapped["tds_values"]),
		"it_requirements": json.dumps(mapped["it_requirements"]),
		"implementation_schedule": json.dumps(mapped["implementation_schedule"]),
		"system_inventory": json.dumps(mapped["system_inventory"]),
		"price_schedule": json.dumps(mapped["price_schedule"]),
		"evaluation_setup": json.dumps(mapped["evaluation_setup"]),
		"forms_and_evidence": json.dumps(mapped["forms_and_evidence"]),
		"contract_values": json.dumps(mapped["contract_values"]),
		"bidder_submission_schema": json.dumps(schema),
	}
	frappe.db.set_value(
		"Tender Configuration",
		configuration_id,
		values,
		update_modified=False,
	)
	return schema


def seed_e1_nssf_tender_configuration(*, clear: bool = True) -> dict[str, Any]:
	"""Load E1 NSSF PoC configuration. Idempotent when clear=True."""
	frappe.set_user("Administrator")
	if clear:
		_clear_seed()

	mapped = map_all_cfg_blobs()
	profile = mapped["profile"]
	std_ensure = ensure_active_canonical_ppra_it_std(force_reimport=False)
	std_id = cstr(std_ensure.get("packageId") or CANONICAL_PACKAGE_ID)
	entity = _ensure_pe(profile.get("procuring_entity_name") or "NSSF Staff Pension Scheme")
	entity_name = (
		frappe.db.get_value("Procuring Entity", entity, "entity_name")
		or profile.get("procuring_entity_name")
		or "NSSF Staff Pension Scheme"
	)
	title = profile.get("tender_title") or "NSSF SPS ERP System"

	package_name = _insert_package(title=title[:140], entity=entity)
	cfg_id = _insert_config(
		package_name=package_name,
		title=title[:140],
		std_version=std_id,
		entity_code=entity,
		entity_name=entity_name,
		short_scope_summary=cstr_trunc(profile.get("short_scope_summary"), 500),
		configuration_note=cstr_trunc(profile.get("configuration_note"), 1000),
	)
	schema = _apply_cfg_blobs(cfg_id, mapped, std_version=std_id)
	frappe.db.commit()

	from kentender_procurement.tender_configurations.services.readiness import (
		run_readiness_check,
	)

	readiness = run_readiness_check(cfg_id)
	frappe.db.commit()

	return {
		"configuration_id": cfg_id,
		"configuration_ref": CONFIG_REF,
		"package_id": package_name,
		"package_code": PACKAGE_CODE,
		"std_version": std_id,
		"counts": mapped["counts"],
		"seed_prefix": SEED_PREFIX,
		"schema_hash": schema.get("schema_hash"),
		"bidder_workspace_route": f"/app/it-electronic-bidder-workspace/{cfg_id}",
		"readiness": {
			"overall_result": readiness.get("overall_result"),
			"blocker_count": readiness.get("blocker_count"),
			"warning_count": readiness.get("warning_count"),
		},
	}


def cstr_trunc(val: Any, n: int) -> str:
	text = str(val or "").strip()
	return text[:n] if text else ""
