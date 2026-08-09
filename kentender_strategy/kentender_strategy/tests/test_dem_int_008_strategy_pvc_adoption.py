# Copyright (c) 2026, KenTender and contributors
"""DEM-INT-008 — Strategy PVC adoption reads MVP Demand Value Treatment."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_consumers_live,
	demand_doctype_available,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_performance import (
	_demand_pvc_treatment_counts,
	get_strategy_performance,
)


DEMAND_CODE = "DEM-INT-008-TEST"


class TestDemInt008StrategyPvcAdoption(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.plan = cls.seed["plan"]
		cls.target = cls.seed["target"]
		cls.procuring_entity = cls.seed["procuring_entity"]
		cls.owner_org_unit = (
			frappe.db.get_value("Performance Target", cls.target, "owner_org_unit")
			or frappe.db.get_value(
				"Organisation Unit",
				{"procuring_entity": cls.procuring_entity},
				"name",
			)
		)
		cls.pvc = frappe.db.get_value(
			"Plan Value Commitment",
			{"plan_version": cls.plan},
			"name",
		)
		if not cls.owner_org_unit or not cls.pvc:
			raise AssertionError("Strategy fixture must provide an owner unit and PVC")

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._delete_test_demand()

	def tearDown(self):
		frappe.set_user("Administrator")
		self._delete_test_demand()
		super().tearDown()

	def _delete_test_demand(self) -> None:
		demand = frappe.db.get_value("Demand", {"demand_code": DEMAND_CODE}, "name")
		if not demand:
			return
		for doctype in ("Demand Value Treatment", "Demand Strategy Reference"):
			for name in frappe.get_all(doctype, filters={"demand": demand}, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.delete_doc("Demand", demand, force=True, ignore_permissions=True)

	def _create_aligned_demand(self) -> str:
		demand = frappe.get_doc(
			{
				"doctype": "Demand",
				"demand_code": DEMAND_CODE,
				"title": "DEM-INT-008 PVC adoption regression",
				"procuring_entity": self.procuring_entity,
				"owner_org_unit": self.owner_org_unit,
				"requester": "Administrator",
				"demand_route": "Standard",
				"currency": "KES",
				"status": "Approved",
				"current_stage": "Complete",
			}
		).insert(ignore_permissions=True)
		target = frappe.db.get_value(
			"Performance Target",
			self.target,
			["target_code", "title"],
			as_dict=True,
		)
		frappe.get_doc(
			{
				"doctype": "Demand Strategy Reference",
				"demand": demand.name,
				"reference_type": "Primary",
				"plan": self.plan,
				"plan_version_id": self.plan,
				"target_id": self.target,
				"target_code": target.target_code,
				"target_name": target.title,
				"snapshot_label": target.title,
			}
		).insert(ignore_permissions=True)
		return demand.name

	def test_pvc_adoption_uses_mvp_related_docs_without_consumers_live(self):
		self.assertTrue(demand_doctype_available())
		self.assertTrue(demand_consumers_live())
		aligned_before, treated_before = _demand_pvc_treatment_counts(self.plan)
		demand = self._create_aligned_demand()
		frappe.get_doc(
			{
				"doctype": "Demand Value Treatment",
				"demand": demand,
				"plan_value_commitment": self.pvc,
				"applicability": "Required",
				"treatment": "Embedded in specification",
				"rationale": "Carry the commitment into the specification.",
			}
		).insert(ignore_permissions=True)

		aligned, treated = _demand_pvc_treatment_counts(self.plan)

		self.assertEqual(aligned, aligned_before + 1)
		self.assertEqual(treated.get(self.pvc, 0), treated_before.get(self.pvc, 0) + 1)
		dto = get_strategy_performance(plan_version=self.plan)
		commitment = next(c for c in dto["commitments"] if c["id"] == self.pvc)
		self.assertEqual(
			commitment["downstream_adoption"],
			f"{treated[self.pvc]} of {aligned} aligned Value Cases addressed",
		)

	def test_deferred_or_not_applicable_treatment_requires_rationale(self):
		aligned_before, treated_before = _demand_pvc_treatment_counts(self.plan)
		demand = self._create_aligned_demand()
		row = frappe.get_doc(
			{
				"doctype": "Demand Value Treatment",
				"demand": demand,
				"plan_value_commitment": self.pvc,
				"applicability": "Required",
				"treatment": "To be determined in Planning",
			}
		).insert(ignore_permissions=True)

		aligned, treated = _demand_pvc_treatment_counts(self.plan)
		self.assertEqual(aligned, aligned_before + 1)
		self.assertEqual(treated.get(self.pvc, 0), treated_before.get(self.pvc, 0))

		row.db_set("rationale", "Planning must resolve whole-life costing.", update_modified=False)
		_, treated_with_reason = _demand_pvc_treatment_counts(self.plan)
		self.assertEqual(
			treated_with_reason.get(self.pvc, 0),
			treated_before.get(self.pvc, 0) + 1,
		)

	def test_performance_depth_seed_uses_related_records_idempotently(self):
		from kentender_strategy.seeds.moh_downstream_usage import (
			CANONICAL_DEMAND_TREATMENTS,
			seed_moh_performance_contribution_depth,
		)

		demand = frappe.get_doc(
			{
				"doctype": "Demand",
				"demand_code": DEMAND_CODE,
				"title": "DEM-INT-008 seed regression",
				"procuring_entity": self.procuring_entity,
				"owner_org_unit": self.owner_org_unit,
				"requester": "Administrator",
				"demand_route": "Standard",
				"currency": "KES",
				"status": "Approved",
				"current_stage": "Complete",
			}
		).insert(ignore_permissions=True)

		with patch(
			"kentender_strategy.seeds.moh_downstream_usage.SEED_DEMAND_CODES",
			(DEMAND_CODE,),
		):
			first = seed_moh_performance_contribution_depth(
				plan_name=self.plan,
				target_name=self.target,
			)
			second = seed_moh_performance_contribution_depth(
				plan_name=self.plan,
				target_name=self.target,
			)

		self.assertEqual(first["linked"]["demand"], demand.name)
		self.assertEqual(
			first["required_treatments_applied"],
			len(CANONICAL_DEMAND_TREATMENTS),
		)
		self.assertEqual(
			frappe.db.count(
				"Demand Strategy Reference",
				{"demand": demand.name, "reference_type": "Primary"},
			),
			1,
		)
		self.assertEqual(
			frappe.db.count("Demand Value Treatment", {"demand": demand.name}),
			second["required_treatments_applied"],
		)
		treatments = frappe.get_all(
			"Demand Value Treatment",
			filters={"demand": demand.name},
			fields=["plan_value_commitment", "treatment", "rationale"],
		)
		for row in treatments:
			code = frappe.db.get_value(
				"Plan Value Commitment",
				row.plan_value_commitment,
				"commitment_code",
			)
			self.assertEqual(
				(row.treatment, row.rationale),
				CANONICAL_DEMAND_TREATMENTS[code],
			)
