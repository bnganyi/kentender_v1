# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-04 — commit importer integration tests (TDD first)."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.constants import (
	CANONICAL_FAMILY_CODE,
	CANONICAL_PACKAGE_ID,
	CANONICAL_VERSION_CODE,
	COMMIT_TARGET_STATE_M1,
	PACKAGE_QUALITY_FULL_EXTRACTION,
	UI_MODE_READ_ONLY_INSPECTION,
)
from kentender_procurement.std_engine.package_import.commit_importer import (
	CommitImporter,
	CommitImporterError,
)
from kentender_procurement.std_engine.package_import.draft_cleanup import _clear_form_field_children
from kentender_procurement.std_engine.package_import.hash_utils import compute_file_sha256
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

PACKAGE_LINKED_DOCTYPES = (
	"STD Clause",
	"STD Section",
	"STD Source Anchor",
	"STD Source Document",
	"STD Parameter",
	"STD Rule",
	"STD Form Schema",
	"STD Requirement Schema",
	"STD Price Schedule Schema",
	"STD Evaluation Schema",
	"STD Render Block",
	"STD Validation Finding",
	"STD Validation Run",
	"STD Audit Event",
	"STD Import Run",
	"STD Usage Binding",
)


def clear_canonical_package_state() -> None:
	package_id = CANONICAL_PACKAGE_ID
	_clear_form_field_children(package_id)
	for doctype in PACKAGE_LINKED_DOCTYPES:
		frappe.db.delete(doctype, {"package_id": package_id})
	frappe.db.delete("STD Import Run", {"package_id": package_id})
	frappe.db.delete("STD Version", package_id)
	frappe.db.delete("STD Family", CANONICAL_FAMILY_CODE)
	frappe.db.commit()


class TestBe04CommitImporterCanonical(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		clear_canonical_package_state()

	@classmethod
	def tearDownClass(cls) -> None:
		clear_canonical_package_state()
		super().tearDownClass()

	def test_commit_creates_core_records(self) -> None:
		report = CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		self.assertEqual(report["commit_status"], "COMMITTED")
		self.assertEqual(report["package_id"], CANONICAL_PACKAGE_ID)
		self.assertTrue(frappe.db.exists("STD Family", CANONICAL_FAMILY_CODE))
		self.assertTrue(frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID))

		version = frappe.get_doc("STD Version", CANONICAL_PACKAGE_ID)
		self.assertEqual(version.lifecycle_state, COMMIT_TARGET_STATE_M1)
		self.assertEqual(int(version.activation_allowed or 0), 0)
		self.assertEqual(version.ui_mode, UI_MODE_READ_ONLY_INSPECTION)
		self.assertEqual(version.package_quality, PACKAGE_QUALITY_FULL_EXTRACTION)
		self.assertEqual(version.package_sha256, compute_file_sha256(default_seed_zip_path()))

		self.assertEqual(frappe.db.count("STD Section", {"package_id": CANONICAL_PACKAGE_ID}), 21)
		self.assertEqual(frappe.db.count("STD Clause", {"package_id": CANONICAL_PACKAGE_ID}), 94)
		self.assertEqual(frappe.db.count("STD Source Anchor", {"package_id": CANONICAL_PACKAGE_ID}), 270)
		self.assertEqual(report["records_committed"], CANONICAL_RECORD_COUNTS)

	def test_registers_official_pdf_not_nssf_fixture(self) -> None:
		CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		docs = frappe.get_all(
			"STD Source Document",
			filters={"package_id": CANONICAL_PACKAGE_ID},
			fields=["source_document_key", "filename", "source_hash", "source_role"],
		)
		self.assertEqual(len(docs), 1)
		self.assertEqual(docs[0]["source_role"], "LEGAL_MASTER_SOURCE")
		self.assertEqual(docs[0]["source_hash"], compute_file_sha256(default_official_pdf_path()))
		self.assertIn("DOC 10", docs[0]["filename"])

	def test_persists_validation_findings_and_audit_events(self) -> None:
		report = CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		self.assertGreater(
			frappe.db.count("STD Validation Finding", {"package_id": CANONICAL_PACKAGE_ID}),
			0,
		)
		self.assertEqual(
			frappe.db.count("STD Validation Run", {"package_id": CANONICAL_PACKAGE_ID}),
			1,
		)
		self.assertGreater(
			frappe.db.count("STD Audit Event", {"package_id": CANONICAL_PACKAGE_ID}),
			0,
		)
		self.assertTrue(report.get("import_run_key"))
		self.assertTrue(frappe.db.exists("STD Import Run", report["import_run_key"]))

	def test_idempotent_recommit_skips_duplicate_writes(self) -> None:
		clear_canonical_package_state()
		first = CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		section_count = frappe.db.count("STD Section", {"package_id": CANONICAL_PACKAGE_ID})
		second = CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		self.assertEqual(first["commit_status"], "COMMITTED")
		self.assertEqual(second["commit_status"], "IDEMPOTENT_SKIP")
		self.assertEqual(frappe.db.count("STD Section", {"package_id": CANONICAL_PACKAGE_ID}), section_count)

	def test_commit_run_function_returns_report(self) -> None:
		from kentender_procurement.std_engine.package_import.commit import run

		report = run(
			zip_path=str(default_seed_zip_path()),
			pdf_path=str(default_official_pdf_path()),
		)
		self.assertIn(report["commit_status"], ("COMMITTED", "IDEMPOTENT_SKIP"))
		self.assertEqual(report["target_state"], COMMIT_TARGET_STATE_M1)


class TestBe04CommitImporterFailures(IntegrationTestCase):
	def tearDown(self) -> None:
		if frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID):
			lifecycle = frappe.db.get_value("STD Version", CANONICAL_PACKAGE_ID, "lifecycle_state")
			if lifecycle == "ACTIVE":
				frappe.db.set_value("STD Version", CANONICAL_PACKAGE_ID, "lifecycle_state", COMMIT_TARGET_STATE_M1)
		clear_canonical_package_state()

	def test_blocked_package_raises(self) -> None:
		source = default_seed_zip_path()
		with tempfile.TemporaryDirectory() as tmp:
			out = Path(tmp) / "missing-sections.zip"
			with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(out, "w") as zout:
				for info in zin.infolist():
					if info.filename.endswith("template/sections.json"):
						continue
					zout.writestr(info, zin.read(info.filename))
			with self.assertRaises(CommitImporterError):
				CommitImporter(out, default_official_pdf_path()).run()

	def test_hash_conflict_raises_when_replace_disabled(self) -> None:
		if not frappe.db.exists("STD Family", CANONICAL_FAMILY_CODE):
			frappe.get_doc(
				{
					"doctype": "STD Family",
					"family_code": CANONICAL_FAMILY_CODE,
					"family_name": "BE04 Conflict Family",
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
		with self.assertRaises(CommitImporterError):
			CommitImporter(default_seed_zip_path(), default_official_pdf_path(), replace_draft=False).run()

	def test_active_version_protection_raises(self) -> None:
		if not frappe.db.exists("STD Family", CANONICAL_FAMILY_CODE):
			frappe.get_doc(
				{
					"doctype": "STD Family",
					"family_code": CANONICAL_FAMILY_CODE,
					"family_name": "BE04 Active Family",
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
				"lifecycle_state": "ACTIVE",
				"package_sha256": compute_file_sha256(default_seed_zip_path()),
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
		with self.assertRaises(CommitImporterError) as ctx:
			CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		self.assertIn("ACTIVE", str(ctx.exception))
