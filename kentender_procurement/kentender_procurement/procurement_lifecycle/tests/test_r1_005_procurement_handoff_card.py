# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-005 — Procurement Handoff Card DocType schema, permissions, and non-authoritative validation."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.handoff_card_status import HANDOFF_CARD_STATUS_VALUES


class TestR1005HandoffCardStatusVocabulary(unittest.TestCase):
	"""LV-R1-005-02 — Python vocabulary matches pack §6.3 (10 values, incl. Stale / Audit Only)."""

	def test_exactly_ten_statuses(self):
		self.assertEqual(len(HANDOFF_CARD_STATUS_VALUES), 10)

	def test_pack_anchor_values(self):
		for label in (
			"Draft",
			"Stale",
			"Audit Only",
			"Handed Off",
			"Superseded",
		):
			with self.subTest(status=label):
				self.assertIn(label, HANDOFF_CARD_STATUS_VALUES)


class TestR1005ProcurementHandoffCardMeta(IntegrationTestCase):
	"""LV-R1-005-01 — DocType exists, naming, indexes, not submittable."""

	def test_doctype_registered(self):
		self.assertTrue(frappe.db.exists("DocType", "Procurement Handoff Card"))

	def test_not_submittable(self):
		meta = frappe.get_meta("Procurement Handoff Card")
		self.assertEqual(int(meta.is_submittable or 0), 0)

	def test_autoname_is_handoff_code_field(self):
		meta = frappe.get_meta("Procurement Handoff Card")
		self.assertEqual(meta.autoname, "field:handoff_code")

	def test_handoff_code_and_journey_code_indexed(self):
		meta = frappe.get_meta("Procurement Handoff Card")
		by_name = {df.fieldname: df for df in meta.fields}
		self.assertEqual(int(by_name["handoff_code"].search_index or 0), 1)
		self.assertEqual(int(by_name["journey_code"].search_index or 0), 1)

	def test_required_fields_exist(self):
		meta = frappe.get_meta("Procurement Handoff Card")
		names = {df.fieldname for df in meta.fields}
		for fn in (
			"handoff_code",
			"handoff_title",
			"journey_code",
			"source_module",
			"target_module",
			"source_object_type",
			"source_object_code",
			"status",
			"generated_by",
			"locked_summary",
			"passed_forward_summary",
			"next_action",
			"evidence_links_json",
			"section_technical_refs",
			"technical_refs_json",
			"is_master_seed",
		):
			with self.subTest(field=fn):
				self.assertIn(fn, names)

	def test_guest_has_no_read(self):
		meta = frappe.get_meta("Procurement Handoff Card")
		roles_with_read = {p.role for p in (meta.permissions or []) if p.get("read")}
		self.assertNotIn("Guest", roles_with_read)

	def test_status_select_matches_python_vocabulary(self):
		meta = frappe.get_meta("Procurement Handoff Card")
		status_df = next(df for df in meta.fields if df.fieldname == "status")
		options = {o.strip() for o in (status_df.options or "").split("\n") if o.strip()}
		self.assertSetEqual(options, set(HANDOFF_CARD_STATUS_VALUES))


