# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-06 — core read API contract tests (TDD first)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.read import (
	get_std_clause,
	get_std_families,
	get_std_family,
	get_std_version,
	get_std_version_sections,
	get_std_version_source_traceability,
)
from kentender_procurement.std_engine.constants import (
	CANONICAL_FAMILY_CODE,
	CANONICAL_PACKAGE_ID,
	COMMIT_TARGET_STATE_M1,
	PACKAGE_QUALITY_RECONCILED_DRAFT,
	UI_MODE_READ_ONLY_INSPECTION,
)
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path
from kentender_procurement.std_engine.services.envelope import ENVELOPE_KEYS
from kentender_procurement.std_engine.tests.test_be_04_commit_importer import (
	clear_canonical_package_state,
)


def _assert_envelope(test_case: IntegrationTestCase, payload: dict) -> None:
	for key in ENVELOPE_KEYS:
		with test_case.subTest(envelope=key):
			test_case.assertIn(key, payload)


class TestBe06ReadApiEnvelope(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		clear_canonical_package_state()
		CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()

	@classmethod
	def tearDownClass(cls) -> None:
		clear_canonical_package_state()
		super().tearDownClass()

	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_std_families()

	def test_get_std_families_returns_canonical_family(self) -> None:
		out = get_std_families()
		_assert_envelope(self, out)
		families = out["data"]["families"]
		self.assertEqual(len(families), 1)
		self.assertEqual(families[0]["familyCode"], CANONICAL_FAMILY_CODE)
		self.assertEqual(families[0]["latestPackageId"], CANONICAL_PACKAGE_ID)
		self.assertIsNotNone(out["packageContext"])
		self.assertGreater(out["validationSummary"]["blockers"], 0)

	def test_get_std_family_returns_version_list(self) -> None:
		out = get_std_family(CANONICAL_FAMILY_CODE)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["familyCode"], CANONICAL_FAMILY_CODE)
		self.assertEqual(len(out["data"]["versions"]), 1)
		version = out["data"]["versions"][0]
		self.assertEqual(version["packageId"], CANONICAL_PACKAGE_ID)
		self.assertEqual(version["lifecycleState"], COMMIT_TARGET_STATE_M1)
		self.assertFalse(version["activationAllowed"])
		self.assertEqual(version["uiMode"], UI_MODE_READ_ONLY_INSPECTION)

	def test_get_std_version_returns_integrity_fields(self) -> None:
		out = get_std_version(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		ctx = out["packageContext"]
		self.assertEqual(ctx["packageId"], CANONICAL_PACKAGE_ID)
		self.assertEqual(ctx["familyCode"], CANONICAL_FAMILY_CODE)
		self.assertEqual(ctx["lifecycleState"], COMMIT_TARGET_STATE_M1)
		self.assertFalse(ctx["activationAllowed"])
		self.assertFalse(ctx["canEdit"])
		self.assertFalse(ctx["canActivate"])
		self.assertEqual(ctx["uiMode"], UI_MODE_READ_ONLY_INSPECTION)
		self.assertEqual(ctx["packageQuality"], PACKAGE_QUALITY_RECONCILED_DRAFT)
		self.assertTrue(out["data"]["packageSha256"])
		self.assertTrue(out["audit"]["snapshotHash"])

	def test_get_std_version_source_traceability(self) -> None:
		out = get_std_version_source_traceability(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertEqual(len(out["data"]["sourceDocuments"]), 1)
		doc = out["data"]["sourceDocuments"][0]
		self.assertEqual(doc["role"], "LEGAL_MASTER_SOURCE")
		self.assertTrue(doc["hash"])
		self.assertIn("DOC 10", doc["name"])
		self.assertEqual(len(out["data"]["anchors"]), 19)

	def test_get_std_version_sections_and_clauses(self) -> None:
		out = get_std_version_sections(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertEqual(len(out["data"]["sections"]), 14)
		self.assertEqual(len(out["data"]["clauses"]), 93)
		section = out["data"]["sections"][0]
		for key in ("id", "code", "name"):
			with self.subTest(section_field=key):
				self.assertIn(key, section)

	def test_get_std_clause_detail(self) -> None:
		clause_key = frappe.get_all(
			"STD Clause",
			filters={"package_id": CANONICAL_PACKAGE_ID},
			pluck="name",
			limit=1,
		)[0]
		out = get_std_clause(clause_key)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["id"], clause_key)
		self.assertTrue(out["data"]["code"])
		self.assertTrue(out["data"]["name"])
		self.assertEqual(out["packageContext"]["packageId"], CANONICAL_PACKAGE_ID)

	def test_not_found_envelopes(self) -> None:
		missing_version = get_std_version("DOES-NOT-EXIST")
		self.assertFalse(missing_version.get("ok", True))
		self.assertEqual(missing_version["error_code"], "STD_VERSION_NOT_FOUND")
		_assert_envelope(self, missing_version)

		missing_family = get_std_family("DOES-NOT-EXIST")
		self.assertEqual(missing_family["error_code"], "STD_FAMILY_NOT_FOUND")

		missing_clause = get_std_clause("DOES-NOT-EXIST")
		self.assertEqual(missing_clause["error_code"], "STD_CLAUSE_NOT_FOUND")
