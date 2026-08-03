# Copyright (c) 2026, KenTender and contributors
"""STR-UI-13 / §13 — readiness DTO, allowed_actions, plan transition matrix."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.moh_review_fixtures import (
	REVIEW_BLOCKERS_PLAN_CODE,
	REVIEW_TX_PLAN_CODE,
	ensure_review_blockers_draft,
	ensure_review_transition_draft,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_readiness import assert_plan_ready_for_submit, get_plan_readiness
from kentender_strategy.services.strategy_transitions import transition_plan


def _ensure_user(email: str, roles: list[str], procuring_entity: str | None = None) -> str:
	ensure_strategy_roles()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	have = set(frappe.get_roles(email))
	for role in (
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Planning Authority",
		"Performance Officer",
		"Performance Verifier",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


class TestStrategyReviewReadiness(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.blockers = ensure_review_blockers_draft(cls.pe)
		cls.tx = ensure_review_transition_draft(cls.pe)

	def test_active_seed_ready_with_empty_actions(self):
		result = get_plan_readiness(self.seed["plan"])
		self.assertTrue(result["ready"])
		self.assertEqual(result["blocker_count"], 0)
		self.assertIn("grouped", result)
		for key in ("Structure", "Targets", "Value Commitments", "Governance"):
			self.assertIn(key, result["grouped"])
		self.assertEqual(result["allowed_actions"], [])
		self.assertIn("return_reason", result)
		self.assertEqual(result["status"], "Active")
		self.assertEqual(result["plan"]["code"], STRATEGY_PLAN_CODE)
		# Shared plan chrome on Review needs the same period/version fields as Overview.
		self.assertTrue(result["plan"].get("effective_period_label"))
		self.assertIn("version_number", result["plan"])
		self.assertIn("start_date", result["plan"])

	def test_incomplete_draft_blockers_and_edit_location(self):
		self.assertTrue(self.blockers.get("ok"))
		result = get_plan_readiness(self.blockers["plan"])
		self.assertFalse(result["ready"])
		self.assertGreaterEqual(result["blocker_count"], 1)
		self.assertEqual(result["plan"]["code"], REVIEW_BLOCKERS_PLAN_CODE)
		structure = result["grouped"]["Structure"]
		self.assertTrue(structure)
		self.assertTrue(all(i.get("edit_location") for i in structure))
		self.assertTrue(any(i.get("title") == "No Programme" for i in structure))
		# Not ready → Submit must not appear even for Administrator (all roles)
		self.assertNotIn("Submit", result["allowed_actions"])
		with self.assertRaises(frappe.ValidationError):
			assert_plan_ready_for_submit(self.blockers["plan"])

	def test_ready_draft_allows_submit_for_manager(self):
		self.tx = ensure_review_transition_draft(self.pe)
		manager = _ensure_user("str.mgr.review@example.com", ["Strategy Manager"], self.pe)
		frappe.set_user(manager)
		try:
			result = get_plan_readiness(self.tx["plan"])
			self.assertTrue(result["ready"], result.get("issues"))
			self.assertIn("Submit", result["allowed_actions"])
		finally:
			frappe.set_user("Administrator")

	def test_viewer_has_no_transition_actions(self):
		self.tx = ensure_review_transition_draft(self.pe)
		viewer = _ensure_user("str.viewer.review@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user(viewer)
		try:
			result = get_plan_readiness(self.tx["plan"])
			self.assertTrue(result["ready"])
			self.assertEqual(result["allowed_actions"], [])
		finally:
			frappe.set_user("Administrator")

	def test_transition_matrix_submit_return_approve_activate(self):
		self.tx = ensure_review_transition_draft(self.pe)
		plan = self.tx["plan"]
		manager = _ensure_user("str.mgr.review.tx@example.com", ["Strategy Manager"], self.pe)
		reviewer = _ensure_user("str.rev.review.tx@example.com", ["Strategy Reviewer"], self.pe)
		pa = _ensure_user("str.pa.review.tx@example.com", ["Planning Authority"], self.pe)

		frappe.set_user(manager)
		try:
			with self.assertRaises(frappe.ValidationError):
				# blockers fixture must still block
				transition_plan(self.blockers["plan"], "Submit")
			out = transition_plan(plan, "Submit")
			self.assertEqual(out["status"], "Submitted")
		finally:
			frappe.set_user("Administrator")

		ready = get_plan_readiness(plan)
		self.assertEqual(ready["status"], "Submitted")
		self.assertIn("Return for correction", ready["allowed_actions"])
		self.assertIn("Approve", ready["allowed_actions"])
		self.assertNotIn("Submit", ready["allowed_actions"])
		self.assertNotIn("Resubmit", ready["allowed_actions"])

		frappe.set_user(reviewer)
		try:
			out = transition_plan(plan, "Return for correction", reason="Missing evidence of ownership")
			self.assertEqual(out["status"], "Returned")
		finally:
			frappe.set_user("Administrator")

		ready = get_plan_readiness(plan)
		self.assertEqual(ready["return_reason"], "Missing evidence of ownership")
		self.assertIn("Resubmit", ready["allowed_actions"])

		frappe.set_user(manager)
		try:
			out = transition_plan(plan, "Resubmit")
			self.assertEqual(out["status"], "Submitted")
		finally:
			frappe.set_user("Administrator")

		frappe.set_user(pa)
		try:
			out = transition_plan(plan, "Approve")
			self.assertEqual(out["status"], "Approved")
			ready = get_plan_readiness(plan)
			self.assertIn("Activate", ready["allowed_actions"])
			out = transition_plan(plan, "Activate")
			self.assertEqual(out["status"], "Active")
		finally:
			frappe.set_user("Administrator")

		ready = get_plan_readiness(plan)
		self.assertTrue(ready["ready"])
		self.assertEqual(ready["allowed_actions"], [])
		self.assertEqual(ready["plan"]["code"], REVIEW_TX_PLAN_CODE)
