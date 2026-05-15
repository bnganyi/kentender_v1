# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-012 — Procurement Workspace Sidebar export matches lifecycle spine contract."""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

_EXPECTED_ITEM_LABELS: tuple[str, ...] = (
	"Procurement Home",
	"Procurement Journeys",
	"My Work",
	"Strategy Alignment",
	"Budget & Funding",
	"Demand Intake & Approval",
	"Procurement Planning",
	"Tender Document Readiness",
	"Tender Management",
	"Bid Opening",
	"Evaluation & Award",
	"Contract Management",
	"Supplier Management",
	"Evidence & Audit",
	"Configuration",
	"Official STD Library",
	"Governance & Configuration",
	"Strategy Alignment (full)",
	"Budget & Funding (full)",
	"Procurement Templates",
	"Risk Profiles",
	"KPI Profiles",
	"Decision Criteria Profiles",
	"Vendor Management Profiles",
	"Procurement Plans",
	"Procurement Packages",
)


class TestProcurementSidebarG012Contract(IntegrationTestCase):
	def test_procurement_sidebar_export_label_order(self):
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		self.assertTrue(os.path.isfile(path), msg=f"Missing sidebar export: {path}")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		items = data.get("items") or []
		labels = tuple(row.get("label") or "" for row in items)
		self.assertEqual(
			labels,
			_EXPECTED_ITEM_LABELS,
			msg="Update G0-012 evidence + Playwright if the spine contract changes intentionally.",
		)

	def test_procurement_sidebar_workspace_targets_exist_on_site(self):
		"""Soft gate: when the site has migrated, cross-check Workspace/Page names used by links."""
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		for row in data.get("items") or []:
			if row.get("type") != "Link":
				continue
			lt = (row.get("link_type") or "").lower()
			target = row.get("link_to")
			if not target:
				continue
			if lt == "workspace":
				self.assertTrue(
					frappe.db.exists("Workspace", target),
					msg=f"Sidebar links to missing Workspace: {target!r}",
				)
			elif lt == "page":
				self.assertTrue(
					frappe.db.exists("Page", target),
					msg=f"Sidebar links to missing Page: {target!r}",
				)
			elif lt == "doctype":
				self.assertTrue(
					frappe.db.exists("DocType", target),
					msg=f"Sidebar links to missing DocType: {target!r}",
				)
