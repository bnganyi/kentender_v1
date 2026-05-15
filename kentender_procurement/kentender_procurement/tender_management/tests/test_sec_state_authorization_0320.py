# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0320 — ``StateAuthorizationService`` / engine ``state_authorization`` context.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_state_authorization_0320
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
from kentender_procurement.tender_management.security.authorization.state_authorization import (
	StateAuthorizationService,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class TestSecStateAuthorization0320(IntegrationTestCase):
	def setUp(self) -> None:
		RolePermissionService.ensure_matrix_seeded()

	def test_active_template_import_denied(self) -> None:
		out = StateAuthorizationService.check_template_state_allows(
			"IMPORT_OFFICIAL_STD_PACKAGE",
			"Active",
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_code, DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED)

	def test_active_template_activate_denied(self) -> None:
		out = StateAuthorizationService.check_template_state_allows(
			"ACTIVATE_STD_TEMPLATE",
			"Active",
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_code, DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED)

	def test_submitted_for_approval_validate_allowed_import_denied(self) -> None:
		self.assertTrue(
			StateAuthorizationService.check_template_state_allows(
				"VALIDATE_STD_TEMPLATE",
				"Submitted for Approval",
			).allowed
		)
		d = StateAuthorizationService.check_template_state_allows(
			"IMPORT_OFFICIAL_STD_PACKAGE",
			"Submitted for Approval",
		)
		self.assertFalse(d.allowed)
		self.assertEqual(d.denial_code, DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED)

	def test_locked_for_approval_instance_edit_denied(self) -> None:
		out = StateAuthorizationService.check_instance_state_allows(
			"EDIT_STD_INSTANCE_PARAMETERS",
			"Locked for Approval",
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_code, DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED)

	def test_published_locked_instance_edit_addendum_code(self) -> None:
		out = StateAuthorizationService.check_instance_state_allows(
			"EDIT_STD_INSTANCE_PARAMETERS",
			"Published Locked",
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_code, DenialCode.POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED)

	def test_published_output_regenerate_denied(self) -> None:
		out = StateAuthorizationService.check_output_state_allows(
			"GENERATE_STD_OUTPUTS",
			"Published",
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_code, DenialCode.STD_AUTH_OUTPUT_LOCKED)

	def test_stale_output_consume_denied(self) -> None:
		out = StateAuthorizationService.check_output_state_allows("CONSUME_DOM", "Stale")
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_code, DenialCode.OUTPUT_STALE)

	def test_superseded_output_consume_denied(self) -> None:
		out = StateAuthorizationService.check_output_state_allows("CONSUME_DSM", "Superseded")
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_code, DenialCode.OUTPUT_SUPERSEDED)

	def test_final_snapshot_mutation_denied(self) -> None:
		out = StateAuthorizationService.check_snapshot_state_allows(
			"GENERATE_STD_OUTPUTS",
			"Final",
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_code, DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED)

	def test_final_snapshot_export_allowed(self) -> None:
		self.assertTrue(
			StateAuthorizationService.check_snapshot_state_allows(
				"EXPORT_EVIDENCE_PACKAGE",
				"Final",
			).allowed
		)

	def test_assert_instance_raises_validation_error(self) -> None:
		with self.assertRaisesRegex(frappe.ValidationError, "addendum"):
			StateAuthorizationService.assert_instance_state_allows(
				"EDIT_STD_INSTANCE_PARAMETERS",
				"Published Locked",
			)

	def test_decision_engine_state_authorization_denies_before_legacy(self) -> None:
		res = AuthorizationDecisionEngine.evaluate(
			"Administrator",
			"EDIT_STD_INSTANCE_PARAMETERS",
			"Tender STD Instance",
			"INST-1",
			context={
				"granted_permissions": ["PERM_INSTANCE_EDIT_PARAMETERS"],
				"state_authorization": {"kind": "instance", "status": "Published Locked"},
				"state_allows": True,
			},
		)
		self.assertFalse(res["allowed"])
		self.assertEqual(res.get("denial_code"), DenialCode.POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED)

	def test_decision_engine_dispatch_check_unified(self) -> None:
		out = StateAuthorizationService.check(
			"PUBLISH_TENDER",
			kind="output",
			status="Stale",
		)
		self.assertFalse(out.allowed)
		self.assertEqual(out.denial_code, DenialCode.OUTPUT_STALE)
