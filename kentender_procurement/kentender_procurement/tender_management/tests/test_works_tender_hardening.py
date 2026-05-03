# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 5 §26 — consolidated Works tender-stage hardening scenarios (WH-014).

Executable cases named in the implementation pack; complements per-ticket
``test_works_tender_hardening_wh00x`` modules.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening
"""

from __future__ import annotations

import json
import uuid

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as procurement_tender_controller,
)
from kentender_procurement.tender_management.services import works_tender_hardening as wth
from kentender_procurement.tender_management.services import works_tender_hardening_validation as wtv
from kentender_procurement.tender_management.services.std_template_engine import (
	load_sample_config,
	load_template,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


def _insert_tender_with_sample_config(tender_reference: str) -> str:
	"""Insert a Works STD sample-backed tender; suffix avoids collision with other tests."""
	suffix = uuid.uuid4().hex[:10]
	doc = frappe.new_doc("Procurement Tender")
	doc.std_template = TEMPLATE_CODE
	doc.tender_title = f"WH-014 {tender_reference} {suffix}"
	doc.tender_reference = f"{tender_reference}-{suffix}"
	doc.configuration_json = json.dumps(
		load_sample_config(load_template(TEMPLATE_CODE)), sort_keys=True, default=str
	)
	doc.insert(ignore_permissions=True)
	return doc.name


class TestWorksTenderHardeningDoc5Section26(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_initialize_works_requirements_creates_required_components(self) -> None:
		name = _insert_tender_with_sample_config("WH014-REQ-001")
		try:
			wth.initialize_works_requirements(name)
			doc = frappe.get_doc("Procurement Tender", name)
			codes = {r.component_code for r in doc.works_requirements}
			for code in (
				"WRK_SCOPE",
				"WRK_SITE",
				"WRK_SPEC",
				"WRK_DRAWINGS",
				"WRK_ESHS",
				"WRK_PROGRAMME",
				"WRK_PERSONNEL",
				"WRK_EQUIPMENT",
				"WRK_COMPLETION",
				"WRK_DLP",
			):
				self.assertIn(code, codes, f"missing works requirement {code}")
			self.assertGreaterEqual(len(doc.works_requirements), 10)
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_section_attachments_are_section_bound(self) -> None:
		name = _insert_tender_with_sample_config("WH014-ATT-001")
		try:
			wth.initialize_section_attachments(name)
			doc = frappe.get_doc("Procurement Tender", name)
			self.assertEqual(len(doc.section_attachments), 3)
			for row in doc.section_attachments:
				self.assertTrue(str(row.section_code or "").strip())
				self.assertTrue(str(row.component_code or "").strip())
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_boq_hardening_populates_bill_item_fields(self) -> None:
		name = _insert_tender_with_sample_config("WH014-BOQ-001")
		try:
			wth.harden_works_boq_structure(name)
			doc = frappe.get_doc("Procurement Tender", name)
			self.assertGreater(len(doc.boq_items), 0)
			for row in doc.boq_items:
				if str(row.formula_type or "") not in ("Summary",):
					self.assertTrue(str(row.bill_code or "").strip(), row.item_code)
					self.assertTrue(str(row.item_number or "").strip(), row.item_code)
					self.assertTrue(str(row.formula_type or "").strip(), row.item_code)
					self.assertIn(row.quantity_locked, (1, True, "1"), row.item_code)
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_boq_summary_rows_not_supplier_editable(self) -> None:
		name = _insert_tender_with_sample_config("WH014-SUM-001")
		try:
			wth.run_works_tender_stage_hardening(name)
			doc = frappe.get_doc("Procurement Tender", name)
			for row in doc.boq_items:
				if str(row.item_category or "") == "GRAND_SUMMARY" or str(row.formula_type or "") == "Summary":
					row.supplier_rate_editable = 1
					break
			else:
				self.fail("expected a summary / GRAND_SUMMARY BoQ row")
			doc.save(ignore_permissions=True)
			out = wtv.validate_works_tender_stage(name)
			codes = {f.get("finding_code") for f in out.get("findings") or []}
			self.assertIn("WORKS-BOQ-009", codes)
			self.assertGreater(out.get("critical_count") or 0, 0)
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_provisional_sums_not_supplier_editable(self) -> None:
		name = _insert_tender_with_sample_config("WH014-PROV-001")
		try:
			wth.run_works_tender_stage_hardening(name)
			doc = frappe.get_doc("Procurement Tender", name)
			for row in doc.boq_items:
				if str(row.item_category or "") == "PROVISIONAL_SUMS":
					row.formula_type = "Provisional Sum"
					row.supplier_rate_editable = 1
					break
			else:
				self.fail("expected a PROVISIONAL_SUMS BoQ row")
			doc.save(ignore_permissions=True)
			out = wtv.validate_works_tender_stage(name)
			codes = {f.get("finding_code") for f in out.get("findings") or []}
			self.assertIn("WORKS-BOQ-008", codes)
			self.assertGreater(out.get("critical_count") or 0, 0)
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_dayworks_required_when_configured(self) -> None:
		name = _insert_tender_with_sample_config("WH014-DAY-001")
		try:
			wth.run_works_tender_stage_hardening(name)
			doc = frappe.get_doc("Procurement Tender", name)
			to_remove = [r for r in doc.boq_items if str(r.item_category or "") == "DAYWORKS"]
			self.assertTrue(to_remove, "sample should include DAYWORKS rows")
			for r in to_remove:
				doc.remove(r)
			doc.save(ignore_permissions=True)
			out = wtv.validate_works_tender_stage(name)
			codes = [f.get("finding_code") for f in out.get("findings") or []]
			self.assertIn("WORKS-BOQ-010", codes)
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_lot_boq_references_valid(self) -> None:
		name = _insert_tender_with_sample_config("WH014-LOT-001")
		try:
			wth.run_works_tender_stage_hardening(name)
			doc = frappe.get_doc("Procurement Tender", name)
			self.assertTrue(doc.lots, "sample should define lots for multi-lot config")
			for row in doc.boq_items:
				if str(row.item_category or "") == "GRAND_SUMMARY":
					continue
				if str(row.formula_type or "") == "Summary":
					continue
				row.lot_code = "ZZ-UNKNOWN-LOT"
				break
			else:
				self.fail("expected a priced BoQ row with lot_code to corrupt")
			doc.save(ignore_permissions=True)
			out = wtv.validate_works_tender_stage(name)
			codes = {f.get("finding_code") for f in out.get("findings") or []}
			self.assertIn("WORKS-LOT-004", codes)
			self.assertGreater(out.get("critical_count") or 0, 0)
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_required_forms_have_submission_component_placeholders(self) -> None:
		name = _insert_tender_with_sample_config("WH014-FORM-001")
		try:
			wth.run_works_tender_stage_hardening(name)
			doc = frappe.get_doc("Procurement Tender", name)
			self.assertGreater(len(doc.required_forms), 0)
			for row in doc.required_forms:
				if str(row.stage or "") != "Bid Submission":
					continue
				if not row.required:
					continue
				self.assertTrue(
					str(row.submission_component_code or "").strip(),
					f"missing submission_component_code for {row.form_code}",
				)
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_derived_model_placeholders_block_publication_not_preview(self) -> None:
		"""Placeholder rows carry ``blocking_for_publication``; §18 does not emit MODEL findings for Placeholder."""
		name = _insert_tender_with_sample_config("WH014-MODEL-001")
		try:
			wth.run_works_tender_stage_hardening(name)
			doc = frappe.get_doc("Procurement Tender", name)
			self.assertEqual(len(doc.derived_model_readiness), 4)
			for row in doc.derived_model_readiness:
				self.assertEqual(str(row.status or ""), "Placeholder")
				self.assertTrue(row.blocking_for_publication in (1, True, "1"))
			prev = procurement_tender_controller.generate_tender_pack_preview(name)
			self.assertTrue(prev.get("ok"), "STD preview must not be blocked by publication-only hardening posture")
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_snapshot_hash_generated(self) -> None:
		name = _insert_tender_with_sample_config("WH014-SNAP-001")
		try:
			out = wth.run_works_tender_stage_hardening(name)
			self.assertTrue(out.get("snapshot_hash"))
			h = frappe.db.get_value("Procurement Tender", name, "works_hardening_snapshot_hash")
			j = frappe.db.get_value("Procurement Tender", name, "works_hardening_snapshot_json")
			self.assertTrue(h)
			self.assertTrue((j or "").strip())
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_legacy_upload_as_source_not_enabled(self) -> None:
		name = _insert_tender_with_sample_config("WH014-LEG-001")
		try:
			wth.run_works_tender_stage_hardening(name)
			raw = frappe.db.get_value("Procurement Tender", name, "works_hardening_validation_json") or "{}"
			envelope = json.loads(raw)
			legacy = [
				f.get("finding_code")
				for f in envelope.get("findings") or []
				if str(f.get("finding_code") or "").startswith("WORKS-LEGACY")
			]
			self.assertEqual(legacy, [])
			self.assertTrue((envelope.get("summary") or {}).get("legacy_lockout_checked"))
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def test_full_hardening_run_primary_seed(self) -> None:
		"""Primary STD sample path: Pass or Warning, never Critical aggregate for configured sample."""
		name = _insert_tender_with_sample_config("WH014-FULL-001")
		try:
			out = wth.run_works_tender_stage_hardening(name)
			val = out.get("validation") or {}
			self.assertEqual(val.get("critical_count"), 0)
			self.assertIn(val.get("status"), (wth.HARDENING_STATUS_PASS, wth.HARDENING_STATUS_WARNING))
			self.assertNotIn(val.get("status"), (wth.HARDENING_STATUS_BLOCKED, wth.HARDENING_STATUS_FAILED))
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)
