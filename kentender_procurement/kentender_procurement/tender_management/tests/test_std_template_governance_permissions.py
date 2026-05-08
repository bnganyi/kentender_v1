# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-013 §22.2 — permission / SoD matrix (doc 7 §22.2).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_permissions
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.std_template.std_template import (
	get_std_template_governance_summary,
)
from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_lifecycle import (
	activate_std_template,
	approve_std_template,
	submit_std_template_for_approval,
)
from kentender_procurement.tender_management.services.std_template_governance_usage import (
	check_std_template_tender_creation_eligibility,
	record_std_template_usage,
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


def _new_user(email: str, *roles: str) -> None:
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()
	u = frappe.new_doc("User")
	u.email = email
	u.first_name = "Gov013"
	u.enabled = 1
	u.send_welcome_email = 0
	u.insert(ignore_permissions=True)
	u.add_roles(*roles)
	frappe.db.commit()


class TestStdTemplateGovernanceSection222(IntegrationTestCase):
	"""Doc 7 §22.2 — matrix test names."""

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"GOV013P-{frappe.generate_hash(length=10)}"
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
			frappe.db.delete("STD Template Validation Finding", {"parent": self._code})
			frappe.db.delete("STD Template Lifecycle Event", {"parent": self._code})
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()
		for em in getattr(self, "_emails", ()):
			if frappe.db.exists("User", em):
				frappe.delete_doc("User", em, force=True, ignore_permissions=True)
				frappe.db.commit()

	def test_importer_cannot_approve_own_template(self) -> None:
		email = "gov013-imp-app@example.com"
		self._emails = (email,)
		_new_user(
			email,
			"STD Template Importer",
			"STD Template Approver",
			"STD Template Administrator",
		)
		_set_validated_guards(self._code)
		frappe.set_user(email)
		submit_std_template_for_approval(self._code, comment="mine")
		with self.assertRaises(frappe.ValidationError):
			approve_std_template(self._code, "self-approve", override_reason=None)

	def test_admin_cannot_activate_without_activator_role(self) -> None:
		sub = "gov013-sub@example.com"
		app = "gov013-app@example.com"
		self._emails = (sub, app)
		_new_user(sub, "STD Template Administrator")
		_new_user(app, "STD Template Approver")
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		frappe.set_user(sub)
		submit_std_template_for_approval(self._code, comment="x")
		frappe.set_user(app)
		approve_std_template(self._code, "ok")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		frappe.set_user(sub)
		with self.assertRaises(frappe.PermissionError):
			activate_std_template(self._code, reason="go live")

	def test_technical_inspector_cannot_approve(self) -> None:
		email = "gov013-ti@example.com"
		self._emails = (email,)
		_new_user(email, "STD Technical Inspector")
		frappe.set_user(email)
		with self.assertRaises(frappe.PermissionError):
			approve_std_template(self._code, "nope", override_reason=None)

	def test_procurement_officer_cannot_view_raw_payload(self) -> None:
		email = "gov013-po@example.com"
		self._emails = (email,)
		_new_user(email, "Procurement Officer")
		frappe.set_user(email)
		self.assertFalse(frappe.has_permission("STD Template", "read", doc=self.doc))
		with self.assertRaises(frappe.PermissionError):
			get_std_template_governance_summary(self._code)

	def test_system_manager_override_requires_reason(self) -> None:
		email = "gov013-sm@example.com"
		self._emails = (email,)
		_new_user(email, "System Manager", "STD Template Administrator")
		_set_validated_guards(self._code)
		frappe.set_user(email)
		submit_std_template_for_approval(self._code, comment="sm path")
		with self.assertRaises(frappe.ValidationError):
			approve_std_template(self._code, "approve", override_reason=None)

	def test_used_template_cannot_be_mutated_by_system_manager(self) -> None:
		email = "gov013-sm2@example.com"
		self._emails = (email,)
		_new_user(email, "System Manager")
		ph = _package_hash(self._code)
		frappe.db.set_value(
			"STD Template",
			self._code,
			{
				"lifecycle_status": gov.STATUS_ACTIVE,
				"allowed_for_tender_creation": 1,
				"package_hash": ph,
				"activation_package_hash": ph,
				"approval_package_hash": ph,
				"latest_validation_package_hash": ph,
				"validation_is_current": 1,
			},
		)
		frappe.db.commit()
		frappe.set_user("Administrator")
		record_std_template_usage(self._code, "Tender", tender="TND-GOV013-1", payload={})
		frappe.set_user(email)
		d = frappe.get_doc("STD Template", self._code)
		d.package_json = '{"mutate": true}'
		with self.assertRaises(frappe.ValidationError):
			d.save()

	def test_inactive_template_not_eligible_for_tender_creation(self) -> None:
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="x")
		approve_std_template(self._code, "ok", override_reason="glass")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		out = check_std_template_tender_creation_eligibility(self._code, None)
		self.assertFalse(out["eligible"])
		self.assertIn("lifecycle_not_active", out["reasons"])
