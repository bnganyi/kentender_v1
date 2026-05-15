# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-002 / LV-R1-002-01 — config load; LV-R1-002-02 — spine contract (keys, fields, order)."""

from __future__ import annotations

import unittest

from kentender_procurement.procurement_lifecycle.constants import (
	JOURNEY_STEP_CONFIG,
	JOURNEY_STEP_CONFIG_VERSION,
	JOURNEY_STEP_KEYS_IN_ORDER,
	JourneyStepConfig,
	get_journey_step_config,
	iter_journey_step_configs,
)
from kentender_procurement.procurement_lifecycle.journey_status_category import (
	ProcurementJourneyStatusCategory,
)


_CANONICAL_STEP_KEYS: tuple[str, ...] = (
	"strategy",
	"budget",
	"demand_captured",
	"demand_approved",
	"procurement_planned",
	"package_prepared",
	"package_released",
	"std_readiness",
	"tender_published",
	"tender_closed",
	"opening_ready",
	"opening_complete",
	"award_approved",
	"contract_handoff",
)


_CANONICAL_LABELS: tuple[str, ...] = (
	"Strategic Priority",
	"Funding Available",
	"Need Captured",
	"Need Approved",
	"Procurement Planned",
	"Package Prepared",
	"Package Released",
	"Tender Document Ready",
	"Tender Published",
	"Tender Closed",
	"Opening Ready",
	"Opening Complete",
	"Award Approved",
	"Contract Handoff",
)


class TestR1002ConfigLoad(unittest.TestCase):
	"""LV-R1-002-01 — versioned config loads and matches spine cardinality."""

	def test_version_is_positive_int(self):
		self.assertIsInstance(JOURNEY_STEP_CONFIG_VERSION, int)
		self.assertGreaterEqual(JOURNEY_STEP_CONFIG_VERSION, 1)

	def test_config_tuple_length_matches_pack_spine(self):
		self.assertEqual(len(JOURNEY_STEP_CONFIG), 14)
		self.assertEqual(JOURNEY_STEP_KEYS_IN_ORDER, _CANONICAL_STEP_KEYS)
		self.assertEqual(tuple(iter_journey_step_configs()), JOURNEY_STEP_CONFIG)

	def test_labels_match_rectification_pack_table_6_2(self):
		self.assertEqual(tuple(c.label for c in JOURNEY_STEP_CONFIG), _CANONICAL_LABELS)

	def test_step_keys_unique(self):
		keys = [c.step_key for c in JOURNEY_STEP_CONFIG]
		self.assertEqual(len(keys), len(set(keys)))

	def test_get_by_key_roundtrip(self):
		for key in _CANONICAL_STEP_KEYS:
			cfg = get_journey_step_config(key)
			self.assertEqual(cfg.step_key, key)

	def test_unknown_step_key_raises(self):
		with self.assertRaises(KeyError):
			get_journey_step_config("nonexistent_step")


class TestR1002StepContract(unittest.TestCase):
	"""LV-R1-002-02 — every step has owner module, handoff title, object type, valid status."""

	def _non_empty(self, s: str) -> bool:
		return bool(s and s.strip())

	def test_each_row_contract(self):
		for cfg in JOURNEY_STEP_CONFIG:
			with self.subTest(step_key=cfg.step_key):
				self.assertIsInstance(cfg, JourneyStepConfig)
				self.assertTrue(self._non_empty(cfg.step_key))
				self.assertTrue(self._non_empty(cfg.label))
				self.assertTrue(self._non_empty(cfg.owner_module))
				self.assertTrue(self._non_empty(cfg.source_object_type))
				self.assertTrue(self._non_empty(cfg.handoff_title))
				self.assertIsInstance(cfg.standard_status_category, ProcurementJourneyStatusCategory)

	def test_standard_status_is_pack_vocabulary(self):
		for cfg in JOURNEY_STEP_CONFIG:
			with self.subTest(step_key=cfg.step_key):
				self.assertIn(cfg.standard_status_category, ProcurementJourneyStatusCategory)

	def test_pack_row_7_handoff_and_object(self):
		cfg = get_journey_step_config("package_released")
		self.assertEqual(cfg.handoff_title, "Planning Release Package")
		self.assertEqual(cfg.source_object_type, "Procurement Package")
		self.assertIs(cfg.standard_status_category, ProcurementJourneyStatusCategory.HANDED_OFF)

	def test_pack_row_1_strategy_alignment_reference(self):
		cfg = get_journey_step_config("strategy")
		self.assertEqual(cfg.handoff_title, "Strategy Alignment Reference")
		self.assertIn("Strategic Plan", cfg.source_object_type)
