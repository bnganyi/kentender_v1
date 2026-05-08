# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-007 — lifecycle transition services (doc 7 §13.3, §14).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_lifecycle_gov007
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_usage import (
	record_std_template_usage,
)
from kentender_procurement.tender_management.services.std_template_governance_lifecycle import (
	activate_std_template,
	approve_std_template,
	archive_std_template,
	reinstate_std_template,
	reject_std_template,
	retire_std_template,
	return_std_template_for_correction,
	submit_std_template_for_approval,
	supersede_std_template,
	suspend_std_template,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005 import (
	_new_gov005_std_template,
)


def _set_validated_guards(doc_name: str) -> None:
	frappe.db.set_value(
		"STD Template",
		doc_name,
		{
			"lifecycle_status": gov.STATUS_VALIDATED,
			"validation_is_current": 1,
			"latest_validation_status": gov.VALIDATION_PASS,
			"latest_validation_run_id": "STD-VAL-TEST",
			"latest_validation_package_hash": frappe.db.get_value(
				"STD Template", doc_name, "package_hash"
			),
			"critical_finding_count": 0,
			"warning_finding_count": 0,
			"info_finding_count": 0,
		},
	)
	frappe.db.commit()


def _set_submitted(doc_name: str, submitter: str) -> None:
	frappe.db.set_value(
		"STD Template",
		doc_name,
		{
			"lifecycle_status": gov.STATUS_SUBMITTED,
			"submitted_for_approval_by": submitter,
			"validation_is_current": 1,
			"latest_validation_status": gov.VALIDATION_PASS,
			"critical_finding_count": 0,
			"package_hash": frappe.db.get_value("STD Template", doc_name, "package_hash"),
		},
	)
	frappe.db.commit()


def _ensure_test_user(email: str, *roles: str) -> None:
	if frappe.db.exists("User", email):
		u = frappe.get_doc("User", email)
	else:
		u = frappe.new_doc("User")
		u.email = email
		u.first_name = "Gov007"
		u.enabled = 1
		u.send_welcome_email = 0
		u.insert(ignore_permissions=True)
	u.add_roles(*roles)
	frappe.db.commit()


class TestStdTemplateGovernanceLifecycleGov007(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"GOV007-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		if frappe.db.exists("STD Template", self._code):
			frappe.db.delete("STD Template Usage", {"parent": self._code})
			frappe.db.set_value(
				"STD Template",
				self._code,
				{
					"tender_usage_count": 0,
					"locked_due_to_usage": 0,
					"mutation_blocked": 0,
				},
			)
			frappe.db.delete("STD Template Lifecycle Event", {"parent": self._code})
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()
		for email in ("gov007sub@example.com", "gov007app@example.com"):
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
				frappe.db.commit()
		frappe.set_user("Administrator")

	def test_std_gov_007_submit_rejects_wrong_state(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			submit_std_template_for_approval(self._code)

	def test_std_gov_007_submit_happy_path(self) -> None:
		_set_validated_guards(self._code)
		out = submit_std_template_for_approval(self._code, comment="please review")
		self.assertTrue(out["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_SUBMITTED)
		self.assertEqual(int(doc.payload_locked or 0), 1)

	def test_std_gov_007_return_requires_reason(self) -> None:
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code)
		with self.assertRaises(frappe.ValidationError):
			return_std_template_for_correction(self._code, "   ")

	def test_std_gov_007_return_and_payload_unlock(self) -> None:
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code)
		out = return_std_template_for_correction(self._code, "needs fix")
		self.assertTrue(out["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_RETURNED)
		self.assertEqual(int(doc.validation_is_current or 0), 0)
		self.assertEqual(int(doc.payload_locked or 0), 0)

	def test_std_gov_007_reject(self) -> None:
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code)
		out = reject_std_template(self._code, "no budget")
		self.assertTrue(out["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_REJECTED)

	def test_std_gov_007_approve_sod_blocks_self_without_override(self) -> None:
		_ensure_test_user(
			"gov007sub@example.com",
			"STD Template Administrator",
			"STD Template Approver",
		)
		_ensure_test_user("gov007app@example.com", "STD Template Approver")
		_set_validated_guards(self._code)
		frappe.set_user("gov007sub@example.com")
		submit_std_template_for_approval(self._code)
		frappe.set_user("gov007sub@example.com")
		with self.assertRaises(frappe.ValidationError):
			approve_std_template(self._code, "ok", override_reason=None)

	def test_std_gov_007_approve_sod_allows_other_user(self) -> None:
		_ensure_test_user("gov007sub@example.com", "STD Template Administrator")
		_ensure_test_user("gov007app@example.com", "STD Template Approver")
		_set_validated_guards(self._code)
		frappe.set_user("gov007sub@example.com")
		submit_std_template_for_approval(self._code)
		frappe.set_user("gov007app@example.com")
		out = approve_std_template(self._code, "approved")
		self.assertTrue(out["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_APPROVED)
		self.assertEqual(int(doc.approval_override_used or 0), 0)

	def test_std_gov_007_approve_self_with_override_as_administrator(self) -> None:
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code)
		out = approve_std_template(self._code, "ok", override_reason="break-glass")
		self.assertTrue(out["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(int(doc.approval_override_used or 0), 1)

	def test_std_gov_007_activate_hash_mismatch(self) -> None:
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code)
		approve_std_template(self._code, "ok", override_reason="x")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": "0" * 64, "latest_validation_package_hash": "0" * 64},
		)
		frappe.db.commit()
		with self.assertRaises(frappe.ValidationError):
			activate_std_template(self._code, reason="go live")

	def test_std_gov_007_activate_suspend_reinstate_retire_archive(self) -> None:
		ph = frappe.db.get_value("STD Template", self._code, "package_hash")
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code)
		approve_std_template(self._code, "ok", override_reason="x")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{
				"approval_package_hash": ph,
				"latest_validation_package_hash": ph,
			},
		)
		frappe.db.commit()
		self.assertTrue(activate_std_template(self._code, reason="go live")["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_ACTIVE)
		self.assertEqual(int(doc.allowed_for_tender_creation or 0), 1)

		self.assertTrue(suspend_std_template(self._code, reason="pause")["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_SUSPENDED)

		self.assertTrue(reinstate_std_template(self._code, reason="resume")["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_ACTIVE)

		self.assertTrue(retire_std_template(self._code, reason="end")["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_RETIRED)

		self.assertTrue(archive_std_template(self._code, reason="cleanup")["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_ARCHIVED)

	def test_std_gov_007_supersede_active(self) -> None:
		other = f"GOV007B-{frappe.generate_hash(length=8)}"
		try:
			_new_gov005_std_template(other)
			ph = frappe.db.get_value("STD Template", self._code, "package_hash")
			_set_validated_guards(self._code)
			submit_std_template_for_approval(self._code)
			approve_std_template(self._code, "ok", override_reason="x")
			frappe.db.set_value(
				"STD Template",
				self._code,
				{"approval_package_hash": ph, "latest_validation_package_hash": ph},
			)
			frappe.db.commit()
			activate_std_template(self._code, reason="go")

			frappe.db.set_value(
				"STD Template",
				other,
				{
					"lifecycle_status": gov.STATUS_APPROVED,
					"package_hash": ph,
					"approval_package_hash": ph,
					"latest_validation_package_hash": ph,
					"validation_is_current": 1,
					"latest_validation_status": gov.VALIDATION_PASS,
					"critical_finding_count": 0,
				},
			)
			frappe.db.commit()

			out = supersede_std_template(self._code, other, reason="new version")
			self.assertTrue(out["ok"])
			doc = frappe.get_doc("STD Template", self._code)
			self.assertEqual(doc.lifecycle_status, gov.STATUS_SUPERSEDED)
			self.assertEqual(
				frappe.db.get_value("STD Template", other, "supersedes_template"),
				self._code,
			)
		finally:
			if frappe.db.exists("STD Template", other):
				frappe.db.delete("STD Template Usage", {"parent": other})
				frappe.delete_doc("STD Template", other, force=True, ignore_permissions=True)
				frappe.db.commit()

	def test_std_gov_007_supersede_with_usage_serializes_impact_payload(self) -> None:
		other = f"GOV007U-{frappe.generate_hash(length=8)}"
		try:
			_new_gov005_std_template(other)
			ph = frappe.db.get_value("STD Template", self._code, "package_hash")
			_set_validated_guards(self._code)
			submit_std_template_for_approval(self._code)
			approve_std_template(self._code, "ok", override_reason="x")
			frappe.db.set_value(
				"STD Template",
				self._code,
				{"approval_package_hash": ph, "latest_validation_package_hash": ph},
			)
			frappe.db.commit()
			activate_std_template(self._code, reason="go")
			record_std_template_usage(self._code, "Tender", tender="TND-USG-1", payload={})

			frappe.db.set_value(
				"STD Template",
				other,
				{
					"lifecycle_status": gov.STATUS_APPROVED,
					"package_hash": ph,
					"approval_package_hash": ph,
					"latest_validation_package_hash": ph,
					"validation_is_current": 1,
					"latest_validation_status": gov.VALIDATION_PASS,
					"critical_finding_count": 0,
				},
			)
			frappe.db.commit()

			out = supersede_std_template(self._code, other, reason="with usage row")
			self.assertTrue(out["ok"])
			doc = frappe.get_doc("STD Template", self._code)
			self.assertEqual(doc.lifecycle_status, gov.STATUS_SUPERSEDED)
			row = next(
				e for e in reversed(doc.lifecycle_events or []) if e.event_code == gov.EVT_SUPERSEDED
			)
			self.assertIn("usage_impact", row.payload_json or "")
		finally:
			if frappe.db.exists("STD Template", other):
				frappe.db.delete("STD Template Usage", {"parent": other})
				frappe.delete_doc("STD Template", other, force=True, ignore_permissions=True)
				frappe.db.commit()

	def test_std_gov_007_guest_cannot_submit(self) -> None:
		_set_validated_guards(self._code)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			submit_std_template_for_approval(self._code)
