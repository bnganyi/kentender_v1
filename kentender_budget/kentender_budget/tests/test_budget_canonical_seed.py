# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical Budget baseline as `make seed-canonical` leaves it
(BUD-CHG-001 v1.11 §15.1–§15.3). Reads the seeded site; writes nothing.

Project Owner decision, 26 Sep 2026: the canonical world keeps the
references the system generates. Until then the seed overwrote its lines'
generated references with `MOH-BL-DHI-2027` / `MOH-BL-HWD-2027` by a direct
write.
"""

from __future__ import annotations

import re

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.seeds import kentender_mvp_v1_portfolio as seed


class TestCanonicalBudgetSeed(IntegrationTestCase):
	def test_the_seeded_world_validates(self):
		failed = [row["check"] for row in seed.validate_budget_seed() if not row["ok"]]
		self.assertEqual(failed, [])

	def test_the_lines_keep_their_generated_references(self):
		for key in seed.LINES:
			line = seed.canonical_budget_line(key)
			self.assertTrue(line, key)
			reference = frappe.db.get_value("Procurement Budget Line", line, "generated_reference")
			self.assertRegex(reference, r"^[A-Z]+-BL-\d{4}$", key)

	def test_the_budget_and_version_references_are_generated(self):
		budget = seed.canonical_budget()
		self.assertTrue(re.fullmatch(r"[A-Z]+-BUD-2027-\d{3}", frappe.db.get_value("Procurement Budget", budget, "generated_reference") or ""))
