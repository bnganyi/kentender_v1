# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-01 — doc 9 §7.2–7.3 action availability response contract.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p2_01_action_availability_pack_0703
"""

from __future__ import annotations

import unittest

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.action_availability.service import (
	PACK_ACTION_AVAILABILITY_V73_KEYS,
	ActionAvailabilityService,
	get_action_availability,
	pack_action_availability_v73_errors,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class TestP201PackValidator0703(unittest.TestCase):
	def test_pack_validator_flags_missing_top_level(self) -> None:
		errs = pack_action_availability_v73_errors({"action_code": "X"})
		self.assertTrue(any(e.startswith("missing_top_level:") for e in errs))

	def test_pack_validator_flags_bad_blocker(self) -> None:
		errs = pack_action_availability_v73_errors(
			{
				"action_code": "A",
				"object_type": "T",
				"object_code": "C",
				"allowed": False,
				"denial_code": "D",
				"risk_level": "Low",
				"required_permission": "P",
				"user_message": "m",
				"blockers": [{"blocker_code": "B"}],
				"confirmation_required": False,
				"reason_required": False,
			}
		)
		self.assertTrue(any("blocker[0]_missing" in e for e in errs))


class TestP201ActionAvailabilityPack0703(IntegrationTestCase):
	def setUp(self) -> None:
		RolePermissionService.ensure_matrix_seeded()

	def test_p2_01_pack_ordered_function_and_v73_keys(self) -> None:
		res = get_action_availability(
			"PUBLISH_TENDER",
			"Tender",
			"TND-P2-01-1",
			"Administrator",
			context={"granted_permissions": ["PERM_TENDER_PUBLISH"]},
		)
		self.assertEqual(pack_action_availability_v73_errors(res), [])
		for key in PACK_ACTION_AVAILABILITY_V73_KEYS:
			self.assertIn(key, res)
		self.assertIsInstance(res["blockers"], list)
		for blocker in res["blockers"]:
			self.assertIsInstance(blocker, dict)
			self.assertEqual(set(blocker.keys()), {"blocker_code", "severity", "owner_module", "required_action"})

	def test_p2_01_context_blockers_override_synthetic(self) -> None:
		res = ActionAvailabilityService.get_action_availability(
			"Administrator",
			"PUBLISH_TENDER",
			"Tender",
			"TND-P2-01-2",
			context={
				"granted_permissions": ["PERM_TENDER_PUBLISH"],
				"state_allows": False,
				"state_denial_code": DenialCode.PUBLISH_APPROVAL_REQUIRED,
				"state_message": "Blocked.",
				"availability_blockers": [
					{
						"blocker_code": "AUTH_PUBLICATION_SNAPSHOT_MISSING",
						"severity": "Critical",
						"owner_module": "STD Engine",
						"required_action": "Regenerate and bind publication snapshot.",
					}
				],
			},
		)
		self.assertEqual(pack_action_availability_v73_errors(res), [])
		self.assertFalse(res["allowed"])
		self.assertEqual(len(res["blockers"]), 1)
		self.assertEqual(res["blockers"][0]["blocker_code"], "AUTH_PUBLICATION_SNAPSHOT_MISSING")
		self.assertEqual(res["blockers"][0]["owner_module"], "STD Engine")

	def test_p2_01_reason_required_from_context(self) -> None:
		res = get_action_availability(
			"PUBLISH_TENDER",
			"Tender",
			"TND-P2-01-3",
			"Administrator",
			context={
				"granted_permissions": ["PERM_TENDER_PUBLISH"],
				"reason_required": True,
			},
		)
		self.assertEqual(pack_action_availability_v73_errors(res), [])
		self.assertTrue(res["reason_required"])
