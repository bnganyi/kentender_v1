# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-18 — workbench Contract Handoff tab DTO (doc 9 §17.11, doc 6 §24, TM2-SMOKE-UI-008).

**EX-10** (doc 9 §25 / doc 8 TM2-SMOKE-WORKS-007 / TM2-SMOKE-CON-003): ``test_EX_10_*`` — contract handoff
must use the **corrected** evaluated BOQ total (**96,754,000** KES display); **96,750,000** KES is denied at
``create_contract_handoff_reference`` (``AUTH_CONTRACT_PRICE_SOURCE_INVALID``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_18_contract_handoff_tab

Canonical doc 9 §21.3 item 10 (corrected evaluated price **96,754,000** KES on workbench Contract Handoff tab):
``apps/kentender_v1/tests/ui/tm2_opening_contract_handoff.spec.ts`` (**Q-06**), env ``UI_TM2_CONTRACT_HANDOFF_TENDER``.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.close_tender import close_tender
from kentender_procurement.tender_management.services.complete_evaluation_handoff import complete_evaluation_handoff
from kentender_procurement.tender_management.services.create_contract_handoff_reference import (
	create_contract_handoff_reference,
)
from kentender_procurement.tender_management.services.prepare_opening_readiness import prepare_opening_readiness
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.services.tm2_workbench_wizard import (
	list_new_tender_wizard_std_options as list_new_tender_wizard_std_options_service,
	submit_new_tender_wizard_completion,
)
from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	get_workbench_tender_detail as get_workbench_tender_detail_service,
)
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture


class TestP918ContractHandoffTab(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P918"

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

	def _past_deadline(self, tm2: str) -> None:
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)

	def _published_si_supplier(self) -> tuple[str, str, str, str]:
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		assert si
		return tcode, tm2, sup, str(si)

	def _chain_to_awarded(self) -> tuple[str, str, str, str, str]:
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

	def _mk_wizard_tender_pair(self) -> tuple[str, str]:
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name

		frappe.set_user("Administrator")
		opt = list_new_tender_wizard_std_options_service("Administrator", pc)
		self.assertTrue(opt.get("ok"), opt)
		options = opt.get("options") or []
		self.assertTrue(options, opt)
		first = options[0]
		std_name = str(first.get("std_template") or "").strip()
		ver = str(first.get("template_version_code") or "").strip()
		prof = str(first.get("applicability_profile_code") or "").strip()
		out = submit_new_tender_wizard_completion(
			"Administrator",
			pc,
			std_name,
			ver,
			prof,
			context={},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		tcode = str(out.get("tender_code") or "").strip()
		tm2 = str(out.get("tm2_tender") or "").strip()
		self.assertTrue(tcode and tm2)
		return tcode, tm2

	def test_EX_10_contract_handoff_rejects_uncorrected_then_accepts_corrected_evaluated_total(self) -> None:
		"""Doc 9 §25 EX-10 — forbidden uncorrected Works total denied; corrected total + tab display."""
		tcode, _tm2, sup, _si, award_code = self._chain_to_awarded()
		ctx_bad = self._award_context(tcode, sup, award_code, price=96_750_000)
		out_bad = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx_bad)
		self.assertFalse(out_bad.get("ok"), out_bad)
		self.assertEqual(out_bad.get("denial_code"), DenialCode.AUTH_CONTRACT_PRICE_SOURCE_INVALID.value)

		ctx_ok = self._award_context(tcode, sup, award_code, price=96_754_000)
		out_ok = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx_ok)
		self.assertTrue(out_ok.get("ok"), out_ok)
		self.assertEqual(out_ok.get("contract_handoff_code"), f"CHR-{tcode}")

		frappe.set_user("Administrator")
		detail = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(detail.get("ok"), detail)
		tab = detail.get("contract_handoff_tab") or {}
		pr_line = str(tab.get("final_evaluated_price_display") or "")
		self.assertTrue(pr_line)
		self.assertRegex(pr_line.replace(",", ""), r"96754000")

	def test_p9_18_contract_handoff_tab_shape(self) -> None:
		tcode, _tm2 = self._mk_wizard_tender_pair()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		tab = out.get("contract_handoff_tab")
		self.assertIsInstance(tab, dict)
		for k in (
			"read_only_notice",
			"dcm_readonly_notice",
			"contract_terms_notice",
			"dcm_output_code",
			"handoff_status",
			"contract_handoff_code",
			"final_evaluated_price_display",
			"handoff_blockers",
			"tab_actions",
		):
			self.assertIn(k, tab)
		self.assertIsInstance(tab["tab_actions"], dict)

	def test_p9_18_after_create_contract_handoff_reference(self) -> None:
		tcode, _tm2, sup, _si, award_code = self._chain_to_awarded()
		ctx = self._award_context(tcode, sup, award_code, price=96_754_000)
		out_c = create_contract_handoff_reference("Administrator", tcode, award_code, context=ctx)
		self.assertTrue(out_c.get("ok"), out_c)
		self.assertEqual(out_c.get("contract_handoff_code"), f"CHR-{tcode}")

		frappe.set_user("Administrator")
		detail = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(detail.get("ok"), detail)
		tab = detail.get("contract_handoff_tab") or {}
		self.assertEqual(tab.get("handoff_status"), "Ready")
		self.assertEqual(tab.get("contract_handoff_code"), f"CHR-{tcode}")
		self.assertTrue(str(tab.get("dcm_output_code") or "").strip())
		pr_line = str(tab.get("final_evaluated_price_display") or "")
		self.assertTrue(pr_line)
		self.assertRegex(pr_line.replace(",", ""), r"96754000")
		cat = (frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "procurement_category") or "").strip().lower()
		if cat == "works":
			self.assertTrue(str(tab.get("works_contract_value_source_notice") or "").strip())
			self.assertIn("BOQ", str(tab.get("final_boq_reference") or ""))
		tab_actions = tab.get("tab_actions") or {}
		self.assertIn("create_contract_handoff", tab_actions)
