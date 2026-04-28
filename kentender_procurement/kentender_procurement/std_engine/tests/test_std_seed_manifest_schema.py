from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

import yaml

from kentender_procurement.std_engine.seed.manifest_schema import (
	REQUIRED_LOAD_ORDER,
	SeedManifestValidationError,
	validate_seed_manifest,
)


PACKAGE_ROOT = (
	Path(__file__).resolve().parents[2]
	/ "fixtures"
	/ "std_engine"
	/ "works_building_rev_apr_2022"
)


class TestSTDSeedManifestSchema(unittest.TestCase):
	def _read_manifest(self) -> dict:
		with (PACKAGE_ROOT / "00_manifest.yaml").open("r", encoding="utf-8") as f:
			return yaml.safe_load(f)

	def test_valid_manifest_schema_passes(self):
		manifest = self._read_manifest()
		validate_seed_manifest(manifest, PACKAGE_ROOT)

	def test_missing_required_key_fails(self):
		manifest = self._read_manifest()
		manifest.pop("version_code")
		with self.assertRaises(SeedManifestValidationError):
			validate_seed_manifest(manifest, PACKAGE_ROOT)

	def test_missing_load_order_entry_fails(self):
		manifest = self._read_manifest()
		manifest["load_order"] = [entry for entry in REQUIRED_LOAD_ORDER if entry != "11_boq"]
		with self.assertRaises(SeedManifestValidationError):
			validate_seed_manifest(manifest, PACKAGE_ROOT)

	def test_manifest_code_mismatch_fails(self):
		manifest = self._read_manifest()
		manifest["idempotency_key"] = "DIFFERENT"
		with self.assertRaises(SeedManifestValidationError):
			validate_seed_manifest(manifest, PACKAGE_ROOT)

	def test_malformed_load_order_type_fails(self):
		manifest = self._read_manifest()
		manifest["load_order"] = "not-a-list"
		with self.assertRaises(SeedManifestValidationError):
			validate_seed_manifest(manifest, PACKAGE_ROOT)

	def test_missing_load_entry_path_fails(self):
		manifest = self._read_manifest()
		manifest["load_order"] = deepcopy(REQUIRED_LOAD_ORDER)
		manifest["load_order"][0] = "missing_file.yaml"
		with self.assertRaises(SeedManifestValidationError):
			validate_seed_manifest(manifest, PACKAGE_ROOT)

