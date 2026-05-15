# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-06 — doc 9 §11.6 late submission (``record_late_submission_attempt`` + ``submit_bid`` gate).

Doc 9 §25 **EX-14** (exit gate): late ``submit_bid`` creates **TM2 Late Submission Attempt**, not
**TM2 Bid Submission** — ``test_EX_14_*``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p6_06_record_late_submission_attempt
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.record_late_submission_attempt import (
	recordLateSubmissionAttempt,
	record_late_submission_attempt,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture


class TestP606RecordLateSubmissionAttempt(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P606"

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

	def _assert_submit_bid_past_deadline_records_late_attempt_not_bid(self) -> None:
		"""§11.6 / §25 EX-14 — ``AUTH_DEADLINE_PASSED`` + late row + audit; bid count unchanged."""
		tcode, tm2, sup, si = self._published_si_supplier()
		ctx = {**self._portal_submit_ctx(), "acting_supplier": sup}
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)
		bid_count_before = frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2, "supplier": sup})
		late_count_before = frappe.db.count("TM2 Late Submission Attempt", {"tm2_tender": tm2, "supplier": sup})
		bid = _valid_bid_for_fixture(tcode, sup, si)
		out = submit_bid("Administrator", tcode, sup, bid, context=ctx)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_DEADLINE_PASSED.value)
		self.assertTrue(out.get("late_attempt"))
		self.assertTrue(out.get("late_attempt_code"))
		self.assertEqual(
			bid_count_before,
			frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2, "supplier": sup}),
		)
		self.assertEqual(
			late_count_before + 1,
			frappe.db.count("TM2 Late Submission Attempt", {"tm2_tender": tm2, "supplier": sup}),
		)
		late_name = str(out.get("late_attempt"))
		self.assertTrue(frappe.db.exists("TM2 Late Submission Attempt", late_name))
		meta = frappe.db.get_value("TM2 Late Submission Attempt", late_name, "attempted_payload_metadata")
		if isinstance(meta, str):
			meta = json.loads(meta or "{}")
		self.assertIsInstance(meta, dict)
		self.assertIn("dsm_output_code", meta)
		aud = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={
				"tm2_tender": tm2,
				"event_type": "Late Submission Rejected",
				"related_object_id": late_name,
			},
			pluck="name",
		)
		self.assertEqual(len(aud), 1)
		self.assertEqual(
			frappe.db.get_value("TM2 Tender Audit Event", aud[0], "denial_code"),
			DenialCode.AUTH_DEADLINE_PASSED.value,
		)

	def test_p6_06_submit_bid_after_deadline_records_attempt_no_bid(self) -> None:
		self._assert_submit_bid_past_deadline_records_late_attempt_not_bid()

	def test_EX_14_late_submission_creates_late_attempt_not_bid_submission(self) -> None:
		"""Doc 9 §25 / doc 8 — post-deadline bid path records **TM2 Late Submission Attempt** only."""
		self._assert_submit_bid_past_deadline_records_late_attempt_not_bid()

	def test_p6_06_record_late_submission_attempt_standalone(self) -> None:
		tcode, tm2, sup, si = self._published_si_supplier()
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)
		bid = _valid_bid_for_fixture(tcode, sup, si)
		out = record_late_submission_attempt(
			"Administrator",
			tcode,
			sup,
			{"acting_supplier": sup},
			bid_payload=bid,
		)
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(out.get("recorded"))
		self.assertTrue(out.get("late_attempt_code"))
		out2 = recordLateSubmissionAttempt(
			"Administrator",
			tcode,
			sup,
			{"acting_supplier": sup},
			bid_payload=bid,
		)
		self.assertTrue(out2.get("ok"), out2)
		self.assertNotEqual(out.get("late_attempt_code"), out2.get("late_attempt_code"))

	def test_p6_06_record_late_before_deadline_denied(self) -> None:
		tcode, tm2, sup, si = self._published_si_supplier()
		bid = _valid_bid_for_fixture(tcode, sup, si)
		before = frappe.db.count("TM2 Late Submission Attempt", {"tm2_tender": tm2, "supplier": sup})
		out = record_late_submission_attempt(
			"Administrator",
			tcode,
			sup,
			{"acting_supplier": sup},
			bid_payload=bid,
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
		after = frappe.db.count("TM2 Late Submission Attempt", {"tm2_tender": tm2, "supplier": sup})
		self.assertEqual(before, after)