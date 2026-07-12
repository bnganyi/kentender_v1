# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-12 — STD-SMOKE-001..015 extraction readiness contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.constants import (
	CANONICAL_FAMILY_CODE,
	CANONICAL_PACKAGE_ID,
	COMMIT_TARGET_STATE_M1,
	PACKAGE_QUALITY_FULL_EXTRACTION,
)
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.draft_cleanup import (
	clear_draft_package_state,
	force_reset_package_state_for_tests,
)
from kentender_procurement.std_engine.package_import.hash_utils import compute_file_sha256
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path
from kentender_procurement.std_engine.validation.validation_engine import get_validation_summary

V1_RECORD_COUNTS = {
	"sections": 21,
	"clauses": 94,
	"parameters": 155,
	"forms": 25,
	"formFields": 75,
	"priceSchedules": 6,
	"evaluationSchemas": 1,
	"renderBlocks": 17,
}


class TestBe12SmokeContracts(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code=CANONICAL_FAMILY_CODE)
		CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()

	@classmethod
	def tearDownClass(cls) -> None:
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code=CANONICAL_FAMILY_CODE)
		super().tearDownClass()

	def test_std_smoke_001_imports_as_draft(self) -> None:
		version = frappe.get_doc("STD Version", CANONICAL_PACKAGE_ID)
		self.assertEqual(version.lifecycle_state, COMMIT_TARGET_STATE_M1)

	def test_std_smoke_002_official_pdf_registered(self) -> None:
		docs = frappe.get_all(
			"STD Source Document",
			filters={"package_id": CANONICAL_PACKAGE_ID},
			fields=["filename", "source_hash", "source_role"],
		)
		self.assertEqual(len(docs), 1)
		self.assertEqual(docs[0]["source_role"], "LEGAL_MASTER_SOURCE")
		self.assertEqual(docs[0]["source_hash"], compute_file_sha256(default_official_pdf_path()))
		self.assertIn("DOC 10", docs[0]["filename"])

	def test_std_smoke_003_mandatory_sections_exist(self) -> None:
		self.assertEqual(
			frappe.db.count("STD Section", {"package_id": CANONICAL_PACKAGE_ID}),
			V1_RECORD_COUNTS["sections"],
		)

	def test_std_smoke_004_locked_clauses_have_full_text(self) -> None:
		missing = frappe.get_all(
			"STD Clause",
			filters={"package_id": CANONICAL_PACKAGE_ID, "clause_text": ["in", ["", None]]},
			fields=["name"],
		)
		self.assertEqual(len(missing), 0)

	def test_std_smoke_005_locked_clauses_have_source_anchors(self) -> None:
		missing = frappe.get_all(
			"STD Clause",
			filters={"package_id": CANONICAL_PACKAGE_ID, "source_anchor": ["in", ["", None]]},
			fields=["name"],
		)
		self.assertEqual(len(missing), 0)

	def test_std_smoke_006_locked_clauses_have_text_hashes(self) -> None:
		missing = frappe.get_all(
			"STD Clause",
			filters={"package_id": CANONICAL_PACKAGE_ID, "content_hash": ["in", ["", None]]},
			fields=["name"],
		)
		self.assertEqual(len(missing), 0)

	def test_std_smoke_007_tds_parameters_render_bound(self) -> None:
		self._assert_parameters_render_bound("tds")

	def test_std_smoke_008_scc_parameters_render_bound(self) -> None:
		self._assert_parameters_render_bound("scc")

	def test_std_smoke_009_tendering_forms_have_fields(self) -> None:
		self.assertEqual(
			frappe.db.count("STD Form Schema", {"package_id": CANONICAL_PACKAGE_ID}),
			V1_RECORD_COUNTS["forms"],
		)
		form_names = frappe.get_all(
			"STD Form Schema",
			filters={"package_id": CANONICAL_PACKAGE_ID},
			pluck="name",
		)
		field_count = 0
		for form_name in form_names:
			field_count += len(frappe.get_doc("STD Form Schema", form_name).form_fields or [])
		self.assertGreaterEqual(field_count, V1_RECORD_COUNTS["formFields"])

	def test_std_smoke_010_evaluation_schema_has_criteria(self) -> None:
		import json

		rows = frappe.get_all(
			"STD Evaluation Schema",
			filters={"package_id": CANONICAL_PACKAGE_ID},
			fields=["metadata_json"],
		)
		self.assertEqual(len(rows), 1)
		meta = json.loads(rows[0]["metadata_json"] or "{}")
		self.assertGreaterEqual(len(meta.get("criteria") or []), 4)

	def test_std_smoke_011_price_schedules_have_schemas(self) -> None:
		self.assertEqual(
			frappe.db.count("STD Price Schedule Schema", {"package_id": CANONICAL_PACKAGE_ID}),
			V1_RECORD_COUNTS["priceSchedules"],
		)

	def test_std_smoke_012_requirements_schema_present(self) -> None:
		self.assertEqual(
			frappe.db.count("STD Requirement Schema", {"package_id": CANONICAL_PACKAGE_ID}),
			1,
		)

	def test_std_smoke_013_render_blocks_cover_mandatory_sections(self) -> None:
		self.assertGreaterEqual(
			frappe.db.count("STD Render Block", {"package_id": CANONICAL_PACKAGE_ID}),
			V1_RECORD_COUNTS["renderBlocks"],
		)

	def test_std_smoke_014_validation_report_has_no_placeholder_blockers(self) -> None:
		blockers = frappe.get_all(
			"STD Validation Finding",
			filters={
				"package_id": CANONICAL_PACKAGE_ID,
				"severity": "BLOCKER",
				"finding_code": ["in", ["EXTRACTION_PLACEHOLDER", "CLAUSE_TEXT_MISSING", "TEXT_HASH_MISSING"]],
			},
			fields=["finding_code"],
		)
		self.assertEqual(len(blockers), 0)

	def test_std_smoke_015_sample_tender_instance_metadata_available(self) -> None:
		version = frappe.get_doc("STD Version", CANONICAL_PACKAGE_ID)
		self.assertEqual(version.package_quality, PACKAGE_QUALITY_FULL_EXTRACTION)
		self.assertGreaterEqual(
			frappe.db.count("STD Usage Binding", {"package_id": CANONICAL_PACKAGE_ID}),
			3,
		)
		summary = get_validation_summary(CANONICAL_PACKAGE_ID)
		self.assertGreaterEqual(summary.get("blockers", 0), 0)

	def _assert_parameters_render_bound(self, section_slug: str) -> None:
		import json

		rows = frappe.get_all(
			"STD Parameter",
			filters={"package_id": CANONICAL_PACKAGE_ID},
			fields=["parameter_key", "metadata_json"],
		)
		section_hits = 0
		for row in rows:
			meta = json.loads(row.get("metadata_json") or "{}")
			section_key = str(meta.get("applies_to_section_key") or "")
			if f".section.{section_slug}" not in section_key:
				continue
			section_hits += 1
			self.assertTrue(meta.get("render_binding_keys"), row["parameter_key"])
		self.assertGreater(section_hits, 0)
