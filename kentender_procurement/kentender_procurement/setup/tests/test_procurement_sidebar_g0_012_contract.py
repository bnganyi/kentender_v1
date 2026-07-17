# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-012 — Procurement Workspace Sidebar export matches lifecycle spine contract."""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

# Civic Ledger IA (Step 1 native-sidebar restyle). Backbone follows the
# B-Components `code.html` spec (Analytics + Tender Management / STD Administration
# Section-Break groups); the canonical flat ``Planning`` link (P5-001) and the
# role-gated Configuration specialists (G0-014) are retained; the redundant flat
# spine links (My Work, Bid Opening, Evaluation & Award, Evidence & Audit,
# Tender Document Readiness) are dropped in favour of the grouped children.
_EXPECTED_ITEM_LABELS: tuple[str, ...] = (
	"Procurement Home",
	"Procurement Journeys",
	"Analytics",
	"Strategy Alignment",
	"Budget & Funding",
	"Demand Intake & Approval",
	"Planning",
	"Tender Management",
	"Procurement Packages",
	"Tender Configurations",
	"Tender Documents",
	"Publications",
	"Bid Submissions",
	"Evaluation",
	"Awards",
	"Contract Management",
	"Supplier Management",
	"STD Administration",
	"STD Library",
	"STD Versions",
	"Forms & Schemas",
	"Import / Validation",
	"Configuration",
	"Governance & Configuration",
	"Strategy Alignment (full)",
	"Budget & Funding (full)",
	"Procurement Templates",
	"Risk Profiles",
	"KPI Profiles",
	"Decision Criteria Profiles",
	"Vendor Management Profiles",
	"Procurement Plans",
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

	def test_procurement_sidebar_section_groups_and_children(self):
		"""Civic Ledger IA: Tender Management + STD Administration are Section-Break
		groups whose child rows immediately follow them in the exact spec order."""
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		items = data.get("items") or []

		def children_of(section_label: str) -> list[str]:
			collected: list[str] = []
			started = False
			for row in items:
				label = row.get("label") or ""
				if row.get("type") == "Section Break":
					if label == section_label:
						started = True
						continue
					if started:
						break  # next section ends the group
				elif started and int(row.get("child") or 0) == 1:
					collected.append(label)
				elif started:
					break  # a non-child top-level row ends the group
			return collected

		# both groups are Section Breaks
		section_labels = {r.get("label") for r in items if r.get("type") == "Section Break"}
		self.assertIn("Tender Management", section_labels)
		self.assertIn("STD Administration", section_labels)

		self.assertEqual(
			children_of("Tender Management"),
			[
				"Procurement Packages",
				"Tender Configurations",
				"Tender Documents",
				"Publications",
				"Bid Submissions",
				"Evaluation",
				"Awards",
			],
		)
		self.assertEqual(
			children_of("STD Administration"),
			[
				"STD Library",
				"STD Versions",
				"Forms & Schemas",
				"Import / Validation",
			],
		)

	def test_procurement_sidebar_drops_flat_spine_duplicates(self):
		"""Redundant flat spine links must not reappear as top-level rows."""
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		labels = {row.get("label") for row in data.get("items") or []}
		for dropped in ("My Work", "Bid Opening", "Evaluation & Award", "Evidence & Audit"):
			self.assertNotIn(dropped, labels, msg=f"{dropped!r} should be superseded by the grouped IA")

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
