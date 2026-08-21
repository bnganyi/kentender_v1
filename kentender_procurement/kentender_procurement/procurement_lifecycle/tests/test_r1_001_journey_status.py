# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-001 / LV-R1-001-01 — enum exhaustiveness; LV-R1-001-02 — procurement package golden mapping."""

from __future__ import annotations

import unittest
from enum import StrEnum

# Historical PP2 Package status strings (DocType retired).
PKG_APPROVED = "Approved"
PKG_CANCELLED = "Cancelled"
PKG_CONSUMED = "Consumed"
PKG_DRAFT = "Draft"
PKG_IN_REVIEW = "In Review"
PKG_READY_FOR_RELEASE = "Ready for Release"
PKG_RELEASED = "Released"
PKG_RETURNED = "Returned"

from kentender_procurement.procurement_lifecycle import (
	JOURNEY_STATUS_CATEGORY_VALUES,
	ProcurementJourneyStatusCategory,
	is_valid_journey_status_category,
	map_raw_to_journey_status_category,
)


_PACK_CANONICAL_VALUES: frozenset[str] = frozenset(
	{
		"Not Started",
		"In Progress",
		"Needs Action",
		"Blocked",
		"Ready for Handoff",
		"Handed Off",
		"Completed",
		"Returned",
		"Cancelled",
		"Superseded",
		"Audit Only",
		"Stale",
	}
)


class TestR1001EnumExhaustive(unittest.TestCase):
	"""LV-R1-001-01 — exhaustive membership and stable vocabulary."""

	def test_enum_is_strenum_with_twelve_members(self):
		self.assertTrue(issubclass(ProcurementJourneyStatusCategory, StrEnum))
		self.assertEqual(len(ProcurementJourneyStatusCategory), 12)

	def test_all_values_unique_and_match_pack(self):
		values = [m.value for m in ProcurementJourneyStatusCategory]
		self.assertEqual(len(values), len(set(values)))
		self.assertEqual(frozenset(values), _PACK_CANONICAL_VALUES)
		self.assertEqual(JOURNEY_STATUS_CATEGORY_VALUES, _PACK_CANONICAL_VALUES)

	def test_is_valid_helper(self):
		self.assertTrue(is_valid_journey_status_category("Handed Off"))
		self.assertFalse(is_valid_journey_status_category("handed off"))
		self.assertFalse(is_valid_journey_status_category(""))


class TestR1001MappingGolden(unittest.TestCase):
	"""LV-R1-001-02 — golden raw → category for Procurement Package."""

	def _map_pkg(self, raw: str) -> ProcurementJourneyStatusCategory:
		return map_raw_to_journey_status_category(module_key="procurement_package", raw_status=raw)

	def test_procurement_package_statuses(self):
		cases = {
			PKG_DRAFT: ProcurementJourneyStatusCategory.NOT_STARTED,
			PKG_IN_REVIEW: ProcurementJourneyStatusCategory.NEEDS_ACTION,
			PKG_APPROVED: ProcurementJourneyStatusCategory.IN_PROGRESS,
			PKG_READY_FOR_RELEASE: ProcurementJourneyStatusCategory.IN_PROGRESS,
			PKG_RELEASED: ProcurementJourneyStatusCategory.HANDED_OFF,
			PKG_RETURNED: ProcurementJourneyStatusCategory.RETURNED,
			PKG_CANCELLED: ProcurementJourneyStatusCategory.CANCELLED,
			PKG_CONSUMED: ProcurementJourneyStatusCategory.COMPLETED,
		}
		for raw, expected in cases.items():
			with self.subTest(raw=raw):
				self.assertIs(self._map_pkg(raw), expected)

	def test_released_to_tender_alias_from_pack(self):
		self.assertIs(
			self._map_pkg("RELEASED_TO_TENDER"),
			ProcurementJourneyStatusCategory.HANDED_OFF,
		)

	def test_unknown_module_key_raises(self):
		with self.assertRaises(ValueError):
			map_raw_to_journey_status_category(module_key="demand_request", raw_status=PKG_DRAFT)

	def test_unknown_status_raises(self):
		with self.assertRaises(ValueError):
			self._map_pkg("Phantom")

	def test_empty_raw_raises(self):
		with self.assertRaises(ValueError):
			self._map_pkg("")
		with self.assertRaises(ValueError):
			self._map_pkg("   ")
