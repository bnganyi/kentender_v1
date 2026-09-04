"""AUTH-ADR-001 v1.6 §5/§9.1 — the shared authorization predicate.

Covers the §18.2 minimum: positive and negative resolution per scope type,
the Cartesian-product regression, Site-wide/OU coexistence, tree coverage,
boundary instants, technical read-all with business-mutation denial, the
registered hook predicates, `require_responsibility`, projections and
diagnostics.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_authorization
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import authorization as auth
from kentender_core.services import responsibility_administration as administration
from kentender_core.services.responsibility_errors import ResponsibilityError
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

NS = "KT_TEST_AUTH"

PAST = "2020-01-01 00:00:00"
FUTURE_FROM = "2097-10-01 00:00:00"
FUTURE_TO = "2097-11-30 23:59:59"
EXPIRED_FROM = "2020-01-01 00:00:00"
EXPIRED_TO = "2020-08-31 23:59:59"


def _grant(user, role, unit="", **kwargs):
	return administration.grant(
		user=user,
		business_role=role,
		organisation_unit=unit,
		fixture_namespace=NS,
		**kwargs,
	)["assignment"]


class AuthorizationTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(purge)
		cls.root = fx.ensure_site_configured()
		cls.directorate = fx.unit("KT Test Auth Directorate", namespace=NS)
		cls.leaf = fx.unit("KT Test Auth Leaf", cls.directorate, namespace=NS)
		cls.hr = fx.unit("KT Test Auth HR", namespace=NS)

		cls.grace = fx.user("auth.grace", "Grace Test")
		cls.mercy = fx.user("auth.mercy", "Mercy Test")
		cls.julia = fx.user("auth.julia", "Julia Test")
		cls.samuel = fx.user("auth.samuel", "Samuel Test")
		cls.norah = fx.user("auth.norah", "Norah Test")
		cls.techie = fx.user("auth.techie", "Techie Test", roles=("System Manager",))

		# The KT-STD §8.3 shapes: an author at the leaf who also decides in HR
		# (the Cartesian-product subject), a Site-wide planner, a scheduled
		# acting decision-maker, an expired one, and a revoked one.
		cls.grace_author = _grant(cls.grace, "Departmental Author", cls.leaf)
		cls.grace_hod = _grant(cls.grace, "Head of User Department", cls.hr)
		cls.mercy_planner = _grant(cls.mercy, "Procurement Planner")
		cls.julia_scheduled = _grant(
			cls.julia,
			"Head of User Department",
			cls.leaf,
			appointment_type="Acting",
			authority_reference="MOH/HR/ACT/2097/041",
			effective_from=FUTURE_FROM,
			effective_to=FUTURE_TO,
		)
		cls.samuel_expired = _grant(
			cls.samuel,
			"Head of User Department",
			cls.directorate,
			effective_from=EXPIRED_FROM,
			effective_to=EXPIRED_TO,
		)
		revoked = _grant(cls.norah, "Departmental Author", cls.directorate)
		administration.revoke(revoked, reason="Officer transferred out of the directorate.")
		cls.norah_revoked = revoked
		frappe.db.commit()

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")


class TestDerivedStatus(AuthorizationTestCase):
	def test_the_four_derived_states_follow_the_period(self):
		"""§4.6 — Scheduled, Active, Expired, Revoked; only Active authorises."""
		self.assertEqual(auth.derived_status("Enabled", None, None), "Active")
		self.assertEqual(auth.derived_status("Enabled", FUTURE_FROM, FUTURE_TO), "Scheduled")
		self.assertEqual(auth.derived_status("Enabled", EXPIRED_FROM, EXPIRED_TO), "Expired")
		self.assertEqual(auth.derived_status("Revoked", None, None), "Revoked")

	def test_boundary_instants_are_inclusive(self):
		"""§18.2.5 — at the exact start the assignment is Active; one second
		before it is Scheduled; one second after the end it is Expired."""
		self.assertEqual(
			auth.derived_status("Enabled", FUTURE_FROM, FUTURE_TO, at=FUTURE_FROM), "Active"
		)
		self.assertEqual(
			auth.derived_status("Enabled", FUTURE_FROM, FUTURE_TO, at="2097-09-30 23:59:59"),
			"Scheduled",
		)
		self.assertEqual(
			auth.derived_status("Enabled", FUTURE_FROM, FUTURE_TO, at="2097-12-01 00:00:00"),
			"Expired",
		)


class TestResolution(AuthorizationTestCase):
	def test_an_ou_role_covers_its_unit_and_descendants_only(self):
		"""AUTH-AC-005/006 — leaf covers the leaf; sibling and parent denied."""
		allowed = auth.authorise_record(self.grace, "Departmental Author", self.leaf)
		self.assertTrue(allowed.allowed)
		self.assertEqual(allowed.assignment_id, self.grace_author)

		for out_of_scope in (self.hr, self.directorate, self.root):
			decision = auth.authorise_record(self.grace, "Departmental Author", out_of_scope)
			self.assertFalse(decision.allowed, out_of_scope)
			self.assertEqual(decision.reason_code, "AUTH_SCOPE_REQUIRED")

	def test_a_parent_assignment_reaches_a_descendant(self):
		granted = _grant(self.mercy, "Head of User Department", self.directorate)
		try:
			decision = auth.authorise_record(self.mercy, "Head of User Department", self.leaf)
			self.assertTrue(decision.allowed)
			self.assertEqual(decision.assignment_id, granted)
		finally:
			administration.revoke(granted, reason="Test fixture cleanup for parent case.")

	def test_the_cartesian_product_regression(self):
		"""AUTH-AC-003/§18.2.2 — author only in the leaf, decide only in HR."""
		self.assertTrue(auth.authorise_record(self.grace, "Departmental Author", self.leaf).allowed)
		self.assertFalse(auth.authorise_record(self.grace, "Departmental Author", self.hr).allowed)
		self.assertTrue(auth.authorise_record(self.grace, "Head of User Department", self.hr).allowed)
		self.assertFalse(auth.authorise_record(self.grace, "Head of User Department", self.leaf).allowed)

	def test_site_wide_and_ou_roles_coexist_without_interference(self):
		"""AUTH-AC-004/§18.2.3 — the planner reaches every unit; holding it
		alongside an OU role never broadens the OU role."""
		for unit in (self.root, self.directorate, self.leaf, self.hr):
			self.assertTrue(auth.authorise_record(self.mercy, "Procurement Planner", unit).allowed)
		granted = _grant(self.mercy, "Departmental Author", self.leaf)
		try:
			self.assertFalse(
				auth.authorise_record(self.mercy, "Departmental Author", self.hr).allowed
			)
		finally:
			administration.revoke(granted, reason="Test fixture cleanup for coexist case.")

	def test_scheduled_expired_and_revoked_do_not_authorise_now(self):
		for user, role, unit in (
			(self.julia, "Head of User Department", self.leaf),
			(self.samuel, "Head of User Department", self.directorate),
		):
			decision = auth.authorise_record(user, role, unit)
			self.assertFalse(decision.allowed)
			self.assertEqual(decision.reason_code, "AUTH_ASSIGNMENT_INACTIVE")
		decision = auth.authorise_record(self.norah, "Departmental Author", self.directorate)
		self.assertFalse(decision.allowed)
		self.assertEqual(decision.reason_code, "AUTH_ASSIGNMENT_INACTIVE")

	def test_the_scheduled_assignment_authorises_at_its_instant(self):
		"""AUTH-AC-015 — acting starts and ends at the configured instants."""
		self.assertTrue(
			auth.authorise_record(self.julia, "Head of User Department", self.leaf, at=FUTURE_FROM).allowed
		)
		self.assertFalse(
			auth.authorise_record(
				self.julia, "Head of User Department", self.leaf, at="2097-12-01 00:00:00"
			).allowed
		)

	def test_no_assignment_at_all_is_responsibility_required(self):
		decision = auth.authorise_record(self.techie, "Departmental Author", self.leaf)
		self.assertFalse(decision.allowed)
		self.assertEqual(decision.reason_code, "AUTH_RESPONSIBILITY_REQUIRED")

	def test_a_frappe_role_without_an_assignment_grants_nothing(self):
		"""AUTH-AC-007/§18.2.7 — an orphan projection is not authority."""
		holder = fx.user("auth.orphan", "Orphan Test", roles=("Departmental Author",))
		frappe.db.commit()
		decision = auth.authorise_record(holder, "Departmental Author", self.leaf)
		self.assertFalse(decision.allowed)
		self.assertEqual(decision.reason_code, "AUTH_RESPONSIBILITY_REQUIRED")

	def test_technical_users_read_everything_and_mutate_nothing(self):
		"""AUTH-AC-018/§18.2.15 — read-all without assignment; command denied."""
		read = auth.authorise_record(
			self.techie, "Departmental Author", self.leaf, purpose=auth.PURPOSE_READ
		)
		self.assertTrue(read.allowed)
		self.assertTrue(read.technical_read)
		command = auth.authorise_record(self.techie, "Departmental Author", self.leaf)
		self.assertFalse(command.allowed)


class TestPermittedScopes(AuthorizationTestCase):
	def test_an_ou_role_returns_its_subtree(self):
		granted = _grant(self.norah, "Head of User Department", self.directorate)
		try:
			self.assertEqual(
				auth.permitted_ou_scopes(self.norah, "Head of User Department"),
				{self.directorate, self.leaf},
			)
		finally:
			administration.revoke(granted, reason="Test fixture cleanup for scopes case.")

	def test_a_site_wide_role_is_unrestricted(self):
		self.assertIsNone(auth.permitted_ou_scopes(self.mercy, "Procurement Planner"))

	def test_no_assignment_is_an_empty_set_never_unrestricted(self):
		self.assertEqual(auth.permitted_ou_scopes(self.grace, "Procurement Planner"), set())

	def test_a_technical_reader_is_unrestricted(self):
		self.assertIsNone(auth.permitted_ou_scopes(self.techie, "Departmental Author"))


class TestRequireResponsibility(AuthorizationTestCase):
	def test_the_helper_returns_the_matching_assignment(self):
		doc = {"doctype": "KT Test Scoped", "organisation_unit": self.leaf}
		with patch.object(auth, "scope_map", return_value={"KT Test Scoped": "organisation_unit"}):
			assignment = auth.require_responsibility(doc, "Departmental Author", user=self.grace)
		self.assertEqual(assignment.name, self.grace_author)

	def test_the_helper_raises_the_exact_contract_code(self):
		doc = {"doctype": "KT Test Scoped", "organisation_unit": self.hr}
		with patch.object(auth, "scope_map", return_value={"KT Test Scoped": "organisation_unit"}):
			with self.assertRaises(ResponsibilityError) as caught:
				auth.require_responsibility(doc, "Departmental Author", user=self.grace)
		self.assertEqual(self.code(caught), "AUTH_SCOPE_REQUIRED")

	def test_an_unregistered_role_is_a_configuration_error(self):
		with self.assertRaises(ResponsibilityError) as caught:
			auth.require_responsibility({}, "Workflow Approver", user=self.grace)
		self.assertEqual(self.code(caught), "AUTH_CONFIGURATION_INVALID")


class TestHookPredicates(AuthorizationTestCase):
	"""§5.3 — the predicate registered as permission_query_conditions and
	has_permission. Exercised against a patched scope map because the map is
	deliberately empty of production DocTypes until each cutover slice."""

	def scoped(self, fn, *args, **kwargs):
		with patch.object(auth, "scope_map", return_value={"KT Test Scoped": "organisation_unit"}):
			return fn(*args, **kwargs)

	def relevant(self, roles):
		return patch.object(auth, "_relevant_business_roles", return_value=roles)

	def test_a_technical_user_is_unrestricted(self):
		self.assertEqual(self.scoped(auth.scope_condition, "KT Test Scoped", self.techie), "")

	def test_an_unmapped_doctype_adds_no_predicate(self):
		self.assertEqual(auth.scope_condition("Unmapped Doctype", self.grace), "")

	def test_no_relevant_assignment_denies_all_rows(self):
		"""Norah's only assignment is revoked — never Frappe's no-rows-means-
		unrestricted default (§11.5)."""
		with self.relevant(("Departmental Author",)):
			condition = self.scoped(auth.scope_condition, "KT Test Scoped", self.norah)
		self.assertEqual(condition, "1=0")

	def test_an_ou_assignment_produces_the_subtree_in_list(self):
		with self.relevant(("Departmental Author",)):
			condition = self.scoped(auth.scope_condition, "KT Test Scoped", self.grace)
		self.assertIn("`tabKT Test Scoped`.`organisation_unit` in (", condition)
		self.assertIn(self.leaf, condition)
		self.assertNotIn(self.hr, condition)

	def test_a_site_wide_assignment_is_row_unrestricted(self):
		with self.relevant(("Procurement Planner",)):
			condition = self.scoped(auth.scope_condition, "KT Test Scoped", self.mercy)
		self.assertEqual(condition, "")

	def test_an_unrelated_site_wide_role_never_widens_another_doctype(self):
		"""AUTH-AC-004 — Mercy's planner assignment is irrelevant to a DocType
		whose read roles do not project it."""
		with self.relevant(("Departmental Author",)):
			condition = self.scoped(auth.scope_condition, "KT Test Scoped", self.mercy)
		self.assertEqual(condition, "1=0")

	def test_has_permission_blocks_the_direct_route_hole(self):
		"""§5.3/§18.2.10 — a record excluded from the list is unreachable by
		direct access too."""
		inside = {"doctype": "KT Test Scoped", "organisation_unit": self.leaf}
		outside = {"doctype": "KT Test Scoped", "organisation_unit": self.hr}
		with self.relevant(("Departmental Author",)):
			# BUD-CHG-001 v1.3 Phase 4 (D6): `True`, not `None`, is the correct
			# "not vetoing" return — Frappe's has_controller_permissions coerces
			# a bare None to a deny for this hook (see authorization.py's own
			# has_permission docstring).
			self.assertTrue(self.scoped(auth.has_permission, inside, "read", self.grace))
			self.assertFalse(self.scoped(auth.has_permission, outside, "read", self.grace))

	def test_has_permission_leaves_technical_reads_to_the_framework(self):
		doc = {"doctype": "KT Test Scoped", "organisation_unit": self.hr}
		self.assertTrue(self.scoped(auth.has_permission, doc, "read", self.techie))

	def test_report_match_conditions_is_the_same_predicate(self):
		"""§5.4/§18.2.9 — reports obtain the identical condition string."""
		with self.relevant(("Departmental Author",)):
			listed = self.scoped(auth.scope_condition, "KT Test Scoped", self.grace)
			reported = self.scoped(auth.report_match_conditions, "KT Test Scoped", self.grace)
		self.assertEqual(listed, reported)


class TestSnapshotAndDiagnostics(AuthorizationTestCase):
	def test_the_snapshot_copies_the_decision_evidence(self):
		"""§15 — later assignment changes never rewrite historical evidence."""
		decision = auth.authorise_record(self.grace, "Departmental Author", self.leaf)
		snapshot = frappe.parse_json(auth.assignment_snapshot(decision.assignment))
		self.assertEqual(snapshot["assignment_id"], self.grace_author)
		self.assertEqual(snapshot["user"], self.grace)
		self.assertEqual(snapshot["business_role"], "Departmental Author")
		self.assertEqual(snapshot["organisation_unit"], self.leaf)
		self.assertTrue(snapshot["evaluated_at"])

	def test_diagnose_buckets_by_derived_status(self):
		report = auth.diagnose_user(self.julia)
		self.assertEqual(
			[row["name"] for row in report["assignments"]["scheduled"]], [self.julia_scheduled]
		)
		report = auth.diagnose_user(self.samuel)
		self.assertEqual(
			[row["name"] for row in report["assignments"]["expired"]], [self.samuel_expired]
		)
		report = auth.diagnose_user(self.norah)
		self.assertIn(self.norah_revoked, [row["name"] for row in report["assignments"]["revoked"]])

	def test_diagnose_reports_orphan_and_missing_projections(self):
		holder = fx.user("auth.diag", "Diag Test", roles=("Strategy Author",))
		frappe.db.commit()
		report = auth.diagnose_user(holder)
		self.assertIn("Strategy Author", report["projection_orphaned"])

		frappe.get_doc("User", holder).remove_roles("Strategy Author")
		granted = _grant(holder, "Strategy Author")
		try:
			frappe.get_doc("User", holder).remove_roles("Strategy Author")
			frappe.local.role_permissions = {}
			report = auth.diagnose_user(holder)
			self.assertIn("Strategy Author", report["projection_missing"])
		finally:
			administration.revoke(granted, reason="Test fixture cleanup for diagnostics.")
