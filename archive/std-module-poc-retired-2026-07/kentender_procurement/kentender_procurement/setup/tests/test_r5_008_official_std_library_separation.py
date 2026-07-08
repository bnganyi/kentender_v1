# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-008 / LV-R5-008-01 — Official STD Library remains separated from Tender Management spine.

Companion evidence: docs/prompts/0. usability handoff/R5_008_official_STD_library_separation_evidence.md
"""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase


def _sidebar_export_rows() -> list:
	path = os.path.join(
		frappe.get_app_path("kentender_procurement"),
		"workspace_sidebar",
		"procurement.json",
	)
	with open(path, encoding="utf-8") as f:
		data = json.load(f)
	return list(data.get("items") or [])


class TestR5008OfficialStdLibrarySeparation(IntegrationTestCase):
	def test_sidebar_official_std_library_targets_std_engine_page(self):
		items = _sidebar_export_rows()
		found = False
		for row in items:
			if row.get("type") != "Link":
				continue
			if row.get("label") != "Official STD Library":
				continue
			found = True
			self.assertEqual((row.get("link_type") or "").lower(), "page")
			self.assertEqual(row.get("link_to"), "std-engine")
		self.assertTrue(found, msg="Missing Official STD Library row in procurement.json sidebar export")

	def test_sidebar_governance_workspace_distinct_from_official_library(self):
		items = _sidebar_export_rows()
		by_label = {
			row.get("label"): row for row in items if row.get("type") == "Link" and row.get("label")
		}
		lib_row = by_label.get("Official STD Library")
		gov_row = by_label.get("Governance & Configuration")
		tm_row = by_label.get("Tender Management")
		self.assertIsNotNone(lib_row)
		self.assertIsNotNone(gov_row)
		self.assertIsNotNone(tm_row)
		self.assertEqual((gov_row.get("link_type") or "").lower(), "workspace")
		self.assertEqual(gov_row.get("link_to"), "Governance & Configuration")
		tm_lt = (tm_row.get("link_type") or "").lower()
		self.assertNotEqual(tm_lt, "")
		self.assertEqual(tm_row.get("link_to"), "tender-management-v2")
		self.assertNotEqual(tm_row.get("link_to"), "std-engine")
		self.assertNotEqual(lib_row.get("link_to"), tm_row.get("link_to"))

	def test_installed_procurement_sidebar_row_std_engine_matches_export(self):
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		doc = frappe.get_doc("Workspace Sidebar", "Procurement")
		matches = [
			r
			for r in doc.items
			if r.type == "Link"
			and r.label == "Official STD Library"
			and (r.link_type or "").lower() == "page"
			and r.link_to == "std-engine"
		]
		self.assertEqual(
			len(matches),
			1,
			msg="Desk sidebar must expose exactly one Official STD Library→std-engine page link",
		)
