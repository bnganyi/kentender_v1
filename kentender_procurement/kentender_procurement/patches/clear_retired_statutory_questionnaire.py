# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear retired statutory questionnaire placeholders on Plan Item Versions."""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.exists("DocType", "Procurement Plan Item Version"):
		return
	# Do not invent preference designations from old questionnaire answers.
	frappe.db.sql(
		"""
		UPDATE `tabProcurement Plan Item Version`
		SET
			statutory_treatment = NULL,
			statutory_target_groups = NULL,
			planned_treatment_value = 0,
			value_treatment_note = NULL
		"""
	)
	frappe.db.commit()
