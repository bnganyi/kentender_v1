# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-11 Readiness and Review — submit/return/mark/activate + AC-018."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_budget.services.budget_readiness_contracts import (
	activate_budget,
	get_budget_readiness,
	mark_budget_reviewed,
	return_budget,
	submit_budget,
)


class TestBudgetReadiness(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def setUp(self):
		# Keep Draft/Submitted seeds stable across mutation tests.
		upsert_moh_mvp_v1_portfolio()

	def _ensure_user(self, email: str, *roles: str) -> str:
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Budget",
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

	def test_draft_seed_has_grouped_blockers(self):
		dto = get_budget_readiness("MOH-BUD-0004")
		self.assertEqual(dto["budget"]["code"], "MOH-BUD-0004")
		self.assertEqual(dto["budget"]["status"], "Draft")
		self.assertEqual(dto["budget"]["status_label"], "Draft State")
		self.assertGreaterEqual(dto["blocker_count"], 1)
		keys = {g["key"] for g in dto["groups"]}
		self.assertEqual(keys, {"source", "lines", "strategy", "governance"})
		source = next(g for g in dto["groups"] if g["key"] == "source")
		self.assertEqual(source["status"], "issue")
		self.assertTrue(
			any("evidence" in (i["message"] or "").lower() for i in source["issues"])
		)
		self.assertFalse(dto["capabilities"]["can_submit"])
		self.assertTrue(dto["capabilities"]["can_run_check"])

	def test_submit_blocked_when_blockers(self):
		res = submit_budget({"budget": "MOH-BUD-0004"})
		self.assertFalse(res.get("ok"))
		self.assertIn("blockers", res.get("errors") or {})

	def test_active_shows_activation_record_no_activate(self):
		dto = get_budget_readiness("MOH-BUD-0001")
		self.assertEqual(dto["budget"]["status"], "Active")
		self.assertTrue(dto["capabilities"]["show_activation_record"])
		self.assertFalse(dto["capabilities"]["can_activate"])
		self.assertFalse(dto["capabilities"]["can_submit"])
		self.assertEqual(dto["capabilities"]["primary_action"], "request_revision")
		self.assertEqual(dto["capabilities"]["primary_label"], "Request revision")
		self.assertTrue(dto["governance"]["activated_by"])
		self.assertTrue(dto["governance"]["activated_at"])

	def test_submitted_seed_ready_for_review_path(self):
		dto = get_budget_readiness("MOH-BUD-0002")
		self.assertEqual(dto["budget"]["status"], "Submitted")
		self.assertEqual(dto["blocker_count"], 0)
		self.assertTrue(dto["capabilities"]["can_return"])
		self.assertTrue(dto["capabilities"]["can_mark_reviewed"])
		self.assertFalse(dto["capabilities"]["can_activate"])  # not yet reviewed

	def test_return_requires_reason(self):
		res = return_budget({"budget": "MOH-BUD-0002", "comment": ""})
		self.assertFalse(res.get("ok"))
		self.assertIn("comment", res.get("errors") or {})

	def test_return_mark_activate_happy_path(self):
		# Return then restore via reseed path is heavy — use a clean Submitted cycle on 0004 after fixing.
		# Prefer 0002: mark reviewed → activate (Admin ≠ seeded submitter).
		name = frappe.db.get_value("Budget", {"generated_reference": "MOH-BUD-0002"}, "name")
		frappe.db.set_value(
			"Budget",
			name,
			{
				"submitted_by": "budget.rev.seed@example.com",
				"reviewed_by": None,
				"reviewed_at": None,
			},
		)
		marked = mark_budget_reviewed({"budget": "MOH-BUD-0002"})
		self.assertTrue(marked.get("ok"), marked)
		self.assertTrue(marked["readiness"]["governance"]["reviewed_by"])
		self.assertEqual(marked["readiness"]["budget"]["status"], "Submitted")
		self.assertTrue(marked["readiness"]["capabilities"]["can_activate"])

		activated = activate_budget({"budget": "MOH-BUD-0002"})
		self.assertTrue(activated.get("ok"), activated)
		self.assertEqual(activated["readiness"]["budget"]["status"], "Active")
		self.assertTrue(activated["readiness"]["capabilities"]["show_activation_record"])

	def test_ac018_submitter_cannot_activate(self):
		officer = self._ensure_user("budget.readiness.submitter@example.com", "Budget Officer")
		# Build a clean Submitted budget owned by officer as submitter.
		upsert_moh_mvp_v1_portfolio()
		# Use ephemeral budget via copy of 0002 fields — mutate 0004 to complete then submit as officer.
		doc = frappe.get_doc("Budget", {"generated_reference": "MOH-BUD-0004"})
		doc.approval_evidence = "/private/files/moh-bud-0004-fixed.pdf"
		doc.save(ignore_permissions=True)
		# Fix line primary + treatments so readiness passes.
		for ln in frappe.get_all(
			"Budget Line", filters={"budget": doc.name}, pluck="name"
		):
			line = frappe.get_doc("Budget Line", ln)
			if not (line.primary_target_code or "").strip():
				line.primary_target_code = "MOH-TGT-0003"
				line.primary_target_name = "Digital health technical capability target"
				line.primary_strategy_linked = 1
			if not line.get("value_treatments"):
				line.append(
					"value_treatments",
					{
						"pvc_code": "PVO-EFT-01",
						"pvc_name": "Improve infrastructure efficiency",
						"requirement_level": "Required",
						"treatment": "Embedded in line",
						"dedicated_amount": 0,
						"rationale": "Included in line delivery.",
						"reviewer_accepted": 0,
					},
				)
			line.save(ignore_permissions=True)

		frappe.set_user(officer)
		try:
			ok = submit_budget({"budget": "MOH-BUD-0004"})
			self.assertTrue(ok.get("ok"), ok)
			# Officer cannot mark reviewed — switch to Admin for mark, then back to officer for activate.
		finally:
			frappe.set_user("Administrator")

		mark_budget_reviewed({"budget": "MOH-BUD-0004"})
		frappe.set_user(officer)
		try:
			# Officer is not Authority — expect permission or ok:false.
			try:
				res = activate_budget({"budget": "MOH-BUD-0004"})
				self.assertFalse(res.get("ok"))
				self.assertIn("AC-018", str(res.get("errors") or {}))
			except frappe.PermissionError:
				pass
		finally:
			frappe.set_user("Administrator")

		# Authority path with same submitter identity: set submitted_by to Admin and try as Admin.
		name = frappe.db.get_value("Budget", {"generated_reference": "MOH-BUD-0004"}, "name")
		# Reseed then create dedicated path: submit as Admin on a fixed draft.
		upsert_moh_mvp_v1_portfolio()
		doc = frappe.get_doc("Budget", {"generated_reference": "MOH-BUD-0004"})
		doc.approval_evidence = "/private/files/moh-bud-0004-fixed.pdf"
		doc.save(ignore_permissions=True)
		for ln in frappe.get_all("Budget Line", filters={"budget": doc.name}, pluck="name"):
			line = frappe.get_doc("Budget Line", ln)
			if not (line.primary_target_code or "").strip():
				line.primary_target_code = "MOH-TGT-0003"
				line.primary_target_name = "Digital health technical capability target"
				line.primary_strategy_linked = 1
			if not line.get("value_treatments"):
				line.append(
					"value_treatments",
					{
						"pvc_code": "PVO-EFT-01",
						"pvc_name": "Improve infrastructure efficiency",
						"requirement_level": "Required",
						"treatment": "Embedded in line",
						"dedicated_amount": 0,
						"rationale": "Included in line delivery.",
					},
				)
			line.save(ignore_permissions=True)
		submit_budget({"budget": "MOH-BUD-0004"})
		mark_budget_reviewed({"budget": "MOH-BUD-0004"})
		# Force submitter == actor
		frappe.db.set_value(
			"Budget",
			frappe.db.get_value("Budget", {"generated_reference": "MOH-BUD-0004"}, "name"),
			"submitted_by",
			"Administrator",
		)
		res = activate_budget({"budget": "MOH-BUD-0004"})
		self.assertFalse(res.get("ok"))
		self.assertIn("AC-018", str((res.get("errors") or {}).get("status") or ""))

	def test_pe_scope_denial(self):
		email = "budget.readiness.pe.deny@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Readiness",
					"last_name": "Deny",
					"send_welcome_email": 0,
					"new_password": "Test@12345",
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Budget Viewer")
		frappe.set_user(email)
		try:
			with self.assertRaises(frappe.PermissionError):
				get_budget_readiness("MOH-BUD-0001")
		finally:
			frappe.set_user("Administrator")
