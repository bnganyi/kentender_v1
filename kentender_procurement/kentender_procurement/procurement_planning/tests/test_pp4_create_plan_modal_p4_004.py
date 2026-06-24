# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-004 — Create Plan modal source contract and API."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes
from kentender_procurement.procurement_planning.api.procurement_plans import create_pp_procurement_plan
from kentender_procurement.procurement_planning.pp2_constants import PLAN_DRAFT
from kentender_procurement.procurement_planning.services.procurement_plan_create_service import (
	create_procurement_plan,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP4CreatePlanModalP4004Source(UnitTestCase):
	def test_create_plan_modal_exposes_required_testids(self) -> None:
		path = _pkg_public("js", "pp3_planning_create_plan_modal.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="pp3-create-plan-modal"', source)
		self.assertIn('data-testid="pp3-create-plan-entity"', source)
		self.assertIn('data-testid="pp3-create-plan-fiscal-year"', source)
		self.assertIn('data-testid="pp3-create-plan-title"', source)
		self.assertIn('data-testid="pp3-create-plan-currency"', source)
		self.assertIn('data-testid="pp3-create-plan-submit"', source)
		self.assertIn("create_pp_procurement_plan", source)

	def test_plans_page_header_exposes_create_plan_button(self) -> None:
		path = _pkg_public("js", "pp2_planning_page_header.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('testId: "pp3-create-plan-button"', source)
		self.assertIn('action: "create_plan"', source)


class TestPP4CreatePlanModalP4004API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[str] = []
		if not _pp_ok():
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

	def test_create_plan_api_creates_draft_plan(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = create_pp_procurement_plan(
			procuring_entity=C.ENTITY_MOH,
			fiscal_year="2026/2027",
			plan_title="Ministry of Health Procurement Plan FY 2026/2027",
			currency="KES",
		)
		self.assertTrue(out.get("ok"), msg=out)
		plan = out.get("plan") or {}
		self._cleanup.append(plan.get("plan_code"))
		self.assertEqual(plan.get("title"), "Ministry of Health Procurement Plan FY 2026/2027")
		self.assertEqual(plan.get("status_label"), "Draft")
		self.assertEqual(
			frappe.db.get_value("Procurement Plan", plan.get("plan_code"), "status"),
			PLAN_DRAFT,
		)

	def test_create_plan_requires_entity(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = create_procurement_plan(
			procuring_entity="",
			fiscal_year=2026,
			plan_title="Test",
			actor="Administrator",
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "MISSING_ENTITY")
