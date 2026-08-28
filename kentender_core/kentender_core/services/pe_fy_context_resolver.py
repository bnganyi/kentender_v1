"""Resolve a Procuring Entity + fiscal-year signal to an existing PE Fiscal Year Context.

Read-only: never creates or mutates a PE Fiscal Year Context. Built for the
AUTH-ADR-001 Phase 2 backfill patch (kentender_core.patches.v1_0.backfill_pe_fy_context_links),
which needs to resolve four differently-shaped business doctypes (a free-text
Financial Year label on two, a bare date range on the other two) against the
same small set of governed contexts without guessing at an unresolvable match.
"""

from __future__ import annotations

import frappe


def resolve_by_financial_year_label(procuring_entity: str, financial_year_label: str) -> str | None:
	"""Match by an exact `Financial Year.label` string (e.g. "2027/28")."""
	if not procuring_entity or not financial_year_label:
		return None
	label = financial_year_label.strip()
	if not label:
		return None
	financial_year = frappe.db.get_value("Financial Year", {"label": label}, "name")
	if not financial_year:
		return None
	return frappe.db.get_value(
		"PE Fiscal Year Context",
		{"procuring_entity": procuring_entity, "financial_year": financial_year},
		"name",
	)


def resolve_by_date_overlap(procuring_entity: str, period_start, period_end) -> str | None:
	"""Match the PE Fiscal Year Context whose Financial Year period overlaps the given range."""
	if not procuring_entity or not period_start or not period_end:
		return None
	contexts = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"procuring_entity": procuring_entity},
		fields=["name", "financial_year"],
	)
	for ctx in contexts:
		fy = frappe.db.get_value("Financial Year", ctx.financial_year, ["start_date", "end_date"], as_dict=True)
		if fy and fy.start_date and fy.end_date and fy.start_date <= period_end and fy.end_date >= period_start:
			return ctx.name
	return None
