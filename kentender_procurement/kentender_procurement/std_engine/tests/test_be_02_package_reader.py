# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-02 — STD seed package tests (TDD first)."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from frappe.tests import UnitTestCase

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.package_contract import REQUIRED_ANY_IMPORT, REQUIRED_VERTICAL_SLICE
from kentender_procurement.std_engine.package_import.package_reader import PackageReader, PackageReaderError
from kentender_procurement.std_engine.paths import default_seed_zip_path


class TestBe02PackageReaderCanonicalZip(UnitTestCase):
	def setUp(self) -> None:
		self.zip_path = default_seed_zip_path()
		self.reader = PackageReader(self.zip_path)

	def test_lists_zip_contents_and_detects_package_root(self) -> None:
		result = self.reader.inspect()
		self.assertTrue(result.package_root.endswith("_seed_package_v0_2/"))
		self.assertGreater(result.files_total, 50)
		self.assertIn("manifest.json", result.files_listed)

	def test_reads_manifest_and_checksums(self) -> None:
		result = self.reader.inspect()
		self.assertEqual(result.package_id, CANONICAL_PACKAGE_ID)
		self.assertEqual(result.manifest.get("package_code"), CANONICAL_PACKAGE_ID)
		self.assertEqual(result.checksums.get("hash_algorithm"), "SHA-256")
		self.assertGreater(len(result.checksums.get("files") or {}), 50)

	def test_required_files_present_in_canonical_package(self) -> None:
		result = self.reader.inspect()
		self.assertEqual(result.missing_required_files, [])
		for rel in (*REQUIRED_ANY_IMPORT, *REQUIRED_VERTICAL_SLICE):
			with self.subTest(path=rel):
				self.assertIn(rel, result.files_listed)

	def test_checksum_verification_passes_for_canonical_package(self) -> None:
		result = self.reader.inspect()
		self.assertEqual(result.checksum_status, "PASSED")
		self.assertEqual(result.checksum_failures, [])

	def test_parses_core_json_payloads(self) -> None:
		result = self.reader.inspect()
		self.assertEqual(len(result.parsed_payloads["family"]["records"]), 1)
		self.assertEqual(len(result.parsed_payloads["version"]["records"]), 1)
		self.assertGreater(len(result.parsed_payloads["sections"]["records"]), 0)
		self.assertGreater(len(result.parsed_payloads["clauses"]["records"]), 0)
		self.assertIn("activation_blockers", result.manifest)

	def test_manifest_reports_activation_not_allowed(self) -> None:
		result = self.reader.inspect()
		self.assertFalse(result.activation_allowed)
		self.assertGreater(len(result.activation_blockers), 0)

	def test_skips_nssf_fixture_paths(self) -> None:
		result = self.reader.inspect()
		self.assertTrue(any(p.startswith("fixtures/nssf_erp/") for p in result.skipped_paths))


class TestBe02PackageReaderFailures(UnitTestCase):
	def test_missing_zip_raises(self) -> None:
		with self.assertRaises(PackageReaderError):
			PackageReader("/tmp/does-not-exist-std-package.zip").inspect()

	def test_missing_required_file_is_reported(self) -> None:
		source = default_seed_zip_path()
		with tempfile.TemporaryDirectory() as tmp:
			out = Path(tmp) / "missing-clauses.zip"
			with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(out, "w") as zout:
				for info in zin.infolist():
					if info.filename.endswith("template/clauses.json"):
						continue
					zout.writestr(info, zin.read(info.filename))
			result = PackageReader(out).inspect()
			self.assertIn("template/clauses.json", result.missing_required_files)

	def test_checksum_failure_is_reported(self) -> None:
		source = default_seed_zip_path()
		with tempfile.TemporaryDirectory() as tmp:
			out = Path(tmp) / "bad-checksum.zip"
			root = "KE-PPRA-IT-2022-04_seed_package_v0_2/"
			with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(out, "w") as zout:
				for info in zin.infolist():
					data = zin.read(info.filename)
					if info.filename == root + "manifest.json":
						data = b"{}\n"
					zout.writestr(info, data)
			result = PackageReader(out).inspect()
			self.assertEqual(result.checksum_status, "FAILED")
			self.assertGreater(len(result.checksum_failures), 0)


class TestBe02ManifestValidator(UnitTestCase):
	def test_invalid_manifest_structure_collects_errors(self) -> None:
		from kentender_procurement.std_engine.package_import.manifest_validator import validate_manifest

		errors = validate_manifest({})
		self.assertGreater(len(errors), 0)

	def test_valid_manifest_from_canonical_zip_has_no_errors(self) -> None:
		from kentender_procurement.std_engine.package_import.manifest_validator import validate_manifest

		result = PackageReader(default_seed_zip_path()).inspect()
		self.assertEqual(validate_manifest(result.manifest), [])
