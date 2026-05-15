# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-010 / LV-R1-010-01 — source module authority: PLC must not own or mutate source workflow state."""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.source_module_authority import (
	AUTHORITATIVE_SOURCE_DOCTYPES,
	handoff_fields_for_stale_mark,
	recommend_handoff_stale_for_source_fingerprint_drift,
)


class TestR1010StaleRecommendationPure(unittest.TestCase):
	"""Pure stale recommendation — no DB; mutates handoff fields only via returned dict."""

	def test_no_drift_returns_none(self):
		self.assertIsNone(
			recommend_handoff_stale_for_source_fingerprint_drift(
				handoff_status="Handed Off",
				snapshot_fingerprint="abc",
				live_fingerprint="abc",
			)
		)

	def test_drift_returns_reason(self):
		r = recommend_handoff_stale_for_source_fingerprint_drift(
			handoff_status="Consumed",
			snapshot_fingerprint="v1",
			live_fingerprint="v2",
		)
		self.assertIsInstance(r, str)
		self.assertIn("source_module", r)

	def test_missing_fingerprints_no_recommendation(self):
		self.assertIsNone(
			recommend_handoff_stale_for_source_fingerprint_drift(
				handoff_status="Ready",
				snapshot_fingerprint=None,
				live_fingerprint="x",
			)
		)

	def test_cancelled_not_eligible(self):
		self.assertIsNone(
			recommend_handoff_stale_for_source_fingerprint_drift(
				handoff_status="Cancelled",
				snapshot_fingerprint="a",
				live_fingerprint="b",
			)
		)

	def test_already_stale_no_recommendation(self):
		self.assertIsNone(
			recommend_handoff_stale_for_source_fingerprint_drift(
				handoff_status="Stale",
				snapshot_fingerprint="a",
				live_fingerprint="b",
			)
		)

	def test_handoff_only_stale_patch(self):
		p = handoff_fields_for_stale_mark(stale_reason="unit-test")
		self.assertEqual(p, {"status": "Stale", "stale_reason": "unit-test"})


def _plc_doctype_controller(name: str) -> Path:
	"""``kentender_procurement/kentender_procurement/doctype/<name>/<name>.py``."""
	base = Path(frappe.get_app_path("kentender_procurement")) / "kentender_procurement" / "doctype"
	return base / name / f"{name}.py"


class TestR1010ControllerStaticGuards(unittest.TestCase):
	"""PLC controllers must not call obvious source-mutation APIs on authoritative DocTypes."""

	def test_handoff_and_journey_files_avoid_db_writes_to_sources(self):
		patterns = []
		for dt in sorted(AUTHORITATIVE_SOURCE_DOCTYPES):
			patterns.append(
				re.compile(
					rf"frappe\.db\.set_(?:value|single_value)\(\s*[\"']{re.escape(dt)}[\"']",
					re.MULTILINE | re.IGNORECASE,
				)
			)
			patterns.append(
				re.compile(
					rf"frappe\.get_doc\(\s*[\"']{re.escape(dt)}[\"']\s*,",
					re.MULTILINE | re.IGNORECASE,
				)
			)
		for rel in ("procurement_handoff_card", "procurement_journey"):
			path = _plc_doctype_controller(rel)
			self.assertTrue(path.is_file(), msg=f"missing {path}")
			text = path.read_text(encoding="utf-8")
			for rx in patterns:
				self.assertIsNone(rx.search(text), msg=f"{path} must not match {rx.pattern}")


class TestR1010SaveDoesNotTouchSourceDocTypes(IntegrationTestCase):
	"""Property: saving PLC aggregates never runs ``Document.save`` on source owners."""

	_journey_code = "JRN-TEST-R1010-001"
	_handoff_code = "HOFF-TEST-R1010-001"

	def tearDown(self):
		frappe.db.delete("Procurement Handoff Card", {"handoff_code": self._handoff_code})
		frappe.db.delete("Procurement Journey", {"journey_code": self._journey_code})
		super().tearDown()

	def _insert_minimal_journey(self):
		frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": self._journey_code,
				"journey_title": "R1-010 authority test journey",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "tender_published",
				"current_stage_label": "Tender Published",
				"current_status_category": "Completed",
				"current_owner_module": "Tender Management",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
				"demand_ref": "DEM-FAKE-R1010",
			}
		).insert()

	def _minimal_handoff(self, status: str = "Ready"):
		return frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._handoff_code,
				"handoff_title": "R1-010 save property test",
				"journey_code": self._journey_code,
				"source_module": "Demand Intake",
				"target_module": "Procurement Planning",
				"source_object_type": "Demand",
				"source_object_code": "DEM-FAKE-R1010",
				"status": status,
				"generated_by": "Administrator",
				"locked_summary": {},
				"passed_forward_summary": {},
				"next_action": "n/a",
				"evidence_links_json": {
					"links": [
						{
							"label": "Demand",
							"object_type": "Demand",
							"object_code": "DEM-FAKE-R1010",
							"module": "Demand Intake",
							"route": "/desk/",
							"visibility": "Internal",
						}
					]
				},
				"is_master_seed": 0,
			}
		)

	def test_handoff_insert_and_update_never_saves_source_doctypes(self):
		self._insert_minimal_journey()
		saved: list[str] = []
		orig = Document.save

		def recording_save(self, *args, **kwargs):
			saved.append(self.doctype)
			return orig(self, *args, **kwargs)

		with patch.object(Document, "save", recording_save):
			doc = self._minimal_handoff()
			doc.insert()
			doc.status = "Handed Off"
			doc.save()

		for dt in AUTHORITATIVE_SOURCE_DOCTYPES:
			self.assertNotIn(dt, saved, msg=f"Document.save must not run for {dt}; got {saved!r}")

	def test_journey_insert_and_update_never_saves_source_doctypes(self):
		saved: list[str] = []
		orig = Document.save

		def recording_save(self, *args, **kwargs):
			saved.append(self.doctype)
			return orig(self, *args, **kwargs)

		with patch.object(Document, "save", recording_save):
			doc = frappe.get_doc(
				{
					"doctype": "Procurement Journey",
					"journey_code": self._journey_code,
					"journey_title": "R1-010 journey save test",
					"procuring_entity_code": "PE-TEST",
					"fiscal_year": "2026/2027",
					"current_stage_key": "tender_published",
					"current_stage_label": "Tender Published",
					"current_status_category": "Completed",
					"current_owner_module": "Tender Management",
					"blocker_count": 0,
					"critical_blocker_count": 0,
					"is_master_seed": 0,
					"demand_ref": "DEM-FAKE-R1010",
				}
			)
			doc.insert()
			doc.next_action = "updated aggregate text only"
			doc.save()

		for dt in AUTHORITATIVE_SOURCE_DOCTYPES:
			self.assertNotIn(dt, saved, msg=f"Document.save must not run for {dt}; got {saved!r}")
