"""Phase 3 permission tests for NDS-CHG-001 v1.1 §6.

Covers the five native roles and the access profiles they resolve to, the
acting-HoD arrangement (NDS-AC-042), cross-OU/PE/FY denial, the Planner's
intake-window-only authority (NDS-AC-043), and the absence of any parallel
permission store (NDS-AC-044) or Budget/Accounting Officer surface
(NDS-AC-023).

Authorization is asserted through the services the commands actually call, not
through role names alone: §17 forbids inferring authority from a role label,
route, ownership alone or Administrator status.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.departmental_needs.constants import (
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	STATE_ACCEPTED,
	STATE_SUBMITTED,
)
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	ACTING_REVIEWER,
	AUDITOR,
	AUTHOR,
	FY,
	ISOLATION_REQUESTER,
	OU_DIGITAL_HEALTH,
	OU_HRMD,
	PE,
	PLANNER,
	REVIEWER,
	_user_permission,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services import permissions, workspace
from kentender_procurement.departmental_needs.services.context import save_intake_window

# §1.1 removed these outright; §6 names exactly five business roles.
RETIRED_ROLES = ("Departmental Need Requester", "Departmental Review Delegate", "Needs Configuration Manager")

# §17 / NDS-AC-023 — no Departmental Needs surface, task or special action.
EXCLUDED_ROLES = ("Budget Officer", "Accounting Officer")

NDS_DOCTYPES = (
	"Departmental Need",
	"Departmental Need Version",
	"Departmental Need Decision",
	"Departmental Need Review Task",
	"Need Withdrawal Request",
	"Needs Intake Window",
)


class DepartmentalNeedsPermissionCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")

	def need(self, reference: str):
		return frappe.get_doc("Departmental Need", reference)

	def accepted_need(self):
		"""NDS-MOH-2027-0001 — Accepted for planning, Digital Health (§14.3)."""
		return self.need("NDS-MOH-2027-0001")

	def hrmd_need(self):
		"""NDS-MOH-2027-0002 — Submitted, HR Management and Development."""
		return self.need("NDS-MOH-2027-0002")

	def drop_scope(self, user: str, doctype: str, value: str) -> None:
		"""End a scope assignment by removing the native User Permission row.

		Restored on cleanup rather than relying on transaction rollback:
		`frappe.clear_cache` can commit, and a leaked revocation would silently
		change what every later test in the class is actually asserting.
		"""
		existed = frappe.db.exists(
			"User Permission", {"user": user, "allow": doctype, "for_value": value}
		)
		frappe.db.delete("User Permission", {"user": user, "allow": doctype, "for_value": value})
		frappe.clear_cache(user=user)
		if existed:
			self.addCleanup(self._restore_scope, user, doctype, value)

	def _restore_scope(self, user: str, doctype: str, value: str) -> None:
		if not frappe.db.exists(
			"User Permission", {"user": user, "allow": doctype, "for_value": value}
		):
			_user_permission(user, doctype, value)
		frappe.clear_cache(user=user)

	def drop_role(self, user: str, role: str) -> None:
		"""End a role assignment, as revoking an acting appointment does."""
		existed = frappe.db.exists(
			"Has Role", {"parent": user, "parenttype": "User", "role": role}
		)
		frappe.db.delete("Has Role", {"parent": user, "parenttype": "User", "role": role})
		frappe.clear_cache(user=user)
		if existed:
			self.addCleanup(self._restore_role, user, role)

	def _restore_role(self, user: str, role: str) -> None:
		if not frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": role}):
			doc = frappe.get_doc("User", user)
			doc.append("roles", {"role": role})
			doc.save(ignore_permissions=True)
		frappe.clear_cache(user=user)


class TestAccessProfiles(DepartmentalNeedsPermissionCase):
	"""§6 — each role resolves to exactly one access profile (NDS-AC-022)."""

	def test_the_author_who_owns_the_need_reads_it_as_owner(self):
		self.assertEqual(permissions.can_view(self.accepted_need(), AUTHOR), (True, "owner"))

	def test_the_head_of_department_reads_needs_in_scope(self):
		self.assertEqual(permissions.can_view(self.accepted_need(), REVIEWER), (True, "department"))

	def test_the_planner_reads_only_an_accepted_need(self):
		# §6 — the Planner reads current accepted versions through the typed
		# source contract, and nothing earlier in the lifecycle.
		self.assertEqual(permissions.can_view(self.accepted_need(), PLANNER), (True, "planning"))
		submitted = self.hrmd_need()
		self.assertEqual(submitted.current_state, STATE_SUBMITTED)
		self.assertEqual(permissions.can_view(submitted, PLANNER), (False, "none"))

	def test_the_auditor_reads_scoped_needs_without_mutation(self):
		self.assertEqual(permissions.can_view(self.accepted_need(), AUDITOR), (True, "oversight"))
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_review_command(self.accepted_need(), AUDITOR)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_a_denied_read_does_not_disclose_the_record(self):
		# §9 — NDS_SCOPE_DENIED must disclose no protected record data.
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_view(self.accepted_need(), ISOLATION_REQUESTER)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")
		self.assertEqual(str(caught.exception), "Departmental Need not found.")


class TestScopeIsolation(DepartmentalNeedsPermissionCase):
	"""NDS-BR-001/019 — every dimension is checked, and a role grants nothing."""

	def test_a_role_without_scope_grants_no_access(self):
		# The isolation requester holds Departmental Author but is scoped to
		# another Procuring Entity entirely.
		self.assertIn(ROLE_DEPARTMENTAL_AUTHOR, permissions.roles_of(ISOLATION_REQUESTER))
		self.assertEqual(permissions.can_view(self.accepted_need(), ISOLATION_REQUESTER), (False, "none"))

	def test_cross_procuring_entity_is_denied(self):
		self.assertFalse(
			permissions.in_scope(
				ISOLATION_REQUESTER,
				procuring_entity=PE,
				organisation_unit=OU_DIGITAL_HEALTH,
				financial_year=FY,
			)
		)

	def test_cross_organisation_unit_is_denied(self):
		self.drop_scope(REVIEWER, "Organisation Unit", OU_HRMD)
		self.assertFalse(
			permissions.in_scope(
				REVIEWER, procuring_entity=PE, organisation_unit=OU_HRMD, financial_year=FY
			)
		)
		# The remaining unit is unaffected: scope narrows, it does not collapse.
		self.assertTrue(
			permissions.in_scope(
				REVIEWER, procuring_entity=PE, organisation_unit=OU_DIGITAL_HEALTH, financial_year=FY
			)
		)

	def test_cross_financial_year_is_denied(self):
		self.assertFalse(
			permissions.in_scope(
				REVIEWER,
				procuring_entity=PE,
				organisation_unit=OU_DIGITAL_HEALTH,
				financial_year="FY-2099-2100",
			)
		)

	def test_missing_scope_fails_closed_for_a_business_role(self):
		# NDS-BR-001 — this module deliberately inverts Frappe's "no rows means
		# unrestricted" default for business roles. `permitted_values` still
		# reports None faithfully; `in_scope` is what fails closed.
		self.drop_scope(REVIEWER, "Organisation Unit", OU_DIGITAL_HEALTH)
		self.drop_scope(REVIEWER, "Organisation Unit", OU_HRMD)
		self.assertIsNone(permissions.permitted_values(REVIEWER, "Organisation Unit"))
		self.assertFalse(
			permissions.in_scope(
				REVIEWER, procuring_entity=PE, organisation_unit=OU_DIGITAL_HEALTH, financial_year=FY
			)
		)

	def test_administrative_users_remain_unrestricted(self):
		# §6 gives System Administrator technical oversight, not departmental
		# authority, so the fail-closed rule above must not lock out setup.
		self.assertTrue(
			permissions.in_scope(
				"Administrator",
				procuring_entity=PE,
				organisation_unit=OU_DIGITAL_HEALTH,
				financial_year=FY,
			)
		)


class TestActingHeadOfDepartment(DepartmentalNeedsPermissionCase):
	"""NDS-AC-042 — same role, scoped User Permission, no delegate role."""

	def test_no_delegate_role_exists(self):
		self.assertEqual(
			frappe.get_all("Role", filters={"name": ("in", list(RETIRED_ROLES))}, pluck="name"), []
		)

	def test_the_acting_head_holds_the_same_role_as_the_substantive_head(self):
		self.assertIn(ROLE_HEAD_OF_USER_DEPARTMENT, permissions.roles_of(ACTING_REVIEWER))
		self.assertIn(ROLE_HEAD_OF_USER_DEPARTMENT, permissions.roles_of(REVIEWER))

	def test_the_acting_head_decides_only_within_the_assigned_unit(self):
		# Julia Njeri acts for Digital Health only, while Dr Kimani covers both.
		permissions.require_review_command(self.accepted_need(), ACTING_REVIEWER)
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_review_command(self.hrmd_need(), ACTING_REVIEWER)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")
		permissions.require_review_command(self.hrmd_need(), REVIEWER)

	def test_an_ended_acting_assignment_fails_closed(self):
		# The approved period is expressed by the assignment's existence: when it
		# ends, the scoped row and the role are both removed.
		permissions.require_review_command(self.accepted_need(), ACTING_REVIEWER)
		self.drop_scope(ACTING_REVIEWER, "Organisation Unit", OU_DIGITAL_HEALTH)
		self.drop_role(ACTING_REVIEWER, ROLE_HEAD_OF_USER_DEPARTMENT)
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_review_command(self.accepted_need(), ACTING_REVIEWER)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_removing_only_the_scope_row_does_not_widen_authority(self):
		# The escalation this module's fail-closed `in_scope` exists to prevent:
		# under Frappe's default semantics, deleting an acting HoD's only
		# Organisation Unit row would leave them unrestricted across *every*
		# department at the exact moment their assignment ended.
		self.drop_scope(ACTING_REVIEWER, "Organisation Unit", OU_DIGITAL_HEALTH)
		self.assertIn(ROLE_HEAD_OF_USER_DEPARTMENT, permissions.roles_of(ACTING_REVIEWER))
		for need in (self.accepted_need(), self.hrmd_need()):
			with self.assertRaises(DepartmentalNeedError) as caught:
				permissions.require_review_command(need, ACTING_REVIEWER)
			self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")


class TestPlannerAuthority(DepartmentalNeedsPermissionCase):
	"""NDS-AC-043 — maintains the intake window, receives no Need decision."""

	def test_the_planner_may_maintain_the_intake_window(self):
		frappe.set_user(PLANNER)
		result = save_intake_window(
			procuring_entity=PE,
			financial_year=FY,
			opens_at="2026-09-01 00:00:00",
			closes_at="2026-11-25 23:59:59",
			expected_version=frappe.db.get_value(
				"Needs Intake Window",
				{"procuring_entity": PE, "financial_year": FY},
				"record_version",
			),
		)
		self.assertTrue(result["ok"])

	def test_the_planner_receives_no_need_decision(self):
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_review_command(self.accepted_need(), PLANNER)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_the_planner_may_not_author_a_need(self):
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_create(PLANNER, PE, OU_DIGITAL_HEALTH, FY)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_a_head_of_department_may_not_maintain_the_intake_window(self):
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_intake_window_command(
				REVIEWER, procuring_entity=PE, financial_year=FY
			)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_the_planner_has_no_review_task_visibility(self):
		# §4.4's queue is departmental; the Planner is not on the doctype at all.
		roles = {row.role for row in frappe.get_meta("Departmental Need Review Task").permissions}
		self.assertNotIn(ROLE_PROCUREMENT_PLANNER, roles)


class TestRoleSurface(DepartmentalNeedsPermissionCase):
	"""NDS-AC-022, NDS-AC-023, NDS-AC-041, NDS-AC-044."""

	def test_only_the_six_specified_roles_appear_on_any_doctype(self):
		allowed = {
			"Administrator",
			"System Manager",
			ROLE_DEPARTMENTAL_AUTHOR,
			ROLE_HEAD_OF_USER_DEPARTMENT,
			ROLE_PROCUREMENT_PLANNER,
			ROLE_AUDITOR,
		}
		for doctype in NDS_DOCTYPES:
			roles = {row.role for row in frappe.get_meta(doctype).permissions}
			self.assertTrue(
				roles.issubset(allowed), f"{doctype} grants unexpected roles: {roles - allowed}"
			)

	def test_budget_and_accounting_officers_receive_nothing(self):
		for doctype in NDS_DOCTYPES:
			roles = {row.role for row in frappe.get_meta(doctype).permissions}
			for excluded in EXCLUDED_ROLES:
				self.assertNotIn(excluded, roles, f"{excluded} appears on {doctype}")
		pages = frappe.get_all("Page", filters={"name": ("like", "departmental-needs%")}, pluck="name")
		self.assertTrue(pages, "expected at least one Departmental Needs page to check")
		granted = frappe.get_all(
			"Has Role",
			filters={
				"parent": ("in", pages),
				"parenttype": "Page",
				"role": ("in", list(EXCLUDED_ROLES) + list(RETIRED_ROLES)),
			},
			fields=["parent", "role"],
		)
		self.assertEqual(granted, [], f"prohibited page roles survive: {granted}")

	def test_no_business_role_may_write_a_decision_record(self):
		# §4.5 — created only by a successful command; §13 keeps it permanently.
		writable = {
			row.role
			for row in frappe.get_meta("Departmental Need Decision").permissions
			if row.write or row.create or row.delete
		}
		self.assertEqual(writable, set())

	def test_only_the_author_and_head_of_department_write_needs(self):
		# NDS-AC-041 — lifecycle actions belong to those two roles only.
		writable = {
			row.role
			for row in frappe.get_meta("Departmental Need").permissions
			if row.write or row.create
		}
		self.assertEqual(
			writable,
			{"Administrator", "System Manager", ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT},
		)

	def test_nothing_may_be_deleted_through_a_role(self):
		for doctype in NDS_DOCTYPES:
			deletable = {row.role for row in frappe.get_meta(doctype).permissions if row.delete}
			self.assertEqual(deletable, set(), f"{doctype} grants delete to {deletable}")

	def test_the_module_consults_no_parallel_permission_store(self):
		"""NDS-AC-044 — native Frappe Role and User Permission only.

		Comments and docstrings are stripped before scanning: several of them
		exist precisely to say these stores must not be used, and matching that
		prose would make the guard fire on its own documentation.
		"""
		import io
		import pathlib
		import tokenize

		module = pathlib.Path(permissions.__file__).parent.parent
		prohibited = (
			"authorization_policy",
			"require_capability",
			"evaluate_capability",
			"Capability Profile",
			"Operational Scope Assignment",
			"Authorization Delegation",
		)
		offenders = []
		for path in sorted(module.rglob("*.py")):
			if "tests" in path.parts or "__pycache__" in path.parts:
				continue
			code = "".join(
				token.string
				for token in tokenize.generate_tokens(io.StringIO(path.read_text()).readline)
				if token.type not in (tokenize.COMMENT, tokenize.STRING)
			)
			offenders += [f"{path.name}:{token}" for token in prohibited if token in code]
		self.assertEqual(offenders, [], f"parallel permission store referenced: {offenders}")


class WorkspaceContextResolutionTest(DepartmentalNeedsPermissionCase):
	"""§8.1 — every §6 role that reads Needs must resolve a context.

	`get_workspace` backs NDS-UI-01 *and* NDS-UI-02, so a role that cannot
	resolve a context cannot open the review screen at all — no rows, no queue,
	no register. §6 gives the Head of User Department departmental review
	authority and §14.2 gives the Planner and Auditor PE/FY-scoped read access,
	so none of them may be turned away by the context resolver.

	Resolving a context is not authority: it names the PE/OU whose rows are
	queried, and `can_view` still filters every row afterwards.
	"""

	def workspace_as(self, user: str, **selection) -> dict:
		frappe.set_user(user)
		return workspace.get_workspace(user=user, **selection)

	def digital_health(self, user: str) -> dict:
		"""One resolved context, so the result carries rows and actions."""
		return self.workspace_as(
			user, procuring_entity=PE, organisation_unit=OU_DIGITAL_HEALTH
		)

	def test_reviewer_resolves_the_departments_they_review(self):
		result = self.workspace_as(REVIEWER)
		self.assertNotEqual(
			result["outcome"],
			"NO_AUTHORISED_CONTEXT",
			msg="the Head of User Department must be able to open the review screen",
		)
		units = {row["organisation_unit"] for row in result["contexts"]}
		self.assertEqual(units, {OU_DIGITAL_HEALTH, OU_HRMD})

	def test_planner_and_auditor_resolve_pe_scoped_contexts(self):
		"""§14.2 — scoped by PE and FY only, so every OU under the PE is in view."""
		for user in (PLANNER, AUDITOR):
			with self.subTest(user=user):
				result = self.workspace_as(user)
				self.assertNotEqual(result["outcome"], "NO_AUTHORISED_CONTEXT")
				entities = {row["procuring_entity"] for row in result["contexts"]}
				self.assertIn(PE, entities)

	def test_author_still_resolves_only_their_own_departments(self):
		"""The widening must not reach beyond the roles that need it."""
		result = self.workspace_as(AUTHOR)
		units = {row["organisation_unit"] for row in result["contexts"]}
		self.assertEqual(units, {OU_DIGITAL_HEALTH, OU_HRMD})

	def test_a_user_with_no_departmental_role_resolves_nothing(self):
		"""Resolution is still closed — it admits the §6 roles, not everyone."""
		result = self.workspace_as(ISOLATION_REQUESTER)
		self.assertNotIn(PE, {row["procuring_entity"] for row in result["contexts"]})

	def test_create_is_offered_only_to_an_author(self):
		"""§12.1 / §17 — the server decides the action; a reviewer never authors.

		The client also hides Create need outside an Open intake window, but
		that check cannot stand alone: intake is Open for part of the year, and
		a reviewer would then be shown a command they do not hold.
		"""
		author_actions = {a["code"] for a in self.digital_health(AUTHOR).get("actions", [])}
		self.assertIn("create", author_actions)
		for user in (REVIEWER, PLANNER, AUDITOR):
			with self.subTest(user=user):
				codes = {a["code"] for a in self.digital_health(user).get("actions", [])}
				self.assertNotIn("create", codes)
