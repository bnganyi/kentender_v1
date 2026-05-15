# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0410 — action availability API handlers.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_action_availability_api_0410
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.action_availability.api import (
	SEC_API_ACTION_CODE_REQUIRED,
	SEC_API_INTERNAL_ERROR,
	SEC_API_ITEMS_REQUIRED,
	SEC_API_PAYLOAD_INVALID,
	sec_api_action_availability,
	sec_api_action_availability_batch,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class TestSecActionAvailabilityApi0410(IntegrationTestCase):
	def setUp(self) -> None:
		RolePermissionService.ensure_matrix_seeded()
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")

	def test_sec_0410_single_success_uses_session_actor(self) -> None:
		res = sec_api_action_availability(
			action_code="PUBLISH_TENDER",
			object_type="Tender",
			object_code="TND-0410-1",
			context={"granted_permissions": ["PERM_TENDER_PUBLISH"]},
		)
		self.assertTrue(res["success"])
		self.assertEqual(res["actor_user_code"], "Administrator")
		self.assertEqual(res["action_code"], "PUBLISH_TENDER")
		self.assertTrue(res["allowed"])
		self.assertEqual(res["required_permission"], "PERM_TENDER_PUBLISH")

	def test_sec_0410_single_denied_not_raw_exception(self) -> None:
		res = sec_api_action_availability(
			action_code="PUBLISH_TENDER",
			object_type="Tender",
			object_code="TND-0410-2",
			context={"granted_permissions": []},
		)
		self.assertTrue(res["success"])
		self.assertFalse(res["allowed"])
		self.assertEqual(res["denial_code"], "STD_AUTH_PERMISSION_DENIED")

	def test_sec_0410_single_invalid_json_context_error_envelope(self) -> None:
		res = sec_api_action_availability(
			action_code="PUBLISH_TENDER",
			object_type="Tender",
			object_code="TND-0410-3",
			context="{bad json",
		)
		self.assertFalse(res["success"])
		self.assertEqual(res["error_code"], SEC_API_PAYLOAD_INVALID)
		self.assertIn("context", (res.get("message") or "").lower())

	def test_sec_0410_batch_success(self) -> None:
		res = sec_api_action_availability_batch(
			items=[
				{
					"action_code": "CONSUME_DOM",
					"object_type": "Tender STD Generated Output",
					"object_code": "OUT-0410-A",
					"context": {"granted_permissions": ["PERM_INSTANCE_VIEW"]},
				},
				{
					"action_code": "PUBLISH_TENDER",
					"object_type": "Tender",
					"object_code": "TND-0410-B",
					"context": {"granted_permissions": []},
				},
			],
		)
		self.assertTrue(res["success"])
		self.assertEqual(len(res["items"]), 2)
		self.assertTrue(res["items"][0]["allowed"])
		self.assertFalse(res["items"][1]["allowed"])
		self.assertEqual(res["items"][1]["denial_code"], "STD_AUTH_PERMISSION_DENIED")

	def test_sec_0410_batch_empty_items_error(self) -> None:
		res = sec_api_action_availability_batch(items=[], context={})
		self.assertFalse(res["success"])
		self.assertEqual(res["error_code"], SEC_API_ITEMS_REQUIRED)

	def test_sec_0410_batch_invalid_item_shape_error(self) -> None:
		res = sec_api_action_availability_batch(items='["bad"]', context={})
		self.assertFalse(res["success"])
		self.assertEqual(res["error_code"], SEC_API_PAYLOAD_INVALID)

	def test_sec_0410_required_field_error_envelope(self) -> None:
		res = sec_api_action_availability(
			action_code="",
			object_type="Tender",
			object_code="TND-0410-REQ",
			context={},
		)
		self.assertFalse(res["success"])
		self.assertEqual(res["error_code"], SEC_API_ACTION_CODE_REQUIRED)

	def test_sec_0410_internal_error_no_stack_trace(self) -> None:
		with patch(
			"kentender_procurement.tender_management.security.action_availability.api.ActionAvailabilityService.get_action_availability",
			side_effect=RuntimeError("boom"),
		):
			res = sec_api_action_availability(
				action_code="PUBLISH_TENDER",
				object_type="Tender",
				object_code="TND-0410-ERR",
				context={"granted_permissions": ["PERM_TENDER_PUBLISH"]},
			)
		self.assertFalse(res["success"])
		self.assertEqual(res["error_code"], SEC_API_INTERNAL_ERROR)
		self.assertEqual(res["message"], "Unexpected server error.")