class TestR1005ProcurementHandoffCardLifecycle(IntegrationTestCase):
	"""Insert smoke + validation (journey dependency + JSON shapes)."""

	_journey_code = "JRN-TEST-R1005-001"
	_handoff_code = "HOFF-TEST-R1005-001"

	def tearDown(self):
		frappe.db.delete("Procurement Handoff Card", {"handoff_code": self._handoff_code})
		frappe.db.delete("Procurement Journey", {"journey_code": self._journey_code})
		super().tearDown()

	def _insert_minimal_journey(self):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": self._journey_code,
				"journey_title": "R1-005 handoff parent journey",
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
		return doc

	def _minimal_evidence_links(self):
		return {
			"links": [
				{
					"label": "Publication Snapshot",
					"object_type": "Publication Snapshot",
					"object_code": "PUBSNAP-TST-001",
					"module": "Tender Management",
					"route": "/desk/",
					"visibility": "Internal",
				}
			]
		}

	def test_evidence_bare_list_normalized_to_links_wrapper(self):
		"""Service callers may pass a §6.4-style bare array; we persist object-shaped JSON."""
		self._insert_minimal_journey()
		inner = self._minimal_evidence_links()["links"]
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._handoff_code,
				"handoff_title": "List wrapper normalization",
				"journey_code": self._journey_code,
				"source_module": "Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": "PKG-TEST-001",
				"status": "Draft",
				"generated_by": "USER-TEST-001",
				"locked_summary": {},
				"passed_forward_summary": {},
				"next_action": "n/a",
				"evidence_links_json": inner,
				"is_master_seed": 0,
			}
		)
		doc.insert()
		reloaded = frappe.get_doc("Procurement Handoff Card", self._handoff_code)
		evidence = reloaded.evidence_links_json
		if isinstance(evidence, str):
			evidence = frappe.parse_json(evidence)
		self.assertIsInstance(evidence, dict)
		self.assertEqual(evidence.get("links"), inner)

	def test_insert_minimal_handoff_card(self):
		self._insert_minimal_journey()
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._handoff_code,
				"handoff_title": "R1-005 schema test handoff",
				"journey_code": self._journey_code,
				"source_module": "Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": "PKG-TEST-001",
				"status": "Ready",
				"generated_by": "USER-TEST-001",
				"locked_summary": {"locked": True},
				"passed_forward_summary": {"items": []},
				"next_action": "Open tender workspace",
				"evidence_links_json": self._minimal_evidence_links(),
				"is_master_seed": 0,
			}
		)
		doc.insert()
		self.assertEqual(doc.name, self._handoff_code)
		reloaded = frappe.get_doc("Procurement Handoff Card", self._handoff_code)
		self.assertEqual(reloaded.handoff_title, "R1-005 schema test handoff")
		self.assertIsNotNone(reloaded.generated_at)

	def test_validate_rejects_unknown_status(self):
		self._insert_minimal_journey()
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._handoff_code,
				"handoff_title": "Bad status",
				"journey_code": self._journey_code,
				"source_module": "Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": "PKG-TEST-001",
				"status": "NotARealHandoffStatus",
				"generated_by": "USER-TEST-001",
				"locked_summary": {},
				"passed_forward_summary": {},
				"next_action": "n/a",
				"evidence_links_json": self._minimal_evidence_links(),
				"is_master_seed": 0,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_validate_rejects_evidence_not_array(self):
		self._insert_minimal_journey()
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._handoff_code,
				"handoff_title": "Bad evidence shape",
				"journey_code": self._journey_code,
				"source_module": "Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": "PKG-TEST-001",
				"status": "Draft",
				"generated_by": "USER-TEST-001",
				"locked_summary": {},
				"passed_forward_summary": {},
				"next_action": "n/a",
				"evidence_links_json": {"links": {"not": "an array"}},
				"is_master_seed": 0,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_validate_rejects_locked_summary_not_object(self):
		self._insert_minimal_journey()
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._handoff_code,
				"handoff_title": "Bad locked summary",
				"journey_code": self._journey_code,
				"source_module": "Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": "PKG-TEST-001",
				"status": "Draft",
				"generated_by": "USER-TEST-001",
				"locked_summary": [],
				"passed_forward_summary": {},
				"next_action": "n/a",
				"evidence_links_json": self._minimal_evidence_links(),
				"is_master_seed": 0,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_link_requires_existing_journey(self):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._handoff_code,
				"handoff_title": "Missing journey",
				"journey_code": "JRN-NONEXISTENT-999",
				"source_module": "Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": "PKG-TEST-001",
				"status": "Draft",
				"generated_by": "USER-TEST-001",
				"locked_summary": {},
				"passed_forward_summary": {},
				"next_action": "n/a",
				"evidence_links_json": self._minimal_evidence_links(),
				"is_master_seed": 0,
			}
		)
		with self.assertRaises(frappe.LinkValidationError):
			doc.insert()
