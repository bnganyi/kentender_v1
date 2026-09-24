# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §10.16 — the Planning-side missing-setting panel
(C01–C04).

Planning never redefines System setup. What it owes the person at the blocked
action is the setting, the action it blocks and its owner — plus a route for an
actor who can actually use it, and the plain sentence naming who to ask for
everyone else. No disabled setup control ever appears in Planning.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import site_configuration
from kentender_procurement.procurement_planning.services import (
	dpp_lifecycle,
	dpp_read,
	missing_setting,
	plan_read,
	planning_authorization as authz,
)
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PLAN_STATUTORY_APPROVER
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_requisition import RequisitionCase


class MissingSettingCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")


class TestPanelShape(MissingSettingCase):
	def test_every_panel_names_the_setting_the_action_and_the_owner(self):
		panel = missing_setting.panel(
			setting="Annual Plan approval authority", affected_action="Adopt and submit",
			section=missing_setting.SECTION_RESPONSIBILITIES, user="Administrator",
		)
		self.assertEqual(panel["setting"], "Annual Plan approval authority")
		self.assertEqual(panel["affected_action"], "Adopt and submit")
		self.assertEqual(panel["responsible_role"], "Administrator or System Manager")

	def test_a_maintainer_gets_a_route_to_the_exact_section(self):
		panel = missing_setting.panel(
			setting="Applicable procurement method rule", affected_action="Send plan for governance review",
			section=missing_setting.SECTION_PROCUREMENT_SETTINGS, user="Administrator",
		)
		self.assertTrue(panel["can_open_setup"])
		self.assertEqual(panel["action"], "Open System setup")
		self.assertEqual(panel["href"], "/app/system-setup#procurement-settings")
		# The sentence naming who to ask is for people who cannot act.
		self.assertEqual(panel["ask_text"], "")

	def test_a_business_actor_is_told_who_to_ask_and_offered_no_control(self):
		panel = missing_setting.panel(
			setting="Applicable procurement schedule", affected_action="Submit annual plan",
			section=missing_setting.SECTION_PROCUREMENT_SETTINGS, user=fx.PLANNER,
		)
		self.assertFalse(panel["can_open_setup"])
		# §10.16 — never a disabled setup control.
		self.assertEqual(panel["action"], "")
		self.assertEqual(panel["href"], "")
		self.assertEqual(panel["ask_text"], "Ask your KenTender administrator to complete this setting.")
		# Every fact survives the missing control.
		self.assertEqual(panel["responsible_role"], "Administrator or System Manager")


class TestC01ApprovalAuthority(MissingSettingCase):
	def test_no_panel_while_the_responsibility_is_actually_held(self):
		self.assertTrue(authz.users_with_site_role(ROLE_PLAN_STATUTORY_APPROVER))
		self.assertIsNone(missing_setting.approval_authority(user=fx.ACCOUNTING_OFFICER))

	def test_the_panel_appears_only_when_nobody_holds_it(self):
		with patch.object(authz, "users_with_site_role", return_value=[]):
			panel = missing_setting.approval_authority(user=fx.ACCOUNTING_OFFICER)
		self.assertEqual(panel["setting"], "Annual Plan approval authority")
		self.assertEqual(panel["affected_action"], "Adopt and submit")
		self.assertFalse(panel["can_open_setup"])


class TestC02DepartmentalSubmissions(MissingSettingCase):
	def test_no_panel_while_submissions_are_open(self):
		self.assertIsNone(missing_setting.dpp_submissions(fiscal_year=fx.FY_OPEN, user=fx.AUTHOR))

	def test_a_closed_window_names_the_setting_and_what_is_still_permitted(self):
		with patch.object(site_configuration, "get_dpp_submission_state", return_value={"open": False}):
			panel = missing_setting.dpp_submissions(fiscal_year=fx.FY_OPEN, user=fx.AUTHOR)
		self.assertEqual(panel["setting"], "Departmental plan submissions")
		self.assertEqual(panel["affected_action"], "Submit initial departmental plan")
		# C02-DPP-CLOSED — the permitted work is named, not silently withdrawn.
		self.assertIn("Saving a draft", panel["note"])
		self.assertIn("returned submission", panel["note"])

	def test_the_departmental_plan_read_carries_it_above_the_submit_action(self):
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN,
			idempotency_key=frappe.generate_hash(length=20), fixture_namespace=fx.NS,
		)
		read = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])
		self.assertIsNone(read["missing_setting"])

		with patch.object(site_configuration, "get_dpp_submission_state", return_value={"open": False}):
			closed = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])
		self.assertEqual(closed["missing_setting"]["setting"], "Departmental plan submissions")


