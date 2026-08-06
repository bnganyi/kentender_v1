# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-SUP-001A — Budget / revision workflow Notification Log."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_notification_service import (
	EVENT_BUDGET_ACTIVATED,
	EVENT_BUDGET_RETURNED,
	EVENT_BUDGET_REVIEWED,
	EVENT_BUDGET_SUBMITTED,
	EVENT_REVISION_APPLIED,
	EVENT_REVISION_REJECTED,
	EVENT_REVISION_RETURNED,
	EVENT_REVISION_SUBMITTED,
	notify_budget_users,
)
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_budget.services.budget_readiness_contracts import (
	activate_budget,
	mark_budget_reviewed,
	return_budget,
	submit_budget,
)
from kentender_budget.services.budget_revision_contracts import (
	apply_budget_revision,
	create_budget_revision,
	reject_budget_revision,
	return_budget_revision,
	submit_budget_revision,
)


class TestBudgetNotifications(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()
		cls.reviewer = cls._ensure_user(
			"budget.notify.reviewer@example.com", "Budget Reviewer"
		)
		cls.authority = cls._ensure_user(
			"budget.notify.authority@example.com", "Budget Authority"
		)
		cls.officer = cls._ensure_user(
			"budget.notify.officer@example.com", "Budget Officer"
		)

	@staticmethod
	def _ensure_user(email: str, *roles: str) -> str:
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Notify",
					"last_name": email.split("@")[0],
					"send_welcome_email": 0,
					"new_password": "Test@12345",
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles(*roles)
		else:
			user = frappe.get_doc("User", email)
			user.add_roles(*roles)
		pe = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name")
		if pe and not frappe.db.exists(
			"User Permission",
			{"user": email, "allow": "Procuring Entity", "for_value": pe},
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

	def setUp(self):
		upsert_moh_mvp_v1_portfolio()
		for name in frappe.get_all(
			"Notification Log",
			filters={"email_header": ["like", "kt-budget:%"]},
			pluck="name",
		):
			frappe.delete_doc(
				"Notification Log", name, force=True, ignore_permissions=True
			)

	def _count_event(self, event_type: str, for_user: str | None = None) -> int:
		filters = {"email_header": ["like", f"kt-budget:{event_type}:%"]}
		if for_user:
			filters["for_user"] = for_user
		return frappe.db.count("Notification Log", filters)

	def _prepare_draft_0004(self):
		doc = frappe.get_doc("Budget", {"generated_reference": "MOH-BUD-0004"})
		doc.approval_evidence = "/private/files/moh-bud-0004-notify.pdf"
		doc.save(ignore_permissions=True)
		for ln in frappe.get_all(
			"Budget Line", filters={"budget": doc.name}, pluck="name"
		):
			line = frappe.get_doc("Budget Line", ln)
			if not (line.primary_target_code or "").strip():
				line.primary_target_code = "MOH-TGT-SKILLS-2029"
				line.primary_target_name = "Digital health technical capability target"
				line.primary_strategy_linked = 1
			if not line.get("value_treatments"):
				line.append(
					"value_treatments",
					{
						"pvc_code": "MOH-PVC-EFT-01",
						"pvc_name": "Improve infrastructure efficiency",
						"requirement_level": "Required",
						"treatment": "Embedded in line",
						"dedicated_amount": 0,
						"rationale": "Included in line delivery.",
					},
				)
			line.save(ignore_permissions=True)
		return doc

	def test_submit_notifies_reviewer_and_authority(self):
		self._prepare_draft_0004()
		frappe.set_user(self.officer)
		try:
			ok = submit_budget({"budget": "MOH-BUD-0004"})
			self.assertTrue(ok.get("ok"), ok)
		finally:
			frappe.set_user("Administrator")
		self.assertGreaterEqual(
			self._count_event(EVENT_BUDGET_SUBMITTED, self.reviewer), 1
		)
		self.assertGreaterEqual(
			self._count_event(EVENT_BUDGET_SUBMITTED, self.authority), 1
		)

	def test_return_reviewed_activate_notify(self):
		name = frappe.db.get_value(
			"Budget", {"generated_reference": "MOH-BUD-0002"}, "name"
		)
		frappe.db.set_value(
			"Budget",
			name,
			{
				"submitted_by": self.officer,
				"reviewed_by": None,
				"reviewed_at": None,
				"status": "Submitted",
			},
		)
		returned = return_budget(
			{"budget": "MOH-BUD-0002", "comment": "Fix evidence attachment."}
		)
		self.assertTrue(returned.get("ok"), returned)
		self.assertGreaterEqual(
			self._count_event(EVENT_BUDGET_RETURNED, self.officer), 1
		)

		# Restore Submitted for review/activate path.
		upsert_moh_mvp_v1_portfolio()
		name = frappe.db.get_value(
			"Budget", {"generated_reference": "MOH-BUD-0002"}, "name"
		)
		frappe.db.set_value(
			"Budget",
			name,
			{
				"submitted_by": self.officer,
				"reviewed_by": None,
				"reviewed_at": None,
				"status": "Submitted",
			},
		)
		marked = mark_budget_reviewed({"budget": "MOH-BUD-0002"})
		self.assertTrue(marked.get("ok"), marked)
		self.assertGreaterEqual(
			self._count_event(EVENT_BUDGET_REVIEWED, self.authority), 1
		)

		activated = activate_budget({"budget": "MOH-BUD-0002"})
		self.assertTrue(activated.get("ok"), activated)
		self.assertGreaterEqual(
			self._count_event(EVENT_BUDGET_ACTIVATED, self.officer), 1
		)

	def test_revision_lifecycle_notifies_submitter(self):
		frappe.set_user(self.officer)
		try:
			saved = create_budget_revision(
				{
					"budget": "MOH-BUD-2027-2028",
					"external_approval_reference": "MOF/NOTIFY/REV",
					"approval_date": "2027-12-01",
					"effective_date": "2027-12-15",
					"reason": "Notify path uplift",
					"approval_evidence": "/private/files/rev-notify.pdf",
					"lines": [
						{"budget_line": "MOH-BL-HWD-2027", "change_amount": 2_000_000},
					],
				}
			)
			self.assertTrue(saved.get("ok"), saved)
			code = saved["revision"]["code"]
			ok = submit_budget_revision({"revision": code})
			self.assertTrue(ok.get("ok"), ok)
		finally:
			frappe.set_user("Administrator")

		self.assertGreaterEqual(
			self._count_event(EVENT_REVISION_SUBMITTED, self.reviewer), 1
		)

		returned = return_budget_revision(
			{"revision": code, "comment": "Clarify reason text."}
		)
		self.assertTrue(returned.get("ok"), returned)
		self.assertGreaterEqual(
			self._count_event(EVENT_REVISION_RETURNED, self.officer), 1
		)

		# Fresh revision for reject
		frappe.set_user(self.officer)
		try:
			saved = create_budget_revision(
				{
					"budget": "MOH-BUD-2027-2028",
					"external_approval_reference": "MOF/NOTIFY/REV-RJ",
					"approval_date": "2027-12-01",
					"effective_date": "2027-12-15",
					"reason": "Reject notify path",
					"approval_evidence": "/private/files/rev-notify-rj.pdf",
					"lines": [
						{"budget_line": "MOH-BL-HWD-2027", "change_amount": 1_500_000},
					],
				}
			)
			code2 = saved["revision"]["code"]
			submit_budget_revision({"revision": code2})
		finally:
			frappe.set_user("Administrator")

		rejected = reject_budget_revision(
			{"revision": code2, "comment": "Out of policy for notify test."}
		)
		self.assertTrue(rejected.get("ok"), rejected)
		self.assertGreaterEqual(
			self._count_event(EVENT_REVISION_REJECTED, self.officer), 1
		)

		# Apply path
		frappe.set_user(self.officer)
		try:
			saved = create_budget_revision(
				{
					"budget": "MOH-BUD-2027-2028",
					"external_approval_reference": "MOF/NOTIFY/REV-AP",
					"approval_date": "2027-12-01",
					"effective_date": "2027-12-15",
					"reason": "Apply notify path",
					"approval_evidence": "/private/files/rev-notify-ap.pdf",
					"lines": [
						{"budget_line": "MOH-BL-HWD-2027", "change_amount": 1_000_000},
					],
				}
			)
			code3 = saved["revision"]["code"]
			submit_budget_revision({"revision": code3})
		finally:
			frappe.set_user("Administrator")

		applied = apply_budget_revision({"revision": code3})
		self.assertTrue(applied.get("ok"), applied)
		self.assertGreaterEqual(
			self._count_event(EVENT_REVISION_APPLIED, self.officer), 1
		)

	def test_notify_idempotent_and_failure_does_not_break_api(self):
		doc = frappe.get_doc("Budget", {"generated_reference": "MOH-BUD-2027-2028"})
		first = notify_budget_users(
			EVENT_BUDGET_SUBMITTED,
			budget_doc=doc,
			correlation_suffix="idem-token-1",
		)
		second = notify_budget_users(
			EVENT_BUDGET_SUBMITTED,
			budget_doc=doc,
			correlation_suffix="idem-token-1",
		)
		self.assertTrue(any(first))
		self.assertEqual(
			[x for x in first if x],
			[x for x in second if x],
		)
		self.assertEqual(
			frappe.db.count(
				"Notification Log",
				{"email_header": ["like", "kt-budget:budget_submitted:%idem-token-1%"]},
			),
			len([x for x in first if x]),
		)

		upsert_moh_mvp_v1_portfolio()
		name = frappe.db.get_value(
			"Budget", {"generated_reference": "MOH-BUD-0002"}, "name"
		)
		frappe.db.set_value(
			"Budget",
			name,
			{
				"submitted_by": self.officer,
				"reviewed_by": None,
				"reviewed_at": None,
				"status": "Submitted",
			},
		)
		with patch(
			"kentender_budget.services.budget_notification_service.emit_notification_log",
			side_effect=RuntimeError("boom"),
		):
			res = return_budget(
				{"budget": "MOH-BUD-0002", "comment": "Notify failure must not reverse."}
			)
		self.assertTrue(res.get("ok"), res)
