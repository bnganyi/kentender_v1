# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-04a — import HTTP scaffold contract tests (TDD first)."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.import_api import commit, dry_run, get_import_run
from kentender_procurement.std_engine.constants import (
	CANONICAL_PACKAGE_ID,
	COMMIT_TARGET_STATE_M1,
)
from kentender_procurement.std_engine.package_import.dry_run_importer import DryRunImporter
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path
from kentender_procurement.std_engine.tests.test_be_04_commit_importer import (
	clear_canonical_package_state,
)

REQUIRED_DRY_RUN_REPORT_FIELDS = (
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
)


class TestBe04aImportApiDryRun(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_guest_denied_dry_run(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			dry_run()

	def test_dry_run_api_returns_contract(self) -> None:
		out = dry_run(
			zip_path=str(default_seed_zip_path()),
			pdf_path=str(default_official_pdf_path()),
		)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("route"), "POST /std-engine/import/dry-run")
		self.assertTrue(out.get("import_run_key"))
		self.assertTrue(frappe.db.exists("STD Import Run", out["import_run_key"]))

		report = out.get("report") or {}
		for field in REQUIRED_DRY_RUN_REPORT_FIELDS:
			with self.subTest(field=field):
				self.assertIn(field, report)
		self.assertEqual(report["package_id"], CANONICAL_PACKAGE_ID)
		self.assertEqual(report["target_state"], COMMIT_TARGET_STATE_M1)

	def test_dry_run_api_matches_importer_service(self) -> None:
		service_report = DryRunImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		api_out = dry_run(
			zip_path=str(default_seed_zip_path()),
			pdf_path=str(default_official_pdf_path()),
		)
		api_report = api_out.get("report") or {}
		for field in (
			"package_id",
			"package_sha256",
			"manifest_hash",
			"record_counts",
			"import_readiness",
			"checksum_status",
			"dry_run_id",
		):
			with self.subTest(field=field):
				self.assertEqual(api_report.get(field), service_report.get(field))


class TestBe04aImportApiCommit(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		clear_canonical_package_state()

	@classmethod
	def tearDownClass(cls) -> None:
		clear_canonical_package_state()
		super().tearDownClass()

	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_guest_denied_commit(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			commit()

	def test_commit_api_returns_contract(self) -> None:
		out = commit(
			zip_path=str(default_seed_zip_path()),
			pdf_path=str(default_official_pdf_path()),
			package_id=CANONICAL_PACKAGE_ID,
		)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("route"), "POST /std-engine/import/commit")
		self.assertIn(out.get("report", {}).get("commit_status"), ("COMMITTED", "IDEMPOTENT_SKIP"))
		self.assertTrue(out.get("import_run_key"))
		self.assertTrue(frappe.db.exists("STD Import Run", out["import_run_key"]))

	def test_commit_blocked_returns_error_envelope(self) -> None:
		source = default_seed_zip_path()
		with tempfile.TemporaryDirectory() as tmp:
			out_zip = Path(tmp) / "missing-sections.zip"
			with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(out_zip, "w") as zout:
				for info in zin.infolist():
					if info.filename.endswith("template/sections.json"):
						continue
					zout.writestr(info, zin.read(info.filename))
			result = commit(zip_path=str(out_zip), pdf_path=str(default_official_pdf_path()))
		self.assertFalse(result.get("ok"))
		self.assertEqual(result.get("error_code"), "STD_IMPORT_COMMIT_FAILED")
		self.assertEqual(result.get("route"), "POST /std-engine/import/commit")


class TestBe04aImportApiGetImportRun(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_get_import_run_returns_persisted_report(self) -> None:
		created = dry_run(
			zip_path=str(default_seed_zip_path()),
			pdf_path=str(default_official_pdf_path()),
		)
		import_run_key = created["import_run_key"]
		out = get_import_run(import_run_key)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("route"), "GET /std-engine/import-runs/:id")

		import_run = out.get("import_run") or {}
		self.assertEqual(import_run.get("import_run_key"), import_run_key)
		self.assertEqual(import_run.get("run_mode"), "DRY_RUN")
		report = import_run.get("report") or {}
		self.assertEqual(report.get("package_id"), CANONICAL_PACKAGE_ID)
		self.assertEqual(json.loads(frappe.db.get_value("STD Import Run", import_run_key, "report_json")), report)

	def test_get_import_run_missing_returns_error(self) -> None:
		out = get_import_run("DOES-NOT-EXIST-STD-IMPORT-RUN")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "STD_IMPORT_RUN_NOT_FOUND")

	def test_auditor_can_read_import_run(self) -> None:
		if not frappe.db.exists("User", "auditor@example.com"):
			self.skipTest("Auditor test user not provisioned")
		created = dry_run(
			zip_path=str(default_seed_zip_path()),
			pdf_path=str(default_official_pdf_path()),
		)
		frappe.set_user("auditor@example.com")
		out = get_import_run(created["import_run_key"])
		self.assertTrue(out.get("ok"))

	def test_guest_denied_get_import_run(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_import_run("ANY-KEY")
