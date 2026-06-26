# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-002 / PP4 nav IA — single Planning Workbench entry contract."""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

_EXPECTED_PLANNING_LABEL = "Planning Workbench"

_FORBIDDEN_PP2_LABELS: frozenset[str] = frozenset(
	{
		"Planning Evidence",
		"Procurement Plan Detail",
		"Planning Inclusion Detail",
		"Release Package Detail",
		"Readiness Review",
		"Review & Approval",
		"Package Lines",
		"Technical Details",
		"Audit Trail",
		"Planning Release Package",
		"Release to Tender Review",
		"Planning Release Package View",
		"Advanced / Technical Details",
		"Procurement Packages",
		"Planning Home",
		"Approved Demands",
		"Plans",
		"Packages",
	}
)

_ALLOWED_PLANNING_URL = "/desk/procurement-planning"

_FORBIDDEN_PP2_CHILD_URL_SUBSTRINGS: tuple[str, ...] = (
	"/procurement-planning/approved-demands",
	"/procurement-planning/evidence",
	"/procurement-planning/inclusions",
	"/procurement-planning/readiness",
	"/procurement-planning/review",
	"/procurement-planning/lines",
	"/procurement-planning/technical",
	"/procurement-planning/audit",
	"/procurement-planning/releases/",
)


