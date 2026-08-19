# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-002 / PP4 nav IA — single Planning Workbench entry contract.

TEMPORARY DECOMMISSION (2026-08-19): Planning Home is broken against the
Demands doctypes deleted by the Departmental Needs greenfield rebuild
(RBD-3xx, deferred out of scope — see
docs/mvp-1-r1/01_departmental_needs/06_Departmental_Needs_Greenfield_Rebuild_Tracker.md).
Until Planning is rebuilt, the "Procurement Plans" rail entry is routed to
the shared "coming-soon" capability overview (same mechanism as Analytics /
Evaluation / Awards / Contract Management / STD Versions) instead of
`planning-workspace`. This file asserts that decommissioned state. To
restore the original contract, revert `link_to`/`route_options`/`url` back
to `planning-workspace` / `/desk/planning-workspace` in
`workspace_sidebar/procurement.json` and remove "Procurement Plans" from
`PLANNED_SIDEBAR_LABELS` in `setup/sidebar_availability.py`.
"""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

_EXPECTED_PLANNING_LABEL = "Procurement Plans"

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
		self.assertEqual((row.get("link_to") or "").strip(), "coming-soon")
		self.assertEqual((row.get("link_type") or "").strip(), "Page")
		self.assertIn(_EXPECTED_PLANNING_LABEL, row.get("route_options") or "")
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

	def test_procurement_rail_entry_routes_to_coming_soon_while_decommissioned(self):
		pp_links = [
			row
			for row in _load_items()
			if row.get("type") == "Link" and row.get("label") == _EXPECTED_PLANNING_LABEL
		]
		self.assertEqual(len(pp_links), 1)
		self.assertEqual((pp_links[0].get("link_to") or "").strip(), "coming-soon")
		self.assertIn(_EXPECTED_PLANNING_LABEL, pp_links[0].get("route_options") or "")

	def test_pp2_planning_router_removed(self):
		"""PP2 retirement — legacy router asset must not remain on disk."""
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"pp2_planning_router.js",
		)
		self.assertFalse(os.path.isfile(path), msg=f"Legacy PP2 router must be deleted: {path}")
