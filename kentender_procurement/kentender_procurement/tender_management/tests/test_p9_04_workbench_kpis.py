# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-04 — ``get_workbench_kpi_counts`` workbench KPI API (doc 9 §14.6).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_04_workbench_kpis
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.tm2_workbench import get_workbench_kpi_counts
from kentender_procurement.tender_management.services.tm2_workbench_kpis import (
	get_workbench_kpi_counts as get_workbench_kpi_counts_service,
)

_EXPECTED_KPIS = (
	"tm2-kpi-draft",
	"tm2-kpi-std-incomplete",
	"tm2-kpi-publication-review",
	"tm2-kpi-published",
	"tm2-kpi-closing-soon",
	"tm2-kpi-clarifications",
	"tm2-kpi-addenda",
	"tm2-kpi-opening-ready",
)


class TestP904WorkbenchKpis(IntegrationTestCase):
	def test_p9_04_service_counts_shape(self) -> None:
		frappe.set_user("Administrator")
		out = get_workbench_kpi_counts_service("Administrator")
		self.assertTrue(out.get("ok"))
		counts = out.get("counts") or {}
		for k in _EXPECTED_KPIS:
			self.assertIn(k, counts)
			self.assertIsInstance(counts[k], int)
			self.assertGreaterEqual(counts[k], 0)
		qc = out.get("queue_counts") or {}
		self.assertIsInstance(qc, dict)
		for _slug, n in qc.items():
			self.assertIsInstance(n, int)
			self.assertGreaterEqual(n, 0)

	def test_p9_04_whitelist_matches_service(self) -> None:
		frappe.set_user("Administrator")
		api_out = get_workbench_kpi_counts()
		svc_out = get_workbench_kpi_counts_service("Administrator")
		self.assertEqual(api_out.get("ok"), svc_out.get("ok"))
		self.assertEqual(api_out.get("counts"), svc_out.get("counts"))
		self.assertEqual(api_out.get("queue_counts"), svc_out.get("queue_counts"))
