# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-011 — Desk whitelisted governance API (doc 7 §20).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_desk_api_gov011
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.std_template.std_template import (
	get_std_template_audit_timeline,
	get_std_template_governance_summary,
	replace_std_template_package,
)
from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005 import (
	_new_gov005_std_template,
)


class TestStdTemplateGovernanceDeskApiGov011(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"GOV011-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		if frappe.db.exists("STD Template", self._code):
			frappe.db.delete("STD Template Usage", {"parent": self._code})
			frappe.db.delete("STD Template Validation Finding", {"parent": self._code})
			frappe.db.delete("STD Template Lifecycle Event", {"parent": self._code})
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()
		frappe.set_user("Administrator")

	def test_std_gov_011_replace_and_resets_validation(self) -> None:
		out = replace_std_template_package(
			self._code,
			package_json='{"x": 1}',
			manifest_json="{}",
			reason="fixture replace",
		)
		self.assertTrue(out.get("ok"))
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_IMPORTED)
		self.assertIn('"x"', doc.package_json or "")
		codes = [r.event_code for r in (doc.lifecycle_events or [])]
		self.assertIn(gov.EVT_PACKAGE_REPLACED, codes)

	def test_std_gov_011_replace_rejected_without_reason(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			replace_std_template_package(self._code, package_json="{}", manifest_json="{}", reason="  ")

	def test_std_gov_011_replace_blocked_in_submitted(self) -> None:
		frappe.db.set_value("STD Template", self._code, {"lifecycle_status": gov.STATUS_SUBMITTED})
		frappe.db.commit()
		with self.assertRaises(frappe.ValidationError):
			replace_std_template_package(
				self._code,
				package_json="{}",
				manifest_json="{}",
				reason="should fail",
			)

	def test_std_gov_011_governance_summary_and_timeline(self) -> None:
		s = get_std_template_governance_summary(self._code)
		self.assertTrue(s.get("ok"))
		self.assertEqual(s.get("std_template"), self._code)
		t = get_std_template_audit_timeline(self._code)
		self.assertTrue(t.get("ok"))
		self.assertIsInstance(t.get("events"), list)
