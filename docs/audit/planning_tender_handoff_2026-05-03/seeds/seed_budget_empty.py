# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""seed_budget_empty — remove all Budget/Budget Allocation records for empty-state testing."""

from __future__ import annotations

import frappe

from kentender_core.seeds._budget_seed_common import clear_budget_data


def run():
	frappe.only_for(("System Manager", "Administrator"))
	out = clear_budget_data()
	frappe.db.commit()
	return out

