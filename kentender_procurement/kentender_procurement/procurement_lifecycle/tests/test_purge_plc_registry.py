# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Purge PLC outside G0-008 registry — integration tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.seeds.purge_plc_outside_works_master_registry import (
	purge_procurement_lifecycle_plc_outside_works_master_registry,
)


def _minimal_evidence():
	return {
		"links": [
			{
				"label": "x",
				"object_type": "Demand",
				"object_code": "DEM-PURGE-TEST",
				"module": "Demands",
				"route": "/desk/",
				"visibility": "Internal",
			}
		]
	}


class TestPurgePlcOutsideWorksMasterRegistry(IntegrationTestCase):
	_DECOY_J = "JRN-PURGE-TEST-DECOY-001"
	_UNDOC_H = "HCO-PURGE-TEST-UNDOC-001"

	def tearDown(self):
		frappe.db.delete("Procurement Handoff Card", {"handoff_code": self._UNDOC_H})
		frappe.db.delete("Procurement Journey", {"journey_code": self._DECOY_J})
		super().tearDown()

	def _insert_decoy_plc(self):
		frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": self._DECOY_J,
				"journey_title": "Purge test decoy",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "tender_published",
				"current_stage_label": "Tender Published",
				"current_status_category": "In Progress",
				"current_owner_module": "Planning",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._UNDOC_H,
				"handoff_title": "Undocumented handoff",
				"journey_code": self._DECOY_J,
				"source_module": "Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": "PKG-PURGE",
				"status": "Draft",
				"generated_by": "USER-PURGE-TEST",
				"locked_summary": {},
				"passed_forward_summary": {},
				"next_action": "n/a",
				"evidence_links_json": _minimal_evidence(),
				"technical_refs_json": {},
				"is_master_seed": 0,
			}
		).insert(ignore_permissions=True)

	def test_dry_run_lists_decoys_without_deleting(self):
		self._insert_decoy_plc()
		out = purge_procurement_lifecycle_plc_outside_works_master_registry(dry_run=True)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("dry_run"))
		self.assertIn(self._DECOY_J, out["would_delete_journeys"])
		self.assertIn(self._UNDOC_H, out["would_delete_handoff_cards"])
		self.assertTrue(frappe.db.exists("Procurement Journey", self._DECOY_J))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", self._UNDOC_H))

	def test_purge_removes_decoy_journey_and_undocumented_handoff(self):
		self._insert_decoy_plc()
		out = purge_procurement_lifecycle_plc_outside_works_master_registry(dry_run=False)
		self.assertTrue(out.get("ok"))
		self.assertIn(self._DECOY_J, out["deleted_journeys"])
		self.assertIn(self._UNDOC_H, out["deleted_handoff_cards"])
		self.assertFalse(frappe.db.exists("Procurement Journey", self._DECOY_J))
		self.assertFalse(frappe.db.exists("Procurement Handoff Card", self._UNDOC_H))

	def test_purge_runs_without_error_when_registry_journey_absent(self):
		out = purge_procurement_lifecycle_plc_outside_works_master_registry(dry_run=False)
		self.assertTrue(out.get("ok"))
