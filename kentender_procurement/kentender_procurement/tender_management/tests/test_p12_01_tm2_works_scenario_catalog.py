# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 — doc 7 §2 scenario registry integrity + stub package discovery."""

from __future__ import annotations

import importlib
import pkgutil
import unittest

from kentender_procurement.tender_management.scenarios.tm2_works_scenarios import (
	iter_tm2_works_scenario_codes,
	scenario_by_code,
	scenario_tracker_slug,
	tm2_works_scenarios,
)


class TestP12Tm2WorksScenarioCatalog(unittest.TestCase):
	def test_doc7_has_thirteen_scenarios(self) -> None:
		specs = tm2_works_scenarios()
		self.assertEqual(len(specs), 13)

	def test_scenario_codes_are_unique_and_ordered_s01_s13(self) -> None:
		codes = [s.code for s in tm2_works_scenarios()]
		self.assertEqual(len(codes), len(set(codes)))
		expected = [f"TM2-WORKS-S{n:02d}" for n in range(1, 14)]
		self.assertEqual(codes, expected)

	def test_tracker_slugs_align_with_implementation_tracker(self) -> None:
		self.assertEqual(scenario_tracker_slug(scenario_by_code("TM2-WORKS-S01")), "S-01")
		self.assertEqual(scenario_tracker_slug(scenario_by_code("TM2-WORKS-S13")), "S-13")

	def test_unknown_code_raises_key_error(self) -> None:
		with self.assertRaises(KeyError):
			scenario_by_code("TM2-WORKS-S99")

	def test_iter_matches_tuple(self) -> None:
		self.assertEqual(list(iter_tm2_works_scenario_codes()), [s.code for s in tm2_works_scenarios()])


class TestP12ScenarioStubPackageImports(unittest.TestCase):
	"""Each ``tests/scenarios/test_tm2_works_sNN.py`` must import (P12-01 per-scenario modules)."""

	def test_all_scenario_stub_modules_import(self) -> None:
		import kentender_procurement.tender_management.tests.scenarios as pkg

		found: set[str] = set()
		for info in pkgutil.iter_modules(pkg.__path__):
			name = info.name
			if not name.startswith("test_tm2_works_s"):
				continue
			importlib.import_module(f"{pkg.__name__}.{name}")
			found.add(name)
		expected = {f"test_tm2_works_s{n:02d}" for n in range(1, 14)}
		self.assertEqual(
			found,
			expected,
			msg=f"Expected thirteen stub modules {expected}, found {found}",
		)
