# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Linked actionable stage matrix (walkable + gate-ready) for demo platform."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import add_to_date, cstr, now_datetime, nowdate

from kentender_core.seeds._common import ensure_department
from kentender_core.seeds.demo_platform_seed.constants import (
	CFG_GATE_READY,
	CFG_NEEDS_ATTENTION,
	CFG_PUBLISHED,
	CFG_PUBLISHED_OPEN2,
	CFG_WALKABLE,
	DEMAND_DRAFT,
	DEMAND_PENDING_HOD,
	PE_MOH,
	PKG_GATE_READY,
	PKG_NEEDS_ATTENTION,
	PKG_PUBLISHED,
	PKG_PUBLISHED_OPEN2,
	PKG_READY_TO_CONFIGURE,
	PKG_WALKABLE,
)
from kentender_core.seeds.stable_platform_seed.constants import (
	IT_BUDGET_LINE_CODE,
	IT_DEPT_NAME,
)
PKG_APPROVED = "Approved"  # PP2 Package DocType retired
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
)
from kentender_procurement.tender_configurations.constants import (
	STATUS_APPROVED_FOR_PREVIEW,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_PUBLISHED,
	STATUS_READY_FOR_PUBLICATION,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	steps_state_all_complete,
	steps_state_focus_cfg,
	steps_state_showcase_nine_cards,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_IN_PROGRESS,
)


def _pe_name() -> str:
	return cstr(frappe.db.get_value("Procuring Entity", PE_MOH, "entity_name") or PE_MOH)


def _ensure_budget_line() -> str:
	if frappe.db.exists("Budget Line", {"budget_line_code": IT_BUDGET_LINE_CODE}):
		return frappe.db.get_value("Budget Line", {"budget_line_code": IT_BUDGET_LINE_CODE}, "name")
	# Fallback: any PE-MOH line
	name = frappe.db.get_value("Budget Line", {"procuring_entity": PE_MOH}, "name")
	if not name:
		frappe.throw("No Budget Line for PE-MOH — load stable platform first.")
	return name


def _seed_demands() -> dict[str, Any]:
	"""Demand demo rows — skipped after DIA preparatory teardown."""
	return {
		"ok": True,
		"skipped": True,
		"reason": "DEMAND_MODULE_RETIRED",
		"message": "Demand Intake retired — demo Demand rows not seeded (Demands MVP-1 pending).",
	}


def _insert_package(code: str, title: str) -> str:
	if frappe.db.exists("Procurement Package", code):
		frappe.delete_doc("Procurement Package", code, force=True, ignore_permissions=True)
	pkg = frappe.get_doc(
		{
			"doctype": "Procurement Package",
			"package_code": code,
			"package_name": title,
			"status": PKG_APPROVED,
			"procurement_method": "Open Tender",
			"contract_type": "Fixed Price",
			"procuring_entity_code": PE_MOH,
			"required_std_category": "Information Technology",
			"procurement_category": "Goods",
			"currency": "KES",
			"is_active": 1,
			"approved_at": nowdate(),
		}
	)
	pkg.flags.ignore_validate = True
	pkg.insert(ignore_permissions=True, ignore_mandatory=True)
	return pkg.name


