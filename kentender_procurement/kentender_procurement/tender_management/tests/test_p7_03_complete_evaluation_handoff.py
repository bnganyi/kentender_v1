# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-03 — doc 9 §12.3 ``complete_evaluation_handoff`` / ``completeEvaluationHandoff``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p7_03_complete_evaluation_handoff
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.close_tender import close_tender
from kentender_procurement.tender_management.services.complete_evaluation_handoff import (
	completeEvaluationHandoff,
	complete_evaluation_handoff,
)
from kentender_procurement.tender_management.services.prepare_opening_readiness import prepare_opening_readiness
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture


class TestP703CompleteEvaluationHandoff(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P703"

	def setUp(self) -> None:
		super().setUp()
		self._p602_suppliers_created: list[str] = []

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

	def _close_ctx(self) -> dict:
		spec = spec_for_action("CLS2_CLOSE_TENDER")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _prepare_ctx(self) -> dict:
		spec = spec_for_action("OR2_PREPARE_OPENING_READINESS")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _eval_handoff_ctx(self) -> dict:
		spec = spec_for_action("EV2_PREPARE_EVALUATION_HANDOFF")
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

	def _closed_prepared_opening_completed(self) -> tuple[str, str, str, str]:
		"""Close → ORR → Opening Completed + ORR opening ref + bid Opened. Returns tcode, tm2, si, opn_code."""
		tcode, tm2, sup, si = self._published_si_supplier()
		ctx_s = {**self._portal_submit_ctx(), "acting_supplier": sup}
		out_b = submit_bid("Administrator", tcode, sup, _valid_bid_for_fixture(tcode, sup, si), context=ctx_s)
		self.assertTrue(out_b.get("ok"), out_b)
		self._past_deadline(tm2)
		out_c = close_tender("Administrator", tcode, context=self._close_ctx())
		self.assertTrue(out_c.get("ok"), out_c)
		out_p = prepare_opening_readiness("Administrator", tcode, context=self._prepare_ctx())
		self.assertTrue(out_p.get("ok"), out_p)
		self.assertEqual(out_p.get("tender_status"), "Opening Ready")
		opn = f"OPN-{tcode}-001"
		orr_name = str(out_p.get("tm2_opening_readiness_record") or "")
		self.assertTrue(orr_name)
		frappe.db.set_value(
			"TM2 Opening Readiness Record",
			orr_name,
			{"opening_record_code": opn},
			update_modified=False,
		)
		bid = frappe.db.get_value("TM2 Bid Submission", {"tm2_tender": tm2}, "name")
		self.assertTrue(bid)
		frappe.db.set_value("TM2 Bid Submission", bid, {"bid_status": "Opened"}, update_modified=False)
		frappe.db.set_value("TM2 Tender", tm2, {"status": "Opening Completed"}, update_modified=False)
		return tcode, tm2, si, opn

	def test_p7_03_handoff_happy_path(self) -> None:
		tcode, tm2, si, opn = self._closed_prepared_opening_completed()
		out = complete_evaluation_handoff(
			"Administrator",
			tcode,
			opn,
			context=self._eval_handoff_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("tender_status"), "Evaluation Ready")
		self.assertEqual(out.get("evaluation_handoff_code"), f"EHR-{tcode}")
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2, "status"), "Evaluation Ready")
		ehr_name = str(out.get("tm2_evaluation_handoff_record") or "")
		self.assertTrue(ehr_name)
		ehr = frappe.get_doc("TM2 Evaluation Handoff Record", ehr_name)
		self.assertEqual(ehr.handoff_status, "Ready")
		self.assertEqual(ehr.opening_record_code, opn)
		self.assertEqual(ehr.tender_std_instance_code, si)
		refs_raw = ehr.opened_submission_refs
		refs = json.loads(refs_raw) if isinstance(refs_raw, str) else refs_raw
		self.assertEqual(len(refs.get("refs")), 1)
		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Evaluation Handoff Completed"},
			pluck="name",
		)
		self.assertEqual(len(ev), 1)

	def test_p7_03_handoff_not_opening_completed_denied(self) -> None:
		tcode, tm2, _si, opn = self._closed_prepared_opening_completed()
		frappe.db.set_value("TM2 Tender", tm2, {"status": "Opening Ready"}, update_modified=False)
		out = complete_evaluation_handoff(
			"Administrator",
			tcode,
			opn,
			context=self._eval_handoff_ctx(),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p7_03_handoff_missing_readiness_denied(self) -> None:
		tcode, tm2, _si, opn = self._closed_prepared_opening_completed()
		orr = frappe.db.get_value("TM2 Opening Readiness Record", {"tm2_tender": tm2}, "name")
		self.assertTrue(orr)
		frappe.delete_doc("TM2 Opening Readiness Record", orr, force=True, ignore_permissions=True)
		out = complete_evaluation_handoff(
			"Administrator",
			tcode,
			opn,
			context=self._eval_handoff_ctx(),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p7_03_handoff_second_call_duplicate_denied(self) -> None:
		tcode, _tm2, _si, opn = self._closed_prepared_opening_completed()
		ctx = self._eval_handoff_ctx()
		out1 = complete_evaluation_handoff("Administrator", tcode, opn, context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		out2 = completeEvaluationHandoff("Administrator", tcode, opn, context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p7_03_handoff_role_denied_without_permission(self) -> None:
		tcode, _tm2, _si, opn = self._closed_prepared_opening_completed()
		out = complete_evaluation_handoff(
			"Administrator",
			tcode,
			opn,
			context={"granted_permissions": []},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p7_03_handoff_opening_code_mismatch_denied(self) -> None:
		tcode, _tm2, _si, opn = self._closed_prepared_opening_completed()
		out = complete_evaluation_handoff(
			"Administrator",
			tcode,
			f"{opn}-WRONG",
			context=self._eval_handoff_ctx(),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p7_03_handoff_orr_missing_opening_stamp_denied(self) -> None:
		tcode, tm2, _si, opn = self._closed_prepared_opening_completed()
		orr = frappe.db.get_value("TM2 Opening Readiness Record", {"tm2_tender": tm2}, "name")
		self.assertTrue(orr)
		frappe.db.set_value(
			"TM2 Opening Readiness Record",
			orr,
			{"opening_record_code": ""},
			update_modified=False,
		)
		try:
			out = complete_evaluation_handoff(
				"Administrator",
				tcode,
				opn,
				context=self._eval_handoff_ctx(),
			)
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
		finally:
			frappe.db.set_value(
				"TM2 Opening Readiness Record",
				orr,
				{"opening_record_code": opn},
				update_modified=False,
			)

	def test_p7_03_handoff_no_opened_submissions_denied(self) -> None:
		tcode, tm2, _si, opn = self._closed_prepared_opening_completed()
		bid = frappe.db.get_value("TM2 Bid Submission", {"tm2_tender": tm2}, "name")
		self.assertTrue(bid)
		frappe.db.set_value("TM2 Bid Submission", bid, {"bid_status": "Sealed"}, update_modified=False)
		try:
			out = complete_evaluation_handoff(
				"Administrator",
				tcode,
				opn,
				context=self._eval_handoff_ctx(),
			)
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
		finally:
			frappe.db.set_value("TM2 Bid Submission", bid, {"bid_status": "Opened"}, update_modified=False)

	def test_p7_03_handoff_dem_not_consumable_denied(self) -> None:
		tcode, tm2, si, opn = self._closed_prepared_opening_completed()
		dem_name = frappe.db.get_value("Tender STD Instance", si, "current_dem_output_code")
		self.assertTrue(dem_name)
		if frappe.db.exists("Tender STD Generated Output", dem_name):
			frappe.db.set_value(
				"Tender STD Generated Output",
				dem_name,
				{"output_status": "Stale"},
				update_modified=False,
			)
			try:
				out = complete_evaluation_handoff(
					"Administrator",
					tcode,
					opn,
					context=self._eval_handoff_ctx(),
				)
				self.assertFalse(out.get("ok"))
				self.assertEqual(out.get("denial_code"), DenialCode.AUTH_DEM_MISSING_OR_STALE.value)
			finally:
				frappe.db.set_value(
					"Tender STD Generated Output",
					dem_name,
					{"output_status": "Published"},
					update_modified=False,
				)

	def test_p7_03_handoff_binding_snapshot_mismatch_denied(self) -> None:
		tcode, tm2, _si, opn = self._closed_prepared_opening_completed()
		bind = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"name",
		)
		self.assertTrue(bind)
		frappe.db.set_value(
			"TM2 Tender STD Binding",
			bind,
			{"publication_snapshot_code": "PUBSNAP-WRONG-TM2"},
			update_modified=False,
		)
		try:
			out = complete_evaluation_handoff(
				"Administrator",
				tcode,
				opn,
				context=self._eval_handoff_ctx(),
			)
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
		finally:
			from kentender_procurement.tender_management.services.tm2_std_adapter import (
				create_or_get_publication_snapshot_for_tm2,
			)

			fixed = create_or_get_publication_snapshot_for_tm2(tcode)
			if fixed.get("ok"):
				frappe.db.set_value(
					"TM2 Tender STD Binding",
					bind,
					{"publication_snapshot_code": fixed.get("publication_snapshot_code")},
					update_modified=False,
				)

	def test_p7_03_handoff_publication_snapshot_adapter_denied(self) -> None:
		tcode, _tm2, _si, opn = self._closed_prepared_opening_completed()
		bad = {
			"ok": False,
			"denial_code": DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			"message": "snapshot denied (fixture)",
		}
		with patch(
			"kentender_procurement.tender_management.services.complete_evaluation_handoff.get_tender_std_output_refs",
			return_value=bad,
		):
			out = complete_evaluation_handoff(
				"Administrator",
				tcode,
				opn,
				context=self._eval_handoff_ctx(),
			)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value)
