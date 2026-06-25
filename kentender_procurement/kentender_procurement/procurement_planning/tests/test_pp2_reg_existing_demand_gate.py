# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2-REG-6 — Run existing Demand Intake and Approval regression modules."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.tests.pp2_reg_regression_helpers import (
	assert_module_gate_passes,
)

_DEMAND_MODULES = [
	"kentender_procurement.demand_intake.tests.test_demand_approval_integrity",
	"kentender_procurement.demand_intake.tests.test_demand_planning_readiness",
	"kentender_procurement.demand_intake.tests.test_dia_audit_api",
	"kentender_procurement.demand_intake.tests.test_demand_submission_readiness",
]


class TestPP7ExistingDemandTestsP2Reg6(IntegrationTestCase):
	def test_pp2_reg_006_demand_intake_regression_gate(self) -> None:
		frappe.set_user("Administrator")
		assert_module_gate_passes(
			frappe.local.site,
			app="kentender_procurement",
			modules=_DEMAND_MODULES,
		)
