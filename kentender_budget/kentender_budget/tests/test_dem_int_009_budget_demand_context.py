"""DEM-INT-009 — Budget check/reserve resolves the MVP Demand contract."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.services.budget_check_reserve_contracts import (
	_demand_context,
	demand_doctype_available,
)


DEMAND_CODE = "DEM-INT-009-TEST"


class TestDemInt009BudgetDemandContext(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.procuring_entity = frappe.db.get_value(
			"Procuring Entity",
			{"entity_code": "PE-MOH"},
			"name",
		)
		cls.owner_org_unit = frappe.db.get_value(
			"Organisation Unit",
			{"procuring_entity": cls.procuring_entity},
			"name",
		)
		if not cls.procuring_entity or not cls.owner_org_unit:
			raise AssertionError("Budget fixture must provide Demand ownership context")

	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._delete_test_demand()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		self._delete_test_demand()
		super().tearDown()

	def _delete_test_demand(self) -> None:
		name = frappe.db.get_value("Demand", {"demand_code": DEMAND_CODE}, "name")
		if name:
			frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)

	def _create_approved_demand(self) -> str:
		return frappe.get_doc(
			{
				"doctype": "Demand",
				"demand_code": DEMAND_CODE,
				"title": "DEM-INT-009 budget source",
				"procuring_entity": self.procuring_entity,
				"owner_org_unit": self.owner_org_unit,
				"requester": "Administrator",
				"demand_route": "Standard",
				"currency": "KES",
				"status": "Approved",
				"current_stage": "Complete",
			}
		).insert(ignore_permissions=True).name

	def test_context_resolves_mvp_demand_by_business_code(self) -> None:
		self.assertTrue(demand_doctype_available())
		demand_name = self._create_approved_demand()

		context = _demand_context(DEMAND_CODE)

		self.assertEqual(context["id"], demand_name)
		self.assertEqual(context["code"], DEMAND_CODE)
		self.assertEqual(context["name"], "DEM-INT-009 budget source")
		self.assertEqual(context["owner_org_unit"], self.owner_org_unit)
		self.assertEqual(context["status"], "Approved")
		self.assertEqual(context["current_stage"], "Complete")
		self.assertEqual(context["demand_code"], DEMAND_CODE)
		self.assertEqual(context["demand_title"], "DEM-INT-009 budget source")
		self.assertNotIn("demand_id", context)
		self.assertNotIn("department", context)

	def test_context_resolves_mvp_demand_by_internal_name(self) -> None:
		demand_name = self._create_approved_demand()

		context = _demand_context(demand_name)

		self.assertEqual(context["id"], demand_name)
		self.assertEqual(context["code"], DEMAND_CODE)

	def test_context_falls_back_without_querying_retired_demand_shape(self) -> None:
		with (
			patch(
				"kentender_budget.services.budget_check_reserve_contracts.demand_doctype_available",
				return_value=False,
			),
			patch(
				"kentender_budget.services.budget_check_reserve_contracts.frappe.get_doc"
			) as get_doc,
		):
			context = _demand_context("DMD-NOT-YET-PERSISTED")

		get_doc.assert_not_called()
		self.assertEqual(context["id"], "")
		self.assertEqual(context["code"], "DMD-NOT-YET-PERSISTED")
		self.assertEqual(context["name"], "DMD-NOT-YET-PERSISTED")
		self.assertEqual(context["owner_org_unit"], "")
		self.assertNotIn("demand_id", context)
		self.assertNotIn("department", context)
