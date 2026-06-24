# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-010 — Run existing Procurement Lifecycle Journey/Handoff regression modules."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.tests.pp7_regression_helpers import (
	assert_module_gate_passes,
)

_LIFECYCLE_MODULES = [
	"kentender_procurement.procurement_lifecycle.tests.test_r8_002_plc_smoke_be_002_journey_aggregation",
	"kentender_procurement.procurement_lifecycle.tests.test_r1_010_source_module_authority",
	"kentender_procurement.procurement_lifecycle.tests.test_r3_017_journey_api",
	"kentender_procurement.procurement_lifecycle.tests.test_r3_001_handoff_card_service",
]


class TestPP7ExistingLifecycleTestsP7010(IntegrationTestCase):
	def test_pp7_010_lifecycle_regression_gate(self) -> None:
		frappe.set_user("Administrator")
		assert_module_gate_passes(
			frappe.local.site,
			app="kentender_procurement",
			modules=_LIFECYCLE_MODULES,
		)
