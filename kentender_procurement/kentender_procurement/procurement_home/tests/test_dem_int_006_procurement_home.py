"""DEM-INT-006 — Procurement Home consumes Demands MVP-1 routes and projections."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate

from kentender_procurement.procurement_home.services import home_actions, home_pipeline


class TestDemInt006ProcurementHome(IntegrationTestCase):
	def test_pipeline_counts_scoped_mvp_demands_and_uses_demands_workspace(self) -> None:
		rows = [
			frappe._dict(
				name="DEM-REVIEW",
				procuring_entity="PE-MOH",
				status="In Review",
				current_stage="Business Review",
			),
			frappe._dict(
				name="DEM-OTHER-PE",
				procuring_entity="PE-CGKIS",
				status="In Review",
				current_stage="Business Review",
			),
			frappe._dict(
				name="DEM-DRAFT",
				procuring_entity="PE-MOH",
				status="Draft",
				current_stage="Request Preparation",
			),
		]
		with (
			patch.object(home_pipeline, "demand_doctype_available", return_value=True),
			patch.object(
				home_pipeline,
				"list_demands_for_workspace",
				return_value={"ok": True, "rows": rows},
			) as scoped_list,
		):
			self.assertEqual(
				home_pipeline._count_demands_under_review("PE-MOH", "reviewer@example.test"),
				1,
			)
		scoped_list.assert_called_once_with(
			user="reviewer@example.test",
			filters={"limit": 500},
		)
		self.assertEqual(home_pipeline.PIPELINE_STAGES[0][2], "/desk/demands-workspace")
		self.assertEqual(home_pipeline.PIPELINE_STAGES[1][2], "/desk/demands-workspace")

	def test_home_actions_use_mvp_fields_and_stage_specific_desk_routes(self) -> None:
		actor = "owner@example.test"
		rows = [
			frappe._dict(
				name="DEM-BUSINESS",
				demand_code="DMD-MOH-001",
				title="Business review demand",
				status="In Review",
				current_stage="Business Review",
				current_owner=actor,
				requester="requester@example.test",
				procuring_entity="PE-MOH",
				modified="2026-08-08 10:00:00",
				required_by_date=None,
			),
			frappe._dict(
				name="DEM-RETURNED",
				demand_code="DMD-MOH-002",
				title="Returned demand",
				status="Returned",
				current_stage="Request Preparation",
				current_owner=actor,
				requester=actor,
				procuring_entity="PE-MOH",
				modified="2026-08-08 11:00:00",
				required_by_date=None,
			),
			frappe._dict(
				name="DEM-APPROVED",
				demand_code="DMD-MOH-003",
				title="Approved demand",
				status="Approved",
				current_stage="Complete",
				current_owner=None,
				requester=actor,
				procuring_entity="PE-MOH",
				modified="2026-08-08 12:00:00",
				required_by_date=None,
			),
		]
		with (
			patch.object(home_actions, "demand_doctype_available", return_value=True),
			patch.object(
				home_actions,
				"list_demands_for_workspace",
				return_value={"ok": True, "rows": rows},
			),
		):
			items = home_actions._demand_actions(actor, "PE-MOH", getdate())

		by_ref = {item["reference"]: item for item in items}
		self.assertEqual(
			by_ref["DMD-MOH-001"]["target_url"],
			"/desk/demand-review/DEM-BUSINESS",
		)
		self.assertEqual(
			by_ref["DMD-MOH-002"]["target_url"],
			"/desk/demand-form/DEM-RETURNED",
		)
		self.assertNotIn("DMD-MOH-003", by_ref)

	def test_home_and_sidebar_sources_have_no_retired_demand_routes(self) -> None:
		app_root = Path(frappe.get_app_path("kentender_procurement"))
		paths = [
			app_root / "procurement_home" / "services" / "home_actions.py",
			app_root / "procurement_home" / "services" / "home_pipeline.py",
			app_root / "procurement_home" / "services" / "home_portfolio.py",
			app_root / "public" / "js" / "procurement_home_page.js",
			app_root / "public" / "js" / "procurement_sidebar_header.js",
		]
		source = "\n".join(path.read_text(encoding="utf-8") for path in paths)
		for retired_route in ("demand-workbench", "demand-hub", "create-demand"):
			self.assertNotIn(retired_route, source)
		self.assertIn("/desk/demands-workspace", source)
		self.assertIn("/desk/demand-review/", source)
		self.assertIn("/desk/demand-form/", source)

	def test_procurement_sidebar_demands_link_targets_workspace(self) -> None:
		path = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "workspace_sidebar"
			/ "procurement.json"
		)
		data = json.loads(path.read_text(encoding="utf-8"))
		demands = next(row for row in data["items"] if row.get("label") == "Demands")
		self.assertEqual(demands.get("link_type"), "Page")
		self.assertEqual(demands.get("link_to"), "demands-workspace")
		self.assertEqual(demands.get("url"), "/desk/demands-workspace")
