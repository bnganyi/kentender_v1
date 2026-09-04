# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.9 §4.4A — the regulator reference register, read side.

Three PPRA-published references change independently of this codebase and are
**effective-dated**: consumers resolve the version in force for the Fiscal
Year they are working on, never the current one (CFG-BR-016). Configuration &
Governance owns the records and never interprets them; a consuming module
decides what blocks and what advises (PLN-CHG-001 v1.12 §7.5: the threshold
matrix blocks, the reservation target and price index advise).

Absence rules (CFG v0.9 §4.4A): a missing threshold matrix for a Fiscal Year
is a configuration defect the consumer fails closed on; a missing reservation
target or price index degrades to "not published" and blocks nothing. This
module reports both through `available` / `published` flags and never raises
for a missing version.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, getdate

from kentender_core.services.configuration_errors import fail_cfg
from kentender_core.services.site_configuration import require_configuration_administrator

DOCTYPE = "Regulatory Reference"

PROCUREMENT_CATEGORIES: tuple[str, ...] = ("Goods", "Works", "Services")

# CFG v0.9 §4.4A / Second Schedule — how a band's maximum is applied.
BASIS_PER_REQUEST = "Per request"
BASIS_PER_ITEM_PER_YEAR = "Per item per financial year"
BASIS_PER_PROCUREMENT = "Per procurement"
BASIS_FUNDS_ALLOCATED = "Funds allocated"
BASIS_SECTION_CONDITIONS = "Section conditions"


def _empty(fiscal_year: str) -> dict[str, Any]:
	return {
		"fiscal_year": fiscal_year,
		"available": False,
		"reference": "",
		"effective_from": "",
		"gazette_reference": "",
		"threshold_matrix": [],
		"reservation": {"published": False, "target_percent": None, "county_target_percent": None, "categories": []},
		"exclusive_preference": {"published": False, "works_amount": None, "goods_services_amount": None},
		"market_price_index": {"published": False, "rows": []},
		"schedule_buffers": [],
	}


def _version_in_force(fiscal_year: str) -> str:
	rows = frappe.get_all(
		DOCTYPE,
		filters={"fiscal_year": fiscal_year, "status": "Active"},
		fields=["name", "effective_from"],
		order_by="effective_from desc, creation desc",
		limit_page_length=1,
	)
	return rows[0]["name"] if rows else ""


def get_regulatory_reference(fiscal_year: str) -> dict[str, Any]:
	"""The register in force for `fiscal_year`, as one read-only projection.

	Never resolves by today's date (CFG-BR-016). A superseded version for the
	same year is retained but never returned; a year with no version returns
	`available = False` with every section marked unpublished.
	"""
	fiscal_year = (fiscal_year or "").strip()
	if not fiscal_year:
		return _empty(fiscal_year)
	name = _version_in_force(fiscal_year)
	if not name:
		return _empty(fiscal_year)
	doc = frappe.get_cached_doc(DOCTYPE, name)
	bands = [
		{
			"procurement_category": row.procurement_category,
			"procurement_method": row.procurement_method,
			"max_amount": flt(row.max_amount),
			"basis": row.basis,
			"statutory_reference": row.statutory_reference or "",
		}
		for row in (doc.threshold_bands or [])
	]
	categories = [
		{
			"category": row.category,
			"advantage_rank": int(row.advantage_rank or 0),
			"is_regional": bool(row.is_regional),
			"statutory_reference": row.statutory_reference or "",
		}
		for row in (doc.reservation_categories or [])
	]
	categories.sort(key=lambda r: (r["advantage_rank"], r["category"]))
	target = flt(doc.reservation_target_percent) if doc.reservation_target_percent is not None else None
	return {
		"fiscal_year": fiscal_year,
		"available": bool(bands),
		"reference": doc.name,
		"effective_from": str(doc.effective_from or ""),
		"gazette_reference": doc.gazette_reference or "",
		"threshold_matrix": bands,
		"reservation": {
			"published": bool(categories) and bool(target),
			"target_percent": target if target else None,
			"county_target_percent": (
				flt(doc.county_resident_target_percent) if doc.county_resident_target_percent else None
			),
			"categories": categories,
		},
		"exclusive_preference": {
			"published": bool(doc.exclusive_preference_works_amount or doc.exclusive_preference_goods_services_amount),
			"works_amount": flt(doc.exclusive_preference_works_amount) or None,
			"goods_services_amount": flt(doc.exclusive_preference_goods_services_amount) or None,
		},
		"market_price_index": {
			"published": bool(doc.market_price_index_published),
			"rows": [
				{
					"procurement_category": row.procurement_category,
					"item": row.item,
					"unit": row.unit or "",
					"indicative_price": flt(row.indicative_price),
				}
				for row in (doc.market_prices or [])
			],
		},
		"schedule_buffers": [
			{
				"procurement_category": row.procurement_category,
				"procurement_method": row.procurement_method,
				"award_approval_buffer_days": int(row.award_approval_buffer_days or 0),
				"notification_buffer_days": int(row.notification_buffer_days or 0),
			}
			for row in (doc.schedule_buffers or [])
		],
	}


