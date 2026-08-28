"""AUTH-ADR-001 — the native Frappe Role + User Permission decision engine.

Read-only decision function tests; SoD/segregation stays a caller-owned
domain check (each domain keeps its own Separation of Duties Rule wiring —
see AUTH-ADR-001 §10), so it's exercised via require_role_capability's
sod_blocked passthrough here rather than reimplemented in this module.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import authorization_role_registry as registry
from kentender_core.services.authorization_native import (
	AUTH_ROLE_REQUIRED,
	AUTH_SCOPE_REQUIRED,
	AUTH_SEGREGATION_BLOCKED,
	evaluate_role_capability,
	require_role_capability,
)
from kentender_core.services.authorization_policy import ResourceContext
from kentender_core.services.authorization_role_registry import ensure_roles

# No live capability maps to a global_central Role today (Reference Data
# Manager, the only global_central Role, is checked directly — not through
# this capability-string map, per CFG-CHG-002 v0.4/AUTH-AC-019). The engine
# must still support the classification correctly for any future domain that
# uses it, so this test-only capability exercises that code path without
# fabricating a fake production capability.
GLOBAL_CAP = "test.global_central.probe"
GLOBAL_CAP_ROLE = "Reference Data Manager"
PE_SCOPED_CAP = "authorization.task.reassign"  # -> KenTender Task Administrator, pe_fy_scoped


class TestAuthorizationNative(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_roles()
		registry.CAPABILITY_ROLE_MAP[GLOBAL_CAP] = GLOBAL_CAP_ROLE

	@classmethod
	def tearDownClass(cls):
		registry.CAPABILITY_ROLE_MAP.pop(GLOBAL_CAP, None)
		super().tearDownClass()

	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.user = f"auth-native-{self.suffix}@kentender.test"
		frappe.get_doc({"doctype": "User", "email": self.user, "first_name": "Native", "send_welcome_email": 0}).insert(ignore_permissions=True)
		self.pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		contexts = frappe.get_all("PE Fiscal Year Context", pluck="name", limit=2)
		self.ctx_a = contexts[0]
		self.ctx_b = contexts[-1] if len(contexts) > 1 else contexts[0]

	def tearDown(self):
		frappe.delete_doc("User", self.user, force=True, ignore_permissions=True)

	def test_no_role_denies(self):
		resource = ResourceContext("Procuring Entity", self.pe, self.pe)
		allowed, reason = evaluate_role_capability(self.user, GLOBAL_CAP, resource)
		self.assertFalse(allowed)
		self.assertEqual(reason, AUTH_ROLE_REQUIRED)

	def test_unmapped_capability_denies(self):
		resource = ResourceContext("Procuring Entity", self.pe, self.pe)
		allowed, reason = evaluate_role_capability(self.user, "no.such.capability", resource)
		self.assertFalse(allowed)
		self.assertEqual(reason, AUTH_ROLE_REQUIRED)

	def test_guest_denies(self):
		resource = ResourceContext("Procuring Entity", self.pe, self.pe)
		allowed, reason = evaluate_role_capability("Guest", GLOBAL_CAP, resource)
		self.assertFalse(allowed)
		self.assertEqual(reason, AUTH_ROLE_REQUIRED)

	def test_administrator_has_no_implicit_business_role(self):
		"""AUTH-ADR-001 §5.3/AUTH-AC-012 — frappe.get_roles('Administrator') is a
		real framework quirk that returns every Role in the system regardless of
		actual assignment; the engine must not let that stand in for a genuine
		business-Role grant."""
		resource = ResourceContext("Procuring Entity", self.pe, self.pe)
		allowed, reason = evaluate_role_capability("Administrator", GLOBAL_CAP, resource)
		self.assertFalse(allowed)
		self.assertEqual(reason, AUTH_ROLE_REQUIRED)

	def test_global_central_role_allows_without_scope(self):
		frappe.get_doc("User", self.user).add_roles(GLOBAL_CAP_ROLE)
		resource = ResourceContext("Procuring Entity", self.pe, self.pe)
		allowed, reason = evaluate_role_capability(self.user, GLOBAL_CAP, resource)
		self.assertTrue(allowed)
		self.assertEqual(reason, "ALLOW")

	def test_pe_fy_scoped_role_without_scope_grant_denies(self):
		frappe.get_doc("User", self.user).add_roles("KenTender Task Administrator")
		resource = ResourceContext("PE Fiscal Year Context", self.ctx_a, self.pe, pe_fy_context_id=self.ctx_a)
		allowed, reason = evaluate_role_capability(self.user, PE_SCOPED_CAP, resource)
		self.assertFalse(allowed)
		self.assertEqual(reason, AUTH_SCOPE_REQUIRED)

	def test_pe_fy_scoped_role_with_matching_scope_allows(self):
		frappe.get_doc("User", self.user).add_roles("KenTender Task Administrator")
		frappe.get_doc({"doctype": "User Permission", "user": self.user, "allow": "PE Fiscal Year Context", "for_value": self.ctx_a}).insert(ignore_permissions=True)
		try:
			resource = ResourceContext("PE Fiscal Year Context", self.ctx_a, self.pe, pe_fy_context_id=self.ctx_a)
			allowed, reason = evaluate_role_capability(self.user, PE_SCOPED_CAP, resource)
			self.assertTrue(allowed)
			self.assertEqual(reason, "ALLOW")
		finally:
			frappe.db.delete("User Permission", {"user": self.user})

	def test_pe_fy_scoped_role_with_mismatched_scope_denies(self):
		frappe.get_doc("User", self.user).add_roles("KenTender Task Administrator")
		frappe.get_doc({"doctype": "User Permission", "user": self.user, "allow": "PE Fiscal Year Context", "for_value": self.ctx_b}).insert(ignore_permissions=True)
		try:
			resource = ResourceContext("PE Fiscal Year Context", self.ctx_a, self.pe, pe_fy_context_id=self.ctx_a)
			allowed, reason = evaluate_role_capability(self.user, PE_SCOPED_CAP, resource)
			self.assertFalse(allowed)
			self.assertEqual(reason, AUTH_SCOPE_REQUIRED)
		finally:
			frappe.db.delete("User Permission", {"user": self.user})

	def test_amina_hassan_shape_role_without_matching_capability_denies(self):
		"""Holding an unrelated reference-data Role must not grant this capability —
		the exact defect AUTH-ADR-001 was written to fix."""
		frappe.get_doc("User", self.user).add_roles(GLOBAL_CAP_ROLE)
		resource = ResourceContext("PE Fiscal Year Context", self.ctx_a, self.pe, pe_fy_context_id=self.ctx_a)
		allowed, reason = evaluate_role_capability(self.user, PE_SCOPED_CAP, resource)
		self.assertFalse(allowed)
		self.assertEqual(reason, AUTH_ROLE_REQUIRED)

	def test_require_role_capability_raises_permission_error_with_reason_title(self):
		resource = ResourceContext("Procuring Entity", self.pe, self.pe)
		with self.assertRaises(frappe.PermissionError):
			require_role_capability(self.user, GLOBAL_CAP, resource)
		self.assertTrue(frappe.local.message_log)
		self.assertEqual(frappe.local.message_log[-1].get("title"), AUTH_ROLE_REQUIRED)
		frappe.local.message_log = []

	def test_require_role_capability_allows_when_role_and_scope_match(self):
		frappe.get_doc("User", self.user).add_roles(GLOBAL_CAP_ROLE)
		resource = ResourceContext("Procuring Entity", self.pe, self.pe)
		require_role_capability(self.user, GLOBAL_CAP, resource)  # must not raise

	def test_require_role_capability_sod_blocked_passthrough(self):
		frappe.get_doc("User", self.user).add_roles(GLOBAL_CAP_ROLE)
		resource = ResourceContext("Procuring Entity", self.pe, self.pe)
		with self.assertRaises(frappe.PermissionError) as ctx:
			require_role_capability(self.user, GLOBAL_CAP, resource, sod_blocked=True)
		self.assertEqual(frappe.local.message_log[-1].get("title"), AUTH_SEGREGATION_BLOCKED)
		frappe.local.message_log = []