class TestC03AndC04ProcurementRules(MissingSettingCase):
	def test_the_panel_names_the_purchase_the_rule_is_missing_for(self):
		from kentender_procurement.procurement_planning.services import readiness

		item = frappe._dict({
			"name": "APIR-TEST", "plan_item_id": "PPI-TEST-001", "title": "Test procurement package",
			"procurement_method": "Open Tender", "procurement_category": "Goods",
			"baseline_invitation_date": "2026-12-01",
			"schedule_profile_version": "", "method_profile_version": "",
		})
		# No rule covers the date — not two rules covering it, which is a
		# different cause and now reads as a different sentence.
		absent = {"found": False, "reason": "no_profile"}
		unresolved = {"method": absent, "schedule": absent, "unresolved": set(), "applicability_date": "2026-12-01"}
		with patch.object(readiness, "method_profile_for", return_value=unresolved):
			panels = missing_setting.item_procurement_rules(item=item, fiscal_year=fx.FY_OPEN, user=fx.PLANNER)

		self.assertEqual(len(panels), 2)
		method, schedule = panels
		self.assertEqual(method["setting"], "Applicable procurement method rule")
		self.assertEqual(method["affected_action"], "Send plan for governance review")
		self.assertEqual(schedule["setting"], "Applicable procurement schedule")
		self.assertEqual(schedule["affected_action"], "Submit annual plan")
		for panel in panels:
			with self.subTest(setting=panel["setting"]):
				# A maintainer cannot act on "a rule is missing" alone.
				self.assertIn("PPI-TEST-001", panel["affected_purchase"])
				self.assertIn("Test procurement package", panel["affected_purchase"])
		# C03-METHOD-MISSING alone names the exact choice that stopped
		# resolving; C04-SCHEDULE-MISSING's own board carries no such line.
		self.assertEqual(
			method["lede"],
			"No procurement method rule is in force on 1 Dec 2026 (this purchase's planned invitation date), "
			"so Open Tender cannot be confirmed.",
		)
		self.assertEqual(schedule["lede"], "")

	def test_a_purchase_with_no_method_chosen_yet_is_not_a_missing_setting(self):
		from kentender_procurement.procurement_planning.services import readiness

		item = frappe._dict({
			"name": "APIR-TEST", "plan_item_id": "PPI-TEST-002", "title": "Not yet classified",
			"procurement_method": "", "procurement_category": "Goods",
			"schedule_profile_version": "", "method_profile_version": "",
		})
		resolved = {"method": {"found": False}, "schedule": {"found": True, "verification_status": "Verified"}, "unresolved": {"method"}}
		with patch.object(readiness, "method_profile_for", return_value=resolved):
			panels = missing_setting.item_procurement_rules(item=item, fiscal_year=fx.FY_OPEN, user=fx.PLANNER)
		# The Planner has not chosen a method yet: that is their own work to
		# finish, not a setting an administrator must add. The schedule side
		# is a resolved, verified profile — no panel of its own either.
		self.assertEqual(panels, [])

	def test_a_rule_that_is_found_but_not_verified_is_a_missing_setting_too(self):
		"""The check only looked at whether a rule existed, never whether it
		was marked valid (found live 23 Sep 2026): the currently active
		version can carry `Production verification pending`, which then only
		surfaced as a raw, unexplained error at Sign and submit."""
		from kentender_procurement.procurement_planning.services import readiness

		item = self._item("PPI-TEST-003")
		resolved = {
			"method": {"found": True, "verification_status": "Production verification pending"},
			"schedule": {"found": True, "verification_status": "Verified"},
			"unresolved": set(),
			"applicability_date": "2026-12-01",
		}
		with patch.object(readiness, "method_profile_for", return_value=resolved):
			panels = missing_setting.item_procurement_rules(item=item, fiscal_year=fx.FY_OPEN, user=fx.PLANNER)
		self.assertEqual(len(panels), 1)
		self.assertEqual(panels[0]["setting"], "Applicable procurement method rule")
		self.assertIn("PPI-TEST-003", panels[0]["affected_purchase"])
		self.assertEqual(
			panels[0]["lede"],
			"The Open Tender rule in force on 1 Dec 2026 (this purchase's planned invitation date) "
			"is not marked valid in System setup, so Open Tender cannot be confirmed.",
		)
		# A rule that exists is not a rule that is missing: nothing invites
		# the reader to add one.
		self.assertEqual(panels[0]["note"], "")

	def _item(self, plan_item_id: str, *, invitation: str = "2026-12-01"):
		return frappe._dict({
			"name": "APIR-TEST", "plan_item_id": plan_item_id, "title": "Test procurement package",
			"procurement_method": "Open Tender", "procurement_category": "Goods",
			"baseline_invitation_date": invitation,
			"schedule_profile_version": "", "method_profile_version": "",
		})

	def test_a_missing_rule_names_the_two_ways_out_of_it(self):
		"""The purchase's own date is half the answer. An administrator adds
		a rule that covers it; the Planner can instead move the date to one
		an existing rule already covers — and only the first was ever said."""
		from kentender_procurement.procurement_planning.services import readiness

		absent = {"found": False, "reason": "no_profile"}
		resolved = {"method": absent, "schedule": {"found": True, "verification_status": "Verified"},
			"unresolved": set(), "applicability_date": "2026-12-01"}
		with patch.object(readiness, "method_profile_for", return_value=resolved):
			panels = missing_setting.item_procurement_rules(item=self._item("PPI-TEST-004"), fiscal_year=fx.FY_OPEN, user=fx.PLANNER)
		self.assertEqual(
			panels[0]["note"],
			"Either a rule covering that date is added in System setup, or this purchase's planned "
			"invitation date moves to one an existing rule already covers.",
		)

	def test_a_purchase_with_no_invitation_date_yet_is_judged_on_its_financial_year(self):
		"""`profiles.applicability_date` falls back to the plan financial
		year's first day, so the sentence must not call that date a planned
		invitation date the purchase does not have."""
		from kentender_procurement.procurement_planning.services import readiness

		absent = {"found": False, "reason": "no_profile"}
		resolved = {"method": absent, "schedule": {"found": True, "verification_status": "Verified"},
			"unresolved": set(), "applicability_date": "2026-07-01"}
		item = self._item("PPI-TEST-005", invitation="")
		with patch.object(readiness, "method_profile_for", return_value=resolved):
			panels = missing_setting.item_procurement_rules(item=item, fiscal_year=fx.FY_OPEN, user=fx.PLANNER)
		self.assertEqual(
			panels[0]["lede"],
			"No procurement method rule is in force on 1 Jul 2026 (the start of this purchase's "
			"financial year), so Open Tender cannot be confirmed.",
		)

	def test_two_rules_in_force_at_once_is_said_as_that_and_not_as_a_missing_one(self):
		"""An ambiguous configuration is the opposite problem from an absent
		rule, and telling a maintainer to add one makes it worse."""
		from kentender_procurement.procurement_planning.services import readiness

		resolved = {"method": {"found": False}, "schedule": {"found": True, "verification_status": "Verified"},
			"unresolved": {"method"}, "applicability_date": "2026-12-01"}
		with patch.object(readiness, "method_profile_for", return_value=resolved):
			panels = missing_setting.item_procurement_rules(item=self._item("PPI-TEST-006"), fiscal_year=fx.FY_OPEN, user=fx.PLANNER)
		self.assertEqual(
			panels[0]["lede"],
			"More than one procurement method rule is in force for Open Tender on 1 Dec 2026 "
			"(this purchase's planned invitation date), so it cannot be confirmed until one of them is retired.",
		)
		self.assertEqual(panels[0]["note"], "")


