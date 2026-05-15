# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P10-03 — doc 9 §18.3 supplier portal tender detail (metadata + deadlines + server time).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p10_03_supplier_portal_tender_detail
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.api.supplier_portal import get_supplier_portal_tender_detail
from kentender_procurement.tender_management.services.supplier_portal_tender_detail import (
	get_supplier_portal_tender_detail as get_supplier_portal_tender_detail_service,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestP1003SupplierPortalTenderDetail(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._p1003_users: list[str] = []
		self._p1003_suppliers: list[str] = []
		self._p1003_profiles: list[str] = []
		self._p1003_groups: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Tender Timeline",
			filters={"tender_code": ["like", "TND-P1003%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P1003%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Access Rule",
			filters={"tender_code": ["like", "TND-P1003%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Access Rule", row):
				frappe.delete_doc("TM2 Tender Access Rule", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P1003%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		for pn in self._p1003_profiles:
			if frappe.db.exists("KTSM Supplier Profile", pn):
				frappe.delete_doc("KTSM Supplier Profile", pn, force=True, ignore_permissions=True)
		for un in self._p1003_users:
			if frappe.db.exists("User", un):
				frappe.delete_doc("User", un, force=True, ignore_permissions=True)
		for sn in self._p1003_suppliers:
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		for gn in self._p1003_groups:
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
		name = f"KT-P1003-{label}"
		if frappe.db.exists("Supplier Group", name):
			if name not in self._p1003_groups:
				self._p1003_groups.append(name)
			return name
		parent = self._parent_supplier_group()
		self.assertTrue(parent, "No parent Supplier Group for P10-03 fixtures")
		frappe.get_doc(
			{
				"doctype": "Supplier Group",
				"supplier_group_name": name,
				"parent_supplier_group": parent,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
		self._p1003_groups.append(name)
		return name

	def _ensure_supplier(self, label: str, *, supplier_group: str) -> str:
		supplier_name = f"P1003 {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			if existing not in self._p1003_suppliers:
				self._p1003_suppliers.append(str(existing))
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
		self._p1003_suppliers.append(doc.name)
		return doc.name

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str) -> Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P1003 Detail TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Works",
				"tender_visibility": "Public",
				"procuring_entity_code": "MOH",
				"procurement_method": "Open Tender",
			}
		).insert(ignore_permissions=True)

	def _mk_access_rule(self, tm2: Document, **extra) -> None:
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

	def _mk_timeline(self, tm2: Document) -> None:
		now = now_datetime()
		frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2.name,
				"timeline_code": f"TTL-{tm2.tender_code}",
				"clarification_deadline_at": add_to_date(now, days=3),
				"submission_deadline_at": add_to_date(now, days=10),
				"opening_scheduled_at": add_to_date(now, days=20),
				"tender_validity_days": 90,
				"timezone": "Africa/Nairobi",
			}
		).insert(ignore_permissions=True)

	def _mk_portal_user(self, email: str) -> str:
		if frappe.db.exists("User", email):
			self._p1003_users.append(email)
			return email
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P1003",
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		u.insert(ignore_permissions=True)
		u.append("roles", {"role": "Customer"})
		u.save(ignore_permissions=True)
		self._p1003_users.append(u.name)
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
		self._p1003_profiles.append(p.name)
		return p.name

	def test_p10_03_no_profile_denied(self) -> None:
		email = f"p1003-noprofile-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail_service(uname, "TND-P1003-ANY")
		self.assertFalse(out.get("ok"), out)
		self.assertTrue(out.get("message"))

	def test_p10_03_unknown_tender_denied(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		sg = self._ensure_leaf_supplier_group("unk")
		sup = self._ensure_supplier("Unk", supplier_group=sg)
		email = f"p1003-unk-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail_service(uname, "TND-P1003-NONEXISTENT-9999")
		self.assertFalse(out.get("ok"), out)

	def test_p10_03_ok_metadata_deadlines_and_whitelist(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		sg = self._ensure_leaf_supplier_group("ok")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tcode = "TND-P1003-2028-0001"
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tcode)
		self._mk_access_rule(tm2)
		self._mk_timeline(tm2)
		sup = self._ensure_supplier("Ok", supplier_group=sg)
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": sup}
		).insert(ignore_permissions=True)
		email = f"p1003-ok-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail_service(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		self.assertIn(" · ", out.get("header_line") or "")
		self.assertIn("MOH", out.get("subheader_line") or "")
		self.assertIn("Open Tender", out.get("subheader_line") or "")
		self.assertIn("Works", out.get("subheader_line") or "")
		self.assertTrue(out.get("server_time_display"))
		self.assertTrue(out.get("submission_deadline_display"))
		self.assertTrue(out.get("time_remaining_display"))
		self.assertIn("documents_addenda", out)
		self.assertIn("bundle", out.get("documents_addenda") or {})
		self.assertIn("submit_bid_panel", out)
		api = get_supplier_portal_tender_detail(tender_code=tcode)
		self.assertEqual(api.get("tender_code"), out.get("tender_code"))
