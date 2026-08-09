# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SCH-* — MVP-1 Planning DocTypes and status vocabularies present."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOCATION_STATUSES,
	ITEM_BASELINE_STATES,
	MVP1_DOCTYPES,
	PLAN_LIFECYCLE_STATES,
	VERSION_STATUSES,
)


class TestPlanningMvp1Schema(IntegrationTestCase):
	def test_all_mvp1_doctypes_exist(self) -> None:
		for dt in MVP1_DOCTYPES:
			self.assertTrue(frappe.db.exists("DocType", dt), msg=f"Missing DocType: {dt}")

	def test_plan_lifecycle_options(self) -> None:
		meta = frappe.get_meta("Procurement Plan")
		opts = set((meta.get_field("lifecycle_state").options or "").split("\n"))
		self.assertEqual(opts, set(PLAN_LIFECYCLE_STATES))
		self.assertIsNotNone(meta.get_field("financial_year"))
		self.assertIsNotNone(meta.get_field("current_approved_version"))
		self.assertIsNotNone(meta.get_field("open_draft_version"))
		self.assertIsNone(meta.get_field("submit_package_integrity_hash"))
		# PP2 status field removed
		self.assertTrue(
			meta.get_field("status") is None or meta.get_field("lifecycle_state") is not None
		)
		self.assertIsNone(meta.get_field("status"))

	def test_version_status_options(self) -> None:
		meta = frappe.get_meta("Procurement Plan Version")
		opts = set((meta.get_field("status").options or "").split("\n"))
		self.assertEqual(opts, set(VERSION_STATUSES))

	def test_item_and_allocation_options(self) -> None:
		item_opts = set(
			(frappe.get_meta("Procurement Plan Item").get_field("baseline_state").options or "").split(
				"\n"
			)
		)
		self.assertEqual(item_opts, set(ITEM_BASELINE_STATES))
		alloc_opts = set(
			(frappe.get_meta("Plan Demand Allocation").get_field("status").options or "").split("\n")
		)
		self.assertEqual(alloc_opts, set(ALLOCATION_STATUSES))

	def test_module_registry_points_at_plan(self) -> None:
		from kentender_core.module_registry import KT_MODULES

		mod = KT_MODULES.get("procurement_planning") or {}
		self.assertEqual(mod.get("form_doctype"), "Procurement Plan")
		self.assertEqual(mod.get("workspace_label"), "Procurement Planning")
