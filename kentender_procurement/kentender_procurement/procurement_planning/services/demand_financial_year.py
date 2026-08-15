"""Derive a Demand's Planning FY from its approved required-by date."""

from __future__ import annotations

from typing import Any

from frappe.utils import getdate

from kentender_core.services.financial_context import enabled_fiscal_years

DEMAND_REQUIRED_BY_MISSING = "DEMAND_REQUIRED_BY_MISSING"
DEMAND_REQUIRED_BY_OUTSIDE_CONFIGURED_FY = "DEMAND_REQUIRED_BY_OUTSIDE_CONFIGURED_FY"
DEMAND_FINANCIAL_YEAR_MISMATCH = "DEMAND_FINANCIAL_YEAR_MISMATCH"
PLANNING_FINANCIAL_YEAR_REQUIRED = "PLANNING_FINANCIAL_YEAR_REQUIRED"
INFERRED_FROM_DEMAND_DATE = "inferred_from_demand_date"

ISSUE_MESSAGES = {
	DEMAND_REQUIRED_BY_MISSING: "This Demand has no approved required-by date and cannot be added to a Plan. Amend and reapprove the Demand.",
	DEMAND_REQUIRED_BY_OUTSIDE_CONFIGURED_FY: "The approved required-by date does not fall within a configured Planning financial year.",
	DEMAND_FINANCIAL_YEAR_MISMATCH: "This Demand belongs to a different financial year and cannot be added to the selected Plan.",
	PLANNING_FINANCIAL_YEAR_REQUIRED: "Select a Planning financial year before adding this Demand.",
}


def derive_demand_financial_year(required_by_date: Any) -> tuple[str | None, dict[str, str] | None]:
	if not required_by_date:
		code = DEMAND_REQUIRED_BY_MISSING
		return None, {"code": code, "reason": ISSUE_MESSAGES[code]}
	required = getdate(required_by_date)
	for period in enabled_fiscal_years(include_past=True):
		if getdate(period["start_date"]) <= required <= getdate(period["end_date"]):
			return period["id"], None
	code = DEMAND_REQUIRED_BY_OUTSIDE_CONFIGURED_FY
	return None, {"code": code, "reason": ISSUE_MESSAGES[code]}


def demand_financial_year_issue(required_by_date: Any, selected_financial_year: str) -> dict[str, str] | None:
	return resolve_demand_financial_year(required_by_date, selected_financial_year)["issue"]


def resolve_demand_financial_year(required_by_date: Any, selected_financial_year: str | None = None) -> dict[str, Any]:
	"""Return the derived FY and an explicit issue; never silently cross-map FYs."""
	derived, issue = derive_demand_financial_year(required_by_date)
	result: dict[str, Any] = {
		"derived_financial_year": derived or "",
		"resolved_source": INFERRED_FROM_DEMAND_DATE,
		"issue": issue,
		"issue_code": issue["code"] if issue else "",
	}
	selected = str(selected_financial_year or "").strip()
	if not issue and not selected:
		code = PLANNING_FINANCIAL_YEAR_REQUIRED
		result["issue"] = {"code": code, "reason": ISSUE_MESSAGES[code], "derived_financial_year": derived or ""}
		result["issue_code"] = code
	elif not issue and derived != selected:
		code = DEMAND_FINANCIAL_YEAR_MISMATCH
		result["issue"] = {"code": code, "reason": ISSUE_MESSAGES[code], "derived_financial_year": derived or ""}
		result["issue_code"] = code
	return result
