# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-14 — STD-SMOKE-016..020 verbatim extraction contracts."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.constants import (
	CANONICAL_FAMILY_CODE,
	CANONICAL_PACKAGE_ID,
)
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.package_reader import PackageReader
from kentender_procurement.std_engine.package_import.draft_cleanup import (
	clear_draft_package_state,
	force_reset_package_state_for_tests,
)
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path_v1_1
from kentender_procurement.std_engine.services.legal_review_service import approve_all_pending
from kentender_procurement.std_engine.validation.validators.verbatim_source import SYNTHETIC_MARKER


class TestBe14VerbatimSmokeContracts(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code=CANONICAL_FAMILY_CODE)
		CommitImporter(default_seed_zip_path_v1_1(), default_official_pdf_path()).run()

	@classmethod
	def tearDownClass(cls) -> None:
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code=CANONICAL_FAMILY_CODE)
		super().tearDownClass()

	def test_std_smoke_016_no_synthetic_clause_template(self) -> None:
		rows = frappe.get_all(
			"STD Clause",
			filters={"package_id": CANONICAL_PACKAGE_ID},
			fields=["clause_text"],
		)
		for row in rows:
			self.assertNotIn(SYNTHETIC_MARKER, row.get("clause_text") or "")

	def test_std_smoke_017_all_clauses_pdf_verbatim(self) -> None:
		rows = frappe.get_all(
			"STD Clause",
			filters={"package_id": CANONICAL_PACKAGE_ID},
			fields=["metadata_json"],
		)
		self.assertEqual(len(rows), 94)
		for row in rows:
			metadata = json.loads(row.get("metadata_json") or "{}")
			self.assertEqual(metadata.get("clause_text_source"), "PDF_VERBATIM")

	def test_std_smoke_018_parameters_have_source_hashes(self) -> None:
		tds_rows = frappe.get_all(
			"STD Parameter",
			filters={"package_id": CANONICAL_PACKAGE_ID, "parameter_key": ["like", "%.parameter.tds.%"]},
			fields=["content_hash", "metadata_json"],
		)
		scc_rows = frappe.get_all(
			"STD Parameter",
			filters={"package_id": CANONICAL_PACKAGE_ID, "parameter_key": ["like", "%.parameter.scc.%"]},
			fields=["content_hash", "metadata_json"],
		)
		self.assertGreaterEqual(len(tds_rows), 1)
		self.assertGreaterEqual(len(scc_rows), 1)
		for row in tds_rows + scc_rows:
			metadata = json.loads(row.get("metadata_json") or "{}")
			self.assertTrue(row.get("content_hash") or metadata.get("normalized_text_hash"))

	def test_std_smoke_019_legal_gate_blocks_activation(self) -> None:
		version = frappe.get_doc("STD Version", CANONICAL_PACKAGE_ID)
		self.assertEqual(int(version.activation_allowed), 0)
		blockers = frappe.get_all(
			"STD Validation Finding",
			filters={
				"package_id": CANONICAL_PACKAGE_ID,
				"finding_code": "LEGAL_REVIEW_PENDING",
				"severity": "BLOCKER",
			},
			fields=["name"],
		)
		self.assertGreater(len(blockers), 0)

	def test_std_smoke_020_post_approval_clears_legal_review_blockers(self) -> None:
		frappe.set_user("Administrator")
		approve_all_pending(CANONICAL_PACKAGE_ID)
		blockers = frappe.get_all(
			"STD Validation Finding",
			filters={
				"package_id": CANONICAL_PACKAGE_ID,
				"finding_code": "LEGAL_REVIEW_PENDING",
				"severity": "BLOCKER",
				"status": "OPEN",
			},
			fields=["name"],
		)
		self.assertEqual(len(blockers), 0)
		version = frappe.get_doc("STD Version", CANONICAL_PACKAGE_ID)
		self.assertEqual(int(version.activation_allowed), 1)

	def test_verbatim_reconciliation_payload_present(self) -> None:
		inspection = PackageReader(default_seed_zip_path_v1_1()).inspect()
		payload = inspection.parsed_payloads.get("verbatim_reconciliation") or {}
		self.assertEqual(payload.get("summary", {}).get("clauses"), 94)
		self.assertEqual(payload.get("summary", {}).get("parameters"), 155)
