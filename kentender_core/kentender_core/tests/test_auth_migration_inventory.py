"""AUTH-ADR-001 Phase 1 — inventory/reconciliation classification (§12.1).

Read-only: seeds one synthetic user per classification bucket and asserts
`classify_user` buckets each correctly, using an injected role_map so the
test is independent of the real (still-evolving) capability-to-Role mapping
table in kentender_core.scripts.auth_migration_inventory.
"""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.scripts.auth_migration_inventory import (
	AMBIGUOUS,
	CONFLICTING_SCOPE,
	CUSTOM_AUTHORITY_WITHOUT_ROLE,
	EXPIRED_OR_INACTIVE,
	MATCHED,
	ROLE_WITHOUT_CUSTOM_AUTHORITY,
	classify_user,
)

GLOBAL_ROLE = "AUTH-TEST-Central Reference Data Steward"
PE_SCOPED_ROLE = "AUTH-TEST-Accounting Officer"


class TestAuthMigrationInventory(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for role in (GLOBAL_ROLE, PE_SCOPED_ROLE):
			if not frappe.db.exists("Role", role):
				frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)

	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self.other_pe = frappe.get_all("Procuring Entity", pluck="name", limit=2)[-1]
		self.role_map = {
			f"GLOBAL-{self.suffix}": (GLOBAL_ROLE, "global_central"),
			f"PESCOPED-{self.suffix}": (PE_SCOPED_ROLE, "pe_scoped"),
		}
		self._users: list[str] = []
		self._profiles: list[str] = []
		self._assignments: list[str] = []

	def tearDown(self):
		for name in self._assignments:
			frappe.delete_doc("Operational Scope Assignment", name, force=True, ignore_permissions=True)
		for name in self._profiles:
			frappe.delete_doc("Capability Profile", name, force=True, ignore_permissions=True)
		for user in self._users:
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)

	def _user(self, label: str) -> str:
		email = f"auth-inv-{label}-{self.suffix}@kentender.test"
		frappe.get_doc({"doctype": "User", "email": email, "first_name": label, "send_welcome_email": 0}).insert(ignore_permissions=True)
		self._users.append(email)
		return email

	def _profile(self, label: str, capabilities: list[str], *, status: str = "Active", effective_from=None) -> str:
		doc = frappe.get_doc({
			"doctype": "Capability Profile",
			"profile_id": f"{label}-{self.suffix}",
			"profile_name": label,
			"capabilities": json.dumps(capabilities),
			"allows_entity_wide": 1,
			"status": status,
			"effective_from": effective_from or add_days(now_datetime(), -1),
			"concurrency_token": uuid4().hex,
		}).insert(ignore_permissions=True)
		self._profiles.append(doc.name)
		return doc.name

	def _assignment(self, user: str, profile_id: str, *, procuring_entity: str | None = None) -> str:
		doc = frappe.get_doc({
			"doctype": "Operational Scope Assignment",
			"assignment_id": f"OSA-{uuid4().hex[:8]}",
			"user_id": user,
			"capability_profile_id": profile_id,
			"procuring_entity_id": procuring_entity or self.pe,
			"effective_from": add_days(now_datetime(), -1),
			"status": "Active",
			"assigned_by": "Administrator",
			"assigned_at": now_datetime(),
			"concurrency_token": uuid4().hex,
		}).insert(ignore_permissions=True)
		self._assignments.append(doc.name)
		return doc.name

	def test_matched_global_central(self):
		user = self._user("matched")
		frappe.get_doc("User", user).add_roles(GLOBAL_ROLE)
		profile = self._profile("GLOBAL", ["reference_data.pe.create_draft"])
		self._assignment(user, profile)

		result = classify_user(user, role_map=self.role_map)

		self.assertEqual(result["bucket"], MATCHED)

	def test_role_without_custom_authority_amina_shape(self):
		"""User holds the visible Role but their only active grant maps elsewhere."""
		user = self._user("amina-shape")
		frappe.get_doc("User", user).add_roles(GLOBAL_ROLE)
		other_profile = self._profile("PESCOPED", ["reference_data.context.approve"])
		self._assignment(user, other_profile, procuring_entity=self.pe)
		frappe.get_doc({
			"doctype": "User Permission",
			"user": user,
			"allow": "Procuring Entity",
			"for_value": self.pe,
		}).insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.db.delete("User Permission", {"user": user}))

		result = classify_user(user, role_map=self.role_map)

		self.assertEqual(result["bucket"], ROLE_WITHOUT_CUSTOM_AUTHORITY)

	def test_custom_authority_without_role(self):
		user = self._user("no-role")
		profile = self._profile("PESCOPED", ["reference_data.context.approve"])
		self._assignment(user, profile, procuring_entity=self.pe)
		frappe.get_doc({
			"doctype": "User Permission",
			"user": user,
			"allow": "Procuring Entity",
			"for_value": self.pe,
		}).insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.db.delete("User Permission", {"user": user}))

		result = classify_user(user, role_map=self.role_map)

		self.assertEqual(result["bucket"], CUSTOM_AUTHORITY_WITHOUT_ROLE)

	def test_conflicting_scope(self):
		user = self._user("conflict")
		frappe.get_doc("User", user).add_roles(PE_SCOPED_ROLE)
		profile = self._profile("PESCOPED", ["reference_data.context.approve"])
		self._assignment(user, profile, procuring_entity=self.pe)
		# Native User Permission scopes a DIFFERENT PE than the OSA grant.
		frappe.get_doc({
			"doctype": "User Permission",
			"user": user,
			"allow": "Procuring Entity",
			"for_value": self.other_pe,
		}).insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.db.delete("User Permission", {"user": user}))

		result = classify_user(user, role_map=self.role_map)

		self.assertEqual(result["bucket"], CONFLICTING_SCOPE)

	def test_expired_or_inactive(self):
		user = self._user("expired")
		frappe.get_doc("User", user).add_roles(GLOBAL_ROLE)
		profile = self._profile(
			"GLOBAL",
			["reference_data.pe.create_draft"],
			status="Ended",
		)
		self._assignment(user, profile)

		result = classify_user(user, role_map=self.role_map)

		self.assertEqual(result["bucket"], EXPIRED_OR_INACTIVE)

	def test_ambiguous_unmapped_profile(self):
		user = self._user("ambiguous")
		profile = self._profile("UNMAPPED", ["budget.approve"])
		self._assignment(user, profile)

		result = classify_user(user, role_map=self.role_map)

		self.assertEqual(result["bucket"], AMBIGUOUS)

	def test_no_authority_at_all_is_unclassified(self):
		user = self._user("nothing")

		result = classify_user(user, role_map=self.role_map)

		self.assertIsNone(result["bucket"])
		self.assertEqual(result["findings"], [])
