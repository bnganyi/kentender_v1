# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-PERM Wave 2 — roles, scope, transitions, admin gate, segregation."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_permissions import (
	ERR_ADMIN_ROLE,
	ERR_SCOPE,
	ERR_SEGREGATION,
	ROLE_BUSINESS,
	ROLE_PAA,
	ROLE_REQUESTER,
	ROLE_VIEWER,
	assert_business_approver_segregation,
	assert_can_perform_stage_action,
	assert_demand_scope,
	can_final_approve,
	ensure_demand_roles,
	operational_roles,
)
from kentender_procurement.demands.services.demand_transitions import (
	ERR_INVALID_TRANSITION,
	preview_transition,
	resolve_transition,
)


def _ensure_user(email: str, roles: list[str], *, replace_roles: bool = False) -> str:
	ensure_demand_roles()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	if replace_roles:
		user.set("roles", [])
	existing = {r.role for r in user.roles}
	for role in roles:
		if role not in existing:
			user.append("roles", {"role": role})
	user.save(ignore_permissions=True)
	frappe.db.commit()
	return email


def _assert_error_code(exc: BaseException, code: str) -> None:
	self_msg = str(exc)
	assert code in self_msg, f"expected {code!r} in {self_msg!r}"


class TestDemandPermissionsWave2(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_demand_roles_exist(self) -> None:
		frappe.set_user("Administrator")
		ensure_demand_roles()
		for role in (
			"Requester",
			"Business Approver",
			"Procurement Approval Authority",
			"Budget Officer",
			"Planning Officer",
			"Demand Viewer",
		):
			self.assertTrue(frappe.db.exists("Role", role), role)

	def test_doctype_permissions_include_operational_roles(self) -> None:
		frappe.set_user("Administrator")
		meta = frappe.get_meta("Demand")
		roles = {p.role for p in meta.permissions}
		self.assertIn(ROLE_REQUESTER, roles)
		self.assertIn(ROLE_BUSINESS, roles)
		self.assertIn(ROLE_PAA, roles)
		self.assertIn("Budget Officer", roles)
		self.assertIn("Planning Officer", roles)
		self.assertIn(ROLE_VIEWER, roles)

	def test_standard_submit_transition(self) -> None:
		result = resolve_transition("Draft", "Request Preparation", "Submit")
		self.assertEqual(result.status, "In Review")
		self.assertEqual(result.stage, "Business Review")

	def test_invalid_transition_stable_code(self) -> None:
		with self.assertRaises(frappe.ValidationError) as ctx:
			resolve_transition("Approved", "Complete", "Submit")
		_assert_error_code(ctx.exception, ERR_INVALID_TRANSITION)

	def test_admin_without_operational_role_cannot_approve(self) -> None:
		"""DIA-AC-013 / DEM-PERM-004."""
		user = _ensure_user(
			"dem-sysadmin-wave2@example.com",
			["System Manager"],
			replace_roles=True,
		)
		self.assertFalse(can_final_approve(user))
		self.assertNotIn(ROLE_PAA, operational_roles(user))
		with self.assertRaises(frappe.PermissionError) as ctx:
			assert_can_perform_stage_action("Final Approval", "Approve", user=user)
		_assert_error_code(ctx.exception, ERR_ADMIN_ROLE)

	def test_paa_can_approve_action(self) -> None:
		user = _ensure_user("dem-paa-wave2@example.com", [ROLE_PAA])
		assert_can_perform_stage_action("Final Approval", "Approve", user=user)
		result = preview_transition(
			status="In Review",
			stage="Final Approval",
			action="Approve",
			user=user,
			check_scope=False,
		)
		self.assertEqual(result.status, "Approved")
		self.assertEqual(result.stage, "Complete")

	def test_requester_cannot_business_support_same_demand(self) -> None:
		"""DEM-PERM-005 segregation."""
		user = _ensure_user("dem-req-wave2@example.com", [ROLE_REQUESTER, ROLE_BUSINESS])
		with self.assertRaises(frappe.PermissionError) as ctx:
			assert_business_approver_segregation(requester=user, actor=user)
		_assert_error_code(ctx.exception, ERR_SEGREGATION)

	def test_small_entity_exception_allows_same_actor(self) -> None:
		user = _ensure_user("dem-small-wave2@example.com", [ROLE_REQUESTER, ROLE_BUSINESS])
		assert_business_approver_segregation(
			requester=user, actor=user, small_entity_exception=True
		)

	def test_preview_blocks_segregation_on_business_support(self) -> None:
		user = _ensure_user("dem-both-wave2@example.com", [ROLE_BUSINESS, ROLE_REQUESTER])
		with self.assertRaises(frappe.PermissionError) as ctx:
			preview_transition(
				status="In Review",
				stage="Business Review",
				action="Support",
				requester=user,
				user=user,
				check_scope=False,
			)
		_assert_error_code(ctx.exception, ERR_SEGREGATION)

	def test_scope_denied_without_user_scope_assignment(self) -> None:
		"""DEM-PERM-002 — role without entity/OU scope grants no record access."""
		user = _ensure_user("dem-noscope-wave2@example.com", [ROLE_REQUESTER])
		with self.assertRaises(frappe.PermissionError) as ctx:
			assert_demand_scope(
				procuring_entity="PE-DOES-NOT-EXIST",
				owner_org_unit="OU-DOES-NOT-EXIST",
				user=user,
				require_write=True,
			)
		_assert_error_code(ctx.exception, ERR_SCOPE)
