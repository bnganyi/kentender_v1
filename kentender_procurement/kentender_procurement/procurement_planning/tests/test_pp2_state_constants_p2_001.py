# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-001 — PP2 package state constants, transitions, and workbench grouping."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_ALLOWED_TRANSITIONS,
	PKG_APPROVED,
	PKG_CANCELLED,
	PKG_CONSUMED,
	PKG_DRAFT,
	PKG_EDITABLE_STATUSES,
	PKG_IN_REVIEW,
	PKG_LIMITED_EDIT_STATUSES,
	PKG_LOCKED_STATUSES,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	PKG_RETURNED,
	PKG_STATUS_ORDER,
	PKG_SUPERSEDED,
	PKG_TERMINAL_STATUSES,
	PKG_TRANSITIONS_REQUIRING_REASON,
	PKG_VALID_STATUSES,
	PKG_WORKBENCH_GROUP,
	WB_APPROVED,
	WB_CONSUMED,
	WB_HANDED_OFF,
	WB_HISTORICAL,
	WB_IN_PREPARATION,
	WB_NEEDS_MY_ACTION,
	WB_NEEDS_REVIEW,
	WB_READY_FOR_HANDOFF,
	is_allowed_pkg_transition,
	is_valid_pkg_status,
	pkg_allows_ordinary_edit,
	pkg_is_terminal,
	pkg_transition_requires_reason,
	pkg_workbench_group,
)


class TestPP2StateConstantsP2001(IntegrationTestCase):
	"""Exhaustive P2-001 constant and helper coverage."""

	def test_golden_status_order_matches_governance(self):
		self.assertEqual(
			PKG_STATUS_ORDER,
			(
				"Draft",
				"In Review",
				"Returned for Correction",
				"Approved",
				"Ready for Release",
				"Released to Tender",
				"Consumed by Tender Management",
				"Superseded",
				"Cancelled",
			),
		)
		self.assertEqual(set(PKG_STATUS_ORDER), PKG_VALID_STATUSES)

	def test_workbench_group_covers_all_statuses(self):
		self.assertEqual(set(PKG_WORKBENCH_GROUP.keys()), PKG_VALID_STATUSES)
		expected = {
			PKG_DRAFT: WB_IN_PREPARATION,
			PKG_IN_REVIEW: WB_NEEDS_REVIEW,
			PKG_RETURNED: WB_NEEDS_MY_ACTION,
			PKG_APPROVED: WB_APPROVED,
			PKG_READY_FOR_RELEASE: WB_READY_FOR_HANDOFF,
			PKG_RELEASED: WB_HANDED_OFF,
			PKG_CONSUMED: WB_CONSUMED,
			PKG_SUPERSEDED: WB_HISTORICAL,
			PKG_CANCELLED: WB_HISTORICAL,
		}
		for status, bucket in expected.items():
			with self.subTest(status=status):
				self.assertEqual(pkg_workbench_group(status), bucket)

	def test_transition_graph_complete_and_valid(self):
		self.assertEqual(set(PKG_ALLOWED_TRANSITIONS.keys()), PKG_VALID_STATUSES)
		for old, targets in PKG_ALLOWED_TRANSITIONS.items():
			with self.subTest(old=old):
				for new in targets:
					self.assertIn(new, PKG_VALID_STATUSES)
		self.assertEqual(PKG_ALLOWED_TRANSITIONS[PKG_SUPERSEDED], ())
		self.assertEqual(PKG_ALLOWED_TRANSITIONS[PKG_CANCELLED], ())

	def test_terminal_and_edit_sets(self):
		self.assertEqual(PKG_TERMINAL_STATUSES, frozenset((PKG_SUPERSEDED, PKG_CANCELLED)))
		self.assertEqual(PKG_LIMITED_EDIT_STATUSES, frozenset((PKG_APPROVED,)))
		self.assertTrue(PKG_EDITABLE_STATUSES <= PKG_VALID_STATUSES)
		self.assertFalse(PKG_EDITABLE_STATUSES & PKG_LOCKED_STATUSES)
		for st in PKG_EDITABLE_STATUSES:
			self.assertTrue(pkg_allows_ordinary_edit(st))
		for st in PKG_TERMINAL_STATUSES:
			self.assertTrue(pkg_is_terminal(st))

	def test_transition_helpers(self):
		self.assertTrue(is_valid_pkg_status(PKG_IN_REVIEW))
		self.assertFalse(is_valid_pkg_status("Submitted"))
		self.assertTrue(is_allowed_pkg_transition(PKG_DRAFT, PKG_IN_REVIEW))
		self.assertFalse(is_allowed_pkg_transition(PKG_DRAFT, PKG_APPROVED))
		self.assertTrue(pkg_transition_requires_reason(PKG_IN_REVIEW, PKG_RETURNED))
		self.assertFalse(pkg_transition_requires_reason(PKG_DRAFT, PKG_IN_REVIEW))
		for pair in PKG_TRANSITIONS_REQUIRING_REASON:
			self.assertTrue(pkg_transition_requires_reason(pair[0], pair[1]))

	def test_doctype_select_options_match_constants(self):
		meta = frappe.get_meta("Procurement Package")
		status_df = meta.get_field("status")
		options = {o.strip() for o in (status_df.options or "").split("\n") if o.strip()}
		self.assertEqual(options, set(PKG_VALID_STATUSES))
