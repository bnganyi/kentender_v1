# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-010 — Supplier denied internal Planning UI/evidence."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.evidence_view_model import (
	get_pp_evidence_view_model,
)
from kentender_procurement.procurement_planning.api.released_to_tender import (
	get_pp_released_to_tender,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)


class TestPP8SupplierConfidentialityP8010(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {seed}")

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _ensure_supplier(self) -> str:
		email = f"p8010.supplier.{frappe.generate_hash(length=6)}@moh.test"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P8010",
				"last_name": "Supplier",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Supplier")
		self._cleanup.append(("User", email))
		return email

	def test_pp8_010_supplier_denied_released_list(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		supplier = self._ensure_supplier()
		frappe.set_user(supplier)
		out = get_pp_released_to_tender()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_pp8_010_supplier_denied_evidence_view_model(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		supplier = self._ensure_supplier()
		frappe.set_user(supplier)
		out = get_pp_evidence_view_model(package_code=PKG_CODE)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")
