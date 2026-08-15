"""Governed Procuring Entity and ERPNext Fiscal Year context.

Planning consumes this public Core contract instead of parsing financial-year
labels or inventing reporting currency locally.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, getdate, nowdate


def fiscal_year_label(start: date | str, end: date | str) -> str:
	start_date = getdate(start)
	end_date = getdate(end)
	return f"{start_date.year}/{str(end_date.year)[-2:]}"


def enabled_fiscal_years(*, include_past: bool = False) -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Fiscal Year"):
		frappe.throw(_("Fiscal Year configuration is unavailable."), title="KT_FY_CONFIG_MISSING")
	today = getdate(nowdate())
	filters: dict[str, Any] = {"disabled": 0}
	if not include_past:
		filters["year_end_date"] = [">=", today]
	rows = frappe.get_all(
		"Fiscal Year",
		filters=filters,
		fields=["name", "year", "year_start_date", "year_end_date", "disabled"],
		order_by="year_start_date asc",
	)
	out: list[dict[str, Any]] = []
	for row in rows:
		start = getdate(row.year_start_date)
		end = getdate(row.year_end_date)
		out.append(
			{
				"id": fiscal_year_label(start, end),
				"label": fiscal_year_label(start, end),
				"fiscal_year": row.name,
				"start_date": str(start),
				"end_date": str(end),
				"is_current": start <= today <= end,
				"is_future": start > today,
			}
		)
	return out


def resolve_fiscal_year(financial_year: str) -> dict[str, Any]:
	wanted = cstr(financial_year).strip()
	for row in enabled_fiscal_years(include_past=True):
		if wanted in (row["id"], row["fiscal_year"]):
			if getdate(row["end_date"]) < getdate(nowdate()):
				# Past records remain resolvable for existing Plans, but callers decide
				# whether they can be selected for a new annual Plan.
				row["is_past"] = True
			else:
				row["is_past"] = False
			return row
	frappe.throw(
		_("Financial year {0} is missing or disabled.").format(wanted or _("(blank)")),
		title="KT_FY_NOT_ENABLED",
	)


def procuring_entity_financial_context(
	*, procuring_entity: str, financial_year: str
) -> dict[str, Any]:
	pe = cstr(procuring_entity).strip()
	if not pe or not frappe.db.exists("Procuring Entity", pe):
		frappe.throw(_("Procuring Entity not found."), title="KT_PE_NOT_FOUND")
	row = frappe.db.get_value(
		"Procuring Entity",
		pe,
		["entity_code", "legal_name", "entity_name", "reporting_currency", "status"],
		as_dict=True,
	)
	if cstr(row.status) != "Active":
		frappe.throw(_("Procuring Entity is not active."), title="KT_PE_DISABLED")
	currency = cstr(row.reporting_currency).strip()
	if not currency:
		frappe.throw(
			_("Reporting currency is not configured for this Procuring Entity."),
			title="KT_PE_CURRENCY_MISSING",
		)
	fy = resolve_fiscal_year(financial_year)
	name = cstr(row.legal_name or row.entity_name or pe).strip()
	code = cstr(row.entity_code or pe).strip().removeprefix("PE-")
	return {
		"procuring_entity": pe,
		"procuring_entity_code": code,
		"procuring_entity_label": name,
		"financial_year": fy["id"],
		"fiscal_year": fy["fiscal_year"],
		"period_start": fy["start_date"],
		"period_end": fy["end_date"],
		"currency": currency,
		"title": f"{name} Annual Procurement Plan {fy['id']}",
		"is_current": fy["is_current"],
		"is_future": fy["is_future"],
		"is_past": fy.get("is_past", False),
	}
