# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-02 — doc 9 §7.4 action codes registered and availability is deterministic.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p2_02_pack_74_action_codes
"""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.action_availability.catalog import (
	PACK_SECTION_7_4_ACTION_CODES,
)
from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
	pack_action_availability_v73_errors,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
	tm2_doc9_section_74_action_codes,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class TestP202Pack74ActionCodes(IntegrationTestCase):
	_FIXTURE_OBJECT_TYPE = "TM2 Tender"
	_FIXTURE_OBJECT_CODE = "TND-P202-FIXTURE-001"

	def setUp(self) -> None:
		RolePermissionService.ensure_matrix_seeded()

	def test_p2_02_pack_74_codes_match_registry_export(self) -> None:
		self.assertEqual(PACK_SECTION_7_4_ACTION_CODES, tm2_doc9_section_74_action_codes())

	def test_p2_02_each_code_registered(self) -> None:
		missing = [ac for ac in sorted(PACK_SECTION_7_4_ACTION_CODES) if spec_for_action(ac) is None]
		self.assertEqual(missing, [])

	def test_p2_02_fixture_tender_allow_then_deny(self) -> None:
		actor = "Administrator"
		for ac in sorted(PACK_SECTION_7_4_ACTION_CODES):
			spec = spec_for_action(ac)
			self.assertIsNotNone(spec, msg=ac)
			assert spec is not None
			perm = spec.required_permission
			ctx_allow = {"granted_permissions": [perm]}
			res_ok = get_action_availability(
				ac,
				self._FIXTURE_OBJECT_TYPE,
				self._FIXTURE_OBJECT_CODE,
				actor,
				context=ctx_allow,
			)
			self.assertEqual(
				pack_action_availability_v73_errors(res_ok),
				[],
				msg=f"{ac}: invalid §7.3 shape when allowed",
			)
			self.assertTrue(res_ok["allowed"], msg=f"{ac}: expected allow with {perm}")
			self.assertEqual(res_ok["action_code"], ac)
			self.assertEqual(res_ok["object_type"], self._FIXTURE_OBJECT_TYPE)
			self.assertEqual(res_ok["object_code"], self._FIXTURE_OBJECT_CODE)
			self.assertEqual(res_ok["required_permission"], perm)

			res_den = get_action_availability(
				ac,
				self._FIXTURE_OBJECT_TYPE,
				self._FIXTURE_OBJECT_CODE,
				actor,
				context={"granted_permissions": []},
			)
			self.assertFalse(res_den["allowed"], msg=f"{ac}: expected deny without grants")
			self.assertEqual(res_den["required_permission"], perm)
