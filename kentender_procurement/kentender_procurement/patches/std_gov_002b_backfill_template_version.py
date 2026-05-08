# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-002b — ensure ``template_version`` is populated (post-002 follow-up)."""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.has_table("tabSTD Template"):
		return
	frappe.db.sql(
		"""
		UPDATE `tabSTD Template`
		SET `template_version` = COALESCE(
			NULLIF(`template_version`, ''),
			NULLIF(`version_label`, ''),
			NULLIF(`package_version`, ''),
			'POC'
		)
		WHERE `template_version` IS NULL OR `template_version` = ''
		"""
	)
