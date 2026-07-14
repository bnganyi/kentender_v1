# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure IT Tender Drafter role and dashboard sample instances."""

from __future__ import annotations

import json
from datetime import timedelta

import frappe

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.services.wizard_progress_service import (
	generate_steps_for_instance,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID

ROLE_NAME = "IT Tender Drafter"

SAMPLE_INSTANCES = (
	{
		"instance_code": "ITCFG-DASH-SEED-001",
		"instance_title": "Data Center Hardware Refresh",
		"wizard_state": ws.IN_CONFIGURATION,
		"planning_package_code": "PP-ICT-2024-009",
		"planning_package_name": "Data Center Refresh Package",
		"procuring_entity_id": "PE-NATIONAL-TREASURY",
		"procuring_entity_name": "National Treasury",
		"procurement_method_code": "OPEN_NATIONAL",
		"procurement_method_name": "Open Tender",
		"completion_percent": 65,
		"current_step_code": "IT_REQUIREMENTS",
		"current_step_name": "IT Requirements",
		"blocking_findings_count": 0,
		"warning_findings_count": 2,
	},
	{
		"instance_code": "ITCFG-DASH-SEED-002",
		"instance_title": "Digital ID Integration Hub",
		"wizard_state": ws.VALIDATION_FAILED,
		"planning_package_code": "PP-ICT-2024-088",
		"planning_package_name": "Digital ID Hub Package",
		"procuring_entity_id": "PE-MIN-ICT",
		"procuring_entity_name": "Ministry of ICT",
		"procurement_method_code": "RFP",
		"procurement_method_name": "RFP",
		"completion_percent": 88,
		"current_step_code": "IT_REQUIREMENTS",
		"current_step_name": "IT Requirements",
		"blocking_findings_count": 3,
		"warning_findings_count": 0,
	},
	{
		"instance_code": "ITCFG-DASH-SEED-003",
		"instance_title": "School Management System Upgrade",
		"wizard_state": ws.READY_FOR_REVIEW,
		"planning_package_code": "PP-ICT-2024-211",
		"planning_package_name": "School MIS Upgrade",
		"procuring_entity_id": "PE-MIN-EDUCATION",
		"procuring_entity_name": "Min. of Education",
		"procurement_method_code": "OPEN_NATIONAL",
		"procurement_method_name": "Open Tender",
		"completion_percent": 100,
		"current_step_code": "REVIEW_AND_APPROVAL",
		"current_step_name": "Review and Approval",
		"blocking_findings_count": 0,
		"warning_findings_count": 0,
	},
	{
		"instance_code": "ITCFG-DASH-SEED-004",
		"instance_title": "Agri-Data Analytic Portal",
		"wizard_state": ws.RETURNED_FOR_CORRECTION,
		"planning_package_code": "PP-ICT-2024-004",
		"planning_package_name": "Agri Data Portal",
		"procuring_entity_id": "PE-DEPT-AGRICULTURE",
		"procuring_entity_name": "Dept. Agriculture",
		"procurement_method_code": "OPEN_NATIONAL",
		"procurement_method_name": "Open Tender",
		"completion_percent": 92,
		"current_step_code": "SCC",
		"current_step_name": "SCC / Contract Carry-Forward",
		"blocking_findings_count": 0,
		"warning_findings_count": 2,
		"due_at_days_ago": 5,
	},
)


SEED_001_STEP_STATUSES = {
	"TENDER_IDENTITY": "COMPLETE",
	"STD_CONFIG_OVERVIEW": "COMPLETE",
	"TENDER_PROFILE": "COMPLETE",
	"TDS": "IN_PROGRESS",
	"IMPLEMENTATION_SCHEDULE": "COMPLETE",
	"SYSTEM_INVENTORY": "COMPLETE",
	"PRICE_SCHEDULE": "COMPLETE",
	"EVALUATION_SETUP": "COMPLETE",
	"FORMS_AND_EVIDENCE": "COMPLETE",
	"IT_REQUIREMENTS": "IN_PROGRESS",
}

SEED_003_STEP_STATUSES = {
	"TENDER_IDENTITY": "COMPLETE",
	"STD_CONFIG_OVERVIEW": "COMPLETE",
	"TENDER_PROFILE": "COMPLETE",
	"TDS": "COMPLETE",
	"IT_REQUIREMENTS": "COMPLETE",
	"IMPLEMENTATION_SCHEDULE": "COMPLETE",
	"SYSTEM_INVENTORY": "COMPLETE",
	"PRICE_SCHEDULE": "COMPLETE",
	"EVALUATION_SETUP": "COMPLETE",
	"FORMS_AND_EVIDENCE": "COMPLETE",
	"SCC": "COMPLETE",
}

SEED_001_PROFILE = {
	"tender_name": "Supply and Commissioning of Data Center Hardware Refresh 2024",
	"contract_description": (
		"Complete overhaul of the existing blade server architecture, including storage arrays "
		"and high-capacity network switches at the Treasury Main Site."
	),
	"lotting_strategy": "SINGLE_LOT",
	"reservation_applies": 1,
	"reserved_group_code": "AGPO",
	"tender_security_applicability": "",
	"clarification_contact_email": "",
	"alternative_tenders_allowed": 0,
	"jv_allowed": 1,
	"pre_tender_meeting_required": 1,
}

SEED_003_PROFILE = {
	"tender_name": "School Management System Upgrade 2024",
	"contract_description": "Upgrade and integration of school MIS modules across county education offices.",
	"lotting_strategy": "SINGLE_LOT",
	"reservation_applies": 0,
	"reserved_group_code": "NONE",
	"tender_security_applicability": "TENDER_SECURING_DECLARATION",
	"clarification_contact_email": "procurement@education.go.ke",
	"alternative_tenders_allowed": 0,
	"jv_allowed": 1,
	"pre_tender_meeting_required": 1,
}

SEED_001_TDS = {
	"procuring_entity_address": "National Treasury, P.O. Box 30007-00100, Nairobi",
	"tender_number": "NT/T/ICT/2024-009",
	"tender_name": "Supply and Commissioning of Data Center Hardware Refresh 2024",
	"alternative_tenders_allowed": "NO",
	"jv_max_members": 3,
	"local_sourcing_preference": "MARGIN_15",
	"electronic_tenders_allowed": 1,
	"envelope_marking": "ELECTRONIC_ONLY",
}

SEED_003_TDS = {
	"procuring_entity_address": "Ministry of Education, P.O. Box 30040-00100, Nairobi",
	"tender_number": "MOE/T/MIS/2024-211",
	"tender_name": "School Management System Upgrade 2024",
	"alternative_tenders_allowed": "NO",
	"jv_max_members": 5,
	"local_sourcing_preference": "NONE",
	"submission_deadline_at": "2026-09-01 17:00:00",
	"opening_at": "2026-09-02 10:00:00",
	"clarification_contact_email": "procurement@education.go.ke",
	"electronic_tenders_allowed": 1,
	"envelope_marking": "ELECTRONIC_ONLY",
	"tender_security_amount": 250000,
	"tender_validity_days": 90,
	"security_issuer_type": "COMMERCIAL_BANK",
}


def _dedupe_step_instances(instance_name: str) -> None:
	rows = frappe.get_all(
		"Wizard Step Instance",
		filters={"tender_std_instance": instance_name},
		fields=["name", "step_code", "status", "step_order", "modified", "creation"],
		order_by="step_order asc, creation asc",
	)
	grouped: dict[str, list[dict]] = {}
	for row in rows:
		code = (row.get("step_code") or "").strip()
		if not code:
			continue
		grouped.setdefault(code, []).append(row)
	priority = {"COMPLETE": 4, "IN_PROGRESS": 3, "INCOMPLETE": 2, "NOT_AVAILABLE": 1}
	for step_rows in grouped.values():
		if len(step_rows) <= 1:
			continue
		keeper = max(
			step_rows,
			key=lambda row: (
				priority.get((row.get("status") or "INCOMPLETE").strip(), 0),
				row.get("modified") or row.get("creation") or "",
			),
		)
		for row in step_rows:
			if row["name"] != keeper["name"]:
				frappe.delete_doc("Wizard Step Instance", row["name"], ignore_permissions=True)


def _ensure_overview_steps(instance_name: str, sample: dict) -> None:
	_dedupe_step_instances(instance_name)
	existing = frappe.db.count("Wizard Step Instance", {"tender_std_instance": instance_name})
	if not existing:
		generate_steps_for_instance(instance_name)

	status_map = sample.get("step_statuses") or {}
	if sample["instance_code"] == "ITCFG-DASH-SEED-001":
		status_map = {**SEED_001_STEP_STATUSES, **status_map}
	if sample["instance_code"] == "ITCFG-DASH-SEED-003":
		status_map = {**SEED_003_STEP_STATUSES, **status_map}

	for step_code, status in status_map.items():
		step_names = frappe.get_all(
			"Wizard Step Instance",
			{"tender_std_instance": instance_name, "step_code": step_code},
			pluck="name",
		)
		for step_name in step_names:
			frappe.db.set_value("Wizard Step Instance", step_name, "status", status)
	_dedupe_step_instances(instance_name)


def _ensure_tds(instance_name: str, sample: dict) -> None:
	tds_map = sample.get("tds") or {}
	if sample["instance_code"] == "ITCFG-DASH-SEED-001":
		tds_map = {**SEED_001_TDS, **tds_map}
	if sample["instance_code"] == "ITCFG-DASH-SEED-003":
		tds_map = {**SEED_003_TDS, **tds_map}
	if not tds_map:
		return
	existing = frappe.db.get_value("Tender STD TDS", {"tender_std_instance": instance_name})
	if existing:
		doc = frappe.get_doc("Tender STD TDS", existing)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Tender STD TDS",
				"tender_std_instance": instance_name,
				"alternative_tenders_allowed": "NO",
				"envelope_marking": "ELECTRONIC_ONLY",
			}
		)
	doc.update(tds_map)
	if doc.get("name"):
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)


