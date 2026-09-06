# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 Phase 2 — cancel the capability-era Planning Workflow
Tasks. The v1.2 tasks are module-local doctypes (decision D4, NDS D3
precedent); leftover core `Workflow Task` rows for `plan.*` capabilities would
otherwise sit open in queues forever. Mirrors NDS's
`cancel_legacy_departmental_needs_workflow_tasks`."""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.exists("DocType", "Workflow Task"):
		return
	frappe.db.sql(
		"""update `tabWorkflow Task`
		set state = 'Cancelled'
		where task_type like 'plan.%%'
		and state not in ('Completed', 'Cancelled', 'Superseded')"""
	)
	frappe.db.commit()
