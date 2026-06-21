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
	"Plans",
	"Packages",
	"Released to Tender",
)

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
		"Procurement Plans",
		"Procurement Packages",
	}
)

_ALLOWED_PP2_CHILD_URLS: frozenset[str] = frozenset(
	{
		"/desk/procurement-planning",
		"/desk/procurement-planning/approved-demands",
		"/desk/procurement-planning/plans",
		"/desk/procurement-planning/packages",
		"/desk/procurement-planning/releases",
	}
)

_FORBIDDEN_PP2_CHILD_URL_SUBSTRINGS: tuple[str, ...] = (
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

	def test_nested_planning_child_links_exclude_evidence_route(self):
		path = os.path.join(frappe.get_app_path("kentender_procurement"), "workspace_sidebar", "procurement.json")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		child_rows = [
			row
			for row in data.get("items") or []
			if row.get("type") == "Link" and int(row.get("child") or 0) == 1 and int(row.get("indent") or 0) >= 1
		]
		evidence_urls = [
			(row.get("url") or "").strip()
			for row in child_rows
			if "/procurement-planning/evidence" in (row.get("url") or "").strip().lower()
		]
		self.assertFalse(
			evidence_urls,
			msg=f"Planning Evidence route must not appear in persistent Planning nav: {evidence_urls}",
		)

	def test_nested_planning_child_links_use_only_canonical_urls(self):
		path = os.path.join(frappe.get_app_path("kentender_procurement"), "workspace_sidebar", "procurement.json")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		child_rows = [
			row
			for row in data.get("items") or []
			if row.get("type") == "Link" and int(row.get("child") or 0) == 1 and int(row.get("indent") or 0) >= 1
		]
		urls = [(row.get("url") or "").strip() for row in child_rows]
		for url in urls:
			self.assertIn(
				url,
				_ALLOWED_PP2_CHILD_URLS,
				msg=f"Planning child link must use canonical surface URL, got {url!r}",
			)
		for url in urls:
			lower = url.lower()
			for forbidden in _FORBIDDEN_PP2_CHILD_URL_SUBSTRINGS:
				self.assertNotIn(
					forbidden,
					lower,
					msg=f"Forbidden detail route substring {forbidden!r} in Planning nav URL {url!r}",
				)

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
