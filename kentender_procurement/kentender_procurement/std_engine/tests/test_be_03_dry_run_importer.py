# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-03 — dry-run importer tests (TDD first)."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.std_engine.constants import (
	CANONICAL_FAMILY_CODE,
	CANONICAL_PACKAGE_ID,
	CANONICAL_VERSION_CODE,
	COMMIT_TARGET_STATE_M1,
)
from kentender_procurement.std_engine.package_import.dry_run_importer import (
	DryRunImporter,
	DryRunImporterError,
)
from kentender_procurement.std_engine.package_import.hash_utils import (
	compute_file_sha256,
	compute_manifest_hash,
)
from kentender_procurement.std_engine.package_import.import_report_writer import build_dry_run_id
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path


CANONICAL_RECORD_COUNTS = {
	"families": 1,
	"versions": 1,
	"sourceDocuments": 1,
	"anchors": 270,
	"sections": 21,
	"clauses": 94,
	"parameters": 155,
	"rules": 22,
	"forms": 25,
	"formFields": 75,
	"requirements": 1,
	"priceSchedules": 6,
	"evaluationSchemas": 1,
	"renderBlocks": 17,
	"usageBindings": 3,
}


class TestBe03DryRunImporterCanonical(UnitTestCase):
	def setUp(self) -> None:
		self.zip_path = default_seed_zip_path()
		self.pdf_path = default_official_pdf_path()
		self.importer = DryRunImporter(self.zip_path, self.pdf_path)

	def test_produces_deterministic_dry_run_id(self) -> None:
		first = self.importer.run()
		second = DryRunImporter(self.zip_path, self.pdf_path).run()
		self.assertEqual(first["dry_run_id"], second["dry_run_id"])
		self.assertTrue(first["dry_run_id"].startswith(f"DRY-{CANONICAL_PACKAGE_ID}-"))

	def test_report_contains_required_fields(self) -> None:
		report = self.importer.run()
		for key in (
			"package_id",
			"family_code",
			"version_code",
			"package_sha256",
			"manifest_hash",
			"source_document_hash",
			"record_counts",
			"missing_required_files",
			"validation_blockers",
			"validation_warnings",
			"import_readiness",
			"checksum_status",
			"target_state",
			"dry_run_id",
			"dry_run_timestamp",
			"records_planned_insert",
			"records_planned_skip",
			"records_planned_fail",
		):
			with self.subTest(field=key):
				self.assertIn(key, report)

	def test_canonical_identity_and_hashes(self) -> None:
		report = self.importer.run()
		self.assertEqual(report["package_id"], CANONICAL_PACKAGE_ID)
		self.assertEqual(report["family_code"], CANONICAL_FAMILY_CODE)
		self.assertEqual(report["version_code"], CANONICAL_VERSION_CODE)
		self.assertEqual(report["package_sha256"], compute_file_sha256(self.zip_path))
		reader_report = self.importer._inspect()  # noqa: SLF001 — test-only access
		self.assertEqual(report["manifest_hash"], compute_manifest_hash(reader_report.manifest))
		self.assertEqual(report["source_document_hash"], compute_file_sha256(self.pdf_path))

	def test_canonical_record_counts(self) -> None:
		report = self.importer.run()
		self.assertEqual(report["record_counts"], CANONICAL_RECORD_COUNTS)

	def test_checksum_passed_and_planned_inserts(self) -> None:
		report = self.importer.run()
		self.assertEqual(report["checksum_status"], "PASSED")
		self.assertEqual(report["missing_required_files"], [])
		self.assertGreater(report["records_planned_insert"], 0)
		self.assertEqual(report["records_planned_fail"], 0)

	def test_target_state_is_draft(self) -> None:
		report = self.importer.run()
		self.assertEqual(report["target_state"], COMMIT_TARGET_STATE_M1)

	def test_activation_blockers_surface_as_validation_blockers(self) -> None:
		report = self.importer.run()
		self.assertGreater(len(report["validation_blockers"]), 0)
		self.assertEqual(report["import_readiness"], "READY_WITH_WARNINGS")

	def test_nssf_source_document_skipped_in_counts(self) -> None:
		report = self.importer.run()
		self.assertEqual(report["record_counts"]["sourceDocuments"], 1)
		self.assertEqual(report["skipped_paths"], [])


