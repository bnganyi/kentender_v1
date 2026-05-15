from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.action_availability.service import (
	ActionAvailabilityService,
)


class TestSecSmokeStateLocks0810(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")

	def _availability(
		self,
		*,
		action_code: str,
		object_type: str,
		object_code: str,
		state_kind: str,
		state_status: str,
		granted_permission: str,
	) -> dict[str, object]:
		return ActionAvailabilityService.get_action_availability(
			"Administrator",
			action_code,
			object_type,
			object_code,
			context={
				"granted_permissions": [granted_permission],
				"state_authorization": {"kind": state_kind, "status": state_status},
			},
		)

	def test_sec_smoke_state_001_edit_draft_std_instance_allowed(self) -> None:
		out = self._availability(
			action_code="EDIT_STD_INSTANCE_PARAMETERS",
			object_type="Tender STD Instance",
			object_code="INST-0810-DRAFT",
			state_kind="instance",
			state_status="Draft",
			granted_permission="PERM_INSTANCE_EDIT_PARAMETERS",
		)
		self.assertTrue(out["allowed"])

	def test_sec_smoke_state_002_edit_locked_for_approval_denied(self) -> None:
		out = self._availability(
			action_code="EDIT_STD_INSTANCE_PARAMETERS",
			object_type="Tender STD Instance",
			object_code="INST-0810-LOCKED",
			state_kind="instance",
			state_status="Locked for Approval",
			granted_permission="PERM_INSTANCE_EDIT_PARAMETERS",
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "STD_AUTH_ACTIVE_VERSION_LOCKED")

	def test_sec_smoke_state_003_edit_published_instance_denied_addendum_required(self) -> None:
		out = self._availability(
			action_code="EDIT_STD_INSTANCE_PARAMETERS",
			object_type="Tender STD Instance",
			object_code="INST-0810-PUBLISHED",
			state_kind="instance",
			state_status="Published Locked",
			granted_permission="PERM_INSTANCE_EDIT_PARAMETERS",
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED")

	def test_sec_smoke_state_004_edit_active_std_template_denied(self) -> None:
		out = self._availability(
			action_code="ACTIVATE_STD_TEMPLATE",
			object_type="STD Template",
			object_code="TPL-0810-ACTIVE",
			state_kind="template",
			state_status="Active",
			granted_permission="PERM_TEMPLATE_ACTIVATE",
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "STD_AUTH_ACTIVE_VERSION_LOCKED")

	def test_sec_smoke_state_005_overwrite_published_output_denied(self) -> None:
		out = self._availability(
			action_code="GENERATE_STD_OUTPUTS",
			object_type="Tender STD Generated Output",
			object_code="OUT-0810-PUBLISHED",
			state_kind="output",
			state_status="Published",
			granted_permission="PERM_INSTANCE_GENERATE_OUTPUTS",
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "STD_AUTH_OUTPUT_LOCKED")

	def test_sec_smoke_state_006_modify_final_snapshot_denied(self) -> None:
		out = self._availability(
			action_code="GENERATE_STD_OUTPUTS",
			object_type="Tender STD Instance Snapshot",
			object_code="SNP-0810-FINAL",
			state_kind="snapshot",
			state_status="Final",
			granted_permission="PERM_INSTANCE_GENERATE_OUTPUTS",
		)
		self.assertFalse(out["allowed"])
		self.assertEqual(out["denial_code"], "STD_AUTH_ACTIVE_VERSION_LOCKED")
