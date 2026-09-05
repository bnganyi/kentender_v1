# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.1 `ResolvePlanningContexts` / §10 — the Financial
Year is a visible, changeable filter derived from configured records; there
is no Procuring Entity to select and no per-user year grant (PLN-AC-001,
PLN-AC-060)."""

from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from kentender_procurement.procurement_planning.services.planning_context import (
	PLANNING_MODULE,
	_default_year,
	resolve_planning_context,
	select_planning_context,
)

BASE = "kentender_procurement.procurement_planning.services.planning_context"


def _year(id_, *, current=False, future=False, past=False, intake=False, plan=False):
	return {
		"id": id_, "label": f"FY {id_}", "start_date": f"{id_[:4]}-07-01", "end_date": f"{int(id_[:4]) + 1}-06-30",
		"is_current": current, "is_future": future, "is_past": past, "intake_open": intake, "has_open_plan": plan,
		"planning_open": True,
	}


PERIODS = [
	_year("2026-2027", past=True),
	_year("2027-2028", current=True),
	_year("2028-2029", future=True),
]


class TestDefaultYear(TestCase):
	def test_default_precedence_intake_open_then_open_plan_then_current_then_future(self) -> None:
		self.assertEqual(_default_year([dict(PERIODS[0], intake_open=True), PERIODS[1], PERIODS[2]]), "2026-2027")
		self.assertEqual(_default_year([PERIODS[0], PERIODS[1], dict(PERIODS[2], has_open_plan=True)]), "2028-2029")
		self.assertEqual(_default_year(PERIODS), "2027-2028")
		self.assertEqual(_default_year([PERIODS[2]]), "2028-2029")
		self.assertEqual(_default_year([]), "")


class TestResolution(TestCase):
	def test_no_responsibility_resolves_to_no_scope_without_a_selector(self) -> None:
		with patch(f"{BASE}.authz.holds_any_planning_responsibility", return_value=False), patch(f"{BASE}._site", return_value={"pe_name": "x", "pe_code": "PE-X"}):
			result = resolve_planning_context(user="nobody@example.test")
		self.assertTrue(result["no_scope"])
		self.assertEqual(result["financial_years"], [])
		self.assertNotIn("procuring_entities", result)

	def test_selection_round_trips_through_the_module_preference(self) -> None:
		import frappe

		user = "Administrator"
		frappe.defaults.clear_user_default("kt_planning_financial_year", user)
		try:
			with patch(f"{BASE}.authz.holds_any_planning_responsibility", return_value=True), patch(
				f"{BASE}.selectable_years", return_value=list(PERIODS)
			), patch(f"{BASE}._site", return_value={"pe_name": "x", "pe_code": "PE-X"}):
				selected = select_planning_context(financial_year="2028-2029", user=user)
				self.assertEqual(selected["financial_year"], "2028-2029")
				self.assertEqual(selected["resolved_financial_year_source"], "selected")
				restored = resolve_planning_context(user=user)
			self.assertEqual(restored["financial_year"], "2028-2029")
			self.assertEqual(restored["resolved_financial_year_source"], "saved_default")
			self.assertFalse(restored["selection_required"])
		finally:
			frappe.defaults.clear_user_default("kt_planning_financial_year", user)

	def test_an_unoffered_year_is_refused_not_trapped(self) -> None:
		import frappe

		with patch(f"{BASE}.authz.holds_any_planning_responsibility", return_value=True), patch(
			f"{BASE}.selectable_years", return_value=list(PERIODS)
		), patch(f"{BASE}._site", return_value={"pe_name": "x", "pe_code": "PE-X"}):
			with self.assertRaises(frappe.ValidationError):
				resolve_planning_context(financial_year="2099-2100", user="Administrator")
		self.assertEqual(PLANNING_MODULE, "planning")
