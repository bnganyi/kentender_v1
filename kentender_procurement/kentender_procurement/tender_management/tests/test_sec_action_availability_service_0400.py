# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0400 — ``ActionAvailabilityService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_action_availability_service_0400
"""

from __future__ import annotations

from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.action_availability.catalog import (
	REQUIRED_ACTION_CODES,
)
from kentender_procurement.tender_management.security.action_availability.service import (
	ActionAvailabilityService,
	get_action_availability,
	pack_action_availability_v73_errors,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	registered_action_codes,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class TestSecActionAvailabilityService0400(IntegrationTestCase):
	def setUp(self) -> None:
		RolePermissionService.ensure_matrix_seeded()

	def test_sec_0400_catalog_required_actions_registered(self) -> None:
		self.assertTrue(REQUIRED_ACTION_CODES <= registered_action_codes())

	def test_sec_0400_allowed_response_shape(self) -> None:
		res = ActionAvailabilityService.get_action_availability(
			"Administrator",
			"PUBLISH_TENDER",
			"Tender",
			"TND-0400-ALLOWED",
			context={
				"granted_permissions": ["PERM_TENDER_PUBLISH"],
				"object_state": "Preparation",
			},
		)
		self.assertEqual(pack_action_availability_v73_errors(res), [])
		self.assertTrue(res["allowed"])
		self.assertEqual(res["action_code"], "PUBLISH_TENDER")
		self.assertEqual(res["object_type"], "Tender")
		self.assertEqual(res["object_code"], "TND-0400-ALLOWED")
		self.assertEqual(res["denial_code"], "")
		self.assertEqual(res["required_permission"], "PERM_TENDER_PUBLISH")
		self.assertEqual(res["risk_level"], "Critical")
		self.assertTrue(res["requires_confirmation"])
		self.assertTrue(res["confirmation_required"])
		self.assertTrue(res["audit_on_attempt"])
		self.assertEqual(res["object_state"], "Preparation")
		self.assertEqual(res["user_message"], res["message"])
		self.assertIsInstance(res["blockers"], list)
		self.assertEqual(res["blockers"], [])
		self.assertFalse(res["reason_required"])

	def test_sec_0400_denied_response_shape(self) -> None:
		res = ActionAvailabilityService.get_action_availability(
			"Administrator",
			"PUBLISH_TENDER",
			"Tender",
			"TND-0400-DENIED",
			context={
				"granted_permissions": ["PERM_TENDER_PUBLISH"],
				"state_allows": False,
				"state_denial_code": DenialCode.PUBLISH_APPROVAL_REQUIRED,
				"state_message": "Tender cannot be published until approval is complete.",
				"object_state": "Preparation",
			},
		)
		self.assertEqual(pack_action_availability_v73_errors(res), [])
		self.assertFalse(res["allowed"])
		self.assertEqual(res["denial_code"], DenialCode.PUBLISH_APPROVAL_REQUIRED)
		self.assertEqual(res["object_type"], "Tender")
		self.assertEqual(res["object_code"], "TND-0400-DENIED")
		self.assertEqual(res["required_permission"], "PERM_TENDER_PUBLISH")
		self.assertEqual(res["object_state"], "Preparation")
		self.assertEqual(res["risk_level"], "Critical")
		self.assertFalse(res["requires_confirmation"])
		self.assertFalse(res["confirmation_required"])
		self.assertTrue(res["audit_on_attempt"])
		self.assertEqual(len(res["blockers"]), 1)
		b0 = res["blockers"][0]
		self.assertEqual(b0["blocker_code"], DenialCode.PUBLISH_APPROVAL_REQUIRED)
		self.assertEqual(b0["severity"], "Critical")

	def test_sec_0400_uses_engine_without_mutation_hooks(self) -> None:
		with patch(
			"kentender_procurement.tender_management.security.action_availability.service.AuthorizationDecisionEngine.evaluate",
			return_value={
				"allowed": True,
				"action_code": "CONSUME_DOM",
				"required_permission": "PERM_INSTANCE_VIEW",
				"risk_level": "Low",
				"requires_confirmation": False,
				"audit_on_attempt": False,
				"message": "Allowed",
			},
		) as eval_mock:
			ctx = {"granted_permissions": ["PERM_INSTANCE_VIEW"], "marker": "x"}
			res = ActionAvailabilityService.get_action_availability(
				"Administrator",
				"CONSUME_DOM",
				"Tender STD Generated Output",
				"OUT-0400",
				context=ctx,
			)

		eval_mock.assert_called_once_with(
			"Administrator",
			"CONSUME_DOM",
			"Tender STD Generated Output",
			"OUT-0400",
			{"granted_permissions": ["PERM_INSTANCE_VIEW"], "marker": "x"},
		)
		self.assertEqual(ctx, {"granted_permissions": ["PERM_INSTANCE_VIEW"], "marker": "x"})
		self.assertTrue(res["allowed"])
		self.assertEqual(pack_action_availability_v73_errors(res), [])

	def test_sec_0400_pack_ordered_entrypoint_matches_service(self) -> None:
		ctx = {"granted_permissions": ["PERM_INSTANCE_VIEW"]}
		a = get_action_availability(
			"CONSUME_DOM",
			"Tender STD Generated Output",
			"OUT-0400-PACK",
			"Administrator",
			context=ctx,
		)
		b = ActionAvailabilityService.get_action_availability(
			"Administrator",
			"CONSUME_DOM",
			"Tender STD Generated Output",
			"OUT-0400-PACK",
			context=ctx,
		)
		self.assertEqual(a, b)

	def test_sec_0400_camel_case_alias(self) -> None:
		res = ActionAvailabilityService.getActionAvailability(
			"Administrator",
			"CONSUME_DSM",
			"Tender STD Generated Output",
			"OUT-0400-ALIAS",
			context={"granted_permissions": ["PERM_INSTANCE_VIEW"]},
		)
		self.assertTrue(res["allowed"])
		self.assertEqual(res["action_code"], "CONSUME_DSM")
		self.assertEqual(pack_action_availability_v73_errors(res), [])
