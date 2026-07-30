# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deterministic UI-00 seed: eligible packages + configurations across statuses."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import nowdate

from kentender_procurement.procurement_planning.pp2_constants import PKG_APPROVED
from kentender_procurement.tender_configurations.constants import (
	STATUS_COMPLETED,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_READY_FOR_REVIEW,
	STATUS_UNDER_REVIEW,
)
from kentender_procurement.tender_configurations.seed.lean_preliminary_criteria import (
	lean_preliminary_criteria_rows,
)
from kentender_procurement.tender_configurations.seed.lean_technical_proposal import (
	FIXTURE_FULL as TP_FIXTURE_FULL,
	merge_technical_proposal_into_evaluation,
)
from kentender_procurement.tender_configurations.seed.lean_qualification_criteria import (
	FIXTURE_FULL,
	merge_qualification_into_evaluation,
)
from kentender_procurement.tender_configurations.services.eligibility import ensure_fixture_std_version

SEED_PREFIX = "TCFG-SEED"
PACKAGE_REFS = (
	f"{SEED_PREFIX}-PKG-READY-001",
	f"{SEED_PREFIX}-PKG-READY-002",
	f"{SEED_PREFIX}-PKG-CFG-IP",
	f"{SEED_PREFIX}-PKG-CFG-NA",
	f"{SEED_PREFIX}-PKG-CFG-RR",
	f"{SEED_PREFIX}-PKG-CFG-UR",
	f"{SEED_PREFIX}-PKG-CFG-RP",
	f"{SEED_PREFIX}-PKG-CFG-DONE",
)


def _clear_seed() -> None:
	# Configs created via API use TCFG-{package_code}; also clear seed-prefixed refs.
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
	# Drop bidder drafts before configs — reseeding reuses stable configuration names,
	# and leftover Electronic Bid Submission rows would otherwise poison new runs.
	for name in config_names:
		for bid_id in frappe.get_all(
			"Electronic Bid Submission",
			filters={"configuration": name},
			pluck="name",
		):
			frappe.delete_doc("Electronic Bid Submission", bid_id, force=True, ignore_permissions=True)

	for name in config_names:
		frappe.delete_doc("Tender Configuration", name, force=True, ignore_permissions=True)

	for code in PACKAGE_REFS:
		if frappe.db.exists("Procurement Package", code):
			frappe.delete_doc("Procurement Package", code, force=True, ignore_permissions=True)


def _ensure_pe() -> str:
	code = f"{SEED_PREFIX}-PE"
	if not frappe.db.exists("Procuring Entity", code):
		# Minimal PE — ignore_mandatory if schema is heavy
		try:
			frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": code,
					"entity_name": "National Treasury",
				}
			).insert(ignore_permissions=True, ignore_mandatory=True)
		except Exception:
			# Fall back to any existing PE
			existing = frappe.get_all("Procuring Entity", limit=1, pluck="name")
			return existing[0] if existing else code
	return code


def _insert_package(
	*,
	code: str,
	title: str,
	method: str,
	entity: str,
	category: str = "Information Technology",
) -> str:
	if frappe.db.exists("Procurement Package", code):
		frappe.db.set_value(
			"Procurement Package",
			code,
			{
				"package_name": title,
				"status": PKG_APPROVED,
				"procurement_method": method,
				"procuring_entity_code": entity,
				"required_std_category": category,
				"procurement_category": "Goods" if category == "Goods" else "Works" if category == "Works" else "Services",
				"is_active": 1,
				"approved_at": nowdate(),
			},
		)
		return code

	doc = frappe.get_doc(
		{
			"doctype": "Procurement Package",
			"package_code": code,
			"package_name": title,
			"status": PKG_APPROVED,
			"procurement_method": method,
			"contract_type": "Fixed Price",
			"procuring_entity_code": entity,
			"required_std_category": category,
			"procurement_category": "Services",
			"currency": "KES",
			"is_active": 1,
			"approved_at": nowdate(),
			"method_override_flag": 0,
		}
	)
	# Seed fixtures intentionally bypass PP2 profile/plan link gates.
	doc.flags.ignore_validate = True
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	frappe.db.set_value(
		"Procurement Package",
		doc.name,
		{
			"status": PKG_APPROVED,
			"approved_at": nowdate(),
			"package_code": code,
			"is_active": 1,
		},
	)
	return doc.name


