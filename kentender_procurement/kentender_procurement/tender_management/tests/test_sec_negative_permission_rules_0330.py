# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0330 — ``NegativePermissionService`` / pack §11 + fixture NEG-SEC-* parity.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_negative_permission_rules_0330
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.authorization.decision_engine import (
	AuthorizationDecisionEngine,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.security.authorization.negative_permissions import (
	NEG_APPROVER_NO_SILENT_EDIT,
	NEG_ASSISTANT_NO_MARK_READY,
	NEG_AUDITOR_NO_MUTATION,
	NEG_CONTRACT_NO_DCM_OVERRIDE,
	NEG_EVAL_NO_MANUAL_CRITERIA,
	NEG_OPENING_NO_EVALUATION,
	NEG_PROC_NO_TEMPLATE_CONFIG,
	NEG_PUBLISHED_NO_DIRECT_EDIT,
	NEG_STD_ADMIN_NO_INSTANCE_CREATE,
	NEG_STD_ADMIN_NO_PACKAGE_RELEASE,
	NEG_SYSADMIN_NO_OPERATIONAL_APPROVAL,
	NegativePermissionService,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


def _ctx(roles: list[str], **extra: object) -> dict[str, object]:
	out: dict[str, object] = {"security_role_codes": roles}
	out.update(extra)
	return out


class TestSecNegativePermissionRules0330(IntegrationTestCase):
	def setUp(self) -> None:
		RolePermissionService.ensure_matrix_seeded()
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")

	def _ensure_user(self, email: str) -> str:
		name = frappe.db.get_value("User", {"email": email}, "name")
		if name:
			frappe.delete_doc("User", name, force=True, ignore_permissions=True)
		elif frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		u = frappe.new_doc("User")
		u.email = email
		u.first_name = "SEC0330"
		u.user_type = "System User"
		u.enabled = 1
		u.new_password = "Test@1234"
		u.send_welcome_email = 0
		u.insert(ignore_permissions=True)
		frappe.db.set_value("User", u.name, "user_type", "System User")
		return u.name

	def _cleanup_user(self, email: str) -> None:
		name = frappe.db.get_value("User", {"email": email}, "name")
		if name:
			frappe.delete_doc("User", name, force=True, ignore_permissions=True)

	def test_neg_sec_002_std_admin_create_instance_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-STD-ADMIN-001",
			"CREATE_STD_INSTANCE_FROM_TENDER",
			"Tender",
			"T-1",
			_ctx(["ROLE_STD_ADMIN"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.STD_AUTH_PERMISSION_DENIED)
		self.assertIn(NEG_STD_ADMIN_NO_INSTANCE_CREATE, out.rule_codes)

	def test_neg_sec_001_std_admin_release_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-STD-ADMIN-001",
			"RELEASE_PACKAGE_TO_TENDER",
			"Procurement Package",
			"P-1",
			_ctx(["ROLE_STD_ADMIN"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.RELEASE_PERMISSION_DENIED)
		self.assertIn(NEG_STD_ADMIN_NO_PACKAGE_RELEASE, out.rule_codes)

	def test_neg_sec_003_proc_officer_template_mapping_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-PROC-OFFICER-001",
			"CONFIGURE_STD_TEMPLATE_MAPPINGS",
			"STD Template",
			"STD-1",
			_ctx(["ROLE_PROCUREMENT_OFFICER"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.STD_AUTH_PERMISSION_DENIED)
		self.assertIn(NEG_PROC_NO_TEMPLATE_CONFIG, out.rule_codes)

	def test_neg_sec_004_assistant_publish_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-PROC-ASSISTANT-001",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			_ctx(["ROLE_PROCUREMENT_ASSISTANT"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.PUBLISH_PERMISSION_DENIED)
		self.assertIn(NEG_ASSISTANT_NO_MARK_READY, out.rule_codes)

	def test_neg_sec_005_approver_boq_during_approval_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-APPROVER-001",
			"EDIT_WORKS_BOQ_DURING_APPROVAL",
			"Tender",
			"T-1",
			_ctx(["ROLE_APPROVING_AUTHORITY"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.STD_AUTH_PERMISSION_DENIED)
		self.assertIn(NEG_APPROVER_NO_SILENT_EDIT, out.rule_codes)

	def test_approver_instance_edit_denied_when_tender_in_approval(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-APPROVER-001",
			"EDIT_STD_INSTANCE_PARAMETERS",
			"Tender STD Instance",
			"I-1",
			_ctx(["ROLE_APPROVING_AUTHORITY"], tender_in_approval=True),
		)
		self.assertFalse(out.allowed)
		self.assertIn(NEG_APPROVER_NO_SILENT_EDIT, out.rule_codes)

	def test_neg_sec_006_opening_boq_correction_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-OPENING-001",
			"PERFORM_BOQ_ARITHMETIC_CORRECTION",
			"Tender",
			"T-1",
			_ctx(["ROLE_OPENING_COMMITTEE"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION)
		self.assertIn(NEG_OPENING_NO_EVALUATION, out.rule_codes)

	def test_neg_sec_007_eval_manual_criteria_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-EVAL-001",
			"ADD_MANUAL_EVALUATION_CRITERIA",
			"Tender",
			"T-1",
			_ctx(["ROLE_EVALUATION_COMMITTEE"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.MANUAL_EVALUATION_CRITERIA_DENIED)
		self.assertIn(NEG_EVAL_NO_MANUAL_CRITERIA, out.rule_codes)

	def test_neg_sec_008_auditor_instance_edit_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-AUDITOR-001",
			"EDIT_STD_INSTANCE_PARAMETERS",
			"Tender STD Instance",
			"I-1",
			_ctx(["ROLE_AUDITOR"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.STD_AUTH_PERMISSION_DENIED)
		self.assertIn(NEG_AUDITOR_NO_MUTATION, out.rule_codes)

	def test_neg_contract_dcm_override_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-CONTRACT-001",
			"SILENT_DCM_CONTRACT_OVERRIDE",
			"Tender",
			"T-1",
			_ctx(["ROLE_CONTRACT_OFFICER"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.STD_AUTH_DCM_CONTRACT_BINDING_VIOLATION)
		self.assertIn(NEG_CONTRACT_NO_DCM_OVERRIDE, out.rule_codes)

	def test_neg_sysadmin_publish_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"USER-SYSADMIN-001",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			_ctx(["ROLE_SYSTEM_ADMIN"]),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.STD_AUTH_PERMISSION_DENIED)
		self.assertIn(NEG_SYSADMIN_NO_OPERATIONAL_APPROVAL, out.rule_codes)

	def test_neg_published_flag_edit_denied(self) -> None:
		out = NegativePermissionService.evaluate_negative_rules(
			"any-actor",
			"EDIT_STD_INSTANCE_PARAMETERS",
			"Tender STD Instance",
			"I-1",
			_ctx([], published_direct_edit_negation=True),
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_codes[0], DenialCode.POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED)
		self.assertIn(NEG_PUBLISHED_NO_DIRECT_EDIT, out.rule_codes)

	def test_administrator_skips_negative_rules(self) -> None:
		self.assertTrue(
			NegativePermissionService.evaluate_negative_rules(
				"Administrator",
				"CREATE_STD_INSTANCE_FROM_TENDER",
				"Tender",
				"T-1",
				_ctx(["ROLE_STD_ADMIN"]),
			).allowed
		)

	def test_evaluate_negative_rules_alias(self) -> None:
		out = NegativePermissionService.evaluateNegativeRules(
			"u",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			_ctx(["ROLE_PROCUREMENT_ASSISTANT"]),
		)
		self.assertFalse(out.allowed)

	def test_sec_0330_engine_denies_despite_broad_grants(self) -> None:
		email = "sec0330_engine_neg@example.com"
		uname = self._ensure_user(email)
		try:
			res = AuthorizationDecisionEngine.evaluate(
				uname,
				"CREATE_STD_INSTANCE_FROM_TENDER",
				"Tender STD Instance",
				"INST-X",
				context={
					"granted_permissions": ["PERM_INSTANCE_CREATE"],
					"security_role_codes": ["ROLE_STD_ADMIN"],
					"enforce_negative_permission_rules": True,
				},
			)
			self.assertFalse(res["allowed"])
			self.assertEqual(res.get("denial_code"), DenialCode.STD_AUTH_PERMISSION_DENIED)
			self.assertTrue(res.get("audit_on_attempt"))
		finally:
			self._cleanup_user(email)