def _ensure_profile(instance_name: str, sample: dict) -> None:
	profile_map = sample.get("profile") or {}
	if sample["instance_code"] == "ITCFG-DASH-SEED-001":
		profile_map = {**SEED_001_PROFILE, **profile_map}
	if sample["instance_code"] == "ITCFG-DASH-SEED-003":
		profile_map = {**SEED_003_PROFILE, **profile_map}
	if not profile_map:
		return
	existing = frappe.db.get_value("Tender STD Profile", {"tender_std_instance": instance_name})
	if existing:
		doc = frappe.get_doc("Tender STD Profile", existing)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Tender STD Profile",
				"tender_std_instance": instance_name,
				"language_code": "en",
				"currency_code": "KES",
			}
		)
	doc.update(profile_map)
	if doc.get("name"):
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)


def ensure_it_tender_drafter_role() -> None:
	if not frappe.db.exists("Role", ROLE_NAME):
		frappe.get_doc({"doctype": "Role", "role_name": ROLE_NAME}).insert(ignore_permissions=True)


def _resolve_std_version_id() -> str:
	if frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID):
		return CANONICAL_PACKAGE_ID
	row = frappe.db.get_value("STD Version", {"family_code": "KE-PPRA-IT"}, "name")
	if not row:
		frappe.throw("No KE-PPRA-IT STD Version found for dashboard seeds.")
	return row


