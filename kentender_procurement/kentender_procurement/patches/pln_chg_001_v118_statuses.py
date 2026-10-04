# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.2.2 / §6.1 (plan D15) — status vocabulary on live rows.

post_model_sync, idempotent: `funding_state` `Awaiting Finance` →
`Awaiting confirmation`; `Plan Governance Decision.resolution_reference` →
`collective_resolution_reference` (the old column is dropped by the Phase 2
exit patch once nothing reads it).
"""

from __future__ import annotations

import frappe


def execute() -> None:
	frappe.db.sql("update `tabAnnual Plan Version` set funding_state = 'Awaiting confirmation' where funding_state = 'Awaiting Finance'")
	if frappe.db.has_column("Plan Governance Decision", "resolution_reference"):
		frappe.db.sql(
			"""update `tabPlan Governance Decision` set collective_resolution_reference = resolution_reference
			where ifnull(collective_resolution_reference, '') = '' and ifnull(resolution_reference, '') != ''"""
		)
	frappe.db.commit()
