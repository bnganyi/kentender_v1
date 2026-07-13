# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure IT Tender Drafter role and dashboard sample instances."""

from __future__ import annotations

import json
from datetime import timedelta

import frappe

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
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
		"current_step_code": "EVALUATION_SETUP",
		"current_step_name": "Evaluation Setup",
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
		if frappe.db.exists("Tender STD Instance", {"instance_code": sample["instance_code"]}):
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


def execute() -> None:
	ensure_it_tender_drafter_role()
	seed_dashboard_sample_instances()
	frappe.db.commit()
