# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-017 — Emergency retains controls; no procurement method."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.api import get_demand_review
from kentender_procurement.demands.services.demand_lifecycle import (
	enrich_demand,
	record_business_decision,
	submit_demand,
)
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	create_draft,
)


class TestDemandRoute(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac017_emergency_requires_justification_and_no_method(self) -> None:
		"""DIA-AC-017 — Emergency keeps controls; enrichment DTO has no method."""
		actors = actor_bundle("dem-ac017")
		# Missing justification blocks submit.
		name = create_draft(
			actors["req"],
			estimate=1000,
			title="AC017 emergency without justification",
			route="Emergency",
		)
		with self.assertRaises(Exception):
			submit_demand(demand=name, user=actors["req"])

		# With justification, full control path remains (Business → Enrichment).
		ok_name = create_draft(
			actors["req"],
			estimate=1000,
			title="AC017 emergency with justification",
			route="Emergency",
			route_justification="Life-saving clinic outage — emergency procurement",
		)
		submitted = submit_demand(demand=ok_name, user=actors["req"])
		self.assertEqual(submitted["demand"]["status"], "In Review")
		self.assertEqual(submitted["demand"]["current_stage"], "Business Review")
		self.assertEqual(submitted["demand"]["demand_route"], "Emergency")

		record_business_decision(
			demand=ok_name, decision="Support", comment="Urgent", user=actors["ba"]
		)
		enriched = enrich_demand(
			demand=ok_name,
			values={
				"confirmed_estimate": 1000,
				"procurement_category": "Works",
				"estimate_basis": "Emergency quote",
				"demand_route": "Emergency",
				"route_justification": "Life-saving clinic outage — emergency procurement",
			},
			strategy_references=[
				{
					"reference_type": "Primary",
					"target_code": "T-AC017",
					"target_name": "Emergency Target",
					"snapshot_label": "Emergency Target (T-AC017)",
					"hierarchy_path": "Outcome > Target",
					"selection_source": "Manual",
					"confirmation_reason": "Emergency alignment",
				}
			],
			value_treatments=[],
			send_for_budget=False,
			user=actors["paa"],
		)
		self.assertEqual(enriched["demand"]["current_stage"], "Procurement Enrichment")
		self.assertNotIn("procurement_method", enriched["demand"])
		self.assertFalse(getattr(frappe.get_doc("Demand", ok_name), "procurement_method", None))

		frappe.set_user(actors["paa"])
		review = get_demand_review(demand=ok_name)
		demand_dto = review.get("demand") or {}
		self.assertNotIn("procurement_method", demand_dto)
		self.assertNotIn("tender_method", demand_dto)
		self.assertNotIn("method_of_procurement", demand_dto)
		# Forbidden keys must not appear in enrichment projection payload.
		flat = json_keys(review)
		for forbidden in (
			"procurement_method",
			"tender_method",
			"method_of_procurement",
			"evaluation_method",
		):
			self.assertNotIn(forbidden, flat)


def json_keys(payload) -> set[str]:
	keys: set[str] = set()

	def walk(node):
		if isinstance(node, dict):
			for k, v in node.items():
				keys.add(str(k))
				walk(v)
		elif isinstance(node, list):
			for item in node:
				walk(item)

	walk(payload)
	return keys
