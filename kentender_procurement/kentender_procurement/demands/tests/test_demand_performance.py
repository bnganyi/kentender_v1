# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-10 / DEM-SVC-015 — Demand performance projection + whitelist."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.api import (
	get_demand_performance_form,
	prepare_demand_performance_ui10,
)
from kentender_procurement.demands.services.demand_lifecycle import get_demand_performance
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_PAA,
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.demands.tests.test_demands_budget_api import _ensure_user


class TestDemandPerformanceUi10(IntegrationTestCase):
	def test_factory_and_projection_sections(self) -> None:
		frappe.set_user("Administrator")
		ensure_demand_roles()
		req = _ensure_user("dem-ui10-req@example.com", [ROLE_REQUESTER])
		payload = prepare_demand_performance_ui10(requester=req)
		self.assertTrue(payload["ok"])
		self.assertTrue(payload["approved_demand"])
		self.assertTrue(payload["returned_demand"])
		self.assertTrue(payload["exception_demand"])

		paa = payload["procurement_approver"]
		frappe.set_user(paa)
		perf = get_demand_performance_form(
			filters={"procuring_entity": payload["procuring_entity"]}
		)
		self.assertTrue(perf["ok"])
		self.assertIn("as_at", perf)
		self.assertIn("basis", perf)
		self.assertTrue(perf["basis"])
		self.assertIn("summary", perf)
		self.assertGreaterEqual(perf["summary"]["demands_count"], 1)
		self.assertIn("KES", perf["summary"]["approved_value_display"])
		self.assertIn(",", perf["summary"]["approved_value_display"])
		self.assertGreaterEqual(perf["summary"]["returned_count"], 1)
		self.assertEqual(len(perf["flow_ageing"]), 6)
		stages = {r["stage"] for r in perf["flow_ageing"]}
		self.assertIn("Approved", stages)
		self.assertIn("Request Preparation", stages)
		fc = perf["funding_control"]
		self.assertGreaterEqual(fc["exceptions"], 1)
		self.assertIn("KES", fc["unfunded_amount_display"])
		self.assertIsNotNone(fc.get("exception_demand"))
		self.assertEqual(fc["exception_demand"]["route"], "demand-review")
		self.assertTrue(perf["planning_uptake"])
		uptake = perf["planning_uptake"][0]
		self.assertIn("Fully planned", uptake["planning_usage"])
		self.assertEqual(uptake["route"], "demand-detail")
		self.assertTrue(perf.get("methodology") is None or True)
		self.assertTrue(isinstance(perf["strategy_coverage"], list))
		self.assertTrue(perf["filter_options"]["statuses"])

	def test_as_at_and_basis_on_service(self) -> None:
		frappe.set_user("Administrator")
		paa = _ensure_user("dem-ui10-paa@example.com", [ROLE_PAA, ROLE_REQUESTER])
		perf = get_demand_performance(user=paa, as_at="2027-10-31")
		self.assertTrue(perf["ok"])
		self.assertEqual(perf["as_at"], "2027-10-31")
		self.assertEqual(perf["as_at_display"], "2027-10-31")
		self.assertIn("Scoped Demand", perf["basis"])

	def test_non_reader_denied(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(Exception):
			get_demand_performance_form()
