# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-126 — post-sync patches must not touch tables an earlier patch dropped.

``pln_chg_001_v12_drop_legacy_planning_doctypes`` (pre_model_sync) drops the old
Procurement Plan tables. A site that is behind then reaches these post-sync patches,
where ``frappe.db.has_column`` / ``show index`` on a missing table raises
``TableMissingError`` and aborts the whole migrate. Each patch now returns quietly
when its table is gone, and stays safe to run twice.
"""

from __future__ import annotations

import importlib

import frappe
from frappe.tests import IntegrationTestCase

_PATCHES = (
	"kentender_procurement.patches.pln_revision_schema_backfill",
	"kentender_procurement.patches.pln_chg_016_schema_cleanup",
	"kentender_procurement.patches.scope_pln_formation_batch_key",
)
_DROPPED_TABLES = ("Procurement Plan", "Procurement Plan Version", "Procurement Plan Item", "Plan Demand Allocation")


class TestPatchesTolerateDroppedTables(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		missing = [t for t in _DROPPED_TABLES if frappe.db.table_exists(t)]
		if missing:
			self.skipTest(f"site still carries the legacy tables {missing}; scenario needs them dropped")

	def test_each_patch_is_a_no_op_when_its_tables_are_gone_and_safe_twice(self):
		for dotted in _PATCHES:
			module = importlib.import_module(dotted)
			with self.subTest(patch=dotted):
				module.execute()
				module.execute()
