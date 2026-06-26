# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-008 — Old five-screen nav entries absent from PP3 Planning IA."""

from __future__ import annotations

import json
import re
from pathlib import Path

import frappe
from frappe.tests import UnitTestCase

from kentender_procurement.procurement_planning.tests.pp8_gate_constants import (
	P8_FORBIDDEN_NAV_HREF_SUBSTRINGS,
)

_ALLOWED_PP4_URLS = frozenset({"/desk/procurement-planning"})

_LEGACY_NAV_LABELS_IN_QUEUE_TABS = (
	"Planning Home",
	"Approved Demands",
	"Planning Evidence",
	"Procurement Packages",
)


class TestPP8NavigationNegativeP8008(UnitTestCase):
	def _router_source(self) -> str:
		path = Path(frappe.get_app_path("kentender_procurement")) / "public" / "js" / "pp2_planning_router.js"
		return path.read_text(encoding="utf-8", errors="replace")

	def test_pp8_008_sidebar_has_single_planning_workbench_link(self) -> None:
		path = Path(frappe.get_app_path("kentender_procurement")) / "workspace_sidebar" / "procurement.json"
		data = json.loads(path.read_text(encoding="utf-8"))
		rows = [
			row
			for row in data.get("items") or []
			if row.get("type") == "Link" and (row.get("label") or "") == "Planning Workbench"
		]
		labels = tuple(row.get("label") or "" for row in rows)
		self.assertEqual(labels, ("Planning Workbench",))
		urls = [(row.get("url") or "").strip() for row in rows]
		for url in urls:
			self.assertIn(url, _ALLOWED_PP4_URLS)

	def test_pp8_008_router_forbids_legacy_nav_labels_and_hrefs(self) -> None:
		source = self._router_source()
		self.assertIn("FORBIDDEN_PLANNING_NAV_LABELS", source)
		self.assertIn("FORBIDDEN_PLANNING_HREF_SUBSTRINGS", source)
		self.assertRegex(source, r'["\']approved demands["\']\s*:\s*true')
		self.assertIn("packages: true", source)
		for href in P8_FORBIDDEN_NAV_HREF_SUBSTRINGS:
			self.assertIn(href, source, msg=f"missing forbidden href guard for {href}")

	def test_pp8_008_workbench_queue_tabs_exclude_legacy_surfaces(self) -> None:
		path = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "public"
			/ "js"
			/ "pp3_planning_workbench_queue_tabs.js"
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		for label in _LEGACY_NAV_LABELS_IN_QUEUE_TABS:
			self.assertNotIn(label, source, msg=f"legacy label {label!r} in queue tabs")

	def test_pp8_008_legacy_top_level_routes_redirect_to_workbench(self) -> None:
		source = self._router_source()
		for legacy in ("approved-demands", "packages", "home", "plans", "releases"):
			self.assertIn(f'head === "{legacy}"', source, msg=f"missing redirect guard for {legacy}")
			self.assertIn('action: "redirect"', source)
