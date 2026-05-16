# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-005 / LV-R5-005-01 — Procurement Package ↔ PLC journey linkage for Planning UI.

Maps ``Procurement Journey.procurement_package_ref`` (business package code) to a compact
navigation payload for Planning workbench list/detail.  Read-only aggregate (ADR-PLC-002).
"""

from __future__ import annotations

from typing import Any

import frappe


def journey_link_hints_by_package_codes(package_codes: list[str]) -> dict[str, dict[str, str]]:
	"""Return ``{package_code: {journey_code, journey_title, open_route}}`` for linked journeys.

	Newest-modified journey wins when multiple journeys reference the same package code
	(consistent with ``journey_object_lookup.resolve_journey_code_for_object`` ordering).

	If the caller cannot **read** ``Procurement Journey``, returns ``{}``.
	"""
	codes = [str(c or "").strip() for c in (package_codes or []) if str(c or "").strip()]
	if not codes:
		return {}

	if not frappe.db.exists("DocType", "Procurement Journey"):
		return {}

	try:
		if not frappe.has_permission("Procurement Journey", "read"):
			return {}
	except frappe.PermissionError:
		return {}

	uniq = sorted(set(codes))
	lim = min(len(uniq) * 8, 500)
	if lim < 1:
		lim = 1

	rows = frappe.get_all(
		"Procurement Journey",
		filters={"docstatus": ("!=", 2), "procurement_package_ref": ("in", uniq)},
		fields=["name", "journey_code", "journey_title", "procurement_package_ref", "modified"],
		order_by="modified desc",
		limit=lim,
	)

	seen_refs: set[str] = set()
	out: dict[str, dict[str, str]] = {}
	for r in rows:
		pc = str(r.get("procurement_package_ref") or "").strip()
		if not pc or pc in seen_refs:
			continue
		journey_code_col = str(r.get("journey_code") or "").strip()
		name_pk = str(r.get("name") or "").strip()
		jroute = journey_code_col or name_pk
		if not jroute:
			continue
		seen_refs.add(pc)
		out[pc] = {
			"journey_code": jroute,
			"journey_title": str(r.get("journey_title") or "").strip(),
			"open_route": f"/desk/plc-procurement-journey/{jroute}",
		}
	return out
