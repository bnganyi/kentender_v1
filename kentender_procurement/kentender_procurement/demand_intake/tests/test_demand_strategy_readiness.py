# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""XMOD-STR-002 / XMOD-STR-003 — Demand strategy + PVC readiness."""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.demand_intake.services.demand_strategy_value import (
	TREATMENT_INCLUDED,
	TREATMENT_NOT_APPLICABLE,
	apply_value_treatments_to_doc,
	required_pvc_treatments_ok,
)
from kentender_procurement.demand_intake.services.readiness import evaluate_submission_readiness
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy
from kentender_strategy.services.strategy_contracts import list_applicable_value_commitments


def _required_fixture(seed_plan: str) -> list[dict]:
	"""Return Required applicable PVCs without category filter (MOH seed includes PVO-EFT-01)."""
	rows = list_applicable_value_commitments(plan_version=seed_plan)
	required = [r for r in rows if str(r.get("consideration_level") or "").startswith("Required")]
	return required


class TestDemandStrategyReadiness(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.seed = upsert_works_master_strategy_hierarchy()

	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()
		self.entity = self.seed["procuring_entity"]
		self.dept = ensure_department(f"Dept STR {frappe.generate_hash(length=4)}", self.entity)
		self._demand_names: list[str] = []

	def tearDown(self):
		if getattr(self, "_skip", False):
			return
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		dept = getattr(self, "dept", None)
		if dept and frappe.db.exists("Procuring Department", dept):
			frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)

	def _mk_demand(self, **kwargs):
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": kwargs.pop("title", None) or f"STR {frappe.generate_hash(length=4)}",
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": kwargs.pop("requisition_type", "Goods"),
				"priority_level": "Normal",
				"demand_type": "Planned",
				"beneficiary_summary": "Benefit",
				"specification_summary": "Scope summary",
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 100,
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		return doc

	def test_missing_strategy_target_not_submission_ready(self):
		if self._skip:
			self.skipTest("Demand DocType not installed")
		doc = self._mk_demand()
		out = evaluate_submission_readiness(doc)
		self.assertFalse(out["ready"])
		check = next(c for c in out["checks"] if c["id"] == "strategy_linkage")
		self.assertFalse(check["ok"])
		self.assertTrue(check["required"])

	def test_strategy_target_present_passes_strategy_check(self):
		if self._skip:
			self.skipTest("Demand DocType not installed")
		doc = self._mk_demand(strategy_target=self.seed["target"])
		out = evaluate_submission_readiness(doc)
		check = next(c for c in out["checks"] if c["id"] == "strategy_linkage")
		self.assertTrue(check["ok"])
		self.assertTrue(doc.strategy_plan_version)

	def test_required_pvc_untreated_fails(self):
		if self._skip:
			self.skipTest("Demand DocType not installed")
		required = _required_fixture(self.seed["plan"])
		if not required:
			self.skipTest("No Required applicable PVCs on MOH plan")
		doc = self._mk_demand(strategy_target=self.seed["target"])
		with patch(
			"kentender_procurement.demand_intake.services.demand_strategy_value.list_demand_applicable_pvcs",
			return_value=required,
		):
			ok, count = required_pvc_treatments_ok(doc)
			self.assertFalse(ok)
			self.assertGreater(count, 0)
			out = evaluate_submission_readiness(doc)
		pvc = next(c for c in out["checks"] if c["id"] == "value_commitments")
		self.assertFalse(pvc["ok"])
		self.assertTrue(pvc["required"])

	def test_required_pvc_included_passes(self):
		if self._skip:
			self.skipTest("Demand DocType not installed")
		required = _required_fixture(self.seed["plan"])
		if not required:
			self.skipTest("No Required applicable PVCs on MOH plan")
		doc = self._mk_demand(strategy_target=self.seed["target"])
		treatments = []
		for r in required:
			obj = r.get("objective") or {}
			treatments.append(
				{
					"pvc_id": r.get("id"),
					"pvc_code": obj.get("code"),
					"pvc_name": obj.get("name"),
					"requirement_level": r.get("consideration_level"),
					"treatment": TREATMENT_INCLUDED,
				}
			)
		apply_value_treatments_to_doc(doc, treatments)
		doc.save(ignore_permissions=True)
		with patch(
			"kentender_procurement.demand_intake.services.demand_strategy_value.list_demand_applicable_pvcs",
			return_value=required,
		):
			ok, _ = required_pvc_treatments_ok(doc)
			self.assertTrue(ok)
			out = evaluate_submission_readiness(doc)
		pvc = next(c for c in out["checks"] if c["id"] == "value_commitments")
		self.assertTrue(pvc["ok"])

	def test_required_pvc_na_needs_rationale(self):
		if self._skip:
			self.skipTest("Demand DocType not installed")
		required = _required_fixture(self.seed["plan"])
		if not required:
			self.skipTest("No Required applicable PVCs on MOH plan")
		doc = self._mk_demand(strategy_target=self.seed["target"])
		r0 = required[0]
		obj = r0.get("objective") or {}
		with self.assertRaises(frappe.ValidationError):
			apply_value_treatments_to_doc(
				doc,
				[
					{
						"pvc_id": r0.get("id"),
						"pvc_code": obj.get("code"),
						"pvc_name": obj.get("name"),
						"requirement_level": r0.get("consideration_level"),
						"treatment": TREATMENT_NOT_APPLICABLE,
						"rationale": "",
					}
				],
			)
		apply_value_treatments_to_doc(
			doc,
			[
				{
					"pvc_id": r0.get("id"),
					"pvc_code": obj.get("code"),
					"pvc_name": obj.get("name"),
					"requirement_level": r0.get("consideration_level"),
					"treatment": TREATMENT_NOT_APPLICABLE,
					"rationale": "Not in scope for this demand",
				}
			],
		)
		doc.save(ignore_permissions=True)
		with patch(
			"kentender_procurement.demand_intake.services.demand_strategy_value.list_demand_applicable_pvcs",
			return_value=required,
		):
			ok, _ = required_pvc_treatments_ok(doc)
		self.assertTrue(ok)

	def test_save_demand_draft_persists_strategy_target(self):
		if self._skip:
			self.skipTest("Demand DocType not installed")
		from kentender_procurement.demand_intake.api.create_demand import save_demand_draft

		result = save_demand_draft(
			title="CDW Strategy Persist",
			requesting_department=self.dept,
			requisition_type="Goods",
			procuring_entity=self.entity,
			required_by_date=today(),
			priority_level="Normal",
			beneficiary_summary="Strategy draft justification",
			strategy_target=self.seed["target"],
		)
		self._demand_names.append(result["demand_name"])
		doc = frappe.get_doc("Demand", result["demand_name"])
		self.assertEqual(doc.strategy_target, self.seed["target"])
		self.assertEqual(doc.strategy_plan_version, self.seed["plan"])

	def test_save_demand_draft_persists_value_treatments(self):
		if self._skip:
			self.skipTest("Demand DocType not installed")
		from kentender_procurement.demand_intake.api.create_demand import save_demand_draft

		required = _required_fixture(self.seed["plan"])
		if not required:
			self.skipTest("No Required applicable PVCs on MOH plan")
		result = save_demand_draft(
			title="CDW PVC Persist",
			requesting_department=self.dept,
			requisition_type="Goods",
			procuring_entity=self.entity,
			required_by_date=today(),
			beneficiary_summary="PVC draft",
			strategy_target=self.seed["target"],
		)
		name = result["demand_name"]
		self._demand_names.append(name)
		payload = []
		for r in required:
			obj = r.get("objective") or {}
			payload.append(
				{
					"pvc_id": r.get("id"),
					"pvc_code": obj.get("code"),
					"pvc_name": obj.get("name"),
					"requirement_level": r.get("consideration_level"),
					"treatment": TREATMENT_INCLUDED,
				}
			)
		save_demand_draft(demand_name=name, value_treatments=json.dumps(payload))
		doc = frappe.get_doc("Demand", name)
		self.assertGreaterEqual(len(doc.get("value_treatments") or []), len(required))
