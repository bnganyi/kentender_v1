"""AUTH-ADR-001 Phase 2 — backfill pe_fy_context on the 4 retrofitted business doctypes.

Idempotent, best-effort: a record with no resolvable Financial Year/date match
is left with pe_fy_context unset (still scoped by its existing Procuring
Entity link — ADR §6.1 explicitly allows PE-only scope where no PE/FY record
applies) and counted in the summary log, never blocked or guessed at.
"""

from __future__ import annotations

import frappe

from kentender_core.services.pe_fy_context_resolver import (
	resolve_by_date_overlap,
	resolve_by_financial_year_label,
)

# (doctype, procuring-entity fieldname, resolution kind, source field(s))
_LABEL_TARGETS = [
	("Departmental Need", "procuring_entity", "target_financial_year"),
	("Procurement Plan", "procuring_entity", "financial_year"),
]
_DATE_RANGE_TARGETS = [
	("Budget", "procuring_entity", "start_date", "end_date"),
	("Strategic Plan", "procuring_entity_id", "period_start", "period_end"),
]


def execute() -> None:
	for doctype, pe_field, label_field in _LABEL_TARGETS:
		if not frappe.db.has_column(doctype, "pe_fy_context"):
			continue
		resolved = unresolved = 0
		rows = frappe.get_all(
			doctype,
			filters={"pe_fy_context": ["in", ["", None]]},
			fields=["name", pe_field, label_field],
		)
		for row in rows:
			ctx = resolve_by_financial_year_label(row.get(pe_field), row.get(label_field))
			if ctx:
				frappe.db.set_value(doctype, row.name, "pe_fy_context", ctx, update_modified=False)
				resolved += 1
			else:
				unresolved += 1
		frappe.logger("auth_migration").info(f"{doctype}: pe_fy_context backfill resolved={resolved} unresolved={unresolved}")

	for doctype, pe_field, start_field, end_field in _DATE_RANGE_TARGETS:
		if not frappe.db.has_column(doctype, "pe_fy_context"):
			continue
		resolved = unresolved = 0
		rows = frappe.get_all(
			doctype,
			filters={"pe_fy_context": ["in", ["", None]]},
			fields=["name", pe_field, start_field, end_field],
		)
		for row in rows:
			ctx = resolve_by_date_overlap(row.get(pe_field), row.get(start_field), row.get(end_field))
			if ctx:
				frappe.db.set_value(doctype, row.name, "pe_fy_context", ctx, update_modified=False)
				resolved += 1
			else:
				unresolved += 1
		frappe.logger("auth_migration").info(f"{doctype}: pe_fy_context backfill resolved={resolved} unresolved={unresolved}")
