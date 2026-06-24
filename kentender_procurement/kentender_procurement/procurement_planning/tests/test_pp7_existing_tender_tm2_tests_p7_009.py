# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-009 — Run existing Tender Management/TM2 regression modules."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.tests.pp7_regression_helpers import (
	assert_module_gate_passes,
)

_TM2_MODULES = [
	"kentender_procurement.procurement_lifecycle.tests.test_r8_012_tm2_legal_smoke_regression",
	"kentender_procurement.procurement_planning.tests.test_pp2_journey_handoff_integration_p4_014",
]


class TestPP7ExistingTenderTm2TestsP7009(IntegrationTestCase):
	def test_pp7_009_tender_tm2_regression_gate(self) -> None:
		frappe.set_user("Administrator")
		assert_module_gate_passes(
			frappe.local.site,
			app="kentender_procurement",
			modules=_TM2_MODULES,
		)
