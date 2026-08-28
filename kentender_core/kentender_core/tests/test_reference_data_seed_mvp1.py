"""CFG-CHG-002 Phase 5 — §16 seed contract idempotency. Covers AC-021.

Deliberately exercises the real seed function against whatever KENTENDER_MVP_V1
state already exists on this site (this seed is inherently a specific,
site-scoped fixture like every other module's own seed — not something to
fake in isolated per-test fixtures), asserting exact record counts before and
after a second run.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1.reference_data import upsert_reference_data_mvp1


class TestReferenceDataSeedMvp1(IntegrationTestCase):
	def _counts(self) -> dict:
		return {
			"pe_nssf": frappe.db.count("Procuring Entity", {"name": "PE-NSSF"}),
			"pe_nssf_versions": frappe.db.count("Procuring Entity Version", {"procuring_entity": "PE-NSSF"}),
			"fy_2027_2028": frappe.db.count("Financial Year", {"name": "FY-2027-2028"}),
			"contexts": frappe.db.count(
				"PE Fiscal Year Context",
				{"name": ["in", ["CTX-MOH-2027-2028", "CTX-NSSF-2027-2028", "CTX-CGKIS-2027-2028"]]},
			),
			"pe_moh_history": frappe.db.count(
				"Audit Event",
				{
					"document_type": "Procuring Entity",
					"document_name": "PE-MOH",
					"action": ["in", ["reference_data.pe.create_draft", "reference_data.pe.activate"]],
				},
			),
			"ctx_moh_history": frappe.db.count("Audit Event", {"document_name": "CTX-MOH-2027-2028"}),
		}

	def test_seed_runs_twice_no_duplicates(self):
		upsert_reference_data_mvp1()
		before = self._counts()
		self.assertEqual(before["pe_nssf"], 1)
		self.assertEqual(before["fy_2027_2028"], 1)
		self.assertEqual(before["contexts"], 3)
		self.assertEqual(before["pe_moh_history"], 2)  # exactly submit + approve_activate

		upsert_reference_data_mvp1()
		after = self._counts()
		self.assertEqual(before, after)

	def test_seeded_data_matches_spec_values(self):
		upsert_reference_data_mvp1()

		for pe, entity_type_code in (("PE-MOH", "NATIONAL_MINISTRY"), ("PE-NSSF", "STATE_CORPORATION"), ("PE-CGKIS", "COUNTY_GOVERNMENT")):
			doc = frappe.get_doc("Procuring Entity", pe)
			self.assertEqual(doc.status, "Active")
			version = frappe.get_doc("Procuring Entity Version", doc.current_version_id)
			self.assertEqual(version.pe_type_code, entity_type_code)
			self.assertEqual(version.timezone, "Africa/Nairobi")

		fy = frappe.get_doc("Financial Year", "FY-2027-2028")
		self.assertEqual(fy.record_status, "Available")
		self.assertEqual(str(fy.start_date), "2027-07-01")
		self.assertEqual(str(fy.end_date), "2028-06-30")

		for ctx_name in ("CTX-MOH-2027-2028", "CTX-NSSF-2027-2028", "CTX-CGKIS-2027-2028"):
			ctx = frappe.get_doc("PE Fiscal Year Context", ctx_name)
			self.assertEqual(ctx.context_status, "Active")
			self.assertEqual(str(ctx.active_from), "2027-01-01 00:00:00")
			self.assertEqual(str(ctx.active_to), "2028-09-30 23:59:00")

	def test_reference_data_manager_granted_only_to_lydia(self):
		"""CFG-CHG-002 v0.4 / AUTH-ADR-001 v1.1 §12.4 — one global Reference
		Data Manager Role, granted only to the confirmed positive fixture
		(Lydia Mwangi). The retired five-role model's other fixture actors
		(Daniel Kariuki, Mercy Kilonzo, Samuel Otieno, Amina Hassan) receive no
		Reference Data authority — Amina specifically must not be granted it
		merely because she is a real, active user of the system elsewhere."""
		upsert_reference_data_mvp1()
		self.assertIn("Reference Data Manager", frappe.get_roles("lydia.mwangi@kentender.example.test"))
		for email in (
			"daniel.kariuki@kentender.example.test",
			"mercy.kilonzo@moh.example.test",
			"samuel.otieno@moh.example.test",
			"amina.hassan@moh.example.test",
		):
			if frappe.db.exists("User", email):
				self.assertNotIn("Reference Data Manager", frappe.get_roles(email))
