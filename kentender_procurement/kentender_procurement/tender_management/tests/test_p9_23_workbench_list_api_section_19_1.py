# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-23 — workbench list contract vs doc 9 §19.1 (``items`` + ``counts``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_23_workbench_list_api_section_19_1
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.tm2_workbench import list_workbench_tenders
from kentender_procurement.tender_management.services.tm2_workbench_tender_list import (
	list_workbench_tenders as list_workbench_tenders_service,
	queue_counts_to_section_19_1,
)


class TestP923WorkbenchListApiSection191(IntegrationTestCase):
	def test_p9_23_section_19_1_top_level_keys(self) -> None:
		frappe.set_user("Administrator")
		out = list_workbench_tenders_service("Administrator", "draft", None, limit=5)
		self.assertTrue(out.get("ok"), out)
		self.assertIn("items", out)
		self.assertIn("counts", out)
		self.assertIsInstance(out["counts"], dict)
		for slug in (
			"draft",
			"std_incomplete",
			"ready_review",
			"returned",
			"approved",
			"published",
			"clarifications",
			"addenda",
			"closing_soon",
			"closed",
			"opening_ready",
			"evaluation_ready",
			"cancelled",
		):
			self.assertIn(slug, out["counts"], msg=f"missing §19.1 counts.{slug}")
			self.assertIsInstance(out["counts"][slug], int)

	def test_p9_23_item_row_keys_match_doc_19_1(self) -> None:
		frappe.set_user("Administrator")
		out = list_workbench_tenders_service("Administrator", "draft", None, limit=10)
		self.assertTrue(out.get("ok"), out)
		required = (
			"tender_code",
			"tender_title",
			"package_code",
			"procuring_entity_code",
			"procurement_method",
			"procurement_category",
			"status",
			"std_readiness_status",
			"std_template_version_code",
			"submission_deadline_at",
			"timezone",
			"badges",
			"blocker_count",
			"current_action_label",
		)
		items = out.get("items") or []
		if not items:
			self.skipTest("No draft tenders in environment for §19.1 row shape check")
		for row in items:
			for k in required:
				self.assertIn(k, row, msg=f"missing item.{k}")
			self.assertIsInstance(row.get("badges"), list)
			self.assertIsInstance(row.get("blocker_count"), int)
			self.assertEqual(row.get("current_action_label"), str(_("Draft")))

	def test_p9_23_whitelist_accepts_filters_param(self) -> None:
		frappe.set_user("Administrator")
		out = list_workbench_tenders(queue="draft", search="", limit=5, filters='{"reserved": true}')
		self.assertTrue(out.get("ok"), out)
		self.assertIn("counts", out)

	def test_p9_23_queue_counts_mapping_snake_case(self) -> None:
		raw = {"std-incomplete": 3, "ready-review": 1, "closing-soon": 0}
		m = queue_counts_to_section_19_1(raw)
		self.assertEqual(m.get("std_incomplete"), 3)
		self.assertEqual(m.get("ready_review"), 1)
		self.assertEqual(m.get("closing_soon"), 0)
