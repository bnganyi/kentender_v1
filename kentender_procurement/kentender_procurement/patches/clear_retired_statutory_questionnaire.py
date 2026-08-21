# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear retired statutory questionnaire placeholders on Plan Item Versions."""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.exists("DocType", "Procurement Plan Item Version"):
		return
	meta = frappe.get_meta("Procurement Plan Item Version")
	sets = []
	if meta.has_field("statutory_treatment"):
		sets.append("statutory_treatment = NULL")
	if meta.has_field("statutory_target_groups"):
		sets.append("statutory_target_groups = NULL")
	if meta.has_field("planned_treatment_value"):
		sets.append("planned_treatment_value = 0")
	if meta.has_field("value_treatment_note"):
		sets.append("value_treatment_note = NULL")
	if not sets:
		return
	frappe.db.sql(
		f"UPDATE `tabProcurement Plan Item Version` SET {', '.join(sets)}"
	)
	frappe.db.commit()
