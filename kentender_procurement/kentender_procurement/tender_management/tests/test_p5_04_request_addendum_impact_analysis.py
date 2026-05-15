# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-04 — doc 9 §10.4 ``request_addendum_impact_analysis``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p5_04_request_addendum_impact_analysis
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.create_addendum import create_addendum
from kentender_procurement.tender_management.services.request_addendum_impact_analysis import (
	request_addendum_impact_analysis,
	requestAddendumImpactAnalysis,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p5_addendum_fixture import (
	_P5PublishedTenderChainMixin,
)


class TestP504RequestAddendumImpactAnalysis(_P5PublishedTenderChainMixin, _P401Tm2Cleanup):
	def _cleanup_air_for_tender(self, tm2: str | None) -> None:
		frappe.set_user("Administrator")
		if not tm2 or not frappe.db.exists("TM2 Tender", tm2):
			return
		for add in frappe.get_all("TM2 Addendum", filters={"tm2_tender": tm2}, pluck="name"):
			for air in frappe.get_all(
				"TM2 Addendum Impact Record",
				filters={"tm2_addendum": add},
				pluck="name",
			):
				if frappe.db.exists("TM2 Addendum Impact Record", air):
					frappe.delete_doc(
						"TM2 Addendum Impact Record",
						air,
						force=True,
						ignore_permissions=True,
					)

	def _published_tender_with_draft_addendum(self) -> tuple[str, str, str, str]:
		"""Return ``(tender_code, tm2_name, addendum_doc_name, addendum_code)``."""
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_air_for_tender, tm2)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		ac = str(out.get("addendum_code") or "")
		ad_name = str(out.get("addendum") or "")
		self.assertTrue(ac and ad_name)
		return tcode, tm2, ad_name, ac

	def _impact_ctx(self) -> dict:
		spec = spec_for_action("ADD2_REQUEST_IMPACT_ANALYSIS")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def test_p5_04_success_air_status_audit(self) -> None:
		tcode, tm2, ad_name, ac = self._published_tender_with_draft_addendum()
		out = requestAddendumImpactAnalysis(
			"Administrator",
			ac,
			context=self._impact_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("addendum_code"), ac)
		self.assertEqual(out.get("tender_code"), tcode)
		self.assertEqual(out.get("addendum_status"), "Impact Analysis Complete")

		air_name = str(out.get("impact_record") or "")
		self.assertTrue(air_name)
		air = frappe.get_doc("TM2 Addendum Impact Record", air_name)
		self.assertEqual(air.tm2_addendum, ad_name)
		self.assertEqual(air.impact_record_code, f"AIR-{ac}")
		self.assertEqual(air.std_impact_analysis_code, f"STDIA-{ac}-TM2")
		pl_raw = air.impact_payload
		if isinstance(pl_raw, str):
			pl_raw = json.loads(pl_raw)
		self.assertIsInstance(pl_raw, dict)
		self.assertTrue(pl_raw.get("ok"))

		ad = frappe.get_doc("TM2 Addendum", ad_name)
		self.assertEqual(ad.status, "Impact Analysis Complete")

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={
				"tm2_tender": tm2,
				"event_type": "Addendum Impact Analysis Completed",
			},
			fields=["related_object_type", "related_object_id", "event_payload"],
			order_by="creation desc",
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].get("related_object_type"), "TM2 Addendum Impact Record")
		self.assertEqual(ev[0].get("related_object_id"), air.impact_record_code)
		pl = ev[0].get("event_payload") or {}
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertEqual(pl.get("addendum_code"), ac)

	def test_p5_04_proposed_changes_passed_to_adapter(self) -> None:
		_tcode, _tm2, _ad_name, ac = self._published_tender_with_draft_addendum()
		pc = {"boq": [{"line": "1"}]}
		captured: dict = {}

		def fake(acode: str, proposed: dict):
			captured["code"] = acode
			captured["proposed"] = proposed
			from kentender_procurement.tender_management.services.tm2_std_adapter import (
				analyze_addendum_impact,
			)

			return analyze_addendum_impact(acode, proposed)

		with patch(
			"kentender_procurement.tender_management.services.request_addendum_impact_analysis.analyze_addendum_impact",
			side_effect=fake,
		):
			out = request_addendum_impact_analysis(
				"Administrator",
				ac,
				context={**self._impact_ctx(), "proposed_changes": pc},
			)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(captured.get("code"), ac)
		self.assertEqual(captured.get("proposed"), pc)

	def test_p5_04_not_draft_denied(self) -> None:
		_tcode, _tm2, ad_name, ac = self._published_tender_with_draft_addendum()
		frappe.db.set_value("TM2 Addendum", ad_name, "status", "Pending Legal Review", update_modified=False)
		out = request_addendum_impact_analysis("Administrator", ac, context=self._impact_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p5_04_duplicate_air_denied(self) -> None:
		_tcode, _tm2, ad_name, ac = self._published_tender_with_draft_addendum()
		first = request_addendum_impact_analysis("Administrator", ac, context=self._impact_ctx())
		self.assertTrue(first.get("ok"), first)
		frappe.db.set_value("TM2 Addendum", ad_name, "status", "Draft", update_modified=False)
		second = request_addendum_impact_analysis("Administrator", ac, context=self._impact_ctx())
		self.assertFalse(second.get("ok"))
		self.assertEqual(second.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p5_04_role_denied(self) -> None:
		_tcode, _tm2, _ad_name, ac = self._published_tender_with_draft_addendum()
		out = request_addendum_impact_analysis(
			"Administrator",
			ac,
			context={"granted_permissions": []},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p5_04_unknown_addendum_denied(self) -> None:
		out = request_addendum_impact_analysis(
			"Administrator",
			"ADD-NONEXISTENT-999999-99",
			context=self._impact_ctx(),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value)

	def test_p5_04_proposed_changes_not_dict_denied(self) -> None:
		_tcode, _tm2, _ad_name, ac = self._published_tender_with_draft_addendum()
		out = request_addendum_impact_analysis(
			"Administrator",
			ac,
			context={**self._impact_ctx(), "proposed_changes": "not-a-dict"},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p5_04_adapter_failure_surfaces(self) -> None:
		_tcode, _tm2, _ad_name, ac = self._published_tender_with_draft_addendum()
		with patch(
			"kentender_procurement.tender_management.services.request_addendum_impact_analysis.analyze_addendum_impact",
			return_value={
				"ok": False,
				"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
				"message": "stub adapter failure",
			},
		):
			out = request_addendum_impact_analysis("Administrator", ac, context=self._impact_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
		self.assertFalse(
			frappe.db.exists("TM2 Addendum Impact Record", {"tm2_addendum": _ad_name}),
		)
