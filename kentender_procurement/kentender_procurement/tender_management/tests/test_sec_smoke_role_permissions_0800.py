from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.action_availability.service import (
	ActionAvailabilityService,
)
from kentender_procurement.tender_management.security.permissions.seed_security_fixtures_0700 import (
	fixture_users,
	upsert_security_seed_fixtures,
)


def _fixture_lookup() -> dict[str, dict[str, str]]:
	return {row["actor_user_code"]: row for row in fixture_users()}


class TestSecSmokeRolePermissions0800(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		upsert_security_seed_fixtures()
		self._fixtures = _fixture_lookup()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")

	def _actor_email(self, actor_user_code: str) -> str:
		return self._fixtures[actor_user_code]["email"]

	def _availability(
		self,
		*,
		actor_user_code: str,
		role_code: str,
		action_code: str,
		context: dict[str, object] | None = None,
	) -> dict[str, object]:
		ctx = {"security_role_codes": [role_code], "enforce_negative_permission_rules": True}
		if context:
			ctx.update(context)
		return ActionAvailabilityService.get_action_availability(
			self._actor_email(actor_user_code),
			action_code,
			"TM2 Tender",
			"TND-SEC-0800",
			context=ctx,
		)

	def test_sec_smoke_role_001_std_admin_import_allowed(self) -> None:
		out = self._availability(
			actor_user_code="USER-STD-ADMIN-001",
			role_code="ROLE_STD_ADMIN",
			action_code="IMPORT_OFFICIAL_STD_PACKAGE",
		)
		self.assertTrue(out["allowed"])

	def test_sec_smoke_role_002_std_admin_create_instance_denied(self) -> None:
		out = self._availability(
			actor_user_code="USER-STD-ADMIN-001",
			role_code="ROLE_STD_ADMIN",
			action_code="CREATE_STD_INSTANCE_FROM_TENDER",
			context={"granted_permissions": ["PERM_INSTANCE_CREATE"]},
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "STD_AUTH_PERMISSION_DENIED")

	def test_sec_smoke_role_003_procurement_officer_release_allowed(self) -> None:
		out = self._availability(
			actor_user_code="USER-PROC-OFFICER-001",
			role_code="ROLE_PROCUREMENT_OFFICER",
			action_code="RELEASE_PACKAGE_TO_TENDER",
		)
		self.assertTrue(out["allowed"])

	def test_sec_smoke_role_004_procurement_officer_template_mapping_denied(self) -> None:
		out = self._availability(
			actor_user_code="USER-PROC-OFFICER-001",
			role_code="ROLE_PROCUREMENT_OFFICER",
			action_code="CONFIGURE_STD_TEMPLATE_MAPPINGS",
			context={"granted_permissions": ["PERM_TEMPLATE_CONFIGURE_MAPPINGS"]},
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "STD_AUTH_PERMISSION_DENIED")

	def test_sec_smoke_role_005_procurement_assistant_mark_ready_denied_by_default(self) -> None:
		out = self._availability(
			actor_user_code="USER-PROC-ASSISTANT-001",
			role_code="ROLE_PROCUREMENT_ASSISTANT",
			action_code="SUBMIT_TENDER_FOR_APPROVAL",
			context={"granted_permissions": ["PERM_TENDER_SUBMIT_APPROVAL"]},
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "STD_AUTH_PERMISSION_DENIED")

	def test_sec_smoke_role_006_approving_authority_approves_allowed(self) -> None:
		out = self._availability(
			actor_user_code="USER-APPROVER-001",
			role_code="ROLE_APPROVING_AUTHORITY",
			action_code="APPROVE_TENDER_PUBLICATION",
		)
		self.assertTrue(out["allowed"])

	def test_sec_smoke_role_007_approving_authority_edits_boq_denied(self) -> None:
		out = self._availability(
			actor_user_code="USER-APPROVER-001",
			role_code="ROLE_APPROVING_AUTHORITY",
			action_code="EDIT_WORKS_BOQ_DURING_APPROVAL",
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "STD_AUTH_PERMISSION_DENIED")

	def test_sec_smoke_role_008_auditor_exports_evidence_allowed(self) -> None:
		out = self._availability(
			actor_user_code="USER-AUDITOR-001",
			role_code="ROLE_AUDITOR",
			action_code="EXPORT_EVIDENCE_PACKAGE",
		)
		self.assertTrue(out["allowed"])

	def test_sec_smoke_role_009_auditor_mutates_instance_denied(self) -> None:
		out = self._availability(
			actor_user_code="USER-AUDITOR-001",
			role_code="ROLE_AUDITOR",
			action_code="EDIT_STD_INSTANCE_PARAMETERS",
			context={"granted_permissions": ["PERM_INSTANCE_EDIT_PARAMETERS"]},
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "STD_AUTH_PERMISSION_DENIED")
