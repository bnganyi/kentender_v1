# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-003 — Procurement Journey DocType schema, permissions sketch, and non-authoritative validation."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.constants import JOURNEY_STEP_KEYS_IN_ORDER
from kentender_procurement.procurement_lifecycle.journey_status_category import JOURNEY_STATUS_CATEGORY_VALUES


class TestR1003ProcurementJourneyMeta(IntegrationTestCase):
	"""LV-R1-003-01 — DocType exists, mandatory contract, not submittable."""

	def test_doctype_registered(self):
		self.assertTrue(frappe.db.exists("DocType", "Procurement Journey"))

	def test_not_submittable(self):
		meta = frappe.get_meta("Procurement Journey")
		self.assertEqual(int(meta.is_submittable or 0), 0)

	def test_autoname_is_journey_code_field(self):
		meta = frappe.get_meta("Procurement Journey")
		self.assertEqual(meta.autoname, "field:journey_code")

	def test_required_fields_exist(self):
		meta = frappe.get_meta("Procurement Journey")
		names = {df.fieldname for df in meta.fields}
		for fn in (
			"journey_code",
			"journey_title",
			"procuring_entity_code",
			"fiscal_year",
			"current_stage_key",
			"current_stage_label",
			"current_status_category",
			"current_owner_module",
			"blocker_count",
			"critical_blocker_count",
			"is_master_seed",
		):
			with self.subTest(field=fn):
				self.assertIn(fn, names)

	def test_guest_has_no_read(self):
		meta = frappe.get_meta("Procurement Journey")
		roles_with_read = {p.role for p in (meta.permissions or []) if p.get("read")}
		self.assertNotIn("Guest", roles_with_read)


class TestR1003ProcurementJourneyLifecycle(IntegrationTestCase):
	"""Insert/delete smoke + LV-R1-003-03 validation."""

	def tearDown(self):
		frappe.db.delete("Procurement Journey", {"journey_code": "JRN-TEST-R1003-001"})
		super().tearDown()

	def test_insert_minimal_journey(self):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": "JRN-TEST-R1003-001",
				"journey_title": "R1-003 schema test journey",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "tender_published",
				"current_stage_label": "Tender Published",
				"current_status_category": "Completed",
				"current_owner_module": "Tender Management",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
			}
		)
		doc.insert()
		self.assertEqual(doc.name, "JRN-TEST-R1003-001")
		reloaded = frappe.get_doc("Procurement Journey", "JRN-TEST-R1003-001")
		self.assertEqual(reloaded.journey_title, "R1-003 schema test journey")

	def test_validate_rejects_unknown_status_category(self):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": "JRN-TEST-R1003-001",
				"journey_title": "Invalid status",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "tender_published",
				"current_stage_label": "Tender Published",
				"current_status_category": "NotARealCategory",
				"current_owner_module": "Tender Management",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_validate_rejects_unknown_stage_key(self):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": "JRN-TEST-R1003-001",
				"journey_title": "Invalid stage",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "phantom_stage",
				"current_stage_label": "Phantom",
				"current_status_category": "Not Started",
				"current_owner_module": "Tender Management",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_validate_rejects_negative_blockers(self):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": "JRN-TEST-R1003-001",
				"journey_title": "Bad blockers",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "tender_published",
				"current_stage_label": "Tender Published",
				"current_status_category": "Completed",
				"current_owner_module": "Tender Management",
				"blocker_count": -1,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()


class TestR1003ContractWithR1001R1002(unittest.TestCase):
	"""Cross-ticket vocabulary alignment (no DB)."""

	def test_stage_keys_subset_of_journey_step_config(self):
		# current_stage_key must be drawable from R1-002 spine keys
		for key in ("tender_published", "strategy", "contract_handoff"):
			self.assertIn(key, JOURNEY_STEP_KEYS_IN_ORDER)

	def test_status_categories_align_with_r1_001(self):
		self.assertIn("Completed", JOURNEY_STATUS_CATEGORY_VALUES)
		self.assertIn("Not Started", JOURNEY_STATUS_CATEGORY_VALUES)
