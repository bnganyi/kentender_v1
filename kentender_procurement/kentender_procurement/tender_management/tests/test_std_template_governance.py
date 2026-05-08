# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-013 §22.1 — consolidated lifecycle integration tests (doc 7 §22.1).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_lifecycle import (
	activate_std_template,
	approve_std_template,
	archive_std_template,
	reinstate_std_template,
	retire_std_template,
	submit_std_template_for_approval,
	supersede_std_template,
	suspend_std_template,
)
from kentender_procurement.tender_management.services.std_template_governance_usage import (
	check_std_template_tender_creation_eligibility,
)
from kentender_procurement.tender_management.services.std_template_governance_validation import (
	run_std_template_validation,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005 import (
	_new_gov005_std_template,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_lifecycle_gov007 import (
	_set_validated_guards,
)


def _package_hash(doc_name: str) -> str:
	ph = frappe.db.get_value("STD Template", doc_name, "package_hash")
	assert ph
	return str(ph)


class TestStdTemplateGovernanceSection221(IntegrationTestCase):
	"""Doc 7 §22.1 — matrix test names."""

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"GOV013A-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		other = getattr(self, "_other_code", None)
		if other and frappe.db.exists("STD Template", other):
			frappe.delete_doc("STD Template", other, force=True, ignore_permissions=True)
			frappe.db.commit()
		if frappe.db.exists("STD Template", self._code):
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()
		frappe.set_user("Administrator")

	def test_import_creates_imported_template(self) -> None:
		d = frappe.get_doc("STD Template", self._code)
		self.assertEqual(d.lifecycle_status, gov.STATUS_IMPORTED)
		self.assertTrue((d.package_hash or "").strip())
		self.assertEqual(int(d.allowed_for_tender_creation or 0), 0)

	def test_validation_pass_moves_to_validated(self) -> None:
		upsert_std_template(commit=True)
		out = run_std_template_validation(TEMPLATE_CODE)
		self.assertTrue(out.get("ok"), msg=out)
		d = frappe.get_doc("STD Template", TEMPLATE_CODE)
		self.assertEqual(d.lifecycle_status, gov.STATUS_VALIDATED)

	def test_validation_failure_moves_to_validation_failed(self) -> None:
		frappe.db.set_value("STD Template", self._code, "package_json", "{}")
		frappe.db.commit()
		out = run_std_template_validation(self._code)
		self.assertFalse(out.get("ok"))
		d = frappe.get_doc("STD Template", self._code)
		self.assertEqual(d.lifecycle_status, gov.STATUS_VALIDATION_FAILED)
		self.assertGreater(len(d.validation_findings or []), 0)

	def test_submit_requires_current_validation(self) -> None:
		_set_validated_guards(self._code)
		frappe.db.set_value("STD Template", self._code, "validation_is_current", 0)
		frappe.db.commit()
		with self.assertRaises(frappe.ValidationError):
			submit_std_template_for_approval(self._code, comment="x")

	def test_submit_moves_validated_to_submitted(self) -> None:
		_set_validated_guards(self._code)
		out = submit_std_template_for_approval(self._code, comment="please review")
		self.assertTrue(out["ok"])
		d = frappe.get_doc("STD Template", self._code)
		self.assertEqual(d.lifecycle_status, gov.STATUS_SUBMITTED)

	def test_approve_moves_submitted_to_approved_not_active(self) -> None:
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="go")
		out = approve_std_template(self._code, "ok", override_reason="break-glass")
		self.assertTrue(out["ok"])
		d = frappe.get_doc("STD Template", self._code)
		self.assertEqual(d.lifecycle_status, gov.STATUS_APPROVED)
		self.assertEqual(int(d.allowed_for_tender_creation or 0), 0)

	def test_activate_moves_approved_to_active(self) -> None:
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="go")
		approve_std_template(self._code, "ok", override_reason="break-glass")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		out = activate_std_template(self._code, reason="go live")
		self.assertTrue(out["ok"])
		d = frappe.get_doc("STD Template", self._code)
		self.assertEqual(d.lifecycle_status, gov.STATUS_ACTIVE)
		self.assertEqual(int(d.allowed_for_tender_creation or 0), 1)

	def test_suspend_blocks_tender_eligibility(self) -> None:
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="go")
		approve_std_template(self._code, "ok", override_reason="x")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		activate_std_template(self._code, reason="live")
		self.assertTrue(suspend_std_template(self._code, reason="pause")["ok"])
		out = check_std_template_tender_creation_eligibility(self._code, None)
		self.assertFalse(out["eligible"])

	def test_reinstate_restores_active(self) -> None:
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="go")
		approve_std_template(self._code, "ok", override_reason="x")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		activate_std_template(self._code, reason="live")
		suspend_std_template(self._code, reason="pause")
		self.assertTrue(reinstate_std_template(self._code, reason="resume")["ok"])
		out = check_std_template_tender_creation_eligibility(self._code, None)
		self.assertTrue(out["eligible"])

	def test_retire_blocks_new_use(self) -> None:
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="go")
		approve_std_template(self._code, "ok", override_reason="x")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		activate_std_template(self._code, reason="live")
		self.assertTrue(retire_std_template(self._code, reason="end")["ok"])
		out = check_std_template_tender_creation_eligibility(self._code, None)
		self.assertFalse(out["eligible"])

	def test_supersede_blocks_old_version(self) -> None:
		self._other_code = f"GOV013B-{frappe.generate_hash(length=8)}"
		_new_gov005_std_template(self._other_code)
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="go")
		approve_std_template(self._code, "ok", override_reason="x")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		activate_std_template(self._code, reason="live")

		frappe.db.set_value(
			"STD Template",
			self._other_code,
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

		out = supersede_std_template(self._code, self._other_code, reason="new version")
		self.assertTrue(out["ok"])
		old = frappe.get_doc("STD Template", self._code)
		self.assertEqual(old.lifecycle_status, gov.STATUS_SUPERSEDED)
		self.assertFalse(
			check_std_template_tender_creation_eligibility(self._code, None)["eligible"]
		)

	def test_archive_blocks_all_operational_actions(self) -> None:
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="go")
		approve_std_template(self._code, "ok", override_reason="x")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		activate_std_template(self._code, reason="live")
		retire_std_template(self._code, reason="end")
		self.assertTrue(archive_std_template(self._code, reason="cleanup")["ok"])
		d = frappe.get_doc("STD Template", self._code)
		self.assertEqual(d.lifecycle_status, gov.STATUS_ARCHIVED)
		with self.assertRaises(frappe.ValidationError):
			submit_std_template_for_approval(self._code, comment="nope")
