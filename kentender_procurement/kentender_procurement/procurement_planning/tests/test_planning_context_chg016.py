from unittest import TestCase
from unittest.mock import patch

from kentender_procurement.procurement_planning.services.demand_financial_year import (
	DEMAND_FINANCIAL_YEAR_MISMATCH,
	DEMAND_REQUIRED_BY_MISSING,
	DEMAND_REQUIRED_BY_OUTSIDE_CONFIGURED_FY,
	INFERRED_FROM_DEMAND_DATE,
	PLANNING_FINANCIAL_YEAR_REQUIRED,
	demand_financial_year_issue,
	derive_demand_financial_year,
	resolve_demand_financial_year,
)
from kentender_procurement.procurement_planning.services.planning_context import (
	FY_DEFAULT,
	PE_DEFAULT,
	_default_year,
	select_planning_context,
)


PERIODS = [
	{"id": "2027/28", "label": "2027/28", "start_date": "2027-07-01", "end_date": "2028-06-30", "is_current": True, "is_future": False, "is_past": False},
	{"id": "2028/29", "label": "2028/29", "start_date": "2028-07-01", "end_date": "2029-06-30", "is_current": False, "is_future": True, "is_past": False},
	{"id": "2026/27", "label": "2026/27", "start_date": "2026-07-01", "end_date": "2027-06-30", "is_current": False, "is_future": False, "is_past": True},
]


class TestPlanningContextChg016(TestCase):
	def test_default_precedence_current_future_past_then_current_without_plan(self) -> None:
		self.assertEqual(_default_year(PERIODS, {"2027/28", "2028/29", "2026/27"}), "2027/28")
		self.assertEqual(_default_year(PERIODS, {"2028/29", "2026/27"}), "2028/29")
		self.assertEqual(_default_year(PERIODS, {"2026/27"}), "2026/27")
		self.assertEqual(_default_year(PERIODS, set()), "2027/28")

	@patch("kentender_procurement.procurement_planning.services.planning_context.frappe.defaults.set_user_default")
	@patch("kentender_procurement.procurement_planning.services.planning_context.resolve_planning_context")
	def test_deliberate_selection_is_the_only_preference_write(self, resolve, set_default) -> None:
		resolve.return_value = {"procuring_entity": "PE-MOH", "financial_year": "2027/28"}
		result = select_planning_context(procuring_entity="PE-MOH", financial_year="2027/28", user="planner@example.test")
		self.assertEqual(result["financial_year"], "2027/28")
		set_default.assert_any_call(PE_DEFAULT, "PE-MOH", user="planner@example.test")
		set_default.assert_any_call(FY_DEFAULT, "2027/28", user="planner@example.test")
		self.assertEqual(set_default.call_count, 2)

	@patch("kentender_procurement.procurement_planning.services.demand_financial_year.enabled_fiscal_years", return_value=PERIODS)
	def test_required_by_inclusive_boundaries_and_exact_issues(self, _periods) -> None:
		self.assertEqual(derive_demand_financial_year("2027-07-01"), ("2027/28", None))
		self.assertEqual(derive_demand_financial_year("2028-06-30"), ("2027/28", None))
		self.assertEqual(derive_demand_financial_year(None)[1]["code"], DEMAND_REQUIRED_BY_MISSING)
		self.assertEqual(derive_demand_financial_year("2035-01-01")[1]["code"], DEMAND_REQUIRED_BY_OUTSIDE_CONFIGURED_FY)
		self.assertEqual(demand_financial_year_issue("2027-12-31", "2028/29")["code"], DEMAND_FINANCIAL_YEAR_MISMATCH)
		incomplete = resolve_demand_financial_year("2027-12-31", "")
		self.assertEqual(incomplete["derived_financial_year"], "2027/28")
		self.assertEqual(incomplete["resolved_source"], INFERRED_FROM_DEMAND_DATE)
		self.assertEqual(incomplete["issue_code"], PLANNING_FINANCIAL_YEAR_REQUIRED)