class TestPlanRulePanels(RequisitionCase):
	"""The plan-level half of C03/C04, against a real governed Version."""

	def test_a_plan_whose_rules_are_all_in_force_shows_no_panel(self):
		accepted, item_id = self.confirmed_item()
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(plan["missing_settings"], [])

	def test_an_unresolvable_rule_names_its_own_purchase_on_the_plan(self):
		from kentender_procurement.procurement_planning.services import readiness

		accepted, item_id = self.confirmed_item()
		frappe.set_user(fx.PLANNER)
		unresolved = {"method": {"found": False}, "schedule": {"found": False}, "unresolved": {"method", "schedule"}}
		with patch.object(readiness, "method_profile_for", return_value=unresolved):
			plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])

		settings = plan["missing_settings"]
		self.assertEqual({p["setting"] for p in settings}, {
			"Applicable procurement method rule", "Applicable procurement schedule",
		})
		for panel in settings:
			with self.subTest(setting=panel["setting"]):
				self.assertIn(item_id, panel["affected_purchase"])
				# The Planner is told who to ask; no setup control is offered.
				self.assertFalse(panel["can_open_setup"])
				self.assertEqual(panel["ask_text"], "Ask your KenTender administrator to complete this setting.")

	def test_an_active_version_carries_no_rule_panels(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		# The rules that governed it resolved at submission; an approved plan
		# is not a setup problem.
		self.assertEqual(plan["missing_settings"], [])


class TestOneSettingIsOnePanel(MissingSettingCase):
	"""A setting is wrong once, not once per purchase.

	Found live 24 Sep 2026: one unresolvable method rule produced four
	identical panels on a four-purchase plan, and four identical lines in the
	submission-issue list above them — the same sentence eight times for one
	missing rule. On a hundred-purchase plan that is two hundred rows, and
	the administrator still has exactly one thing to fix.
	"""

	def _item(self, n: int, *, invitation: str = "2026-12-01", method: str = "Open Tender"):
		return frappe._dict({
			"name": f"APIR-{n}", "plan_item_id": f"PPI-TEST-{n:03d}", "title": f"Purchase {n}",
			"procurement_method": method, "procurement_category": "Goods",
			"baseline_invitation_date": invitation,
			"schedule_profile_version": "", "method_profile_version": "",
		})

	def test_one_missing_rule_across_many_purchases_is_one_panel(self):
		from kentender_procurement.procurement_planning.services import readiness

		absent = {"found": False, "reason": "no_profile"}
		resolved = {"method": absent, "schedule": {"found": True, "verification_status": "Verified"},
			"unresolved": set(), "applicability_date": "2026-12-01"}
		items = [self._item(n) for n in range(1, 5)]
		with patch.object(readiness, "method_profile_for", return_value=resolved):
			panels = missing_setting.rule_panels(items=items, fiscal_year=fx.FY_OPEN, user=fx.PLANNER)

		self.assertEqual(len(panels), 1)
		self.assertEqual(panels[0]["setting"], "Applicable procurement method rule")
		self.assertEqual(panels[0]["affected_count"], 4)
		self.assertEqual(
			panels[0]["affected_purchase"],
			"4 purchases: PPI-TEST-001, PPI-TEST-002, PPI-TEST-003 and 1 more",
		)

	def test_a_hundred_purchases_still_produce_one_panel_and_a_readable_line(self):
		from kentender_procurement.procurement_planning.services import readiness

		absent = {"found": False, "reason": "no_profile"}
		resolved = {"method": absent, "schedule": {"found": True, "verification_status": "Verified"},
			"unresolved": set(), "applicability_date": "2026-12-01"}
		items = [self._item(n) for n in range(1, 101)]
		with patch.object(readiness, "method_profile_for", return_value=resolved):
			panels = missing_setting.rule_panels(items=items, fiscal_year=fx.FY_OPEN, user=fx.PLANNER)

		self.assertEqual(len(panels), 1)
		self.assertEqual(panels[0]["affected_count"], 100)
		self.assertIn("100 purchases:", panels[0]["affected_purchase"])
		self.assertIn("and 97 more", panels[0]["affected_purchase"])

	def test_a_single_affected_purchase_is_still_named_in_full(self):
		from kentender_procurement.procurement_planning.services import readiness

		absent = {"found": False, "reason": "no_profile"}
		resolved = {"method": absent, "schedule": {"found": True, "verification_status": "Verified"},
			"unresolved": set(), "applicability_date": "2026-12-01"}
		with patch.object(readiness, "method_profile_for", return_value=resolved):
			panels = missing_setting.rule_panels(items=[self._item(7)], fiscal_year=fx.FY_OPEN, user=fx.PLANNER)
		self.assertEqual(panels[0]["affected_count"], 1)
		self.assertEqual(panels[0]["affected_purchase"], "Purchase 7 · PPI-TEST-007")

	def test_different_causes_stay_different_panels(self):
		"""Grouping is by what is actually wrong, never by the setting alone:
		a rule that is missing and a rule that is not marked valid want
		different work from the administrator."""
		from kentender_procurement.procurement_planning.services import readiness

		absent = {"method": {"found": False, "reason": "no_profile"}, "schedule": {"found": True, "verification_status": "Verified"},
			"unresolved": set(), "applicability_date": "2026-12-01"}
		unmarked = {"method": {"found": True, "verification_status": "Production verification pending"},
			"schedule": {"found": True, "verification_status": "Verified"},
			"unresolved": set(), "applicability_date": "2027-06-01"}

		def by_item(item, fiscal_year, **kw):
			return absent if item.plan_item_id == "PPI-TEST-001" else unmarked

		with patch.object(readiness, "method_profile_for", side_effect=by_item):
			panels = missing_setting.rule_panels(items=[self._item(1), self._item(2), self._item(3)], fiscal_year=fx.FY_OPEN, user=fx.PLANNER)
		self.assertEqual(len(panels), 2)
		self.assertEqual([p["affected_count"] for p in panels], [1, 2])
		self.assertIn("No procurement method rule is in force", panels[0]["lede"])
		self.assertIn("is not marked valid", panels[1]["lede"])
