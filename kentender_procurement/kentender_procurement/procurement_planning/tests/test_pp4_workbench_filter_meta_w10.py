# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""W10 — Planning Workbench filter-drawer option-list API contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.workbench_item import (
	get_pp_workbench_filter_meta,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP4WorkbenchFilterMetaW10(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._skip = not _pp_ok()

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_001_administrator_receives_full_option_lists(self):
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_pp_workbench_filter_meta()
		self.assertTrue(out.get("ok"), out)

		# Regression guard: department options must never surface the
		# `Procuring Department` doctype's raw hash id (autoname="hash") —
		# `value` and `label` are always the same human display text.
		for dept in out.get("departments") or []:
			self.assertEqual(dept.get("value"), dept.get("label"))
			self.assertTrue(dept.get("value"))
			self.assertNotRegex(str(dept.get("value")), r"^[a-z0-9]{10}$")

		category_values = {c.get("value") for c in out.get("categories") or []}
		self.assertEqual(category_values, {"Works", "Goods", "Services", "Consultancy"})

		value_range_keys = {v.get("value") for v in out.get("value_ranges") or []}
		self.assertEqual(value_range_keys, {"under_100m", "100m_500m", "over_500m"})

		sort_keys = {s.get("value") for s in out.get("sort_options") or []}
		self.assertEqual(
			sort_keys,
			{"newest", "oldest", "value_desc", "value_asc", "title_asc", "title_desc"},
		)

	def test_002_guest_denied(self):
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		out = get_pp_workbench_filter_meta()
		self.assertFalse(out.get("ok"))
