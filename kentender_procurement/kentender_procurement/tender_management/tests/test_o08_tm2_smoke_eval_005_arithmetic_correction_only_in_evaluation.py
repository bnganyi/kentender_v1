# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""O-08 — doc 8 **TM2-SMOKE-EVAL-005**; doc 9 §21.2 ``test_TM2_SMOKE_EVAL_005_…``.

**Correction only at evaluation boundary:** opening/register payloads must **not** carry DEM-shaped
BOQ arithmetic correction structures (:meth:`~kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial.ManualRuleDenialService.validate_opening_register_payload`).
The same semantics are **materialized in DEM** (``boq_arithmetic_correction`` in ``content_json``),
and the **Evaluation** consumer may consume that published DEM via
:class:`~kentender_procurement.tender_management.derived_models.consumption.output_consumption.OutputConsumptionService`
(doc 9 §25 **EX-09**: ``test_EX_09_*`` in ``tender_management.tests.test_p9_17_evaluation_handoff_tab``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_o08_tm2_smoke_eval_005_arithmetic_correction_only_in_evaluation
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial import (
	ManualRuleDenialService,
)
from kentender_procurement.tender_management.derived_models.consumption.output_consumption import (
	OutputConsumptionService,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)


def _as_dict(content_json: object) -> dict:
	if isinstance(content_json, dict):
		return content_json
	if isinstance(content_json, str) and content_json.strip():
		return json.loads(content_json)
	return {}


class TestO08Tm2SmokeEval005ArithmeticCorrectionOnlyInEvaluation(IntegrationTestCase):
	"""Doc 8 TM2-SMOKE-EVAL-005 — arithmetic correction belongs in DEM / evaluation, not opening."""

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	@classmethod
	def tearDownClass(cls) -> None:
		frappe.set_user("Administrator")
		super().tearDownClass()

	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _cleanup_tender(self, tender_name: str) -> None:
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
				frappe.delete_doc(
					"Tender STD Instance BOQ",
					boq_name,
					force=True,
					ignore_permissions=True,
				)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def _minimal_valid_boq_payload(self) -> dict:
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

	def test_TM2_SMOKE_EVAL_005_arithmetic_correction_only_in_evaluation(self) -> None:
		# Opening / DOM register must reject DEM-shaped arithmetic correction injection.
		open_bad = ManualRuleDenialService.validate_opening_register_payload(
			{"boq_arithmetic_correction": {"enabled": True, "correction_rules": [{"rule": "x"}]}},
		)
		self.assertFalse(open_bad.get("ok"), open_bad)
		self.assertEqual(
			open_bad.get("denial_code"),
			DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value,
		)

		# Published DEM carries the correction model; Evaluation consumption remains allowed.
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "O-08 TM2-SMOKE-EVAL-005"
		doc.tender_reference = "O08-EVAL-005"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dem = StdInstanceGeneratedOutputService.generate_dem(si.name)
			cj = _as_dict(dem.content_json)
			bac = cj.get("boq_arithmetic_correction") or {}
			self.assertTrue(bac.get("enabled"), bac)
			self.assertTrue(isinstance(bac.get("correction_rules"), list) and bac["correction_rules"])

			StdInstanceGeneratedOutputService.publish_output(dem.name)
			res = OutputConsumptionService.validate_consumption(dem.name, "Evaluation", None)
			self.assertTrue(res.get("allowed"), res)
			self.assertEqual(res.get("output_status"), "Published")
			self.assertEqual(res.get("blockers"), [])
		finally:
			self._cleanup_tender(doc.name)
