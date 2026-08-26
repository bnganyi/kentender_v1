# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 3 — §12 lifecycle engine.

Covers the full transition table (submit/return/resubmit/activate), atomic
activation (content reassignment + supersession + package pointers), content
cloning on `create_next_draft`, snapshot-staleness rejection, and the specific
"can a package get a second Draft after its first activation" scenario that
Phase 3 found broken in Phase 1's original guard.

Uses real Configurator/Reviewer test users throughout (not "Administrator") —
Phase 4 added capability gating on top of every function tested here, and
Administrator is deliberately denied (§12, no fallback). See Phase 4's own test
module for the authorization behaviour itself; this module exercises the
*lifecycle* rules, with authorization satisfied but out of focus.
"""

from __future__ import annotations

import uuid

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.std_configuration.services import std_authorization, std_lifecycle
from kentender_procurement.std_configuration.tests.std_test_fixtures import populate_minimum_coverage

PACKAGE_CODE = "KE-TEST-STD-P3"


class TestSTDChg001Phase3Lifecycle(FrappeTestCase):
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
				"official_title": "Test Package for Phase 3",
				"requirement_profile": "Information Technology",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		self._cleanup()
		for email in self._users:
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		# FrappeTestCase rolls back anything left uncommitted at class-cleanup
		# time (`_rollback_db`); without this explicit commit, a User created and
		# deleted within the same uncommitted transaction was observed to leak
		# past that rollback rather than being cleanly discarded — confirmed live
		# by isolating a single test run and checking residue immediately after.
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
		email = f"std.p3.{label}.{self.suffix}@example.test"
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
		# §6.1 step 7 — submit_for_review now runs the real complete check
		# (Phase 6), so every coverage area needs real minimal content, not just
		# an official source, or submission is correctly refused.
		populate_minimum_coverage(draft.name, PACKAGE_CODE)
		return draft

	# --- submit / return / resubmit / activate --------------------------------

	def test_submit_requires_official_source(self):
		draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)
		with self.assertRaises(frappe.ValidationError):
			std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)

	def test_full_happy_path_submit_activate(self):
		draft = self._submittable_draft()
		task = std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)
		draft.reload()
		self.assertEqual(draft.state, "In review")
		self.assertEqual(task.snapshot_record_version, draft.record_version)

		version = std_lifecycle.activate_package(task.name, actor=self.reviewer)
		self.assertEqual(version.status, "Active")
		self.assertEqual(version.version_number, 1)

		self.package.reload()
		self.assertEqual(self.package.current_active_version_id, version.name)
		self.assertFalse(self.package.current_draft_id)

		task.reload()
		self.assertEqual(task.status, "Decided")

	def test_return_then_resubmit_then_activate(self):
		draft = self._submittable_draft()
		task = std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)

		decision = std_lifecycle.return_for_correction(
			task.name,
			"Fix the bidder response mapping for Security requirements.",
			actor=self.reviewer,
		)
		self.assertEqual(decision.decision, "Return for correction")
		draft.reload()
		self.assertEqual(draft.state, "Returned")

		task2 = std_lifecycle.resubmit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)
		draft.reload()
		self.assertEqual(draft.state, "In review")

		version = std_lifecycle.activate_package(task2.name, actor=self.reviewer)
		self.assertEqual(version.status, "Active")

	def test_cannot_activate_draft_not_in_review(self):
		self._submittable_draft()
		with self.assertRaises(frappe.DoesNotExistError):
			# No review task exists yet — draft is still "Draft".
			std_lifecycle.activate_package("nonexistent-task", actor=self.reviewer)

	def test_cannot_return_or_activate_against_stale_snapshot(self):
		draft = self._submittable_draft()
		task = std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)
		# Simulate the Draft moving after submission (defense-in-depth path —
		# no area-save command exists yet to do this through the front door).
		frappe.db.set_value("STD Cfg Draft", draft.name, "record_version", 999)
		with self.assertRaises(frappe.ValidationError):
			std_lifecycle.activate_package(task.name, actor=self.reviewer)
		with self.assertRaises(frappe.ValidationError):
			std_lifecycle.return_for_correction(task.name, "some correction", actor=self.reviewer)

	# --- the bug Phase 3 found and fixed in Phase 1's guard --------------------

	def test_new_draft_allowed_after_activation(self):
		draft = self._submittable_draft()
		task = std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)
		std_lifecycle.activate_package(task.name, actor=self.reviewer)

		# Would have raised under the old STD Cfg Draft.state-based guard, since
		# the activated draft's state ("In review") never leaves the query.
		second_draft = std_lifecycle.create_draft(
			PACKAGE_CODE, "April 2021 edition", actor=self.configurator
		)
		self.assertTrue(second_draft.name)

	# --- create_next_draft content cloning -------------------------------------

	def test_create_next_draft_clones_content_from_active_version(self):
		draft = self._submittable_draft()
		frappe.get_doc(
			{
				"doctype": "STD Cfg Parameter Definition",
				"reference_doctype": "STD Cfg Draft",
				"reference_name": draft.name,
				"parameter_key": "tender.validity_days",
				"label": "Tender validity",
				"value_type": "Duration",
				"runtime_owner": "Tender Preparation",
				"render_binding": "TDS.validity",
			}
		).insert(ignore_permissions=True)

		task = std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)
		version = std_lifecycle.activate_package(task.name, actor=self.reviewer)

		# Activation reassigns (not duplicates) content onto the Version — check
		# this specific fixture row by key, not a raw count (the coverage fixture
		# helper adds its own separate Parameter Definition too).
		self.assertTrue(
			frappe.db.exists(
				"STD Cfg Parameter Definition",
				{
					"reference_doctype": "STD Cfg Version",
					"reference_name": version.name,
					"parameter_key": "tender.validity_days",
				},
			)
		)
		self.assertFalse(
			frappe.db.exists(
				"STD Cfg Parameter Definition",
				{
					"reference_doctype": "STD Cfg Draft",
					"reference_name": draft.name,
					"parameter_key": "tender.validity_days",
				},
			)
		)

		next_draft = std_lifecycle.create_next_draft(
			PACKAGE_CODE, "June 2028 revision", actor=self.configurator
		)
		self.assertEqual(next_draft.based_on_version_id, version.name)
		self.assertEqual(next_draft.proposed_version_number, 2)

		cloned = frappe.get_all(
			"STD Cfg Parameter Definition",
			filters={
				"reference_doctype": "STD Cfg Draft",
				"reference_name": next_draft.name,
				"parameter_key": "tender.validity_days",
			},
			fields=["parameter_key", "name"],
		)
		self.assertEqual(len(cloned), 1)
		self.assertEqual(cloned[0].parameter_key, "tender.validity_days")

	def test_create_next_draft_requires_active_version(self):
		with self.assertRaises(frappe.ValidationError):
			std_lifecycle.create_next_draft(PACKAGE_CODE, "June 2028 revision", actor=self.configurator)

	# --- available_actions -------------------------------------------------------

	def test_available_actions_by_state(self):
		draft = self._submittable_draft()
		self.assertEqual(
			set(std_lifecycle.available_actions(draft)),
			{"save_area", "run_complete_check", "submit_for_review"},
		)
		std_lifecycle.submit_for_review(draft.name, reviewer=self.reviewer, actor=self.configurator)
		draft.reload()
		self.assertEqual(
			set(std_lifecycle.available_actions(draft)), {"return_for_correction", "activate_package"}
		)
