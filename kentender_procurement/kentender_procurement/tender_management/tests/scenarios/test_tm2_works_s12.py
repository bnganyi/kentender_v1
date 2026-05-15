# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S12 (Contract Price Source Validation).

**§2:** contract handoff must reject the **uncorrected** evaluated Works total (**96,750,000** KES probe)
with ``AUTH_CONTRACT_PRICE_SOURCE_INVALID``; the **corrected** total (**96,754,000** KES) is accepted
(doc 9 §12.4 **P7-04**; doc 8 **TM2-SMOKE-CON-003**; **EX-10**). Chain mirrors ``test_p7_04_*`` /
``test_p9_18_contract_handoff_tab.test_EX_10_*``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s12
"""

from __future__ import annotations

import unittest

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.scenarios.tm2_works_scenarios import (
	scenario_by_code,
	scenario_tracker_slug,
)
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
from kentender_procurement.tender_management.services.prepare_opening_readiness import (
	prepare_opening_readiness,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture

_CODE = "TM2-WORKS-S12"


class TestTM2WorksS12Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Contract Price Source Validation")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS12ContractPriceSource(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	"""Doc 7 §2 — TM2-WORKS-S12 (tracker **S-12**). Aligned with ``test_p7_04_forbidden_uncorrected_price_denied``."""

	p6_supplier_fixture_prefix = "S12"

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
		self.assertTrue(si)
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
		opn = f"OPN-{tcode}-S12"
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
		award_code = f"AWD-{tcode}-S12"
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

	def test_S_12_rejects_uncorrected_evaluated_price_then_accepts_corrected_for_contract_handoff(self) -> None:
		"""Forbidden **96,750,000** KES → ``AUTH_CONTRACT_PRICE_SOURCE_INVALID``; **96,754,000** KES → CHR."""
		tcode, tm2, sup, _si, award_code = self._chain_to_awarded()
		ctx_bad = self._award_context(tcode, sup, award_code, price=96_750_000)
		out_bad = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx_bad)
		self.assertFalse(out_bad.get("ok"), out_bad)
		self.assertEqual(out_bad.get("denial_code"), DenialCode.AUTH_CONTRACT_PRICE_SOURCE_INVALID.value)
		self.assertFalse(
			frappe.db.get_value("TM2 Contract Handoff Reference", {"tm2_tender": tm2}, "name"),
			"no CHR after forbidden uncorrected total",
		)

		ctx_ok = self._award_context(tcode, sup, award_code, price=96_754_000)
		out_ok = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx_ok)
		self.assertTrue(out_ok.get("ok"), out_ok)
		self.assertEqual(out_ok.get("contract_handoff_code"), f"CHR-{tcode}")
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2, "status"), "Contract Handoff Completed")
