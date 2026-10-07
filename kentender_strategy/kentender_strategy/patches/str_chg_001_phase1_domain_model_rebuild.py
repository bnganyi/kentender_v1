# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.3 Phase 1 — drop doctypes removed by the clean rebuild and
clear pre-rebuild Strategic Plan data (dev site; no production data exists,
disposal explicitly authorised by the product owner 2026-08-23 — see
docs/mvp-1-r1/02_strategy/IMPLEMENTATION_TRACKER.md decision log).

Removed outright, no alias/compatibility layer (STR-CHG-001 §1.1/§19):
Performance Measurement, Strategy Value Commitment (+Link), Strategy Audit
Event (migrated onto kentender_core's shared Audit Event), and the old
Programme/Sub-programme/Objective/Outcome doctypes unified into Strategy Node.
"""

from __future__ import annotations

import frappe

from kentender_core.utils.patch_guards import doctype_is_shipped

REMOVED_DOCTYPES = [
	"Performance Measurement",
	"Strategy Value Commitment",
	"Strategy Value Commitment Link",
	"Strategy Audit Event",
	"Strategy Programme",
	"Strategy Sub Programme",
	"Strategic Objective",
	"Strategic Outcome",
]


def execute() -> None:
	for name in REMOVED_DOCTYPES:
		if doctype_is_shipped(name):
			continue
		if frappe.db.exists("DocType", name):
			frappe.delete_doc("DocType", name, force=1, ignore_permissions=True)

	# Strategic Plan's schema changed incompatibly (identity/version split);
	# pre-rebuild rows cannot be reconciled into the new shape. Only those rows
	# go: a row that carries the rebuilt identity (`plan_id`, required since the
	# rebuild) is current data and is never touched, so a site that has not
	# logged this patch but holds real plans keeps them (AUD-XC-125).
	if frappe.db.table_exists("Strategic Plan") and frappe.db.has_column("Strategic Plan", "plan_id"):
		frappe.db.sql("DELETE FROM `tabStrategic Plan` WHERE `plan_id` IS NULL OR `plan_id` = ''")

	frappe.db.commit()
