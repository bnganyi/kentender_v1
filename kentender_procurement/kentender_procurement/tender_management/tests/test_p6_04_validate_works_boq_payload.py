# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-04 — doc 9 §11.4 ``validate_works_boq_payload``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p6_04_validate_works_boq_payload
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.validate_works_boq_payload import (
	validateWorksBoqPayload,
	validate_works_boq_payload,
)
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.tm2_works_boq_supplier_fixture import (
	Tm2WorksBoqSupplierFixture,
)


def _boq_payload_with_provisional() -> dict:
	return {
		"header": {"currency": "KES"},
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


class TestP604ValidateWorksBoqPayload(Tm2WorksBoqSupplierFixture, _P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P604"

	def test_p6_04_happy_path_total_and_currency(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier_boq()
		out = validate_works_boq_payload(tcode, sup, {"lines": self._valid_lines()})
		self.assertTrue(out.get("ok"), out)
		self.assertFalse(out.get("correction_applied"))
		self.assertEqual(out.get("currency"), "KES")
		# 100 * 10 + 5000 provisional lump = 6000
		self.assertEqual(out.get("submitted_total_price"), 6000)
		self.assertEqual(out.get("line_amounts", {}).get("1.1"), 1000.0)
		self.assertEqual(out.get("line_amounts", {}).get("1.2"), 5000.0)
		out2 = validateWorksBoqPayload(tcode, sup, self._valid_lines())
		self.assertTrue(out2.get("ok"), out2)

	def test_p6_04_list_root_lines_ok(self) -> None:
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		out = validate_works_boq_payload(tcode, sup, self._valid_lines())
		self.assertTrue(out.get("ok"), out)

	def test_p6_04_bills_shape_denied(self) -> None:
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		out = validate_works_boq_payload(tcode, sup, _boq_payload_with_provisional())
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value)

	def test_p6_04_extra_line_key_denied(self) -> None:
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		bad = [{"item_number": "1.1", "rate": 1, "description": "no"}]
		out = validate_works_boq_payload(tcode, sup, {"lines": bad})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value)

	def test_p6_04_arithmetic_field_denied(self) -> None:
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		out = validate_works_boq_payload(
			tcode,
			sup,
			{"lines": self._valid_lines(), "correction_applied": False},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value)

	def test_p6_04_negative_rate_denied(self) -> None:
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		lines = [{"item_number": "1.1", "rate": -1}, {"item_number": "1.2"}]
		out = validate_works_boq_payload(tcode, sup, {"lines": lines})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.INVALID_BOQ_RATE_NEGATIVE.value)

	def test_p6_04_zero_rate_denied_by_default(self) -> None:
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		lines = [{"item_number": "1.1", "rate": 0}, {"item_number": "1.2"}]
		out = validate_works_boq_payload(tcode, sup, {"lines": lines})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value)

	def test_p6_04_zero_rate_allowed_when_dsm_flag(self) -> None:
		"""Simulate DSM ``boq_rate_entry.allow_zero_supplier_rates`` (published DSM is DB-immutable)."""
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		with patch(
			"kentender_procurement.tender_management.services.validate_works_boq_payload._allow_zero_rates",
			return_value=True,
		):
			lines = [{"item_number": "1.1", "rate": 0}, {"item_number": "1.2"}]
			out = validate_works_boq_payload(tcode, sup, {"lines": lines})
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("submitted_total_price"), 5000)

	def test_p6_04_quantity_mismatch_denied(self) -> None:
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		lines = [{"item_number": "1.1", "rate": 1, "quantity": 99}, {"item_number": "1.2"}]
		out = validate_works_boq_payload(tcode, sup, {"lines": lines})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_QUANTITY_LOCKED.value)

	def test_p6_04_missing_rate_denied(self) -> None:
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		lines = [{"item_number": "1.2"}]
		out = validate_works_boq_payload(tcode, sup, {"lines": lines})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.REQUIRED_BOQ_RATE_MISSING.value)

	def test_p6_04_unknown_item_denied(self) -> None:
		tcode, _tm2, sup, _si = self._published_si_supplier_boq()
		lines = [*self._valid_lines(), {"item_number": "9.9", "rate": 1}]
		out = validate_works_boq_payload(tcode, sup, {"lines": lines})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value)

	def test_p6_04_non_works_category_denied(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier_boq()
		frappe.db.set_value(
			"Tender STD Instance",
			si,
			{"procurement_category": "GOODS"},
			update_modified=False,
		)
		self.addCleanup(
			lambda: frappe.db.set_value(
				"Tender STD Instance",
				si,
				{"procurement_category": "WORKS"},
				update_modified=False,
			)
		)
		out = validate_works_boq_payload(tcode, sup, {"lines": self._valid_lines()})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
