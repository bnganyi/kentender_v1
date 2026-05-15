# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §18.2 — supplier portal tender list (allowed tenders only).

**EX-12** (doc 9 §25 / doc 8 TM2-SMOKE-SEC-003): ``test_EX_12_*`` — portal list rows come only from
**TM2 Supplier Participation** for the logged-in supplier (no cross-supplier tender leakage).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p10_02_supplier_portal_tender_list
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.supplier_portal import list_supplier_portal_tenders
from kentender_procurement.tender_management.services.supplier_portal_tender_list import (
	list_supplier_portal_tenders as list_supplier_portal_tenders_service,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestP1002SupplierPortalTenderList(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._p1002_users: list[str] = []
		self._p1002_suppliers: list[str] = []
		self._p1002_profiles: list[str] = []
		self._p1002_groups: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P1002%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Access Rule",
			filters={"tender_code": ["like", "TND-P1002%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Access Rule", row):
				frappe.delete_doc("TM2 Tender Access Rule", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P1002%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		for pn in self._p1002_profiles:
			if frappe.db.exists("KTSM Supplier Profile", pn):
				frappe.delete_doc("KTSM Supplier Profile", pn, force=True, ignore_permissions=True)
		for un in self._p1002_users:
			if frappe.db.exists("User", un):
				frappe.delete_doc("User", un, force=True, ignore_permissions=True)
		for sn in self._p1002_suppliers:
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		for gn in self._p1002_groups:
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
		name = f"KT-P1002-{label}"
		if frappe.db.exists("Supplier Group", name):
			if name not in self._p1002_groups:
				self._p1002_groups.append(name)
			return name
		parent = self._parent_supplier_group()
		self.assertTrue(parent, "No parent Supplier Group for P10-02 fixtures")
		frappe.get_doc(
			{
				"doctype": "Supplier Group",
				"supplier_group_name": name,
				"parent_supplier_group": parent,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
		self._p1002_groups.append(name)
		return name

	def _ensure_supplier(self, label: str, *, supplier_group: str) -> str:
		supplier_name = f"P1002 {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			if existing not in self._p1002_suppliers:
				self._p1002_suppliers.append(str(existing))
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
		self._p1002_suppliers.append(doc.name)
		return doc.name

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str) -> frappe.model.document.Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P1002 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
				"procuring_entity_code": "MOH",
				"procurement_method": "Open Tender",
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

	def _mk_portal_user(self, email: str) -> str:
		if frappe.db.exists("User", email):
			self._p1002_users.append(email)
			return email
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P1002",
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		u.insert(ignore_permissions=True)
		u.append("roles", {"role": "Customer"})
		u.save(ignore_permissions=True)
		self._p1002_users.append(u.name)
		return u.name

	def _mk_ktsm_profile(self, *, supplier: str, external_user: str) -> str | None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return None
		p = frappe.get_doc(
			{
				"doctype": "KTSM Supplier Profile",
				"erpnext_supplier": supplier,
				"approval_status": "Approved",
				"operational_status": "Active",
				"compliance_status": "Complete",
				"external_user": external_user,
			}
		).insert(ignore_permissions=True)
		self._p1002_profiles.append(p.name)
		return p.name

	def test_p10_02_no_supplier_profile_returns_empty(self) -> None:
		email = f"p1002-noprofile-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		frappe.set_user(uname)
		out = list_supplier_portal_tenders_service(uname)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("items"), [])
		self.assertIsNone(out.get("supplier"))
		self.assertTrue(out.get("message"))

	def test_p10_02_whitelist_matches_service(self) -> None:
		email = f"p1002-whitelist-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		frappe.set_user(uname)
		api = list_supplier_portal_tenders()
		svc = list_supplier_portal_tenders_service(uname)
		self.assertEqual(api.get("ok"), svc.get("ok"))
		self.assertEqual(api.get("supplier"), svc.get("supplier"))
		self.assertEqual(len(api.get("items") or []), len(svc.get("items") or []))

	def test_p10_02_ineligible_supplier_hidden(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		sg = self._ensure_leaf_supplier_group("inelig")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P1002-2028-0001")
		self._mk_access_rule(tm2)
		sup = self._ensure_supplier("Inelig", supplier_group=sg)
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": sup}
		).insert(ignore_permissions=True)
		email = f"p1002-inelig-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		frappe.db.set_value("Supplier", sup, "disabled", 1, update_modified=False)
		frappe.set_user(uname)
		out = list_supplier_portal_tenders_service(uname)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("items"), [])
		frappe.db.set_value("Supplier", sup, "disabled", 0, update_modified=False)

	def test_p10_02_eligible_participation_lists_tender(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		sg = self._ensure_leaf_supplier_group("elig")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tcode = "TND-P1002-2028-0002"
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tcode)
		self._mk_access_rule(tm2)
		sup = self._ensure_supplier("Elig", supplier_group=sg)
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": sup}
		).insert(ignore_permissions=True)
		email = f"p1002-elig-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		frappe.set_user(uname)
		out = list_supplier_portal_tenders_service(uname)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("supplier"), sup)
		items = out.get("items") or []
		self.assertEqual(len(items), 1, out)
		row = items[0]
		self.assertEqual(row.get("tender_code"), tcode)
		self.assertEqual(row.get("tender_title"), "P1002 TM2")
		self.assertEqual(row.get("procuring_entity_code"), "MOH")
		self.assertEqual(row.get("procurement_method"), "Open Tender")
		self.assertEqual(row.get("procurement_category"), "Goods")
		self.assertIn("access_requirement", row)

	def test_EX_12_portal_list_excludes_tenders_without_participation(self) -> None:
		"""EX-12 — supplier B's list must not include tenders where only supplier A participates."""
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		sg = self._ensure_leaf_supplier_group("ex12")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		h = frappe.generate_hash(length=4)
		tcode_a = f"TND-P1002-EX12-{h}-A"
		tcode_b = f"TND-P1002-EX12-{h}-B"
		tm_a = self._mk_tm2(plan.name, pkg.name, tender_code=tcode_a)
		self._mk_access_rule(tm_a)
		tm_b = self._mk_tm2(plan.name, pkg.name, tender_code=tcode_b)
		self._mk_access_rule(tm_b)
		sup_a = self._ensure_supplier("Ex12Alpha", supplier_group=sg)
		sup_b = self._ensure_supplier("Ex12Beta", supplier_group=sg)
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm_a.name, "supplier": sup_a}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm_b.name, "supplier": sup_b}
		).insert(ignore_permissions=True)
		email = f"p1002-ex12-{h}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup_b, external_user=uname)
		frappe.set_user(uname)
		out = list_supplier_portal_tenders_service(uname)
		self.assertTrue(out.get("ok"), out)
		codes = {str(r.get("tender_code") or "").strip() for r in (out.get("items") or [])}
		self.assertIn(tcode_b, codes)
		self.assertNotIn(tcode_a, codes)
