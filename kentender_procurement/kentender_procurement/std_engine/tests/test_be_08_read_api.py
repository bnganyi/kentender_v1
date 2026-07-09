# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-08 — governance read API contract tests (TDD first)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.read import (
	get_std_import_run,
	get_std_version_audit_log,
	get_std_version_diff,
	get_std_version_import_runs,
	get_std_version_usage_bindings,
	get_std_version_validation_report,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID, FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path
from kentender_procurement.std_engine.services.envelope import ENVELOPE_KEYS
from kentender_procurement.std_engine.services.governance_read_service import VERSION_DIFF_STUB_REASON
from kentender_procurement.std_engine.tests.test_be_04_commit_importer import (
	clear_canonical_package_state,
)
from kentender_procurement.std_engine.validation.validation_engine import get_validation_summary


def _assert_envelope(test_case: IntegrationTestCase, payload: dict) -> None:
	for key in ENVELOPE_KEYS:
		with test_case.subTest(envelope=key):
			test_case.assertIn(key, payload)


class TestBe08GovernanceReadApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		clear_canonical_package_state()
		cls.commit_out = CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()

	@classmethod
	def tearDownClass(cls) -> None:
		clear_canonical_package_state()
		super().tearDownClass()

	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_validation_report_returns_persisted_findings(self) -> None:
		out = get_std_version_validation_report(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertIsNotNone(out["data"]["validationRun"])
		self.assertEqual(out["data"]["validationRun"]["runKey"], f"VAL-{CANONICAL_PACKAGE_ID}")
		self.assertGreater(out["data"]["count"], 0)
		self.assertGreater(out["data"]["summary"]["blockers"], 0)
		self.assertGreater(out["data"]["summary"]["warnings"], 0)
		self.assertEqual(out["data"]["summary"], get_validation_summary(CANONICAL_PACKAGE_ID))

		finding = out["data"]["findings"][0]
		for field in ("id", "code", "name", "severity", "objectType", "objectId"):
			with self.subTest(field=field):
				self.assertIn(field, finding)

	def test_audit_log_returns_import_and_validation_events(self) -> None:
		out = get_std_version_audit_log(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertGreater(out["data"]["count"], 0)
		self.assertGreaterEqual(out["pagination"]["total"], out["data"]["count"])
		event_types = {row["eventType"] for row in out["data"]["events"]}
		self.assertIn("PACKAGE_IMPORT_COMMITTED", event_types)

		event = out["data"]["events"][0]
		for field in ("id", "code", "name", "eventType", "occurredAt"):
			with self.subTest(field=field):
				self.assertIn(field, event)

	def test_usage_bindings_seeded_from_smoke_expectations(self) -> None:
		out = get_std_version_usage_bindings(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertEqual(out["data"]["count"], 3)
		self.assertEqual(len(out["data"]["bindings"]), 3)
		kpis = out["data"]["usageKpis"]
		self.assertEqual(kpis["totalTendersBoundAllVersions"], 0)
		self.assertEqual(kpis["activeTendersThisVersion"], 0)
		self.assertEqual(kpis["historicalRecords"], 0)
		self.assertEqual(kpis["openAddenda"], 0)
		self.assertEqual(kpis["activeStabilityBadge"], "Draft")
		for binding in out["data"]["bindings"]:
			self.assertEqual(binding["fixtureSource"], FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION)
			for field in ("id", "code", "name"):
				with self.subTest(field=field):
					self.assertTrue(binding[field])

	def test_version_diff_single_version_stub(self) -> None:
		out = get_std_version_diff(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, out)
		self.assertFalse(out["data"]["compareAvailable"])
		self.assertEqual(out["data"]["reason"], VERSION_DIFF_STUB_REASON)
		self.assertEqual(out["data"]["currentVersion"]["packageId"], CANONICAL_PACKAGE_ID)
		self.assertEqual(out["data"]["comparisonVersions"], [])

	def test_import_runs_list_and_detail(self) -> None:
		list_out = get_std_version_import_runs(CANONICAL_PACKAGE_ID)
		_assert_envelope(self, list_out)
		self.assertGreaterEqual(list_out["data"]["count"], 1)

		import_run_key = self.commit_out.get("import_run_key")
		self.assertTrue(import_run_key)
		detail_out = get_std_import_run(import_run_key)
		_assert_envelope(self, detail_out)
		self.assertEqual(detail_out["data"]["importRun"]["import_run_key"], import_run_key)
		self.assertEqual(detail_out["data"]["importRun"]["package_id"], CANONICAL_PACKAGE_ID)
		self.assertIn("report", detail_out["data"]["importRun"])

	def test_not_found_envelopes(self) -> None:
		missing = get_std_version_validation_report("DOES-NOT-EXIST")
		self.assertEqual(missing["error_code"], "STD_VERSION_NOT_FOUND")
		_assert_envelope(self, missing)

		missing_run = get_std_import_run("DOES-NOT-EXIST")
		self.assertEqual(missing_run["error_code"], "STD_IMPORT_RUN_NOT_FOUND")
