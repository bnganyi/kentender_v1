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
	CFG_WALKABLE,
	DEMAND_DRAFT,
	DEMAND_PENDING_HOD,
	PE_MOH,
	PKG_GATE_READY,
	PKG_NEEDS_ATTENTION,
	PKG_PUBLISHED,
	PKG_READY_TO_CONFIGURE,
	PKG_WALKABLE,
)
from kentender_core.seeds.stable_platform_seed.constants import (
	IT_BUDGET_LINE_CODE,
	IT_DEPT_NAME,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_APPROVED
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
	"""Walkable Draft + gate-ready Pending HoD under PE-MOH (Home actions)."""
	from kentender_procurement.demand_intake.seeds.dia_seed_common import ensure_core_prerequisites

	ensure_core_prerequisites()
	dept = ensure_department(IT_DEPT_NAME, PE_MOH)
	bl = _ensure_budget_line()
	out: dict[str, Any] = {}
	u_req = "requisitioner@moh.test"

	specs = (
		(
			DEMAND_DRAFT,
			"Demo Draft — District Hospital Clinical Workstations",
			"Draft",
			"walkable",
			"Edit and submit for HoD approval",
		),
		(
			DEMAND_PENDING_HOD,
			"Demo Pending HoD — Secure Wi‑Fi Expansion Phase 1",
			"Pending HoD Approval",
			"gate_ready",
			"Approve (HoD) from Demand workbench / Home",
		),
	)
	for demand_id, title, status, role, next_action in specs:
		existing = frappe.db.get_value("Demand", {"demand_id": demand_id}, "name")
		if existing:
			frappe.delete_doc("Demand", existing, force=True, ignore_permissions=True)
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": title,
				"demand_id": demand_id,
				"procuring_entity": PE_MOH,
				"requesting_department": dept,
				"requested_by": u_req,
				"request_date": "2026-06-01",
				"required_by_date": "2026-12-31",
				"priority_level": "High",
				"demand_type": "Planned",
				"requisition_type": "Goods",
				"budget_line": bl,
				"beneficiary_summary": "Demo platform seed — linked DIA stage under PE-MOH.",
				"specification_summary": title,
				"delivery_location": "Ministry of Health — priority district hospital sites",
				"items": [
					{
						"item_description": title,
						"category": "ICT Equipment",
						"uom": "Lot",
						"quantity": 1.0,
						"estimated_unit_cost": 5_000_000.0,
					}
				],
				"status": "Draft",
				"reservation_status": "None",
				"planning_status": "Not Planned",
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		if frappe.db.get_value("Demand", doc.name, "demand_id") != demand_id:
			frappe.db.set_value("Demand", doc.name, "demand_id", demand_id, update_modified=False)
		if status != "Draft":
			frappe.db.set_value(
				"Demand",
				doc.name,
				{
					"status": status,
					"submitted_by": u_req,
					"submitted_at": "2026-06-05 09:00:00",
				},
			)
		out[role] = {
			"demand_id": demand_id,
			"name": doc.name,
			"status": status,
			"title": title,
			"next_action": next_action,
		}
	return out


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
	row: dict[str, Any] = {
		"doctype": "Tender Configuration",
		"configuration_ref": ref,
		"tender_title": title,
		"status": status,
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
		"steps_state": steps_state,
		"approval_date": nowdate(),
		"short_scope_summary": "Demo platform IT STD configuration (linked PE-MOH).",
	}
	if full_payload:
		row.update(_gate_ready_payload())
	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	return doc.name


def _gate_ready_payload() -> dict[str, Any]:
	"""Minimal complete fields so Ready for Publication / preview is believable."""
	return {
		"lot_structure": "Single lot",
		"tds_values": json.dumps(
			{
				"tender_currency": "KES",
				"bid_validity_period": "90",
				"bid_validity_unit": "days",
				"tender_security_required": "Yes",
				"tender_security_type": "Tender Security",
				"tender_security_amount": "10000",
				"tender_security_currency": "KES",
				"submission_channel": "E-Procurement Portal",
				"alternatives_permitted": "No",
				"opening_method": "Electronic Opening",
			}
		),
		"it_requirements": json.dumps(
			[
				{
					"requirement_id": "DEMO-REQ-001",
					"title": "Network backbone",
					"description": "Provide campus LAN backbone for the district hospital.",
					"requirement_family": "System Requirements",
					"category_label": "Technical Requirement",
					"treatment_label": "Mandatory",
				}
			]
		),
		"evaluation_setup": json.dumps(
			{
				"technical_pass_mark": 70,
				"technical_scoring_total": 100,
				"criteria": [
					{
						"criterion_name": "Relevant experience",
						"stage": "Technical",
						"evaluation_basis": "Pass/Fail",
					}
				],
			}
		),
		"implementation_schedule": json.dumps(
			{
				"milestones": [{"milestone_id": "MS-01", "name": "Kick-off", "sequence": "1"}],
				"delivery_timing_complete": 1,
			}
		),
		"price_schedule": json.dumps(
			{"items": [{"item_name": "IT lot", "unit": "Lot", "quantity": "1", "currency": "KES"}]}
		),
		"contract_values": json.dumps(
			{
				"contract_values": [
					{
						"contract_value_id": "SCC-01",
						"item_label": "Governing law",
						"value_or_obligation": "Laws of Kenya",
					}
				]
			}
		),
		"system_inventory": json.dumps({"not_applicable": 1, "items": []}),
		"forms_and_evidence": json.dumps(
			{
				"submission_items": [
					{"item_id": "FORM-001", "title": "Form of Tender", "category": "Standard Form"}
				]
			}
		),
		"bidder_submission_schema": json.dumps(
			{
				"version": 1,
				"schema_hash": "demo-platform",
				"sections": [{"key": "form_of_tender", "title": "Form of Tender", "required": True}],
			}
		),
	}


def _seed_cfg_matrix() -> dict[str, Any]:
	ensure_active_canonical_ppra_it_std(force_reimport=False)
	if not frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID):
		frappe.throw(f"Missing ACTIVE STD {CANONICAL_PACKAGE_ID}")

	ready_pkg = _insert_package(PKG_READY_TO_CONFIGURE, "Demo Ready — Hospital Edge Switches")
	_insert_package(PKG_WALKABLE, "Demo Walkable — County LAN Refresh")
	walk = _insert_config(
		ref=CFG_WALKABLE,
		package_code=PKG_WALKABLE,
		title="Demo Walkable — County LAN Refresh",
		status=STATUS_IN_PROGRESS,
		steps_state=steps_state_focus_cfg("CFG-01", status_label=STEP_IN_PROGRESS),
	)
	_insert_package(PKG_NEEDS_ATTENTION, "Demo Needs Attention — Network Upgrade Phase 2")
	na = _insert_config(
		ref=CFG_NEEDS_ATTENTION,
		package_code=PKG_NEEDS_ATTENTION,
		title="Demo Needs Attention — Network Upgrade Phase 2",
		status=STATUS_NEEDS_ATTENTION,
		steps_state=steps_state_showcase_nine_cards(),
		blockers=2,
		warnings=1,
	)
	_insert_package(PKG_GATE_READY, "Demo Gate-Ready — HMIS Soft Services Lot")
	gate = _insert_config(
		ref=CFG_GATE_READY,
		package_code=PKG_GATE_READY,
		title="Demo Gate-Ready — HMIS Soft Services Lot",
		status=STATUS_READY_FOR_PUBLICATION,
		steps_state=steps_state_all_complete(),
		full_payload=True,
	)
	# Also stamp Approved for Preview so document preview / publication setup paths work
	frappe.db.set_value(
		"Tender Configuration",
		gate,
		{"status": STATUS_APPROVED_FOR_PREVIEW, "blocker_count": 0, "warning_count": 0},
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

	_insert_package(PKG_PUBLISHED, "Demo Published — Shared County IT Support Services")
	cfg = _insert_config(
		ref=CFG_PUBLISHED,
		package_code=PKG_PUBLISHED,
		title="Demo Published — Shared County IT Support Services",
		status=STATUS_APPROVED_FOR_PREVIEW,
		steps_state=steps_state_all_complete(),
		full_payload=True,
	)
	persist_compiled_schema(cfg)
	gen = generate_document_preview(cfg)
	if gen.get("preview_status") != "Generated":
		# Fallback: stamp publication directly
		return _direct_publish(cfg, past_deadline=False, past_opening=False, seal_bids=False)

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
			"tender_notice": "Demo platform published IT tender — receiving submissions.",
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
		"configuration_ref": CFG_PUBLISHED,
		"publication_id": pub_id,
		"role": "portfolio",
		"submission_stage": "Receiving submissions",
		"next_action": "View tender on Bid Submissions landing",
	}


