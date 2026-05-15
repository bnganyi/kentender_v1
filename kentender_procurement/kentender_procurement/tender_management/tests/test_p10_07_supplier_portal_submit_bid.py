# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P10-07 — doc 9 §18.7 supplier portal submit bid modal + §21.3 item 8 addendum gate.

**EX-07** (doc 9 §25 / doc 8 TM2-SMOKE-WORKS-004): ``test_EX_07_*`` — submission rejects
evaluation-stage arithmetic / correction fields on the bid payload, and sealed totals follow
uncorrected BOQ math only.

Canonical doc 9 §21.3 Q-05 **item 8**: ``apps/kentender_v1/tests/ui/tm2_supplier_submission.spec.ts``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p10_07_supplier_portal_submit_bid
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr, flt, set_request
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
from kentender_procurement.tender_management.tests.tm2_works_boq_supplier_fixture import Tm2WorksBoqSupplierFixture


class TestP1007SupplierPortalSubmitBid(Tm2WorksBoqSupplierFixture, _P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P1007"

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
		self._p1007_users: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for un in self._p1007_users:
			if frappe.db.exists("User", un):
				frappe.delete_doc("User", un, force=True, ignore_permissions=True)
		self._p1007_users.clear()
		super().tearDown()

	def _mk_portal_user(self, email: str) -> str:
		if frappe.db.exists("User", email):
			self._p1007_users.append(email)
			return email
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P1007",
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		u.insert(ignore_permissions=True)
		u.append("roles", {"role": "Customer"})
		u.save(ignore_permissions=True)
		self._p1007_users.append(u.name)
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

	def test_p10_07_submit_panel_flags_pending_tm2_addendum(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup = self._published_with_supplier()
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2,
				"title": "P1007 ack gate",
				"reason": "Fixture for P10-07 addendum acknowledgement gate.",
				"requires_supplier_acknowledgement": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("TM2 Addendum", ad.name, "status", "Issued", update_modified=False)

		email = f"p1007-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)

		frappe.set_user(uname)
		out = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(out.get("ok"), out)
		panel = out.get("submit_bid_panel") or {}
		self.assertFalse(panel.get("addendum_ack_complete"), panel)
		self.assertTrue(panel.get("submit_disabled_by_addendum_ack"), panel)
		self.assertTrue(panel.get("pending_addendum_codes"), panel)

	def test_p10_07_submit_api_denied_when_tm2_addendum_ack_missing(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2,
				"title": "P1007 submit deny",
				"reason": "Fixture for P10-07 submit denial.",
				"requires_supplier_acknowledgement": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("TM2 Addendum", ad.name, "status", "Issued", update_modified=False)

		email = f"p1007b-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		bid = _valid_bid_for_fixture(tcode, sup, str(si))

		frappe.set_user(uname)
		out = submit_supplier_portal_bid(tender_code=tcode, bid_payload=bid)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ADDENDUM_ACK_REQUIRED.value)
		self.assertTrue(out.get("pending_addendum_codes"), out)

	def test_p10_07_submit_happy_path_whitelist(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		email = f"p1007c-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		bid = _valid_bid_for_fixture(tcode, sup, str(si))

		frappe.set_user(uname)
		detail = get_supplier_portal_tender_detail(uname, tcode)
		self.assertTrue(detail.get("ok"), detail)
		panel = detail.get("submit_bid_panel") or {}
		self.assertTrue(panel.get("addendum_ack_complete"), panel)

		out = submit_supplier_portal_bid(tender_code=tcode, bid_payload=bid)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("bid_status"), "Sealed")

	def test_EX_07_portal_submit_rejects_corrected_evaluated_price_field(self) -> None:
		"""Doc 9 §25 EX-07 — portal ``submit_supplier_portal_bid`` denies evaluation-style correction keys."""
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		email = f"p1007ex07a-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		bad = {**bid, "corrected_evaluated_price": 96_754_000}

		frappe.set_user(uname)
		out = submit_supplier_portal_bid(tender_code=tcode, bid_payload=bad)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value)

	def test_EX_07_portal_submit_rejects_boq_line_arithmetic_key(self) -> None:
		"""EX-07 — BOQ lines may only carry ``item_number`` / ``rate`` / optional ``quantity``."""
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup, si = self._published_si_supplier_boq()
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		self.assertTrue(bid.get("boq"), bid)
		rows = list(bid["boq"])
		rows[0] = {**rows[0], "boq_arithmetic_correction": {}}
		bid["boq"] = rows

		email = f"p1007ex07b-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)

		frappe.set_user(uname)
		out = submit_supplier_portal_bid(tender_code=tcode, bid_payload=bid)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value)

	def test_EX_07_sealed_submission_total_matches_uncorrected_boq_math(self) -> None:
		"""EX-07 — stored ``total_submitted_price`` is PE qty × supplier rate (no correction path)."""
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup, si = self._published_si_supplier_boq()
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		self.assertTrue(bid.get("boq"), bid)
		rate = flt(bid["boq"][0].get("rate"))
		boq_name = frappe.db.get_value("Tender STD Instance BOQ", {"tender_std_instance": si}, "name")
		self.assertTrue(boq_name)
		item_num = cstr(bid["boq"][0].get("item_number") or "").strip()
		qty = flt(
			frappe.db.get_value(
				"Tender STD Instance BOQ Item",
				{"parent": boq_name, "item_number": item_num},
				"quantity",
			)
		)
		# Mirrors ``submit_bid._compute_total_and_currency``: rate lines (qty × rate) + locked PE amounts.
		extra_locked = 0.0
		for row in frappe.get_all(
			"Tender STD Instance BOQ Item",
			{"parent": boq_name},
			["item_number", "rate_required_from_supplier", "fixed_amount", "provisional_sum_amount"],
		):
			if cstr(row.get("item_number") or "").strip() == item_num:
				continue
			if not row.get("rate_required_from_supplier"):
				lock_val = flt(row.get("fixed_amount")) or flt(row.get("provisional_sum_amount"))
				if lock_val:
					extra_locked += lock_val
		expected_total = int(round(qty * rate + extra_locked))

		email = f"p1007ex07c-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)

		frappe.set_user(uname)
		out = submit_supplier_portal_bid(tender_code=tcode, bid_payload=bid)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("total_submitted_price"), expected_total)
		db_total = frappe.db.get_value("TM2 Bid Submission", {"tm2_tender": tm2, "supplier": sup}, "total_submitted_price")
		self.assertEqual(int(flt(db_total)), expected_total)

	def test_p10_07_detail_page_html_addendum_gate_attrs(self) -> None:
		if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
			return
		tcode, tm2, sup = self._published_with_supplier()
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2,
				"title": "P1007 html",
				"reason": "Fixture for P10-07 HTML gate.",
				"requires_supplier_acknowledgement": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("TM2 Addendum", ad.name, "status", "Issued", update_modified=False)

		email = f"p1007d-{frappe.generate_hash(length=6)}@example.com"
		uname = self._mk_portal_user(email)
		self._mk_ktsm_profile(supplier=sup, external_user=uname)

		frappe.set_user(uname)
		clear_website_cache()
		set_request(method="GET", path=f"/supplier/tenders/{tcode}")
		resp = get_response()
		self.assertEqual(resp.status_code, 200)
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="tm2-supplier-action-submit-bid"', body)
		self.assertIn('data-submit-disabled-by-addendum="1"', body)
