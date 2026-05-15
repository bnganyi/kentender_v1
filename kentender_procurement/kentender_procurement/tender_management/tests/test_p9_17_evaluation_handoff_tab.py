# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-17 — workbench Evaluation Handoff tab DTO (doc 9 §17.10, doc 6 §23).

**EX-09** (doc 9 §25 / doc 8 TM2-SMOKE-EVAL-005): ``test_EX_09_*`` — BOQ arithmetic correction is
materialized on the published **DEM** and consumable under the **Evaluation** boundary (not via
opening-register injection); see :class:`~kentender_procurement.tender_management.derived_models.consumption.output_consumption.OutputConsumptionService`.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_17_evaluation_handoff_tab
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.derived_models.consumption.output_consumption import (
	OutputConsumptionService,
)
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.close_tender import close_tender
from kentender_procurement.tender_management.services.complete_evaluation_handoff import complete_evaluation_handoff
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
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture
from kentender_procurement.tender_management.works_completion.services.boq_completion import WorksBoqCompletionService


class TestP917EvaluationHandoffTab(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P917"

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
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

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

	def _past_deadline(self, tm2: str) -> None:
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)

	def _ex09_as_dict(self, content_json: object) -> dict:
		if isinstance(content_json, dict):
			return content_json
		if isinstance(content_json, str) and content_json.strip():
			return json.loads(content_json)
		return {}

	def _ex09_cleanup_procurement_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			for snap_name in frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				if frappe.db.exists("Tender STD Instance Snapshot", snap_name):
					frappe.delete_doc(
						"Tender STD Instance Snapshot",
						snap_name,
						force=True,
						ignore_permissions=True,
					)
			for out_name in frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				if frappe.db.exists("Tender STD Generated Output", out_name):
					frappe.delete_doc(
						"Tender STD Generated Output",
						out_name,
						force=True,
						ignore_permissions=True,
					)
			for boq_name in frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				if frappe.db.exists("Tender STD Instance BOQ", boq_name):
					frappe.delete_doc(
						"Tender STD Instance BOQ",
						boq_name,
						force=True,
						ignore_permissions=True,
					)
			if frappe.db.exists("Tender STD Instance", name):
				frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def _ex09_minimal_valid_boq_payload(self) -> dict:
		return {
			"header": {"currency": "USD"},
			"bills": [
				{
					"bill_number": "B1",
					"bill_title": "Preliminaries",
					"bill_type": "Standard",
					"order_index": 0,
					"items": [
						{
							"item_number": "1.1",
							"description": "Site clearance",
							"unit": "m2",
							"quantity": 100,
							"item_type": "Normal",
							"supplier_input_mode": "Rate Only",
						},
					],
				},
			],
		}

	def test_EX_09_published_dem_boq_arithmetic_correction_allowed_for_evaluation_consumer(self) -> None:
		"""Doc 9 §25 EX-09 / doc 8 TM2-SMOKE-EVAL-005 — DEM carries correction rules; Evaluation may consume."""
		frappe.set_user("Administrator")
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "P917 EX-09 DEM arithmetic"
		doc.tender_reference = "P917-EX09"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._ex09_minimal_valid_boq_payload())
			dem = StdInstanceGeneratedOutputService.generate_dem(si.name)
			cj = self._ex09_as_dict(dem.content_json)
			bac = cj.get("boq_arithmetic_correction") or {}
			self.assertTrue(bac.get("enabled"), bac)
			self.assertTrue(isinstance(bac.get("correction_rules"), list) and bac["correction_rules"])

			StdInstanceGeneratedOutputService.publish_output(dem.name)
			res = OutputConsumptionService.validate_consumption(dem.name, "Evaluation", None)
			self.assertTrue(res.get("allowed"), res)
			self.assertEqual(res.get("output_status"), "Published")
			self.assertEqual(res.get("blockers"), [])
		finally:
			self._ex09_cleanup_procurement_tender(doc.name)

	def _published_si_supplier(self) -> tuple[str, str, str, str]:
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		assert si
		return tcode, tm2, sup, str(si)

	def _closed_prepared_opening_completed(self) -> tuple[str, str, str, str]:
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
		return tcode, tm2, si, opn

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

	def test_p9_17_evaluation_handoff_tab_shape(self) -> None:
		tcode, _tm2 = self._mk_wizard_tender_pair()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		tab = out.get("evaluation_handoff_tab")
		self.assertIsInstance(tab, dict)
		for k in (
			"read_only_notice",
			"dem_readonly_notice",
			"criteria_derived_notice",
			"handoff_status",
			"evaluation_handoff_code",
			"dem_output_code",
			"dsm_output_code",
			"opened_submissions",
			"handoff_blockers",
			"tab_actions",
		):
			self.assertIn(k, tab)
		self.assertIsInstance(tab["opened_submissions"], list)
		self.assertIsInstance(tab["tab_actions"], dict)
		crit = str(tab.get("criteria_derived_notice") or "")
		self.assertIn("Evaluation criteria are derived", crit)
		self.assertIn("cannot be modified", crit)

	def test_p9_17_after_complete_evaluation_handoff(self) -> None:
		tcode, _tm2, _si, opn = self._closed_prepared_opening_completed()
		out_e = complete_evaluation_handoff(
			"Administrator",
			tcode,
			opn,
			context=self._eval_handoff_ctx(),
		)
		self.assertTrue(out_e.get("ok"), out_e)
		self.assertEqual(out_e.get("evaluation_handoff_code"), f"EHR-{tcode}")

		frappe.set_user("Administrator")
		detail = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(detail.get("ok"), detail)
		tab = detail.get("evaluation_handoff_tab") or {}
		self.assertEqual(tab.get("handoff_status"), "Ready")
		self.assertEqual(tab.get("evaluation_handoff_code"), f"EHR-{tcode}")
		self.assertTrue(str(tab.get("dem_output_code") or "").strip())
		self.assertTrue(str(tab.get("dsm_output_code") or "").strip())
		opened = tab.get("opened_submissions") or []
		self.assertTrue(opened)
		tab_actions = tab.get("tab_actions") or {}
		self.assertIn("prepare_evaluation_handoff", tab_actions)
		self.assertIn("send_to_evaluation", tab_actions)