def _direct_publish(
	cfg_id: str, *, past_deadline: bool, past_opening: bool, seal_bids: bool
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
	pkg = frappe.get_doc(
		{
			"doctype": PACKAGE_DOCTYPE,
			"configuration": cfg_id,
			"configuration_ref": cfg_id,
			"package_status": "Awaiting Publication Setup",
			"document_hash": frappe.generate_hash(length=32),
			"tender_html": "<html><body>demo-platform</body></html>",
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
			"tender_notice": "Demo platform publication.",
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

	# Sealed / openable
	pkg_s = f"{PKG_PUBLISHED}-SEALED"
	cfg_s = f"{CFG_PUBLISHED}-SEALED"
	_insert_package(pkg_s, "Demo Sealed — District Firewall Refresh")
	cfg = _insert_config(
		ref=cfg_s,
		package_code=pkg_s,
		title="Demo Sealed — District Firewall Refresh",
		status=STATUS_APPROVED_FOR_PREVIEW,
		steps_state=steps_state_all_complete(),
		full_payload=True,
	)
	sealed = _direct_publish(cfg, past_deadline=True, past_opening=True, seal_bids=True)

	# Opened
	pkg_o = f"{PKG_PUBLISHED}-OPENED"
	cfg_o = f"{CFG_PUBLISHED}-OPENED"
	_insert_package(pkg_o, "Demo Opened — Endpoint Security Suite")
	cfg2 = _insert_config(
		ref=cfg_o,
		package_code=pkg_o,
		title="Demo Opened — Endpoint Security Suite",
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
		"published_receiving": published,
		"bid_submissions": bids,
	}
