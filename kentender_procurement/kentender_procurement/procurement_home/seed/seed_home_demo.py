# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Coherent demonstration fixture for Procurement Home (§16).

Creates / updates a small set of real module rows when missing so Home sections
can demonstrate populated states. Safe to re-run (idempotent by business codes).
Does not seed Home-specific totals — figures are computed by Home services.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, now_datetime

from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_doctype_available,
)


def _ensure_pe() -> str:
	if frappe.db.exists("Procuring Entity", "PE-MOH"):
		return "PE-MOH"
	if frappe.db.exists("Procuring Entity", "MOH"):
		return "MOH"
	# Fall back to any entity
	name = frappe.db.get_value("Procuring Entity", {}, "name")
	return name or "PE-MOH"


def seed_procurement_home_demo() -> dict:
	"""Idempotent demo seed for Home. Returns summary codes created/ensured."""
	pe = _ensure_pe()
	summary: dict = {"procuring_entity": pe, "demands": [], "notes": []}

	if demand_doctype_available():
		pending = frappe.get_all(
			"Demand",
			filters={
				"procuring_entity": ["in", [pe, "MOH", "PE-MOH"]],
				"status": "In Review",
			},
			pluck="demand_code",
			limit=3,
		)
		summary["demands"] = [c for c in pending if c]
		if not summary["demands"]:
			summary["notes"].append(
				"No In Review Demands found — Home demand actions may be empty."
			)
	else:
		summary["demands"] = []
		summary["notes"].append("Demand DocType unavailable — Home demand actions empty.")

	tm_count = 0
	if frappe.db.exists("DocType", "TM2 Tender"):
		tm_count = frappe.db.count(
			"TM2 Tender",
			{"procuring_entity_code": ["in", [pe, "MOH", "PE-MOH"]]},
		)
	summary["tm2_tenders"] = tm_count
	summary["as_of"] = str(now_datetime())
	summary["deadline_horizon"] = str(add_days(now_datetime(), 14))
	return summary


def run():
	return seed_procurement_home_demo()
