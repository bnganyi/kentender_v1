# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""F1 / F2 — full planning seed (skipped after DIA preparatory teardown)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


class TestF1ProcurementPlanningSeed(IntegrationTestCase):
	def test_f1_seed_retired_with_dia(self) -> None:
		frappe.set_user("Administrator")
		self.skipTest(
			"F1 planning seed depends on Demand Intake helpers deleted in DIA preparatory teardown."
		)
