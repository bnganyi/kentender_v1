# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-05 — doc 9 §11.5 ``submit_bid`` / ``submitBid`` (submit, seal, receipt).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p6_05_submit_bid
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submitBid, submit_bid
from kentender_procurement.tender_management.services.tm2_std_adapter import get_current_dsm
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


def _dsm_json_for_instance(si: str) -> tuple[str, dict]:
	meta = get_current_dsm(si)
	assert meta.get("ok"), meta
	name = str(meta.get("output_code") or "")
	doc = frappe.get_doc("Tender STD Generated Output", name)
	raw = doc.get("content_json")
	if isinstance(raw, dict):
		return name, raw
	return name, json.loads(raw or "{}")


def _fill_mandatory_requirements(content: dict) -> dict[str, dict]:
	out: dict[str, dict] = {}
	for row in content.get("requirements") or []:
		if not isinstance(row, dict) or not row.get("mandatory"):
			continue
		code = (row.get("requirement_code") or "").strip()
		rt = (row.get("requirement_type") or "").strip()
		if not code or rt in ("System", "BOQRateEntry"):
			continue
		if rt in ("Declaration", "Acknowledgement"):
			out[code] = {"acknowledged": True}
		else:
			out[code] = {"value": "fixture"}
	return out


def _fill_mandatory_dsm_addendum_acks(content: dict) -> dict[str, bool]:
	flags: dict[str, bool] = {}
	for row in content.get("addendum_acknowledgements") or []:
		if not isinstance(row, dict):
			continue
		if row.get("mandatory"):
			ac = (row.get("addendum_code") or "").strip()
			if ac:
				flags[ac] = True
	return flags


def _valid_bid_for_fixture(tcode: str, sup: str, si: str) -> dict:
	dsm_name, content = _dsm_json_for_instance(si)
	reqs = _fill_mandatory_requirements(content)
	acks = _fill_mandatory_dsm_addendum_acks(content)
	bid: dict = {
		"tender_std_instance_code": si,
		"dsm_output_code": dsm_name,
		"supplier": sup,
		"requirements": reqs,
		"addendum_acknowledgements": acks,
		"boq": [],
	}
	if content.get("boq_rate_entry") and isinstance(content["boq_rate_entry"], dict):
		if content["boq_rate_entry"].get("enabled"):
			boq_doc = frappe.db.get_value("Tender STD Instance BOQ", {"tender_std_instance": si}, "name")
			assert boq_doc, "Fixture must have BOQ when DSM enables rate entry"
			bid["boq"] = [{"item_number": "1.1", "rate": 10.5}]
	return bid


class TestP605SubmitBid(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P605"

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

	def _portal_ctx(self) -> dict:
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

	def test_p6_05_happy_path_sealed_receipt_audits(self) -> None:
		tcode, tm2, sup, si = self._published_si_supplier()
		ctx = {**self._portal_ctx(), "acting_supplier": sup}
		bid = _valid_bid_for_fixture(tcode, sup, si)
		out = submitBid("Administrator", tcode, sup, bid, context=ctx)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("bid_status"), "Sealed")
		bc = str(out.get("bid_code") or "")
		self.assertTrue(bc)
		self.assertEqual(out.get("receipt_code"), f"RCT-{bc}")
		self.assertEqual(str(out.get("receipt") or ""), f"RCT-{bc}")
		sub_hash = str(out.get("submission_hash") or "")
		self.assertEqual(len(sub_hash), 64)
		bid_name = str(out.get("bid_submission") or "")
		self.assertTrue(bid_name)
		self.assertEqual(frappe.db.get_value("TM2 Bid Submission", bid_name, "bid_status"), "Sealed")
		self.assertEqual(frappe.db.get_value("TM2 Bid Submission", bid_name, "submission_hash"), sub_hash)
		events = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "related_object_id": bid_name},
			pluck="event_type",
		)
		self.assertIn("Bid Submitted", events)
		self.assertIn("Bid Sealed", events)
		comp_n = frappe.db.count("TM2 Bid Submission Component", {"tm2_bid_submission": bid_name})
		self.assertGreater(comp_n, 0)

	def test_p6_05_draft_tender_denied(self) -> None:
		self._ensure_std_bindable()
		tcode = self._mk_approved_for_publication(seed_outputs=False)
		out = submit_bid(
			"Administrator",
			tcode,
			"irrelevant-supplier",
			{},
			context={**self._portal_ctx(), "acting_supplier": "irrelevant-supplier"},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p6_05_deadline_passed_denied(self) -> None:
		tcode, tm2, sup, si = self._published_si_supplier()
		tl = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2}, "name")
		self.assertTrue(tl)
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl,
			{"submission_deadline_at": add_to_date(now_datetime(), days=-1)},
			update_modified=False,
		)
		bid = _valid_bid_for_fixture(tcode, sup, si)
		out = submit_bid(
			"Administrator",
			tcode,
			sup,
			bid,
			context={**self._portal_ctx(), "acting_supplier": sup},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_DEADLINE_PASSED.value)
		self.assertTrue(out.get("late_attempt"))
		self.assertTrue(out.get("late_attempt_code"))

	def test_p6_05_duplicate_sealed_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		ctx = {**self._portal_ctx(), "acting_supplier": sup}
		bid = _valid_bid_for_fixture(tcode, sup, si)
		out1 = submit_bid("Administrator", tcode, sup, bid, context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		out2 = submit_bid("Administrator", tcode, sup, bid, context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
		self.assertEqual(out2.get("existing_bid_submission"), out1.get("bid_submission"))

	def test_p6_05_validation_denied_missing_requirement(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		ctx = {**self._portal_ctx(), "acting_supplier": sup}
		dsm_name, content = _dsm_json_for_instance(si)
		reqs = _fill_mandatory_requirements(content)
		if "DSM-FORE-001" in reqs:
			del reqs["DSM-FORE-001"]
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": reqs,
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [],
		}
		out = submit_bid("Administrator", tcode, sup, bid, context=ctx)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p6_05_role_denied_without_permission(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		bid = _valid_bid_for_fixture(tcode, sup, si)
		out = submit_bid(
			"Administrator",
			tcode,
			sup,
			bid,
			context={"granted_permissions": [], "acting_supplier": sup},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)
