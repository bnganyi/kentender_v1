# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-001 / PP2-SMOKE-UI-002 — Procurement rail nested Planning contract."""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

_EXPECTED_PP2_CHILD_LABELS: tuple[str, ...] = (
	"Planning Home",
	"Approved Demands",
	"Packages",
	"Released to Tender",
	"Planning Evidence",
)

_FORBIDDEN_PP2_LABELS: frozenset[str] = frozenset(
	{
		"Procurement Plan Detail",
		"Planning Inclusion Detail",
		"Readiness Review",
		"Review & Approval",
		"Release to Tender Review",
		"Planning Release Package View",
		"Advanced / Technical Details",
		"Procurement Plans",
		"Procurement Packages",
	}
)


class TestProcurementPlanningSidebarP5001Contract(IntegrationTestCase):
	def test_procurement_sidebar_has_nested_planning_parent_and_five_children(self):
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		self.assertTrue(os.path.isfile(path), msg=f"Missing sidebar export: {path}")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		items = data.get("items") or []
		pp_parent = None
		for row in items:
			if row.get("type") == "Section Break" and row.get("label") == "Procurement Planning":
				pp_parent = row
				break
		self.assertIsNotNone(pp_parent, msg="Procurement rail must include Procurement Planning parent.")
		self.assertTrue(int(pp_parent.get("collapsible") or 0) == 1)
		self.assertTrue(int(pp_parent.get("show_arrow") or 0) == 0)

		child_rows = [
			row
			for row in items
			if row.get("type") == "Link" and int(row.get("child") or 0) == 1 and int(row.get("indent") or 0) >= 1
		]
		labels = tuple(row.get("label") or "" for row in child_rows)
		self.assertEqual(
			labels,
			_EXPECTED_PP2_CHILD_LABELS,
			msg="Procurement Planning parent must expose exactly five child surface links.",
		)
		for row in child_rows:
			self.assertEqual(
				(row.get("link_to") or "").strip(),
				"Procurement Planning",
				msg=f"Nested link {row.get('label')!r} must stay in Procurement Planning workspace shell.",
			)
			url = (row.get("url") or "").strip()
			self.assertTrue(url.startswith("/desk/procurement-planning"))

	def test_nested_planning_links_exclude_forbidden_labels(self):
		path = os.path.join(frappe.get_app_path("kentender_procurement"), "workspace_sidebar", "procurement.json")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		labels = {
			row.get("label") or ""
			for row in data.get("items") or []
			if row.get("type") == "Link" and int(row.get("child") or 0) == 1 and int(row.get("indent") or 0) >= 1
		}
		forbidden = labels & _FORBIDDEN_PP2_LABELS
		self.assertFalse(
			forbidden,
			msg=f"Forbidden permanent Planning nav labels present: {sorted(forbidden)}",
		)

	def test_procurement_rail_entry_targets_planning_workspace(self):
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		pp_links = [
			row
			for row in data.get("items") or []
			if row.get("type") == "Section Break" and row.get("label") == "Procurement Planning"
		]
		self.assertEqual(len(pp_links), 1)
		self.assertTrue(int(pp_links[0].get("collapsible") or 0) == 1)
