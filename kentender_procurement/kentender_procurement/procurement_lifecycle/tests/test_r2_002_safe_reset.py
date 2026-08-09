# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-002 / LV-R2-002-01 — Safe reset: only master-flagged WORKS PLC rows in §4/§16 code lists are removed.

Seed spec §19.4 and SEED-TEST-006: non-master and off-allowlist PLC records must survive ``reset=True``.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
	load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
	BASE_HANDOFF_CODES,
	JOURNEY_CODE,
	OPENING_HANDOFF_CODES,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_loader import _reset_master_plc_rows


def _minimal_evidence_links() -> dict:
	return {
		"links": [
			{
				"label": "Test evidence",
				"object_type": "Demand",
				"object_code": "DEM-R2002-TEST",
				"module": "Demands",
				"route": "/desk/",
				"visibility": "Internal",
			}
		]
	}


class TestR2002SafeResetIntegration(IntegrationTestCase):
	"""LV-R2-002-01 — reset scope is allowlisted codes × ``is_master_seed``; decoys survive."""

	_DECOY_JOURNEY = "JRN-R2002-DECOY-001"
	_DECOY_HANDOFF = "HCO-R2002-DECOY-001"
	_OTHER_MASTER_HANDOFF = "HCO-R2002-NONWORKS-MASTER-001"

	def tearDown(self):
		frappe.db.delete("Procurement Handoff Card", {"handoff_code": self._DECOY_HANDOFF})
		frappe.db.delete("Procurement Handoff Card", {"handoff_code": self._OTHER_MASTER_HANDOFF})
		frappe.db.delete("Procurement Journey", {"journey_code": self._DECOY_JOURNEY})
		load_procurement_lifecycle_works_master(reset=True, checkpoint="OPENING_READY")
		super().tearDown()

	def _insert_decoy_plc(self):
		"""Non-WORKS PLC rows (different business codes, ``is_master_seed=0``)."""
		j = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": self._DECOY_JOURNEY,
				"journey_title": "R2-002 decoy journey (non-WORKS)",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "tender_published",
				"current_stage_label": "Tender Published",
				"current_status_category": "In Progress",
				"current_owner_module": "Procurement Planning",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
			}
		)
		j.insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._DECOY_HANDOFF,
				"handoff_title": "R2-002 decoy handoff",
				"journey_code": self._DECOY_JOURNEY,
				"source_module": "Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": "PKG-R2002-DECOY",
				"status": "Draft",
				"generated_by": "USER-R2002-TEST",
				"locked_summary": {},
				"passed_forward_summary": {},
				"next_action": "n/a",
				"evidence_links_json": _minimal_evidence_links(),
				"technical_refs_json": {},
				"is_master_seed": 0,
			}
		).insert(ignore_permissions=True)
		# Not a WORKS §16 code, but ``is_master_seed=1`` — reset must not blanket-delete by flag alone.
		frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": self._OTHER_MASTER_HANDOFF,
				"handoff_title": "Non-WORKS handoff flagged master",
				"journey_code": self._DECOY_JOURNEY,
				"source_module": "Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": "PKG-R2002-OTHER",
				"status": "Draft",
				"generated_by": "USER-R2002-TEST",
				"locked_summary": {},
				"passed_forward_summary": {},
				"next_action": "n/a",
				"evidence_links_json": _minimal_evidence_links(),
				"technical_refs_json": {},
				"is_master_seed": 1,
			}
		).insert(ignore_permissions=True)

	def test_load_with_reset_leaves_unrelated_journey_and_handoffs_intact(self):
		self._insert_decoy_plc()
		out = load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")
		self.assertTrue(out.get("ok"), msg=out)
		self.assertTrue(frappe.db.exists("Procurement Journey", self._DECOY_JOURNEY))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", self._DECOY_HANDOFF))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", self._OTHER_MASTER_HANDOFF))
		self.assertTrue(frappe.db.exists("Procurement Journey", JOURNEY_CODE))

	def test_reset_master_plc_rows_removes_only_works_master_artifacts(self):
		load_procurement_lifecycle_works_master(reset=True, checkpoint="OPENING_READY")
		self._insert_decoy_plc()
		self.assertTrue(frappe.db.exists("Procurement Journey", JOURNEY_CODE))
		for hc in BASE_HANDOFF_CODES:
			self.assertTrue(frappe.db.exists("Procurement Handoff Card", hc))
		for hc in OPENING_HANDOFF_CODES:
			self.assertTrue(frappe.db.exists("Procurement Handoff Card", hc))

		_reset_master_plc_rows(include_opening_handoffs=True)

		self.assertFalse(frappe.db.exists("Procurement Journey", JOURNEY_CODE))
		for hc in BASE_HANDOFF_CODES:
			self.assertFalse(frappe.db.exists("Procurement Handoff Card", hc))
		for hc in OPENING_HANDOFF_CODES:
			self.assertFalse(frappe.db.exists("Procurement Handoff Card", hc))

		self.assertTrue(frappe.db.exists("Procurement Journey", self._DECOY_JOURNEY))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", self._DECOY_HANDOFF))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", self._OTHER_MASTER_HANDOFF))

	def test_reset_does_not_delete_allowlisted_handoff_when_not_master_seed(self):
		"""§19.4 — ``is_master_seed`` gate: same business code as master but user row must not be wiped."""
		load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")
		spec_code = BASE_HANDOFF_CODES[0]
		doc = frappe.get_doc("Procurement Handoff Card", spec_code)
		doc.is_master_seed = 0
		doc.save(ignore_permissions=True)
		self.assertEqual(cint(frappe.db.get_value("Procurement Handoff Card", spec_code, "is_master_seed")), 0)

		_reset_master_plc_rows(include_opening_handoffs=True)

		self.assertTrue(frappe.db.exists("Procurement Handoff Card", spec_code))
		self.assertEqual(cint(frappe.db.get_value("Procurement Handoff Card", spec_code, "is_master_seed")), 0)
