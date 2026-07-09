# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-05 — validation engine tests (TDD first)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.dry_run_importer import DryRunImporter
from kentender_procurement.std_engine.package_import.package_reader import PackageReader
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path
from kentender_procurement.std_engine.tests.test_be_04_commit_importer import (
	clear_canonical_package_state,
)
from kentender_procurement.std_engine.validation.validation_engine import (
	ValidationEngine,
	get_validation_summary,
)
from kentender_procurement.std_engine.validation.validators.activation_blockers import (
	ActivationBlockersValidator,
)
from kentender_procurement.std_engine.validation.validators.clause_coverage import (
	ClauseCoverageValidator,
)
from kentender_procurement.std_engine.validation.validators.context import ValidationContext
from kentender_procurement.std_engine.validation.validators.source_traceability import (
	SourceTraceabilityValidator,
)


class TestBe05ValidationValidatorsUnit(UnitTestCase):
	def test_activation_blockers_validator_emits_blockers(self) -> None:
		inspection = PackageReader(default_seed_zip_path()).inspect()
		context = ValidationContext(package_id=CANONICAL_PACKAGE_ID, inspection=inspection)
		findings = ActivationBlockersValidator().validate(context)
		self.assertGreater(len(findings), 0)
		self.assertTrue(all(f.severity == "BLOCKER" for f in findings))
		self.assertTrue(all(f.lifecycle_gate == "ACTIVATION" for f in findings))

	def test_clause_coverage_validator_clean_for_canonical_inspection(self) -> None:
		inspection = PackageReader(default_seed_zip_path()).inspect()
		context = ValidationContext(
			package_id=CANONICAL_PACKAGE_ID,
			inspection=inspection,
			db_checks_enabled=False,
		)
		findings = ClauseCoverageValidator().validate(context)
		self.assertEqual(findings, [])


class TestBe05ValidationEngineIntegration(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		clear_canonical_package_state()
		CommitImporter(default_seed_zip_path(), default_official_pdf_path()).run()

	@classmethod
	def tearDownClass(cls) -> None:
		clear_canonical_package_state()
		super().tearDownClass()

	def test_commit_triggers_validation_run_and_blockers(self) -> None:
		self.assertTrue(frappe.db.exists("STD Validation Run", f"VAL-{CANONICAL_PACKAGE_ID}"))
		blockers = frappe.get_all(
			"STD Validation Finding",
			filters={"package_id": CANONICAL_PACKAGE_ID, "severity": "BLOCKER"},
		)
		warnings = frappe.get_all(
			"STD Validation Finding",
			filters={"package_id": CANONICAL_PACKAGE_ID, "severity": "WARNING"},
		)
		self.assertGreater(len(blockers), 0)
		self.assertGreater(len(warnings), 0)
		self.assertEqual(
			frappe.db.get_value("STD Version", CANONICAL_PACKAGE_ID, "validation_status"),
			"BLOCKED",
		)

	def test_validation_summary_matches_persisted_findings(self) -> None:
		summary = get_validation_summary(CANONICAL_PACKAGE_ID)
		blockers = frappe.db.count(
			"STD Validation Finding",
			{"package_id": CANONICAL_PACKAGE_ID, "severity": "BLOCKER"},
		)
		warnings = frappe.db.count(
			"STD Validation Finding",
			{"package_id": CANONICAL_PACKAGE_ID, "severity": "WARNING"},
		)
		self.assertEqual(summary["blockers"], blockers)
		self.assertEqual(summary["warnings"], warnings)

	def test_source_traceability_passes_for_canonical_import(self) -> None:
		context = ValidationContext(package_id=CANONICAL_PACKAGE_ID, db_checks_enabled=True)
		findings = SourceTraceabilityValidator().validate(context)
		self.assertEqual(findings, [])

	def test_rerun_validation_is_idempotent(self) -> None:
		engine = ValidationEngine()
		inspection = PackageReader(default_seed_zip_path()).inspect()
		dry_report = DryRunImporter(default_seed_zip_path(), default_official_pdf_path()).run()
		first = engine.run_for_package(
			CANONICAL_PACKAGE_ID,
			dry_report=dry_report,
			inspection=inspection,
			run_type="MANUAL_REVALIDATION",
		)
		first_count = frappe.db.count(
			"STD Validation Finding",
			{"package_id": CANONICAL_PACKAGE_ID},
		)
		second = engine.run_for_package(
			CANONICAL_PACKAGE_ID,
			dry_report=dry_report,
			inspection=inspection,
			run_type="MANUAL_REVALIDATION",
		)
		second_count = frappe.db.count(
			"STD Validation Finding",
			{"package_id": CANONICAL_PACKAGE_ID},
		)
		frappe.db.commit()
		self.assertEqual(first.run_key, second.run_key)
		self.assertEqual(first_count, second_count)
		self.assertEqual(first.summary, second.summary)

	def test_clause_coverage_flags_dangling_anchor_in_database(self) -> None:
		clause_name = f"{CANONICAL_PACKAGE_ID}.clause.test-dangling-anchor"
		if frappe.db.exists("STD Clause", clause_name):
			frappe.delete_doc("STD Clause", clause_name, force=True)
		frappe.get_doc(
			{
				"doctype": "STD Clause",
				"package_id": CANONICAL_PACKAGE_ID,
				"family_code": "KE-PPRA-IT",
				"version_code": CANONICAL_PACKAGE_ID,
				"clause_key": clause_name,
				"section": frappe.get_all(
					"STD Section",
					filters={"package_id": CANONICAL_PACKAGE_ID},
					pluck="name",
					limit=1,
				)[0],
				"object_key": "test-dangling-anchor",
				"source_anchor": "missing.anchor.key",
			}
		).insert(ignore_permissions=True, ignore_links=True)
		frappe.db.commit()

		findings = ClauseCoverageValidator().validate(
			ValidationContext(package_id=CANONICAL_PACKAGE_ID, db_checks_enabled=True)
		)
		self.assertTrue(any(f.finding_code == "CLAUSE_DANGLING_ANCHOR" for f in findings))
		frappe.delete_doc("STD Clause", clause_name, force=True)
		frappe.db.commit()

	def test_validation_run_entrypoint(self) -> None:
		from kentender_procurement.std_engine.validation.run import run

		frappe.set_user("Administrator")
		out = run(CANONICAL_PACKAGE_ID)
		self.assertEqual(out["package_id"], CANONICAL_PACKAGE_ID)
		self.assertEqual(out["run_key"], f"VAL-{CANONICAL_PACKAGE_ID}")
		self.assertGreaterEqual(out["finding_count"], 0)
		self.assertGreater(out["summary"]["blockers"], 0)
