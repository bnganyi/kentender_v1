"""AUD-XC-026 — the legacy AUTH-G04 engine (Operational Scope Assignment,
Capability Profile, Workflow Queue / Membership / Routing Rule / Task,
Authorization Delegation, Separation of Duties Rule) authorises nothing and
takes no writes (AUTH-ADR-001 §11.3 step 9, §11.5). The rows that exist are
kept for the migration evidence; `User Responsibility Assignment` is the only
authority record.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_legacy_authorization_retired
"""

from __future__ import annotations

import importlib
import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.services import authorization_policy as policy
from kentender_core.services.command_write_guard import CommandWriteError, fixture_insert, purge_doc

LEGACY = (
	"Operational Scope Assignment",
	"Capability Profile",
	"Workflow Queue",
	"Workflow Queue Membership",
	"Workflow Routing Rule",
	"Workflow Task",
	"Authorization Delegation",
	"Separation of Duties Rule",
)


class TestLegacyEngineIsRetired(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.suffix = uuid4().hex[:8]
		self.pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self.user = f"kt.test.legacy.{self.suffix}@example.test"
		frappe.get_doc({"doctype": "User", "email": self.user, "first_name": "Legacy", "enabled": 1, "send_welcome_email": 0}).insert(ignore_permissions=True)
		self.addCleanup(self._remove_user)
		self.addCleanup(frappe.set_user, "Administrator")

	def _remove_user(self) -> None:
		frappe.set_user("Administrator")
		for contact in frappe.get_all("Contact Email", filters={"email_id": self.user}, pluck="parent"):
			frappe.delete_doc("Contact", contact, force=1, ignore_permissions=True)
		frappe.delete_doc("User", self.user, force=1, ignore_permissions=True)

	def _legacy_rows(self) -> None:
		"""An Active assignment of an Active profile: what the old engine authorised from."""
		profile = fixture_insert(frappe.get_doc({
			"doctype": "Capability Profile", "profile_id": f"CAP-RET-{self.suffix}", "profile_name": "Retired", "capabilities": json.dumps(["plan.view"]),
			"allows_entity_wide": 1, "status": "Active", "effective_from": add_days(now_datetime(), -1), "concurrency_token": uuid4().hex,
		}))
		self.addCleanup(purge_doc, "Capability Profile", profile.name)
		assignment = fixture_insert(frappe.get_doc({
			"doctype": "Operational Scope Assignment", "assignment_id": f"OSA-RET-{self.suffix}", "user_id": self.user, "capability_profile_id": profile.name,
			"procuring_entity_id": self.pe, "effective_from": add_days(now_datetime(), -1), "status": "Active", "assigned_by": "Administrator",
			"assigned_at": now_datetime(), "concurrency_token": uuid4().hex,
		}))
		self.addCleanup(purge_doc, "Operational Scope Assignment", assignment.name)

	def test_an_active_legacy_assignment_authorises_nothing(self):
		self._legacy_rows()
		decision = policy.evaluate_capability(self.user, "plan.view", policy.ResourceContext("Procuring Entity", self.pe, self.pe))
		self.assertFalse(decision.allowed)
		self.assertEqual(decision.reason_code, "LEGACY_AUTHORIZATION_RETIRED")
		with self.assertRaises(frappe.PermissionError):
			policy.require_capability(self.user, "plan.view", policy.ResourceContext("Procuring Entity", self.pe, self.pe))

	def test_no_legacy_doctype_can_be_created_changed_or_deleted_by_anyone(self):
		self._legacy_rows()
		name = frappe.db.get_value("Operational Scope Assignment", {"user_id": self.user}, "name")
		for doctype in LEGACY:
			for permission in frappe.get_meta(doctype).permissions:
				self.assertFalse(permission.write or permission.create or permission.delete, f"{doctype}: {permission.role}")
			values = {"doctype": doctype}
			autoname = frappe.get_meta(doctype).autoname or ""
			if autoname.startswith("field:"):
				values[autoname.removeprefix("field:")] = f"RET-{self.suffix}"
			with self.assertRaises(CommandWriteError, msg=f"{doctype} insert") as inserted:
				frappe.get_doc(values).insert(ignore_permissions=True)
			self.assertEqual(inserted.exception.code, "COMMAND_ONLY_WRITE")
		with self.assertRaises(CommandWriteError):
			frappe.client.set_value("Operational Scope Assignment", name, "status", "Ended")
		with self.assertRaises(CommandWriteError):
			frappe.client.delete("Operational Scope Assignment", name)
		self.assertEqual(frappe.db.get_value("Operational Scope Assignment", name, "status"), "Active")

	def test_the_commands_that_wrote_or_authorised_are_gone(self):
		from kentender_core import authorization_api
		from kentender_core.services import my_work

		for removed in ("add_assignment", "revise_routing_rule"):
			self.assertFalse(hasattr(authorization_api, removed), removed)
		self.assertFalse(hasattr(my_work, "claim_my_work_task"))
		for module in ("workflow_tasks", "workflow_routing"):
			with self.assertRaises(ImportError, msg=module):
				importlib.import_module(f"kentender_core.services.{module}")

	def test_the_read_only_inspection_still_works(self):
		self._legacy_rows()
		from kentender_core.services.authorization_administration import get_user_operational_access

		view = get_user_operational_access(self.user, user="Administrator")
		self.assertEqual(len(view["assignments"]), 1)
