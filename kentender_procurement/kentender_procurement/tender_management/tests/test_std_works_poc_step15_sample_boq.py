# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 15 — sample BoQ generation (engine + controller).

Run:
    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_step15_sample_boq
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as controller,
)
from kentender_procurement.tender_management.services import std_template_engine as engine
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

PRIMARY_SAMPLE_CATEGORY_COUNT = 9


class TestStdWorksPocStep15SampleBoq(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

		self.tender = frappe.new_doc("Procurement Tender")
		self.tender.std_template = TEMPLATE_CODE
		self.tender.tender_title = "Step15 Smoke Tender"
		self.tender.tender_reference = "STEP15-SMOKE"
		self.tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		self.tender.tender_scope = "NATIONAL"
		self.tender.insert(ignore_permissions=True)

	def _reload_tender(self):
		return frappe.get_doc("Procurement Tender", self.tender.name)

	def _primary_template(self) -> dict:
		return engine.load_template(TEMPLATE_CODE)

	# ------------------------------------------------------------------
	# STEP15-AC-001 — rows from sample_tender.json
	# ------------------------------------------------------------------

	def test_step15_ac001_load_sample_boq_rows_from_package(self) -> None:
		template = self._primary_template()
		rows = engine.load_sample_boq_rows(template)
		self.assertEqual(len(rows), PRIMARY_SAMPLE_CATEGORY_COUNT)
		self.assertTrue(all(isinstance(r, dict) for r in rows))

	# ------------------------------------------------------------------
	# STEP15-AC-002 / AC-003 / AC-004 / AC-005 / AC-006 / AC-007 / AC-008
	# ------------------------------------------------------------------

	def test_step15_generate_writes_child_rows_idempotent_envelope(self) -> None:
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		tender.set("boq_items", [])
		tender.save(ignore_permissions=True)

		result = controller.generate_sample_boq(self.tender.name)
		self.assertTrue(result["ok"])
		self.assertEqual(result["message"], "Sample BoQ generated.")
		self.assertEqual(result["boq_row_count"], PRIMARY_SAMPLE_CATEGORY_COUNT)
		self.assertEqual(result["lot_verification"], "verified")
		self.assertEqual(len(result["categories"]), PRIMARY_SAMPLE_CATEGORY_COUNT)

		tender2 = self._reload_tender()
		self.assertEqual(len(tender2.boq_items), PRIMARY_SAMPLE_CATEGORY_COUNT)
		codes = [r.item_code for r in tender2.boq_items]
		self.assertEqual(len(codes), len(set(codes)))

		categories_on_doc = {r.item_category for r in tender2.boq_items}
		self.assertIn("DAYWORKS", categories_on_doc)
		self.assertIn("PROVISIONAL_SUMS", categories_on_doc)
		self.assertIn("GRAND_SUMMARY", categories_on_doc)

		for r in tender2.boq_items:
			self.assertIn(
				"STD-WORKS-POC sample_tender.json",
				r.notes or "",
			)

		result2 = controller.generate_sample_boq(self.tender.name)
		self.assertEqual(result2["boq_row_count"], PRIMARY_SAMPLE_CATEGORY_COUNT)
		tender3 = self._reload_tender()
		self.assertEqual(len(tender3.boq_items), PRIMARY_SAMPLE_CATEGORY_COUNT)
		self.assertEqual(
			[r.item_code for r in tender2.boq_items],
			[r.item_code for r in tender3.boq_items],
		)

	# ------------------------------------------------------------------
	# STEP15-AC-009 / AC-010 — validation errors
	# ------------------------------------------------------------------

	def test_step15_ac009_unknown_category_raises(self) -> None:
		template = self._primary_template()
		rows = engine.load_sample_boq_rows(template)
		bad = dict(rows[0])
		bad["item_category"] = "NOT_A_REAL_CATEGORY"
		with self.assertRaises(ValueError) as ctx:
			engine.validate_sample_boq_rows(
				[bad],
				engine.get_allowed_boq_categories(),
				existing_lot_codes=frozenset({"LOT-001"}),
				strict_lot_references=True,
			)
		self.assertIn("unknown item_category", str(ctx.exception))

	def test_step15_ac010_missing_required_field_raises(self) -> None:
		template = self._primary_template()
		rows = engine.load_sample_boq_rows(template)
		bad = {k: v for k, v in rows[0].items() if k != "description"}
		with self.assertRaises(ValueError) as ctx:
			engine.validate_sample_boq_rows(
				[bad],
				engine.get_allowed_boq_categories(),
			)
		self.assertIn("missing required field", str(ctx.exception))

	def test_step15_duplicate_item_code_raises(self) -> None:
		template = self._primary_template()
		rows = engine.load_sample_boq_rows(template)
		first = dict(rows[0])
		second = dict(rows[1])
		second["item_code"] = first["item_code"]
		with self.assertRaises(ValueError) as ctx:
			engine.validate_sample_boq_rows(
				[first, second],
				engine.get_allowed_boq_categories(),
			)
		self.assertIn("Duplicate item_code", str(ctx.exception))

	def test_step15_bad_lot_reference_raises_when_lots_exist(self) -> None:
		template = self._primary_template()
		rows = engine.load_sample_boq_rows(template)
		bad = dict(rows[0])
		bad["lot_code"] = "LOT-999"
		with self.assertRaises(ValueError) as ctx:
			engine.validate_sample_boq_rows(
				[bad],
				engine.get_allowed_boq_categories(),
				existing_lot_codes=frozenset({"LOT-001", "LOT-002"}),
				strict_lot_references=True,
			)
		self.assertIn("LOT-999", str(ctx.exception))

	# ------------------------------------------------------------------
	# STEP15-AC-011 — BoQ rules pass after generation
	# ------------------------------------------------------------------

	def test_step15_ac011_validation_passes_boq_rules_after_generate(self) -> None:
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		tender.set("boq_items", [])
		tender.save(ignore_permissions=True)
		controller.generate_sample_boq(self.tender.name)

		res = controller.validate_tender_configuration(self.tender.name)
		self.assertTrue(res["ok"])
		tender2 = self._reload_tender()
		blockers = {
			m.rule_code
			for m in tender2.validation_messages
			if getattr(m, "severity", None) == "BLOCKER"
		}
		self.assertNotIn("RULE_BOQ_REQUIRE_ROWS", blockers)
		self.assertNotIn("RULE_DAYWORKS_REQUIRE_ROWS", blockers)
		self.assertNotIn("RULE_PROVISIONAL_SUMS_REQUIRE_ROWS", blockers)

	def test_step15_missing_dayworks_row_blocks_validation(self) -> None:
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		kept = [r for r in tender.boq_items if r.item_category != "DAYWORKS"]
		tender.set("boq_items", [])
		for r in kept:
			tender.append("boq_items", r.as_dict())
		tender.save(ignore_permissions=True)

		res = controller.validate_tender_configuration(self.tender.name)
		self.assertFalse(res["ok"])
		tender2 = self._reload_tender()
		codes = {m.rule_code for m in tender2.validation_messages}
		self.assertIn("RULE_DAYWORKS_REQUIRE_ROWS", codes)

	def test_step15_missing_provisional_sums_row_blocks_validation(self) -> None:
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		kept = [r for r in tender.boq_items if r.item_category != "PROVISIONAL_SUMS"]
		tender.set("boq_items", [])
		for r in kept:
			tender.append("boq_items", r.as_dict())
		tender.save(ignore_permissions=True)

		res = controller.validate_tender_configuration(self.tender.name)
		self.assertFalse(res["ok"])
		tender2 = self._reload_tender()
		codes = {m.rule_code for m in tender2.validation_messages}
		self.assertIn("RULE_PROVISIONAL_SUMS_REQUIRE_ROWS", codes)

	# ------------------------------------------------------------------
	# STEP15-AC-012 — preview warning (HTML substring via renderer module)
	# ------------------------------------------------------------------

	def test_step15_ac012_boq_warning_in_preview_html(self) -> None:
		controller.load_sample_tender(self.tender.name)
		controller.generate_tender_pack_preview(self.tender.name)
		html = self._reload_tender().generated_tender_pack_html or ""
		self.assertIn(
			"representative sample structured data",
			html.lower(),
		)

	# ------------------------------------------------------------------
	# STEP15 — invalidation after BoQ replace
	# ------------------------------------------------------------------

	def test_step15_resets_validation_status_after_generate(self) -> None:
		controller.load_sample_tender(self.tender.name)
		controller.validate_tender_configuration(self.tender.name)
		tender = self._reload_tender()
		self.assertNotEqual(tender.validation_status, "Not Validated")

		tender.set("boq_items", [])
		tender.save(ignore_permissions=True)
		controller.generate_sample_boq(self.tender.name)
		tender2 = self._reload_tender()
		self.assertEqual(tender2.validation_status, "Not Validated")
		self.assertEqual(len(tender2.validation_messages), 0)

	# ------------------------------------------------------------------
	# STEP15 — no lots on tender
	# ------------------------------------------------------------------

	def test_step15_skipped_lot_verification_when_no_lots(self) -> None:
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		tender.set("lots", [])
		tender.set("boq_items", [])
		tender.save(ignore_permissions=True)

		result = controller.generate_sample_boq(self.tender.name)
		self.assertTrue(result["ok"])
		self.assertEqual(result["lot_verification"], "skipped_no_lots")
		self.assertEqual(result["boq_row_count"], PRIMARY_SAMPLE_CATEGORY_COUNT)
