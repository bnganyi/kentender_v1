# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 4 — roles and permissions.

Covers: role seed idempotency; an unassigned user denied; Administrator-with-no-
role denied (no fallback); a correctly-assigned actor pair completing the full
submit→activate path; and the maker-checker rule blocking a single actor who
holds both roles from activating their own submission.
"""

from __future__ import annotations

import uuid

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.std_configuration.services import std_authorization, std_lifecycle
from kentender_procurement.std_configuration.tests.std_test_fixtures import populate_minimum_coverage

PACKAGE_CODE = "KE-TEST-STD-P4"


class TestSTDChg001Phase4Governance(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.suffix = uuid.uuid4().hex[:8]
		self._users: list[str] = []
		self._cleanup()
		std_authorization.ensure_std_configuration_governance_roles()
		self.package = frappe.get_doc(
			{
				"doctype": "STD Cfg Package",
				"package_code": PACKAGE_CODE,
				"official_title": "Test Package for Phase 4",
				"requirement_profile": "Information Technology",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		self._cleanup()
		for email in self._users:
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		# See Phase 3's identical comment: without this explicit commit, a User
		# created and deleted within the same uncommitted transaction leaks past
		# FrappeTestCase's class-cleanup rollback instead of being discarded.
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

	def _user(self, label: str, role: str | None = None) -> str:
		email = f"std.p4.{label}.{self.suffix}@example.test"
		doc = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		)
		if role:
			doc.append("roles", {"role": role})
		doc.insert(ignore_permissions=True)
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

	def test_role_seed_is_idempotent(self):
		first = std_authorization.ensure_std_configuration_governance_roles()
		second = std_authorization.ensure_std_configuration_governance_roles()
		self.assertEqual(second["roles"], [])
		self.assertTrue(frappe.db.exists("Role", "STD Configurator"))
		self.assertTrue(frappe.db.exists("Role", "STD Reviewer"))

	def test_unassigned_user_denied(self):
		nobody = self._user("nobody")
		with self.assertRaises(frappe.PermissionError):
			std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=nobody)

	def test_administrator_with_no_role_denied(self):
		# §12 "fail closed when missing or ambiguous" — no System Manager/
		# Administrator fallback, matching Strategy's own §16.2 no-fallback rule.
		with self.assertRaises(frappe.PermissionError):
			std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor="Administrator")

	def _submittable_draft(self, actor: str):
		draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=actor)
		src = self._make_source("STD Cfg Draft", draft.name)
		draft.official_source_file_id = src.name
		draft.save(ignore_permissions=True)
		# §6.1 step 7 — submit_for_review now runs the real complete check
		# (Phase 6); every coverage area needs real minimal content.
		populate_minimum_coverage(draft.name, PACKAGE_CODE)
		return draft

	def test_correct_actor_pair_completes_full_path(self):
		configurator = self._user("configurator", "STD Configurator")
		reviewer = self._user("reviewer", "STD Reviewer")

		draft = self._submittable_draft(configurator)
		task = std_lifecycle.submit_for_review(draft.name, reviewer=reviewer, actor=configurator)
		version = std_lifecycle.activate_package(task.name, actor=reviewer)
		self.assertEqual(version.status, "Active")

	def test_reviewer_cannot_submit(self):
		reviewer_only = self._user("reviewer-only", "STD Reviewer")
		with self.assertRaises(frappe.PermissionError):
			std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=reviewer_only)

	def test_maker_checker_blocks_same_actor_even_with_both_roles(self):
		double_hat = self._user("double-hat", "STD Configurator")
		frappe.get_doc("User", double_hat).append("roles", {"role": "STD Reviewer"}).save(
			ignore_permissions=True
		)

		draft = self._submittable_draft(double_hat)
		task = std_lifecycle.submit_for_review(draft.name, reviewer=double_hat, actor=double_hat)
		with self.assertRaises(frappe.PermissionError):
			std_lifecycle.activate_package(task.name, actor=double_hat)

	def test_different_reviewer_can_activate_after_double_hat_submission(self):
		# Confirms the block above is the SoD pairing, not a blanket role conflict.
		submitter = self._user("submitter", "STD Configurator")
		other_reviewer = self._user("other-reviewer", "STD Reviewer")

		draft = self._submittable_draft(submitter)
		task = std_lifecycle.submit_for_review(draft.name, reviewer=other_reviewer, actor=submitter)
		version = std_lifecycle.activate_package(task.name, actor=other_reviewer)
		self.assertEqual(version.status, "Active")
