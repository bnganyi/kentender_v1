# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-006 — Handoff evidence link contract (pack §6.4), storage decision, and size limits."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.evidence_links import (
	EVIDENCE_LINKS_MAX_LINKS,
	EVIDENCE_LINKS_MAX_SERIALIZED_BYTES,
	EVIDENCE_LINK_FIELD_MAX_CHARS,
	EVIDENCE_LINK_REQUIRED_KEYS,
	EVIDENCE_LINK_VISIBILITY_VALUES,
	evidence_links_serialized_byte_length,
	normalize_evidence_links_raw,
	parse_validate_and_normalize_evidence_links,
	validate_evidence_links_normalized,
)


def _valid_link(**overrides: str) -> dict[str, str]:
	base = {
		"label": "Publication Snapshot",
		"object_type": "Publication Snapshot",
		"object_code": "PUBSNAP-TST-001",
		"module": "Tender Management",
		"route": "/desk/",
		"visibility": "Internal",
	}
	base.update(overrides)
	return base


class TestR1006EvidenceLinksPure(unittest.TestCase):
	"""LV-R1-006-01 — normalize/validate without Frappe DB."""

	def test_normalize_bare_list(self):
		self.assertEqual(normalize_evidence_links_raw([]), {"links": []})

	def test_normalize_dict_with_links(self):
		self.assertEqual(
			normalize_evidence_links_raw({"links": [_valid_link()]}),
			{"links": [_valid_link()]},
		)

	def test_parse_validate_strips_strings(self):
		w = parse_validate_and_normalize_evidence_links({"links": [_valid_link(label="  x  ")]})
		self.assertEqual(w["links"][0]["label"], "x")

	def test_rejects_missing_required_key(self):
		link = _valid_link()
		del link["route"]
		with self.assertRaises(ValueError):
			parse_validate_and_normalize_evidence_links({"links": [link]})

	def test_rejects_bad_visibility(self):
		with self.assertRaises(ValueError):
			parse_validate_and_normalize_evidence_links(
				{"links": [_valid_link(visibility="Extranet")]}
			)

	def test_rejects_too_many_links(self):
		links = [_valid_link(object_code=f"CODE-{i:04d}") for i in range(EVIDENCE_LINKS_MAX_LINKS + 1)]
		with self.assertRaises(ValueError) as ctx:
			parse_validate_and_normalize_evidence_links({"links": links})
		self.assertIn("50", str(ctx.exception))

	def test_rejects_field_too_long(self):
		long_text = "x" * (EVIDENCE_LINK_FIELD_MAX_CHARS + 1)
		with self.assertRaises(ValueError):
			parse_validate_and_normalize_evidence_links({"links": [_valid_link(route=long_text)]})

	def test_rejects_oversized_payload(self):
		"""Build a valid structure whose canonical JSON exceeds ``EVIDENCE_LINKS_MAX_SERIALIZED_BYTES``."""
		link = _valid_link(
			label="y" * EVIDENCE_LINK_FIELD_MAX_CHARS,
			object_type="y" * EVIDENCE_LINK_FIELD_MAX_CHARS,
			object_code="y" * EVIDENCE_LINK_FIELD_MAX_CHARS,
			module="y" * EVIDENCE_LINK_FIELD_MAX_CHARS,
			route="y" * EVIDENCE_LINK_FIELD_MAX_CHARS,
			visibility="Internal",
		)
		# Seven max-width links exceed ~64KiB UTF-8 JSON (6 × 2048 chars per link + overhead).
		wrapper = {"links": [link, link, link, link, link, link, link]}
		byte_len = evidence_links_serialized_byte_length(wrapper)
		self.assertGreater(byte_len, EVIDENCE_LINKS_MAX_SERIALIZED_BYTES)
		with self.assertRaises(ValueError) as ctx:
			validate_evidence_links_normalized(wrapper)
		self.assertIn("bytes", str(ctx.exception))

	def test_visibility_enum_is_pack_internal_superset(self):
		self.assertIn("Internal", EVIDENCE_LINK_VISIBILITY_VALUES)
		self.assertTrue(set(EVIDENCE_LINK_REQUIRED_KEYS).issuperset({"label", "visibility"}))


class TestR1006EvidenceLinksOnHandoffCard(IntegrationTestCase):
	"""R1-006 — DocType ``validate`` delegates to ``evidence_links`` helpers."""

	_journey_code = "JRN-TEST-R1006-001"
	_handoff_code = "HOFF-TEST-R1006-001"

	def tearDown(self):
		frappe.db.delete("Procurement Handoff Card", {"handoff_code": self._handoff_code})
		frappe.db.delete("Procurement Journey", {"journey_code": self._journey_code})
		super().tearDown()

	def _insert_journey(self):
		frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": self._journey_code,
				"journey_title": "R1-006 parent",
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
		).insert()

	def _base_handoff_kwargs(self):
		return {
			"doctype": "Procurement Handoff Card",
			"handoff_code": self._handoff_code,
			"handoff_title": "R1-006 evidence test",
			"journey_code": self._journey_code,
			"source_module": "Planning",
			"target_module": "Tender Management",
			"source_object_type": "Procurement Package",
			"source_object_code": "PKG-TEST-001",
			"status": "Draft",
			"generated_by": "USER-TEST",
			"locked_summary": {},
			"passed_forward_summary": {},
			"next_action": "Review evidence",
			"is_master_seed": 0,
		}

	def test_insert_accepts_supplier_visibility(self):
		self._insert_journey()
		kw = self._base_handoff_kwargs()
		kw["evidence_links_json"] = {"links": [_valid_link(visibility="Supplier")]}
		frappe.get_doc(kw).insert()
		doc = frappe.get_doc("Procurement Handoff Card", self._handoff_code)
		evidence = doc.evidence_links_json
		if isinstance(evidence, str):
			evidence = frappe.parse_json(evidence)
		self.assertEqual(evidence["links"][0]["visibility"], "Supplier")

	def test_insert_rejects_missing_route(self):
		self._insert_journey()
		kw = self._base_handoff_kwargs()
		link = _valid_link()
		del link["route"]
		kw["evidence_links_json"] = {"links": [link]}
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(kw).insert()

	def test_insert_rejects_too_many_links(self):
		self._insert_journey()
		kw = self._base_handoff_kwargs()
		kw["evidence_links_json"] = {
			"links": [
				_valid_link(object_code=f"OBJ-{i:04d}", route=f"/desk/{i}")
				for i in range(EVIDENCE_LINKS_MAX_LINKS + 1)
			]
		}
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(kw).insert()
