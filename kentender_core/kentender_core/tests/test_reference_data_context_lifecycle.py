"""CFG-CHG-002 Phase 3 — PE Fiscal Year Context lifecycle + resolver.
Covers BR-004..010 and AC-009..014 evidence for CFG-308.
"""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_to_date, now_datetime

from kentender_core.services import reference_data_permissions as perm
from kentender_core.services.reference_data_resolver import (
	resolve_authorized_contexts,
	validate_context_for_command,
)
from kentender_core.services import reference_data_queries as queries
from kentender_core.services.reference_data_transitions import (
	activate_due_contexts,
	approve_context,
	approve_context_reopen,
	close_context,
	close_due_contexts,
	create_context_draft,
	create_fy_draft,
	create_pe_draft,
	recommend_context,
	recommend_context_reopen,
	propose_context_reopen,
	retire_fy,
	retire_pe,
	submit_context,
	submit_fy,
	suspend_context,
	approve_fy,
	approve_activate_pe,
	submit_pe,
)


class TestReferenceDataContextLifecycle(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.steward = self._user("steward")
		self.reviewer = self._user("reviewer")
		self.ao = self._user("ao")
		self.outsider = self._user("outsider")

		# A dedicated Active PE + Available FY this test owns end to end (not the
		# shared seed fixture), so context creation prerequisites are exact.
		self.pe_type = self._pe_type()
		self.pe_steward = self._user("pe_steward")
		self.pe_approver = self._user("pe_approver")
		pe_create_profile = self._profile("PECREATE", [perm.PE_CREATE_DRAFT])
		pe_approve_profile = self._profile("PEAPPROVE", [perm.PE_APPROVE_ACTIVATE, perm.PE_RETIRE])
		anchor_pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self._assign(self.pe_steward, pe_create_profile, anchor_pe)
		self._sod_rule("PE", perm.PE_CREATE_DRAFT, perm.PE_APPROVE_ACTIVATE)
		self.entity_code = f"PE-TESTCTX-{self.suffix}".upper()
		create_pe_draft(
			{
				"entity_code": self.entity_code,
				"legal_name": "Test Context Entity",
				"display_name": "Test Context Entity",
				"pe_type_code": self.pe_type,
			},
			user=self.pe_steward,
		)
		self._assign(self.pe_steward, pe_create_profile, self.entity_code)
		self._assign(self.pe_approver, pe_approve_profile, self.entity_code)
		submit_pe(self.entity_code, user=self.pe_steward)
		approve_activate_pe(self.entity_code, user=self.pe_approver)

		fy_create_profile = self._profile("FYCREATE", [perm.FY_CREATE_DRAFT])
		fy_approve_profile = self._profile("FYAPPROVE", [perm.FY_APPROVE_AVAILABLE, perm.FY_RETIRE])
		self._assign(self.pe_steward, fy_create_profile, anchor_pe)
		self._assign(self.pe_approver, fy_approve_profile, anchor_pe)
		self._sod_rule("FY", perm.FY_CREATE_DRAFT, perm.FY_APPROVE_AVAILABLE)
		self.start_year = 2200 + (int(self.suffix, 16) % 700)
		self.fy_name = f"FY-{self.start_year}-{self.start_year + 1}"
		create_fy_draft(self.start_year, user=self.pe_steward)
		submit_fy(self.fy_name, user=self.pe_steward)
		approve_fy(self.fy_name, user=self.pe_approver)

		# Context governance profiles, scoped to the test PE.
		self.steward_profile = self._profile("CTXSTEWARD", [perm.CTX_CREATE_DRAFT])
		self.reviewer_profile = self._profile("CTXREVIEWER", [perm.CTX_RECOMMEND])
		self.ao_profile = self._profile("CTXAO", [perm.CTX_APPROVE])
		self._assign(self.steward, self.steward_profile, self.entity_code)
		self._assign(self.reviewer, self.reviewer_profile, self.entity_code)
		self._assign(self.ao, self.ao_profile, self.entity_code)
		self._sod_rule("CTX-SUB-REC", perm.CTX_CREATE_DRAFT, perm.CTX_RECOMMEND)
		self._sod_rule("CTX-SUB-APP", perm.CTX_CREATE_DRAFT, perm.CTX_APPROVE)
		self._sod_rule("CTX-REC-APP", perm.CTX_RECOMMEND, perm.CTX_APPROVE)

		self.context_name = f"CTX-{self.entity_code.removeprefix('PE-')}-{self.start_year}-{self.start_year + 1}"

	def tearDown(self):
		for doctype, filters in (
			("PE Fiscal Year Context", [["name", "=", self.context_name]]),
			("Financial Year", [["name", "=", self.fy_name]]),
			("Procuring Entity Version", [["procuring_entity", "=", self.entity_code]]),
			("Procuring Entity", [["name", "=", self.entity_code]]),
			("Audit Event", [["document_name", "in", [self.context_name, self.fy_name, self.entity_code]]]),
			("Operational Scope Assignment", [["name", "like", f"%{self.suffix}%"]]),
			("Separation of Duties Rule", [["name", "like", f"%{self.suffix}%"]]),
			("Capability Profile", [["name", "like", f"%{self.suffix}%"]]),
			("PE Type", [["name", "like", f"%{self.suffix}%"]]),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.steward, self.reviewer, self.ao, self.outsider, self.pe_steward, self.pe_approver):
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

	def _profile(self, label, capabilities):
		doc = frappe.get_doc(
			{
				"doctype": "Capability Profile",
				"profile_id": f"CAP-{label}-{self.suffix}",
				"profile_name": f"Test {label}",
				"capabilities": json.dumps(capabilities),
				"allows_entity_wide": 1,
				"status": "Active",
				"concurrency_token": uuid4().hex,
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _assign(self, user, profile, pe):
		frappe.get_doc(
			{
				"doctype": "Operational Scope Assignment",
				"assignment_id": f"OSA-CTX-{uuid4().hex[:10]}-{self.suffix}",
				"user_id": user,
				"capability_profile_id": profile,
				"procuring_entity_id": pe,
				"effective_from": add_days(now_datetime(), -1),
				"status": "Active",
				"assigned_by": "Administrator",
				"assigned_at": now_datetime(),
				"concurrency_token": uuid4().hex,
			}
		).insert(ignore_permissions=True)

	def _sod_rule(self, label, first, second):
		frappe.get_doc(
			{
				"doctype": "Separation of Duties Rule",
				"rule_id": f"SOD-{label}-{self.suffix}",
				"rule_name": f"Test {label}",
				"first_capability": first,
				"second_capability": second,
				"enforcement_level": "Workflow instance",
				"status": "Active",
				"effective_from": add_days(now_datetime(), -1),
			}
		).insert(ignore_permissions=True)

	def _create_draft(self, active_from=None, active_to=None):
		active_from = active_from or add_days(now_datetime(), -1)
		active_to = active_to or add_days(now_datetime(), 30)
		result = create_context_draft(self.entity_code, self.fy_name, active_from, active_to, user=self.steward)
		self.assertEqual(result["context"], self.context_name)
		return result

	def test_stale_expected_version_rejected_with_version_conflict(self):
		"""AC-017/BR-016 — a command carrying a stale expected_version must be
		rejected with no partial effect; the record's real state must be untouched."""
		self._create_draft()
		current = frappe.db.get_value("PE Fiscal Year Context", self.context_name, "modified")
		# Someone else changes the record in between the caller's read and their command.
		frappe.db.set_value("PE Fiscal Year Context", self.context_name, "closed_reason", "", update_modified=True)
		stale_version = str(current)

		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			submit_context(self.context_name, user=self.steward, expected_version=stale_version)
		self.assertTrue(any((m.get("title") or "") == "VERSION_CONFLICT" for m in frappe.local.message_log))

		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Draft")  # unchanged — no partial effect

		fresh_version = str(ctx.modified)
		submit_context(self.context_name, user=self.steward, expected_version=fresh_version)
		ctx.reload()
		self.assertEqual(ctx.context_status, "Under Review")

	def test_prerequisites_pe_active_fy_available(self):
		"""BR-005."""
		with self.assertRaises(frappe.ValidationError):
			create_context_draft(
				"PE-DOES-NOT-EXIST", self.fy_name, now_datetime(), add_days(now_datetime(), 30), user=self.steward
			)

	def test_active_to_before_active_from_rejected(self):
		"""BR-006."""
		with self.assertRaises(frappe.ValidationError):
			create_context_draft(
				self.entity_code,
				self.fy_name,
				now_datetime(),
				add_days(now_datetime(), -5),
				user=self.steward,
			)

	def test_full_lifecycle_immediate_activation(self):
		"""AC-009/AC-011 — active_from already reached activates immediately on approval."""
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Active")

	def test_core_readiness_reports_all_four_checks_ready(self):
		"""§12.6/§12.11 — Core readiness must report per-check status (PE active, FY
		available, PE type configured, timezone configured), not just one aggregate."""
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)
		detail = queries.get_pe_fy_context(self.context_name, user=self.ao)
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
		self._create_draft(active_from=add_to_date(now_datetime(), days=2), active_to=add_days(now_datetime(), 30))
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Scheduled")

		activate_due_contexts()  # not due yet
		ctx.reload()
		self.assertEqual(ctx.context_status, "Scheduled")

		frappe.db.set_value("PE Fiscal Year Context", self.context_name, "active_from", add_days(now_datetime(), -1))
		activate_due_contexts()
		ctx.reload()
		self.assertEqual(ctx.context_status, "Active")

	def test_sod_blocks_submit_vs_recommend(self):
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		with self.assertRaises(frappe.PermissionError):
			recommend_context(self.context_name, user=self.steward)

	def test_sod_blocks_submit_vs_approve(self):
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		with self.assertRaises(frappe.PermissionError):
			approve_context(self.context_name, user=self.steward)

	def test_sod_blocks_recommend_vs_approve(self):
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		with self.assertRaises(frappe.PermissionError):
			approve_context(self.context_name, user=self.reviewer)

	def test_duplicate_pe_fy_pair_rejected(self):
		"""BR-001 via docname collision."""
		self._create_draft()
		with self.assertRaises(frappe.DuplicateEntryError):
			create_context_draft(
				self.entity_code, self.fy_name, now_datetime(), add_days(now_datetime(), 30), user=self.steward
			)

	def test_close_requires_reason_and_acknowledgement(self):
		"""AC-015."""
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)

		with self.assertRaises(frappe.ValidationError):
			close_context(self.context_name, "", acknowledged=True, user=self.ao)
		with self.assertRaises(frappe.ValidationError):
			close_context(self.context_name, "Done for the year", acknowledged=False, user=self.ao)

		close_context(self.context_name, "Done for the year", acknowledged=True, user=self.ao)
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Closed")
		self.assertEqual(ctx.closed_by, self.ao)

		# AC-015 — disappears from new-work selectors; the record itself is untouched.
		result = resolve_authorized_contexts(self.ao)
		self.assertNotIn(self.context_name, {c["context_id"] for c in result["contexts"]})
		self.assertTrue(frappe.db.exists("PE Fiscal Year Context", self.context_name))

	def test_auto_close_due_contexts(self):
		"""AC §6.3 'ACTIVE | Reach active_to | CLOSED' — automated, scheduler audit."""
		self._create_draft(active_to=add_days(now_datetime(), 30))
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)
		frappe.db.set_value("PE Fiscal Year Context", self.context_name, "active_to", add_days(now_datetime(), -1))

		close_due_contexts()
		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Closed")
		self.assertEqual(ctx.closed_by, "Administrator")

	def test_exceptional_reopen_requires_full_chain_no_direct_toggle(self):
		"""AC-016 — no direct toggle; full propose/recommend/approve route required."""
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)
		close_context(self.context_name, "Closing for reopen test", acknowledged=True, user=self.ao)

		# Cannot approve reopen without proposing/recommending first.
		with self.assertRaises(frappe.ValidationError):
			approve_context_reopen(self.context_name, user=self.ao)

		propose_context_reopen(self.context_name, "Need to reopen", user=self.steward)
		with self.assertRaises(frappe.ValidationError):
			approve_context_reopen(self.context_name, user=self.ao)  # still missing recommend

		recommend_context_reopen(self.context_name, user=self.reviewer)
		approve_context_reopen(self.context_name, user=self.ao)

		ctx = frappe.get_doc("PE Fiscal Year Context", self.context_name)
		self.assertEqual(ctx.context_status, "Active")

	def test_resolver_returns_active_context_for_authorized_actor_only(self):
		"""AC-012/AC-013 — authorized actors get the context; an unrelated user gets none."""
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)

		result = resolve_authorized_contexts(self.ao)
		context_ids = {c["context_id"] for c in result["contexts"]}
		self.assertIn(self.context_name, context_ids)

		outsider_result = resolve_authorized_contexts(self.outsider)
		self.assertEqual(outsider_result["contexts"], [])
		self.assertIsNone(outsider_result["auto_selected"])

	def test_list_query_never_returns_out_of_scope_contexts(self):
		"""AC-022 — there is no broad "all configured contexts" API a downstream
		module could call client-side; list_pe_fy_contexts scopes exactly like the
		resolver does, using the same _authorized_pes() gate."""
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)

		as_ao = queries.list_pe_fy_contexts(user=self.ao)
		self.assertIn(self.context_name, {r["context_id"] for r in as_ao["rows"]})

		as_outsider = queries.list_pe_fy_contexts(user=self.outsider)
		self.assertEqual(as_outsider["rows"], [])

	def test_validate_context_for_command_rejects_non_active(self):
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		with self.assertRaises(frappe.ValidationError):
			validate_context_for_command(self.ao, perm.CTX_APPROVE, self.context_name)

	def test_current_and_next_fy_contexts_both_active_for_one_pe(self):
		"""AC-012 — a PE may have two simultaneously Active contexts (current and
		next FY); the authorized selector returns both, not just one."""
		second_start_year = self.start_year + 1
		second_fy_name = f"FY-{second_start_year}-{second_start_year + 1}"
		create_fy_draft(second_start_year, user=self.pe_steward)
		submit_fy(second_fy_name, user=self.pe_steward)
		approve_fy(second_fy_name, user=self.pe_approver)
		try:
			self._create_draft()
			submit_context(self.context_name, user=self.steward)
			recommend_context(self.context_name, user=self.reviewer)
			approve_context(self.context_name, user=self.ao)

			second_context_name = f"CTX-{self.entity_code.removeprefix('PE-')}-{second_start_year}-{second_start_year + 1}"
			create_context_draft(
				self.entity_code, second_fy_name, now_datetime(), add_days(now_datetime(), 400), user=self.steward
			)
			submit_context(second_context_name, user=self.steward)
			recommend_context(second_context_name, user=self.reviewer)
			approve_context(second_context_name, user=self.ao)

			result = resolve_authorized_contexts(self.ao)
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
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)

		before = resolve_authorized_contexts(self.ao, remembered_context=self.context_name)
		self.assertTrue(before["remembered_context_valid"])
		self.assertIn(self.context_name, {c["context_id"] for c in before["contexts"]})

		suspend_context(self.context_name, "Under review", user=self.ao)

		after = resolve_authorized_contexts(self.ao, remembered_context=self.context_name)
		self.assertFalse(after["remembered_context_valid"])
		self.assertNotIn(self.context_name, {c["context_id"] for c in after["contexts"]})

		with self.assertRaises(frappe.ValidationError):
			validate_context_for_command(self.ao, perm.CTX_APPROVE, self.context_name)

	def test_validate_context_for_command_out_of_scope_does_not_disclose_existence(self):
		"""AC-013 — an actor outside their assignment must be denied 'without
		disclosing out-of-scope data'. A real, Active, in-scope-for-someone-else
		context must fail with the exact same safe message/title as a genuinely
		non-existent context — otherwise the message itself discloses existence."""
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)

		def _fail(fn):
			frappe.local.message_log = []
			with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
				fn()
			self.assertEqual(len(frappe.local.message_log), 1)
			return frappe.local.message_log[0]

		real_but_out_of_scope = _fail(
			lambda: validate_context_for_command(self.outsider, perm.CTX_APPROVE, self.context_name)
		)
		nonexistent = _fail(
			lambda: validate_context_for_command(self.outsider, perm.CTX_APPROVE, "CTX-DOES-NOT-EXIST")
		)
		self.assertEqual(real_but_out_of_scope["title"], nonexistent["title"])
		self.assertEqual(real_but_out_of_scope["message"], nonexistent["message"])

	def test_retire_pe_blocked_while_context_active(self):
		"""Closes the loop from Phase 1's deferred retire_pe() guard."""
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)

		with self.assertRaises(frappe.ValidationError):
			retire_pe(self.entity_code, "test", frappe.utils.today(), user=self.pe_approver)

	def test_retire_fy_blocked_while_context_active(self):
		self._create_draft()
		submit_context(self.context_name, user=self.steward)
		recommend_context(self.context_name, user=self.reviewer)
		approve_context(self.context_name, user=self.ao)

		with self.assertRaises(frappe.ValidationError):
			retire_fy(self.fy_name, user=self.pe_approver)