def register_regulatory_reference(
	*,
	fiscal_year: str,
	effective_from: str,
	gazette_reference: str = "",
	threshold_bands: list[dict[str, Any]] | None = None,
	reservation_categories: list[dict[str, Any]] | None = None,
	reservation_target_percent: float | None = None,
	county_resident_target_percent: float | None = None,
	exclusive_preference_works_amount: float | None = None,
	exclusive_preference_goods_services_amount: float | None = None,
	market_prices: list[dict[str, Any]] | None = None,
	schedule_buffers: list[dict[str, Any]] | None = None,
	fixture_namespace: str = "",
) -> dict[str, Any]:
	"""Register one new version for a Fiscal Year (Administrator / System
	Manager only). Idempotent on `(fiscal_year, gazette_reference)`: a
	re-run with the same gazette reference returns the existing version
	without creating a second one. A different gazette reference supersedes
	the earlier Active version (retained).
	"""
	require_configuration_administrator()
	fiscal_year = (fiscal_year or "").strip()
	if not frappe.db.exists("Fiscal Year", fiscal_year):
		fail_cfg("CFG_PE_INVALID", "That financial year does not exist.")
	gazette = (gazette_reference or "").strip()
	if gazette:
		existing = frappe.db.get_value(
			DOCTYPE, {"fiscal_year": fiscal_year, "gazette_reference": gazette}, "name"
		)
		if existing:
			return {"reference": existing, "created": False}
	for band in threshold_bands or []:
		if band.get("procurement_category") not in PROCUREMENT_CATEGORIES:
			fail_cfg("CFG_PE_INVALID", "Each threshold band needs a goods, works or services category.")
		if not frappe.db.exists("Procurement Method", band.get("procurement_method")):
			fail_cfg("CFG_PE_INVALID", f"Unknown procurement method: {band.get('procurement_method')}.")
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"fiscal_year": fiscal_year,
			"effective_from": getdate(effective_from),
			"gazette_reference": gazette,
			"status": "Active",
			"reservation_target_percent": reservation_target_percent,
			"county_resident_target_percent": county_resident_target_percent,
			"exclusive_preference_works_amount": exclusive_preference_works_amount,
			"exclusive_preference_goods_services_amount": exclusive_preference_goods_services_amount,
			"market_price_index_published": 1 if market_prices else 0,
			"threshold_bands": threshold_bands or [],
			"reservation_categories": reservation_categories or [],
			"market_prices": market_prices or [],
			"schedule_buffers": schedule_buffers or [],
			"fixture_namespace": fixture_namespace,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"reference": doc.name, "created": True}


def purge_fixture_references(fixture_namespace: str) -> int:
	"""Test/fixture cleanup only — production versions are never deleted."""
	names = frappe.get_all(DOCTYPE, filters={"fixture_namespace": fixture_namespace}, pluck="name")
	for name in names:
		doc = frappe.get_doc(DOCTYPE, name)
		doc.flags.kt_fixture_purge = True
		doc.delete(ignore_permissions=True)
	return len(names)
