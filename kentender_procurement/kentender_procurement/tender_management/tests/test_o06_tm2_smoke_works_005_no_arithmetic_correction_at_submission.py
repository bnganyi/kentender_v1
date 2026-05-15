# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""O-06 — doc 8 **TM2-SMOKE-WORKS-005**; doc 9 §21.2 ``test_TM2_SMOKE_WORKS_005_…``.

Submission must **not** accept evaluation-stage arithmetic / correction fields on the bid payload
(doc 8 §12 narrative: system computes submitted totals; correction logic belongs to Evaluation only).

* Top-level forbidden keys (e.g. ``corrected_total_price``, ``arithmetic_correction``) →
  ``BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION``.
* Extra keys on ``boq`` line dicts (only ``item_number``, ``rate``, optional ``quantity`` allowed) →
  ``BOQ_SUPPLIER_RATE_ENTRY_DENIED``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_o06_tm2_smoke_works_005_no_arithmetic_correction_at_submission
"""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.tm2_std_adapter import get_current_dsm
from kentender_procurement.tender_management.services.validate_bid_submission_against_dsm import (
	validate_bid_submission_against_dsm,
)
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.tm2_works_boq_supplier_fixture import (
	Tm2WorksBoqSupplierFixture,
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


def _valid_bid(sup: str, si: str) -> dict:
	dsm_name, content = _dsm_json_for_instance(si)
	return {
		"tender_std_instance_code": si,
		"dsm_output_code": dsm_name,
		"supplier": sup,
		"requirements": _fill_mandatory_requirements(content),
		"addendum_acknowledgements": _fill_mandatory_dsm_addendum_acks(content),
		"boq": [{"item_number": "1.1", "rate": 10.0}, {"item_number": "1.2"}],
	}


class TestO06Tm2SmokeWorks005NoArithmeticCorrectionAtSubmission(
	Tm2WorksBoqSupplierFixture,
	_P401Tm2Cleanup,
	P6PublishedTm2Fixture,
):
	"""Doc 8 TM2-SMOKE-WORKS-005 — bid submission rejects arithmetic / correction payload keys."""

	p6_supplier_fixture_prefix = "O06"

	def test_TM2_SMOKE_WORKS_005_no_arithmetic_correction_at_submission(self) -> None:
		tcode, _tm2, sup, si = self._published_si_supplier_boq()
		base = _valid_bid(sup, si)

		out_top = validate_bid_submission_against_dsm(
			tcode,
			sup,
			{**base, "corrected_total_price": 96750000},
		)
		self.assertFalse(out_top.get("ok"), out_top)
		self.assertEqual(
			out_top.get("denial_code"),
			DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value,
		)

		out_line = validate_bid_submission_against_dsm(
			tcode,
			sup,
			{
				**base,
				"boq": [
					{"item_number": "1.1", "rate": 10.0, "boq_arithmetic_correction": {}},
					{"item_number": "1.2"},
				],
			},
		)
		self.assertFalse(out_line.get("ok"), out_line)
		self.assertEqual(out_line.get("denial_code"), DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value)
