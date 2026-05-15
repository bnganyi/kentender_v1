# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P10-06 — doc 9 §18.6 supplier portal Works BOQ editor (locked quantities; editable rates).

**EX-06** (doc 9 §25): ``test_EX_06_*`` assert portal DTO never exposes quantity-edit flags and that
``validate_works_boq_payload`` rejects tampered quantities on the same fixture (``BOQ_QUANTITY_LOCKED``).

**EX-18** (doc 9 §25): ``test_EX_18_*`` — portal **Works BOQ** + **§18.5 submission checklist** both trace the
bound published **DSM**; server rejects quantity tamper (DSM + BOQ locks).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p10_06_supplier_portal_works_boq
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, cstr, now_datetime, set_request
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.supplier_portal_submission_checklist import (
	build_supplier_portal_submission_checklist,
)
from kentender_procurement.tender_management.services.supplier_portal_tender_detail import (
	get_supplier_portal_tender_detail,
)
from kentender_procurement.tender_management.services.validate_works_boq_payload import (
	validate_works_boq_payload,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService, get_boq_for_instance
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestP1006SupplierPortalWorksBoq(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		self._p1006_users: list[str] = []
		self._p1006_suppliers: list[str] = []
		self._p1006_profiles: list[str] = []
		self._p1006_groups: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		tm2_names = frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P1006%"]}, pluck="name")
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
			"Tender STD Instance BOQ",
			filters={"tender_std_instance": ["in", si_names] if si_names else ["__none__"]},
			pluck="name",
		):
			if frappe.db.exists("Tender STD Instance BOQ", row):
				frappe.delete_doc("Tender STD Instance BOQ", row, force=True, ignore_permissions=True)
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
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P1006%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		for pn in self._p1006_profiles:
			if frappe.db.exists("KTSM Supplier Profile", pn):
				frappe.delete_doc("KTSM Supplier Profile", pn, force=True, ignore_permissions=True)
		for un in self._p1006_users:
			if frappe.db.exists("User", un):
				frappe.delete_doc("User", un, force=True, ignore_permissions=True)
		for sn in self._p1006_suppliers:
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		for gn in self._p1006_groups:
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
		name = f"KT-P1006-{label}"
		if frappe.db.exists("Supplier Group", name):
			if name not in self._p1006_groups:
				self._p1006_groups.append(name)
			return name
		parent = self._parent_supplier_group()
		self.assertTrue(parent, "No parent Supplier Group for P10-06 fixtures")
		frappe.get_doc(
			{
				"doctype": "Supplier Group",
				"supplier_group_name": name,
				"parent_supplier_group": parent,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
		self._p1006_groups.append(name)
		return name

	def _ensure_supplier(self, label: str, *, supplier_group: str) -> str:
		supplier_name = f"P1006 {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			if existing not in self._p1006_suppliers:
				self._p1006_suppliers.append(str(existing))
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
		self._p1006_suppliers.append(doc.name)
		return doc.name

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str, status: str = "Draft") -> Document:
		doc = frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P1006 TM2",
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
			self._p1006_users.append(email)
			return email
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P1006",
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		u.insert(ignore_permissions=True)
		u.append("roles", {"role": "Customer"})
		u.save(ignore_permissions=True)
		self._p1006_users.append(u.name)
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
		self._p1006_profiles.append(p.name)
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

	def _seed_boq_and_publish_dsm(self, si_name: str) -> str:
		existing = get_boq_for_instance(si_name)
		if existing:
			frappe.delete_doc("Tender STD Instance BOQ", existing.name, force=True, ignore_permissions=True)
		boq = StdInstanceBoqService.create_boq_for_instance(
			si_name, currency="KES", ignore_boq_publication_lock=True
		)
		boq = StdInstanceBoqService.add_bill(
			boq.name, "B1", "Lot 1", "Works", ignore_boq_publication_lock=True
		)
		bill_code = (boq.boq_bills or [])[0].bill_instance_code
		StdInstanceBoqService.add_item(
			boq.name,
			bill_code,
			"3.1",
			"Reinforced concrete",
			"m3",
			110.0,
			item_type="Normal",
			supplier_input_mode="Rate Only",
			rate_required_from_supplier=True,
			status="Published",
			ignore_boq_publication_lock=True,
		)
		StdInstanceBoqService.add_item(
			boq.name,
			bill_code,
			"8.1",
			"Provisional sum fixture",
			"Sum",
			1.0,
			item_type="Provisional Sum",
			supplier_input_mode="Fixed Amount",
			rate_required_from_supplier=False,
			fixed_amount=3_000_000.0,
			status="Published",
			ignore_boq_publication_lock=True,
		)
		frappe.db.set_value(
			"Tender STD Instance BOQ",
			boq.name,
			"status",
			"Published",
			update_modified=False,
		)
		d = StdInstanceGeneratedOutputService.generate_dsm(
			si_name,
			ignore_generated_output_lock=True,
			generated_by_job_code="JOB-P1006-BOQ",
		)
		StdInstanceGeneratedOutputService.publish_output(
			d.name,
			ignore_generated_output_immutability=True,
		)
		return str(d.name)

	def _base_works_portal_with_boq(self) -> tuple[str, Document, str]:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			self.skipTest("KTSM Supplier Profile not installed")
		sg = self._ensure_leaf_supplier_group("boq")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tcode = f"TND-P1006-{frappe.generate_hash(length=4)}"
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tcode, status="Published")
		self._mk_access_rule(tm2)
		self._mk_timeline(tm2)
		si = self._mk_std_instance(tm2.name)
		bind = self._mk_binding(tm2.name, si.name)
		dsm_name = self._seed_boq_and_publish_dsm(si.name)
		frappe.db.set_value(
			"TM2 Tender STD Binding",
			bind.name,
			{
				"bundle_output_code": "GB-P1006-FIXTURE-V1",
				"publication_snapshot_code": "PUBSNAP-P1006-V1",
				"dsm_output_code": dsm_name,
				"dom_output_code": "DOM-P1006-V1",
				"dem_output_code": "DEM-P1006-V1",
				"dcm_output_code": "DCM-P1006-V1",
			},
			update_modified=False,
		)
		sup = self._ensure_supplier("Boq", supplier_group=sg)
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": sup}
		).insert(ignore_permissions=True)
		email = f"p1006-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		return tcode, tm2, uname

	def test_EX_18_portal_dsm_drives_boq_panel_submission_checklist_and_locks_quantities(self) -> None:
		"""Doc 9 §25 EX-18 — DSM output binds Works BOQ + §18.5 checklist; quantities locked (§11.4)."""
		tcode, tm2, uname = self._base_works_portal_with_boq()
		sup = frappe.db.get_value(
			"TM2 Supplier Participation",
			{"tm2_tender": tm2.name},
			"supplier",
		)
		self.assertTrue(sup)
		dsm_binding = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2.name, "is_active": 1},
			"dsm_output_code",
		)
		self.assertTrue(dsm_binding)

		frappe.set_user(uname)
		detail = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(detail.get("ok"), detail)
		bq = detail.get("works_boq") or {}
		self.assertTrue(bq.get("show_panel"), bq)
		self.assertTrue(bq.get("dsm_boq_rates_enabled"), bq)
		sc_embed = (detail.get("submission_checklist") or {}) if isinstance(detail.get("submission_checklist"), dict) else {}
		self.assertEqual(cstr(sc_embed.get("dsm_output_code") or "").strip(), cstr(dsm_binding).strip())
		tpl = (detail.get("submit_bid_panel") or {}).get("bid_payload_template") or {}
		self.assertEqual(cstr(tpl.get("dsm_output_code") or "").strip(), cstr(dsm_binding).strip())

		cl = build_supplier_portal_submission_checklist(tm2.name, str(sup))
		self.assertTrue(cl.get("has_dsm"), cl)
		self.assertEqual(cstr(cl.get("dsm_output_code") or "").strip(), cstr(dsm_binding).strip())
		kinds = {cstr(i.get("kind") or "").strip() for i in (cl.get("items") or [])}
		self.assertIn("boq_rates", kinds)

		lines = [{"item_number": "3.1", "rate": 100.0, "quantity": 109.0}]
		v = validate_works_boq_payload(tcode, str(sup), {"lines": lines})
		self.assertFalse(v.get("ok"), v)
		self.assertEqual(v.get("denial_code"), DenialCode.BOQ_QUANTITY_LOCKED.value)

	def test_EX_06_portal_boq_rows_never_expose_quantity_edit_flags(self) -> None:
		"""Doc 9 §25 EX-06 — DTO rows carry PE quantity as data only; no quantity-editable flags."""
		tcode, _tm2, uname = self._base_works_portal_with_boq()
		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		rows = (out.get("works_boq") or {}).get("rows") or []
		forbidden = frozenset({"quantity_editable", "editable_quantity", "supplier_quantity", "quantity_input"})
		for row in rows:
			self.assertFalse(forbidden & row.keys(), row)
		by_num = {r["item_number"]: r for r in rows}
		self.assertEqual(by_num["3.1"]["quantity"], 110.0)
		self.assertEqual(by_num["8.1"]["quantity"], 1.0)

	def test_EX_06_validate_works_boq_payload_rejects_quantity_tamper(self) -> None:
		"""Same P10-06 fixture: wrong optional quantity echo → ``BOQ_QUANTITY_LOCKED`` (§11.4)."""
		tcode, tm2, _uname = self._base_works_portal_with_boq()
		sup = frappe.db.get_value(
			"TM2 Supplier Participation",
			{"tm2_tender": tm2.name},
			"supplier",
		)
		self.assertTrue(sup)
		lines = [{"item_number": "3.1", "rate": 100.0, "quantity": 109.0}]
		out = validate_works_boq_payload(tcode, str(sup), {"lines": lines})
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_QUANTITY_LOCKED.value)

	def test_p10_06_works_boq_detail_rows_and_flags(self) -> None:
		tcode, tm2, uname = self._base_works_portal_with_boq()
		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		bq = out.get("works_boq") or {}
		self.assertTrue(bq.get("show_panel"), bq)
		self.assertTrue(bq.get("dsm_boq_rates_enabled"), bq)
		rows = bq.get("rows") or []
		self.assertEqual(len(rows), 2, rows)
		by_num = {r["item_number"]: r for r in rows}
		self.assertTrue(by_num["3.1"]["rate_editable"])
		self.assertFalse(by_num["8.1"]["rate_editable"])
		self.assertGreater(by_num["8.1"]["line_locked_amount"], 0)

	def test_p10_06_non_works_no_boq_panel(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			self.skipTest("KTSM Supplier Profile not installed")
		sg = self._ensure_leaf_supplier_group("nw")
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tcode = f"TND-P1006-{frappe.generate_hash(length=4)}"
		tm2 = frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P1006 Goods",
				"tender_code": tcode,
				"procurement_package": pkg.name,
				"procurement_plan": plan.name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
				"procuring_entity_code": "MOH",
				"procurement_method": "Open Tender",
				"status": "Published",
			}
		).insert(ignore_permissions=True)
		self._mk_access_rule(tm2)
		self._mk_timeline(tm2)
		si = self._mk_std_instance(tm2.name)
		self._mk_binding(tm2.name, si.name)
		sup = self._ensure_supplier("Nw", supplier_group=sg)
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": sup}
		).insert(ignore_permissions=True)
		email = f"p1006nw-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		bq = out.get("works_boq") or {}
		self.assertFalse(bq.get("show_panel"))

	def test_p10_06_portal_html_quantity_and_rate_controls(self) -> None:
		tcode, _tm2, uname = self._base_works_portal_with_boq()
		frappe.set_user(uname)
		clear_website_cache()
		set_request(method="GET", path=f"/supplier/tenders/{tcode}")
		resp = get_response()
		self.assertEqual(resp.status_code, 200)
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="tm2-supplier-works-boq-editor"', body)
		self.assertIn('data-testid="tm2-supplier-boq-row"', body)
		self.assertIn('data-testid="tm2-supplier-boq-quantity"', body)
		self.assertIn('data-boq-row="3.1"', body)
		self.assertIn('data-testid="tm2-supplier-boq-rate-input"', body)
		self.assertIn('data-testid="tm2-supplier-boq-rate-locked"', body)
		self.assertIn('min="0"', body)
