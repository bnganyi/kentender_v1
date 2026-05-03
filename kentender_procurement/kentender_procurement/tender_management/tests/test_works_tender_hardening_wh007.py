# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-007 — ``Tender BoQ Item`` extensions: bill/item, locks, formula, row status (doc 5 §13).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh007

§13.1 cross-field rules are **WH-010**; this module asserts schema + persistence only.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

_EXPECTED_FORMULA_TYPES = {
	"Measured",
	"Provisional Sum",
	"Daywork",
	"Summary",
	"Fixed",
}
_EXPECTED_BOQ_ROW_STATUSES = {"Draft", "Active", "Superseded"}


class TestWorksTenderHardeningWh007(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh007_tender_boq_item_meta_new_fields(self) -> None:
		meta = frappe.get_meta("Tender BoQ Item")
		self.assertEqual(meta.istable, 1)

		def _f(name: str):
			f = meta.get_field(name)
			self.assertIsNotNone(f, f"missing field {name}")
			return f

		bc = _f("boq_code")
		self.assertEqual(bc.fieldtype, "Data")
		self.assertEqual(int(bc.reqd or 0), 1)

		bv = _f("boq_version")
		self.assertEqual(bv.fieldtype, "Data")
		self.assertEqual(int(bv.reqd or 0), 1)
		self.assertEqual(bv.default, "V1")

		bill_c = _f("bill_code")
		self.assertEqual(bill_c.fieldtype, "Data")
		self.assertEqual(int(bill_c.reqd or 0), 1)

		bill_n = _f("bill_number")
		self.assertEqual(bill_n.fieldtype, "Data")
		self.assertEqual(int(bill_n.reqd or 0), 0)

		bill_t = _f("bill_title")
		self.assertEqual(bill_t.fieldtype, "Data")
		self.assertEqual(int(bill_t.reqd or 0), 1)

		inum = _f("item_number")
		self.assertEqual(inum.fieldtype, "Data")
		self.assertEqual(int(inum.reqd or 0), 1)

		ql = _f("quantity_locked")
		self.assertEqual(ql.fieldtype, "Check")
		self.assertEqual(int(ql.reqd or 0), 1)
		self.assertEqual(ql.default, "1")

		pr = _f("pricing_required")
		self.assertEqual(pr.fieldtype, "Check")
		self.assertEqual(int(pr.reqd or 0), 0)
		self.assertEqual(pr.default, "0")

		sre = _f("supplier_rate_editable")
		self.assertEqual(sre.fieldtype, "Check")
		self.assertEqual(int(sre.reqd or 0), 0)
		self.assertEqual(sre.default, "0")

		fa = _f("fixed_amount")
		self.assertEqual(fa.fieldtype, "Currency")
		self.assertEqual(int(fa.reqd or 0), 0)

		ft = _f("formula_type")
		self.assertEqual(ft.fieldtype, "Select")
		self.assertEqual(int(ft.reqd or 0), 1)
		self.assertEqual(ft.default, "Measured")
		self.assertEqual(
			set((ft.options or "").strip().split("\n")),
			_EXPECTED_FORMULA_TYPES,
		)

		ase = _f("allow_supplier_amount_edit")
		self.assertEqual(ase.fieldtype, "Check")
		self.assertEqual(int(ase.reqd or 0), 0)
		self.assertEqual(ase.default, "0")

		sp = _f("source_package_line_code")
		self.assertEqual(sp.fieldtype, "Data")
		self.assertEqual(int(sp.reqd or 0), 0)

		brs = _f("boq_row_status")
		self.assertEqual(brs.fieldtype, "Select")
		self.assertEqual(int(brs.reqd or 0), 0)
		self.assertEqual(brs.default, "Draft")
		self.assertEqual(
			set((brs.options or "").strip().split("\n")),
			_EXPECTED_BOQ_ROW_STATUSES,
		)

	def test_wh007_boq_row_persists_on_tender(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-007 Tender BoQ Item Extensions"
		doc.tender_reference = "WH007-BOQ-001"
		doc.append(
			"boq_items",
			{
				"item_code": "WH007-001",
				"lot_code": "LOT-001",
				"boq_code": "WH007-BOQ",
				"boq_version": "V1",
				"bill_code": "B01",
				"bill_number": "1",
				"bill_title": "Preliminaries",
				"item_number": "1.01",
				"item_category": "PRELIMINARIES",
				"description": "Site establishment",
				"unit": "Item",
				"quantity": 1,
				"rate": None,
				"amount": None,
				"quantity_locked": 1,
				"pricing_required": 1,
				"supplier_rate_editable": 0,
				"fixed_amount": None,
				"formula_type": "Measured",
				"allow_supplier_amount_edit": 0,
				"source_package_line_code": "PKGL-MOH-2026-001-01",
				"boq_row_status": "Active",
				"is_priced_by_bidder": 1,
				"notes": "WH-007 persistence row",
			},
		)
		doc.insert(ignore_permissions=True)
		try:
			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			self.assertEqual(len(reloaded.boq_items), 1)
			row = reloaded.boq_items[0]
			self.assertEqual(row.item_code, "WH007-001")
			self.assertEqual(row.boq_code, "WH007-BOQ")
			self.assertEqual(row.boq_version, "V1")
			self.assertEqual(row.bill_code, "B01")
			self.assertEqual(row.bill_number, "1")
			self.assertEqual(row.bill_title, "Preliminaries")
			self.assertEqual(row.item_number, "1.01")
			self.assertEqual(int(row.quantity_locked or 0), 1)
			self.assertEqual(int(row.pricing_required or 0), 1)
			self.assertEqual(int(row.supplier_rate_editable or 0), 0)
			self.assertEqual(row.formula_type, "Measured")
			self.assertEqual(int(row.allow_supplier_amount_edit or 0), 0)
			self.assertEqual(row.source_package_line_code, "PKGL-MOH-2026-001-01")
			self.assertEqual(row.boq_row_status, "Active")
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
