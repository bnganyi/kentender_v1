# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 10 — §17.2-17.9 one-time reuse/transformation utility.

Covers: the reuse bundle's own checksum integrity check (passes against the
real bundle, fails against a tampered copy); the bundle loader's real parsed
counts against the real `KE-PPRA-IT-2022-04` seed package; the disposition
register covering every mandatory §17.5 content class (including the honest
`Unavailable` rows where the real bundle has no per-item data); real
`STD Cfg Assistance Batch` proposals produced for every mapped class, with
counts traceable to the source; accepted items passing the SAME target-entity
validators as direct entry (§17.6 step 7, §17.7's "loses its legacy
character"); the run refusing to write against a non-Draft state (§17.6's
closing paragraph); and the §17.8 reconciliation report's shape.
"""

from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.std_configuration.api import std_configuration_api as api
from kentender_procurement.std_configuration.services import (
	std_assistance,
	std_authorization,
	std_lifecycle,
	std_reuse_bundle,
	std_reuse_transformation,
)
from kentender_procurement.std_configuration.tests.std_test_fixtures import populate_minimum_coverage

PACKAGE_CODE = "KE-TEST-STD-P10"


class TestSTDChg001Phase10ReuseTransformation(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.suffix = uuid.uuid4().hex[:8]
		self._users: list[str] = []
		self._cleanup()
		std_authorization.ensure_std_configuration_governance_roles()
		self.configurator = self._user("configurator", "STD Configurator")
		self.reviewer = self._user("reviewer", "STD Reviewer")
		self.package = frappe.get_doc(
			{
				"doctype": "STD Cfg Package",
				"package_code": PACKAGE_CODE,
				"official_title": "Test Package for Phase 10",
				"requirement_profile": "Information Technology",
			}
		).insert(ignore_permissions=True)
		self.draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)

	def tearDown(self):
		frappe.set_user("Administrator")
		self._cleanup()
		for email in self._users:
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _cleanup(self):
		# Scoped to THIS test's own package's Draft/Version names throughout —
		# see Phases 1-9's own `_cleanup()` docstrings for why an unscoped
		# wildcard delete here would be a real, previously-proven bug.
		draft_names = frappe.get_all("STD Cfg Draft", {"package_id": PACKAGE_CODE}, pluck="name")
		version_names = frappe.get_all("STD Cfg Version", {"package_id": PACKAGE_CODE}, pluck="name")
		reference_names = draft_names + version_names
		if draft_names:
			frappe.db.delete("STD Cfg Reuse Run", {"draft_id": ["in", draft_names]})
			frappe.db.delete("STD Cfg Assistance Batch", {"draft_id": ["in", draft_names]})
		if reference_names:
			for doctype in std_lifecycle.REFERENCE_SCOPED_CONTENT_DOCTYPES:
				frappe.db.delete(doctype, {"reference_name": ["in", reference_names]})
			frappe.db.delete("STD Cfg Validation Finding", {"reference_name": ["in", reference_names]})
		for section in frappe.get_all("STD Cfg Section", {"package_id": PACKAGE_CODE}, pluck="name"):
			frappe.db.delete("STD Cfg Content Block", {"section_id": section})
			frappe.db.delete("STD Cfg Section", {"name": section})
		frappe.db.delete("STD Cfg Tender Manifest", {"package_code": PACKAGE_CODE})
		if draft_names:
			task_names = frappe.get_all("STD Cfg Review Task", {"draft_id": ["in", draft_names]}, pluck="name")
			if task_names:
				frappe.db.delete("STD Cfg Decision", {"review_task_id": ["in", task_names]})
			frappe.db.delete("STD Cfg Review Task", {"draft_id": ["in", draft_names]})
		frappe.db.delete("STD Cfg Source Document", {"official_title": ["like", "Test Source%"]})
		frappe.db.delete("STD Cfg Draft", {"package_id": PACKAGE_CODE})
		if version_names:
			frappe.db.delete("STD Cfg Runtime Manifest", {"std_version_id": ["in", version_names]})
		frappe.db.delete("STD Cfg Version", {"package_id": PACKAGE_CODE})
		frappe.db.delete("STD Cfg Package", {"package_code": PACKAGE_CODE})
		frappe.db.commit()

	def _user(self, label: str, role: str) -> str:
		email = f"std.p10.{label}.{self.suffix}@example.test"
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": label,
				"enabled": 1,
				"send_welcome_email": 0,
				"roles": [{"role": role}],
			}
		).insert(ignore_permissions=True)
		self._users.append(email)
		return email

	# --- bundle integrity and inventory -----------------------------------------

	def test_bundle_checksums_verify_against_real_bundle(self):
		result = std_reuse_bundle.verify_bundle_checksums(std_reuse_bundle.DEFAULT_BUNDLE_DIR)
		self.assertTrue(result["verified"], result)
		self.assertGreater(result["file_count"], 0)

	def test_bundle_checksum_detects_tampering(self):
		with tempfile.TemporaryDirectory() as tmp:
			tmp_bundle = Path(tmp) / "bundle"
			shutil.copytree(std_reuse_bundle.DEFAULT_BUNDLE_DIR, tmp_bundle)
			target = tmp_bundle / "template" / "family.json"
			target.write_text(target.read_text() + " ")
			result = std_reuse_bundle.verify_bundle_checksums(str(tmp_bundle))
			self.assertFalse(result["verified"])
			self.assertIn("template/family.json", result["mismatched"])

	def test_load_bundle_parses_real_counts(self):
		bundle = std_reuse_bundle.load_bundle(std_reuse_bundle.DEFAULT_BUNDLE_DIR)
		self.assertEqual(len(bundle["sections"]), 21)
		self.assertEqual(len(bundle["clauses"]), 94)
		self.assertEqual(len(bundle["parameters"]), 155)
		self.assertEqual(len(bundle["price_schedule_catalog"]), 6)
		self.assertEqual(len(bundle["evaluation_schema"][0]["criteria"]), 4)
		self.assertEqual(len(bundle["form_catalog"]), 25)
		self.assertEqual(len(bundle["form_fields"]), 75)

	# --- the transformation run itself -------------------------------------------

	def _run(self):
		return std_reuse_transformation.run_reuse_transformation(self.draft.name, actor=self.configurator)

	def test_run_creates_sections_directly_for_mapped_codes(self):
		self._run()
		mapped_codes = {our_code for our_code, *_ in std_reuse_transformation.SECTION_CODE_MAP.values()}
		created = frappe.get_all("STD Cfg Section", {"package_id": PACKAGE_CODE}, pluck="section_code")
		self.assertEqual(set(created), mapped_codes)

	def test_run_is_idempotent_on_sections(self):
		self._run()
		before = frappe.db.count("STD Cfg Section", {"package_id": PACKAGE_CODE})
		self._run()
		after = frappe.db.count("STD Cfg Section", {"package_id": PACKAGE_CODE})
		self.assertEqual(before, after)

	def test_disposition_register_covers_mandatory_content_classes(self):
		run = self._run()
		classes = {row.content_class for row in run.register}
		self.assertEqual(
			classes,
			{"Label/Help", "Locked text", "Parameter", "Requirement", "Schedule", "Price", "Evaluation", "Form", "Contract", "Fixture"},
		)
		dispositions = {row.disposition for row in run.register}
		self.assertEqual(dispositions, {"Reuse as proposal", "Unavailable", "Reference only", "Retire"})

	def test_run_produces_real_batches_with_traceable_counts(self):
		bundle = std_reuse_bundle.load_bundle(std_reuse_bundle.DEFAULT_BUNDLE_DIR)
		run = self._run()

		by_class = {row.content_class: row for row in run.register}
		self.assertEqual(by_class["Parameter"].proposed_row_count + by_class["Parameter"].unresolved_count, len(bundle["parameters"]))
		self.assertEqual(by_class["Price"].proposed_row_count, len(bundle["price_schedule_catalog"]))
		self.assertEqual(by_class["Evaluation"].proposed_row_count, len(bundle["evaluation_schema"][0]["criteria"]))
		self.assertEqual(by_class["Form"].proposed_row_count, len(bundle["form_catalog"]))
		self.assertGreater(by_class["Locked text"].proposed_row_count, 0)
		self.assertEqual(
			by_class["Locked text"].proposed_row_count + by_class["Locked text"].unresolved_count, len(bundle["clauses"])
		)

		# Every "Reuse as proposal" row targeting a governed assistance entity
		# (i.e. every one except Sections, which are created directly — see
		# `_ensure_sections`'s docstring) links to a real batch.
		for row in run.register:
			if (
				row.disposition == "Reuse as proposal"
				and row.target_entity in std_assistance.ALLOWED_TARGET_ENTITIES
				and row.proposed_row_count
			):
				self.assertTrue(row.assistance_batch_id)
				batch = frappe.get_doc("STD Cfg Assistance Batch", row.assistance_batch_id)
				self.assertEqual(len(batch.proposals), row.proposed_row_count)

	def test_unavailable_rows_have_no_target_entity_and_no_batch(self):
		run = self._run()
		for row in run.register:
			if row.disposition == "Unavailable":
				self.assertFalse(row.target_entity)
				self.assertFalse(row.assistance_batch_id)
				self.assertEqual(row.proposed_row_count, 0)

	def test_accepted_proposals_pass_real_target_validators(self):
		# Each `prepare_proposal` call snapshots the Draft's CURRENT
		# `record_version`; accepting one batch bumps it and correctly stales
		# any OTHER batch prepared earlier in the same run (§16.2 staleness —
		# proven directly in Phase 8's own tests). So here each target
		# entity's proposal is prepared and accepted immediately, one at a
		# time, rather than reusing the one combined run's batches out of
		# order — proving the mapped payload itself passes real validators,
		# which is this test's actual point.
		bundle = std_reuse_bundle.load_bundle(std_reuse_bundle.DEFAULT_BUNDLE_DIR)

		price_items, _ = std_reuse_transformation._map_price_schemas(bundle)
		price_batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "pricing/price_schedule_catalog.json", price_items[:1], actor=self.configurator
		)
		result = std_assistance.accept_items(price_batch.name, [price_batch.proposals[0].name], actor=self.configurator)
		self.assertTrue(
			frappe.db.exists(
				"STD Cfg Price Schema",
				{"name": result["accepted"][0]["created"], "reference_doctype": "STD Cfg Draft", "reference_name": self.draft.name},
			)
		)

		eval_items, _ = std_reuse_transformation._map_evaluation_criteria(bundle)
		eval_batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "evaluation/evaluation_schema.json", eval_items[:1], actor=self.configurator
		)
		result = std_assistance.accept_items(eval_batch.name, [eval_batch.proposals[0].name], actor=self.configurator)
		self.assertTrue(frappe.db.exists("STD Cfg Evaluation Schema", {"name": result["accepted"][0]["created"]}))

		form_items, _ = std_reuse_transformation._map_forms(bundle)
		form_batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "forms/form_catalog.json", form_items[:1], actor=self.configurator
		)
		result = std_assistance.accept_items(form_batch.name, [form_batch.proposals[0].name], actor=self.configurator)
		form_doc = frappe.get_doc("STD Cfg Form Schema", result["accepted"][0]["created"])
		self.assertGreater(len(form_doc.fields), 0)

	def test_refuses_to_run_against_non_draft_state(self):
		self.draft.official_source_file_id = frappe.get_doc(
			{
				"doctype": "STD Cfg Source Document",
				"reference_doctype": "STD Cfg Draft",
				"reference_name": self.draft.name,
				"official_title": "Test Source Document",
				"official_issue_label": "April 2021 edition",
				"file_id": "/files/test.pdf",
			}
		).insert(ignore_permissions=True).name
		self.draft.save(ignore_permissions=True)
		populate_minimum_coverage(self.draft.name, PACKAGE_CODE)
		std_lifecycle.submit_for_review(self.draft.name, reviewer=self.reviewer, actor=self.configurator)
		self.draft.reload()
		self.assertNotEqual(self.draft.state, "Draft")
		with self.assertRaises(frappe.ValidationError):
			self._run()

	def test_reconciliation_report_shape(self):
		run = self._run()
		report = std_reuse_transformation.reconciliation_report(run.name)
		self.assertEqual(report["unmapped_source_fields"], 0)
		self.assertEqual(report["duplicate_target_keys"], 0)
		self.assertTrue(report["unavailable_targets"])
		self.assertIn("Parameter", report["by_content_class"])
		self.assertGreater(report["by_content_class"]["Parameter"]["proposed"], 0)

	# --- API layer -----------------------------------------------------------------

	def test_full_path_through_api_layer(self):
		frappe.set_user(self.configurator)
		result = api.run_std_reuse_transformation(self.draft.name)
		frappe.set_user("Administrator")
		self.assertTrue(result["run_id"])
		self.assertTrue(result["register"])

		report = api.get_std_reuse_reconciliation_report(result["run_id"])
		self.assertEqual(report["unmapped_source_fields"], 0)
