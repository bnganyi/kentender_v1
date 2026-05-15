# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P10-04 — doc 9 §18.4 supplier portal documents & addenda (bundle control + list).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p10_04_supplier_portal_documents_addenda
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime, set_request
from frappe.utils.file_manager import save_file
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.services.supplier_portal_tender_detail import (
	get_supplier_portal_tender_detail,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestP1004SupplierPortalDocumentsAddenda(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		self._p1004_users: list[str] = []
		self._p1004_suppliers: list[str] = []
		self._p1004_profiles: list[str] = []
		self._p1004_groups: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Addendum Acknowledgement",
			filters={"tender_code": ["like", "TND-P1004%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Addendum Acknowledgement", row):
				frappe.delete_doc("TM2 Addendum Acknowledgement", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Addendum", filters={"tender_code": ["like", "TND-P1004%"]}, pluck="name"):
			if frappe.db.exists("TM2 Addendum", row):
				frappe.delete_doc("TM2 Addendum", row, force=True, ignore_permissions=True)
		tm2_names = frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P1004%"]}, pluck="name")
		for row in frappe.get_all("File", filters={"attached_to_doctype": "TM2 Tender"}, fields=["name", "attached_to_name"]):
			if row.attached_to_name in tm2_names:
				frappe.delete_doc("File", row.name, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender STD Binding",
			filters={"tm2_tender": ["in", tm2_names] if tm2_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender STD Binding", row):
				frappe.delete_doc("TM2 Tender STD Binding", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": ["in", tm2_names] if tm2_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("Tender STD Instance", row):
				frappe.delete_doc("Tender STD Instance", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline",
			filters={"tm2_tender": ["in", tm2_names] if tm2_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tm2_tender": ["in", tm2_names] if tm2_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Access Rule",
			filters={"tm2_tender": ["in", tm2_names] if tm2_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Access Rule", row):
				frappe.delete_doc("TM2 Tender Access Rule", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P1004%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		for pn in self._p1004_profiles:
			if frappe.db.exists("KTSM Supplier Profile", pn):
				frappe.delete_doc("KTSM Supplier Profile", pn, force=True, ignore_permissions=True)
		for un in self._p1004_users:
			if frappe.db.exists("User", un):
				frappe.delete_doc("User", un, force=True, ignore_permissions=True)
		for sn in self._p1004_suppliers:
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		for gn in self._p1004_groups:
			if frappe.db.exists("Supplier Group", gn):
				try:
					frappe.delete_doc("Supplier Group", gn, force=True, ignore_permissions=True)
				except Exception:
					pass
		if hasattr(frappe.local, "request"):
			delattr(frappe.local, "request")
		super().tearDown()

	def _parent_supplier_group(self) -> str:
		parent = frappe.db.get_value("Supplier Group", {"name": "All Supplier Groups"}, "name")
		if parent:
			return str(parent)
		return str(
			frappe.db.get_value("Supplier Group", {"is_group": 1}, "name", order_by="lft asc") or ""
		)

	def _ensure_leaf_supplier_group(self, label: str) -> str:
		name = f"KT-P1004-{label}"
		if frappe.db.exists("Supplier Group", name):
			if name not in self._p1004_groups:
				self._p1004_groups.append(name)
			return name
		parent = self._parent_supplier_group()
		self.assertTrue(parent, "No parent Supplier Group for P10-04 fixtures")
		frappe.get_doc(
			{
				"doctype": "Supplier Group",
				"supplier_group_name": name,
				"parent_supplier_group": parent,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
		self._p1004_groups.append(name)
		return name

	def _ensure_supplier(self, label: str, *, supplier_group: str) -> str:
		supplier_name = f"P1004 {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			if existing not in self._p1004_suppliers:
				self._p1004_suppliers.append(str(existing))
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
		self._p1004_suppliers.append(doc.name)
		return doc.name

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str, status: str = "Draft") -> Document:
		doc = frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P1004 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Works",
				"tender_visibility": "Public",
				"procuring_entity_code": "MOH",
				"procurement_method": "Open Tender",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		if status and status != "Draft":
			frappe.db.set_value("TM2 Tender", doc.name, "status", status, update_modified=False)
		return doc

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
			self._p1004_users.append(email)
			return email
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P1004",
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		u.insert(ignore_permissions=True)
		u.append("roles", {"role": "Customer"})
		u.save(ignore_permissions=True)
		self._p1004_users.append(u.name)
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
		self._p1004_profiles.append(p.name)
		return p.name

	def _mk_std_instance(self, tm2_name: str) -> Document:
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		return frappe.get_doc(
			{
				"doctype": "Tender STD Instance",
				"naming_series": "STDINST-.#####",
				"tm2_tender": tm2_name,
				"template_version_code": ver,
				"applicability_profile_code": prof,
				"procurement_category": "WORKS",
				"procurement_method": "OPEN_COMPETITIVE_TENDERING",
				"instance_status": "Draft",
				"readiness_status": "Not Ready",
				"created_from_tender_context": 1,
			}
		).insert(ignore_permissions=True)

	def _mk_binding(self, tm2_name: str, si_name: str) -> Document:
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender STD Binding",
				"tm2_tender": tm2_name,
				"std_template": TEMPLATE_CODE,
				"std_template_code": TEMPLATE_CODE,
				"std_template_version_code": ver,
				"std_applicability_profile_code": prof,
				"tender_std_instance": si_name,
				"is_active": 1,
				"binding_status": "Active",
				"readiness_status": "Ready",
			}
		).insert(ignore_permissions=True)

	def _base_portal_tender(self, *, status: str) -> tuple[str, Document, str]:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			self.skipTest("KTSM Supplier Profile not installed")
		sg = self._ensure_leaf_supplier_group("doc")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tcode = f"TND-P1004-{frappe.generate_hash(length=4)}"
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tcode, status=status)
		self._mk_access_rule(tm2)
		self._mk_timeline(tm2)
		si = self._mk_std_instance(tm2.name)
		bind = self._mk_binding(tm2.name, si.name)
		frappe.db.set_value(
			"TM2 Tender STD Binding",
			bind.name,
			{
				"bundle_output_code": "GB-P1004-FIXTURE-V1",
				"publication_snapshot_code": "PUBSNAP-P1004-V1",
				"dsm_output_code": "DSM-P1004-V1",
				"dom_output_code": "DOM-P1004-V1",
				"dem_output_code": "DEM-P1004-V1",
				"dcm_output_code": "DCM-P1004-V1",
			},
			update_modified=False,
		)
		sup = self._ensure_supplier("Doc", supplier_group=sg)
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": sup}
		).insert(ignore_permissions=True)
		email = f"p1004-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		return tcode, tm2, uname

	def test_p10_04_bundle_download_blocked_until_published(self) -> None:
		tcode, tm2, uname = self._base_portal_tender(status="Draft")
		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		dd = out.get("documents_addenda") or {}
		bundle = dd.get("bundle") or {}
		self.assertEqual(bundle.get("bundle_output_code"), "GB-P1004-FIXTURE-V1")
		self.assertFalse(bundle.get("download_allowed"))
		self.assertTrue(bundle.get("download_denial_reason"))

	def test_p10_04_bundle_download_allowed_when_published_addenda_and_attachment(self) -> None:
		tcode, tm2, uname = self._base_portal_tender(status="Published")
		save_file(
			"p1004-public.txt",
			b"hello-p1004",
			"TM2 Tender",
			tm2.name,
			is_private=0,
		)
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2.name,
				"title": "P1004 structural",
				"reason": "Fixture for P10-04 supplier portal addenda list.",
				"status": "Draft",
				"primary_impact_type": "No Structural Impact",
				"affects_deadline": 0,
				"affects_submission_model": 0,
				"affects_opening_model": 0,
				"affects_evaluation_model": 0,
				"affects_contract_model": 0,
				"requires_supplier_acknowledgement": 1,
			}
		)
		ad.flags.ignore_tm2_add_tender_state_gate = True
		ad.insert(ignore_permissions=True)
		frappe.db.set_value(
			"TM2 Addendum",
			ad.name,
			{"status": "Issued", "issued_at": now_datetime(), "issued_by": "Administrator"},
			update_modified=False,
		)
		supplier = frappe.db.get_value(
			"TM2 Supplier Participation",
			{"tm2_tender": tm2.name},
			"supplier",
		)
		self.assertTrue(supplier)
		supplier_code = frappe.db.get_value(
			"TM2 Supplier Participation",
			{"tm2_tender": tm2.name},
			"supplier_code",
		)
		ack = frappe.get_doc(
			{
				"doctype": "TM2 Addendum Acknowledgement",
				"tm2_addendum": ad.name,
				"supplier": supplier,
				"required": 1,
				"acknowledged": 1,
				"acknowledged_by": "Administrator",
				"acknowledged_at": now_datetime(),
			}
		)
		frappe.set_user("Administrator")
		ack.insert(ignore_permissions=True)

		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		dd = out.get("documents_addenda") or {}
		bundle = dd.get("bundle") or {}
		self.assertTrue(bundle.get("download_allowed"), bundle)
		self.assertFalse((bundle.get("download_denial_reason") or "").strip())
		atts = dd.get("attachments") or []
		self.assertTrue(any("p1004-public" in str(a.get("file_name") or "") for a in atts), atts)
		rows = dd.get("addenda") or []
		self.assertTrue(rows, rows)
		self.assertTrue(any("Issued" in str(r.get("summary_line") or "") for r in rows), rows)
		self.assertTrue(
			any(supplier_code and supplier_code in str(r.get("summary_line") or "") for r in rows),
			rows,
		)

		clear_website_cache()
		set_request(method="GET", path=f"/supplier/tenders/{tcode}")
		resp = get_response()
		self.assertEqual(resp.status_code, 200)
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="tm2-supplier-bundle-download-control"', body)
		self.assertIn('data-bundle-download-allowed="1"', body)
