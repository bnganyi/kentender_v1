# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""XMOD-STR-001 — Budget Line primary Strategy Reference validate-on-save."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_line_contracts import save_budget_line
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy


class TestBudgetLineStrategyValidate(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()
		cls.strategy = upsert_works_master_strategy_hierarchy()

	def _ensure_draft_budget(self, code: str = "MOH-BUD-STR-VAL") -> str:
		pe = self.seed["procuring_entity"]
		name = frappe.db.get_value("Budget", {"generated_reference": code}, "name")
		if name:
			frappe.db.set_value("Budget", name, "status", "Draft", update_modified=False)
			return code
		frappe.get_doc(
			{
				"doctype": "Budget",
				"generated_reference": code,
				"title": "Strategy validate draft",
				"procuring_entity": pe,
				"fiscal_period": "2047/48",
				"start_date": "2047-07-01",
				"end_date": "2048-06-30",
				"currency": "KES",
				"budget_owner": "Budget Officer",
				"registration_source": "Direct capture",
				"authoritative_reference": "MOH-STR-VAL",
				"approval_date": "2047-06-01",
				"external_approved_total": 100_000_000,
				"approval_evidence": "/files/test.pdf",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		return code

	def _base_payload(self, budget_code: str, **overrides) -> dict:
		payload = {
			"budget": budget_code,
			"title": "Strategy validate line",
			"organisational_owner": "Head, ICT",
			"classification": "Services",
			"funding_source_type": "Exchequer",
			"funding_source_name": "Exchequer",
			"approved_amount": 25_000_000,
			"primary_target": {
				"id": self.strategy["target"],
				"code": frappe.db.get_value("Performance Target", self.strategy["target"], "target_code"),
			},
			"value_treatments": [],
		}
		payload.update(overrides)
		return payload

	def test_active_primary_target_fills_authoritative_primary_fields(self):
		budget_code = self._ensure_draft_budget()
		result = save_budget_line(self._base_payload(budget_code))
		self.assertTrue(result.get("ok"), result)
		line = result["line"]
		doc = frappe.get_doc("Budget Line", {"generated_reference": line["code"]})
		self.assertEqual(doc.primary_target_id, self.strategy["target"])
		self.assertEqual(doc.primary_plan_version_id, self.strategy["plan"])
		self.assertTrue((doc.primary_target_code or "").strip())
		self.assertTrue((doc.primary_target_name or "").strip())
		self.assertTrue((doc.primary_snapshot_label or "").strip())
		self.assertEqual(int(doc.primary_strategy_linked or 0), 1)

	def test_unknown_primary_target_rejected(self):
		budget_code = self._ensure_draft_budget()
		result = save_budget_line(
			self._base_payload(
				budget_code,
				primary_target={"id": "not-a-real-target", "code": "NO-SUCH-TGT"},
			)
		)
		self.assertFalse(result.get("ok"), result)
		self.assertIn("primary_target", result.get("errors") or {})

	def test_non_active_primary_target_rejected_on_create(self):
		budget_code = self._ensure_draft_budget("MOH-BUD-STR-VAL-NA")
		# Active target on a Draft plan is not selectable_for_new (STR-AC-009).
		bad = frappe.db.sql(
			"""
			select pt.name, pt.target_code
			from `tabPerformance Target` pt
			inner join `tabStrategic Plan` sp on sp.name = pt.plan_version
			where pt.status = 'Active' and sp.status != 'Active'
			limit 1
			""",
			as_dict=True,
		)
		if not bad:
			self.skipTest("No Active-on-non-Active-plan target available")
		result = save_budget_line(
			self._base_payload(
				budget_code,
				primary_target={"id": bad[0].name, "code": bad[0].target_code},
			)
		)
		self.assertFalse(result.get("ok"), result)
		self.assertIn("primary_target", result.get("errors") or {})

	def test_unchanged_historical_primary_still_saves(self):
		budget_code = self._ensure_draft_budget("MOH-BUD-STR-VAL-HIST")
		created = save_budget_line(self._base_payload(budget_code, title="Historical keep"))
		self.assertTrue(created.get("ok"), created)
		line_code = created["line"]["code"]
		# Re-save same primary without requiring Active re-check path to fail.
		result = save_budget_line(
			self._base_payload(
				budget_code,
				line=line_code,
				title="Historical keep updated",
				primary_target={
					"id": self.strategy["target"],
					"code": frappe.db.get_value(
						"Performance Target", self.strategy["target"], "target_code"
					),
				},
			)
		)
		self.assertTrue(result.get("ok"), result)
		self.assertEqual(result["line"]["title"], "Historical keep updated")
