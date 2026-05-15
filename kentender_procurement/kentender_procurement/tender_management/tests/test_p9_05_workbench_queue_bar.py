# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-05 — queue bar counts + ``tm2-queue-std-incomplete`` (doc 9 §14.7, doc 6 §8, doc 7 §28.2).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_05_workbench_queue_bar
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.tm2_workbench_kpis import (
	get_workbench_kpi_counts as get_workbench_kpi_counts_service,
)


_EXPECTED_QUEUE_SLUGS = (
	"draft",
	"std-incomplete",
	"ready-review",
	"returned",
	"approved",
	"published",
	"clarifications",
	"addenda",
	"closing-soon",
	"closed",
	"opening-ready",
	"evaluation-ready",
	"cancelled",
)


class TestP905WorkbenchQueueBar(IntegrationTestCase):
	def test_p9_05_queue_counts_keys(self) -> None:
		frappe.set_user("Administrator")
		out = get_workbench_kpi_counts_service("Administrator")
		self.assertTrue(out.get("ok"))
		qc = out.get("queue_counts") or {}
		for slug in _EXPECTED_QUEUE_SLUGS:
			self.assertIn(slug, qc)
			self.assertIsInstance(qc[slug], int)
			self.assertGreaterEqual(qc[slug], 0)

	def test_p9_05_std_incomplete_queue_matches_kpi(self) -> None:
		frappe.set_user("Administrator")
		out = get_workbench_kpi_counts_service("Administrator")
		self.assertEqual(
			out["queue_counts"]["std-incomplete"],
			out["counts"]["tm2-kpi-std-incomplete"],
		)
