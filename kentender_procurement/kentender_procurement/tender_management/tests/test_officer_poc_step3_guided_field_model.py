# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — Officer step 3 guided field model.

Exercises ``get_officer_guided_field_model`` against the bundled Works POC
``fields.json`` (grouping, field inventory size, stable anchor field codes).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_officer_poc_step3_guided_field_model
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.services.officer_tender_config import (
	OFFICER_POC_TEMPLATE_CODE,
	build_officer_guided_field_model,
	get_officer_guided_field_model,
	load_officer_fields_document,
)


def _officer_field_model_spec_path() -> Path:
	repo = Path(__file__).resolve().parents[4]
	return (
		repo
		/ "docs"
		/ "prompts"
		/ "std poc"
		/ "tender configuration"
		/ "3. procurement_officer_tender_configuration_poc_guided_configuration_field_model.md"
	)


class TestOfficerPocStep3GuidedFieldModel(UnitTestCase):
	def test_field_model_spec_has_stable_anchors(self) -> None:
		path = _officer_field_model_spec_path()
		self.assertTrue(path.is_file(), f"Expected field model spec at {path}")
		text = path.read_text(encoding="utf-8")
		for anchor in (
			"## 7. Field Group Model",
			"## 10. Required Group and Field Inventory",
			"TENDER_IDENTITY",
			"OFFICER-FIELD-AC-001",
		):
			with self.subTest(anchor=anchor):
				self.assertIn(anchor, text)

	def test_get_officer_guided_field_model_matches_package_shape(self) -> None:
		model = get_officer_guided_field_model()
		self.assertEqual(model.get("template_code"), OFFICER_POC_TEMPLATE_CODE)
		groups = model["groups"]
		self.assertEqual(len(groups), 9)
		codes = [g["group_code"] for g in groups]
		self.assertEqual(
			codes[0],
			"TENDER_IDENTITY",
			msg="First group follows package render_order",
		)
		total_fields = sum(len(g["fields"]) for g in groups)
		self.assertEqual(total_fields, 75)
		all_codes = [f["field_code"] for g in groups for f in g["fields"]]
		self.assertEqual(len(all_codes), len(set(all_codes)))
		for required in (
			"TENDER.TENDER_REFERENCE",
			"TENDER.TENDER_NAME",
			"METHOD.PROCUREMENT_METHOD",
			"METHOD.TENDER_SCOPE",
			"WORKS.DAYWORKS_INCLUDED",
			"WORKS.PROVISIONAL_SUMS_INCLUDED",
		):
			with self.subTest(required=required):
				self.assertIn(required, all_codes)

	def test_build_model_is_deterministic_for_same_payload(self) -> None:
		raw = load_officer_fields_document()
		a = build_officer_guided_field_model(raw)
		b = build_officer_guided_field_model(raw)
		self.assertEqual(a, b)
