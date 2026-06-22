# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5C-010 — Approved Demands queue parameter contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.approved_demands import (
	get_pp_approved_demands_awaiting_planning,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP2ApprovedDemandsQueuesP5C010(IntegrationTestCase):
	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_approved_demands_awaiting_planning(queue="blocked")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_administrator_accepts_supported_queue_keys(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		for queue in ("ready-to-plan", "blocked", "already-planned"):
			out = get_pp_approved_demands_awaiting_planning(queue=queue, limit=20)
			self.assertTrue(out.get("ok"), msg=out.get("message"))
			self.assertEqual(out.get("queue_key"), queue)
			self.assertIn("total", out)
			self.assertIn("rows", out)
			self.assertIsInstance(out.get("rows"), list)

	def test_invalid_queue_defaults_to_ready_to_plan(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		out = get_pp_approved_demands_awaiting_planning(queue="not-a-real-queue")
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		self.assertEqual(out.get("queue_key"), "ready-to-plan")
