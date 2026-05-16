# Copyright (c) 2026, KenTender and contributors

"""R5-011 / LV-R5-011-01 — TM2 Tender procurement hand-offs panel."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.journey_api import get_tm2_handoff_panel
from kentender_procurement.tender_management.services.tm2_handoff_panel import (
	build_tm2_handoff_panel_payload,
)

_WORKS_TM2 = "TND-MOH-2026-001"
_PKGREL = "PKGREL-MOH-2026-001"
_STDREADY = "STDREADY-TND-MOH-2026-001"
_PUBCERT = "PUBCERT-TND-MOH-2026-001"


class TestR5011Tm2HandoffPanel(IntegrationTestCase):
	def test_build_raises_on_blank_code(self):
		with self.assertRaises(ValueError):
			build_tm2_handoff_panel_payload("")

	def test_api_works_tender_three_base_handoffs(self):
		if not frappe.db.exists("TM2 Tender", _WORKS_TM2):
			self.skipTest("WORKS TM2 tender not seeded on site.")
		if not frappe.db.exists("Procurement Handoff Card", _PKGREL):
			self.skipTest("WORKS PKGREL hand-off not seeded on site.")

		frappe.set_user("Administrator")
		out = get_tm2_handoff_panel(_WORKS_TM2, 0)
		self.assertIsNotNone(out)
		self.assertEqual(out.get("tender_code"), _WORKS_TM2)
		codes = [h["handoff_code"] for h in out.get("handoffs") or []]
		self.assertIn(_PKGREL, codes)
		self.assertIn(_STDREADY, codes)
		self.assertIn(_PUBCERT, codes)

	def test_optional_includes_close_record_when_loaded(self):
		if not frappe.db.exists("TM2 Tender", _WORKS_TM2):
			self.skipTest("WORKS TM2 tender not seeded on site.")
		if not frappe.db.exists(
			"Procurement Handoff Card",
			"CLOSECERT-TND-MOH-2026-001",
		):
			self.skipTest("Optional OPENING_READY hand-offs not seeded on site.")

		frappe.set_user("Administrator")
		out_on = get_tm2_handoff_panel(_WORKS_TM2, True)
		self.assertIsNotNone(out_on)
		codes = [h["handoff_code"] for h in out_on.get("handoffs") or []]
		self.assertIn("CLOSECERT-TND-MOH-2026-001", codes)
