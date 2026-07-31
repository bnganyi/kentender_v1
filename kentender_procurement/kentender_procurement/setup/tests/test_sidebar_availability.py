# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Availability states are separate from authorization (menu badge + filter)."""

from __future__ import annotations

import unittest

from kentender_procurement.setup.sidebar_availability import (
	PLANNED_BADGE_SUFFIX,
	PLANNED_SIDEBAR_LABELS,
	apply_availability_to_sidebar_items,
)


class TestSidebarAvailability(unittest.TestCase):
	def test_planned_labels_get_badge_suffix(self):
		items = [{"label": label, "type": "Link"} for label in sorted(PLANNED_SIDEBAR_LABELS)]
		out = apply_availability_to_sidebar_items(items)
		self.assertEqual(len(out), len(PLANNED_SIDEBAR_LABELS))
		for row in out:
			self.assertEqual(row.get("suffix"), PLANNED_BADGE_SUFFIX)

	def test_disabled_configuration_labels_are_filtered(self):
		items = [
			{"label": "Demands", "type": "Link"},
			{"label": "Configuration", "type": "Section Break"},
			{"label": "Procurement Templates", "type": "Link"},
			{"label": "Strategy Alignment (full)", "type": "Link"},
		]
		out = apply_availability_to_sidebar_items(items)
		labels = [row["label"] for row in out]
		self.assertEqual(labels, ["Demands"])

	def test_available_labels_unchanged(self):
		items = [{"label": "Tenders", "type": "Link", "link_to": "publications"}]
		out = apply_availability_to_sidebar_items(items)
		self.assertEqual(out[0].get("suffix"), None)
		self.assertEqual(out[0]["label"], "Tenders")
