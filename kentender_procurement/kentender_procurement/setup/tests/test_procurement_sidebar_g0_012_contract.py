# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-012 — Procurement Workspace Sidebar export matches lifecycle spine contract."""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

# Civic Ledger IA: Planned capability overviews + Available modules.
# Configuration is Disabled for deployment (omitted from export).
_EXPECTED_ITEM_LABELS: tuple[str, ...] = (
	"Home",
	"Analytics",
	"Strategy Alignment",
	"Budget & Funding",
	"Departmental Needs",
	"Procurement Plans",
	"Tender Management",
	"Tender Configurations",
	"Tenders",
	"Bid Submissions",
	"Evaluation",
	"Awards",
	"Contract Management",
	"Supplier Management",
	"STD Administration",
	"STD Library",
	"STD Versions",
	"Forms & Schemas",
	"Import Review",
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
		"""Tender Management + STD Administration Section-Break groups."""
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
						break
				elif started and int(row.get("child") or 0) == 1:
					collected.append(label)
				elif started:
					break
			return collected

		section_labels = {r.get("label") for r in items if r.get("type") == "Section Break"}
		self.assertIn("Tender Management", section_labels)
		self.assertIn("STD Administration", section_labels)
		self.assertNotIn("Configuration", section_labels)

		self.assertEqual(
			children_of("Tender Management"),
			[
				"Tender Configurations",
				"Tenders",
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
				"Import Review",
			],
		)

	def test_procurement_sidebar_home_routes_to_procurement_home_page(self):
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		home = next(r for r in data.get("items") or [] if r.get("label") == "Home")
		self.assertEqual(home.get("link_type"), "Page")
		self.assertEqual(home.get("link_to"), "kt-procurement-home")

	def test_procurement_sidebar_planned_items_route_to_coming_soon(self):
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		planned = {
			"Analytics",
			"Evaluation",
			"Awards",
			"Contract Management",
			"STD Versions",
			"Procurement Plans",
		}
		for row in data.get("items") or []:
			label = row.get("label") or ""
			if label == "Bid Submissions":
				self.assertEqual(row.get("link_type"), "Page")
				self.assertEqual(row.get("link_to"), "bid-submissions")
				continue
			if label not in planned:
				continue
			self.assertEqual(row.get("link_type"), "Page")
			self.assertEqual(row.get("link_to"), "coming-soon")
			self.assertIn(label, row.get("route_options") or "")

	def test_std_administration_has_no_url_hash_placeholders(self):
		"""URL/# links always open a new tab in Frappe — STD Admin must use Page routes."""
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		in_std = False
		for row in data.get("items") or []:
			if row.get("type") == "Section Break" and row.get("label") == "STD Administration":
				in_std = True
				continue
			if in_std and row.get("type") == "Section Break":
				break
			if not in_std or int(row.get("child") or 0) != 1:
				if in_std and row.get("type") == "Link" and int(row.get("child") or 0) != 1:
					break
				continue
			self.assertEqual(
				(row.get("link_type") or "").lower(),
				"page",
				msg=f"STD Administration child {row.get('label')!r} must be a Page link (not URL)",
			)
			self.assertNotEqual((row.get("url") or "").strip(), "#")

	def test_procurement_sidebar_drops_flat_spine_duplicates(self):
		"""Redundant / retired flat spine links must not reappear."""
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		labels = {row.get("label") for row in data.get("items") or []}
		for dropped in (
			"My Work",
			"Bid Opening",
			"Evaluation & Award",
			"Evidence & Audit",
			"Procurement Journeys",
			"Tender Management Hub",
			"Configuration",
			"Procurement Home",
			"Demand Intake & Approval",
			"Publications",
			"Import / Validation",
		):
			self.assertNotIn(dropped, labels, msg=f"{dropped!r} should not appear in current IA")

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

	def test_sidebar_setup_patch_shows_rail_after_desk_home(self):
		"""Desktop leaves the rail hidden; setup() must .show() it (first-open bug)."""
		header_js = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"procurement_sidebar_header.js",
		)
		home_js = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"procurement_home_page.js",
		)
		with open(header_js, encoding="utf-8") as f:
			header = f.read()
		with open(home_js, encoding="utf-8") as f:
			home = f.read()
		self.assertIn("patchSetupShowsRail", header)
		self.assertIn("wrapper.show()", header)
		self.assertIn("sidebar.wrapper.show()", home)
