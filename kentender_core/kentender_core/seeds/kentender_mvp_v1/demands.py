# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KENTENDER_MVP_V1 Demands stage — module-owned seed entry after Budget."""

from __future__ import annotations

from typing import Any

import frappe


def upsert_demands() -> dict[str, Any]:
	"""Seed the three canonical Demand anchors (DEM-SEED-001…003)."""
	if not frappe.db.exists("DocType", "Demand"):
		return {"ok": False, "reason": "Demand DocType unavailable"}

	from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
		upsert_county_draft_demand,
		upsert_principal_approved_demand,
		upsert_returned_shortfall_demand,
	)

	principal = upsert_principal_approved_demand(commit=False)
	returned = upsert_returned_shortfall_demand(commit=False)
	county = upsert_county_draft_demand(commit=False)
	frappe.db.commit()
	return {
		"ok": True,
		"principal": principal,
		"returned": returned,
		"county": county,
	}
