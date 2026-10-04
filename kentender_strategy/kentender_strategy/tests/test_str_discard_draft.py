# Copyright (c) 2026, KenTender and contributors
"""discard_strategy_plan_draft — a Strategy Author can permanently remove a
Draft version that has never been submitted. Discarding a plan's only-ever
version (version 1) removes the plan itself; discarding a Draft successor
(version 2+) leaves the plan and its Active version untouched. Once a
version has ever been submitted (even if later Returned to Draft), it can
no longer be discarded — mirrors the structure-delete lock in
save_strategy_structure_draft (§5.1/§11.4).

    bench --site kentender.midas.com run-tests --app kentender_strategy \
        --module kentender_strategy.tests.test_str_discard_draft
"""

from __future__ import annotations

import frappe

from kentender_strategy.services import strategy_ui_contracts as ui
from kentender_strategy.services.strategy_transitions import transition_plan_version
from kentender_strategy.services.strategy_writes import discard_strategy_plan_draft
from kentender_strategy.tests.test_str_chg_001_v1_8_usability import UsabilityTestBase


class TestDiscardFirstDraft(UsabilityTestBase):
	def test_discard_removes_the_version_and_the_plan(self):
		plan_id, v1 = self._plan_and_version()
		fixture = self._fill_hierarchy(v1)
		author, _approver = self._actors("discard1")

		self.assertTrue(ui.get_plan_workspace(plan_id)["capabilities"]["discard_draft"])

		frappe.set_user(author)
		out = discard_strategy_plan_draft(v1)
		frappe.set_user("Administrator")

		self.assertTrue(out["plan_discarded"])
		self.assertIsNone(out["plan_id"])
		self.assertFalse(frappe.db.exists("Strategic Plan", plan_id))
		self.assertFalse(frappe.db.exists("Strategic Plan Version", v1))
		for dt, key in (
			("Strategy Node", "pillar"),
			("Strategy Node", "programme"),
			("Strategy Node", "objective"),
			("Performance Indicator", "indicator"),
			("Performance Target", "target"),
		):
			self.assertFalse(frappe.db.exists(dt, fixture[key]))

	def test_discard_requires_author_capability(self):
		_, v1 = self._plan_and_version()
		author, approver = self._actors("discard2")
		frappe.set_user(approver)
		with self.assertRaises(frappe.ValidationError):
			discard_strategy_plan_draft(v1)
		frappe.set_user("Administrator")
		self.assertTrue(frappe.db.exists("Strategic Plan Version", v1))

	def test_discard_blocked_once_ever_submitted(self):
		plan_id, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		author, approver = self._actors("discard3")
		frappe.set_user(author)
		transition_plan_version(v1, "Submit for approval")
		frappe.set_user(approver)
		transition_plan_version(v1, "Return", reason="Please fix the target period before resubmitting.")
		frappe.set_user(author)

		self.assertFalse(ui.get_plan_workspace(plan_id)["capabilities"]["discard_draft"])
		with self.assertRaises(frappe.ValidationError) as ctx:
			discard_strategy_plan_draft(v1)
		frappe.set_user("Administrator")
		self.assertIn("already been submitted", str(ctx.exception))
		self.assertTrue(frappe.db.exists("Strategic Plan Version", v1))

	def test_discard_blocked_while_submitted(self):
		_, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		author, _approver = self._actors("discard4")
		frappe.set_user(author)
		transition_plan_version(v1, "Submit for approval")
		with self.assertRaises(frappe.ValidationError) as ctx:
			discard_strategy_plan_draft(v1)
		frappe.set_user("Administrator")
		self.assertIn("Only a Draft version can be discarded", str(ctx.exception))


class TestDiscardSuccessorDraft(UsabilityTestBase):
	def test_discard_removes_only_the_successor_and_leaves_the_plan_active(self):
		plan_id, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		author, approver = self._actors("discard5")
		self._activate(v1, author, approver)
		v2 = self._successor(plan_id, author)

		ws = ui.get_plan_workspace(plan_id, version_number=2)
		self.assertTrue(ws["capabilities"]["discard_draft"])

		frappe.set_user(author)
		out = discard_strategy_plan_draft(v2)
		frappe.set_user("Administrator")

		self.assertFalse(out["plan_discarded"])
		self.assertEqual(out["plan_id"], plan_id)
		self.assertFalse(frappe.db.exists("Strategic Plan Version", v2))
		self.assertTrue(frappe.db.exists("Strategic Plan", plan_id))
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", v1, "status"), "Active")
		ws_after = ui.get_plan_workspace(plan_id)
		self.assertEqual(ws_after["current_version"]["id"], v1)
		self.assertIsNone(ws_after["pending_update"])
