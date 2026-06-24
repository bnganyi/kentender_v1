# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-007 — Run existing Budget regression modules."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.tests.pp7_regression_helpers import (
	assert_module_gate_passes,
)

_BUDGET_MODULES = [
	"kentender_budget.tests.test_budget_b01",
	"kentender_budget.tests.test_budget_landing_api",
	"kentender_budget.tests.test_budget_audit_api",
	"kentender_budget.tests.test_moh_entity_permission_aliases",
]


class TestPP7ExistingBudgetTestsP7007(IntegrationTestCase):
	def test_pp7_007_budget_regression_gate(self) -> None:
		frappe.set_user("Administrator")
		assert_module_gate_passes(
			frappe.local.site,
			app="kentender_budget",
			modules=_BUDGET_MODULES,
		)
