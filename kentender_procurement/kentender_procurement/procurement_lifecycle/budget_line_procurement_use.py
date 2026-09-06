# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-003 / LV-R5-003-02 — read-only procurement-use aggregation for a Budget Line.

Returns funding confirmation (budget meta + amounts) plus linked procurement journeys,
demands, and packages for desk panels.  Navigation aggregate only (ADR-PLC-002).

Data model relationships (WORKS seed):
  Procurement Journey.budget_line_ref  → Budget Line.name
  Procurement Journey.demand_ref       → Demand.demand_id  (NOT Demand.name)
  Procurement Journey.procurement_package_ref → Procurement Package.name
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import frappe


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _journey_route(journey_code: str | None, fallback_name: str) -> str:
	code = (journey_code or "").strip() or (fallback_name or "").strip()
	if not code:
		return "/desk/plc-procurement-journey"
	return f"/desk/plc-procurement-journey/{code}"


def _fetch_demands(demand_ids: list[str]) -> list[dict[str, Any]]:
	"""Fetch Demand rows by ``demand_id`` (business code, not doc name)."""
	if not demand_ids:
		return []
	unique_ids = list(dict.fromkeys(i for i in demand_ids if i))
	if not unique_ids:
		return []
	rows = frappe.get_all(
		"Demand",
		filters={"demand_id": ["in", unique_ids]},
		fields=["name", "demand_id", "title", "status"],
		order_by="modified desc",
		limit=200,
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		docname = (r.get("name") or "").strip()
		out.append(
			{
				"id": docname,
				"demand_id": (r.get("demand_id") or "").strip(),
				"title": (r.get("title") or "").strip(),
				"status": (r.get("status") or "").strip(),
				"list_route": f"/app/demand/{quote(docname, safe='')}",
			}
		)
	return out


def _fetch_packages(package_names: list[str]) -> list[dict[str, Any]]:
	"""Fetch Procurement Package rows by name."""
	if not package_names:
		return []
	unique_names = list(dict.fromkeys(n for n in package_names if n))
	if not unique_names:
		return []
	rows = frappe.get_all(
		"Procurement Package",
		filters={"name": ["in", unique_names]},
		fields=["name", "package_code", "package_name", "status"],
		order_by="modified desc",
		limit=200,
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		docname = (r.get("name") or "").strip()
		code = (r.get("package_code") or docname).strip()
		title = (r.get("package_name") or "").strip()
		out.append(
			{
				"id": docname,
				"code": code,
				"name": title,
				"status": (r.get("status") or "").strip(),
				"list_route": f"/app/procurement-package/{quote(docname, safe='')}",
			}
		)
	return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_procurement_use_payload(budget_line_name: str) -> dict[str, Any]:
	"""Return funding confirmation + linked journeys / demands / packages.

	Caller is responsible for enforcing permissions before calling this function.

	Args:
		budget_line_name: Frappe ``name`` (primary key) of the ``Budget Line`` document.

	Returns:
		A dict with ``ok=True`` and aggregated data, or ``ok=False`` with an error.
	"""
	nm = (budget_line_name or "").strip()
	if not nm:
		return {
			"ok": False,
			"error": "MISSING_PARAMS",
			"message": "budget_line_name is required.",
			"journeys": [],
			"demands": [],
			"packages": [],
		}

	bl_row = frappe.db.get_value(
		"Procurement Budget Line",
		nm,
		["generated_reference", "budget"],
		as_dict=True,
	)
	if not bl_row:
		return {
			"ok": False,
			"error": "NOT_FOUND",
			"message": "Budget Line not found.",
			"journeys": [],
			"demands": [],
			"packages": [],
		}

	# BUD-CHG-001 v1.2 §4.2/§4.3/§4.4 — Budget Line no longer carries a title
	# or amounts directly; those live on the Active Budget Version's Budget
	# Line Version, with Reserved/Committed always computed live (§5), never
	# stored. This stays a raw, permission-free read (the caller already
	# enforces Journey visibility via `_require_journey_read_permission`) —
	# not routed through kentender_budget's own capability-gated read API,
	# which would add an unrelated Budget-role requirement to this panel.
	budget_meta: dict[str, Any] = {}
	line_title = ""
	amount_allocated = 0.0
	amount_reserved = 0.0
	amount_available = 0.0
	if bl_row.get("budget"):
		budget_row = frappe.db.get_value(
			"Procurement Budget", bl_row["budget"], ["title", "fiscal_year", "currency"], as_dict=True
		)
		if budget_row:
			budget_meta = dict(budget_row)
		version_row = frappe.db.get_value(
			"Procurement Budget Version", {"budget": bl_row["budget"], "status": "Active"}, ["name", "status"], as_dict=True
		)
		if version_row:
			budget_meta["status"] = version_row.status
			line_version_row = frappe.db.get_value(
				"Procurement Budget Line Version",
				{"budget_version": version_row.name, "budget_line": nm},
				["title", "approved_amount"],
				as_dict=True,
			)
			if line_version_row:
				line_title = (line_version_row.get("title") or "").strip()
				amount_allocated = frappe.utils.flt(line_version_row.get("approved_amount"))
				amount_reserved = frappe.utils.flt(
					frappe.db.sql(
						"select coalesce(sum(remaining_amount), 0) from `tabFunding Reservation` "
						"where budget_line = %s and status in ('Active', 'Partially Converted', 'Needs Attention')",
						(nm,),
					)[0][0]
				)
				reservation_names = frappe.get_all("Funding Reservation", filters={"budget_line": nm}, pluck="name")
				amount_committed = 0.0
				if reservation_names:
					amount_committed = frappe.utils.flt(
						frappe.db.sql(
							"select coalesce(sum(current_amount), 0) from `tabProcurement Commitment` "
							"where reservation in %s and status = 'Active'",
							(reservation_names,),
						)[0][0]
					)
				amount_available = amount_allocated - amount_reserved - amount_committed

	# Journeys linked to this budget line
	journey_rows = frappe.get_all(
		"Procurement Journey",
		filters={"budget_line_ref": nm},
		fields=[
			"name",
			"journey_code",
			"journey_title",
			"current_stage_label",
			"current_status_category",
			"demand_ref",
			"procurement_package_ref",
		],
		order_by="modified desc",
		limit=200,
	)

	journeys_out: list[dict[str, Any]] = []
	demand_ids: list[str] = []
	package_names: list[str] = []

	for jr in journey_rows:
		jc = (jr.get("journey_code") or jr.get("name") or "").strip()
		jn = (jr.get("name") or "").strip()
		journeys_out.append(
			{
				"journey_code": jc,
				"journey_title": (jr.get("journey_title") or "").strip(),
				"current_stage_label": (jr.get("current_stage_label") or "").strip(),
				"current_status_category": (jr.get("current_status_category") or "").strip(),
				"open_route": _journey_route(jr.get("journey_code"), jn),
			}
		)
		if jr.get("demand_ref"):
			demand_ids.append(jr["demand_ref"])
		if jr.get("procurement_package_ref"):
			package_names.append(jr["procurement_package_ref"])

	demands_out = _fetch_demands(demand_ids)
	packages_out = _fetch_packages(package_names)

	bl_code = (bl_row.get("generated_reference") or nm).strip()

	return {
		"ok": True,
		"budget_line_name": nm,
		"budget_line_code": bl_code,
		"budget_line_display_name": line_title,
		# Funding confirmation
		"budget_doc_name": bl_row.get("budget") or "",
		"budget_name": budget_meta.get("title") or "",
		"fiscal_year": budget_meta.get("fiscal_year"),
		"budget_status": budget_meta.get("status") or "",
		"currency": budget_meta.get("currency") or "",
		"amount_allocated": amount_allocated,
		"amount_reserved": amount_reserved,
		"amount_available": amount_available,
		# Linked procurement objects
		"journeys": journeys_out,
		"demands": demands_out,
		"packages": packages_out,
	}
