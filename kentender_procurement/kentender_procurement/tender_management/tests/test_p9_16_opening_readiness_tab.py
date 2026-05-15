# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-16 — workbench Opening Readiness tab DTO (doc 9 §17.9, doc 6 §22, smoke TM2-SMOKE-UI-007).

**EX-08** (doc 9 §25 / doc 8 TM2-SMOKE-OPEN-003): ``test_EX_08_*`` — opening-register JSON must not
carry BOQ arithmetic / evaluation injection; validated via :class:`ManualRuleDenialService`.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_16_opening_readiness_tab
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial import (
	ManualRuleDenialService,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.close_tender import close_tender
from kentender_procurement.tender_management.services.prepare_opening_readiness import prepare_opening_readiness
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	get_workbench_tender_detail as get_workbench_tender_detail_service,
)
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture


class TestP916OpeningReadinessTab(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P916"

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

	def _closed_with_one_sealed_bid(self) -> tuple[str, str, str, str, str]:
		tcode, tm2, sup, si = self._published_si_supplier()
		ctx_s = {**self._portal_submit_ctx(), "acting_supplier": sup}
		out_b = submit_bid("Administrator", tcode, sup, _valid_bid_for_fixture(tcode, sup, si), context=ctx_s)
		self.assertTrue(out_b.get("ok"), out_b)
		self._past_deadline(tm2)
		out_c = close_tender("Administrator", tcode, context=self._close_ctx())
		self.assertTrue(out_c.get("ok"), out_c)
		self.assertEqual(out_c.get("tender_status"), "Closed")
		cl = str(out_c.get("tm2_tender_closing_record") or "")
		self.assertTrue(cl)
		return tcode, tm2, sup, si, cl

	def test_p9_16_opening_readiness_tab_shape(self) -> None:
		tcode, _tm2 = self._mk_wizard_tender_pair()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		tab = out.get("opening_readiness_tab")
		self.assertIsInstance(tab, dict)
		for k in (
			"read_only_notice",
			"readiness_status",
			"opening_readiness_code",
			"closing_record_code",
			"dom_output_code",
			"publication_snapshot_code",
			"valid_sealed_submissions_count",
			"opening_rules",
			"readiness_blockers",
			"tab_actions",
			"works_arithmetic_notice",
		):
			self.assertIn(k, tab)
		self.assertIsInstance(tab["opening_rules"], list)
		self.assertIsInstance(tab["readiness_blockers"], list)
		self.assertIsInstance(tab["tab_actions"], dict)

	def _mk_wizard_tender_pair(self) -> tuple[str, str]:
		from kentender_procurement.tender_management.services.tm2_workbench_wizard import (
			list_new_tender_wizard_std_options as list_new_tender_wizard_std_options_service,
			submit_new_tender_wizard_completion,
		)

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

	def test_p9_16_after_prepare_opening_readiness(self) -> None:
		tcode, _tm2, _sup, si, _cl = self._closed_with_one_sealed_bid()
		out_p = prepare_opening_readiness("Administrator", tcode, context=self._prepare_ctx())
		self.assertTrue(out_p.get("ok"), out_p)
		self.assertEqual(out_p.get("opening_readiness_code"), f"ORR-{tcode}")

		frappe.set_user("Administrator")
		detail = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(detail.get("ok"), detail)
		tab = detail.get("opening_readiness_tab") or {}
		self.assertEqual(tab.get("readiness_status"), "Ready")
		self.assertEqual(tab.get("opening_readiness_code"), f"ORR-{tcode}")
		self.assertTrue(str(tab.get("dom_output_code") or "").strip())
		self.assertEqual(tab.get("tender_std_instance_code"), si)
		self.assertEqual(tab.get("valid_sealed_submissions_count"), 1)
		self.assertGreaterEqual(int(tab.get("sealed_submission_ref_count") or 0), 1)
		notice = str(tab.get("works_arithmetic_notice") or "")
		cat = (frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "procurement_category") or "").strip().lower()
		if cat == "works":
			self.assertIn("Arithmetic correction", notice)
		tab_actions = tab.get("tab_actions") or {}
		self.assertIn("prepare_opening_readiness", tab_actions)
		self.assertIn("send_to_opening", tab_actions)

	def test_EX_08_opening_register_payload_rejects_arithmetic_correction(self) -> None:
		"""Doc 9 §25 EX-08 — opening payload cannot carry ``arithmetic_correction`` (doc 8 OPEN-003)."""
		out = ManualRuleDenialService.validate_opening_register_payload(
			{"arithmetic_correction": {"applied": True}},
		)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value)

	def test_EX_08_opening_register_payload_rejects_boq_arithmetic_correction_block(self) -> None:
		"""EX-08 — ``boq_arithmetic_correction`` structure is rejected at opening."""
		out = ManualRuleDenialService.validate_opening_register_payload(
			{"rows": [], "boq_arithmetic_correction": {"enabled": True, "correction_rules": [{"rule": "x"}]}},
		)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value)

	def test_EX_08_opening_register_payload_rejects_corrected_evaluated_boq_total(self) -> None:
		"""EX-08 — evaluation-stage corrected BOQ total must not appear on opening register."""
		out = ManualRuleDenialService.validate_opening_register_payload(
			{"corrected_evaluated_boq_total": 96_754_000},
		)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value)

	def test_EX_08_opening_register_payload_accepts_dom_safe_opening_rows(self) -> None:
		"""EX-08 — minimal DOM-shaped opening rows (submitted totals only) remain valid."""
		ok = ManualRuleDenialService.validate_opening_register_payload(
			{"rows": [{"bid_code": "BID-1", "submitted_total_bid_price": 96_750_000}]},
		)
		self.assertTrue(ok.get("ok"), ok)
