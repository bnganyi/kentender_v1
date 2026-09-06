# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-002 / PP4 nav IA — single Planning entry contract.

PLN-CHG-001 v1.2 Phase 3: the decommission ended. The rail's one Planning
entry is "Procurement Planning" → the v1.2 Vue-in-Desk Page
("procurement-planning"); §10 forbids any further Planning sidebar entry
(work queues arrive through My Work and notifications, never the rail).
"""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

_EXPECTED_PLANNING_LABEL = "Procurement Planning"

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


def _load_items() -> list[dict]:
	path = os.path.join(
		frappe.get_app_path("kentender_procurement"),
		"workspace_sidebar",
		"procurement.json",
	)
	with open(path, encoding="utf-8") as f:
		data = json.load(f)
	return data.get("items") or []


class TestProcurementPlanningSidebarP5001Contract(IntegrationTestCase):
	def test_procurement_sidebar_has_single_planning_workbench_link(self):
		items = _load_items()
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
		self.assertEqual((row.get("link_to") or "").strip(), "procurement-planning")
		self.assertEqual((row.get("link_type") or "").strip(), "Page")
		self.assertFalse(row.get("route_options"))
		self.assertEqual(int(row.get("child") or 0), 0)
		self.assertEqual(int(row.get("indent") or 0), 0)

	def test_planning_workbench_link_excludes_evidence_route(self):
		planning_rows = [
			row
			for row in _load_items()
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

	def test_planning_workbench_link_has_no_forbidden_child_url(self):
		"""Decommissioned entry carries no `url` at all; guard survives if one is ever restored."""
		planning_rows = [
			row
			for row in _load_items()
			if row.get("type") == "Link" and (row.get("label") or "") == _EXPECTED_PLANNING_LABEL
		]
		for row in planning_rows:
			url = (row.get("url") or "").strip().lower()
			for forbidden in _FORBIDDEN_PP2_CHILD_URL_SUBSTRINGS:
				self.assertNotIn(
					forbidden,
					url,
					msg=f"Forbidden detail route substring {forbidden!r} in Planning nav URL {url!r}",
				)

	def test_planning_workbench_link_excludes_forbidden_labels(self):
		labels = {row.get("label") or "" for row in _load_items() if row.get("type") == "Link"}
		forbidden = labels & _FORBIDDEN_PP2_LABELS
		self.assertFalse(
			forbidden,
			msg=f"Forbidden permanent Planning nav labels present: {sorted(forbidden)}",
		)

	def test_procurement_rail_entry_routes_to_the_v12_page(self):
		pp_links = [
			row
			for row in _load_items()
			if row.get("type") == "Link" and row.get("label") == _EXPECTED_PLANNING_LABEL
		]
		self.assertEqual(len(pp_links), 1)
		self.assertEqual((pp_links[0].get("link_to") or "").strip(), "procurement-planning")

	def test_pp2_planning_router_removed(self):
		"""PP2 retirement — legacy router asset must not remain on disk."""
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"pp2_planning_router.js",
		)
		self.assertFalse(os.path.isfile(path), msg=f"Legacy PP2 router must be deleted: {path}")
