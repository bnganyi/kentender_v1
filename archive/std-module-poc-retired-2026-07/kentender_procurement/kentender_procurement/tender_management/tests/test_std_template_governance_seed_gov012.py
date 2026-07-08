# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-012 — WORKS POC STD Template governance seed (doc 7 §21).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_seed_gov012
"""

from __future__ import annotations

import json

import frappe
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	SEED_MARKER,
	SEED_RUN_ID,
	SOURCE_AUTHORITY,
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE


def _new_gov012_std_template(template_code: str) -> Document:
	doc = frappe.new_doc("STD Template")
	doc.template_code = template_code
	doc.template_name = f"STD-GOV-012 {template_code}"
	doc.template_short_name = template_code[:12]
	doc.authority = "Test Authority"
	doc.country = "KE"
	doc.procurement_category = "WORKS"
	doc.template_family = "Works"
	doc.version_label = "1.0"
	doc.template_version = "POC-V1"
	doc.package_version = "1"
	doc.source_authority = "Test Authority"
	doc.package_json = "{}"
	doc.package_hash = "a" * 64
	doc.package_hash_algorithm = gov.HASH_ALGORITHM
	doc.canonicalization_version = gov.CANONICALIZATION_VERSION
	doc.lifecycle_status = gov.STATUS_IMPORTED
	doc.latest_validation_status = gov.VALIDATION_NOT_RUN
	doc.critical_finding_count = 0
	doc.warning_finding_count = 0
	doc.info_finding_count = 0
	doc.validation_is_current = 0
	doc.is_governed_version = 1
	doc.tender_usage_count = 0
	doc.locked_due_to_usage = 0
	doc.mutation_blocked = 0
	doc.delete_blocked = 1
	doc.payload_locked = 0
	doc.is_suspended = 0
	doc.is_historical = 0
	doc.approval_override_used = 0
	doc.is_default_active_version = 0
	doc.allowed_for_import = 1
	doc.allowed_for_tender_creation = 0
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc


class TestStdTemplateGovernanceSeedGov012(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._template_code = f"GOV012-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov012_std_template(self._template_code)

	def tearDown(self) -> None:
		if frappe.db.exists("STD Template", self._template_code):
			frappe.delete_doc("STD Template", self._template_code, force=True, ignore_permissions=True)
			frappe.db.commit()
		frappe.set_user("Administrator")

	def test_gov012_approved_idempotent(self) -> None:
		r1 = seed_std_template_governance_for_existing_works_poc(
			self._template_code, force_mode="approved"
		)
		self.assertTrue(r1.get("ok"))
		self.assertEqual(r1.get("action"), "seeded")

		r2 = seed_std_template_governance_for_existing_works_poc(
			self._template_code, force_mode="approved"
		)
		self.assertTrue(r2.get("ok"))
		self.assertEqual(r2.get("action"), "noop")

		d = frappe.get_doc("STD Template", self._template_code)
		self.assertEqual(d.lifecycle_status, gov.STATUS_APPROVED)
		self.assertEqual(int(d.allowed_for_tender_creation or 0), 0)
		self.assertEqual(int(d.is_default_active_version or 0), 0)
		self.assertEqual(d.source_authority, SOURCE_AUTHORITY)
		self.assertEqual(d.source_document_code, self._template_code)
		self.assertEqual(d.latest_validation_package_hash, d.package_hash)
		self.assertEqual(d.approval_package_hash, d.package_hash)
		rows = d.get("lifecycle_events") or []
		self.assertEqual(len(rows), 3)
		codes = [r.event_code for r in rows]
		self.assertIn(gov.EVT_IMPORTED, codes)
		self.assertIn(gov.EVT_VALIDATION_COMPLETED, codes)
		self.assertIn(gov.EVT_APPROVED, codes)
		self.assertNotIn(gov.EVT_ACTIVATED, codes)

	def test_gov012_active_then_noop(self) -> None:
		r1 = seed_std_template_governance_for_existing_works_poc(
			self._template_code, force_mode="active"
		)
		self.assertTrue(r1.get("ok"))
		self.assertEqual(r1.get("action"), "seeded")

		r2 = seed_std_template_governance_for_existing_works_poc(
			self._template_code, force_mode="active"
		)
		self.assertTrue(r2.get("ok"))
		self.assertEqual(r2.get("action"), "noop")

		d = frappe.get_doc("STD Template", self._template_code)
		self.assertEqual(d.lifecycle_status, gov.STATUS_ACTIVE)
		self.assertEqual(int(d.allowed_for_tender_creation or 0), 1)
		self.assertEqual(int(d.payload_locked or 0), 1)
		self.assertEqual(d.activation_package_hash, d.package_hash)
		self.assertEqual(d.latest_validation_run_id, SEED_RUN_ID)
		rows = d.get("lifecycle_events") or []
		self.assertEqual(len(rows), 4)
		self.assertEqual(rows[-1].event_code, gov.EVT_ACTIVATED)

	def test_gov012_approved_to_active_upgrade(self) -> None:
		seed_std_template_governance_for_existing_works_poc(
			self._template_code, force_mode="approved"
		)
		r_up = seed_std_template_governance_for_existing_works_poc(
			self._template_code, force_mode="active"
		)
		self.assertTrue(r_up.get("ok"))
		self.assertEqual(r_up.get("action"), "upgrade")

		d = frappe.get_doc("STD Template", self._template_code)
		self.assertEqual(d.lifecycle_status, gov.STATUS_ACTIVE)
		self.assertEqual(int(d.allowed_for_tender_creation or 0), 1)
		rows = d.get("lifecycle_events") or []
		self.assertEqual(len(rows), 4)
		self.assertEqual(rows[-1].event_code, gov.EVT_ACTIVATED)

	def test_gov012_missing_std_template(self) -> None:
		missing = f"GOV012-MISSING-{frappe.generate_hash(length=8)}"
		out = seed_std_template_governance_for_existing_works_poc(missing)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error"), "missing_std_template")

	def test_gov012_poc_template_code_constant(self) -> None:
		self.assertEqual(TEMPLATE_CODE, "KE-PPRA-WORKS-BLDG-2022-04-POC")

	def test_gov012_payload_marker_json(self) -> None:
		seed_std_template_governance_for_existing_works_poc(
			self._template_code, force_mode="approved"
		)
		d = frappe.get_doc("STD Template", self._template_code)
		row = (d.get("lifecycle_events") or [])[0]
		data = json.loads(row.payload_json or "{}")
		self.assertEqual(data.get("seed"), SEED_MARKER)
		self.assertEqual(data.get("mode"), "approved")
