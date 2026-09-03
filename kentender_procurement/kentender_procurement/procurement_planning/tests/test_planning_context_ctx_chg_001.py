"""CTX-CHG-001 Phase E — Planning context on the corrected persistence model.

Split out of test_planning_context_chg016.py, which no longer imports (it
still references the retired Demands-era demand_financial_year service and has
been un-runnable since that module's deletion).
"""

from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from kentender_procurement.procurement_planning.services.planning_context import (
	PLANNING_MODULE,
	_default_year,
	resolve_planning_context,
	select_planning_context,
)

PERIODS = [
	{"id": "2027/28", "label": "2027/28", "start_date": "2027-07-01", "end_date": "2028-06-30", "is_current": True, "is_future": False, "is_past": False},
	{"id": "2028/29", "label": "2028/29", "start_date": "2028-07-01", "end_date": "2029-06-30", "is_current": False, "is_future": True, "is_past": False},
	{"id": "2026/27", "label": "2026/27", "start_date": "2026-07-01", "end_date": "2027-06-30", "is_current": False, "is_future": False, "is_past": True},
]


class TestPlanningContextPersistence(TestCase):
	def test_default_precedence_current_future_past_then_current_without_plan(self) -> None:
		self.assertEqual(_default_year(PERIODS, {"2027/28", "2028/29", "2026/27"}), "2027/28")
		self.assertEqual(_default_year(PERIODS, {"2028/29", "2026/27"}), "2028/29")
		self.assertEqual(_default_year(PERIODS, {"2026/27"}), "2026/27")
		self.assertEqual(_default_year(PERIODS, set()), "2027/28")

	@patch("kentender_core.services.working_context.select_module_fy")
	@patch("kentender_core.services.working_context.select_working_pe")
	@patch("kentender_procurement.procurement_planning.services.planning_context.resolve_planning_context")
	def test_deliberate_selection_writes_the_corrected_model(self, resolve, select_pe, select_fy) -> None:
		# CTX-CHG-001 — the write goes to the global working PE plus this
		# module's own kt_planning_financial_year, nothing else.
		resolve.return_value = {"procuring_entity": "PE-MOH", "financial_year": "2027/28"}
		result = select_planning_context(procuring_entity="PE-MOH", financial_year="2027/28", user="planner@example.test")
		self.assertEqual(result["financial_year"], "2027/28")
		select_pe.assert_called_once_with("PE-MOH", "planner@example.test")
		select_fy.assert_called_once_with(
			PLANNING_MODULE, "2027/28", "planner@example.test", offered=["2027/28"]
		)


class TestPlanningContextRoundTrip(TestCase):
	"""A selection must actually restore on the next request.

	The old Title-Case default keys never round-tripped (frappe.defaults'
	is_a_user_permission_key rerouted them), so "remember my selection" was a
	silent no-op that this exact test would have caught. Runs against the real
	frappe.defaults storage with the eligibility helpers mocked.
	"""

	def test_selection_restores_on_the_next_resolution(self) -> None:
		import frappe

		user = "Administrator"
		entities = [{"id": "PE-RT", "code": "PE-RT", "name": "Round Trip", "label": "Round Trip"}]
		years = (
			[dict(PERIODS[0], has_open_plan=True, planning_open=True),
			 dict(PERIODS[1], has_open_plan=False, planning_open=True)],
			{"2027/28"},
		)
		base = "kentender_procurement.procurement_planning.services.planning_context"
		frappe.defaults.clear_user_default("kt_planning_financial_year", user)
		try:
			with patch(f"{base}._authorised_entities", return_value=entities), patch(
				f"{base}._selectable_years", return_value=years
			), patch(
				"kentender_core.services.working_context.select_working_pe"
			), patch(
				"kentender_core.services.working_context.get_working_pe",
				return_value={"selected": {"id": "PE-RT"}},
			):
				select_planning_context(procuring_entity="PE-RT", financial_year="2028/29", user=user)
				restored = resolve_planning_context(user=user)
			self.assertEqual(restored["financial_year"], "2028/29")
			self.assertEqual(restored["resolved_financial_year_source"], "saved_default")
		finally:
			frappe.defaults.clear_user_default("kt_planning_financial_year", user)
