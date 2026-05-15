# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-03 — doc 9 §11.3 ``validate_bid_submission_against_dsm``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p6_03_validate_bid_submission_against_dsm
"""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.tm2_std_adapter import get_current_dsm
from kentender_procurement.tender_management.services.validate_bid_submission_against_dsm import (
	validateBidSubmissionAgainstDsm,
	validate_bid_submission_against_dsm,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import WorksBoqCompletionService


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


class TestP603ValidateBidSubmissionAgainstDsm(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P603"

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

	def _published_si_supplier(self) -> tuple[str, str, str, str]:
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		assert si
		return tcode, tm2, sup, str(si)

	def _boq_payload_with_provisional(self) -> dict:
		return {
			"header": {"currency": "USD"},
			"bills": [
				{
					"bill_number": "B1",
					"bill_title": "Lot 1",
					"bill_type": "Standard",
					"order_index": 0,
					"items": [
						{
							"item_number": "1.1",
							"description": "Measured work",
							"unit": "m2",
							"quantity": 100,
							"item_type": "Normal",
							"supplier_input_mode": "Rate Only",
							"rate_required_from_supplier": True,
						},
						{
							"item_number": "1.2",
							"description": "Provisional allowance",
							"unit": "nr",
							"quantity": 1,
							"item_type": "Provisional Sum",
							"supplier_input_mode": "Fixed Amount",
							"rate_required_from_supplier": False,
							"fixed_amount": 5000,
						},
					],
				},
			],
		}

	def test_p6_03_early_deny_arithmetic_fields_on_bid_payload(self) -> None:
		"""Doc 8 TM2-SMOKE-WORKS-005 / O-06 — arithmetic / correction keys rejected before tender lookup."""
		out = validate_bid_submission_against_dsm(
			"TND-NONEXISTENT-00000",
			"nobody",
			{"corrected_total_price": 1},
		)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(
			out.get("denial_code"),
			DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value,
		)

	def test_p6_03_happy_path(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
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
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertTrue(out.get("ok"), out)
		out2 = validateBidSubmissionAgainstDsm(tcode, sup, bid)
		self.assertTrue(out2.get("ok"), out2)

	def test_p6_03_dsm_output_mismatch_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		dsm_name, content = _dsm_json_for_instance(si)
		reqs = _fill_mandatory_requirements(content)
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name + "-NOTFOUND",
			"supplier": sup,
			"requirements": reqs,
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p6_03_std_instance_mismatch_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		dsm_name, content = _dsm_json_for_instance(si)
		reqs = _fill_mandatory_requirements(content)
		bid = {
			"tender_std_instance_code": si + "-X",
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": reqs,
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p6_03_missing_supplier_field_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		dsm_name, content = _dsm_json_for_instance(si)
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"requirements": _fill_mandatory_requirements(content),
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p6_03_missing_mandatory_requirement_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
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
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
		self.assertIn("DSM-FORE-001", out.get("missing_components") or [])

	def test_p6_03_db_addendum_ack_denied(self) -> None:
		tcode, tm2, sup, si = self._published_si_supplier()
		dsm_name, content = _dsm_json_for_instance(si)
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2,
				"title": "P603 ack gate",
				"reason": "Fixture for P6-03.",
				"requires_supplier_acknowledgement": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("TM2 Addendum", ad.name, "status", "Issued", update_modified=False)
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": _fill_mandatory_requirements(content),
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ADDENDUM_ACK_REQUIRED.value)

	def test_p6_03_boq_missing_required_rate_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		WorksBoqCompletionService.save_boq(si, self._boq_payload_with_provisional())
		d_new = StdInstanceGeneratedOutputService.generate_dsm(si)
		StdInstanceGeneratedOutputService.publish_output(d_new.name)
		dsm_name, content = _dsm_json_for_instance(si)
		reqs = _fill_mandatory_requirements(content)
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": reqs,
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [{"item_number": "1.2"}],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.REQUIRED_BOQ_RATE_MISSING.value)

	def test_p6_03_dsm_sheet_addendum_ack_required_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		dsm_name, content = _dsm_json_for_instance(si)
		patched = json.loads(json.dumps(content))
		patched.setdefault("addendum_acknowledgements", []).append(
			{"addendum_code": "ADD-SHEET-1", "mandatory": True}
		)
		frappe.db.set_value(
			"Tender STD Generated Output",
			dsm_name,
			"content_json",
			json.dumps(patched),
			update_modified=False,
		)
		reqs = _fill_mandatory_requirements(content)
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": reqs,
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ADDENDUM_ACK_REQUIRED.value)
		self.assertIn("ADD-SHEET-1", out.get("missing_dsm_addendum_ack_codes") or [])

	def test_p6_03_boq_negative_rate_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		WorksBoqCompletionService.save_boq(si, self._boq_payload_with_provisional())
		d_new = StdInstanceGeneratedOutputService.generate_dsm(si)
		StdInstanceGeneratedOutputService.publish_output(d_new.name)
		dsm_name, content = _dsm_json_for_instance(si)
		self.assertTrue(content.get("boq_rate_entry", {}).get("enabled"), content)
		reqs = _fill_mandatory_requirements(content)
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": reqs,
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [
				{"item_number": "1.1", "rate": -1},
				{"item_number": "1.2"},
			],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.INVALID_BOQ_RATE_NEGATIVE.value)

	def test_p6_03_boq_quantity_locked_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		WorksBoqCompletionService.save_boq(si, self._boq_payload_with_provisional())
		d_new = StdInstanceGeneratedOutputService.generate_dsm(si)
		StdInstanceGeneratedOutputService.publish_output(d_new.name)
		dsm_name, content = _dsm_json_for_instance(si)
		reqs = _fill_mandatory_requirements(content)
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": reqs,
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [
				{"item_number": "1.1", "rate": 10, "quantity": 99},
				{"item_number": "1.2"},
			],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_QUANTITY_LOCKED.value)

	def test_p6_03_boq_provisional_rate_locked_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		WorksBoqCompletionService.save_boq(si, self._boq_payload_with_provisional())
		d_new = StdInstanceGeneratedOutputService.generate_dsm(si)
		StdInstanceGeneratedOutputService.publish_output(d_new.name)
		dsm_name, content = _dsm_json_for_instance(si)
		reqs = _fill_mandatory_requirements(content)
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": reqs,
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [
				{"item_number": "1.1", "rate": 10},
				{"item_number": "1.2", "rate": 1},
			],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_FIXED_AMOUNT_LOCKED.value)

	def test_p6_03_boq_happy_with_rates(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		WorksBoqCompletionService.save_boq(si, self._boq_payload_with_provisional())
		d_new = StdInstanceGeneratedOutputService.generate_dsm(si)
		StdInstanceGeneratedOutputService.publish_output(d_new.name)
		dsm_name, content = _dsm_json_for_instance(si)
		reqs = _fill_mandatory_requirements(content)
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": reqs,
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [
				{"item_number": "1.1", "rate": 12.5},
				{"item_number": "1.2"},
			],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertTrue(out.get("ok"), out)

	def test_p6_03_dsm_missing_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier()
		dsm_name, content = _dsm_json_for_instance(si)
		frappe.db.set_value("Tender STD Instance", si, "current_dsm_output_code", None, update_modified=False)
		meta = get_current_dsm(si)
		self.assertFalse(meta.get("ok"))
		bid = {
			"tender_std_instance_code": si,
			"dsm_output_code": dsm_name,
			"supplier": sup,
			"requirements": _fill_mandatory_requirements(content),
			"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
			"boq": [],
		}
		out = validate_bid_submission_against_dsm(tcode, sup, bid)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_DSM_MISSING_OR_STALE.value)
