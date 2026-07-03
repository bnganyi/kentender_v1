# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-010 — Workbench filter metadata API contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.workbench_filters import (
	get_pp_workbench_filter_metadata,
)
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	SUPPORTED_QUEUES,
	get_workbench_item_view_model,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP3WorkbenchFilterMetadataP3010(IntegrationTestCase):
	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_workbench_filter_metadata(queue="needs_planning")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_invalid_queue(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		out = get_pp_workbench_filter_metadata(queue="invalid_queue_key")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_INVALID_QUEUE")

	def test_facets_shape_for_non_empty_queue(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		target_queue = ""
		for queue in sorted(SUPPORTED_QUEUES):
			out = get_workbench_item_view_model(queue=queue, actor="Administrator", limit=5, start=0)
			if out.get("ok") and (out.get("total") or 0) > 0:
				target_queue = queue
				break
		if not target_queue:
			self.skipTest("No queue with rows available for facet contract test")

		meta = get_pp_workbench_filter_metadata(queue=target_queue)
		self.assertTrue(meta.get("ok"), msg=meta)
		self.assertEqual(meta.get("queue"), target_queue)
		self.assertIn("facets", meta)
		facets = meta.get("facets") or {}
		for key in ("departments", "categories", "value_ranges", "created_date_bounds", "sort_options"):
			self.assertIn(key, facets)
		self.assertEqual(len(facets.get("value_ranges") or []), 3)
		self.assertGreaterEqual(len(facets.get("sort_options") or []), 4)
