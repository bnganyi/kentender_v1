# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-020 — Strategy snapshot remains readable after plan supersession."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.api import get_demand_review
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_final_approval,
)


class TestDemandStrategySnapshot(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac020_strategy_snapshot_readable_after_supersession(self) -> None:
		"""DIA-AC-020 — Demand Strategy Reference survives plan supersession."""
		actors = actor_bundle("dem-ac020")
		name = advance_to_final_approval(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="AC020 strategy snapshot",
		)
		ref_name = frappe.db.get_value(
			"Demand Strategy Reference",
			{"demand": name, "reference_type": "Primary"},
			"name",
		)
		self.assertTrue(ref_name)
		snapshot_before = frappe.db.get_value(
			"Demand Strategy Reference", ref_name, "snapshot_label"
		)
		self.assertTrue(snapshot_before)

		plan = frappe.db.get_value(
			"Strategic Plan",
			{"plan_code": C.PLAN_CODE, "procuring_entity": C.PE_MOH},
			"name",
		)
		if not plan:
			plan = frappe.db.get_value(
				"Strategic Plan",
				{"procuring_entity": C.PE_MOH},
				"name",
			)
		self.assertTrue(plan, "MOH Strategic Plan fixture required for AC-020")
		prior_status = frappe.db.get_value("Strategic Plan", plan, "status")
		frappe.db.set_value(
			"Demand Strategy Reference",
			ref_name,
			{"plan": plan, "plan_version_id": plan},
		)
		frappe.db.set_value("Strategic Plan", plan, "status", "Superseded")

		try:
			frappe.set_user(actors["paa"])
			review = get_demand_review(demand=name)
			refs = (review.get("strategy") or {}).get("references") or review.get(
				"strategy_references"
			)
			if refs is None:
				# Fall back to direct child read — projection must remain readable.
				refs = frappe.get_all(
					"Demand Strategy Reference",
					filters={"demand": name},
					fields=[
						"snapshot_label",
						"target_code",
						"target_name",
						"plan",
						"hierarchy_path",
					],
				)
			self.assertTrue(refs)
			primary = refs[0] if isinstance(refs, list) else refs
			label = (
				primary.get("snapshot_label")
				if isinstance(primary, dict)
				else getattr(primary, "snapshot_label", None)
			)
			self.assertEqual(label, snapshot_before)
			self.assertEqual(
				frappe.db.get_value("Strategic Plan", plan, "status"),
				"Superseded",
			)
			self.assertEqual(
				frappe.db.get_value("Demand Strategy Reference", ref_name, "snapshot_label"),
				snapshot_before,
			)
		finally:
			if prior_status:
				frappe.db.set_value("Strategic Plan", plan, "status", prior_status)
