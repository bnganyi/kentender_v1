# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-SUP-002 — API role matrix (server enforcement for BUD-AC-015/018/019 + export)."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.seeds.budget_role_users import upsert_budget_role_users
from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_funding_performance_contracts import (
	export_funding_performance,
	get_funding_performance,
)
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_budget.services.budget_readiness_contracts import (
	activate_budget,
	get_budget_readiness,
	mark_budget_reviewed,
	return_budget,
	submit_budget,
)
from kentender_budget.services.budget_revision_contracts import (
	apply_budget_revision,
	create_budget_revision,
	reject_budget_revision,
	submit_budget_revision,
)

VIEWER = "budget.viewer@moh.test"
OFFICER = "budget.officer@moh.test"
REVIEWER = "budget.reviewer@moh.test"
AUTHORITY = "budget.authority@moh.test"
DUAL = "budget.officer.authority@moh.test"
OTHER = "budget.officer@moe.test"


class TestBudgetRoleMatrix(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		upsert_budget_role_users()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def setUp(self):
		frappe.set_user("Administrator")
		upsert_moh_mvp_v1_portfolio()
		upsert_budget_role_users()

	def tearDown(self):
		frappe.set_user("Administrator")

	def _prepare_draft_0004(self):
		doc = frappe.get_doc("Budget", {"generated_reference": "MOH-BUD-0004"})
		doc.approval_evidence = "/private/files/moh-bud-0004-role-matrix.pdf"
		doc.save(ignore_permissions=True)
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
					},
				)
			line.save(ignore_permissions=True)
		return doc

	def test_viewer_active_ok_draft_denied(self):
		frappe.set_user(VIEWER)
		active = get_budget_readiness("MOH-BUD-0001")
		self.assertEqual(active["budget"]["status"], "Active")
		perf = get_funding_performance()
		self.assertTrue(perf["capabilities"]["can_export"])
		export_funding_performance()
		with self.assertRaises(frappe.PermissionError):
			get_budget_readiness("MOH-BUD-0004")
		with self.assertRaises(frappe.PermissionError):
			submit_budget({"budget": "MOH-BUD-0004"})
		with self.assertRaises(frappe.PermissionError):
			return_budget({"budget": "MOH-BUD-0002", "comment": "x"})
		with self.assertRaises(frappe.PermissionError):
			activate_budget({"budget": "MOH-BUD-0002"})
		with self.assertRaises(frappe.PermissionError):
			create_budget_revision(
				{
					"budget": "MOH-BUD-0001",
					"external_approval_reference": "X",
					"approval_date": "2027-12-01",
					"effective_date": "2027-12-15",
					"reason": "viewer deny",
					"approval_evidence": "/private/files/x.pdf",
					"lines": [{"budget_line": "MOH-BL-0002", "change_amount": 1_000_000}],
				}
			)

	def test_officer_submit_ok_review_denied_export_denied(self):
		self._prepare_draft_0004()
		frappe.set_user(OFFICER)
		ok = submit_budget({"budget": "MOH-BUD-0004"})
		self.assertTrue(ok.get("ok"), ok)
		with self.assertRaises(frappe.PermissionError):
			return_budget({"budget": "MOH-BUD-0002", "comment": "officer cannot return"})
		with self.assertRaises(frappe.PermissionError):
			mark_budget_reviewed({"budget": "MOH-BUD-0002"})
		with self.assertRaises(frappe.PermissionError):
			activate_budget({"budget": "MOH-BUD-0002"})
		with self.assertRaises(frappe.PermissionError):
			apply_budget_revision({"revision": "BR-MOH-0002"})
		with self.assertRaises(frappe.PermissionError):
			reject_budget_revision({"revision": "BR-MOH-0002", "comment": "no"})
		perf = get_funding_performance()
		self.assertFalse(perf["capabilities"]["can_export"])
		with self.assertRaises(frappe.PermissionError):
			export_funding_performance()

	def test_reviewer_return_mark_ok_submit_activate_denied(self):
		name = frappe.db.get_value(
			"Budget", {"generated_reference": "MOH-BUD-0002"}, "name"
		)
		frappe.db.set_value(
			"Budget",
			name,
			{
				"status": "Submitted",
				"submitted_by": OFFICER,
				"reviewed_by": None,
				"reviewed_at": None,
			},
		)
		frappe.set_user(REVIEWER)
		marked = mark_budget_reviewed({"budget": "MOH-BUD-0002"})
		self.assertTrue(marked.get("ok"), marked)
		# restore for return path
		frappe.set_user("Administrator")
		upsert_moh_mvp_v1_portfolio()
		frappe.db.set_value(
			"Budget",
			frappe.db.get_value("Budget", {"generated_reference": "MOH-BUD-0002"}, "name"),
			{
				"status": "Submitted",
				"submitted_by": OFFICER,
				"reviewed_by": None,
				"reviewed_at": None,
			},
		)
		frappe.set_user(REVIEWER)
		returned = return_budget(
			{"budget": "MOH-BUD-0002", "comment": "Return for role matrix evidence."}
		)
		self.assertTrue(returned.get("ok"), returned)
		self._prepare_draft_0004()
		with self.assertRaises(frappe.PermissionError):
			submit_budget({"budget": "MOH-BUD-0004"})
		with self.assertRaises(frappe.PermissionError):
			activate_budget({"budget": "MOH-BUD-0002"})
		with self.assertRaises(frappe.PermissionError):
			apply_budget_revision({"revision": "BR-MOH-0002"})
		with self.assertRaises(frappe.PermissionError):
			create_budget_revision(
				{
					"budget": "MOH-BUD-0001",
					"external_approval_reference": "X",
					"approval_date": "2027-12-01",
					"effective_date": "2027-12-15",
					"reason": "reviewer deny create",
					"approval_evidence": "/private/files/x.pdf",
					"lines": [{"budget_line": "MOH-BL-0002", "change_amount": 1_000_000}],
				}
			)

	def test_authority_activate_ok_submit_denied(self):
		name = frappe.db.get_value(
			"Budget", {"generated_reference": "MOH-BUD-0002"}, "name"
		)
		frappe.db.set_value(
			"Budget",
			name,
			{
				"status": "Submitted",
				"submitted_by": OFFICER,
				"reviewed_by": REVIEWER,
				"reviewed_at": frappe.utils.now_datetime(),
			},
		)
		frappe.set_user(AUTHORITY)
		activated = activate_budget({"budget": "MOH-BUD-0002"})
		self.assertTrue(activated.get("ok"), activated)
		self.assertEqual(activated["readiness"]["budget"]["status"], "Active")
		self._prepare_draft_0004()
		with self.assertRaises(frappe.PermissionError):
			submit_budget({"budget": "MOH-BUD-0004"})
		with self.assertRaises(frappe.PermissionError):
			create_budget_revision(
				{
					"budget": "MOH-BUD-0001",
					"external_approval_reference": "X",
					"approval_date": "2027-12-01",
					"effective_date": "2027-12-15",
					"reason": "authority deny create",
					"approval_evidence": "/private/files/x.pdf",
					"lines": [{"budget_line": "MOH-BL-0002", "change_amount": 1_000_000}],
				}
			)
		perf = get_funding_performance()
		self.assertTrue(perf["capabilities"]["can_export"])

	def test_ac018_dual_role_cannot_activate_own_submission(self):
		self._prepare_draft_0004()
		frappe.set_user(DUAL)
		ok = submit_budget({"budget": "MOH-BUD-0004"})
		self.assertTrue(ok.get("ok"), ok)
		# Dual can mark reviewed (has Authority)
		marked = mark_budget_reviewed({"budget": "MOH-BUD-0004"})
		self.assertTrue(marked.get("ok"), marked)
		denied = activate_budget({"budget": "MOH-BUD-0004"})
		self.assertFalse(denied.get("ok"))
		self.assertIn("AC-018", str((denied.get("errors") or {}).get("status") or ""))

		# Own revision apply denied
		saved = create_budget_revision(
			{
				"budget": "MOH-BUD-0001",
				"external_approval_reference": "MOF/ROLE/AC018",
				"approval_date": "2027-12-01",
				"effective_date": "2027-12-15",
				"reason": "AC-018 dual apply deny",
				"approval_evidence": "/private/files/ac018.pdf",
				"lines": [{"budget_line": "MOH-BL-0002", "change_amount": 1_000_000}],
			}
		)
		self.assertTrue(saved.get("ok"), saved)
		code = saved["revision"]["code"]
		sub = submit_budget_revision({"revision": code})
		self.assertTrue(sub.get("ok"), sub)
		apply_denied = apply_budget_revision({"revision": code})
		self.assertFalse(apply_denied.get("ok"))

	def test_other_entity_cannot_access_moh(self):
		frappe.set_user(OTHER)
		with self.assertRaises(frappe.PermissionError):
			get_budget_readiness("MOH-BUD-0001")
		with self.assertRaises(frappe.PermissionError):
			get_budget_readiness("MOH-BUD-0002")
		with self.assertRaises(frappe.PermissionError):
			submit_budget({"budget": "MOH-BUD-0004"})

	def test_active_baseline_not_directly_submittable(self):
		"""AC-015 — Active budgets cannot use Draft submit path."""
		frappe.set_user(OFFICER)
		res = submit_budget({"budget": "MOH-BUD-0001"})
		self.assertFalse(res.get("ok"))
