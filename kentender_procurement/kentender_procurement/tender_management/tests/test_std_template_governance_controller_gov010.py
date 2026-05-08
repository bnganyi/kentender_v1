# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-010 — ``STD Template`` controller guards (doc 7 §19, domain §27).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_controller_gov010
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005 import (
	_new_gov005_std_template,
)


class TestStdTemplateGovernanceControllerGov010(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"GOV010-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		if self._code and frappe.db.exists("STD Template", self._code):
			frappe.db.delete("STD Template Usage", {"parent": self._code})
			frappe.db.delete("STD Template Validation Finding", {"parent": self._code})
			frappe.db.delete("STD Template Lifecycle Event", {"parent": self._code})
			frappe.db.set_value(
				"STD Template",
				self._code,
				{
					"tender_usage_count": 0,
					"locked_due_to_usage": 0,
					"mutation_blocked": 0,
					"usage_summary_json": None,
				},
			)
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()
		frappe.set_user("Administrator")

	def test_std_gov_010_imported_allows_package_edit(self) -> None:
		d = frappe.get_doc("STD Template", self._code)
		d.package_json = '{"edited": true}'
		d.save()
		self.assertIn("edited", d.package_json)

	def test_std_gov_010_submitted_blocks_protected_field_change(self) -> None:
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"lifecycle_status": gov.STATUS_SUBMITTED},
		)
		frappe.db.commit()
		d = frappe.get_doc("STD Template", self._code)
		d.package_json = '{"blocked": true}'
		with self.assertRaises(frappe.ValidationError):
			d.save()
		final = frappe.get_doc("STD Template", self._code)
		codes = [r.event_code for r in (final.lifecycle_events or [])]
		self.assertIn(gov.EVT_MUTATION_BLOCKED, codes)

	def test_std_gov_010_usage_blocks_package_change(self) -> None:
		d = frappe.get_doc("STD Template", self._code)
		d.append(
			"template_usage",
			{
				"usage_code": f"STD-USG-{frappe.generate_hash(length=8)}",
				"used_at": frappe.utils.now_datetime(),
				"used_by": "Administrator",
				"usage_type": "Planning Mapping Test",
				"package_hash_at_use": d.package_hash,
				"usage_status": "Active",
			},
		)
		d.save(ignore_permissions=True)
		frappe.db.commit()
		d2 = frappe.get_doc("STD Template", self._code)
		d2.package_json = '{"after_usage": true}'
		with self.assertRaises(frappe.ValidationError):
			d2.save()

	def test_std_gov_010_allowed_for_tender_creation_clamped_when_not_active(self) -> None:
		d = frappe.get_doc("STD Template", self._code)
		d.allowed_for_tender_creation = 1
		d.save()
		d.reload()
		self.assertEqual(int(d.allowed_for_tender_creation or 0), 0)

	def test_std_gov_010_derived_flags_active_template(self) -> None:
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"lifecycle_status": gov.STATUS_ACTIVE},
		)
		frappe.db.commit()
		d = frappe.get_doc("STD Template", self._code)
		d.save()
		d.reload()
		self.assertEqual(int(d.payload_locked or 0), 1)
		self.assertEqual(int(d.mutation_blocked or 0), 1)
		self.assertEqual(int(d.delete_blocked or 0), 1)

	def test_std_gov_010_delete_blocked_with_usage(self) -> None:
		d = frappe.get_doc("STD Template", self._code)
		d.append(
			"template_usage",
			{
				"usage_code": f"STD-USG-{frappe.generate_hash(length=8)}",
				"used_at": frappe.utils.now_datetime(),
				"used_by": "Administrator",
				"usage_type": "Planning Mapping Test",
				"package_hash_at_use": d.package_hash,
				"usage_status": "Active",
			},
		)
		d.save(ignore_permissions=True)
		frappe.db.commit()
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)

	def test_std_gov_010_privileged_delete_without_usage(self) -> None:
		frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
		frappe.db.commit()
		self.assertFalse(frappe.db.exists("STD Template", self._code))
		self._code = ""
