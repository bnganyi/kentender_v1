# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-008 — Run existing STD Admin/STD Engine regression modules."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.tests.pp7_regression_helpers import (
	assert_module_gate_passes,
)

_STD_MODULES = [
	"kentender_procurement.procurement_lifecycle.tests.test_r8_013_std_governance_smoke_regression",
	"kentender_procurement.procurement_lifecycle.tests.test_r1_001_journey_status",
]


class TestPP7ExistingStdTestsP7008(IntegrationTestCase):
	def test_pp7_008_std_regression_gate(self) -> None:
		frappe.set_user("Administrator")
		assert_module_gate_passes(
			frappe.local.site,
			app="kentender_procurement",
			modules=_STD_MODULES,
		)
