# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-005 — Activate Plan flow."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes
from kentender_procurement.procurement_planning.api.procurement_plans import activate_pp_procurement_plan
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP4ActivatePlanP4005Source(UnitTestCase):
	def test_plan_summary_exposes_activate_button(self) -> None:
		path = _pkg_public("js", "pp3_planning_plan_summary.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="pp3-activate-plan-button"', source)
		self.assertIn("activate_pp_procurement_plan", source)


class TestPP4ActivatePlanP4005API(IntegrationTestCase):
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

	def _mk_draft(self) -> str:
		code = f"PLAN-P4005-{frappe.generate_hash()[:6].upper()}"
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": "Draft Plan P4005",
				"plan_code": code,
				"fiscal_year": 2026,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_DRAFT,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		self._cleanup.append(plan.name)
		return plan.name

	def test_authority_can_activate_draft_plan(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		plan_code = self._mk_draft()
		frappe.db.commit()
		out = activate_pp_procurement_plan(plan_id=plan_code)
		self.assertTrue(out.get("ok"), msg=out)
		self.assertEqual(out.get("status_label"), "Active")
		self.assertEqual(frappe.db.get_value("Procurement Plan", plan_code, "status"), PLAN_ACTIVE)
