# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-001 — Active Plan view-model service/API contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes
from kentender_procurement.procurement_planning.api.active_plan import (
	get_pp_active_plan_view_model,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PLAN_ACTIVE,
	PLAN_DRAFT,
)
from kentender_procurement.procurement_planning.services.active_plan_view_model import (
	get_active_plan_view_model,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP3ActivePlanViewModelP2001(IntegrationTestCase):
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

	def _mk_plan(self, *, status: str, fiscal_year: int = 2032, is_active: int = 1) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"P2-001 plan {frappe.generate_hash(length=5)}",
				"plan_code": f"PLAN-P2001-{frappe.generate_hash()[:6].upper()}",
				"fiscal_year": fiscal_year,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": status,
				"is_active": is_active,
			}
		)
		plan.insert(ignore_permissions=True)
		self._cleanup.append(plan.name)
		return plan.name

	def test_guest_denied_api(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_active_plan_view_model()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_no_active_plan_returns_gate_payload(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		self._mk_plan(status=PLAN_DRAFT, fiscal_year=2032, is_active=1)
		frappe.db.commit()

		out = get_active_plan_view_model(actor="Administrator", fiscal_year=2032)
		self.assertTrue(out.get("ok"), msg=out)
		self.assertFalse(out.get("has_active_plan"))
		self.assertIn("No active procurement plan exists", out.get("message", ""))
		self.assertEqual((out.get("primary_action") or {}).get("label"), "Create Plan")
		self.assertEqual((out.get("secondary_action") or {}).get("label"), "Activate Existing Plan")

	def test_active_plan_envelope_fields(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		plan_name = self._mk_plan(status=PLAN_ACTIVE, fiscal_year=2031, is_active=1)
		frappe.db.commit()

		out = get_active_plan_view_model(actor="Administrator", fiscal_year=2031)
		self.assertTrue(out.get("ok"), msg=out)
		self.assertTrue(out.get("has_active_plan"))
		self.assertEqual(out.get("plan_code"), frappe.db.get_value("Procurement Plan", plan_name, "plan_code"))
		self.assertIsInstance(out.get("plan_title"), str)
		self.assertTrue(str(out.get("plan_title") or "").strip())
		self.assertEqual(out.get("fiscal_year"), "2031/2032")
		self.assertIsInstance(out.get("procuring_entity"), str)
		self.assertEqual(out.get("status_label"), "Active")
		self.assertIsInstance(out.get("can_change_plan"), bool)
		self.assertIsInstance(out.get("can_view_plan"), bool)
		self.assertTrue(out.get("can_view_plan"))

	def test_api_matches_service_output(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		self._mk_plan(status=PLAN_ACTIVE, fiscal_year=2034, is_active=1)
		frappe.db.commit()

		service_out = get_active_plan_view_model(actor="Administrator", fiscal_year=2034)
		api_out = get_pp_active_plan_view_model(fiscal_year=2034)
		self.assertEqual(service_out, api_out)
