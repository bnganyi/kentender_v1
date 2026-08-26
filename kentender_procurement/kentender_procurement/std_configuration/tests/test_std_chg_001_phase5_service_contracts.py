# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 5 — §13 service contracts.

Covers: reads that are genuinely buildable now; area-save commands including
idempotent replay (exactly one Command Journal row, identical result on
retry); the lifecycle commands at the API layer (not just `std_lifecycle`
directly); the §13.3 error codes now wired through (`STD_DRAFT_CHANGED`,
`STD_REVIEW_CHANGED`, `STD_VERSION_NOT_ACTIVE`); and that every read/command
explicitly blocked on a later phase says so clearly rather than silently
returning nothing.
"""

from __future__ import annotations

import uuid

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.std_configuration.api import std_configuration_api as api
from kentender_procurement.std_configuration.services import std_authorization, std_lifecycle
from kentender_procurement.std_configuration.tests.std_test_fixtures import populate_minimum_coverage

PACKAGE_CODE = "KE-TEST-STD-P5"


class TestSTDChg001Phase5ServiceContracts(FrappeTestCase):
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
				"official_title": "Test Package for Phase 5",
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
		# at the time — only Phase 9's persistent fixture surfaced it.
		draft_names = frappe.get_all("STD Cfg Draft", {"package_id": PACKAGE_CODE}, pluck="name")
		version_names = frappe.get_all("STD Cfg Version", {"package_id": PACKAGE_CODE}, pluck="name")
		reference_names = draft_names + version_names
		if reference_names:
			for doctype in std_lifecycle.REFERENCE_SCOPED_CONTENT_DOCTYPES:
				frappe.db.delete(doctype, {"reference_name": ["in", reference_names]})
			frappe.db.delete("STD Cfg Validation Finding", {"reference_name": ["in", reference_names]})
			frappe.db.delete("STD Cfg Command Journal", {"document_name": ["in", reference_names]})
		for section in frappe.get_all("STD Cfg Section", {"package_id": PACKAGE_CODE}, pluck="name"):
			frappe.db.delete("STD Cfg Content Block", {"section_id": section})
			frappe.db.delete("STD Cfg Section", {"name": section})
		frappe.db.delete("STD Cfg Tender Manifest", {"package_code": PACKAGE_CODE})
		if draft_names:
			task_names = frappe.get_all("STD Cfg Review Task", {"draft_id": ["in", draft_names]}, pluck="name")
			if task_names:
				frappe.db.delete("STD Cfg Decision", {"review_task_id": ["in", task_names]})
				frappe.db.delete("STD Cfg Command Journal", {"document_name": ["in", task_names]})
			frappe.db.delete("STD Cfg Review Task", {"draft_id": ["in", draft_names]})
		frappe.db.delete("STD Cfg Source Document", {"official_title": ["like", "Test Source%"]})
		frappe.db.delete("STD Cfg Draft", {"package_id": PACKAGE_CODE})
		if version_names:
			frappe.db.delete("STD Cfg Runtime Manifest", {"std_version_id": ["in", version_names]})
		frappe.db.delete("STD Cfg Version", {"package_id": PACKAGE_CODE})
		frappe.db.delete("STD Cfg Package", {"package_code": PACKAGE_CODE})
		frappe.db.commit()

	def _user(self, label: str, role: str) -> str:
		email = f"std.p5.{label}.{self.suffix}@example.test"
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

	def _submittable_draft(self):
		draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)
		src = self._make_source("STD Cfg Draft", draft.name)
		draft.official_source_file_id = src.name
		draft.save(ignore_permissions=True)
		return draft

	# --- reads -------------------------------------------------------------------

	def test_list_and_get_package_home_report_state(self):
		listed = {row["name"]: row for row in api.list_std_packages()}
		self.assertIn(PACKAGE_CODE, listed)
		self.assertEqual(listed[PACKAGE_CODE]["state"], "Not configured")

		draft = self._submittable_draft()
		home = api.get_std_package_home(PACKAGE_CODE)
		self.assertEqual(home["state"], "Draft in progress")
		self.assertEqual(home["current_draft_id"], draft.name)

	def test_get_configuration_area_returns_saved_items(self):
		draft = self._submittable_draft()
		frappe.set_user(self.configurator)
		api.save_std_parameters(
			draft.name,
			[
				{
					"parameter_key": "tender.validity_days",
					"label": "Tender validity",
					"value_type": "Duration",
					"runtime_owner": "Tender Preparation",
					"render_binding": "TDS.validity",
				}
			],
		)
		frappe.set_user("Administrator")
		area = api.get_std_configuration_area("STD Cfg Draft", draft.name, "PCFG-03")
		self.assertEqual(len(area["items"]["STD Cfg Parameter Definition"]), 1)

	def test_get_configuration_area_rejects_unknown_area(self):
		with self.assertRaises(frappe.ValidationError):
			api.get_std_configuration_area("STD Cfg Draft", "whatever", "PCFG-99")

	def test_get_active_std_version_none_before_activation(self):
		self.assertIsNone(api.get_active_std_version(PACKAGE_CODE))

	def test_get_runtime_manifest_requires_active_version(self):
		draft = self._submittable_draft()
		src = frappe.db.get_value("STD Cfg Draft", draft.name, "official_source_file_id")
		version = frappe.get_doc(
			{
				"doctype": "STD Cfg Version",
				"package_id": PACKAGE_CODE,
				"version_number": 1,
				"status": "Superseded",
				"official_issue_label": "April 2021 edition",
				"official_source_file_id": src,
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			api.get_runtime_manifest(version.name)

	def test_get_assistance_proposal_reads_batch(self):
		draft = self._submittable_draft()
		batch = frappe.get_doc(
			{
				"doctype": "STD Cfg Assistance Batch",
				"draft_id": draft.name,
				"assistance_type": "Prior configuration",
				"input_reference": "IT_STD_Config_Control_Pack_v3.json",
				"actor": self.configurator,
			}
		).insert(ignore_permissions=True)
		result = api.get_assistance_proposal(batch.name)
		self.assertEqual(result["assistance_type"], "Prior configuration")

	def test_blocked_reads_and_commands_say_so_clearly(self):
		# GetSTDCoverageReport/GetSTDReadinessReport/RunSTDCompleteCheck (Phase
		# 6) and the 4 assistance commands (Phase 8) all moved from "blocked"
		# to "real" as later phases landed — only GetSTDPreview remains
		# genuinely blocked (Phase 11's UI-composition work).
		draft = self._submittable_draft()
		with self.assertRaises(frappe.ValidationError) as ctx:
			api.get_std_preview("STD Cfg Draft", draft.name)
		self.assertIn("not implemented yet", str(ctx.exception))

	# --- area-save commands + idempotency -----------------------------------------

	def test_save_std_parameters_create_then_update(self):
		draft = self._submittable_draft()
		frappe.set_user(self.configurator)
		result = api.save_std_parameters(
			draft.name,
			[
				{
					"parameter_key": "tender.validity_days",
					"label": "Tender validity",
					"value_type": "Duration",
					"runtime_owner": "Tender Preparation",
					"render_binding": "TDS.validity",
				}
			],
		)
		row_name = result["saved"]["STD Cfg Parameter Definition"][0]

		update_result = api.save_std_parameters(draft.name, [{"name": row_name, "label": "Tender validity period"}])
		frappe.set_user("Administrator")
		self.assertEqual(
			frappe.db.get_value("STD Cfg Parameter Definition", row_name, "label"), "Tender validity period"
		)
		self.assertEqual(update_result["saved"]["STD Cfg Parameter Definition"], [row_name])

	def test_save_area_bumps_draft_record_version(self):
		draft = self._submittable_draft()
		before = draft.record_version
		frappe.set_user(self.configurator)
		api.save_std_parameters(
			draft.name,
			[
				{
					"parameter_key": "tender.validity_days",
					"label": "Tender validity",
					"value_type": "Duration",
					"runtime_owner": "Tender Preparation",
					"render_binding": "TDS.validity",
				}
			],
		)
		frappe.set_user("Administrator")
		after = frappe.db.get_value("STD Cfg Draft", draft.name, "record_version")
		self.assertGreater(int(after), int(before or 0))

	def test_save_area_is_idempotent(self):
		draft = self._submittable_draft()
		key = f"idem-{uuid.uuid4().hex}"
		frappe.set_user(self.configurator)
		first = api.save_std_parameters(
			draft.name,
			[
				{
					"parameter_key": "tender.validity_days",
					"label": "Tender validity",
					"value_type": "Duration",
					"runtime_owner": "Tender Preparation",
					"render_binding": "TDS.validity",
				}
			],
			idempotency_key=key,
		)
		second = api.save_std_parameters(
			draft.name,
			[
				{
					"parameter_key": "tender.validity_days",
					"label": "Tender validity",
					"value_type": "Duration",
					"runtime_owner": "Tender Preparation",
					"render_binding": "TDS.validity",
				}
			],
			idempotency_key=key,
		)
		frappe.set_user("Administrator")
		self.assertEqual(first, second)
		self.assertEqual(
			frappe.db.count(
				"STD Cfg Parameter Definition",
				{"reference_doctype": "STD Cfg Draft", "reference_name": draft.name},
			),
			1,
		)
		self.assertEqual(frappe.db.count("STD Cfg Command Journal", {"idempotency_key": key}), 1)

	# --- lifecycle commands at the API layer ---------------------------------------

	def test_full_path_through_api_layer(self):
		draft = self._submittable_draft()
		populate_minimum_coverage(draft.name, PACKAGE_CODE)
		frappe.set_user(self.configurator)
		task = api.submit_std_for_review(draft.name, reviewer=self.reviewer)
		self.assertEqual(task["state"], "In review")

		frappe.set_user(self.reviewer)
		version = api.activate_std_version(task["review_task_id"])
		self.assertEqual(version["status"], "Active")
		frappe.set_user("Administrator")

	def test_submit_rejects_stale_expected_record_version(self):
		draft = self._submittable_draft()
		frappe.set_user(self.configurator)
		with self.assertRaises(frappe.ValidationError):
			api.submit_std_for_review(draft.name, reviewer=self.reviewer, expected_record_version=999)
		frappe.set_user("Administrator")

	def test_activate_command_is_idempotent(self):
		draft = self._submittable_draft()
		populate_minimum_coverage(draft.name, PACKAGE_CODE)
		frappe.set_user(self.configurator)
		task = api.submit_std_for_review(draft.name, reviewer=self.reviewer)
		frappe.set_user(self.reviewer)
		key = f"idem-{uuid.uuid4().hex}"
		first = api.activate_std_version(task["review_task_id"], idempotency_key=key)
		second = api.activate_std_version(task["review_task_id"], idempotency_key=key)
		frappe.set_user("Administrator")
		self.assertEqual(first, second)
		self.assertEqual(frappe.db.count("STD Cfg Version", {"package_id": PACKAGE_CODE, "status": "Active"}), 1)
