# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-UI-06 Source Demand funding labels must never leak internal IDs."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
	_funding_line_label,
	_is_internal_id,
)


class TestPlanItemEditorFundingLabel(FrappeTestCase):
	def test_internal_id_heuristic(self):
		self.assertTrue(_is_internal_id("v1l6o48g15"))
		self.assertTrue(_is_internal_id("85cjgmcemd"))
		self.assertFalse(_is_internal_id("RSV-MOH-0090"))
		self.assertFalse(_is_internal_id("Digital clinical systems infrastructure"))
		self.assertFalse(_is_internal_id(""))

	def test_funding_line_label_resolves_hash_reservation_to_budget_line_title(self):
		if not frappe.db.exists("Funding Reservation", "v1l6o48g15"):
			self.skipTest("Fixture reservation v1l6o48g15 not on site")
		label = _funding_line_label("v1l6o48g15")
		self.assertTrue(label)
		self.assertNotEqual(label, "v1l6o48g15")
		self.assertFalse(_is_internal_id(label))
		self.assertEqual(label, "Digital clinical systems infrastructure")

	def test_funding_line_label_accepts_generated_reference(self):
		if not frappe.db.exists(
			"Funding Reservation", {"generated_reference": "RSV-MOH-0090"}
		):
			self.skipTest("RSV-MOH-0090 not on site")
		label = _funding_line_label("RSV-MOH-0090")
		self.assertEqual(label, "Digital clinical systems infrastructure")
		self.assertFalse(_is_internal_id(label))

	def test_unknown_hash_returns_empty(self):
		self.assertEqual(_funding_line_label("zzzzzzzz99"), "")
