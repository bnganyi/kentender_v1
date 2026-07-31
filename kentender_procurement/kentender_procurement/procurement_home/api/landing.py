# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Legacy landing shim — delegates to functional Home API."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.procurement_home.api.home import get_procurement_home


@frappe.whitelist()
def get_procurement_home_landing_data() -> dict:
	"""Backward-compatible alias. Prefer get_procurement_home."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	home = get_procurement_home()
	# Minimal KPI-shaped subset for any leftover callers
	figures = (home.get("portfolio") or {}).get("figures") or []
	kpis = []
	for fig in figures[:4]:
		kpis.append(
			{
				"id": fig.get("key"),
				"label": fig.get("label"),
				"value": fig.get("value"),
				"format": "number",
				"currency": fig.get("currency"),
				"testid": f"ph-kpi-{fig.get('key')}",
			}
		)
	return {"ok": True, "kpis": kpis, "home": home}