def _insert_config(
	*,
	ref: str,
	package_name: str,
	package_ref: str,
	title: str,
	status: str,
	std_version: str,
	entity_name: str,
	method: str,
	blockers: int = 0,
	warnings: int = 0,
	steps_state: dict | None = None,
) -> str:
	from kentender_procurement.tender_configurations.services.configuration_home import (
		default_steps_state_for_seed,
	)

	if frappe.db.exists("Tender Configuration", ref):
		frappe.delete_doc("Tender Configuration", ref, force=True, ignore_permissions=True)
	state = steps_state
	if state is None:
		state = default_steps_state_for_seed(needs_attention=blockers > 0)
	doc = frappe.get_doc(
		{
			"doctype": "Tender Configuration",
			"configuration_ref": ref,
			"tender_title": title,
			"status": status,
			"procurement_package": package_name,
			"procurement_package_ref": package_ref,
			"package_title": title,
			"procuring_entity_name": entity_name,
			"procuring_entity_code": entity_name,
			"procurement_method": method,
			"std_family_key": "IT",
			"std_family_label": "Information Technology",
			"std_version": std_version,
			"std_document_label": "IT Standard Tender Document — April 2022",
			"blocker_count": blockers,
			"warning_count": warnings,
			"steps_state": state,
			"approval_date": nowdate(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _apply_bidder_facing_preview_blobs(configuration_id: str) -> None:
	"""Seed CFG JSON so WG-03 required sections render as bidder-facing content."""
	frappe.db.set_value(
		"Tender Configuration",
		configuration_id,
		{
			"tds_values": json.dumps(
				{
					"contact_officer": "Jane Doe",
					"contact_email": "procurement@example.go.ke",
					"clarification_submission_method": "E-Procurement Portal",
					"clarification_deadline": "2026-08-30T15:30",
					"pre_tender_meeting": "No",
					"tender_submission_deadline": "2026-09-15T17:00",
					"tender_opening_datetime": "2026-09-15T17:30",
					"bid_validity_period": "120",
					"bid_validity_unit": "days",
					"submission_channel": "E-Procurement Portal",
					"submission_language": "English",
					"tender_currency": "KES",
					"tender_security_required": "Yes",
					"tender_security_type": "Tender Security",
					"tender_security_amount": "50000",
					"tender_security_currency": "KES",
					"tender_security_validity_period": "14",
					"tender_security_validity_unit": "days",
					"margin_of_preference_applies": "No",
					"opening_method": "Electronic Opening",
					"opening_location": "KenTender portal",
					"opening_attendance_allowed": "Yes",
				}
			),
			"it_requirements": json.dumps(
				[
					{
						"requirement_id": "REQ-001",
						"title": "Helpdesk Service Continuity",
						"description": (
							"The solution shall support continuous helpdesk operations with "
							"defined service levels for incident response."
						),
						"category_label": "Business Objective",
						"treatment_label": "Mandatory",
					},
					{
						"requirement_id": "REQ-002",
						"title": "Compute Node Performance",
						"description": (
							"Compute nodes must meet the stated processor and memory requirements."
						),
						"category_label": "Technical Requirement",
						"treatment_label": "Mandatory",
					},
					{
						"requirement_id": "REQ-003",
						"title": "Three-Year On-site Support",
						"description": (
							"Provide three-year on-site support and warranty services."
						),
						"category_label": "Support & Warranty",
						"treatment_label": "Mandatory",
					},
				]
			),
			"evaluation_setup": json.dumps(
				merge_technical_proposal_into_evaluation(
					merge_qualification_into_evaluation(
						{
							"criteria": lean_preliminary_criteria_rows()
							+ [
								{
									"criterion_name": "Technical compliance for: REQ-002",
									"stage": "Technical",
									"evaluation_basis": "Scored",
									"marks": "50",
									"related_requirement_id": "REQ-002",
									"bidder_evidence": "Required",
									"evidence_instruction": "Provide datasheets demonstrating compliance.",
								},
							]
						},
						fixture=FIXTURE_FULL,
					),
					fixture=TP_FIXTURE_FULL,
				)
			),
			"price_schedule": json.dumps(
				{
					"items": [
						{
							"item_name": "Price for requirement: REQ-002",
							"related_requirement_id": "REQ-002",
							"bidder_facing_description": (
								"Supply, install, and commission compute nodes meeting the "
								"specified performance requirement."
							),
							"unit": "Lot",
							"quantity": "1",
							"currency": "KES",
						},
						{
							"item_name": "Price for requirement: REQ-003",
							"related_requirement_id": "REQ-003",
							"bidder_facing_description": (
								"Provide three-year on-site support and warranty services."
							),
							"unit": "Lot",
							"quantity": "1",
							"currency": "KES",
						},
					]
				}
			),
			"system_inventory": json.dumps({"not_applicable": 1, "items": []}),
			# F1 / WG-03 preview hard-requires CFG-09 SCC topics.
			"contract_values": json.dumps(
				{
					"contract_values": [
						{
							"contract_value_id": "SCC-01",
							"item_label": "Governing law",
							"value_or_obligation": "Governing law: Laws of Kenya",
						},
						{
							"contract_value_id": "SCC-02",
							"item_label": "Scope",
							"value_or_obligation": "Scope: All modules in Part 2",
						},
						{
							"contract_value_id": "SCC-03",
							"item_label": "Commencement",
							"value_or_obligation": (
								"Commencement within 14 days; 24 month implementation period"
							),
						},
						{
							"contract_value_id": "SCC-04",
							"item_label": "Payment",
							"value_or_obligation": "Milestone payment schedule as agreed",
						},
						{
							"contract_value_id": "SCC-05",
							"item_label": "Source code / escrow",
							"value_or_obligation": "Source code escrow within 30 days",
						},
						{
							"contract_value_id": "SCC-06",
							"item_label": "Subcontracting",
							"value_or_obligation": "Subcontracting requires prior written approval",
						},
						{
							"contract_value_id": "SCC-07",
							"item_label": "SLA",
							"value_or_obligation": "P1 response 4 hours / resolution 24 hours",
						},
						{
							"contract_value_id": "SCC-08",
							"item_label": "Performance security",
							"value_or_obligation": "10% performance security of Contract Price",
						},
						{
							"contract_value_id": "SCC-09",
							"item_label": "Warranty",
							"value_or_obligation": "Twelve-month warranty after go-live",
						},
					]
				}
			),
		},
		update_modified=False,
	)


def seed_ui00_dashboard(*, clear: bool = True) -> dict[str, Any]:
	"""Load deterministic UI-00 queue data. Idempotent when clear=True."""
	frappe.set_user("Administrator")
	if clear:
		_clear_seed()

	std_id = ensure_fixture_std_version()
	# Preview generation rejects fixture sample ITT/GCC — bind preview-path configs to ACTIVE PPRA.
	from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
	from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
		ensure_active_canonical_ppra_it_std,
	)

	ensure_active_canonical_ppra_it_std(force_reimport=False)
	preview_std_id = CANONICAL_PACKAGE_ID
	entity = _ensure_pe()
	entity_name = frappe.db.get_value("Procuring Entity", entity, "entity_name") or "National Treasury"

	ready_1 = _insert_package(
		code=PACKAGE_REFS[0],
		title="Data Center Hardware Refresh",
		method="Open Tender",
		entity=entity,
		category="Information Technology",
	)
	ready_2 = _insert_package(
		code=PACKAGE_REFS[1],
		title="County Office Renovation Works",
		method="Open Tender",
		entity=entity,
		category="Works",
	)
	# Works may lack ACTIVE STD — force IT category for eligibility of second ready pkg
	frappe.db.set_value("Procurement Package", ready_2, "required_std_category", "Information Technology")

	from kentender_procurement.tender_configurations.services.configuration_home import (
		steps_state_all_complete,
		steps_state_focus_cfg,
		steps_state_showcase_nine_cards,
	)
	from kentender_procurement.tender_configurations.services.configuration_steps import (
		STEP_IN_PROGRESS,
	)

	cfg_pkgs = []
	for code, title in (
		(PACKAGE_REFS[2], "ERP Implementation Services"),
		(PACKAGE_REFS[3], "Network Upgrade Phase 2"),
		(PACKAGE_REFS[4], "Cloud Hosting Services"),
		(PACKAGE_REFS[5], "Under Review Hosting Renewal"),
		(PACKAGE_REFS[6], "Helpdesk Platform"),
		(PACKAGE_REFS[7], "Legacy Archive Digitization"),
	):
		cfg_pkgs.append(
			_insert_package(code=code, title=title, method="Open Tender", entity=entity)
		)

	all_done = steps_state_all_complete()
	configs = [
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-IP",
			package_name=cfg_pkgs[0],
			package_ref=PACKAGE_REFS[2],
			title="ERP Implementation Services",
			status=STATUS_IN_PROGRESS,
			std_version=std_id,
			entity_name=entity_name,
			method="Open Tender",
			warnings=2,
			steps_state=steps_state_focus_cfg("CFG-01", status_label=STEP_IN_PROGRESS),
		),
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-NA",
			package_name=cfg_pkgs[1],
			package_ref=PACKAGE_REFS[3],
			title="Network Upgrade Phase 2",
			status=STATUS_NEEDS_ATTENTION,
			std_version=std_id,
			entity_name=entity_name,
			method="Open Tender",
			blockers=2,
			warnings=1,
			steps_state=steps_state_showcase_nine_cards(),
		),
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-RR",
			package_name=cfg_pkgs[2],
			package_ref=PACKAGE_REFS[4],
			title="Cloud Hosting Services",
			status=STATUS_READY_FOR_REVIEW,
			std_version=preview_std_id,
			entity_name=entity_name,
			method="Open Tender",
			steps_state=all_done,
		),
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-UR",
			package_name=cfg_pkgs[3],
			package_ref=PACKAGE_REFS[5],
			title="Under Review Hosting Renewal",
			status=STATUS_UNDER_REVIEW,
			std_version=preview_std_id,
			entity_name=entity_name,
			method="Open Tender",
			steps_state=all_done,
		),
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-RP",
			package_name=cfg_pkgs[4],
			package_ref=PACKAGE_REFS[6],
			title="Helpdesk Platform",
			status=STATUS_READY_FOR_PUBLICATION,
			std_version=preview_std_id,
			entity_name=entity_name,
			method="Open Tender",
			steps_state=all_done,
		),
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-DONE",
			package_name=cfg_pkgs[5],
			package_ref=PACKAGE_REFS[7],
			title="Legacy Archive Digitization",
			status=STATUS_COMPLETED,
			std_version=preview_std_id,
			entity_name=entity_name,
			method="Open Tender",
			steps_state=all_done,
		),
	]

	# WG-03 preview requires bidder-facing CFG content on publication-path configs.
	preview_ready_refs = {
		f"{SEED_PREFIX}-TCFG-RR",
		f"{SEED_PREFIX}-TCFG-UR",
		f"{SEED_PREFIX}-TCFG-RP",
		f"{SEED_PREFIX}-TCFG-DONE",
	}
	for cfg_id in configs:
		if cfg_id in preview_ready_refs:
			_apply_bidder_facing_preview_blobs(cfg_id)

	frappe.db.commit()
	return {
		"std_version": std_id,
		"ready_packages": [ready_1, ready_2],
		"configurations": configs,
		"entity": entity,
	}


def clear_ui00_seed() -> None:
	_clear_seed()
	frappe.db.commit()