def _insert_config(
	*,
	ref: str,
	package_code: str,
	title: str,
	status: str,
	steps_state: dict[str, Any],
	blockers: int = 0,
	warnings: int = 0,
	full_payload: bool = False,
) -> str:
	if frappe.db.exists("Tender Configuration", ref):
		frappe.delete_doc("Tender Configuration", ref, force=True, ignore_permissions=True)
	entity_name = _pe_name()
	# Gate-ready / publishable rows start In Progress; complete fixture + readiness promote status.
	insert_status = status
	if full_payload and status in (
		STATUS_APPROVED_FOR_PREVIEW,
		STATUS_READY_FOR_PUBLICATION,
		STATUS_PUBLISHED,
	):
		insert_status = STATUS_IN_PROGRESS
	row: dict[str, Any] = {
		"doctype": "Tender Configuration",
		"configuration_ref": ref,
		"tender_title": title,
		"status": insert_status,
		"procurement_package": package_code,
		"procurement_package_ref": package_code,
		"package_title": title,
		"procuring_entity_name": entity_name,
		"procuring_entity_code": PE_MOH,
		"procurement_method": "Open Tender",
		"std_family_key": "IT",
		"std_family_label": "Information Technology",
		"std_version": CANONICAL_PACKAGE_ID,
		"std_document_label": "IT Standard Tender Document — April 2022",
		"blocker_count": blockers,
		"warning_count": warnings,
		"steps_state": steps_state if not full_payload else steps_state_focus_cfg("CFG-01"),
		"approval_date": nowdate(),
		"lot_structure": "Single lot",
		# Profile readiness wants ≥6 words in scope (titles alone are often too short).
		"short_scope_summary": (
			f"{title}. Ministry of Health IT procurement under the PPRA IT Standard Tender Document."
		),
	}
	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	if full_payload:
		_fill_complete_cfg_from_e1_fixture(doc.name, target_status=status)
	return doc.name


def _fill_complete_cfg_from_e1_fixture(configuration_id: str, *, target_status: str) -> dict[str, Any]:
	"""Apply the proven E1 NSSF CFG-01…09 fixture blobs and refuse to gate if readiness fails.

	Lean / sparse JSON is not sufficient — only map_all_cfg_blobs + schema compile
	matches run_readiness_check. Stamping steps_state Complete without this is forbidden.
	"""
	from kentender_procurement.tender_configurations.seed.e1_nssf_seed import _apply_cfg_blobs
	from kentender_procurement.tender_configurations.services.e1_nssf_fixture_mapper import (
		map_all_cfg_blobs,
	)
	from kentender_procurement.tender_configurations.services.readiness import (
		run_readiness_check,
	)

	mapped = map_all_cfg_blobs()
	std_id = cstr(
		frappe.db.get_value("Tender Configuration", configuration_id, "std_version")
		or CANONICAL_PACKAGE_ID
	)
	_apply_cfg_blobs(configuration_id, mapped, std_version=std_id)

	# Electronic publish path expects tender security required (same as NSSF publish seed).
	tds_raw = frappe.db.get_value("Tender Configuration", configuration_id, "tds_values")
	try:
		tds = json.loads(tds_raw) if isinstance(tds_raw, str) else (tds_raw or {})
	except (TypeError, ValueError):
		tds = {}
	if not isinstance(tds, dict):
		tds = {}
	tds["tender_security_required"] = "Yes"
	if cstr(tds.get("tender_security_type") or "") in ("", "Not Required"):
		tds["tender_security_type"] = "Bank Guarantee"
	if not cstr(tds.get("tender_security_amount") or "").strip():
		tds["tender_security_amount"] = "500000"
	if not cstr(tds.get("tender_security_currency") or "").strip():
		tds["tender_security_currency"] = "KES"
	if not cstr(tds.get("tender_security_validity_period") or "").strip():
		tds["tender_security_validity_period"] = "120"
	if not cstr(tds.get("tender_security_validity_unit") or "").strip():
		tds["tender_security_validity_unit"] = "days"
	frappe.db.set_value(
		"Tender Configuration",
		configuration_id,
		{
			"tds_values": json.dumps(tds, ensure_ascii=False),
			"steps_state": json.dumps(steps_state_all_complete()),
		},
		update_modified=False,
	)
	frappe.db.commit()

	readiness = run_readiness_check(configuration_id)
	blockers = int(readiness.get("blocker_count") or 0)
	warnings = int(readiness.get("warning_count") or 0)
	if blockers > 0 or warnings > 0:
		frappe.throw(
			frappe._(
				"Demo platform CFG {0} still has {1} blocker(s) / {2} warning(s) after E1 fixture fill. "
				"Refusing to mark gate-ready / publishable."
			).format(configuration_id, blockers, warnings),
			title="DEMO_CFG_READINESS_ISSUES",
		)

	# Promote only after proven clean readiness (never stamp Approved over empty/noisy data).
	promote_to = target_status
	if promote_to == STATUS_PUBLISHED:
		promote_to = STATUS_APPROVED_FOR_PREVIEW
	elif promote_to == STATUS_READY_FOR_PUBLICATION:
		promote_to = STATUS_APPROVED_FOR_PREVIEW
	frappe.db.set_value(
		"Tender Configuration",
		configuration_id,
		{
			"status": promote_to,
			"blocker_count": 0,
			"warning_count": 0,
			"steps_state": json.dumps(steps_state_all_complete()),
			"approval_date": nowdate(),
		},
		update_modified=False,
	)
	frappe.db.commit()
	return readiness


