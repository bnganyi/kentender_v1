# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 7 — all seven §10 runtime manifests, generated on
activation.

Covers: Tender Configuration's real manifest items (deterministic, correctly
step-tagged); the six shared-DocType manifests (Requirement Composer, Bidder
Response, Evaluation, Contract Formation, Contract Management, Render), each
real-generated, schema-validated, and digest-stable; `GetRuntimeManifest`
returning real data post-activation; and the one part of §11.3's atomicity
claim provable in a non-HTTP test context — an induced failure on the LAST
manifest generated (Render) leaves no Version and no manifest row of any kind
once rolled back, confirming all seven manifests plus Version creation and
content reassignment share one uncommitted transaction.
"""

from __future__ import annotations

import uuid
from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.std_configuration.api import std_configuration_api as api
from kentender_procurement.std_configuration.services import std_authorization, std_lifecycle
from kentender_procurement.std_configuration.tests.std_test_fixtures import populate_minimum_coverage

PACKAGE_CODE = "KE-TEST-STD-P7"


class TestSTDChg001Phase7ManifestGeneration(FrappeTestCase):
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
				"official_title": "Test Package for Phase 7",
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
		frappe.db.delete("STD Cfg Tender Manifest", {"package_code": PACKAGE_CODE})
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
		email = f"std.p7.{label}.{self.suffix}@example.test"
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

	def _activated_version(self):
		draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)
		src = self._make_source("STD Cfg Draft", draft.name)
		draft.official_source_file_id = src.name
		draft.save(ignore_permissions=True)
		populate_minimum_coverage(draft.name, PACKAGE_CODE)
		task = std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)
		return std_lifecycle.activate_package(task.name, actor=self.reviewer)

	# --- generation --------------------------------------------------------------

	def test_activation_generates_real_manifest_items(self):
		version = self._activated_version()
		manifest = frappe.get_doc("STD Cfg Tender Manifest", {"std_version_id": version.name})
		self.assertEqual(manifest.manifest_type, "Tender Configuration")
		self.assertGreater(len(manifest.items), 0)
		steps = {item.step_id for item in manifest.items}
		self.assertTrue(steps.issubset({f"CFG-{n:02d}" for n in range(2, 10)}))
		# The fixture helper populates exactly one row per relevant PCFG
		# doctype, so exactly one manifest item per step it touches.
		self.assertEqual(
			steps,
			{"CFG-02", "CFG-03", "CFG-04", "CFG-05", "CFG-06", "CFG-07", "CFG-08", "CFG-09"},
		)

	def test_manifest_item_keys_are_stable_and_traceable(self):
		version = self._activated_version()
		manifest = frappe.get_doc("STD Cfg Tender Manifest", {"std_version_id": version.name})
		param_item = next(i for i in manifest.items if i.step_id == "CFG-02")
		source_param = frappe.get_all(
			"STD Cfg Parameter Definition",
			filters={"reference_doctype": "STD Cfg Version", "reference_name": version.name},
			fields=["parameter_key", "label"],
			limit_page_length=1,
		)[0]
		self.assertEqual(param_item.item_key, source_param.parameter_key)
		self.assertEqual(param_item.label, source_param.label)

	def test_get_runtime_manifest_returns_real_data_after_activation(self):
		version = self._activated_version()
		result = api.get_runtime_manifest(version.name)
		self.assertIsNotNone(result["manifest"])
		self.assertGreater(len(result["manifest"]["items"]), 0)

	# --- the six shared-DocType manifests ------------------------------------------

	def test_all_six_shared_manifests_are_generated(self):
		version = self._activated_version()
		rows = frappe.get_all(
			"STD Cfg Runtime Manifest",
			filters={"std_version_id": version.name},
			fields=["manifest_type", "status", "content_digest", "payload"],
		)
		types = {r.manifest_type for r in rows}
		self.assertEqual(
			types,
			{"Requirement Composer", "Bidder Response", "Evaluation", "Contract Formation", "Contract Management", "Render"},
		)
		for row in rows:
			self.assertEqual(row.status, "Generated")
			self.assertTrue(row.content_digest)
			self.assertTrue(frappe.parse_json(row.payload))

	def test_requirement_composer_payload_has_real_content(self):
		version = self._activated_version()
		row = frappe.get_doc("STD Cfg Runtime Manifest", {"std_version_id": version.name, "manifest_type": "Requirement Composer"})
		payload = frappe.parse_json(row.payload)
		self.assertEqual(len(payload["categories"]), 1)
		self.assertEqual(payload["categories"][0]["category"], "Functional")
		self.assertEqual(len(payload["schedule"]), 1)

	def test_evaluation_payload_lists_four_fixed_stages(self):
		version = self._activated_version()
		row = frappe.get_doc("STD Cfg Runtime Manifest", {"std_version_id": version.name, "manifest_type": "Evaluation"})
		payload = frappe.parse_json(row.payload)
		self.assertEqual(
			payload["stages"],
			["Preliminary responsiveness", "Technical evaluation", "Financial evaluation", "Post-qualification"],
		)
		self.assertEqual(len(payload["criteria"]), 1)

	def test_render_payload_reflects_package_sections(self):
		version = self._activated_version()
		row = frappe.get_doc("STD Cfg Runtime Manifest", {"std_version_id": version.name, "manifest_type": "Render"})
		payload = frappe.parse_json(row.payload)
		self.assertEqual(len(payload["sections"]), 3)
		self.assertTrue(all(section["blocks"] for section in payload["sections"]))

	def test_digest_is_deterministic_across_reruns_of_the_same_content(self):
		from kentender_procurement.std_configuration.services.std_runtime_manifest import (
			_build_evaluation,
			compute_digest,
		)

		version = self._activated_version()
		payload_first = _build_evaluation(version.name)
		payload_second = _build_evaluation(version.name)
		self.assertEqual(compute_digest(payload_first), compute_digest(payload_second))

	def test_validator_rejects_malformed_payload(self):
		from kentender_procurement.std_configuration.services.std_runtime_manifest import _VALIDATORS

		with self.assertRaises(frappe.ValidationError):
			_VALIDATORS["Evaluation"]({"stages": []})  # missing "criteria" key
		with self.assertRaises(frappe.ValidationError):
			_VALIDATORS["Render"]({"sections": "not-a-list"})

	def test_runtime_manifest_unique_per_version_and_type(self):
		version = self._activated_version()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "STD Cfg Runtime Manifest",
					"manifest_type": "Render",
					"std_version_id": version.name,
					"schema_version": "1",
					"status": "Generated",
					"generated_at": frappe.utils.now_datetime(),
					"content_digest": "dupe",
					"payload": "{}",
				}
			).insert(ignore_permissions=True)

	# --- atomicity ----------------------------------------------------------------

	def test_activation_failure_leaves_no_version_row(self):
		draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)
		src = self._make_source("STD Cfg Draft", draft.name)
		draft.official_source_file_id = src.name
		draft.save(ignore_permissions=True)
		populate_minimum_coverage(draft.name, PACKAGE_CODE)
		task = std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)

		# Real HTTP requests get an automatic rollback-on-exception at the
		# request boundary (AGENTS.md §4.4); this test isn't a real request, so
		# it draws that same boundary explicitly with a savepoint scoped to
		# just the activation attempt — NOT `frappe.db.rollback()` bare, which
		# would also discard this test's own setUp (Package/Draft/Task, never
		# committed either, per FrappeTestCase's own per-class transaction).
		# Failure induced on Render — the LAST of the seven manifests generated
		# (Tender Configuration + 5 of the 6 shared-DocType manifests run first)
		# — the strongest available proof: if Render failing still leaves zero
		# Version/manifest rows, everything generated before it in this same
		# call was rolled back too, not just "failing first aborts everything."
		# Baseline of pre-existing Runtime Manifest rows (e.g. the real golden
		# `KE-PPRA-IT` fixture, Phase 9) — the post-rollback assertion below
		# checks no NEW rows appeared, not that the table is globally empty.
		baseline_manifest_names = set(frappe.get_all("STD Cfg Runtime Manifest", pluck="name"))

		savepoint_name = "std_p7_activation_failure"
		frappe.db.savepoint(savepoint_name)
		with mock.patch.dict(
			"kentender_procurement.std_configuration.services.std_runtime_manifest._BUILDERS",
			{"Render": mock.Mock(side_effect=RuntimeError("induced failure for atomicity proof"))},
		):
			with self.assertRaises(RuntimeError):
				std_lifecycle.activate_package(task.name, actor=self.reviewer)
		frappe.db.rollback(save_point=savepoint_name)

		self.assertFalse(frappe.db.exists("STD Cfg Version", {"package_id": PACKAGE_CODE}))
		self.assertFalse(frappe.db.exists("STD Cfg Tender Manifest", {"package_code": PACKAGE_CODE}))
		self.assertEqual(
			baseline_manifest_names, set(frappe.get_all("STD Cfg Runtime Manifest", pluck="name"))
		)
		self.package.reload()
		self.assertFalse(self.package.current_active_version_id)