def seed_dashboard_sample_instances() -> None:
	std_version = _resolve_std_version_id()
	package_hash = frappe.db.get_value("STD Version", std_version, "package_sha256")
	for sample in SAMPLE_INSTANCES:
		existing_name = frappe.db.get_value(
			"Tender STD Instance",
			{"instance_code": sample["instance_code"]},
		)
		if existing_name:
			_ensure_overview_steps(existing_name, sample)
			_ensure_profile(existing_name, sample)
			_ensure_tds(existing_name, sample)
			frappe.db.set_value(
				"Tender STD Instance",
				existing_name,
				{
					"current_step_code": sample["current_step_code"],
					"current_step_name": sample["current_step_name"],
					"completion_percent": sample["completion_percent"],
				},
			)
			continue
		due_at = None
		if sample.get("due_at_days_ago"):
			due_at = frappe.utils.add_days(frappe.utils.today(), -int(sample["due_at_days_ago"]))
		doc = frappe.get_doc(
			{
				"doctype": "Tender STD Instance",
				"instance_code": sample["instance_code"],
				"instance_title": sample["instance_title"],
				"wizard_state": sample["wizard_state"],
				"std_version": std_version,
				"std_package_code": std_version,
				"package_hash": package_hash,
				"procuring_entity_id": sample["procuring_entity_id"],
				"procuring_entity_name": sample["procuring_entity_name"],
				"planning_package_code": sample["planning_package_code"],
				"planning_package_name": sample["planning_package_name"],
				"procurement_method_code": sample["procurement_method_code"],
				"procurement_method_name": sample["procurement_method_name"],
				"initiation_source": ws.INITIATION_DASHBOARD,
				"current_validation_status": "PASSED_WITH_WARNINGS"
				if sample["warning_findings_count"]
				else "FAILED"
				if sample["blocking_findings_count"]
				else "PASSED",
				"completion_percent": sample["completion_percent"],
				"current_step_code": sample["current_step_code"],
				"current_step_name": sample["current_step_name"],
				"due_at": due_at,
				"owner_user": frappe.session.user if frappe.session.user != "Guest" else None,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Wizard Progress Snapshot",
				"tender_std_instance": doc.name,
				"snapshot_at": frappe.utils.now_datetime(),
				"wizard_state": sample["wizard_state"],
				"blocking_findings_count": sample["blocking_findings_count"],
				"warning_findings_count": sample["warning_findings_count"],
				"completed_steps": 1,
				"total_steps": 15,
				"snapshot_payload_json": json.dumps({"seed": True}),
			}
		).insert(ignore_permissions=True)
		_ensure_overview_steps(doc.name, sample)
		_ensure_profile(doc.name, sample)
		_ensure_tds(doc.name, sample)


def execute() -> None:
	ensure_it_tender_drafter_role()
	seed_dashboard_sample_instances()
	frappe.db.commit()
