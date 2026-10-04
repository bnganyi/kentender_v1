# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 plan §5 — the Tenders and Requisitions test wipes must
only ever remove test-world rows. Before 26 Sep 2026 they deleted every
Tender, Requisition and Requisitions-owned Funding Reservation on the site,
canonical data included (STD-TPL-IMP-001 FU-13).

The proof is by counts: whatever non-test Tenders, Requisitions and
reservations exist before `wipe_all()` still exist after it. A test-world
row planted first proves the wipe still does its job.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.tenders.tests import fixtures as fx


def _real_rows() -> dict[str, set[str]]:
	return {
		"Tender": set(frappe.get_all("Tender", filters={"name": ("not in", fx.test_tenders() or ("",))}, pluck="name")),
		"Procurement Requisition": set(
			frappe.get_all("Procurement Requisition", filters={"name": ("not in", req_fx.test_requisitions() or ("",))}, pluck="name")
		),
		"Funding Reservation": set(
			frappe.get_all(
				"Funding Reservation",
				filters={"calling_module": "Procurement Requisitions", "name": ("not in", req_fx.test_reservations() or ("",))},
				pluck="name",
			)
		),
	}


class TestFixtureScope(IntegrationTestCase):
	def test_test_year_convention(self):
		self.assertTrue(req_fx.is_test_fiscal_year("2101-2102"))
		self.assertTrue(req_fx.is_test_fiscal_year("2100-2101"))
		self.assertFalse(req_fx.is_test_fiscal_year("2027-2028"))
		self.assertFalse(req_fx.is_test_fiscal_year(""))

	def test_wipe_all_leaves_real_rows(self):
		before = _real_rows()
		fx.wipe_all()
		after = {
			"Tender": set(frappe.get_all("Tender", pluck="name")),
			"Procurement Requisition": set(frappe.get_all("Procurement Requisition", pluck="name")),
			"Funding Reservation": set(frappe.get_all("Funding Reservation", filters={"calling_module": "Procurement Requisitions"}, pluck="name")),
		}
		for doctype, names in before.items():
			self.assertEqual(names, after[doctype], f"{doctype}: the test wipe removed or kept the wrong rows")
		self.assertEqual(fx.test_tenders(), [])
		self.assertEqual(req_fx.test_requisitions(), [])
		self.assertEqual(req_fx.test_reservations(), [])
