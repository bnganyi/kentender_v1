from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from kentender_procurement.std_engine.seed.validator import (
	SeedPackageValidationError,
	validate_seed_package,
)


PACKAGE_ROOT = (
	Path(__file__).resolve().parents[2]
	/ "fixtures"
	/ "std_engine"
	/ "works_building_rev_apr_2022"
)


class TestSTDSeedValidationCommand(unittest.TestCase):
	def test_validation_passes_for_current_package(self):
		result = validate_seed_package(str(PACKAGE_ROOT))
		self.assertEqual(result["status"], "ok")

	def test_validation_fails_with_precise_missing_path_error(self):
		with tempfile.TemporaryDirectory() as tmp:
			dst = Path(tmp) / "pkg"
			shutil.copytree(PACKAGE_ROOT, dst)
			(dst / "11_boq" / "11a_boq_definition.yaml").unlink()
			with self.assertRaises(SeedPackageValidationError) as ctx:
				validate_seed_package(str(dst))
			self.assertIn("11_boq", str(ctx.exception))

	def test_validation_fails_on_placeholder_legal_text(self):
		with tempfile.TemporaryDirectory() as tmp:
			dst = Path(tmp) / "pkg"
			shutil.copytree(PACKAGE_ROOT, dst)
			target = dst / "07_clauses" / "07a_invitation_to_tender.yaml"
			data = yaml.safe_load(target.read_text(encoding="utf-8"))
			data["invitation_to_tender_clauses"][0]["text_verbatim"] = "lorem ipsum legal sample text"
			target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
			with self.assertRaises(SeedPackageValidationError) as ctx:
				validate_seed_package(str(dst))
			self.assertIn("placeholder legal text", str(ctx.exception).lower())

