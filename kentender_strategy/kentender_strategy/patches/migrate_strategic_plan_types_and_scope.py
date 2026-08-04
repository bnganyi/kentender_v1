# Copyright (c) 2026, KenTender and contributors
"""Migrate Strategic Plan types and backfill ESP scope (STR-FR-005)."""

from __future__ import annotations

import frappe

TYPE_MAP = {
	"Sector Strategy": "Thematic Plan",
	"Other": "Annual Implementation Plan",
}


def execute():
	if not frappe.db.exists("DocType", "Strategic Plan"):
		return
	if not frappe.db.has_column("Strategic Plan", "scope_type"):
		# migrate will add columns from JSON; re-run after sync if needed
		return

	for old, new in TYPE_MAP.items():
		frappe.db.sql(
			"""
			UPDATE `tabStrategic Plan`
			SET plan_type = %s
			WHERE plan_type = %s
			""",
			(new, old),
		)

	# Entity Strategic Plan: scope is the procuring entity
	frappe.db.sql(
		"""
		UPDATE `tabStrategic Plan`
		SET scope_type = 'Procuring Entity',
			scope_id = procuring_entity,
			parent_plan = NULL
		WHERE plan_type = 'Entity Strategic Plan'
		  AND (
			IFNULL(scope_type, '') = ''
			OR IFNULL(scope_id, '') = ''
			OR scope_id != procuring_entity
			OR parent_plan IS NOT NULL
		  )
		"""
	)
