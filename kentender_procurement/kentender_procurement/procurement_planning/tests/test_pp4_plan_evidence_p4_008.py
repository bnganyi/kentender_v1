# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-008 — Plan evidence action."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes
from kentender_procurement.procurement_planning.api.procurement_plans import (
	get_pp_procurement_plan_evidence_view_model,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP4PlanEvidenceP4008Source(UnitTestCase):
	def test_plan_summary_and_drawer_support_plan_evidence(self) -> None:
		summary = _pkg_public("js", "pp3_planning_plan_summary.js")
		drawer = _pkg_public("js", "pp3_planning_evidence_drawer.js")
		summary_source = summary.read_text(encoding="utf-8", errors="replace")
		drawer_source = drawer.read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="pp3-view-plan-evidence"', summary_source)
		self.assertIn("get_pp_procurement_plan_evidence_view_model", drawer_source)
		self.assertIn("openForPlan", drawer_source)


class TestPP4PlanEvidenceP4008API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[str] = []
		if not frappe.db.exists("DocType", "Procurement Plan"):
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for name in reversed(self._cleanup):
			if frappe.db.exists("Procurement Plan", name):
				frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_plan_evidence_returns_business_timeline(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		code = f"PLAN-P4008-{frappe.generate_hash()[:6].upper()}"
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": "Evidence Plan",
				"plan_code": code,
				"fiscal_year": 2026,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_ACTIVE,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		self._cleanup.append(plan.name)
		frappe.db.commit()
		out = get_pp_procurement_plan_evidence_view_model(plan_id=code)
		self.assertTrue(out.get("ok"), msg=out)
		self.assertEqual(out.get("title"), "Evidence Plan")
		self.assertTrue(out.get("timeline"))
		self.assertTrue(out.get("records"))
		self.assertFalse((out.get("technical_details") or {}).get("visible_by_default"))
