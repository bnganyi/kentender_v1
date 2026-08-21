# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KENTENDER_MVP_V1 Planning stage — module-owned seed entry after Demands."""

from __future__ import annotations

from typing import Any

import frappe


def upsert_planning() -> dict[str, Any]:
	"""Seed Demo v2.7 base Planning (Approved V1 + Active PPI @ 455M)."""
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return {"ok": False, "reason": "Procurement Plan DocType unavailable"}

	from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import (
		upsert_planning_base,
	)

	return upsert_planning_base(commit=False)
