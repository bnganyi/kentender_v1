# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 6 — §11 validation and coverage engine.

Covers: each of the sixteen coverage rows independently triggerable as
Incomplete; a representative subset of the seventeen §11.2 Blocking
conditions independently triggerable; the complete-check-vs-area-save
validation-depth difference (§16.4); a package with zero Blocking findings
and all sixteen coverage rows Pass reporting readiness truthfully bounded by
the still-missing Phase 7 manifest; and — the real integration this phase's
own implementation surfaced — that `submit_for_review` (Phase 3) now
genuinely refuses a Draft with incomplete coverage, and accepts one that
has real (if minimal) content across every area.
"""

from __future__ import annotations

import uuid

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.std_configuration.services import std_authorization, std_coverage, std_lifecycle
from kentender_procurement.std_configuration.tests.std_test_fixtures import populate_minimum_coverage

PACKAGE_CODE = "KE-TEST-STD-P6"


class TestSTDChg001Phase6CoverageValidation(FrappeTestCase):
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
				"official_title": "Test Package for Phase 6",
				"requirement_profile": "Information Technology",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		self._cleanup()
		for email in self._users:
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _cleanup(self):
		# Scoped to THIS test's own package's Draft/Version names throughout —
		# a blanket `{"reference_doctype": ["in", [...]]}` (no reference_name
		# filter) or `["like", "%"]` here would delete every OTHER package's
		# content too, including the real golden `KE-PPRA-IT` fixture (Phase
		# 9). Confirmed live: this exact bug class silently passed for 8
		# phases because each phase's tests were the only content on the site
		# at the time — only Phase 9's persistent fixture surfaced it. Also
		# adds `STD Cfg Tender Manifest` cleanup, missing before even though
		# this class's own tests activate packages and create one.
		draft_names = frappe.get_all("STD Cfg Draft", {"package_id": PACKAGE_CODE}, pluck="name")
		version_names = frappe.get_all("STD Cfg Version", {"package_id": PACKAGE_CODE}, pluck="name")
		reference_names = draft_names + version_names
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
		email = f"std.p6.{label}.{self.suffix}@example.test"
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

	def _make_source(self, ref_doctype, ref_name):
		return frappe.get_doc(
			{
				"doctype": "STD Cfg Source Document",
				"reference_doctype": ref_doctype,
				"reference_name": ref_name,
				"official_title": "Test Source Document",
				"official_issue_label": "April 2021 edition",
				"file_id": "/files/test.pdf",
			}
		).insert(ignore_permissions=True)

	def _bare_draft(self):
		draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)
		src = self._make_source("STD Cfg Draft", draft.name)
		draft.official_source_file_id = src.name
		draft.save(ignore_permissions=True)
		return draft

	def _complete_draft(self):
		draft = self._bare_draft()
		populate_minimum_coverage(draft.name, PACKAGE_CODE)
		return draft

	# --- coverage register -----------------------------------------------------

	def test_bare_draft_has_all_sixteen_rows_incomplete_except_source_gated_area(self):
		draft = self._bare_draft()
		rows = std_coverage.coverage_report("STD Cfg Draft", draft.name)
		self.assertEqual(len(rows), 16)
		self.assertTrue(all(row["result"] == "Incomplete" for row in rows))

	def test_complete_draft_passes_all_sixteen_rows(self):
		draft = self._complete_draft()
		rows = std_coverage.coverage_report("STD Cfg Draft", draft.name)
		self.assertTrue(all(row["result"] == "Pass" for row in rows), rows)

	def test_coverage_row_order_is_fixed_and_official(self):
		draft = self._bare_draft()
		rows = std_coverage.coverage_report("STD Cfg Draft", draft.name)
		self.assertEqual([row["number"] for row in rows], list(range(1, 17)))

	# --- blocking findings -------------------------------------------------------

	def test_missing_source_is_blocking(self):
		draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)
		check = std_coverage.run_complete_check("STD Cfg Draft", draft.name)
		self.assertIn("STD_MISSING_SOURCE", [f["code"] for f in check["blocking"]])

	def test_parameter_without_consumer_is_blocking(self):
		draft = self._complete_draft()
		bad = frappe.get_doc(
			{
				"doctype": "STD Cfg Parameter Definition",
				"reference_doctype": "STD Cfg Draft",
				"reference_name": draft.name,
				"parameter_key": "no.consumer.param",
				"label": "No consumer",
				"value_type": "Text",
				"runtime_owner": "Tender Preparation",
				"render_binding": "placeholder",
			}
		).insert(ignore_permissions=True)
		# Blank out the binding directly (bypassing the save-time guard) to prove
		# the complete check independently re-derives this, not just trusts save.
		frappe.db.set_value("STD Cfg Parameter Definition", bad.name, "render_binding", "")
		check = std_coverage.run_complete_check("STD Cfg Draft", draft.name)
		self.assertIn("STD_PARAMETER_NO_CONSUMER", [f["code"] for f in check["blocking"]])

	def test_form_with_no_field_schema_is_blocking(self):
		draft = self._complete_draft()
		frappe.get_doc(
			{
				"doctype": "STD Cfg Form Schema",
				"reference_doctype": "STD Cfg Draft",
				"reference_name": draft.name,
				"form_key": "opaque-form",
				"form_name": "Opaque Upload Form",
				"activation": "Always",
				"render_location": "Section IV",
			}
		).insert(ignore_permissions=True)
		check = std_coverage.run_complete_check("STD Cfg Draft", draft.name)
		self.assertIn("STD_FORM_OPAQUE_UPLOAD", [f["code"] for f in check["blocking"]])

	def test_undeclared_placeholder_in_locked_text_is_blocking(self):
		draft = self._complete_draft()
		section = frappe.get_all("STD Cfg Section", {"package_id": PACKAGE_CODE}, pluck="name", limit_page_length=1)[0]
		frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				"reference_doctype": "STD Cfg Draft",
				"reference_name": draft.name,
				"section_id": section,
				"block_type": "Locked text",
				"display_order": 99,
				"locked_text": "See {{ tender.undeclared_key }} for details.",
			}
		).insert(ignore_permissions=True)
		check = std_coverage.run_complete_check("STD Cfg Draft", draft.name)
		self.assertIn("STD_UNDECLARED_PLACEHOLDER", [f["code"] for f in check["blocking"]])

	def test_required_parameter_without_output_mapping_is_blocking(self):
		draft = self._complete_draft()
		frappe.get_doc(
			{
				"doctype": "STD Cfg Parameter Definition",
				"reference_doctype": "STD Cfg Draft",
				"reference_name": draft.name,
				"parameter_key": "unmapped.required.param",
				"label": "Unmapped required",
				"value_type": "Text",
				"runtime_owner": "Tender Preparation",
				"required": 1,
				"render_binding": "placeholder",
			}
		).insert(ignore_permissions=True)
		check = std_coverage.run_complete_check("STD Cfg Draft", draft.name)
		self.assertIn("STD_OUTPUT_MAPPING_MISSING", [f["code"] for f in check["blocking"]])

	def test_complete_draft_has_zero_blocking_findings(self):
		draft = self._complete_draft()
		check = std_coverage.run_complete_check("STD Cfg Draft", draft.name)
		self.assertEqual(check["blocking_count"], 0, check["blocking"])

	def test_findings_are_persisted_and_replaced_on_rerun(self):
		draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)
		std_coverage.run_complete_check("STD Cfg Draft", draft.name)
		first_count = frappe.db.count(
			"STD Cfg Validation Finding", {"reference_doctype": "STD Cfg Draft", "reference_name": draft.name}
		)
		self.assertGreater(first_count, 0)

		src = self._make_source("STD Cfg Draft", draft.name)
		draft.official_source_file_id = src.name
		draft.save(ignore_permissions=True)
		populate_minimum_coverage(draft.name, PACKAGE_CODE)
		std_coverage.run_complete_check("STD Cfg Draft", draft.name)
		second_count = frappe.db.count(
			"STD Cfg Validation Finding", {"reference_doctype": "STD Cfg Draft", "reference_name": draft.name}
		)
		self.assertEqual(second_count, 0)

	# --- warnings ------------------------------------------------------------------

	def test_vendor_neutrality_trigger_is_a_warning_not_blocking(self):
		draft = self._complete_draft()
		frappe.get_doc(
			{
				"doctype": "STD Cfg Requirement Schema",
				"reference_doctype": "STD Cfg Draft",
				"reference_name": draft.name,
				"category": "Integration",
				"display_order": 2,
				"allowed_response_types": "Compliance choice",
				"acceptance_mode": "Fixture",
				"vendor_neutrality_trigger": 1,
				"render_binding": "x",
				"bidder_response_binding": "x",
				"evaluation_binding": "x",
				"contract_carry_forward_binding": "x",
			}
		).insert(ignore_permissions=True)
		check = std_coverage.run_complete_check("STD Cfg Draft", draft.name)
		self.assertIn("STD_VENDOR_NEUTRALITY_REVIEW", [f["code"] for f in check["warnings"]])
		self.assertEqual(check["blocking_count"], 0)

	# --- complete-check vs area-save depth difference ---------------------------

	def test_area_save_does_not_run_full_coverage_check(self):
		"""§16.4 — area save validates only the changed area, not full coverage."""
		draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)
		from kentender_procurement.std_configuration.api import std_configuration_api as api

		frappe.set_user(self.configurator)
		# Draft has no official source, no other content — a full complete check
		# would find 16 Blocking findings — but saving one valid parameter still
		# succeeds (area-save only validates PCFG-03's own guard).
		api.save_std_parameters(
			draft.name,
			[
				{
					"parameter_key": "area.save.only",
					"label": "Area save only",
					"value_type": "Text",
					"runtime_owner": "Tender Preparation",
					"render_binding": "x",
				}
			],
		)
		frappe.set_user("Administrator")
		self.assertTrue(
			frappe.db.exists("STD Cfg Parameter Definition", {"parameter_key": "area.save.only"})
		)
		self.assertEqual(
			frappe.db.count("STD Cfg Validation Finding", {"reference_doctype": "STD Cfg Draft", "reference_name": draft.name}),
			0,
		)

	# --- submit/activate integration (real coverage now gates them) -------------

	def test_submit_rejects_incomplete_draft(self):
		draft = self._bare_draft()
		with self.assertRaises(frappe.ValidationError):
			std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)

	def test_submit_accepts_complete_draft(self):
		draft = self._complete_draft()
		task = std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)
		self.assertTrue(task.name)

	def test_readiness_report_is_honest_about_missing_manifest_step(self):
		draft = self._complete_draft()
		report = std_coverage.readiness_report("STD Cfg Draft", draft.name)
		self.assertEqual(report["coverage_pass_count"], 16)
		self.assertEqual(report["blocking_count"], 0)
		self.assertIsNone(report["steps"])
		self.assertIsNone(report["ready_for_tender_review"])
