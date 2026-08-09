"""DEM-INT-007 — lifecycle handoff and journey bootstrap use MVP Demands."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_procurement.demands.api import (
	approve_and_reserve_form,
	prepare_final_approval_ui08,
)
from kentender_procurement.demands.services.demand_permissions import ROLE_REQUESTER
from kentender_procurement.demands.tests.test_demands_budget_api import _ensure_user
from kentender_procurement.procurement_lifecycle.demand_approval_handoff import (
	create_demand_approval_certificate,
)
from kentender_procurement.procurement_lifecycle.demand_journey_bootstrap import (
	ensure_procurement_journey_for_demand_code,
)
from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_consumers_live,
	demand_doctype_available,
)
from kentender_procurement.procurement_lifecycle.demand_planning_status import (
	build_demand_planning_status_payload,
)


class TestDemInt007DemandHandoff(IntegrationTestCase):
	def _approved_demand(self) -> tuple[str, str]:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-int007-req@example.com", [ROLE_REQUESTER])
		)
		frappe.set_user(payload["procurement_approver"])
		result = approve_and_reserve_form(demand=payload["demand"])
		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], "Approved")
		self.assertEqual(cint(result["planning_ready"]), 1)
		frappe.set_user("Administrator")
		return payload["demand"], payload["demand_code"]

	def test_bootstrap_and_handoff_use_mvp_demand_contract_without_consumer_flag(self) -> None:
		self.assertTrue(demand_doctype_available())
		self.assertTrue(demand_consumers_live())
		demand_name, demand_code = self._approved_demand()

		journey_code = ensure_procurement_journey_for_demand_code(demand_code)
		self.assertTrue(journey_code)
		journey = frappe.db.get_value(
			"Procurement Journey",
			journey_code,
			(
				"demand_ref",
				"journey_title",
				"procuring_entity_code",
				"procurement_category",
				"budget_line_ref",
			),
			as_dict=True,
		)
		self.assertEqual(journey["demand_ref"], demand_code)
		self.assertTrue(journey["journey_title"])
		self.assertTrue(journey["procuring_entity_code"])
		self.assertTrue(journey["procurement_category"])
		self.assertTrue(journey["budget_line_ref"])

		handoff_code = f"DEMAPP-{journey_code.removeprefix('JRN-')}"
		card = frappe.db.get_value(
			"Procurement Handoff Card",
			handoff_code,
			(
				"source_module",
				"source_object_code",
				"locked_summary",
				"passed_forward_summary",
				"technical_refs_json",
				"evidence_links_json",
			),
			as_dict=True,
		)
		self.assertIsNotNone(card)
		self.assertEqual(card["source_module"], "Demands")
		self.assertEqual(card["source_object_code"], demand_code)

		locked = json.loads(card["locked_summary"])
		self.assertEqual(locked["demand_code"], demand_code)
		self.assertEqual(locked["status"], "Approved")
		self.assertEqual(cint(locked["planning_ready"]), 1)
		self.assertEqual(locked["planning_usage"], "Not taken up")
		self.assertGreater(float(locked["approved_estimated_value"]), 0)
		self.assertTrue(locked["budget_line"])

		passed = json.loads(card["passed_forward_summary"])
		self.assertTrue(passed["approved_need"])
		self.assertTrue(passed["owner_org_unit"])
		self.assertEqual(passed["planning_action"], "Include in Procurement Planning")

		technical = json.loads(card["technical_refs_json"])
		self.assertTrue(technical["demand_item_code"])
		self.assertTrue(technical["budget_line_code"])
		self.assertTrue(technical["funding_reservation"])

		links = json.loads(card["evidence_links_json"])["links"]
		demand_link = next(link for link in links if link["object_type"] == "Demand")
		self.assertEqual(demand_link["module"], "Demands")
		self.assertEqual(demand_link["object_code"], demand_code)
		self.assertEqual(demand_link["route"], f"/desk/demand-detail/{demand_name}")

		self.assertEqual(ensure_procurement_journey_for_demand_code(demand_code), journey_code)
		self.assertEqual(
			frappe.db.count(
				"Procurement Handoff Card", {"handoff_code": handoff_code}
			),
			1,
		)

	def test_planning_status_uses_mvp_usage_and_bootstrapped_handoff(self) -> None:
		demand_name, demand_code = self._approved_demand()
		journey_code = ensure_procurement_journey_for_demand_code(demand_code)

		out = build_demand_planning_status_payload(demand_name)

		self.assertTrue(out["ok"], out)
		self.assertEqual(out["demand_code"], demand_code)
		self.assertEqual(out["planning_usage"], "Not taken up")
		self.assertTrue(out["planning_ready"])
		self.assertEqual(out["journey"]["journey_code"], journey_code)
		self.assertEqual(
			out["demand_approval_certificate"]["handoff_code"],
			f"DEMAPP-{journey_code.removeprefix('JRN-')}",
		)

	def test_draft_demand_does_not_create_handoff(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-int007-draft@example.com", [ROLE_REQUESTER])
		)
		demand_name = payload["demand"]
		demand_code = payload["demand_code"]
		frappe.db.set_value(
			"Demand",
			demand_name,
			{"status": "Draft", "current_stage": "Request Preparation", "planning_ready": 0},
			update_modified=False,
		)

		self.assertIsNone(ensure_procurement_journey_for_demand_code(demand_code))
		with self.assertRaisesRegex(ValueError, "DEMAND_NOT_APPROVED"):
			create_demand_approval_certificate(demand_code, "JRN-DEM-INT-007-DRAFT")
