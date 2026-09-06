# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Idempotent E1 NSSF PoC seed: fixture 09 → TCFG-E1-NSSF-ERP + schema 10 artifact."""

from __future__ import annotations

import json
from typing import Any

import frappe

def _pp2_pkg_available() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))

from frappe.utils import cstr, nowdate

PKG_APPROVED = "Approved"  # PP2 Package DocType retired
from kentender_procurement.tender_configurations.constants import (
	STATUS_APPROVED_FOR_PREVIEW,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	steps_state_all_complete,
)
from kentender_procurement.tender_configurations.services.e1_nssf_fixture_mapper import (
	map_all_cfg_blobs,
)
from kentender_procurement.tender_configurations.constants import CANONICAL_PACKAGE_ID
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

	if (_pp2_pkg_available() and frappe.db.exists("Procurement Package"), PACKAGE_CODE):
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
	if (_pp2_pkg_available() and frappe.db.exists("Procurement Package"), PACKAGE_CODE):
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


def _scc_value(row: dict[str, Any]) -> str:
	return cstr(
		row.get("value_or_obligation")
		or row.get("source_value")
		or row.get("value")
		or row.get("configured_value")
		or ""
	).strip()


def _complete_cfg09_for_readiness(configuration_id: str) -> None:
	"""Bind STD parameter codes and fill required CFG-09 / TDS values for readiness.

	Fixture 09 labels alone no longer satisfy contract_parameter_readiness (matches by
	parameter_code / readiness_parameter_id). Gate-ready seeds must complete this step.
	"""
	from kentender_procurement.tender_configurations.services.contract_parameter_readiness import (
		ensure_std_declared_contract_values,
	)

	doc = frappe.get_doc("Tender Configuration", configuration_id)
	try:
		cv_blob = json.loads(doc.contract_values or "{}")
	except (TypeError, ValueError):
		cv_blob = {}
	if not isinstance(cv_blob, dict):
		cv_blob = {}
	existing = [r for r in (cv_blob.get("contract_values") or []) if isinstance(r, dict)]
	merged = ensure_std_declared_contract_values(doc, existing)

	defaults = {
		"payment": (
			"Milestone payments per SCC: 30% on contract signature, "
			"40% on UAT acceptance, 30% on final acceptance."
		),
		"warranty": (
			"Twelve-month warranty after go-live; defects liability aligned to "
			"Phase 2 support; performance security valid through warranty plus 60 days."
		),
		"performance_security": "10% of the Contract Price as an unconditional bank guarantee.",
		"sla": (
			"Severity-1 response within 4 hours; Severity-2 next business day; "
			"monthly uptime target 99.5%."
		),
	}
	present_pids = {
		cstr(r.get("readiness_parameter_id") or "").strip()
		for r in merged
		if cstr(r.get("readiness_parameter_id") or "").strip()
	}
	for row in merged:
		pid = cstr(row.get("readiness_parameter_id") or "").strip()
		if pid in defaults and not _scc_value(row):
			row["value_or_obligation"] = defaults[pid]
			row["value"] = defaults[pid]
			row["source_value"] = defaults[pid]
			if not cstr(row.get("source_screen") or "").strip():
				row["source_screen"] = "User entered"
			if not cstr(row.get("contract_location") or "").strip():
				row["contract_location"] = "Special Conditions of Contract"
			if not cstr(row.get("category") or "").strip():
				row["category"] = "SCC Value"

	# SLA is applicability-gated; NSSF requirements mention SLA so a bound row is required.
	if "sla" not in present_pids:
		merged.append(
			{
				"contract_value_id": "SCC-SLA-01",
				"item_label": "SLA / defect response",
				"category": "SCC Value",
				"readiness_parameter_id": "sla",
				"parameter_code": "IT-SCC-054",
				"source_screen": "User entered",
				"source_item_label": "SLA",
				"source_value": defaults["sla"],
				"contract_location": "Special Conditions of Contract",
				"value_or_obligation": defaults["sla"],
				"value": defaults["sla"],
				"editable_here": 1,
			}
		)

	try:
		tds = json.loads(doc.tds_values or "{}")
	except (TypeError, ValueError):
		tds = {}
	if not isinstance(tds, dict):
		tds = {}
	if not cstr(tds.get("performance_security") or tds.get("performance_security_percent") or "").strip():
		tds["performance_security_percent"] = "10"
		tds["performance_security"] = "10% of the Contract Price"

	frappe.db.set_value(
		"Tender Configuration",
		configuration_id,
		{
			"contract_values": json.dumps({"contract_values": merged}, ensure_ascii=False),
			"tds_values": json.dumps(tds, ensure_ascii=False),
		},
		update_modified=False,
	)


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
	from kentender_procurement.tender_configurations.seed.lean_technical_proposal import (
		FIXTURE_FULL as TP_FIXTURE_FULL,
		merge_technical_proposal_into_evaluation,
	)

	ev_setup = mapped.get("evaluation_setup") if isinstance(mapped.get("evaluation_setup"), dict) else {}
	ev_setup = merge_technical_proposal_into_evaluation(ev_setup, fixture=TP_FIXTURE_FULL)
	values: dict[str, Any] = {
		"tds_values": json.dumps(mapped["tds_values"]),
		"it_requirements": json.dumps(mapped["it_requirements"]),
		"implementation_schedule": json.dumps(mapped["implementation_schedule"]),
		"system_inventory": json.dumps(mapped["system_inventory"]),
		"price_schedule": json.dumps(mapped["price_schedule"]),
		"evaluation_setup": json.dumps(ev_setup),
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
	_complete_cfg09_for_readiness(configuration_id)
	return schema


def _clear_publication_artifacts() -> None:
	"""Remove NSSF publication + confirmed packages linked to this seed prefix."""
	pub_names = frappe.get_all(
		"IT Tender Publication Record",
		filters={"configuration_ref": ("like", f"{SEED_PREFIX}%")},
		pluck="name",
	)
	pub_names += frappe.get_all(
		"IT Tender Publication Record",
		filters={"configuration": ("like", f"{SEED_PREFIX}%")},
		pluck="name",
	)
	for name in set(pub_names):
		frappe.delete_doc("IT Tender Publication Record", name, force=True, ignore_permissions=True)

	pkg_names = frappe.get_all(
		"Confirmed Tender Document Package",
		filters={"configuration_ref": ("like", f"{SEED_PREFIX}%")},
		pluck="name",
	)
	for name in pkg_names:
		frappe.delete_doc(
			"Confirmed Tender Document Package", name, force=True, ignore_permissions=True
		)


def seed_e1_nssf_tender_configuration(*, clear: bool = True) -> dict[str, Any]:
	"""Load E1 NSSF PoC configuration. Idempotent when clear=True."""
	frappe.set_user("Administrator")
	if clear:
		_clear_publication_artifacts()
		_clear_seed()

	mapped = map_all_cfg_blobs()
	profile = mapped["profile"]
	# STD Engine retired 2026-09-05 — no package to activate; std_version is a label.
	std_id = CANONICAL_PACKAGE_ID
	entity = _ensure_pe(profile.get("procuring_entity_name") or "NSSF Staff Pension Scheme")
	entity_name = (
		frappe.db.get_value("Procuring Entity", entity, "entity_name")
		or profile.get("procuring_entity_name")
		or "NSSF Staff Pension Scheme"
	)
	title = cstr(profile.get("tender_title") or "NSSF SPS ERP System").strip()
	# CFG-01 readiness warns when title length > 120; keep a clear short display title.
	display_title = (
		title
		if len(title) <= 120
		else "NSSF SPS Enterprise Resource Planning (ERP) System"
	)
	scope = cstr_trunc(profile.get("short_scope_summary"), 500) or title
	if len(scope.split()) < 6:
		scope = (
			f"{display_title}. Supply, installation, configuration and maintenance "
			"of an ERP system for NSSF Staff Pension Scheme."
		)

	package_name = _insert_package(title=display_title[:140], entity=entity)
	cfg_id = _insert_config(
		package_name=package_name,
		title=display_title[:140],
		std_version=std_id,
		entity_code=entity,
		entity_name=entity_name,
		short_scope_summary=scope,
		configuration_note=cstr_trunc(
			profile.get("configuration_note") or title, 1000
		),
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


def publish_e1_nssf_with_electronic_template(*, clear: bool = True) -> dict[str, Any]:
	"""Seed NSSF config, confirm package, publish with lean electronic template snapshot."""
	from frappe.utils import add_to_date, now_datetime

	from kentender_procurement.tender_configurations.services.document_preview import (
		confirm_document_preview,
		generate_document_preview,
	)
	from kentender_procurement.tender_configurations.services.publication_setup import (
		publish_tender_for_development_preview,
		save_publication_setup,
	)

	seeded = seed_e1_nssf_tender_configuration(clear=clear)
	cfg_id = seeded["configuration_id"]
	# F0 applicable set for NSSF lean path: no lots, tender security required.
	# Fixture mapper leaves security "No"; override here (not in the template file).
	import json as _json

	tds_raw = frappe.db.get_value("Tender Configuration", cfg_id, "tds_values")
	try:
		tds = _json.loads(tds_raw) if isinstance(tds_raw, str) else (tds_raw or {})
	except (TypeError, ValueError):
		tds = {}
	if not isinstance(tds, dict):
		tds = {}
	tds["tender_security_required"] = "Yes"
	if cstr(tds.get("tender_security_type") or "") in ("", "Not Required"):
		tds["tender_security_type"] = "Bank Guarantee"
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{"tds_values": _json.dumps(tds, ensure_ascii=False)},
		update_modified=False,
	)
	frappe.db.commit()

	gen = generate_document_preview(cfg_id)
	if cstr(gen.get("preview_status")) != "Generated":
		frappe.throw(
			frappe._("NSSF document preview failed: {0}").format(gen.get("render_exception")),
			title="NSSF_SEED_PREVIEW",
		)
	conf = confirm_document_preview(cfg_id, {"confirm_ready_for_handoff": 1})
	pub_id = conf["publication_id"]
	now = now_datetime()
	save_publication_setup(
		pub_id,
		{
			"publication_mode": "immediate",
			"publication_datetime": str(now),
			"tender_notice": "NSSF SPS ERP — lean electronic STD publication.",
			"clarification_deadline": str(add_to_date(now, days=2)),
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=15, hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
			"acknowledgement_confirmed": 1,
		},
	)
	# F0: template remains Draft — use development-preview seal for test/NSSF publish.
	published = publish_tender_for_development_preview(pub_id)
	pub_ref = cstr(published.get("publication_ref") or "") or cstr(
		frappe.db.get_value("IT Tender Publication Record", pub_id, "publication_ref") or ""
	)
	snap_raw = frappe.db.get_value(
		"IT Tender Publication Record", pub_id, "electronic_template_snapshot"
	)
	import json as _json

	snapshot = _json.loads(snap_raw) if snap_raw else {}
	return {
		**seeded,
		"publication_id": pub_id,
		"publication_ref": pub_ref,
		"electronic_template_hash": frappe.db.get_value(
			"IT Tender Publication Record", pub_id, "electronic_template_hash"
		),
		"calibration_counts": (snapshot or {}).get("calibration_counts") or {},
		"portal_workspace_url": f"/tenders/{pub_ref}/workspace",
		"portal_fot_url": f"/tenders/{pub_ref}/sections/form_of_tender",
	}


def cstr_trunc(val: Any, n: int) -> str:
	text = str(val or "").strip()
	return text[:n] if text else ""
