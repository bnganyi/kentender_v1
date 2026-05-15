# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-06 — ``list_workbench_tenders`` workbench list API (doc 9 §14.8 / §19.1).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_06_workbench_tender_list
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.tm2_workbench import list_workbench_tenders
from kentender_procurement.tender_management.services.tm2_workbench_tender_list import (
	list_workbench_tenders as list_workbench_tenders_service,
)


class TestP906WorkbenchTenderList(IntegrationTestCase):
	def test_p9_06_list_ok_shape(self) -> None:
		frappe.set_user("Administrator")
		out = list_workbench_tenders_service("Administrator", None, None, limit=5)
		self.assertTrue(out.get("ok"))
		self.assertIsInstance(out.get("items"), list)
		self.assertIn("counts", out)
		self.assertIsInstance(out["counts"], dict)
		for row in out["items"]:
			for key in (
				"tender_code",
				"tender_title",
				"package_code",
				"procuring_entity_code",
				"procurement_method",
				"procurement_category",
				"status",
				"std_readiness_status",
				"std_template_version_code",
				"blocker_count",
				"blocker_summary",
				"badges",
				"current_action_label",
			):
				self.assertIn(key, row)
			self.assertIsInstance(row.get("badges"), list)
			self.assertIsInstance(row.get("blocker_count"), int)

	def test_p9_06_unknown_queue(self) -> None:
		frappe.set_user("Administrator")
		out = list_workbench_tenders_service("Administrator", "not-a-real-queue", None, limit=5)
		self.assertFalse(out.get("ok"))
		self.assertIn("counts", out)
		self.assertIsInstance(out.get("counts"), dict)

	def test_p9_06_whitelist_matches_service(self) -> None:
		frappe.set_user("Administrator")
		api_out = list_workbench_tenders(queue="draft", search="", limit=10)
		svc_out = list_workbench_tenders_service("Administrator", "draft", "", limit=10)
		self.assertEqual(api_out.get("ok"), svc_out.get("ok"))
		self.assertEqual(len(api_out.get("items") or []), len(svc_out.get("items") or []))
		self.assertEqual(api_out.get("counts"), svc_out.get("counts"))
