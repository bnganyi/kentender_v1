# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-006 — governance validation service (doc 7 §13.2, §14.3, §15).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_validation_gov006
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_validation import (
	clear_std_template_validation_findings,
	run_std_template_validation,
	validate_std_template_package_payload,
	write_std_template_validation_findings,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	compute_package_hash,
	get_template_package_path,
	load_template_package,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005 import (
	_new_gov005_std_template,
)


class TestStdTemplateGovernanceValidationGov006(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._template_code = f"GOV006-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov005_std_template(self._template_code)

	def tearDown(self) -> None:
		if frappe.db.exists("STD Template", self._template_code):
			frappe.delete_doc("STD Template", self._template_code, force=True, ignore_permissions=True)
			frappe.db.commit()
		frappe.set_user("Administrator")

	def test_std_gov_006_validate_invalid_json_string(self) -> None:
		out = validate_std_template_package_payload("{not json")
		self.assertFalse(out["ok"])
		self.assertEqual(out["status"], gov.VALIDATION_FAILED)
		self.assertGreaterEqual(out["critical_count"], 1)
		self.assertTrue(any(f.get("finding_code") == "STD-PKG-012" for f in out["findings"]))

	def test_std_gov_006_validate_empty_object(self) -> None:
		out = validate_std_template_package_payload({})
		self.assertFalse(out["ok"])
		self.assertIn(out["status"], (gov.VALIDATION_FAILED, gov.VALIDATION_BLOCKED))

	def test_std_gov_006_validate_works_poc_package_ok(self) -> None:
		pkg = dict(load_template_package())
		pkg["package_hash"] = compute_package_hash(get_template_package_path())
		out = validate_std_template_package_payload(pkg)
		self.assertTrue(out["ok"], msg=out.get("findings"))
		self.assertIn(
			out["status"],
			(gov.VALIDATION_PASS, gov.VALIDATION_PASS_WARNINGS),
		)
		self.assertTrue(out["run_id"].startswith("STD-VAL-"))

	def test_std_gov_006_run_updates_lifecycle_and_findings(self) -> None:
		frappe.db.set_value("STD Template", self._template_code, "package_json", "{}")
		frappe.db.commit()
		out = run_std_template_validation(self._template_code)
		self.assertFalse(out["ok"])
		self.assertEqual(out["lifecycle_status"], gov.STATUS_VALIDATION_FAILED)
		reloaded = frappe.get_doc("STD Template", self._template_code)
		self.assertEqual(reloaded.lifecycle_status, gov.STATUS_VALIDATION_FAILED)
		self.assertGreater(len(reloaded.validation_findings or []), 0)
		self.assertEqual(reloaded.latest_validation_run_id, out["run_id"])
		self.assertEqual(reloaded.validation_is_current, 1)
		events = reloaded.lifecycle_events or []
		codes = [e.event_code for e in events]
		self.assertIn(gov.EVT_VALIDATION_STARTED, codes)
		self.assertIn(gov.EVT_VALIDATION_COMPLETED, codes)

	def test_std_gov_006_run_malformed_package_json(self) -> None:
		frappe.db.set_value("STD Template", self._template_code, "package_json", "{broken")
		frappe.db.commit()
		out = run_std_template_validation(self._template_code)
		self.assertFalse(out["ok"])
		reloaded = frappe.get_doc("STD Template", self._template_code)
		self.assertEqual(reloaded.lifecycle_status, gov.STATUS_VALIDATION_FAILED)
		self.assertEqual(len(reloaded.validation_findings or []), 1)
		self.assertEqual(reloaded.validation_findings[0].finding_code, "STD-PKG-012")

	def test_std_gov_006_run_guest_forbidden(self) -> None:
		frappe.db.set_value("STD Template", self._template_code, "package_json", "{}")
		frappe.db.commit()
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			run_std_template_validation(self._template_code)

	def test_std_gov_006_clear_and_write_findings_helpers(self) -> None:
		doc = frappe.get_doc("STD Template", self._template_code)
		clear_std_template_validation_findings(doc)
		write_std_template_validation_findings(
			doc,
			"STD-VAL-MANUAL",
			[
				{
					"finding_code": "TEST-001",
					"severity": "Warning",
					"area": "TEST",
					"message": "hello",
					"blocks_approval": 0,
					"blocks_activation": 0,
					"payload_json": None,
				}
			],
		)
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		reloaded = frappe.get_doc("STD Template", self._template_code)
		self.assertEqual(len(reloaded.validation_findings), 1)
		self.assertEqual(reloaded.validation_findings[0].finding_code, "TEST-001")

	def test_std_gov_006_second_run_replaces_findings(self) -> None:
		# Package manifest template_code must match ``STD Template.name`` (engine check).
		upsert_std_template(commit=True)
		code = "KE-PPRA-WORKS-BLDG-2022-04-POC"
		first = run_std_template_validation(code)
		self.assertTrue(first["ok"], msg=first)
		second = run_std_template_validation(code)
		self.assertNotEqual(first["run_id"], second["run_id"])
		doc = frappe.get_doc("STD Template", code)
		self.assertEqual(doc.latest_validation_run_id, second["run_id"])
