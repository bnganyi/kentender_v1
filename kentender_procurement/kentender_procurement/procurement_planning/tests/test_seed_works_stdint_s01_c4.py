# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C4 — Doc 3 §18.2 governance: seeds README documents no transitional tender bypass.

Run::

	bench --site <site> run-tests --app kentender_procurement \\
	  --module kentender_procurement.procurement_planning.tests.test_seed_works_stdint_s01_c4
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import IntegrationTestCase

import kentender_procurement.procurement_planning.seeds as planning_seeds_pkg


class TestSeedWorksStdintS01C4(IntegrationTestCase):
	def test_c4_seeds_readme_flags_section_18_2_not_used(self) -> None:
		readme = Path(planning_seeds_pkg.__file__).resolve().parent / "README.md"
		self.assertTrue(readme.is_file(), f"Missing seeds README: {readme}")
		text = readme.read_text(encoding="utf-8")
		self.assertIn("§18.2", text)
		self.assertIn("§18.1", text)
		self.assertIn("does not implement that shortcut", text)
		self.assertIn("§20", text)
		self.assertIn("§28", text)
		self.assertIn("§30", text)
