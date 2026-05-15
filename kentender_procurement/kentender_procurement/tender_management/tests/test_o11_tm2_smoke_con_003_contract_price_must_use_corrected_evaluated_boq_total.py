# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""O-11 — doc 8 **TM2-SMOKE-CON-003**; doc 9 §21.2 ``test_TM2_SMOKE_CON_003_…``.

Contract handoff must **not** accept the pack **uncorrected** Works evaluated total (**96,750,000** KES);
the corrected evaluated BOQ total must be used instead. ``create_contract_handoff_reference`` denies
with ``AUTH_CONTRACT_PRICE_SOURCE_INVALID`` (doc 9 §12.4). **EX-10** exit gate:
``test_EX_10_contract_handoff_rejects_uncorrected_then_accepts_corrected_evaluated_total`` in
``tender_management.tests.test_p9_18_contract_handoff_tab``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_o11_tm2_smoke_con_003_contract_price_must_use_corrected_evaluated_boq_total
"""

from __future__ import annotations

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


class TestO11Tm2SmokeCon003ContractPriceMustUseCorrectedEvaluatedBoqTotal(
	_P401Tm2Cleanup,
	P6PublishedTm2Fixture,
):
	"""Doc 8 TM2-SMOKE-CON-003 — forbidden uncorrected final price rejected at contract handoff."""

	p6_supplier_fixture_prefix = "O11"

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
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

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

	def _award_context(self, tcode: str, sup: str, award_code: str, *, price: int) -> dict:
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

	def test_TM2_SMOKE_CON_003_contract_price_must_use_corrected_evaluated_boq_total(self) -> None:
		tcode, _tm2, sup, _si, award_code = self._chain_to_awarded()
		ctx = self._award_context(tcode, sup, award_code, price=96_750_000)
		out = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTRACT_PRICE_SOURCE_INVALID.value)
