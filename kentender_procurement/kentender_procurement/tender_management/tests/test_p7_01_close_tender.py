# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-01 — doc 9 §12.1 ``close_tender`` / ``closeTender``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p7_01_close_tender
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.close_tender import closeTender, close_tender
from kentender_procurement.tender_management.services.create_addendum import create_addendum
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture


class TestP701CloseTender(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P701"

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

	def _close_ctx(self) -> dict:
		spec = spec_for_action("CLS2_CLOSE_TENDER")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _portal_submit_ctx(self) -> dict:
		spec = spec_for_action("BID2_SUBMIT")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _published_si_supplier(self) -> tuple[str, str, str, str]:
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		assert si
		return tcode, tm2, sup, str(si)

	def _past_deadline(self, tm2: str) -> None:
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)

	def test_p7_01_close_happy_one_sealed_bid(self) -> None:
		tcode, tm2, sup, si = self._published_si_supplier()
		ctx_s = {**self._portal_submit_ctx(), "acting_supplier": sup}
		out_b = submit_bid("Administrator", tcode, sup, _valid_bid_for_fixture(tcode, sup, si), context=ctx_s)
		self.assertTrue(out_b.get("ok"), out_b)
		self._past_deadline(tm2)
		out = close_tender("Administrator", tcode, context=self._close_ctx())
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("tender_status"), "Closed")
		self.assertEqual(out.get("valid_submission_count"), 1)
		self.assertEqual(out.get("closing_code"), f"CLS-{tcode}")
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2, "status"), "Closed")
		cl = frappe.get_doc("TM2 Tender Closing Record", out.get("tm2_tender_closing_record"))
		self.assertEqual(cl.closing_status, "Closed On Time")
		self.assertEqual(int(cl.valid_submission_count or 0), 1)
		self.assertEqual(int(cl.withdrawn_submission_count or 0), 0)
		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Tender Closed"},
			pluck="name",
		)
		self.assertEqual(len(ev), 1)

	def test_p7_01_close_no_valid_submissions(self) -> None:
		tcode, tm2, _sup, _si = self._published_si_supplier()
		self._past_deadline(tm2)
		out = closeTender("Administrator", tcode, context=self._close_ctx())
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("tender_status"), "Closed - No Valid Submissions")
		self.assertEqual(out.get("valid_submission_count"), 0)
		cl = frappe.get_doc("TM2 Tender Closing Record", out.get("tm2_tender_closing_record"))
		self.assertEqual(cl.closing_status, "Closed With No Valid Submissions")
		self.assertEqual(int(cl.no_valid_submissions or 0), 1)

	def test_p7_01_close_before_deadline_denied(self) -> None:
		tcode, tm2, _sup, _si = self._published_si_supplier()
		out = close_tender("Administrator", tcode, context=self._close_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p7_01_close_blocked_by_draft_addendum(self) -> None:
		tcode, tm2, _sup, _si = self._published_si_supplier()
		self._past_deadline(tm2)
		spec_add = spec_for_action("ADD2_CREATE")
		self.assertIsNotNone(spec_add)
		assert spec_add is not None
		aout = create_addendum(
			"Administrator",
			tcode,
			payload={
				"title": "P701 close block",
				"reason": "Fixture addendum for close tender gate.",
				"primary_impact_type": "No Structural Impact",
			},
			context={"granted_permissions": [spec_add.required_permission]},
		)
		self.assertTrue(aout.get("ok"), aout)
		out = close_tender("Administrator", tcode, context=self._close_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p7_01_close_idempotent_second_call_denied(self) -> None:
		tcode, tm2, _sup, _si = self._published_si_supplier()
		self._past_deadline(tm2)
		ctx = self._close_ctx()
		out1 = close_tender("Administrator", tcode, context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		out2 = close_tender("Administrator", tcode, context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p7_01_close_role_denied_without_permission(self) -> None:
		tcode, tm2, _sup, _si = self._published_si_supplier()
		self._past_deadline(tm2)
		out = close_tender("Administrator", tcode, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p7_01_close_draft_tender_denied(self) -> None:
		self._ensure_std_bindable()
		tcode = self._mk_approved_for_publication(seed_outputs=False)
		out = close_tender("Administrator", tcode, context=self._close_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)
