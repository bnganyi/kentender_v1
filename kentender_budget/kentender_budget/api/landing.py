# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget landing API — neutralized by MVP-1 Budget preparatory teardown."""

from __future__ import annotations

from typing import Any

import frappe


@frappe.whitelist()
def get_budget_landing_data() -> dict[str, Any]:
	"""Empty landing payload until MVP-1 Budget Desk is rebuilt."""
	return {
		"ok": True,
		"skipped": True,
		"reason": "mvp1-budget-teardown",
		"budgets": [],
		"summary": {},
	}