class TestProcurementPlanningSidebarP5001Contract(IntegrationTestCase):
	def test_procurement_sidebar_has_single_planning_workbench_link(self):
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		self.assertTrue(os.path.isfile(path), msg=f"Missing sidebar export: {path}")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		items = data.get("items") or []
		planning_rows = [
			row
			for row in items
			if row.get("type") == "Link" and (row.get("label") or "") == _EXPECTED_PLANNING_LABEL
		]
		self.assertEqual(
			len(planning_rows),
			1,
			msg="Procurement rail must expose exactly one Planning Workbench link.",
		)
		row = planning_rows[0]
		self.assertEqual((row.get("link_to") or "").strip(), "Procurement Planning")
		self.assertEqual((row.get("url") or "").strip(), _ALLOWED_PLANNING_URL)
		self.assertEqual(int(row.get("child") or 0), 0)
		self.assertEqual(int(row.get("indent") or 0), 0)

	def test_planning_workbench_link_excludes_evidence_route(self):
		path = os.path.join(frappe.get_app_path("kentender_procurement"), "workspace_sidebar", "procurement.json")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		planning_rows = [
			row
			for row in data.get("items") or []
			if row.get("type") == "Link" and (row.get("label") or "") == _EXPECTED_PLANNING_LABEL
		]
		evidence_urls = [
			(row.get("url") or "").strip()
			for row in planning_rows
			if "/procurement-planning/evidence" in (row.get("url") or "").strip().lower()
		]
		self.assertFalse(
			evidence_urls,
			msg=f"Planning Evidence route must not appear in persistent Planning nav: {evidence_urls}",
		)

	def test_planning_workbench_link_uses_only_root_canonical_url(self):
		path = os.path.join(frappe.get_app_path("kentender_procurement"), "workspace_sidebar", "procurement.json")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		planning_rows = [
			row
			for row in data.get("items") or []
			if row.get("type") == "Link" and (row.get("label") or "") == _EXPECTED_PLANNING_LABEL
		]
		urls = [(row.get("url") or "").strip() for row in planning_rows]
		for url in urls:
			self.assertEqual(url, _ALLOWED_PLANNING_URL)
		for url in urls:
			lower = url.lower()
			for forbidden in _FORBIDDEN_PP2_CHILD_URL_SUBSTRINGS:
				self.assertNotIn(
					forbidden,
					lower,
					msg=f"Forbidden detail route substring {forbidden!r} in Planning nav URL {url!r}",
				)

	def test_planning_workbench_link_excludes_forbidden_labels(self):
		path = os.path.join(frappe.get_app_path("kentender_procurement"), "workspace_sidebar", "procurement.json")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		labels = {
			row.get("label") or ""
			for row in data.get("items") or []
			if row.get("type") == "Link" and (row.get("url") or "").strip().startswith("/desk/procurement-planning")
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
			if row.get("type") == "Link" and row.get("label") == _EXPECTED_PLANNING_LABEL
		]
		self.assertEqual(len(pp_links), 1)
		self.assertEqual((pp_links[0].get("link_to") or "").strip(), "Procurement Planning")
		self.assertEqual((pp_links[0].get("url") or "").strip(), _ALLOWED_PLANNING_URL)

	def test_pp2_planning_router_has_no_forbidden_implementation_copy(self):
		import re

		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"pp2_planning_router.js",
		)
		self.assertTrue(os.path.isfile(path), msg=f"Missing router asset: {path}")
		source = open(path, encoding="utf-8").read()
		translated = re.findall(r'__\(\s*"([^"]+)"\s*\)', source)
		translated += re.findall(r"__\(\s*'([^']+)'\s*\)", source)
		forbidden = (
			"shell baseline",
			"feature content deferred",
			"stub content",
			"P5 surfaces completed",
			"this will be implemented later",
			"technical placeholder",
			"Choose a planning workspace action",
			"Open a planning queue from the sidebar",
			"Canonical PP2 rendering is active",
		)
		hits = [
			text
			for text in translated
			if any(token.lower() in text.lower() for token in forbidden)
		]
		self.assertFalse(hits, msg=f"Forbidden implementation copy in router __() strings: {hits}")

	def test_pp2_planning_router_forbids_packages_as_persistent_nav(self):
		import re

		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"pp2_planning_router.js",
		)
		self.assertTrue(os.path.isfile(path), msg=f"Missing router asset: {path}")
		source = open(path, encoding="utf-8").read()
		labels_block = re.search(
			r"const\s+FORBIDDEN_PLANNING_NAV_LABELS\s*=\s*\{(?P<body>.*?)\}\s*;",
			source,
			re.DOTALL,
		)
		self.assertIsNotNone(
			labels_block,
			msg="FORBIDDEN_PLANNING_NAV_LABELS block missing in pp2_planning_router.js",
		)
		label_body = labels_block.group("body")
		self.assertTrue(
			'"packages": true' in label_body or "packages: true" in label_body,
			msg="Packages must be explicitly forbidden as ordinary persistent Planning nav label (P1-005).",
		)
		hrefs_block = re.search(
			r"const\s+FORBIDDEN_PLANNING_HREF_SUBSTRINGS\s*=\s*\[(?P<body>.*?)\]\s*;",
			source,
			re.DOTALL,
		)
		self.assertIsNotNone(
			hrefs_block,
			msg="FORBIDDEN_PLANNING_HREF_SUBSTRINGS block missing in pp2_planning_router.js",
		)
		self.assertIn(
			'"/procurement-planning/packages"',
			hrefs_block.group("body"),
			msg="Packages route must be explicitly forbidden as ordinary persistent Planning nav href (P1-005).",
		)

	def test_pp2_planning_router_forbids_planning_evidence_as_persistent_nav(self):
		import re

		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"pp2_planning_router.js",
		)
		self.assertTrue(os.path.isfile(path), msg=f"Missing router asset: {path}")
		source = open(path, encoding="utf-8").read()
		labels_block = re.search(
			r"const\s+FORBIDDEN_PLANNING_NAV_LABELS\s*=\s*\{(?P<body>.*?)\}\s*;",
			source,
			re.DOTALL,
		)
		self.assertIsNotNone(
			labels_block,
			msg="FORBIDDEN_PLANNING_NAV_LABELS block missing in pp2_planning_router.js",
		)
		label_body = labels_block.group("body")
		self.assertTrue(
			'"planning evidence": true' in label_body or "planning evidence: true" in label_body,
			msg="Planning Evidence must be explicitly forbidden as ordinary persistent Planning nav label (P1-006).",
		)
		hrefs_block = re.search(
			r"const\s+FORBIDDEN_PLANNING_HREF_SUBSTRINGS\s*=\s*\[(?P<body>.*?)\]\s*;",
			source,
			re.DOTALL,
		)
		self.assertIsNotNone(
			hrefs_block,
			msg="FORBIDDEN_PLANNING_HREF_SUBSTRINGS block missing in pp2_planning_router.js",
		)
		self.assertIn(
			'"/procurement-planning/evidence"',
			hrefs_block.group("body"),
			msg="Planning Evidence route must be explicitly forbidden as ordinary persistent Planning nav href (P1-006).",
		)
		self.assertIn(
			"isForbiddenPlanningNavLink",
			source,
			msg="Router must keep stale sidebar guard function for planning evidence links.",
		)
