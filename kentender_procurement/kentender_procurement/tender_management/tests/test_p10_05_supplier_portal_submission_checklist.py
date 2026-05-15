# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P10-05 — doc 9 §18.5 supplier portal submission checklist (DSM-only rows).

**EX-05 (doc 9 §25):** ``test_EX_05_*`` methods assert the exit gate — checklist rows derive only
from bound DSM content and no fabricated rows appear when the DSM document is missing.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p10_05_supplier_portal_submission_checklist
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, cstr, now_datetime, set_request
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache

from kentender_procurement.tender_management.derived_models.dsm.schema import dsm_default_boq_rate_entry
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.services.supplier_portal_submission_checklist import (
	build_supplier_portal_submission_checklist,
)
from kentender_procurement.tender_management.services.supplier_portal_tender_detail import (
	get_supplier_portal_tender_detail,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


def _p1005_dsm_content() -> dict:
	return {
		"requirements": [
			{
				"requirement_code": "REQ-DEC-P1005",
				"requirement_type": "Declaration",
				"label": "Fixture declaration",
				"mandatory": True,
				"supplier_action": "Declare",
				"source_trace": {"source_type": "SystemRule"},
			},
			{
				"requirement_code": "REQ-OPT-P1005",
				"requirement_type": "Form",
				"label": "Optional form",
				"mandatory": False,
				"supplier_action": "CompleteForm",
				"source_trace": {"source_type": "Form", "source_form_code": "F-P1005"},
			},
		],
		"boq_rate_entry": dsm_default_boq_rate_entry(enabled=False),
		"addendum_acknowledgements": [
			{"addendum_code": "AD-P1005", "mandatory": True},
		],
	}


class TestP1005SupplierPortalSubmissionChecklist(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		self._p1005_users: list[str] = []
		self._p1005_suppliers: list[str] = []
		self._p1005_profiles: list[str] = []
		self._p1005_groups: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		tm2_names = frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P1005%"]}, pluck="name")
		for row in frappe.get_all(
			"TM2 Bid Submission Component",
			filters={"tm2_tender": ["in", tm2_names] if tm2_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Submission Component", row):
				frappe.delete_doc("TM2 Bid Submission Component", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Bid Submission",
			filters={"tm2_tender": ["in", tm2_names] if tm2_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Submission", row):
				frappe.delete_doc("TM2 Bid Submission", row, force=True, ignore_permissions=True)
		si_names = frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": ["in", tm2_names] if tm2_names else ["__none__"]},
			pluck="name",
		)
		for row in frappe.get_all(
			"Tender STD Generated Output",
			filters={"tender_std_instance": ["in", si_names] if si_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("Tender STD Generated Output", row):
				frappe.delete_doc("Tender STD Generated Output", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender STD Binding",
			filters={"tm2_tender": ["in", tm2_names] if tm2_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender STD Binding", row):
				frappe.delete_doc("TM2 Tender STD Binding", row, force=True, ignore_permissions=True)
		for row in si_names:
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
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P1005%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		for pn in self._p1005_profiles:
			if frappe.db.exists("KTSM Supplier Profile", pn):
				frappe.delete_doc("KTSM Supplier Profile", pn, force=True, ignore_permissions=True)
		for un in self._p1005_users:
			if frappe.db.exists("User", un):
				frappe.delete_doc("User", un, force=True, ignore_permissions=True)
		for sn in self._p1005_suppliers:
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		for gn in self._p1005_groups:
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
		name = f"KT-P1005-{label}"
		if frappe.db.exists("Supplier Group", name):
			if name not in self._p1005_groups:
				self._p1005_groups.append(name)
			return name
		parent = self._parent_supplier_group()
		self.assertTrue(parent, "No parent Supplier Group for P10-05 fixtures")
		frappe.get_doc(
			{
				"doctype": "Supplier Group",
				"supplier_group_name": name,
				"parent_supplier_group": parent,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
		self._p1005_groups.append(name)
		return name

	def _ensure_supplier(self, label: str, *, supplier_group: str) -> str:
		supplier_name = f"P1005 {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			if existing not in self._p1005_suppliers:
				self._p1005_suppliers.append(str(existing))
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
		self._p1005_suppliers.append(doc.name)
		return doc.name

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str, status: str = "Draft") -> Document:
		doc = frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P1005 TM2",
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
			self._p1005_users.append(email)
			return email
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P1005",
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		u.insert(ignore_permissions=True)
		u.append("roles", {"role": "Customer"})
		u.save(ignore_permissions=True)
		self._p1005_users.append(u.name)
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
		self._p1005_profiles.append(p.name)
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

	def _insert_dsm_output(self, si_name: str) -> Document:
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		return frappe.get_doc(
			{
				"doctype": "Tender STD Generated Output",
				"naming_series": "STD-OUT-.#####",
				"tender_std_instance": si_name,
				"output_type": "DSM",
				"version_number": 1,
				"output_status": "Current",
				"source_template_version_code": ver,
				"source_profile_code": prof,
				"content_json": _p1005_dsm_content(),
				"generated_by_job_code": "JOB-P1005-FIXTURE",
				"generated_at": now_datetime(),
			}
		).insert(ignore_permissions=True)

	def _base_portal_tender(self, *, status: str = "Published") -> tuple[str, Document, str, str, str]:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			self.skipTest("KTSM Supplier Profile not installed")
		sg = self._ensure_leaf_supplier_group("chk")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tcode = f"TND-P1005-{frappe.generate_hash(length=4)}"
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tcode, status=status)
		self._mk_access_rule(tm2)
		self._mk_timeline(tm2)
		si = self._mk_std_instance(tm2.name)
		bind = self._mk_binding(tm2.name, si.name)
		dsm = self._insert_dsm_output(si.name)
		frappe.db.set_value(
			"TM2 Tender STD Binding",
			bind.name,
			{
				"bundle_output_code": "GB-P1005-FIXTURE-V1",
				"publication_snapshot_code": "PUBSNAP-P1005-V1",
				"dsm_output_code": dsm.name,
				"dom_output_code": "DOM-P1005-V1",
				"dem_output_code": "DEM-P1005-V1",
				"dcm_output_code": "DCM-P1005-V1",
			},
			update_modified=False,
		)
		sup = self._ensure_supplier("Chk", supplier_group=sg)
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": sup}
		).insert(ignore_permissions=True)
		email = f"p1005-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		return tcode, tm2, uname, sup, si.name

	def test_p10_05_checklist_incomplete_without_bid(self) -> None:
		tcode, tm2, uname, sup, _si = self._base_portal_tender()
		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		cl = out.get("submission_checklist") or {}
		self.assertTrue(cl.get("has_dsm"), cl)
		self.assertEqual(cl.get("dsm_output_code"), frappe.db.get_value("TM2 Tender STD Binding", {"tm2_tender": tm2.name, "is_active": 1}, "dsm_output_code"))
		self.assertFalse(cl.get("all_mandatory_complete"))
		items = cl.get("items") or []
		codes = {i.get("requirement_code") for i in items if i.get("kind") == "requirement"}
		self.assertIn("REQ-DEC-P1005", codes)
		self.assertIn("REQ-OPT-P1005", codes)
		acks = [i for i in items if i.get("kind") == "addendum_ack"]
		self.assertTrue(acks)
		self.assertEqual(acks[0].get("addendum_code"), "AD-P1005")

	def test_p10_05_checklist_complete_with_bid_snapshot_and_component(self) -> None:
		tcode, tm2, uname, sup, si = self._base_portal_tender()
		frappe.set_user("Administrator")
		bid = frappe.get_doc(
			{
				"doctype": "TM2 Bid Submission",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"dsm_output_code": frappe.db.get_value(
					"TM2 Tender STD Binding",
					{"tm2_tender": tm2.name, "is_active": 1},
					"dsm_output_code",
				),
				"tender_std_instance_code": si,
				"publication_snapshot_code": "PUBSNAP-P1005-V1",
				"addendum_acknowledgement_snapshot": {"AD-P1005": True},
			}
		)
		bid.insert(ignore_permissions=True)
		comp = frappe.get_doc(
			{
				"doctype": "TM2 Bid Submission Component",
				"tm2_bid_submission": bid.name,
				"std_submission_requirement_code": "REQ-DEC-P1005",
				"component_type": "OTHER",
				"component_label": "Declaration",
				"required": 0,
				"submitted": 1,
				"validation_status": "Pending",
			}
		)
		comp.flags.ignore_tm2_bsc_dsm_requirement_gate = True
		comp.insert(ignore_permissions=True)

		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		cl = out.get("submission_checklist") or {}
		self.assertTrue(cl.get("all_mandatory_complete"), cl)

	def test_p10_05_checklist_rows_in_portal_html(self) -> None:
		tcode, _tm2, uname, _sup, _si = self._base_portal_tender()
		frappe.set_user(uname)
		clear_website_cache()
		set_request(method="GET", path=f"/supplier/tenders/{tcode}")
		resp = get_response()
		self.assertEqual(resp.status_code, 200)
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="tm2-supplier-submission-checklist"', body)
		self.assertIn('data-testid="tm2-supplier-checklist-row"', body)
		self.assertIn('data-checklist-row="req-dec-p1005"', body)

	def test_EX_05_checklist_rows_derive_only_from_bound_dsm(self) -> None:
		"""Doc 9 §25 EX-05 — rows mirror DSM ``requirements`` / ``addendum_acknowledgements`` (+ optional BOQ rates)."""
		_tcode, tm2, _uname, sup, _si = self._base_portal_tender()
		cl = build_supplier_portal_submission_checklist(tm2.name, sup)
		self.assertTrue(cl.get("has_dsm"), cl)
		dsm_row = cstr(cl.get("dsm_output_code") or "").strip()
		self.assertTrue(dsm_row)
		self.assertEqual(
			dsm_row,
			frappe.db.get_value("TM2 Tender STD Binding", {"tm2_tender": tm2.name, "is_active": 1}, "dsm_output_code"),
		)
		dsm_payload = _p1005_dsm_content()
		expected_req_codes = {
			cstr(r.get("requirement_code") or "").strip()
			for r in (dsm_payload.get("requirements") or [])
			if isinstance(r, dict) and cstr(r.get("requirement_type") or "").strip() not in ("System", "BOQRateEntry")
		}
		expected_req_codes.discard("")
		items = cl.get("items") or []
		for it in items:
			kind = cstr(it.get("kind") or "").strip()
			self.assertIn(kind, ("requirement", "addendum_ack", "boq_rates"), it)
		got_req = {cstr(i.get("requirement_code") or "").strip() for i in items if i.get("kind") == "requirement"}
		self.assertEqual(got_req, expected_req_codes)
		ack_codes = {cstr(i.get("addendum_code") or "").strip() for i in items if i.get("kind") == "addendum_ack"}
		self.assertEqual(ack_codes, {"AD-P1005"})

	def test_EX_05_missing_dsm_output_yields_no_invented_checklist_rows(self) -> None:
		"""Doc 9 §25 EX-05 — no DSM document → ``has_dsm`` false and **no** fabricated requirement rows."""
		sg = self._ensure_leaf_supplier_group("ex05miss")
		plan = self._mk_plan(fiscal_year=2032)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tcode = f"TND-P1005-EX05MISS-{frappe.generate_hash(length=4)}"
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tcode, status="Published")
		self._mk_access_rule(tm2)
		self._mk_timeline(tm2)
		si = self._mk_std_instance(tm2.name)
		bind = self._mk_binding(tm2.name, si.name)
		frappe.db.set_value(
			"TM2 Tender STD Binding",
			bind.name,
			{
				"dsm_output_code": "STD-OUT-NONEXISTENT-EX05",
				"bundle_output_code": "GB-EX05-V1",
				"dom_output_code": "DOM-EX05-V1",
				"dem_output_code": "DEM-EX05-V1",
				"dcm_output_code": "DCM-EX05-V1",
				"publication_snapshot_code": "PUBSNAP-EX05-V1",
			},
			update_modified=False,
		)
		sup = self._ensure_supplier("Ex05Miss", supplier_group=sg)
		cl = build_supplier_portal_submission_checklist(tm2.name, sup)
		self.assertFalse(cl.get("has_dsm"), cl)
		self.assertEqual(cl.get("items"), [])