def _seed_cfg_matrix() -> dict[str, Any]:
	ensure_active_canonical_ppra_it_std(force_reimport=False)
	if not frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID):
		frappe.throw(f"Missing ACTIVE STD {CANONICAL_PACKAGE_ID}")

	ready_pkg = _insert_package(PKG_READY_TO_CONFIGURE, "Hospital Edge Switches")
	_insert_package(PKG_WALKABLE, "County LAN Refresh")
	walk = _insert_config(
		ref=CFG_WALKABLE,
		package_code=PKG_WALKABLE,
		title="County LAN Refresh",
		status=STATUS_IN_PROGRESS,
		steps_state=steps_state_focus_cfg("CFG-01", status_label=STEP_IN_PROGRESS),
	)
	_insert_package(PKG_NEEDS_ATTENTION, "Network Upgrade Phase 2")
	na = _insert_config(
		ref=CFG_NEEDS_ATTENTION,
		package_code=PKG_NEEDS_ATTENTION,
		title="Network Upgrade Phase 2",
		status=STATUS_NEEDS_ATTENTION,
		steps_state=steps_state_showcase_nine_cards(),
		blockers=2,
		warnings=1,
	)
	_insert_package(PKG_GATE_READY, "Supply and configuration of HMIS Software")
	gate = _insert_config(
		ref=CFG_GATE_READY,
		package_code=PKG_GATE_READY,
		title="Supply and configuration of HMIS Software",
		status=STATUS_APPROVED_FOR_PREVIEW,
		steps_state=steps_state_all_complete(),
		full_payload=True,
	)

	return {
		"ready_to_configure_package": {
			"package_ref": PKG_READY_TO_CONFIGURE,
			"name": ready_pkg,
			"role": "walkable",
			"next_action": "Create configuration from Ready to Configure tab",
		},
		"walkable_config": {
			"configuration_ref": CFG_WALKABLE,
			"name": walk,
			"status": STATUS_IN_PROGRESS,
			"role": "walkable",
			"desk": f"/desk/it-tender-configuration-home/{CFG_WALKABLE}",
			"next_action": "Walk CFG-01…09",
		},
		"needs_attention_config": {
			"configuration_ref": CFG_NEEDS_ATTENTION,
			"name": na,
			"status": STATUS_NEEDS_ATTENTION,
			"role": "walkable",
			"next_action": "Resolve blockers then continue steps",
		},
		"gate_ready_config": {
			"configuration_ref": CFG_GATE_READY,
			"name": gate,
			"status": STATUS_APPROVED_FOR_PREVIEW,
			"role": "gate_ready",
			"desk": f"/desk/it-tender-configuration-home/{CFG_GATE_READY}",
			"next_action": "Confirm document package → Publication Setup → Publish",
		},
	}


