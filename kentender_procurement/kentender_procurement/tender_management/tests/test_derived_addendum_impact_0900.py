# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0900 — ``DerivedModelImpactService`` (pack §16 addendum → outputs).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_addendum_impact_0900
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.addendum.derived_model_impact import (
	DERIVED_ADDENDUM_IMPACT_UNKNOWN_CHANGE_TYPE,
	DerivedModelImpactService,
)
from kentender_procurement.tender_management.std_instance.boq import BOQ_STALE_OUTPUT_KEYS
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_ADDENDUM_IMPACT_ANALYSED


def _msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


class TestDerivedAddendumImpact0900(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		frappe.clear_messages()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_boq_matches_works_boq_stale_keys(self) -> None:
		r = DerivedModelImpactService.get_affected_outputs_for_change("boq_quantity_item_change")
		self.assertEqual(set(r["affected_outputs"]), set(BOQ_STALE_OUTPUT_KEYS))
		self.assertEqual(r["affected_outputs"], ["Bundle", "DSM", "DEM", "DCM"])

	def test_submission_deadline_bundle_dsm_dom(self) -> None:
		r = DerivedModelImpactService.get_affected_outputs_for_change("submission_deadline")
		self.assertEqual(r["change_type"], "submission_deadline_change")
		self.assertEqual(r["affected_outputs"], ["Bundle", "DSM", "DOM"])

	def test_opening_datetime_bundle_dom_only_not_dsm(self) -> None:
		r = DerivedModelImpactService.get_affected_outputs_for_change("opening_datetime_change")
		self.assertEqual(r["affected_outputs"], ["Bundle", "DOM"])
		self.assertNotIn("DSM", r["affected_outputs"])

	def test_drawing_without_ack_no_dsm(self) -> None:
		r = DerivedModelImpactService.get_affected_outputs_for_change("drawing_change", {})
		self.assertEqual(r["affected_outputs"], ["Bundle", "DEM", "DCM"])

	def test_drawing_with_ack_includes_dsm(self) -> None:
		r = DerivedModelImpactService.get_affected_outputs_for_change(
			"drawing",
			{"drawing_acknowledgement_required": True},
		)
		self.assertEqual(r["affected_outputs"], ["Bundle", "DSM", "DEM", "DCM"])

	def test_scc_and_contract_form(self) -> None:
		scc = DerivedModelImpactService.get_affected_outputs_for_change("scc_value_change")
		self.assertEqual(scc["affected_outputs"], ["Bundle", "DCM"])
		cf = DerivedModelImpactService.get_affected_outputs_for_change("contract_form_change")
		self.assertEqual(cf["affected_outputs"], ["Bundle", "DCM"])

	def test_regeneration_plan_order_and_preserve_flag(self) -> None:
		r = DerivedModelImpactService.get_affected_outputs_for_change("specification_change")
		plan = r["regeneration_plan"]
		self.assertEqual([p["output_type"] for p in plan], ["Bundle", "DSM", "DEM", "DCM"])
		self.assertTrue(all(p.get("preserve_prior_versions") for p in plan))

	def test_source_addendum_code_in_hints(self) -> None:
		r = DerivedModelImpactService.get_affected_outputs_for_change(
			"boq",
			{"source_addendum_code": "ADD-01"},
		)
		self.assertEqual(r["source_addendum_code"], "ADD-01")
		self.assertTrue(r["regeneration_hints"]["link_regenerated_outputs"])

	def test_unknown_change_type_title(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			DerivedModelImpactService.get_affected_outputs_for_change("not_a_real_change_type")
		self.assertEqual(_msg_title(), DERIVED_ADDENDUM_IMPACT_UNKNOWN_CHANGE_TYPE)

	def test_audit_emitted_when_instance_code_present(self) -> None:
		with patch(
			"kentender_procurement.tender_management.derived_models.addendum.derived_model_impact.emit_std_instance_event",
		) as mock_emit:
			DerivedModelImpactService.get_affected_outputs_for_change(
				"tender_security_change",
				{"instance_code": "STD-INST-1", "addendum_code": "A-9"},
			)
		mock_emit.assert_called_once()
		args, kwargs = mock_emit.call_args
		self.assertEqual(args[0], EVT_STDINST_ADDENDUM_IMPACT_ANALYSED)
		self.assertEqual(kwargs["instance_code"], "STD-INST-1")
		self.assertEqual(kwargs["details"]["change_type"], "tender_security_change")
		self.assertEqual(kwargs["details"]["source_addendum_code"], "A-9")

	def test_no_audit_without_instance_code(self) -> None:
		with patch(
			"kentender_procurement.tender_management.derived_models.addendum.derived_model_impact.emit_std_instance_event",
		) as mock_emit:
			DerivedModelImpactService.get_affected_outputs_for_change("tender_security_change")
		mock_emit.assert_not_called()
