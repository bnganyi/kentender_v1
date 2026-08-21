# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-09 Budget Revision Review — apply/return/reject + AC-016/018."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_budget.seeds.budget_authorization_seed import (
	assign_budget_test_user,
	upsert_budget_authorization,
	upsert_budget_test_authorization,
)
from kentender_budget.services.budget_revision_contracts import (
	apply_budget_revision,
	create_budget_revision,
	get_budget_revision_review_context,
	list_budget_revisions,
	reject_budget_revision,
	return_budget_revision,
	review_budget_revision,
	submit_budget_revision,
)


class TestBudgetRevisionReview(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		upsert_budget_authorization()
		upsert_budget_test_authorization()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def setUp(self):
		# Isolate from Playwright leftovers / prior test floor mutations.
		line = frappe.db.get_value(
			"Budget Line", {"generated_reference": "MOH-BL-HWD-2027"}, "name"
		)
		if line:
			frappe.db.set_value(
				"Budget Line",
				line,
				{"amount_reserved": 0, "amount_committed": 0, "approved_amount": 80_000_000},
			)

	def _make_officer(self, email: str) -> str:
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Revision",
					"last_name": "Officer",
					"send_welcome_email": 0,
					"new_password": "Test@12345",
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Budget Officer")
		pe = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name")
		if pe and not frappe.db.exists(
			"User Permission", {"user": email, "allow": "Procuring Entity", "for_value": pe}
		):
			frappe.get_doc(
				{
					"doctype": "User Permission",
					"user": email,
					"allow": "Procuring Entity",
					"for_value": pe,
					"is_default": 1,
				}
			).insert(ignore_permissions=True)
		return email

	def _task_payload(self, code: str) -> dict:
		revision = frappe.db.get_value("Budget Revision", {"generated_reference": code}, "name")
		name = frappe.db.get_value("Workflow Task", {"subject_type": "Budget Revision", "subject_id": revision, "state": "Open"}, "name")
		task = frappe.get_doc("Workflow Task", name)
		return {"revision": code, "task_id": task.name, "concurrency_token": task.concurrency_token}

	def _create_and_submit_as(self, user: str, change: float = 3_000_000) -> str:
		assign_budget_test_user(user, "officer")
		frappe.set_user(user)
		try:
			saved = create_budget_revision(
				{
					"budget": "MOH-BUD-2027-2028",
					"external_approval_reference": "MOF/TEST/REV-APPLY",
					"approval_date": "2027-12-01",
					"effective_date": "2027-12-15",
					"reason": "Apply path uplift",
					"approval_evidence": "/private/files/rev-apply-test.pdf",
					"lines": [
						{"budget_line": "MOH-BL-HWD-2027", "change_amount": change},
					],
				}
			)
			self.assertTrue(saved.get("ok"), saved)
			code = saved["revision"]["code"]
			ok = submit_budget_revision({"revision": code})
			self.assertTrue(ok.get("ok"), ok)
			return code
		finally:
			frappe.set_user("Administrator")

	def test_list_includes_seeded_submitted(self):
		upsert_moh_mvp_v1_portfolio()
		dto = list_budget_revisions("MOH-BUD-2027-2028")
		by_code = {r["code"]: r for r in dto["rows"]}
		self.assertIn("BR-MOH-0002", by_code)
		seed = by_code["BR-MOH-0002"]
		self.assertEqual(seed["status"], "Submitted")
		self.assertEqual(seed["open_action"], "")
		self.assertEqual(seed["action_label"], "")
		self.assertEqual(seed["task_id"], "")
		self.assertEqual(seed["status_label"], "Pending Review")
		self.assertEqual(by_code["BR-MOH-0001"]["open_action"], "edit")
		self.assertEqual(by_code["BR-MOH-0001"]["action_label"], "Edit revision")

	def test_review_context_seeded_submitted(self):
		upsert_moh_mvp_v1_portfolio()
		ctx = get_budget_revision_review_context("BR-MOH-0002")
		self.assertEqual(ctx["revision"]["code"], "BR-MOH-0002")
		self.assertEqual(ctx["revision"]["status"], "Submitted")
		self.assertEqual(ctx["financial"]["additions_display"], "KES 5,000,000")
		self.assertFalse(ctx["blockers"])
		# Status and technical administration no longer imply task authority.
		self.assertFalse(ctx["capabilities"]["can_apply"])
		self.assertFalse(ctx["capabilities"]["can_return"])
		self.assertFalse(ctx["capabilities"]["can_reject"])
		self.assertEqual(ctx["capabilities"]["task_id"], "")
		alias = review_budget_revision("BR-MOH-0002")
		self.assertEqual(alias["revision"]["code"], "BR-MOH-0002")

	def test_return_requires_comment_then_resubmit(self):
		code = self._create_and_submit_as(
			self._make_officer("budget.rev.return@example.com"), change=2_000_000
		)
		missing = return_budget_revision({**self._task_payload(code), "comment": ""})
		self.assertFalse(missing.get("ok"))
		self.assertIn("comment", missing.get("errors") or {})

		ok = return_budget_revision({**self._task_payload(code), "comment": "Please attach clearer evidence."})
		self.assertTrue(ok.get("ok"), ok)
		self.assertEqual(ok["revision"]["status"], "Returned")

		officer = "budget.rev.return@example.com"
		frappe.set_user(officer)
		try:
			saved = create_budget_revision(
				{
					"budget": "MOH-BUD-2027-2028",
					"revision": code,
					"external_approval_reference": "MOF/TEST/REV-RETURNED",
					"approval_date": "2027-12-01",
					"effective_date": "2027-12-15",
					"reason": "Resubmit after return",
					"approval_evidence": "/private/files/rev-return-test.pdf",
					"lines": [
						{"budget_line": "MOH-BL-HWD-2027", "change_amount": 2_500_000},
					],
				}
			)
			self.assertTrue(saved.get("ok"), saved)
			again = submit_budget_revision({"revision": code})
			self.assertTrue(again.get("ok"), again)
			self.assertEqual(again["revision"]["status"], "Submitted")
		finally:
			frappe.set_user("Administrator")

	def test_reject_requires_comment(self):
		code = self._create_and_submit_as(
			self._make_officer("budget.rev.reject@example.com"), change=1_500_000
		)
		missing = reject_budget_revision(self._task_payload(code))
		self.assertFalse(missing.get("ok"))
		self.assertIn("comment", missing.get("errors") or {})
		ok = reject_budget_revision({**self._task_payload(code), "comment": "Out of policy."})
		self.assertTrue(ok.get("ok"), ok)
		self.assertEqual(ok["revision"]["status"], "Rejected")

	def test_ac018_submitter_cannot_apply(self):
		officer = self._make_officer("budget.rev.ac018@example.com")
		code = self._create_and_submit_as(officer, change=1_000_000)
		frappe.set_user(officer)
		try:
			with self.assertRaises(frappe.PermissionError):
				apply_budget_revision(self._task_payload(code))
		finally:
			frappe.set_user("Administrator")

		frappe.db.set_value(
			"Budget Revision",
			{"generated_reference": code},
			"submitted_by",
			"Administrator",
		)
		denied = apply_budget_revision(self._task_payload(code))
		self.assertFalse(denied.get("ok"))
		self.assertIn("status", denied.get("errors") or {})

	def test_apply_updates_line_atomically(self):
		officer = self._make_officer("budget.rev.apply@example.com")
		code = self._create_and_submit_as(officer, change=4_000_000)
		before = flt(
			frappe.db.get_value(
				"Budget Line",
				{"generated_reference": "MOH-BL-HWD-2027"},
				"approved_amount",
			)
		)
		ok = apply_budget_revision(self._task_payload(code))
		self.assertTrue(ok.get("ok"), ok)
		self.assertEqual(ok["revision"]["status"], "Applied")
		self.assertEqual(ok["revision"]["applied_by"], "Administrator")
		after = flt(
			frappe.db.get_value(
				"Budget Line",
				{"generated_reference": "MOH-BL-HWD-2027"},
				"approved_amount",
			)
		)
		self.assertEqual(after, before + 4_000_000)

	def test_ac016_blocker_disables_apply(self):
		officer = self._make_officer("budget.rev.floor@example.com")
		code = self._create_and_submit_as(officer, change=1_000_000)
		line_name = frappe.db.get_value(
			"Budget Line", {"generated_reference": "MOH-BL-HWD-2027"}, "name"
		)
		try:
			frappe.db.set_value("Budget Line", line_name, "amount_reserved", 90_000_000)
			ctx = get_budget_revision_review_context(code)
			self.assertTrue(ctx["blockers"])
			self.assertFalse(ctx["capabilities"]["can_apply"])
			denied = apply_budget_revision(self._task_payload(code))
			self.assertFalse(denied.get("ok"))
			self.assertIn("blockers", denied.get("errors") or {})
		finally:
			frappe.db.set_value("Budget Line", line_name, "amount_reserved", 0)