def _publish_demo_config() -> dict[str, Any]:
	"""Published IT tender on PE-MOH for Bid Submissions receiving + bidder path."""
	from kentender_procurement.tender_configurations.services.document_preview import (
		confirm_document_preview,
		generate_document_preview,
	)
	from kentender_procurement.tender_configurations.services.publication_setup import (
		publish_tender_for_development_preview,
		save_publication_setup,
	)
	from kentender_procurement.tender_configurations.services.schema_compiler import (
		persist_compiled_schema,
	)

	def _publish_open(package_code: str, cfg_ref: str, title: str, notice: str) -> dict[str, Any]:
		_insert_package(package_code, title)
		cfg = _insert_config(
			ref=cfg_ref,
			package_code=package_code,
			title=title,
			status=STATUS_APPROVED_FOR_PREVIEW,
			steps_state=steps_state_all_complete(),
			full_payload=True,
		)
		persist_compiled_schema(cfg)
		gen = generate_document_preview(cfg)
		if gen.get("preview_status") != "Generated":
			return _direct_publish(
				cfg,
				past_deadline=False,
				past_opening=False,
				seal_bids=False,
				tender_notice=notice,
			)

		conf = confirm_document_preview(cfg, {"confirm_ready_for_handoff": 1})
		pub_id = conf["publication_id"]
		now = now_datetime()
		sub = add_to_date(now, days=14)
		opn = add_to_date(now, days=15)
		save_publication_setup(
			pub_id,
			{
				"publication_mode": "immediate",
				"publication_datetime": str(add_to_date(now, days=-1)),
				"tender_notice": notice,
				"clarification_deadline": str(add_to_date(sub, days=-2)),
				"submission_deadline": str(sub),
				"opening_datetime": str(opn),
				"bidder_visibility": "All Registered Bidders",
				"activate_bidder_workspace": 1,
				"acknowledgement_confirmed": 1,
			},
		)
		publish_tender_for_development_preview(pub_id)
		frappe.db.set_value(
			"IT Tender Publication Record",
			pub_id,
			{"submission_deadline": sub, "opening_datetime": opn},
		)
		frappe.db.set_value("Tender Configuration", cfg, "status", STATUS_PUBLISHED)
		return {
			"configuration_ref": cfg_ref,
			"publication_id": pub_id,
			"role": "portfolio",
			"submission_stage": "Receiving submissions",
			"next_action": "View tender on Bid Submissions landing",
		}

	primary = _publish_open(
		PKG_PUBLISHED,
		CFG_PUBLISHED,
		"Shared County IT Support Services",
		"Invitation to tender for shared county IT support services under the IT STD.",
	)
	secondary = _publish_open(
		PKG_PUBLISHED_OPEN2,
		CFG_PUBLISHED_OPEN2,
		"County EMR Interoperability Platform",
		"Invitation to tender for county EMR interoperability platform services.",
	)
	return {"primary": primary, "secondary_open": secondary}


def _direct_publish(
	cfg_id: str,
	*,
	past_deadline: bool,
	past_opening: bool,
	seal_bids: bool,
	tender_notice: str | None = None,
) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.seed.bid_submissions_officer_fixtures import (
		seal_three_bidders,
	)
	from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
		PACKAGE_DOCTYPE,
	)
	from kentender_procurement.tender_configurations.services.schema_compiler import (
		persist_compiled_schema,
	)

	persist_compiled_schema(cfg_id)
	now = now_datetime()
	sub = add_to_date(now, days=-2) if past_deadline else add_to_date(now, days=14)
	opn = add_to_date(now, days=-1) if past_opening else add_to_date(now, days=15)
	title = cstr(frappe.db.get_value("Tender Configuration", cfg_id, "tender_title") or cfg_id)
	pkg = frappe.get_doc(
		{
			"doctype": PACKAGE_DOCTYPE,
			"configuration": cfg_id,
			"configuration_ref": cfg_id,
			"package_status": "Awaiting Publication Setup",
			"document_hash": frappe.generate_hash(length=32),
			"tender_html": f"<html><body>{frappe.utils.escape_html(title)}</body></html>",
			"bidder_submission_schema": json.dumps(
				{
					"version": 1,
					"schema_hash": "demo-platform",
					"sections": [
						{"key": "form_of_tender", "title": "Form of Tender", "required": True}
					],
				}
			),
			"evaluation_schema": json.dumps({}),
			"price_schedule_schema": json.dumps({}),
			"forms_evidence_schema": json.dumps({}),
		}
	)
	pkg.flags.ignore_permissions = True
	pkg.insert(ignore_permissions=True)
	pub = frappe.get_doc(
		{
			"doctype": "IT Tender Publication Record",
			"configuration": cfg_id,
			"configuration_ref": cfg_id,
			"confirmed_package": pkg.name,
			"document_hash": pkg.document_hash,
			"status": "Published",
			"submission_deadline": sub,
			"opening_datetime": opn,
			"publication_datetime": add_to_date(now, days=-3),
			"tender_notice": tender_notice or f"Invitation to tender — {title}.",
			"activate_bidder_workspace": 1,
			"electronic_template_snapshot": json.dumps(
				{
					"sections": [
						{"section_key": "form_of_tender", "label": "Form of Tender"},
						{"section_key": "price_schedule", "label": "Price Schedule"},
					]
				}
			),
		}
	)
	pub.flags.ignore_publication_boundary = True
	pub.insert(ignore_permissions=True)
	frappe.db.set_value("Tender Configuration", cfg_id, "status", STATUS_PUBLISHED)
	frappe.db.commit()
	bids: list[str] = []
	if seal_bids:
		bids = seal_three_bidders(cfg_id, pub.name)
	return {
		"configuration_ref": cfg_id,
		"publication_id": pub.name,
		"bid_ids": bids,
		"submission_deadline": str(sub),
		"opening_datetime": str(opn),
	}


