# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-03 — doc 9 §10.3 ``create_addendum``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p5_03_create_addendum
"""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.create_addendum import create_addendum
from kentender_procurement.tender_management.services.submit_clarification import submit_clarification
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p5_addendum_fixture import (
	_P5PublishedTenderChainMixin,
)


class TestP503CreateAddendum(_P5PublishedTenderChainMixin, _P401Tm2Cleanup):
	def test_p5_03_success_draft_and_audit(self) -> None:
		tcode, tm2 = self._published_tender()
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("status"), "Draft")
		self.assertTrue(str(out.get("addendum_code") or "").startswith(f"ADD-{tcode}-"))

		add = frappe.get_doc("TM2 Addendum", out.get("addendum"))
		self.assertEqual(add.status, "Draft")
		self.assertEqual(add.primary_impact_type, "BOQ Change")

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Addendum Created"},
			fields=["related_object_id", "event_payload"],
			order_by="creation desc",
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].get("related_object_id"), add.name)
		pl = ev[0].get("event_payload") or {}
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertEqual(pl.get("addendum_code"), out.get("addendum_code"))

	def test_p5_03_reason_required(self) -> None:
		tcode, _tm2 = self._published_tender()
		p = self._base_payload()
		p["reason"] = "  "
		out = create_addendum("Administrator", tcode, payload=p, context=self._add_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_REASON_REQUIRED.value)

	def test_p5_03_title_required(self) -> None:
		tcode, _tm2 = self._published_tender()
		p = self._base_payload()
		p["title"] = ""
		out = create_addendum("Administrator", tcode, payload=p, context=self._add_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p5_03_primary_impact_required(self) -> None:
		tcode, _tm2 = self._published_tender()
		p = self._base_payload()
		p["primary_impact_type"] = ""
		out = create_addendum("Administrator", tcode, payload=p, context=self._add_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p5_03_invalid_primary_impact(self) -> None:
		tcode, _tm2 = self._published_tender()
		p = self._base_payload()
		p["primary_impact_type"] = "Not A Real Type"
		out = create_addendum("Administrator", tcode, payload=p, context=self._add_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p5_03_tender_state_denied(self) -> None:
		tcode, tm2 = self._published_tender()
		frappe.db.set_value("TM2 Tender", tm2, "status", "Draft", update_modified=False)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p5_03_role_denied(self) -> None:
		tcode, _tm2 = self._published_tender()
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context={"granted_permissions": []},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p5_03_proposed_changes_in_audit_payload(self) -> None:
		tcode, tm2 = self._published_tender()
		p = self._base_payload()
		p["proposed_changes"] = {"boq": [{"line": "12", "action": "revise_qty"}]}
		out = create_addendum("Administrator", tcode, payload=p, context=self._add_ctx())
		self.assertTrue(out.get("ok"), out)
		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Addendum Created"},
			fields=["event_payload"],
			order_by="creation desc",
			limit=1,
		)
		pl = ev[0].get("event_payload") or {}
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertIn("boq", (pl.get("proposed_changes") or {}))

	def test_p5_03_source_clarification_lineage(self) -> None:
		tcode, tm2 = self._published_tender()
		self._ensure_open_clarification_window(tm2)
		sup = self._ensure_supplier("Src")
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2, "supplier": sup}
		).insert(ignore_permissions=True)
		spec_clr = spec_for_action("CLR2_SUBMIT")
		assert spec_clr is not None
		sout = submit_clarification(
			"Administrator",
			tcode,
			payload={"supplier": sup, "question_text": "Line 5 scope unclear."},
			context={"granted_permissions": [spec_clr.required_permission], "acting_supplier": sup},
		)
		self.assertTrue(sout.get("ok"), sout)
		clr_name = str(sout.get("clarification_request") or "")

		p = self._base_payload()
		p["tm2_source_clarification_request"] = clr_name
		out = create_addendum("Administrator", tcode, payload=p, context=self._add_ctx())
		self.assertTrue(out.get("ok"), out)
		add = frappe.get_doc("TM2 Addendum", out.get("addendum"))
		self.assertEqual(add.tm2_source_clarification_request, clr_name)

	def test_p5_03_proposed_changes_not_dict_denied(self) -> None:
		tcode, _tm2 = self._published_tender()
		p = self._base_payload()
		p["proposed_changes"] = "not-a-dict"
		out = create_addendum("Administrator", tcode, payload=p, context=self._add_ctx())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
