# Copyright (c) 2026, KenTender and contributors
"""Shared fixture helpers for the STR-CHG-001 suites.

STR-BR-010 / §12.3: a Fiscal Year target must fall within its plan period,
so a suite whose fixture plans live in the far future (2040–2045, chosen so
they never overlap the canonical §14.3 plan's 2023–2028 authority) needs a
Fiscal Year in that window. ERPNext Fiscal Year rows carry only a date
range; one shared, idempotently-created year is harmless to leave behind
and is deliberately not deleted (a parallel suite may be using it).
"""

from __future__ import annotations

import frappe


def ensure_fiscal_year(start_year: int) -> str:
	name = f"{start_year}-{start_year + 1}"
	if not frappe.db.exists("Fiscal Year", name):
		frappe.get_doc(
			{
				"doctype": "Fiscal Year",
				"year": name,
				"year_start_date": f"{start_year}-07-01",
				"year_end_date": f"{start_year + 1}-06-30",
			}
		).insert(ignore_permissions=True)
	return name