def _seed_bid_scenarios() -> dict[str, Any]:
	"""Closed+sealed (openable) and Opened register — PE-MOH linked demo pubs."""
	from kentender_procurement.tender_configurations.services.bid_submissions import (
		open_submitted_bids,
	)

	# Sealed / openable — past submission deadline (Closed on bidder portal; openable on Desk)
	pkg_s = f"{PKG_PUBLISHED}-SEALED"
	cfg_s = f"{CFG_PUBLISHED}-SEALED"
	_insert_package(pkg_s, "District Firewall Refresh")
	cfg = _insert_config(
		ref=cfg_s,
		package_code=pkg_s,
		title="District Firewall Refresh",
		status=STATUS_APPROVED_FOR_PREVIEW,
		steps_state=steps_state_all_complete(),
		full_payload=True,
	)
	sealed = _direct_publish(cfg, past_deadline=True, past_opening=True, seal_bids=True)

	# Opened — past deadline + opened register (Closed on bidder portal)
	pkg_o = f"{PKG_PUBLISHED}-OPENED"
	cfg_o = f"{CFG_PUBLISHED}-OPENED"
	_insert_package(pkg_o, "Endpoint Security Suite")
	cfg2 = _insert_config(
		ref=cfg_o,
		package_code=pkg_o,
		title="Endpoint Security Suite",
		status=STATUS_APPROVED_FOR_PREVIEW,
		steps_state=steps_state_all_complete(),
		full_payload=True,
	)
	opened_pub = _direct_publish(cfg2, past_deadline=True, past_opening=True, seal_bids=True)
	frappe.set_user("Administrator")
	open_result = open_submitted_bids(opened_pub["publication_id"])

	return {
		"closed_sealed": {
			**sealed,
			"role": "gate_ready",
			"next_action": "Open submitted bids on Bid Submissions sealed screen",
		},
		"opened": {
			**opened_pub,
			"opening": open_result,
			"role": "portfolio",
			"next_action": "Open register → View bid",
		},
	}


def seed_actionable_stages() -> dict[str, Any]:
	"""Seed DIA + CFG + publication + bid actionable matrix on PE-MOH."""
	frappe.set_user("Administrator")
	demands = _seed_demands()
	frappe.db.commit()
	cfg = _seed_cfg_matrix()
	frappe.db.commit()
	published = _publish_demo_config()
	frappe.db.commit()
	bids = _seed_bid_scenarios()
	frappe.db.commit()
	return {
		"demands": demands,
		"tender_configurations": cfg,
		"published_receiving": published.get("primary") if isinstance(published, dict) else published,
		"published_open": published,
		"bid_submissions": bids,
	}
