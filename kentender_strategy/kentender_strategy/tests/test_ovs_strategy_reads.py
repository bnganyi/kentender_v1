# Copyright (c) 2026, KenTender and contributors
"""The Accounting Officer, the Head of Procurement Function and a Head of User Department read approved
Strategy (OVS-CHG-001 v0.6 §4.1; plan Phase 10; tracker OVS6-1001; acceptance OVS-AC-008, OVS-AC-009).

"Active AO, HOPF and HoD responsibilities can read approved current and historical Strategy versions and
their recorded approval reasons. No general Draft or pending review access is added." Since 5 October 2026 (owner:
Strategy is a universally readable module) every enabled internal (System) user reads the same approved versions, with or
without a Strategy responsibility; supplier and other Website accounts do not. Approved means a
version that is Current or Previous; a version awaiting approval, a draft and the approval task stay with
the people who already hold them. Strategy has no department attribution, so a Head of User Department
reads the same approved versions as the two offices (the approved-version read is not departmental)."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe

from kentender_core.services import responsibility_administration as administration
from kentender_strategy.services import strategy_ui_contracts as ui
from kentender_strategy.services.strategy_authorization import ROLE_STRATEGY_APPROVER, ROLE_STRATEGY_AUTHOR, ensure_strategy_governance_roles
from kentender_strategy.services.strategy_transitions import transition_plan_version
from kentender_strategy.tests.fixtures import ensure_fiscal_year, pin_review_date
from kentender_strategy.tests.test_str_technical_read import TechnicalReadTestBase

# The suite's usual 2040 window collides with Frappe's own `_Test Fiscal Year 2040` on a site that loaded test records;
# this suite uses a window nothing else occupies.
FY, START, END = "2060-2061", "2060-07-01", "2065-06-30"


class TestApprovedStrategyReads(TechnicalReadTestBase):
	def setUp(self):
		ensure_strategy_governance_roles()
		ensure_fiscal_year(2060)
		self.suffix = uuid4().hex[:8]
		self._cleanup = []
		patcher = patch("kentender_strategy.tests.test_str_technical_read.FY", FY)
		patcher.start()
		self.addCleanup(patcher.stop)
		pin_review_date(self)
		self.author = self._user("author")
		self.approver = self._user("approver")
		self._grant(self.author, ROLE_STRATEGY_AUTHOR)
		self._grant(self.approver, ROLE_STRATEGY_APPROVER)
		unit = frappe.db.get_value("Organisation Unit", {"status": "Active"}, "name")
		self.readers = {}
		for label, role, ou in (("ao", "Accounting Officer", ""), ("hopf", "Head of Procurement Function", ""), ("hod", "Head of User Department", unit)):
			user = self._user(label)
			outcome = administration.grant(
				user=user, business_role=role, organisation_unit=ou, fixture_namespace="STR_TECHREAD_TESTS", actor="Administrator")
			self._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))
			self.readers[label] = user
		self.outsider = self._user("outsider")
		self.pending_plan, self.pending = self._make("Pending", approve=False)
		self.approved_plan, self.approved = self._make("Approved", approve=True)

	def _make(self, label: str, *, approve: bool):
		plan = self._plan(title=f"OVS {label} {self.suffix}", period_start=START, period_end=END)
		version = self._version(plan, effective_from=START, effective_to=END)
		self._hierarchy(version)
		frappe.set_user(self.author)
		try:
			transition_plan_version(version.name, "Submit for approval")
		finally:
			frappe.set_user("Administrator")
		if approve:
			frappe.set_user(self.approver)
			try:
				transition_plan_version(version.name, "Approve")
			finally:
				frappe.set_user("Administrator")
		version.reload()
		return plan, version

	def as_user(self, user, fn, *args, **kwargs):
		frappe.set_user(user)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_the_three_readers_see_the_approved_plan_and_not_the_one_awaiting_approval(self):
		self.assertEqual(self.approved.status, "Active")
		for label, user in self.readers.items():
			portfolio = self.as_user(user, ui.get_strategy_portfolio)
			self.assertFalse(portfolio["forbidden"], label)
			ids = [p["id"] for p in portfolio["plans"]]
			self.assertIn(self.approved_plan.name, ids, label)
			self.assertNotIn(self.pending_plan.name, ids, label)
			self.assertEqual(portfolio["my_work"], [], label)
			self.assertFalse(portfolio["can_create_plan"], label)
			self.assertEqual({o["value"] for o in portfolio["status_options"]}, {"Active", "Superseded"}, label)

	def test_each_row_offers_view_with_a_route_to_the_plan(self):
		# UAT: the register drew a View button for these readers but the row carried no route,
		# so clicking it did nothing.
		for label, user in self.readers.items():
			portfolio = self.as_user(user, ui.get_strategy_portfolio)
			row = next(p for p in portfolio["plans"] if p["id"] == self.approved_plan.name)
			self.assertEqual(row["available_action"], "View", label)
			self.assertEqual(row["action_route"], ui.plan_route(self.approved_plan.plan_id), label)

	def test_they_open_the_approved_plan_its_structure_and_the_approval_history(self):
		for label, user in self.readers.items():
			workspace = self.as_user(user, ui.get_plan_workspace, self.approved_plan.plan_id)
			self.assertFalse(workspace.get("forbidden"), label)
			self.assertFalse(workspace.get("not_found"), label)
			self.assertFalse(workspace["capabilities"]["update_plan"], label)
			self.assertFalse(workspace["capabilities"]["submit"], label)
			tree = self.as_user(user, ui.get_strategy_tree, self.approved.name)
			self.assertFalse(tree.get("not_found"), label)
			events = [e["event"] for e in self.as_user(user, ui.get_plan_history, self.approved_plan.plan_id)]
			self.assertIn("Approve", events, label)

	def test_a_plan_version_not_yet_approved_is_not_found_to_them(self):
		for label, user in self.readers.items():
			self.assertTrue(self.as_user(user, ui.get_plan_workspace, self.pending_plan.plan_id).get("not_found"), label)
			self.assertTrue(self.as_user(user, ui.get_strategy_tree, self.pending.name).get("not_found"), label)
			self.assertEqual(self.as_user(user, ui.get_version_history, self.pending.name), [], label)
			self.assertEqual(self.as_user(user, ui.get_plan_history, self.pending_plan.plan_id), [], label)

	def test_the_approval_task_and_the_comparison_stay_with_the_people_who_hold_them(self):
		for label, user in self.readers.items():
			self.assertTrue(self.as_user(user, ui.get_version_review_overview, self.approved.name).get("forbidden"), label)
			self.assertTrue(self.as_user(user, ui.diff_strategy_versions, None, self.approved.name).get("not_found"), label)

	def test_every_internal_user_reads_the_approved_plan_and_nothing_else(self):
		# Owner, 5 Oct 2026: Strategy is a universally readable module. A signed-in internal user with no
		# Strategy responsibility at all reads approved plans; drafts, pending plans and the approval task stay closed.
		user = self.outsider
		portfolio = self.as_user(user, ui.get_strategy_portfolio)
		self.assertFalse(portfolio["forbidden"])
		ids = [p["id"] for p in portfolio["plans"]]
		self.assertIn(self.approved_plan.name, ids)
		self.assertNotIn(self.pending_plan.name, ids)
		self.assertEqual(portfolio["my_work"], [])
		self.assertFalse(portfolio["can_create_plan"])
		workspace = self.as_user(user, ui.get_plan_workspace, self.approved_plan.plan_id)
		self.assertFalse(workspace.get("forbidden"))
		self.assertFalse(workspace.get("not_found"))
		self.assertFalse(workspace["capabilities"]["update_plan"])
		self.assertFalse(self.as_user(user, ui.get_strategy_tree, self.approved.name).get("not_found"))
		self.assertTrue(self.as_user(user, ui.get_plan_workspace, self.pending_plan.plan_id).get("not_found"))
		self.assertTrue(self.as_user(user, ui.get_strategy_tree, self.pending.name).get("not_found"))
		self.assertTrue(self.as_user(user, ui.get_version_review_overview, self.approved.name).get("forbidden"))

	def test_a_supplier_or_other_website_account_is_still_refused(self):
		email = f"kt.test.str.supplier.{self.suffix}@test.local"
		doc = frappe.get_doc({"doctype": "User", "email": email, "first_name": "supplier", "enabled": 1, "send_welcome_email": 0, "user_type": "Website User"}).insert(ignore_permissions=True)
		self._track(doc)
		self.assertTrue(self.as_user(email, ui.get_strategy_portfolio)["forbidden"])
		self.assertTrue(self.as_user(email, ui.get_plan_workspace, self.approved_plan.plan_id).get("forbidden"))

	def test_a_disabled_internal_user_is_refused(self):
		frappe.db.set_value("User", self.outsider, "enabled", 0)
		self.assertTrue(self.as_user(self.outsider, ui.get_strategy_portfolio)["forbidden"])

	def test_the_existing_readers_still_see_the_pending_plan(self):
		ids = [p["id"] for p in self.as_user(self.approver, ui.get_strategy_portfolio)["plans"]]
		self.assertIn(self.pending_plan.name, ids)


	# AUD-STR-005 — the whitelisted downstream contracts follow the owner's read ruling: every internal user
	# reads the approved plans; portal accounts read nothing; a Draft or pending version's lineage stays with
	# the Strategy readers. In-process callers (Planning, Requisitions) use the services and are unaffected.

	def _nodes(self, version):
		return frappe.get_all("Strategy Node", filters={"plan_version_id": version.name}, pluck="name", order_by="display_order asc")

	def _website_user(self):
		email = f"kt.test.str.portal.{self.suffix}@test.local"
		doc = frappe.get_doc({"doctype": "User", "email": email, "first_name": "portal", "enabled": 1, "send_welcome_email": 0, "user_type": "Website User"}).insert(ignore_permissions=True)
		self._track(doc)
		return email

	def test_a_portal_account_is_refused_every_consumer_endpoint(self):
		from kentender_strategy.api import strategy_consumer_api as api

		portal = self._website_user()
		node = self._nodes(self.approved)[0]
		calls = (
			lambda: api.resolve_strategy_context(as_of_date=START),
			lambda: api.list_strategy_objectives(self.approved.name),
			lambda: api.get_strategy_lineage(node),
			lambda: api.list_active_targets(),
			lambda: api.create_strategy_snapshot(self.approved.name, node, f"kt-test-{self.suffix}"),
		)
		for i, call in enumerate(calls):
			with self.assertRaises(frappe.PermissionError, msg=f"call #{i}"):
				self.as_user(portal, call)
		self.assertFalse(frappe.db.exists("Audit Event", {"reason": f"kt-test-{self.suffix}"}))

	def test_an_internal_user_without_a_responsibility_reads_the_approved_plan_through_the_api(self):
		from kentender_strategy.api import strategy_consumer_api as api

		out = self.as_user(self.outsider, api.list_strategy_objectives, self.approved.name)
		self.assertIn("rows", out)
		node = self._nodes(self.approved)[0]
		self.assertEqual(self.as_user(self.outsider, api.get_strategy_lineage, node)["node_id"], node)

	def test_lineage_of_a_version_awaiting_approval_is_refused_to_a_plain_internal_user(self):
		from kentender_strategy.api import strategy_consumer_api as api

		node = self._nodes(self.pending)[0]
		with self.assertRaises(frappe.DoesNotExistError):
			self.as_user(self.outsider, api.get_strategy_lineage, node)
		# the Strategy readers keep their view of it
		self.assertEqual(self.as_user(self.approver, api.get_strategy_lineage, node)["node_id"], node)

	def test_the_in_process_service_still_answers_for_system_callers(self):
		from kentender_strategy.services import strategy_consumer as consumer

		node = self._nodes(self.pending)[0]
		# Administrator (a background job, a seed) is a technical reader
		self.assertEqual(consumer.get_strategy_lineage(node)["node_id"], node)
