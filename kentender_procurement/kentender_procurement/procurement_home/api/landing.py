# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — cross-module landing (Information Architecture v1.0 §5.1)."""

from __future__ import annotations

import frappe
from frappe import _


def _append_kpis_from_dia(out: list[dict], dia: dict) -> None:
	if not dia.get("ok"):
		return
	cur = str(dia.get("currency") or "KES")
	for row in (dia.get("kpis") or [])[:2]:
		rid = row.get("id") or "kpi"
		out.append(
			{
				"id": f"dia_{rid}",
				"label": row.get("label") or "",
				"value": row.get("value"),
				"format": row.get("format"),
				"currency": row.get("currency") or cur,
				"testid": f"ph-kpi-dia-{rid}",
			}
		)


def _append_kpis_from_pp(out: list[dict], pp: dict) -> None:
	if not pp.get("ok"):
		return
	cur = str(pp.get("currency") or "KES")
	for row in (pp.get("kpis") or [])[:2]:
		rid = row.get("id") or "kpi"
		out.append(
			{
				"id": f"pp_{rid}",
				"label": row.get("label") or "",
				"value": row.get("value"),
				"format": row.get("format"),
				"currency": row.get("currency") or cur,
				"testid": f"ph-kpi-pp-{rid}",
			}
		)


@frappe.whitelist()
def get_procurement_home_landing_data() -> dict:
	"""Subset of DIA + PP KPIs for the Procurement Home workbench shell."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	from kentender_procurement.demand_intake.api.landing import get_dia_landing_shell_data
	from kentender_procurement.procurement_planning.api.landing import get_pp_landing_shell_data

	dia = get_dia_landing_shell_data()
	pp = get_pp_landing_shell_data()

	kpis: list[dict] = []
	_append_kpis_from_dia(kpis, dia)
	_append_kpis_from_pp(kpis, pp)

	return {
		"ok": True,
		"kpis": kpis[:4],
		"dia_ok": bool(dia.get("ok")),
		"pp_ok": bool(pp.get("ok")),
		"dia_message": (dia.get("message") if not dia.get("ok") else None),
		"pp_message": (pp.get("message") if not pp.get("ok") else None),
	}
