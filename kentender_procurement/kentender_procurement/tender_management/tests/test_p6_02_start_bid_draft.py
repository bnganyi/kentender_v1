# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-02 — doc 9 §11.2 ``start_bid_draft`` / ``save_bid_draft``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p6_02_start_bid_draft
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.start_bid_draft import (
	saveBidDraft,
	save_bid_draft,
	startBidDraft,
	start_bid_draft,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP602StartBidDraft(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P602"

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

	def _portal_ctx(self) -> dict:
		spec_s = spec_for_action("BID2_START_DRAFT")
		spec_v = spec_for_action("BID2_SAVE_DRAFT")
		self.assertTrue(spec_s and spec_v)
		assert spec_s is not None and spec_v is not None
		return {
			"granted_permissions": [spec_s.required_permission, spec_v.required_permission],
		}

	def test_p6_02_draft_tender_denied(self) -> None:
		self._ensure_std_bindable()
		tcode = self._mk_approved_for_publication(seed_outputs=False)
		out = start_bid_draft(
			"Administrator",
			tcode,
			"irrelevant-supplier",
			context={**self._portal_ctx(), "acting_supplier": "irrelevant-supplier"},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p6_02_success_metadata_only_idempotent_save(self) -> None:
		tcode, tm2, sup = self._published_with_supplier()
		ctx = {
			**self._portal_ctx(),
			"acting_supplier": sup,
		}
		out = start_bid_draft("Administrator", tcode, sup, context=ctx)
		self.assertTrue(out.get("ok"), out)
		self.assertNotIn("validation_summary", out)
		self.assertTrue(out.get("draft_metadata_code"))
		self.assertTrue(out.get("dsm_output_code"))
		self.assertFalse(out.get("idempotent"))

		out2 = startBidDraft("Administrator", tcode, sup, context=ctx)
		self.assertTrue(out2.get("ok"), out2)
		self.assertTrue(out2.get("idempotent"))
		self.assertNotIn("validation_summary", out2)

		sv = save_bid_draft("Administrator", tcode, sup, context=ctx)
		self.assertTrue(sv.get("ok"), sv)
		self.assertNotIn("validation_summary", sv)
		self.assertEqual(frappe.db.get_value("TM2 Bid Draft Metadata", out.get("bid_draft_metadata"), "draft_status"), "Saved")

		sv2 = saveBidDraft("Administrator", tcode, sup, context=ctx)
		self.assertTrue(sv2.get("ok"), sv2)

	def test_p6_02_role_denied_without_permission(self) -> None:
		tcode, _tm2, sup = self._published_with_supplier()
		out = start_bid_draft(
			"Administrator",
			tcode,
			sup,
			context={"granted_permissions": [], "acting_supplier": sup},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p6_02_deadline_passed_denied(self) -> None:
		tcode, tm2, sup = self._published_with_supplier()
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)
		out = start_bid_draft(
			"Administrator",
			tcode,
			sup,
			context={**self._portal_ctx(), "acting_supplier": sup},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_DEADLINE_PASSED.value)

	def test_p6_02_no_participation_denied(self) -> None:
		tcode, tm2, sup = self._published_with_supplier()
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tm2_tender": tm2, "supplier": sup},
			pluck="name",
		):
			frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		out = start_bid_draft(
			"Administrator",
			tcode,
			sup,
			context={**self._portal_ctx(), "acting_supplier": sup},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)

	def test_p6_02_acting_supplier_mismatch_denied(self) -> None:
		tcode, _tm2, sup = self._published_with_supplier()
		other = self._ensure_supplier("Beta")
		out = start_bid_draft(
			"Administrator",
			tcode,
			sup,
			context={**self._portal_ctx(), "acting_supplier": other},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)

	def test_p6_02_dsm_missing_denied(self) -> None:
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		frappe.db.set_value("Tender STD Instance", si, "current_dsm_output_code", None, update_modified=False)
		out = start_bid_draft(
			"Administrator",
			tcode,
			sup,
			context={**self._portal_ctx(), "acting_supplier": sup},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_DSM_MISSING_OR_STALE.value)

	def test_p6_02_addendum_ack_required_denied(self) -> None:
		tcode, tm2, sup = self._published_with_supplier()
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2,
				"title": "P602 ack gate",
				"reason": "Fixture for P6-02 addendum acknowledgement gate.",
				"requires_supplier_acknowledgement": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("TM2 Addendum", ad.name, "status", "Issued", update_modified=False)
		out = start_bid_draft(
			"Administrator",
			tcode,
			sup,
			context={**self._portal_ctx(), "acting_supplier": sup},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ADDENDUM_ACK_REQUIRED.value)

	def test_p6_02_save_without_start_denied(self) -> None:
		tcode, _tm2, sup = self._published_with_supplier()
		out = save_bid_draft(
			"Administrator",
			tcode,
			sup,
			context={**self._portal_ctx(), "acting_supplier": sup},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p6_02_supplier_ineligible_denied(self) -> None:
		tcode, _tm2, sup = self._published_with_supplier()
		frappe.db.set_value("Supplier", sup, "disabled", 1, update_modified=False)
		self.addCleanup(lambda: frappe.db.set_value("Supplier", sup, "disabled", 0, update_modified=False))
		out = start_bid_draft(
			"Administrator",
			tcode,
			sup,
			context={**self._portal_ctx(), "acting_supplier": sup},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)
