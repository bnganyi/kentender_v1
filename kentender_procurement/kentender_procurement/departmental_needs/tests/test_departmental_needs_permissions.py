"""Phase 3 permission tests for NDS-CHG-001 v1.6 §6.

Covers the five business roles and the access profiles they resolve to, the
acting-HoD arrangement (NDS-AC-042), cross-OU denial, the closed §9 error
contract, and the absence of any parallel permission store (NDS-AC-044) or
Budget/Accounting Officer surface (NDS-AC-023).

Authorization is asserted through the services the commands actually call, not
through role names alone: §17 forbids inferring authority from a role label,
route, ownership alone or Administrator status. Every scope-ending action below
goes through the real `kentender_core.services.responsibility_administration`
`grant`/`revoke` commands — never a raw `User Permission`/`Has Role` write —
since AUTH-ADR-001 v1.6 makes `User Responsibility Assignment` the sole
authority source; a Frappe Role is a synchronized projection of it, not an
independent grant.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.responsibility_administration import grant, revoke
from kentender_procurement.departmental_needs.constants import (
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	STATE_SUBMITTED,
)
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	ACTING_REVIEWER,
	AUDITOR,
	AUTHOR,
	DEPARTMENTAL_AUTHOR,
	FY,
	PLANNER,
	REVIEWER,
	_granted_units,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services import permissions, workspace
from kentender_procurement.departmental_needs.services.context import resolve_creation_context

# §1.1 removed these outright; §6 names exactly four business roles (plus
# technical read-all, which is not a business role).
RETIRED_ROLES = ("Departmental Need Requester", "Departmental Review Delegate", "Needs Configuration Manager")

# §17 / NDS-AC-023 — no Departmental Needs surface, task or special action.
EXCLUDED_ROLES = ("Budget Officer", "Accounting Officer")

NDS_DOCTYPES = (
	"Departmental Need",
	"Departmental Need Version",
	"Departmental Need Decision",
	"Departmental Need Review Task",
	"Need Withdrawal Request",
)

# A real actor who holds zero currently-Enabled NDS authority: Samuel Otieno's
# only grant (Head of User Department, Directorate of Digital Health and
# Policy) expired 31 Aug 2026, per KT-STD-001 §8.3 / site_setup.py. Using a
# real, expired grant proves the fail-closed behaviour without inventing a
# separate isolation actor — AUTH-ADR-001 v1.6 has no PE dimension left to
# isolate against.
NO_GRANT_USER = "samuel.otieno@moh.example.test"

NS_TEST_GRANT = "KENTENDER_NDS_PERMISSIONS_TEST"

# A disposable Acting Head of User Department with a window that always
# covers "now" — Julia's own real Acting appointment (§14.2) is only
# effective 1 Oct-30 Nov 2026, which is not always the date this suite runs
# on, but `TestActingHeadOfDepartment` needs to exercise "is currently acting"
# behaviour regardless of the calendar.
ACTING_TEST_USER = "nds.test.acting.hod@example.test"


class DepartmentalNeedsPermissionCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()
		units = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)
		cls.ou = units["Digital Health"]
		cls.ou_hrmd = units["Human Resources Management and Development"]

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

	def drop_scope(self, user: str, business_role: str, organisation_unit: str) -> None:
		"""End a real assignment by revoking it — restored on cleanup.

		AUTH-ADR-001 v1.6 makes `User Responsibility Assignment` the sole
		authority source, so "ending" an assignment (however it was granted —
		Permanent or Acting) is exactly `revoke()`, which also strips the
		Frappe Role `grant()` synced onto the user. There is no separate
		"scope row" to drop independently of the role any more — one
		assignment carries both atomically.
		"""
		assignment = frappe.db.get_value(
			"User Responsibility Assignment",
			{
				"user": user,
				"business_role": business_role,
				"organisation_unit": organisation_unit,
				"status": "Enabled",
			},
			["name", "appointment_type", "authority_reference", "effective_from", "effective_to"],
			as_dict=True,
		)
		if not assignment:
			return
		revoke(assignment.name, reason="Test-only revocation.", actor="Administrator")
		self.addCleanup(
			self._restore_scope,
			user,
			business_role,
			organisation_unit,
			assignment.appointment_type,
			assignment.authority_reference,
			assignment.effective_from,
			assignment.effective_to,
		)

	def _restore_scope(
		self,
		user: str,
		business_role: str,
		organisation_unit: str,
		appointment_type: str,
		authority_reference: str,
		effective_from,
		effective_to,
	) -> None:
		kwargs = {"appointment_type": appointment_type or "Permanent"}
		if authority_reference:
			kwargs["authority_reference"] = authority_reference
		if effective_from:
			kwargs["effective_from"] = str(effective_from)
		if effective_to:
			kwargs["effective_to"] = str(effective_to)
		grant(
			user=user,
			business_role=business_role,
			organisation_unit=organisation_unit,
			fixture_namespace=NS_TEST_GRANT,
			actor="Administrator",
			**kwargs,
		)


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
			permissions.require_view(self.accepted_need(), NO_GRANT_USER)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")
		self.assertEqual(str(caught.exception), "Departmental Need not found.")


class TestScopeGating(DepartmentalNeedsPermissionCase):
	"""NDS-BR-001/019 — every dimension is checked, and a role grants nothing
	on its own. AUTH-ADR-001 v1.6 §1.1 removed the Procuring Entity dimension
	entirely (the site is exactly one implicit PE), so scope is Organisation
	Unit only now."""

	def test_a_role_without_scope_grants_no_access(self):
		# Samuel's only grant (§14.2) expired 31 Aug 2026 — the stored `status`
		# field stays "Enabled" forever unless explicitly revoked (expiry is a
		# time-derived read, not a stored state transition), but the resolver
		# still denies him: `_within_period` checks `effective_to` directly.
		self.assertFalse(
			permissions.in_scope(
				NO_GRANT_USER, business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=self.ou
			)
		)
		self.assertEqual(permissions.can_view(self.accepted_need(), NO_GRANT_USER), (False, "none"))

	def test_cross_organisation_unit_is_denied(self):
		self.drop_scope(REVIEWER, ROLE_HEAD_OF_USER_DEPARTMENT, self.ou_hrmd)
		self.assertFalse(
			permissions.in_scope(REVIEWER, business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=self.ou_hrmd)
		)
		# The remaining unit is unaffected: scope narrows, it does not collapse.
		self.assertTrue(
			permissions.in_scope(REVIEWER, business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=self.ou)
		)

	def test_missing_scope_fails_closed_for_a_business_role(self):
		# NDS-BR-001 — a business role with no covering assignment anywhere is
		# denied, never falls back to "unrestricted" the way a bare Frappe Role
		# would under the framework's own default permission semantics.
		self.drop_scope(REVIEWER, ROLE_HEAD_OF_USER_DEPARTMENT, self.ou)
		self.drop_scope(REVIEWER, ROLE_HEAD_OF_USER_DEPARTMENT, self.ou_hrmd)
		self.assertFalse(
			permissions.in_scope(REVIEWER, business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=self.ou)
		)

	def test_administrative_users_remain_unrestricted(self):
		# §6 gives System Administrator technical oversight, not departmental
		# authority, so the fail-closed rule above must not lock out setup.
		self.assertTrue(
			permissions.in_scope(
				"Administrator", business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=self.ou
			)
		)


class TestActingHeadOfDepartment(DepartmentalNeedsPermissionCase):
	"""NDS-AC-042 — an Acting appointment is one time-bound URA row, not a
	separate delegate role."""

	def test_no_delegate_role_exists(self):
		self.assertEqual(
			frappe.get_all("Role", filters={"name": ("in", list(RETIRED_ROLES))}, pluck="name"), []
		)

	def test_the_acting_head_holds_a_real_time_bound_assignment(self):
		row = frappe.db.get_value(
			"User Responsibility Assignment",
			{
				"user": ACTING_REVIEWER,
				"business_role": ROLE_HEAD_OF_USER_DEPARTMENT,
				"organisation_unit": self.ou,
				"status": "Enabled",
			},
			["appointment_type", "effective_from", "effective_to"],
			as_dict=True,
		)
		self.assertEqual(row.appointment_type, "Acting")
		self.assertTrue(row.effective_from and row.effective_to)
		# The synced Frappe Role projection exists too — a UI convenience, not
		# an independent authority source (§6).
		self.assertTrue(
			frappe.db.exists(
				"Has Role",
				{"parent": ACTING_REVIEWER, "parenttype": "User", "role": ROLE_HEAD_OF_USER_DEPARTMENT},
			)
		)

	def _ensure_acting_test_user(self) -> str:
		if not frappe.db.exists("User", ACTING_TEST_USER):
			doc = frappe.get_doc(
				{
					"doctype": "User",
					"email": ACTING_TEST_USER,
					"first_name": "Acting",
					"last_name": "Test Reviewer",
					"send_welcome_email": 0,
					"user_type": "System User",
					"enabled": 1,
				}
			)
			doc.insert(ignore_permissions=True)
			doc.add_roles("Desk User")
		grant(
			user=ACTING_TEST_USER,
			business_role=ROLE_HEAD_OF_USER_DEPARTMENT,
			organisation_unit=self.ou,
			appointment_type="Acting",
			authority_reference="Test-only acting appointment.",
			effective_from="2020-01-01 00:00:00",
			effective_to="2099-12-31 23:59:59",
			fixture_namespace=NS_TEST_GRANT,
			actor="Administrator",
		)
		return ACTING_TEST_USER

	def test_the_acting_head_decides_only_within_the_assigned_unit(self):
		# Acts for Digital Health only, while Dr Kimani covers both.
		acting = self._ensure_acting_test_user()
		permissions.require_review_command(self.accepted_need(), acting)
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_review_command(self.hrmd_need(), acting)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")
		permissions.require_review_command(self.hrmd_need(), REVIEWER)

	def test_an_ended_acting_assignment_fails_closed(self):
		# The approved period is expressed by the assignment's existence: when
		# it ends (revoked), authority stops immediately — `_within_period`
		# would also catch a naturally-expired `effective_to`, but this proves
		# the earlier, explicit end works the same way.
		acting = self._ensure_acting_test_user()
		permissions.require_review_command(self.accepted_need(), acting)
		self.drop_scope(acting, ROLE_HEAD_OF_USER_DEPARTMENT, self.ou)
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_review_command(self.accepted_need(), acting)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")


class TestServerSideContextPreferences(DepartmentalNeedsPermissionCase):
	"""CTX-CHG-001 — the working Organisation Unit is a server-side, per-user,
	per-module preference (`kt_needs_org_unit`). AUTH-ADR-001 v1.6 removed the
	Procuring Entity dimension this module used to remember alongside it."""

	CONTEXT_KEYS = ("kt_needs_org_unit", "kt_needs_financial_year")

	def clear_preferences(self, *users) -> None:
		for user in users:
			for key in self.CONTEXT_KEYS:
				frappe.defaults.clear_user_default(key, user)

	def setUp(self):
		super().setUp()
		self.clear_preferences(AUTHOR, REVIEWER)
		self.addCleanup(self.clear_preferences, AUTHOR, REVIEWER)

	def test_an_explicit_selection_is_remembered_server_side(self):
		frappe.set_user(AUTHOR)
		picked = workspace.get_workspace(organisation_unit=self.ou)
		self.assertEqual(picked["outcome"], "READY")
		# Rule 5.2 — a bare next request resolves the last valid selection.
		resolved = workspace.get_workspace()
		self.assertEqual(resolved["outcome"], "READY")
		self.assertEqual(resolved["context"]["organisation_unit"], self.ou)

	def test_preferences_never_leak_between_users(self):
		frappe.set_user(AUTHOR)
		workspace.get_workspace(organisation_unit=self.ou)
		# The reviewer shares the browser in the field; here they share nothing
		# but the server — their own resolution must still prompt (Peter has
		# two departments, so no single one auto-selects).
		frappe.set_user(REVIEWER)
		fresh = workspace.get_workspace()
		self.assertEqual(fresh["outcome"], "CONTEXT_SELECTION_REQUIRED")

	def test_a_remembered_unit_outside_the_offer_heals_to_unselected(self):
		"""A remembered OU the caller no longer holds resolves to "unselected"
		(re-prompt where more than one context exists), never to access and
		never to a hard error — the offer itself is the authority on what may
		be picked. Grace has two real contexts, so a single-context shortcut
		cannot mask this: healing must actually run `get_module_ou`."""
		frappe.defaults.set_user_default("kt_needs_org_unit", "OU-DOES-NOT-EXIST", user=AUTHOR)
		frappe.set_user(AUTHOR)
		offer = workspace.get_workspace()
		self.assertEqual(offer["outcome"], "CONTEXT_SELECTION_REQUIRED")
		self.assertEqual({row["organisation_unit"] for row in offer["contexts"]}, {self.ou, self.ou_hrmd})

	def test_a_direct_record_link_ignores_the_working_preference(self):
		"""Rule 6 — a record opens under its own stored scope after permission
		validation, whatever the remembered preference happens to say."""
		frappe.defaults.set_user_default("kt_needs_org_unit", self.ou_hrmd, user=AUTHOR)
		frappe.set_user(AUTHOR)
		read = workspace.get_need(need="NDS-MOH-2027-0001")
		self.assertTrue(read["ok"])
		self.assertEqual(read["need"]["organisation_unit"], self.ou)


class TestPlannerAuthority(DepartmentalNeedsPermissionCase):
	"""NDS-AC-043 — Site-wide read of accepted sources, no Need decision, no
	authoring authority. NDS owns no intake-window configuration surface any
	more (§4.1/§11.11/§16.4.11) — the Needs-submission flag is Configuration &
	Governance's own, maintained in `/app/system-setup`, never through an NDS
	command."""

	def test_the_planner_receives_no_need_decision(self):
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_review_command(self.accepted_need(), PLANNER)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_the_planner_may_not_author_a_need(self):
		with self.assertRaises(DepartmentalNeedError) as caught:
			permissions.require_create(PLANNER, self.ou)
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
		"""NDS-AC-044 — the AUTH-ADR-001 v1.6 resolver and native Frappe Role
		projections only.

		Comments and docstrings are stripped before scanning: several of them
		exist precisely to say these stores must not be used, and matching that
		prose would make the guard fire on its own documentation. Ordinary
		string literals (e.g. a real `frappe.get_all("User Permission", ...)`
		call) are kept — an earlier stripper blanked every string, which made
		this guard vacuous against the exact violation it exists to catch
		(see `test_departmental_needs_static_scan.py::strip_python`).
		"""
		import pathlib

		from kentender_procurement.departmental_needs.tests.test_departmental_needs_static_scan import strip_python

		module = pathlib.Path(permissions.__file__).parent.parent
		prohibited = (
			"authorization_policy",
			"require_capability",
			"evaluate_capability",
			"Capability Profile",
			"Operational Scope Assignment",
			"Authorization Delegation",
			"User Permission",
		)
		offenders = []
		for path in sorted(module.rglob("*.py")):
			if "tests" in path.parts or "__pycache__" in path.parts:
				continue
			code = strip_python(path.read_text())
			offenders += [f"{path.name}:{token}" for token in prohibited if token in code]
		self.assertEqual(offenders, [], f"parallel permission store referenced: {offenders}")


class WorkspaceContextResolutionTest(DepartmentalNeedsPermissionCase):
	"""§8.1 — every §6 role that reads Needs must resolve a context.

	`get_workspace` backs NDS-UI-01 *and* NDS-UI-02, so a role that cannot
	resolve a context cannot open the review screen at all — no rows, no queue,
	no register. §6 gives the Head of User Department departmental review
	authority and §14.2 gives the Planner and Auditor Site-wide read access, so
	none of them may be turned away by the context resolver.

	Resolving a context is not authority: it names the Organisation Unit whose
	rows are queried, and `can_view` still filters every row afterwards.
	"""

	def workspace_as(self, user: str, **selection) -> dict:
		frappe.set_user(user)
		return workspace.get_workspace(user=user, **selection)

	def digital_health(self, user: str) -> dict:
		"""One resolved context, so the result carries rows and actions."""
		return self.workspace_as(user, organisation_unit=self.ou)

	def test_reviewer_resolves_the_departments_they_review(self):
		result = self.workspace_as(REVIEWER)
		self.assertNotEqual(
			result["outcome"],
			"NO_AUTHORISED_CONTEXT",
			msg="the Head of User Department must be able to open the review screen",
		)
		units = {row["organisation_unit"] for row in result["contexts"]}
		self.assertEqual(units, {self.ou, self.ou_hrmd})

	def test_planner_and_auditor_resolve_every_active_unit(self):
		"""§14.2 — Site-wide, so every active Organisation Unit is in view."""
		for user in (PLANNER, AUDITOR):
			with self.subTest(user=user):
				result = self.workspace_as(user)
				self.assertNotEqual(result["outcome"], "NO_AUTHORISED_CONTEXT")
				units = {row["organisation_unit"] for row in result["contexts"]}
				self.assertIn(self.ou, units)
				self.assertIn(self.ou_hrmd, units)

	def test_author_still_resolves_only_their_own_departments(self):
		"""The widening must not reach beyond the roles that need it."""
		result = self.workspace_as(AUTHOR)
		units = {row["organisation_unit"] for row in result["contexts"]}
		self.assertEqual(units, {self.ou, self.ou_hrmd})

	def test_a_user_with_no_departmental_role_resolves_nothing(self):
		"""Resolution is still closed — it admits the §6 roles, not everyone."""
		result = self.workspace_as(NO_GRANT_USER)
		units = {row["organisation_unit"] for row in result["contexts"]}
		self.assertNotIn(self.ou, units)
		self.assertNotIn(self.ou_hrmd, units)

	def test_create_is_offered_only_to_an_author(self):
		"""§12.1 / §17 — the server decides the action; a reviewer never authors.

		The client also hides Create need outside an Open Needs-submission
		flag, but that check cannot stand alone: the flag is Open for part of
		the year, and a reviewer would then be shown a command they do not
		hold.
		"""
		author_actions = {a["code"] for a in self.digital_health(AUTHOR).get("actions", [])}
		self.assertIn("create", author_actions)
		for user in (REVIEWER, PLANNER, AUDITOR):
			with self.subTest(user=user):
				codes = {a["code"] for a in self.digital_health(user).get("actions", [])}
				self.assertNotIn("create", codes)


class ScopeDiagnosticTest(DepartmentalNeedsPermissionCase):
	"""KT-STD-001 v1.2 §3A — `get_workspace`'s internal, non-rendered
	`scope_diagnostic` distinguishes two causes of an empty `contexts` list
	that `viewing_contexts` itself collapses to one outcome. Not a new visible
	page state (NDS-CHG-001 v1.8 §11.15 defines none) — this only proves the
	underlying distinction is computed correctly for administrator/log use.
	"""

	def workspace_as(self, user: str, **selection) -> dict:
		frappe.set_user(user)
		return workspace.get_workspace(user=user, **selection)

	def test_no_responsibility_at_all_is_diagnosed_as_such(self):
		"""Samuel's assignment is expired (KT-STD-001 §8.3), so he resolves no
		scope at all — the same diagnosis a never-granted user would get."""
		self.assertEqual(permissions.scope_diagnostic(NO_GRANT_USER), "no_responsibility")
		result = self.workspace_as(NO_GRANT_USER)
		self.assertEqual(result["outcome"], "NO_AUTHORISED_CONTEXT")
		self.assertEqual(result["scope_diagnostic"], "no_responsibility")

	def test_a_held_responsibility_on_an_inactive_unit_is_diagnosed_separately(self):
		"""A real Enabled assignment whose Organisation Unit is not Active
		resolves zero contexts too — but for a different reason, and
		`scope_diagnostic` must not conflate the two."""
		from kentender_core.services.organisation_structure import add_organisation_unit

		unit = add_organisation_unit(name=f"Inactive Test Unit {frappe.generate_hash(length=6)}")["unit"]
		self.addCleanup(frappe.db.set_value, "Organisation Unit", unit, "status", "Active")
		frappe.db.set_value("Organisation Unit", unit, "status", "Inactive")

		email = f"nds.inactive.{frappe.generate_hash(length=6)}@test.local"
		user_doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Inactive Unit",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "System User",
				"roles": [{"role": "Desk User"}],
			}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "User", email, force=True, ignore_permissions=True)
		outcome = grant(
			user=email,
			business_role=ROLE_DEPARTMENTAL_AUTHOR,
			organisation_unit=unit,
			fixture_namespace="NDS_SCOPE_DIAGNOSTIC_TEST",
			actor="Administrator",
		)
		self.addCleanup(
			frappe.delete_doc, "User Responsibility Assignment", outcome["assignment"], force=True, ignore_permissions=True
		)

		self.assertEqual(permissions.scope_diagnostic(email), "unit_not_configured")
		result = self.workspace_as(email)
		self.assertEqual(result["outcome"], "NO_AUTHORISED_CONTEXT")
		self.assertEqual(result["scope_diagnostic"], "unit_not_configured")
