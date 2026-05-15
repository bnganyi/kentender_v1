# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-01 — doc 9 §11.1 ``check_supplier_tender_access`` (Supplier Management adapter).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p6_01_check_supplier_tender_access
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
	checkSupplierTenderAccess,
)
from kentender_procurement.tender_management.services.supplier_management_adapter import (
	evaluate_supplier_eligibility_for_tender,
	evaluateSupplierEligibilityForTender,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestP601CheckSupplierTenderAccess(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._p601_suppliers: list[str] = []
		self._p601_groups: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P601%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Access Rule",
			filters={"tender_code": ["like", "TND-P601%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Access Rule", row):
				frappe.delete_doc("TM2 Tender Access Rule", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P601%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		for sn in self._p601_suppliers:
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		for gn in self._p601_groups:
			if frappe.db.exists("Supplier Group", gn):
				try:
					frappe.delete_doc("Supplier Group", gn, force=True, ignore_permissions=True)
				except Exception:
					pass
		super().tearDown()

	def _parent_supplier_group(self) -> str:
		parent = frappe.db.get_value("Supplier Group", {"name": "All Supplier Groups"}, "name")
		if parent:
			return str(parent)
		return str(
			frappe.db.get_value("Supplier Group", {"is_group": 1}, "name", order_by="lft asc") or ""
		)

	def _ensure_leaf_supplier_group(self, label: str) -> str:
		name = f"KT-P601-{label}"
		if frappe.db.exists("Supplier Group", name):
			if name not in self._p601_groups:
				self._p601_groups.append(name)
			return name
		parent = self._parent_supplier_group()
		self.assertTrue(parent, "No parent Supplier Group for P6-01 fixtures")
		frappe.get_doc(
			{
				"doctype": "Supplier Group",
				"supplier_group_name": name,
				"parent_supplier_group": parent,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
		self._p601_groups.append(name)
		return name

	def _ensure_supplier(self, label: str, *, supplier_group: str) -> str:
		supplier_name = f"P601 {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			if existing not in self._p601_suppliers:
				self._p601_suppliers.append(str(existing))
			return str(existing)
		doc = frappe.get_doc(
			{
				"doctype": "Supplier",
				"naming_series": "SUP-.YYYY.-",
				"supplier_name": supplier_name,
				"supplier_type": "Company",
				"supplier_group": supplier_group,
			}
		).insert(ignore_permissions=True)
		self._p601_suppliers.append(doc.name)
		return doc.name

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str) -> frappe.model.document.Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P601 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

	def _mk_access_rule(self, tm2: frappe.model.document.Document, **extra) -> None:
		base = {
			"doctype": "TM2 Tender Access Rule",
			"tm2_tender": tm2.name,
			"visibility": "Public",
			"requires_supplier_login_for_documents": 0,
			"requires_invitation": 0,
			"allows_public_notice": 1,
			"allows_public_document_download": 0,
			"eligibility_service_required": 0,
		}
		base.update(extra)
		frappe.get_doc(base).insert(ignore_permissions=True)

	def test_p6_01_unknown_tender_denied(self) -> None:
		out = check_supplier_tender_access(
			"Administrator",
			"TND-P601-NONEXISTENT-9999",
			"Some-Supplier",
			context={},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value)

	def test_p6_01_unresolved_supplier_denied(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P601-2028-0001")
		self._mk_access_rule(tm2)
		out = check_supplier_tender_access(
			"Administrator",
			"TND-P601-2028-0001",
			"NOT-A-RESOLVABLE-SUPPLIER-REF-XYZ",
			context={},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p6_01_alpha_beta_pass_fixture_groups(self) -> None:
		sg_build = self._ensure_leaf_supplier_group("Building")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P601-2028-0002")
		self._mk_access_rule(
			tm2,
			supplier_category_restriction={"categories": [sg_build]},
		)
		s_alpha = self._ensure_supplier("Alpha", supplier_group=sg_build)
		s_beta = self._ensure_supplier("Beta", supplier_group=sg_build)
		for sup in (s_alpha, s_beta):
			out = check_supplier_tender_access(
				"Administrator",
				"TND-P601-2028-0002",
				sup,
				context={},
			)
			self.assertTrue(out.get("ok"), out)
			self.assertEqual(out.get("supplier"), sup)
			self.assertTrue(out.get("eligibility", {}).get("eligible"))

	def test_p6_01_gamma_suspended_denied(self) -> None:
		sg = self._ensure_leaf_supplier_group("GammaSG")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P601-2028-0003")
		self._mk_access_rule(tm2)
		s_gamma = self._ensure_supplier("Gamma", supplier_group=sg)
		frappe.db.set_value("Supplier", s_gamma, "disabled", 1, update_modified=False)
		out = check_supplier_tender_access(
			"Administrator",
			"TND-P601-2028-0003",
			s_gamma,
			context={},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)
		self.assertIn("suspended", str(out.get("message") or "").lower())

	def test_p6_01_delta_category_mismatch_denied(self) -> None:
		sg_build = self._ensure_leaf_supplier_group("BuildingB")
		sg_roads = self._ensure_leaf_supplier_group("Roads")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P601-2028-0004")
		self._mk_access_rule(
			tm2,
			supplier_category_restriction={"categories": [sg_build]},
		)
		s_delta = self._ensure_supplier("Delta", supplier_group=sg_roads)
		out = check_supplier_tender_access(
			"Administrator",
			"TND-P601-2028-0004",
			s_delta,
			context={},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)
		self.assertIn("category", str(out.get("message") or "").lower())

	def test_p6_01_context_evaluator_override(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P601-2028-0005")
		self._mk_access_rule(tm2)
		sg = self._ensure_leaf_supplier_group("OverrideSG")
		sup = self._ensure_supplier("Override", supplier_group=sg)

		def _eval(**kw: object) -> dict:
			return {"eligible": False, "message": "stub SM denial", "checks": []}

		out = check_supplier_tender_access(
			"Administrator",
			"TND-P601-2028-0005",
			sup,
			context={"supplier_eligibility_evaluator": _eval},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)
		self.assertEqual(out.get("message"), "stub SM denial")

	def test_p6_01_camel_case_alias(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P601-2028-0006")
		self._mk_access_rule(tm2)
		sg = self._ensure_leaf_supplier_group("CamelSG")
		sup = self._ensure_supplier("Camel", supplier_group=sg)
		out = checkSupplierTenderAccess("Administrator", "TND-P601-2028-0006", sup, context={})
		self.assertTrue(out.get("ok"), out)

	def test_p6_01_adapter_camel_case_alias(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P601-2028-0007")
		self._mk_access_rule(tm2)
		sg = self._ensure_leaf_supplier_group("AdCamelSG")
		sup = self._ensure_supplier("AdCamel", supplier_group=sg)
		out = evaluateSupplierEligibilityForTender(
			tm2_tender=tm2.name,
			tender_code="TND-P601-2028-0007",
			supplier=sup,
			context={},
		)
		self.assertTrue(out.get("eligible"), out)

	def test_p6_01_evaluate_matches_check_for_ineligible(self) -> None:
		sg = self._ensure_leaf_supplier_group("EvalSG")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P601-2028-0008")
		self._mk_access_rule(tm2)
		sup = self._ensure_supplier("Eval", supplier_group=sg)
		frappe.db.set_value("Supplier", sup, {"on_hold": 1}, update_modified=False)
		ev = evaluate_supplier_eligibility_for_tender(
			tm2_tender=tm2.name,
			tender_code="TND-P601-2028-0008",
			supplier=sup,
			context={},
		)
		self.assertFalse(ev.get("eligible"))
		out = check_supplier_tender_access(
			"Administrator",
			"TND-P601-2028-0008",
			sup,
			context={},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)
