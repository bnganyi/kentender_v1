"""CFG-CHG-002 v0.4 Phase 3 — PE Fiscal Year Context lifecycle + resolver
under the single Reference Data Manager Role model (no draft/submit/
recommend/approve chain; "Enable PE for Financial Year" is one governed
action). Covers BR-004..010 and AC-009..014 evidence for CFG-308.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_to_date, now_datetime

from kentender_core.services import reference_data_queries as queries
from kentender_core.services.reference_data_permissions import REFERENCE_DATA_MANAGER_ROLE
from kentender_core.services.reference_data_resolver import (
	resolve_authorized_contexts,
	validate_context_for_command,
)
from kentender_core.services.reference_data_transitions import (
	activate_due_contexts,
	activate_pe,
	close_context,
	close_due_contexts,
	create_fy_draft,
	create_pe_draft,
	enable_context,
	make_fy_available,
	reinstate_context,
	reopen_context,
	retire_fy,
	retire_pe,
	suspend_context,
)


class TestReferenceDataContextLifecycle(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.manager = self._user("manager")
		self.outsider = self._user("outsider")

		if not frappe.db.exists("Role", REFERENCE_DATA_MANAGER_ROLE):
			frappe.get_doc({"doctype": "Role", "role_name": REFERENCE_DATA_MANAGER_ROLE, "desk_access": 1}).insert(
				ignore_permissions=True
			)
		frappe.get_doc("User", self.manager).add_roles(REFERENCE_DATA_MANAGER_ROLE)

		# A dedicated Active PE + Available FY this test owns end to end.
		self.pe_type = self._pe_type()
		self.entity_code = f"PE-TESTCTX-{self.suffix}".upper()
		create_pe_draft(
			{
				"entity_code": self.entity_code,
				"legal_name": "Test Context Entity",
				"display_name": "Test Context Entity",
				"pe_type_code": self.pe_type,
			},
			user=self.manager,
		)
		activate_pe(self.entity_code, user=self.manager)

		self.start_year = 2200 + (int(self.suffix, 16) % 700)
		self.fy_name = f"FY-{self.start_year}-{self.start_year + 1}"
		create_fy_draft(self.start_year, user=self.manager)
		make_fy_available(self.fy_name, user=self.manager)

		self.context_name = f"CTX-{self.entity_code.removeprefix('PE-')}-{self.start_year}-{self.start_year + 1}"

	def tearDown(self):
		for doctype, filters in (
			("PE Fiscal Year Context", [["name", "=", self.context_name]]),
			("Financial Year", [["name", "=", self.fy_name]]),
			("Procuring Entity Version", [["procuring_entity", "=", self.entity_code]]),
			("Procuring Entity", [["name", "=", self.entity_code]]),
			("Audit Event", [["document_name", "in", [self.context_name, self.fy_name, self.entity_code]]]),
			("PE Type", [["name", "like", f"%{self.suffix}%"]]),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.manager, self.outsider):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _user(self, label):
		email = f"cfgpefy.ctx.{label}.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		return email

	def _pe_type(self):
		code = f"TESTCTXTYPE_{self.suffix}".upper()
		frappe.get_doc(
			{"doctype": "PE Type", "type_code": code, "label": "Test Type", "status": "Active"}
		).insert(ignore_permissions=True)
		return code

	def _enable(self, active_from=None, active_to=None):
		active_from = active_from or add_days(now_datetime(), -1)
		active_to = active_to or add_days(now_datetime(), 30)
		result = enable_context(self.entity_code, self.fy_name, active_from, active_to, user=self.manager)
		self.assertEqual(result["context"], self.context_name)
		return result

	def test_enable_requires_reference_data_manager_role(self):
		with self.assertRaises(frappe.PermissionError):
			enable_context(
				self.entity_code, self.fy_name, add_days(now_datetime(), -1), add_days(now_datetime(), 30), user=self.outsider
			)

	def test_stale_expected_version_rejected_with_version_conflict(self):
		"""AC-017/BR-016 — a command carrying a stale expected_version must be
		rejected with no partial effect; the record's real state must be untouched."""
		self._enable(active_from=add_to_date(now_datetime(), days=2))
		current = frappe.db.get_value("PE Fiscal Year Context", self.context_name, "modified")
		frappe.db.set_value("PE Fiscal Year Context", self.context_name, "closed_reason", "", update_modified=True)
		stale_version = str(current)

		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			suspend_context(self.context_name, "n/a", user=self.manager, expected_version=stale_version)
		self.assertTrue(any((m.get("title") or "") == "VERSION_CONFLICT" for m in frappe.local.message_log))

	def test_prerequisites_pe_active_fy_available(self):
		"""BR-005."""
		with self.assertRaises(frappe.ValidationError):
			enable_context(
				"PE-DOES-NOT-EXIST", self.fy_name, now_datetime(), add_days(now_datetime(), 30), user=self.manager
			)

	def test_active_to_before_active_from_rejected(self):
		"""BR-006."""
		with self.assertRaises(frappe.ValidationError):
			enable_context(
				self.entity_code, self.fy_name, now_datetime(), add_days(now_datetime(), -5), user=self.manager
			)

	def test_enable_immediate_activation(self):
		"""AC-009/AC-011 — active_from already reached activates immediately."""
		self._enable()
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Active")

	def test_core_readiness_reports_all_four_checks_ready(self):
		"""§12.6/§12.11 — Core readiness must report per-check status (PE active, FY
		available, PE type configured, timezone configured), not just one aggregate."""
		self._enable()
		detail = queries.get_pe_fy_context(self.context_name, user=self.manager)
		labels = {c["label"]: c["status"] for c in detail["core_readiness"]}
		self.assertEqual(
			labels,
			{
				"Procuring Entity active": "Ready",
				"Financial Year available": "Ready",
				"PE type configured": "Ready",
				"Timezone configured": "Ready",
			},
		)

	def test_future_active_from_stays_scheduled_until_due(self):
		"""AC-011 — a future context remains Scheduled until active_from."""
		self._enable(active_from=add_to_date(now_datetime(), days=2), active_to=add_days(now_datetime(), 30))
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Scheduled")

		activate_due_contexts()  # not due yet
		ctx.reload()
		self.assertEqual(ctx.context_status, "Scheduled")

		frappe.db.set_value("PE Fiscal Year Context", self.context_name, "active_from", add_days(now_datetime(), -1))
		activate_due_contexts()
		ctx.reload()
		self.assertEqual(ctx.context_status, "Active")

	def test_duplicate_pe_fy_pair_rejected(self):
		"""BR-001."""
		self._enable()
		with self.assertRaises(frappe.ValidationError):
			enable_context(self.entity_code, self.fy_name, now_datetime(), add_days(now_datetime(), 30), user=self.manager)

	def test_close_requires_reason_and_acknowledgement(self):
		"""AC-015."""
		self._enable()

		with self.assertRaises(frappe.ValidationError):
			close_context(self.context_name, "", acknowledged=True, user=self.manager)
		with self.assertRaises(frappe.ValidationError):
			close_context(self.context_name, "Done for the year", acknowledged=False, user=self.manager)

		close_context(self.context_name, "Done for the year", acknowledged=True, user=self.manager)
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Closed")
		self.assertEqual(ctx.closed_by, self.manager)

		# AC-015 — disappears from new-work selectors; the record itself is untouched.
		result = resolve_authorized_contexts(self.manager)
		self.assertNotIn(self.context_name, {c["context_id"] for c in result["contexts"]})
		self.assertTrue(frappe.db.exists("PE Fiscal Year Context", self.context_name))

	def test_auto_close_due_contexts(self):
		"""AC §6.3 'ACTIVE | Reach active_to | CLOSED' — automated, scheduler audit."""
		self._enable(active_to=add_days(now_datetime(), 30))
		frappe.db.set_value("PE Fiscal Year Context", self.context_name, "active_to", add_days(now_datetime(), -1))

		close_due_contexts()
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Closed")
		self.assertEqual(ctx.closed_by, "Administrator")

	def test_reopen_is_one_governed_action_no_multi_stage_chain(self):
		"""AC-016 — one action with a reason and new dates, not a propose/
		recommend/approve chain."""
		self._enable()
		close_context(self.context_name, "Closing for reopen test", acknowledged=True, user=self.manager)

		with self.assertRaises(frappe.PermissionError):
			reopen_context(
				self.context_name,
				"Need to reopen",
				add_days(now_datetime(), -1),
				add_days(now_datetime(), 30),
				user=self.outsider,
			)

		reopen_context(
			self.context_name, "Need to reopen", add_days(now_datetime(), -1), add_days(now_datetime(), 30), user=self.manager
		)
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Active")

	def test_reinstate_after_suspend(self):
		self._enable()
		suspend_context(self.context_name, "Under review", user=self.manager)
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Suspended")

		reinstate_context(self.context_name, user=self.manager)
		ctx.reload()
		self.assertEqual(ctx.context_status, "Active")

	def test_resolver_returns_active_context_for_authorized_actor_only(self):
		"""AC-012/AC-013 — Reference Data Manager sees the context; an unrelated
		user gets none."""
		self._enable()

		result = resolve_authorized_contexts(self.manager)
		context_ids = {c["context_id"] for c in result["contexts"]}
		self.assertIn(self.context_name, context_ids)

		outsider_result = resolve_authorized_contexts(self.outsider)
		self.assertEqual(outsider_result["contexts"], [])
		self.assertIsNone(outsider_result["auto_selected"])

	def test_list_query_never_returns_out_of_scope_contexts(self):
		"""AC-022 — there is no broad "all configured contexts" API a downstream
		module could call client-side; list_pe_fy_contexts scopes exactly like the
		resolver does."""
		self._enable()

		as_manager = queries.list_pe_fy_contexts(user=self.manager)
		self.assertIn(self.context_name, {r["context_id"] for r in as_manager["rows"]})

		as_outsider = queries.list_pe_fy_contexts(user=self.outsider)
		self.assertEqual(as_outsider["rows"], [])

	def test_validate_context_for_command_rejects_non_active(self):
		self._enable(active_from=add_to_date(now_datetime(), days=2))
		with self.assertRaises(frappe.ValidationError):
			validate_context_for_command(self.outsider, self.context_name)

	def test_current_and_next_fy_contexts_both_active_for_one_pe(self):
		"""AC-012 — a PE may have two simultaneously Active contexts (current and
		next FY); the authorized selector returns both, not just one."""
		second_start_year = self.start_year + 1
		second_fy_name = f"FY-{second_start_year}-{second_start_year + 1}"
		create_fy_draft(second_start_year, user=self.manager)
		make_fy_available(second_fy_name, user=self.manager)
		try:
			self._enable()

			second_context_name = f"CTX-{self.entity_code.removeprefix('PE-')}-{second_start_year}-{second_start_year + 1}"
			enable_context(self.entity_code, second_fy_name, now_datetime(), add_days(now_datetime(), 400), user=self.manager)

			result = resolve_authorized_contexts(self.manager)
			context_ids = {c["context_id"] for c in result["contexts"]}
			self.assertIn(self.context_name, context_ids)
			self.assertIn(second_context_name, context_ids)
			self.assertIsNone(result["auto_selected"])  # more than one — no single auto-selection
		finally:
			for doctype, filters in (
				("PE Fiscal Year Context", [["financial_year", "=", second_fy_name]]),
				("Financial Year", [["name", "=", second_fy_name]]),
				("Audit Event", [["document_name", "like", f"%{second_fy_name}%"]]),
			):
				for name in frappe.get_all(doctype, filters=filters, pluck="name"):
					frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def test_remembered_context_suspended_after_load_is_revalidated_away(self):
		"""AC-014 — a remembered context suspended after the caller's page load must
		be dropped on the next read, not silently kept because it "was valid a
		moment ago"."""
		self._enable()

		before = resolve_authorized_contexts(self.manager, remembered_context=self.context_name)
		self.assertTrue(before["remembered_context_valid"])
		self.assertIn(self.context_name, {c["context_id"] for c in before["contexts"]})

		suspend_context(self.context_name, "Under review", user=self.manager)

		after = resolve_authorized_contexts(self.manager, remembered_context=self.context_name)
		self.assertFalse(after["remembered_context_valid"])
		self.assertNotIn(self.context_name, {c["context_id"] for c in after["contexts"]})

		with self.assertRaises(frappe.ValidationError):
			validate_context_for_command(self.manager, self.context_name)

	def test_validate_context_for_command_out_of_scope_does_not_disclose_existence(self):
		"""AC-013 — a genuinely non-existent context and a real-but-not-Active
		context must fail with the exact same safe message/title."""
		self._enable(active_from=add_to_date(now_datetime(), days=2))  # -> Scheduled, not Active

		def _fail(fn):
			frappe.local.message_log = []
			with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
				fn()
			self.assertEqual(len(frappe.local.message_log), 1)
			return frappe.local.message_log[0]

		not_active = _fail(lambda: validate_context_for_command(self.outsider, self.context_name))
		nonexistent = _fail(lambda: validate_context_for_command(self.outsider, "CTX-DOES-NOT-EXIST"))
		self.assertEqual(not_active["title"], nonexistent["title"])
		self.assertEqual(not_active["message"], nonexistent["message"])

	def test_retire_pe_blocked_while_context_active(self):
		"""Closes the loop from Phase 1's deferred retire_pe() guard."""
		self._enable()
		with self.assertRaises(frappe.ValidationError):
			retire_pe(self.entity_code, "test", frappe.utils.today(), user=self.manager)

	def test_retire_fy_blocked_while_context_active(self):
		self._enable()
		with self.assertRaises(frappe.ValidationError):
			retire_fy(self.fy_name, user=self.manager)
