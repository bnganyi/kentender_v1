# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-008 / LV-R1-008-01 — handoff card status **StrEnum** + transition graph tests."""

from __future__ import annotations

import unittest

from kentender_procurement.procurement_lifecycle.handoff_card_status import HANDOFF_CARD_STATUS_VALUES
from kentender_procurement.procurement_lifecycle.handoff_card_transitions import (
	ALLOWED_HANDOFF_STATUS_TRANSITIONS,
	HandoffCardStatus,
	allowed_next_handoff_statuses,
	assert_transition_graph_well_formed,
	assert_valid_handoff_status_transition,
	can_handoff_status_transition,
)


class TestR1008StrEnumMatchesVocabulary(unittest.TestCase):
	def test_enum_values_exhaustive(self):
		enum_vals = {e.value for e in HandoffCardStatus}
		self.assertEqual(enum_vals, set(HANDOFF_CARD_STATUS_VALUES))
		self.assertEqual(len(HandoffCardStatus), 10)


class TestR1008TransitionGraphIntegrity(unittest.TestCase):
	def test_graph_well_formed(self):
		assert_transition_graph_well_formed()

	def test_every_status_is_source_key(self):
		self.assertSetEqual(set(ALLOWED_HANDOFF_STATUS_TRANSITIONS), set(HANDOFF_CARD_STATUS_VALUES))


class TestR1008HappyPath(unittest.TestCase):
	def test_draft_ready_handed_off_consumed(self):
		for a, b in (
			("Draft", "Ready"),
			("Ready", "Handed Off"),
			("Handed Off", "Consumed"),
		):
			with self.subTest(a=a, b=b):
				assert_valid_handoff_status_transition(a, b)

	def test_noop_always_ok(self):
		for s in HANDOFF_CARD_STATUS_VALUES:
			with self.subTest(status=s):
				assert_valid_handoff_status_transition(s, s)


class TestR1008NegativePaths(unittest.TestCase):
	def test_draft_to_consumed_illegal(self):
		with self.assertRaises(ValueError):
			assert_valid_handoff_status_transition("Draft", "Consumed")

	def test_consumed_to_ready_illegal(self):
		with self.assertRaises(ValueError):
			assert_valid_handoff_status_transition("Consumed", "Ready")

	def test_cancelled_to_ready_illegal(self):
		with self.assertRaises(ValueError):
			assert_valid_handoff_status_transition("Cancelled", "Ready")

	def test_unknown_from_status(self):
		with self.assertRaises(ValueError):
			assert_valid_handoff_status_transition("Phantom", "Draft")

	def test_can_helper(self):
		self.assertTrue(can_handoff_status_transition("Draft", "Ready"))
		self.assertFalse(can_handoff_status_transition("Draft", "Consumed"))


class TestR1008AllowedNext(unittest.TestCase):
	def test_ready_next_includes_handed_off(self):
		self.assertIn("Handed Off", allowed_next_handoff_statuses("Ready"))

	def test_consumed_next_is_subset(self):
		self.assertEqual(allowed_next_handoff_statuses("Consumed"), frozenset({"Stale", "Audit Only"}))
