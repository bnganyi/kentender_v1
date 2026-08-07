# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2-REG-6 — Demand Intake regression gate (retired with DIA teardown)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


class TestPP7ExistingDemandTestsP2Reg6(IntegrationTestCase):
	def test_pp2_reg_006_demand_intake_regression_gate(self) -> None:
		frappe.set_user("Administrator")
		self.skipTest(
			"Demand Intake regression modules deleted with DIA preparatory teardown "
			"(Demands MVP-1 pending)."
		)
