# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-06 — TM2 Tender Access Rule (one per tender, TAC-*, TM2-ACR-001/003).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_tender_access_rule_p1_06
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2TenderAccessRuleP106(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for name in frappe.get_all(
			"TM2 Tender Access Rule", filters={"tender_code": ["like", "TND-P106%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Access Rule", name):
				frappe.delete_doc("TM2 Tender Access Rule", name, force=True, ignore_permissions=True)
		for name in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P106%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", name):
				frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)
		super().tearDown()

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str) -> frappe.model.document.Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P106 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

	def test_p106_insert_and_access_rule_code(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P106-2028-0001")
		rule = frappe.get_doc(
			{
				"doctype": "TM2 Tender Access Rule",
				"tm2_tender": tm2.name,
				"visibility": "Public",
				"requires_supplier_login_for_documents": 1,
				"requires_invitation": 0,
				"allows_public_notice": 1,
				"allows_public_document_download": 0,
				"supplier_category_restriction": {
					"categories": ["Works Contractor", "Building Contractor"],
				},
				"eligibility_service_required": 1,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(rule.access_rule_code, f"TAC-{tm2.tender_code}")
		self.assertEqual(rule.name, rule.access_rule_code)

	def test_p106_second_rule_same_tender_rejected(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P106-2028-0002")
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
		frappe.get_doc(dict(base)).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(dict(base)).insert(ignore_permissions=True)

	def test_p106_acr_001_restricted_requires_gate(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P106-2028-0003")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Tender Access Rule",
					"tm2_tender": tm2.name,
					"visibility": "Restricted",
					"requires_supplier_login_for_documents": 0,
					"requires_invitation": 0,
					"allows_public_notice": 0,
					"allows_public_document_download": 0,
					"eligibility_service_required": 0,
				}
			).insert(ignore_permissions=True)
		ok = frappe.get_doc(
			{
				"doctype": "TM2 Tender Access Rule",
				"tm2_tender": tm2.name,
				"visibility": "Restricted",
				"requires_supplier_login_for_documents": 0,
				"requires_invitation": 0,
				"allows_public_notice": 0,
				"allows_public_document_download": 0,
				"eligibility_service_required": 1,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(ok.visibility, "Restricted")

	def test_p106_published_parent_locks_policy(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P106-2028-0004")
		rule = frappe.get_doc(
			{
				"doctype": "TM2 Tender Access Rule",
				"tm2_tender": tm2.name,
				"visibility": "Public",
				"requires_supplier_login_for_documents": 0,
				"requires_invitation": 0,
				"allows_public_notice": 1,
				"allows_public_document_download": 0,
				"eligibility_service_required": 0,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("TM2 Tender", tm2.name, "status", "Published")
		rule.reload()
		rule.visibility = "Login Required"
		with self.assertRaises(frappe.ValidationError):
			rule.save(ignore_permissions=True)

	def test_p106_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Tender Access Rule")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"access_rule_code",
			"tender_code",
			"visibility",
			"requires_supplier_login_for_documents",
			"requires_invitation",
			"allows_public_notice",
			"allows_public_document_download",
			"supplier_category_restriction",
			"eligibility_service_required",
			"access_policy_snapshot",
			"created_at",
			"updated_at",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
