# Copyright (c) 2026, KenTender and contributors
"""Pre-sync: drop Demand Intake Module Def so migrate does not import deleted package."""

from __future__ import annotations

import frappe


def execute() -> None:
	if frappe.db.exists("Module Def", "Demand Intake"):
		frappe.db.delete("Module Def", {"name": "Demand Intake"})
		frappe.clear_cache()