class TestBe03DryRunImporterFailures(UnitTestCase):
	def test_missing_pdf_raises(self) -> None:
		with self.assertRaises(DryRunImporterError):
			DryRunImporter(default_seed_zip_path(), "/tmp/no-such-std-pdf.pdf").run()

	def test_missing_required_file_blocks_import(self) -> None:
		source = default_seed_zip_path()
		with tempfile.TemporaryDirectory() as tmp:
			out = Path(tmp) / "missing-sections.zip"
			with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(out, "w") as zout:
				for info in zin.infolist():
					if info.filename.endswith("template/sections.json"):
						continue
					zout.writestr(info, zin.read(info.filename))
			report = DryRunImporter(out, default_official_pdf_path()).run()
			self.assertIn("template/sections.json", report["missing_required_files"])
			self.assertEqual(report["import_readiness"], "BLOCKED")

	def test_checksum_failure_blocks_import(self) -> None:
		source = default_seed_zip_path()
		root = "KE-PPRA-IT-2022-04_seed_package_v1_0/"
		with tempfile.TemporaryDirectory() as tmp:
			out = Path(tmp) / "bad-checksum.zip"
			with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(out, "w") as zout:
				for info in zin.infolist():
					data = zin.read(info.filename)
					if info.filename == root + "checksums.json":
						data = b'{"algorithm":"SHA-256","files":{"manifest.json":"deadbeef"}}\n'
					zout.writestr(info, data)
			report = DryRunImporter(out, default_official_pdf_path()).run()
			self.assertEqual(report["checksum_status"], "FAILED")
			self.assertEqual(report["import_readiness"], "BLOCKED")

	def test_missing_anchor_reference_adds_warning(self) -> None:
		source = default_seed_zip_path()
		root = "KE-PPRA-IT-2022-04_seed_package_v1_0/"
		with tempfile.TemporaryDirectory() as tmp:
			out = Path(tmp) / "bad-anchor.zip"
			with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(out, "w") as zout:
				for info in zin.infolist():
					data = zin.read(info.filename)
					if info.filename == root + "template/clauses.json":
						import json

						payload = json.loads(data)
						payload["records"][0]["source_anchor_key"] = "missing.anchor.key"
						data = json.dumps(payload).encode()
					zout.writestr(info, data)
			report = DryRunImporter(out, default_official_pdf_path()).run()
			self.assertTrue(any("anchor" in w.lower() for w in report["validation_warnings"]))


class TestBe03DryRunIdHelper(UnitTestCase):
	def test_build_dry_run_id_is_deterministic(self) -> None:
		package_sha256 = "a" * 64
		self.assertEqual(
			build_dry_run_id(CANONICAL_PACKAGE_ID, package_sha256),
			f"DRY-{CANONICAL_PACKAGE_ID}-{'A' * 8}",
		)


class TestBe03DryRunBenchEntry(IntegrationTestCase):
	def test_dry_run_run_function_returns_report(self) -> None:
		from kentender_procurement.std_engine.package_import.dry_run import run

		report = run(
			zip_path=str(default_seed_zip_path()),
			pdf_path=str(default_official_pdf_path()),
		)
		self.assertEqual(report["package_id"], CANONICAL_PACKAGE_ID)


class TestBe03DryRunIdempotentPlanning(IntegrationTestCase):
	def tearDown(self) -> None:
		from kentender_procurement.std_engine.package_import.draft_cleanup import clear_draft_package_state

		clear_draft_package_state(CANONICAL_PACKAGE_ID, family_code=CANONICAL_FAMILY_CODE)

	def test_existing_matching_hash_plans_skip(self) -> None:
		if not frappe.db.exists("STD Family", CANONICAL_FAMILY_CODE):
			frappe.get_doc(
				{
					"doctype": "STD Family",
					"family_code": CANONICAL_FAMILY_CODE,
					"family_name": "BE03 Test Family",
					"authority_code": "PPRA",
					"procurement_category": "IT",
				}
			).insert(ignore_permissions=True)

		package_sha256 = compute_file_sha256(default_seed_zip_path())
		frappe.get_doc(
			{
				"doctype": "STD Version",
				"package_id": CANONICAL_PACKAGE_ID,
				"family_code": CANONICAL_FAMILY_CODE,
				"version_code": CANONICAL_VERSION_CODE,
				"lifecycle_state": COMMIT_TARGET_STATE_M1,
				"package_sha256": package_sha256,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()

		report = DryRunImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		self.assertGreater(report["records_planned_skip"], 0)
		self.assertEqual(report["records_planned_fail"], 0)
		self.assertEqual(report["records_planned_insert"], 0)

	def test_existing_conflicting_hash_plans_fail(self) -> None:
		if not frappe.db.exists("STD Family", CANONICAL_FAMILY_CODE):
			frappe.get_doc(
				{
					"doctype": "STD Family",
					"family_code": CANONICAL_FAMILY_CODE,
					"family_name": "BE03 Test Family",
					"authority_code": "PPRA",
					"procurement_category": "IT",
				}
			).insert(ignore_permissions=True)

		frappe.get_doc(
			{
				"doctype": "STD Version",
				"package_id": CANONICAL_PACKAGE_ID,
				"family_code": CANONICAL_FAMILY_CODE,
				"version_code": CANONICAL_VERSION_CODE,
				"lifecycle_state": COMMIT_TARGET_STATE_M1,
				"package_sha256": "0" * 64,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()

		report = DryRunImporter(
			default_seed_zip_path(),
			default_official_pdf_path(),
			replace_draft=False,
		).run()
		self.assertGreater(report["records_planned_fail"], 0)
		self.assertEqual(report["import_readiness"], "BLOCKED")
		frappe.db.delete("STD Version", CANONICAL_PACKAGE_ID)
		frappe.db.commit()
