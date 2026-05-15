# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-04 — doc 9 §12.4 ``create_contract_handoff_reference`` / ``createContractHandoffReference``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p7_04_create_contract_handoff_reference
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
	complete_evaluation_handoff,
)
from kentender_procurement.tender_management.services.create_contract_handoff_reference import (
	createContractHandoffReference,
	create_contract_handoff_reference,
)
from kentender_procurement.tender_management.services.prepare_opening_readiness import prepare_opening_readiness
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture


class TestP704CreateContractHandoffReference(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P704"

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

	def _contract_ctx(self) -> dict:
		spec = spec_for_action("CON2_CREATE_CONTRACT_HANDOFF")
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

	def _closed_prepared_opening_completed(self) -> tuple[str, str, str, str, str]:
		"""Close → ORR → Opening Completed + ORR opening ref + bid Opened. Returns tcode, tm2, sup, si, opn."""
		tcode, tm2, sup, si = self._published_si_supplier()
		ctx_s = {**self._portal_submit_ctx(), "acting_supplier": sup}
		out_b = submit_bid("Administrator", tcode, sup, _valid_bid_for_fixture(tcode, sup, si), context=ctx_s)
		self.assertTrue(out_b.get("ok"), out_b)
		self._past_deadline(tm2)
		out_c = close_tender("Administrator", tcode, context=self._close_ctx())
		self.assertTrue(out_c.get("ok"), out_c)
		out_p = prepare_opening_readiness("Administrator", tcode, context=self._prepare_ctx())
		self.assertTrue(out_p.get("ok"), out_p)
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
		return tcode, tm2, sup, si, opn

	def _chain_to_awarded(self) -> tuple[str, str, str, str, str]:
		tcode, tm2, sup, si, opn = self._closed_prepared_opening_completed()
		out_e = complete_evaluation_handoff(
			"Administrator",
			tcode,
			opn,
			context=self._eval_handoff_ctx(),
		)
		self.assertTrue(out_e.get("ok"), out_e)
		frappe.db.set_value("TM2 Tender", tm2, {"status": "Awarded"}, update_modified=False)
		award_code = f"AWD-{tcode}-001"
		return tcode, tm2, sup, si, award_code

	def _award_context(self, tcode: str, sup: str, award_code: str, *, price: int = 96_754_000) -> dict:
		return {
			**self._contract_ctx(),
			"award": {
				"award_decision_code": award_code,
				"awarded_supplier": sup,
				"final_evaluated_price": price,
				"currency": "KES",
				"final_boq_reference": f"BOQ-{tcode}-CORRECTED-01",
			},
		}

	def test_p7_04_contract_handoff_happy_path(self) -> None:
		tcode, tm2, sup, si, award_code = self._chain_to_awarded()
		ctx = self._award_context(tcode, sup, award_code)
		out = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("tender_status"), "Contract Handoff Completed")
		self.assertEqual(out.get("contract_handoff_code"), f"CHR-{tcode}")
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2, "status"), "Contract Handoff Completed")
		chr_name = str(out.get("tm2_contract_handoff_reference") or "")
		self.assertTrue(chr_name)
		doc = frappe.get_doc("TM2 Contract Handoff Reference", chr_name)
		self.assertEqual(doc.handoff_status, "Ready")
		self.assertEqual(doc.award_decision_code, award_code)
		self.assertEqual(doc.awarded_supplier, sup)
		self.assertEqual(doc.tender_std_instance_code, si)
		raw = doc.contract_handoff_payload
		payload = json.loads(raw) if isinstance(raw, str) else raw
		self.assertEqual(payload.get("award_decision_code"), award_code)
		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Contract Handoff Reference Created"},
			pluck="name",
		)
		self.assertEqual(len(ev), 1)

	def test_p7_04_not_awarded_denied(self) -> None:
		tcode, tm2, sup, _si, award_code = self._chain_to_awarded()
		frappe.db.set_value("TM2 Tender", tm2, {"status": "Evaluation Ready"}, update_modified=False)
		out = create_contract_handoff_reference(
			"Administrator",
			tcode,
			award_code,
			context=self._award_context(tcode, sup, award_code),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p7_04_missing_ehr_denied(self) -> None:
		tcode, tm2, sup, _si, award_code = self._chain_to_awarded()
		ehr = frappe.db.get_value("TM2 Evaluation Handoff Record", {"tm2_tender": tm2}, "name")
		self.assertTrue(ehr)
		frappe.delete_doc("TM2 Evaluation Handoff Record", ehr, force=True, ignore_permissions=True)
		out = create_contract_handoff_reference(
			"Administrator",
			tcode,
			award_code,
			context=self._award_context(tcode, sup, award_code),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p7_04_forbidden_uncorrected_price_denied(self) -> None:
		tcode, tm2, sup, _si, award_code = self._chain_to_awarded()
		ctx = self._award_context(tcode, sup, award_code, price=96_750_000)
		out = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTRACT_PRICE_SOURCE_INVALID.value)

	def test_p7_04_missing_award_payload_denied(self) -> None:
		tcode, _tm2, _sup, _si, award_code = self._chain_to_awarded()
		out = create_contract_handoff_reference(
			"Administrator",
			tcode,
			award_code,
			context=self._contract_ctx(),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p7_04_award_code_mismatch_denied(self) -> None:
		tcode, _tm2, sup, _si, award_code = self._chain_to_awarded()
		ctx = self._award_context(tcode, sup, award_code)
		ctx["award"]["award_decision_code"] = f"{award_code}-X"
		out = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p7_04_second_call_duplicate_denied(self) -> None:
		tcode, _tm2, sup, _si, award_code = self._chain_to_awarded()
		ctx = self._award_context(tcode, sup, award_code)
		out1 = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		out2 = createContractHandoffReference("Administrator", tcode, award_code, context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p7_04_role_denied_without_permission(self) -> None:
		tcode, _tm2, sup, _si, award_code = self._chain_to_awarded()
		ctx = self._award_context(tcode, sup, award_code)
		ctx.pop("granted_permissions", None)
		ctx["granted_permissions"] = []
		out = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p7_04_dcm_not_consumable_denied(self) -> None:
		tcode, tm2, sup, si, award_code = self._chain_to_awarded()
		dcm_name = frappe.db.get_value("Tender STD Instance", si, "current_dcm_output_code")
		self.assertTrue(dcm_name)
		if frappe.db.exists("Tender STD Generated Output", dcm_name):
			frappe.db.set_value(
				"Tender STD Generated Output",
				dcm_name,
				{"output_status": "Stale"},
				update_modified=False,
			)
			try:
				out = create_contract_handoff_reference(
					"Administrator",
					tcode,
					award_code,
					context=self._award_context(tcode, sup, award_code),
				)
				self.assertFalse(out.get("ok"))
				self.assertEqual(out.get("denial_code"), DenialCode.AUTH_DCM_MISSING_OR_STALE.value)
			finally:
				frappe.db.set_value(
					"Tender STD Generated Output",
					dcm_name,
					{"output_status": "Published"},
					update_modified=False,
				)

	def test_p7_04_binding_snapshot_mismatch_denied(self) -> None:
		tcode, tm2, sup, _si, award_code = self._chain_to_awarded()
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
			out = create_contract_handoff_reference(
				"Administrator",
				tcode,
				award_code,
				context=self._award_context(tcode, sup, award_code),
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

	def test_p7_04_publication_snapshot_adapter_denied(self) -> None:
		tcode, _tm2, sup, _si, award_code = self._chain_to_awarded()
		bad = {
			"ok": False,
			"denial_code": DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			"message": "snapshot denied (fixture)",
		}
		with patch(
			"kentender_procurement.tender_management.services.create_contract_handoff_reference.get_tender_std_output_refs",
			return_value=bad,
		):
			out = create_contract_handoff_reference(
				"Administrator",
				tcode,
				award_code,
				context=self._award_context(tcode, sup, award_code),
			)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value)
