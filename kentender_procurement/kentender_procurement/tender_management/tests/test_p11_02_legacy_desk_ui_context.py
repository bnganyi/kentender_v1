# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P11-02 — doc 9 §22.2 desk UI context (archive banner vs hide v1 POC when TM2 exists).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p11_02_legacy_desk_ui_context
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender import (
	get_legacy_desk_ui_context,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)

_PACK_LEGACY_BANNER = (
	"Legacy tender record — historical only. Cannot be used as Tender v2 source of truth."
)


class TestP1102LegacyDeskUiContext(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		self._tm2_to_delete: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for name in self._tm2_to_delete:
			if name and frappe.db.exists("TM2 Tender", name):
				frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)
		super().tearDown()

	def _mk_tm2_minimal(self, *, plan_name: str, pkg_name: str) -> frappe.model.document.Document:
		pkg_code = frappe.db.get_value("Procurement Package", pkg_name, "package_code") or pkg_name
		plan_code = frappe.db.get_value("Procurement Plan", plan_name, "plan_code") or plan_name
		tm2 = frappe.new_doc("TM2 Tender")
		tm2.tender_code = f"TND-P11-{frappe.generate_hash(length=6)}"
		tm2.tender_title = "P11-02 TM2 fixture"
		tm2.status = "Draft"
		tm2.is_active = 1
		tm2.procurement_package = pkg_name
		tm2.procurement_plan = plan_name
		tm2.procurement_package_code = pkg_code
		tm2.procurement_plan_code = plan_code
		tm2.procuring_entity_code = "MOH"
		tm2.fiscal_year = "2026"
		tm2.procurement_method = "Open Tender"
		tm2.procurement_category = "Works"
		tm2.tender_visibility = "Internal Preview"
		tm2.currency = "KES"
		tm2.flags.ignore_validate = True
		tm2.insert(ignore_permissions=True)
		self._tm2_to_delete.append(tm2.name)
		return tm2

	def test_p11_02_legacy_banner_string_without_tm2(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "P11-02 legacy banner"
		doc.tender_reference = f"P11-BNR-{frappe.generate_hash(length=6)}"
		doc.procurement_package = pkg.name
		doc.procurement_plan = plan.name
		doc.insert(ignore_permissions=True)
		self._created.append(("Procurement Tender", doc.name))
		ctx = get_legacy_desk_ui_context(doc.name)
		self.assertTrue(ctx.get("ok"))
		self.assertFalse(ctx.get("hide_v1_desk_navigation"))
		self.assertEqual(ctx.get("legacy_archive_banner"), _PACK_LEGACY_BANNER)
		self.assertIsNone(ctx.get("tm2_tender"))

	def test_p11_02_hides_v1_nav_when_active_tm2_on_package(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "P11-02 TM2 peer"
		doc.tender_reference = f"P11-TM2-{frappe.generate_hash(length=6)}"
		doc.procurement_package = pkg.name
		doc.procurement_plan = plan.name
		doc.insert(ignore_permissions=True)
		self._created.append(("Procurement Tender", doc.name))
		tm2 = self._mk_tm2_minimal(plan_name=plan.name, pkg_name=pkg.name)
		ctx = get_legacy_desk_ui_context(doc.name)
		self.assertTrue(ctx.get("ok"))
		self.assertTrue(ctx.get("hide_v1_desk_navigation"))
		self.assertEqual(ctx.get("tm2_tender"), tm2.name)
		self.assertTrue((ctx.get("tm2_tender_code") or "").strip())
