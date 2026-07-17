# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Wizard step progress calculations."""

from __future__ import annotations

import frappe

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws


def generate_steps_for_instance(instance_name: str) -> list[dict]:
	steps = []
	for step_code, step_order, step_title in ws.DEFAULT_WIZARD_STEPS:
		doc = frappe.get_doc(
			{
				"doctype": "Wizard Step Instance",
				"tender_std_instance": instance_name,
				"step_code": step_code,
				"step_order": step_order,
				"step_title": step_title,
				"status": "INCOMPLETE",
			}
		)
		doc.insert(ignore_permissions=True)
		steps.append(doc)
	return steps


def compute_progress(instance_name: str) -> dict:
	steps = frappe.get_all(
		"Wizard Step Instance",
		filters={"tender_std_instance": instance_name},
		fields=["step_code", "step_title", "step_order", "status"],
		order_by="step_order asc",
	)
	total = len(steps) or 1
	completed = sum(1 for row in steps if row.status == "COMPLETE")
	percent = int(round((completed / total) * 100))
	current = next((row for row in steps if row.status != "COMPLETE"), steps[0] if steps else None)
	return {
		"completion_percent": percent,
		"current_step_code": current.step_code if current else None,
		"current_step_name": current.step_title if current else None,
		"completed_steps": completed,
		"total_steps": total,
	}


def create_progress_snapshot(
	instance_name: str,
	*,
	wizard_state: str,
	blocking_findings_count: int = 0,
	warning_findings_count: int = 0,
) -> str:
	progress = compute_progress(instance_name)
	doc = frappe.get_doc(
		{
			"doctype": "Wizard Progress Snapshot",
			"tender_std_instance": instance_name,
			"snapshot_at": frappe.utils.now_datetime(),
			"wizard_state": wizard_state,
			"blocking_findings_count": blocking_findings_count,
			"warning_findings_count": warning_findings_count,
			"completed_steps": progress["completed_steps"],
			"total_steps": progress["total_steps"],
			"snapshot_payload_json": frappe.as_json(progress),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
