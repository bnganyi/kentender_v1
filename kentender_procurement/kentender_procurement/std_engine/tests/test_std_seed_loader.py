from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import frappe

from kentender_procurement.std_engine.seed.loader import SeedLoadError, load_std_seed_package


PACKAGE_ROOT = (
	Path(__file__).resolve().parents[2]
	/ "fixtures"
	/ "std_engine"
	/ "works_building_rev_apr_2022"
)


class TestSTDSeedLoader(unittest.TestCase):
	def test_dry_run_returns_report(self):
		report = load_std_seed_package(str(PACKAGE_ROOT), dry_run=True)
		self.assertTrue(report["dry_run"])
		self.assertGreaterEqual(report["skipped"] + report["created"] + report["updated"], 1)

	def test_missing_manifest_blocks_load(self):
		with tempfile.TemporaryDirectory() as tmp:
			with self.assertRaises(SeedLoadError):
				load_std_seed_package(tmp, dry_run=True)

	def test_rerun_is_idempotent_for_unchanged_records(self):
		first = load_std_seed_package(str(PACKAGE_ROOT), dry_run=True)
		second = load_std_seed_package(str(PACKAGE_ROOT), dry_run=True)
		self.assertEqual(first["processed"], second["processed"])

	def test_refuses_mutation_for_immutable_without_force(self):
		frappe.db.set_value(
			"STD Template Version",
			{"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022"},
			"version_label",
			"CHANGED OUTSIDE SEED",
		)
		frappe.db.commit()
		try:
			with self.assertRaises(SeedLoadError):
				load_std_seed_package(str(PACKAGE_ROOT), dry_run=False, force=False)
		finally:
			frappe.db.set_value(
				"STD Template Version",
				{"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022"},
				"version_label",
				"Building and Associated Civil Engineering Works Rev April 2022",
			)
			frappe.db.commit()

