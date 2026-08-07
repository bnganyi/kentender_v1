# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C4 — PP3 planning slice (skipped after DIA preparatory teardown)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


class TestC4Pp3Slice(IntegrationTestCase):
	def test_pp3_slice_retired_with_dia(self) -> None:
		frappe.set_user("Administrator")
		self.skipTest(
			"PP3 slice depends on Demand Intake helpers deleted in DIA preparatory teardown."
		)
