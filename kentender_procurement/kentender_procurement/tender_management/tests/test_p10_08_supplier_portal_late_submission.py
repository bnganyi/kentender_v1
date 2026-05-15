# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P10-08 — doc 9 §18.8 supplier portal late submission message (§21.3 item 9: official server time).

Canonical doc 9 §21.3 Q-05 **item 9**: ``apps/kentender_v1/tests/ui/tm2_supplier_submission.spec.ts``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p10_08_supplier_portal_late_submission
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime, set_request
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache

from kentender_procurement.tender_management.api.supplier_portal import submit_supplier_portal_bid
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.supplier_portal_tender_detail import (
	get_supplier_portal_tender_detail,
)
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import _P401Tm2Cleanup
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture


class TestP1008SupplierPortalLateSubmission(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P1008"

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
			update_modified=False,
		)

	def setUp(self) -> None:
		super().setUp()
		self._p602_suppliers_created: list[str] = []
		self._p1008_users: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for un in self._p1008_users:
			if frappe.db.exists("User", un):
				frappe.delete_doc("User", un, force=True, ignore_permissions=True)
		self._p1008_users.clear()
		super().tearDown()

	def _mk_portal_user(self, email: str) -> str:
		if frappe.db.exists("User", email):
			self._p1008_users.append(email)
			return email
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P1008",
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		u.insert(ignore_permissions=True)
		u.append("roles", {"role": "Customer"})
		u.save(ignore_permissions=True)
		self._p1008_users.append(u.name)
		return u.name

	def _mk_ktsm_profile(self, *, supplier: str, external_user: str) -> str | None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return None
		existing = frappe.db.get_value("KTSM Supplier Profile", {"erpnext_supplier": supplier}, "name")
		if existing:
			frappe.db.set_value(
				"KTSM Supplier Profile",
				existing,
				"external_user",
				external_user,
				update_modified=False,
			)
			return str(existing)
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
		self.addCleanup(
			lambda: frappe.delete_doc("KTSM Supplier Profile", p.name, force=True, ignore_permissions=True)
			if frappe.db.exists("KTSM Supplier Profile", p.name)
			else None
		)
		return p.name

	def test_p10_08_late_notice_shows_official_server_time_and_deadline(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup = self._published_with_supplier()
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), hours=-2)},
			update_modified=False,
		)

		email = f"p1008-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)

		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		self.assertTrue((out.get("server_time_display") or "").strip())
		sb = out.get("submit_bid_panel") or {}
		self.assertTrue(sb.get("deadline_passed"), sb)
		ls = sb.get("late_submission_notice") or {}
		self.assertTrue(ls.get("visible"), ls)
		self.assertIn("official server time", (ls.get("lead_message") or "").lower())
		self.assertEqual(ls.get("official_server_time_label"), out.get("server_time_display"))
		self.assertEqual(ls.get("deadline_label"), out.get("submission_deadline_display"))

	def test_p10_08_portal_html_late_panel_selectors(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup = self._published_with_supplier()
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), minutes=-45)},
			update_modified=False,
		)
		email = f"p1008h-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		srv = (out.get("server_time_display") or "").strip()
		self.assertTrue(srv)

		clear_website_cache()
		set_request(method="GET", path=f"/supplier/tenders/{tcode}")
		resp = get_response()
		self.assertEqual(resp.status_code, 200)
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="tm2-supplier-late-submission-message"', body)
		self.assertIn('data-testid="tm2-supplier-late-official-server-time-line"', body)
		self.assertIn(srv, body)

	def test_p10_08_submit_api_deadline_denied_no_receipt(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)
		email = f"p1008s-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		frappe.set_user(uname)
		out = submit_supplier_portal_bid(tender_code=tcode, bid_payload=bid)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_DEADLINE_PASSED.value)
		self.assertTrue(out.get("late_attempt") or out.get("late_attempt_code"))
