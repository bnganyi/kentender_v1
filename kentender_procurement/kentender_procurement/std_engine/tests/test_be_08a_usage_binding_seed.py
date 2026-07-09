# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-08a — usage binding seed contract tests (TDD first)."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.read import get_std_version_usage_bindings
from kentender_procurement.std_engine.constants import (
	CANONICAL_PACKAGE_ID,
	FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION,
)
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.import_planner import load_optional_payloads
from kentender_procurement.std_engine.package_import.package_reader import PackageReader
from kentender_procurement.std_engine.package_import.record_mapper import map_usage_binding_record
from kentender_procurement.std_engine.package_import.usage_binding_seeder import (
	seed_usage_bindings_from_smoke_tests,
)
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path
from kentender_procurement.std_engine.tests.test_be_04_commit_importer import (
	clear_canonical_package_state,
)

CANONICAL_USAGE_BINDING_COUNT = 3


class TestBe08aUsageBindingSeed(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		clear_canonical_package_state()
		cls.commit_report = CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()

	@classmethod
	def tearDownClass(cls) -> None:
		clear_canonical_package_state()
		super().tearDownClass()

	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_commit_seeds_smoke_test_usage_bindings(self) -> None:
		self.assertEqual(
			self.commit_report["records_committed"]["usageBindings"],
			CANONICAL_USAGE_BINDING_COUNT,
		)
		self.assertEqual(
			frappe.db.count("STD Usage Binding", {"package_id": CANONICAL_PACKAGE_ID}),
			CANONICAL_USAGE_BINDING_COUNT,
		)

	def test_seeded_rows_tagged_as_smoke_expectations(self) -> None:
		rows = frappe.get_all(
			"STD Usage Binding",
			filters={"package_id": CANONICAL_PACKAGE_ID},
			fields=["binding_key", "fixture_source", "binding_status", "metadata_json"],
			order_by="binding_key asc",
		)
		self.assertEqual(len(rows), CANONICAL_USAGE_BINDING_COUNT)
		for row in rows:
			with self.subTest(binding=row.binding_key):
				self.assertEqual(row.fixture_source, FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION)
				self.assertEqual(row.binding_status, "READY_TO_IMPLEMENT")
				metadata = json.loads(row.metadata_json or "{}")
				self.assertEqual(metadata.get("fixtureSource"), FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION)
				self.assertTrue(metadata.get("displayTitle"))
				self.assertEqual(metadata.get("category"), "TENDER_BINDING_OR_CONTRACT")

	def test_usage_bindings_read_api_returns_display_titles(self) -> None:
		out = get_std_version_usage_bindings(CANONICAL_PACKAGE_ID)
		self.assertEqual(out["data"]["count"], CANONICAL_USAGE_BINDING_COUNT)
		names = {binding["name"] for binding in out["data"]["bindings"]}
		self.assertIn("Contract fields carry forward only from authorized sources.", names)
		self.assertTrue(all(binding["code"] == "TENDER_BINDING_OR_CONTRACT" for binding in out["data"]["bindings"]))

	def test_idempotent_recommit_does_not_duplicate_bindings(self) -> None:
		count_before = frappe.db.count("STD Usage Binding", {"package_id": CANONICAL_PACKAGE_ID})
		second = CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		self.assertEqual(second["commit_status"], "IDEMPOTENT_SKIP")
		self.assertEqual(
			frappe.db.count("STD Usage Binding", {"package_id": CANONICAL_PACKAGE_ID}),
			count_before,
		)

	def test_mapper_uses_test_key_as_binding_key(self) -> None:
		inspection = PackageReader(default_seed_zip_path()).inspect()
		optional_payloads = load_optional_payloads(
			default_seed_zip_path(),
			inspection.package_root,
			inspection.files_listed,
		)
		record = optional_payloads["tender_binding_smoke_tests"]["records"][0]
		from kentender_procurement.std_engine.package_import.record_mapper import (
			package_context_from_inspection,
		)

		ctx = package_context_from_inspection(inspection)
		mapped = map_usage_binding_record(record, ctx)
		self.assertEqual(mapped["binding_key"], record["test_key"])
		self.assertEqual(mapped["fixture_source"], FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION)

	def test_seeder_skips_existing_binding_keys(self) -> None:
		from kentender_procurement.std_engine.package_import.record_mapper import (
			package_context_from_inspection,
		)

		inspection = PackageReader(default_seed_zip_path()).inspect()
		optional_payloads = load_optional_payloads(
			default_seed_zip_path(),
			inspection.package_root,
			inspection.files_listed,
		)
		ctx = package_context_from_inspection(inspection)
		stats: dict[str, int] = {}
		seed_usage_bindings_from_smoke_tests(
			ctx,
			optional_payloads.get("tender_binding_smoke_tests"),
			stats,
		)
		self.assertEqual(stats["usageBindings"], 0)
