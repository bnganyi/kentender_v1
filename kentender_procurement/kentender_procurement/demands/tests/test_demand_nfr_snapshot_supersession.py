# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-NFR-010 — snapshot / decisions / audit after Strategy or Budget supersession."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
	upsert_principal_approved_demand,
)
from kentender_procurement.demands.services.demand_lifecycle import get_demand_audit
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_approved,
)


class TestDemandNfrSnapshotSupersession(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_nfr010_snapshot_survives_strategy_and_budget_supersession(self) -> None:
		"""DIA-NFR-010 — approved snapshot, decisions, audit remain after supersession."""
		actors = actor_bundle("dem-nfr010")
		name = advance_to_approved(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="NFR010 supersession snapshot",
		)
		doc = frappe.get_doc("Demand", name)
		baseline = doc.approved_baseline_snapshot
		self.assertTrue(baseline)
		baseline_obj = json.loads(baseline)
		self.assertEqual(baseline_obj.get("title"), "NFR010 supersession snapshot")

		ref_name = frappe.db.get_value(
			"Demand Strategy Reference",
			{"demand": name, "reference_type": "Primary"},
			"name",
		)
		snapshot_label = frappe.db.get_value(
			"Demand Strategy Reference", ref_name, "snapshot_label"
		)
		plan = frappe.db.get_value(
			"Strategic Plan",
			{"plan_code": C.PLAN_CODE, "procuring_entity": C.PE_MOH},
			"name",
		) or frappe.db.get_value(
			"Strategic Plan", {"procuring_entity": C.PE_MOH}, "name"
		)
		self.assertTrue(plan)
		prior_plan = frappe.db.get_value("Strategic Plan", plan, "status")
		frappe.db.set_value(
			"Demand Strategy Reference",
			ref_name,
			{"plan": plan, "plan_version_id": plan},
		)
		frappe.db.set_value("Strategic Plan", plan, "status", "Superseded")

		# Budget supersession: mark linked Budget as Superseded/Archived if allowed.
		alloc = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": name},
			["budget", "budget_line", "allocation_amount"],
			as_dict=True,
		)
		prior_budget_status = None
		budget_name = (alloc or {}).get("budget")
		if budget_name and frappe.db.exists("Budget", budget_name):
			prior_budget_status = frappe.db.get_value("Budget", budget_name, "status")
			# Budget has no Superseded; Closed stands in for portfolio supersession.
			frappe.db.set_value("Budget", budget_name, "status", "Closed")

		try:
			doc.reload()
			self.assertEqual(doc.approved_baseline_snapshot, baseline)
			self.assertEqual(
				frappe.db.get_value(
					"Demand Strategy Reference", ref_name, "snapshot_label"
				),
				snapshot_label,
			)
			decisions = frappe.get_all(
				"Demand Decision",
				filters={"demand": name},
				fields=["decision", "stage"],
			)
			self.assertTrue(decisions)
			self.assertTrue(any(d.decision == "Approve" for d in decisions))

			audit = get_demand_audit(demand=name, user=actors["paa"])
			self.assertTrue(audit.get("ok"))
			self.assertTrue(audit.get("decisions"))
			# Seed principal also remains readable after portfolio supersession.
			seed = upsert_principal_approved_demand(commit=False)
			seed_doc = frappe.get_doc("Demand", seed["demand"])
			self.assertTrue(seed_doc.approved_baseline_snapshot)
			seed_audit = get_demand_audit(demand=seed["demand"], user=actors["paa"])
			self.assertTrue(seed_audit.get("decisions") is not None)
		finally:
			if prior_plan:
				frappe.db.set_value("Strategic Plan", plan, "status", prior_plan)
			if budget_name and prior_budget_status:
				frappe.db.set_value("Budget", budget_name, "status", prior_budget_status)
