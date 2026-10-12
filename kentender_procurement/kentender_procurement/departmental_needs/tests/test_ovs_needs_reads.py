# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Accounting Officer and the Head of Procurement Function read submitted and decided Needs
(OVS-CHG-001 v0.6 §4.1; NDS-CHG-001 v1.16 §6; plan Phase 10; tracker OVS6-1003; acceptance
OVS-AC-008, OVS-AC-009).

A neutral read, site-wide, of a Need that was sent for review or decided. Unsent author drafts, returned
Needs under correction and withdrawn Needs stay under their existing access. The grant gives no decision,
no task and no workspace of its own."""

from __future__ import annotations

import frappe

from kentender_procurement.departmental_needs.constants import STATE_ACCEPTED, STATE_NOT_TAKEN_FORWARD, STATE_SUBMITTED
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.services import permissions, workspace
from kentender_procurement.departmental_needs.tests.test_departmental_needs_permissions import NO_GRANT_USER, DepartmentalNeedsPermissionCase

AO = "amina.hassan@moh.example.test"
HOPF = "charles.mutiso@moh.example.test"


class TestOversightOfNeeds(DepartmentalNeedsPermissionCase):
	def in_state(self, state: str):
		need = self.accepted_need()
		need.current_state = state
		return need

	def test_both_offices_read_a_submitted_or_decided_need_as_observers(self):
		for user in (AO, HOPF):
			for state in (STATE_SUBMITTED, STATE_ACCEPTED, STATE_NOT_TAKEN_FORWARD):
				self.assertEqual(permissions.can_view(self.in_state(state), user), (True, "oversight"), f"{user} {state}")

	def test_a_draft_a_returned_need_and_a_withdrawn_need_stay_closed_to_them(self):
		for user in (AO, HOPF):
			for state in ("Draft", "Returned", "Withdrawn"):
				self.assertEqual(permissions.can_view(self.in_state(state), user), (False, "none"), f"{user} {state}")

	def test_the_grant_gives_no_decision_and_no_task(self):
		for user in (AO, HOPF):
			with self.assertRaises(DepartmentalNeedError) as caught:
				permissions.require_review_command(self.hrmd_need(), user)
			self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")
			self.assertEqual(permissions.require_review_read(self.hrmd_need(), user), "oversight")
			record = workspace.get_need(need=self.hrmd_need().name, user=user)
			self.assertEqual(record["access_profile"], "oversight")
			self.assertEqual([a["code"] for a in record["actions"]], ["view"])

	def test_the_workspace_offers_every_unit_and_lists_no_draft(self):
		for user in (AO, HOPF):
			self.assertTrue(permissions.viewing_contexts(user), user)
			listed = workspace.get_workspace(user=user)
			self.assertEqual(listed["outcome"], "READY")
			states = {n["status"] for n in listed["needs"]}
			self.assertTrue(states <= {STATE_SUBMITTED, STATE_ACCEPTED, STATE_NOT_TAKEN_FORWARD}, states)
			self.assertTrue(listed["needs"], user)

	def test_a_person_with_no_responsibility_is_unchanged(self):
		self.assertEqual(permissions.can_view(self.accepted_need(), NO_GRANT_USER), (False, "none"))


class TestOfficesOpenTheNeedThroughTheFrameworkRoutes(DepartmentalNeedsPermissionCase):
	"""KT-ACCESS-REV-001 AR-05 — the service layer already admitted the two offices; the Desk and REST
	routes (list, record, count) refused them because the DocType carried no read row for them. The row
	exists now; the reader hook still limits them to submitted and decided Needs, read-only."""

	def test_the_list_and_the_record_open_for_both_offices_in_oversight_states_only(self):
		submitted, accepted = self.hrmd_need(), self.accepted_need()
		for user in (AO, HOPF):
			with self.subTest(user=user):
				frappe.set_user(user)
				names = frappe.get_list("Departmental Need", pluck="name", limit_page_length=0)
				self.assertIn(submitted.name, names)
				self.assertIn(accepted.name, names)
				states = {row.current_state for row in frappe.get_list("Departmental Need", fields=["current_state"], limit_page_length=0)}
				self.assertTrue(states <= {STATE_SUBMITTED, STATE_ACCEPTED, STATE_NOT_TAKEN_FORWARD}, states)
				self.assertTrue(frappe.has_permission("Departmental Need", "read", doc=accepted.name, user=user))

	def test_the_grant_is_read_only_on_the_framework_routes(self):
		accepted = self.accepted_need()
		for user in (AO, HOPF):
			for ptype in ("write", "create", "delete", "submit"):
				self.assertFalse(frappe.has_permission("Departmental Need", ptype, doc=accepted.name, user=user), f"{user} {ptype}")

	def test_the_departments_other_records_stay_closed_to_the_offices(self):
		for user in (AO, HOPF):
			with self.subTest(user=user):
				frappe.set_user(user)
				for doctype in ("Departmental Need Revision", "Departmental Need Decision", "Departmental Need Review Task", "Need Withdrawal Request"):
					with self.assertRaises(frappe.PermissionError):
						frappe.get_list(doctype, limit_page_length=1)
