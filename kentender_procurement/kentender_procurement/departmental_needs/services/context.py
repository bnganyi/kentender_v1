from __future__ import annotations

from kentender_core.services.financial_context import enabled_fiscal_years, resolve_fiscal_year

from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.permissions import creation_contexts


def selectable_financial_year(financial_year: str) -> dict:
	row = resolve_fiscal_year(financial_year)
	if row.get("is_future"):
		fail(
			"NDS_INTAKE_WINDOW_NOT_CONFIGURED",
			"Future-year Departmental Needs intake is unavailable until an intake window is configured.",
		)
	if row.get("is_past"):
		fail("NDS_FINANCIAL_YEAR_CLOSED", "The selected financial year is closed for Departmental Needs intake.")
	return row


def resolve_creation_context(*, user: str | None = None) -> dict:
	contexts = creation_contexts(user)
	return {
		"ok": bool(contexts),
		"outcome": "READY" if contexts else "NO_ACTIVE_OPERATIONAL_ASSIGNMENT",
		"contexts": contexts,
		"requires_selection": len(contexts) > 1,
		"financial_years": [row for row in enabled_fiscal_years() if not row.get("is_future") and not row.get("is_past")],
	}
