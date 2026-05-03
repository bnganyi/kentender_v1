# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-006 — ``Tender Lot`` extensions: package line traceability + ``lot_status`` (doc 5 §12).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh006
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


class TestWorksTenderHardeningWh006(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh006_tender_lot_meta_new_fields(self) -> None:
		meta = frappe.get_meta("Tender Lot")
		self.assertEqual(meta.istable, 1)

		pl = meta.get_field("package_line")
		self.assertIsNotNone(pl)
		self.assertEqual(pl.fieldtype, "Link")
		self.assertEqual(pl.options, "Procurement Package Line")
		self.assertEqual(int(pl.reqd or 0), 0)

		sp = meta.get_field("source_package_line_code")
		self.assertIsNotNone(sp)
		self.assertEqual(sp.fieldtype, "Data")
		self.assertEqual(int(sp.reqd or 0), 0)

		ls = meta.get_field("lot_status")
		self.assertIsNotNone(ls)
		self.assertEqual(ls.fieldtype, "Select")
		self.assertEqual(ls.default, "Draft")
		self.assertEqual(
			set((ls.options or "").strip().split("\n")),
			{"Draft", "Active", "Superseded"},
		)

		ev = meta.get_field("estimated_value")
		self.assertIsNotNone(ev)
		self.assertEqual(ev.fieldtype, "Currency")

	def test_wh006_lot_row_persists_on_tender(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-006 Tender Lot Extensions"
		doc.tender_reference = "WH006-LOT-001"
		doc.append(
			"lots",
			{
				"lot_code": "WH006-LOT-A",
				"lot_title": "Traceability lot",
				"source_package_line_code": "PKGL-MOH-2026-001-01",
				"lot_status": "Active",
				"estimated_value": 68000000,
				"currency": "KES",
			},
		)
		doc.insert(ignore_permissions=True)
		try:
			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			self.assertEqual(len(reloaded.lots), 1)
			row = reloaded.lots[0]
			self.assertEqual(row.lot_code, "WH006-LOT-A")
			self.assertEqual(row.source_package_line_code, "PKGL-MOH-2026-001-01")
			self.assertEqual(row.lot_status, "Active")
			self.assertEqual(float(row.estimated_value or 0), 68000000.0)
			self.assertEqual(row.currency, "KES")
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
