"""AUTH-ADR-001 v1.6 §9.2/§14.2–§14.4 — the administration commands.

Covers idempotent grant, overlap and exclusive-office refusal with the exact
conflicting record, revocation with reason and concurrency, the Frappe Role
projection sync and its scheduled expiry reconciliation, the register
projection, the server preview and the assignment detail.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_responsibility_administration
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import responsibility_administration as administration
from kentender_core.services.responsibility_errors import ResponsibilityError
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

NS = "KT_TEST_ADMIN"


def _grant(user, role, unit="", **kwargs):
	return administration.grant(
		user=user, business_role=role, organisation_unit=unit, fixture_namespace=NS, **kwargs
	)


class AdministrationTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(purge)
		cls.root = fx.ensure_site_configured()
		cls.unit = fx.unit("KT Test Admin Unit", namespace=NS)
		cls.child = fx.unit("KT Test Admin Child", cls.unit, namespace=NS)
		frappe.db.commit()

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")


class TestGrant(AdministrationTestCase):
	def test_a_grant_creates_an_enabled_assignment_with_audit_fields(self):
		actor = fx.user("adm.grantee.one")
		result = _grant(actor, "Departmental Author", self.child)
		self.assertTrue(result["created"])
		row = frappe.db.get_value(
			"User Responsibility Assignment",
			result["assignment"],
			["status", "assigned_by", "assigned_at", "organisation_unit"],
			as_dict=True,
		)
		self.assertEqual(row.status, "Enabled")
		self.assertEqual(row.organisation_unit, self.child)
		self.assertTrue(row.assigned_by)
		self.assertTrue(row.assigned_at)

	def test_an_identical_regrant_returns_the_existing_record(self):
		"""§4.7/§18.2.16 — idempotent grant."""
		actor = fx.user("adm.grantee.two")
		first = _grant(actor, "Departmental Author", self.child)
		again = _grant(actor, "Departmental Author", self.child)
		self.assertFalse(again["created"])
		self.assertEqual(again["assignment"], first["assignment"])

	def test_a_different_overlapping_grant_for_the_same_tuple_is_refused(self):
		actor = fx.user("adm.grantee.three")
		_grant(actor, "Departmental Author", self.child)
		with self.assertRaises(ResponsibilityError) as caught:
			_grant(
				actor,
				"Departmental Author",
				self.child,
				appointment_type="Acting",
				authority_reference="MOH/HR/ACT/2097/099",
				effective_from="2097-01-01 00:00:00",
				effective_to="2097-06-30 23:59:59",
			)
		self.assertEqual(self.code(caught), "AUTH_CONFIGURATION_INVALID")

	def test_a_site_wide_grant_ignores_a_supplied_unit(self):
		actor = fx.user("adm.grantee.four")
		result = _grant(actor, "Procurement Planner", self.child)
		unit = frappe.db.get_value(
			"User Responsibility Assignment", result["assignment"], "organisation_unit"
		)
		self.assertFalse(unit)

	def test_a_disabled_or_website_user_cannot_hold_a_responsibility(self):
		actor = fx.user("adm.disabled")
		frappe.db.set_value("User", actor, "enabled", 0)
		with self.assertRaises(ResponsibilityError) as caught:
			_grant(actor, "Departmental Author", self.child)
		self.assertEqual(self.code(caught), "AUTH_CONFIGURATION_INVALID")
		frappe.db.set_value("User", actor, "enabled", 1)

	def test_an_ordinary_actor_may_not_grant(self):
		ordinary = fx.user("adm.ordinary")
		frappe.db.commit()
		frappe.set_user(ordinary)
		try:
			with self.assertRaises(ResponsibilityError) as caught:
				administration.grant(
					user=ordinary,
					business_role="Departmental Author",
					organisation_unit=self.child,
					fixture_namespace=NS,
				)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(self.code(caught), "AUTH_RESPONSIBILITY_REQUIRED")


class TestExclusiveOffice(AdministrationTestCase):
	"""§4.7 — the mechanism, exercised by patching Head of User Department to
	exclusive for the duration of each test: no registered role declares the
	flag yet (tracker D4), but the server behaviour must be proven so a module
	document can flip it without new code."""

	def exclusive_hod(self):
		import dataclasses
		from unittest.mock import patch as mock_patch

		from kentender_core.services import business_role_registry as registry

		entry = dataclasses.replace(
			registry.REGISTRY["Head of User Department"], exclusive_office=True
		)
		return mock_patch.dict(registry.REGISTRY, {"Head of User Department": entry})

	def test_a_second_active_holder_for_the_same_office_is_refused(self):
		"""§4.7/AUTH-AC-017 — with the exact conflicting record named."""
		peter = fx.user("adm.peter", "Peter Admin Test")
		julia = fx.user("adm.julia", "Julia Admin Test")
		with self.exclusive_hod():
			_grant(peter, "Head of User Department", self.child)
			with self.assertRaises(ResponsibilityError) as caught:
				_grant(julia, "Head of User Department", self.child)
		self.assertEqual(self.code(caught), "AUTH_EXCLUSIVE_OFFICE_CONFLICT")
		self.assertIn("Peter Admin Test", str(caught.exception))

	def test_the_same_office_in_a_different_scope_is_permitted(self):
		one = fx.user("adm.hod.one")
		two = fx.user("adm.hod.two")
		scope_a = fx.unit("KT Test Admin Office A", namespace=NS)
		scope_b = fx.unit("KT Test Admin Office B", namespace=NS)
		with self.exclusive_hod():
			_grant(one, "Head of User Department", scope_a)
			result = _grant(two, "Head of User Department", scope_b)
		self.assertTrue(result["created"])

	def test_non_overlapping_acting_periods_are_permitted(self):
		"""§16 — a substantive holder and a future acting one may coexist when
		their periods do not overlap the same instants."""
		holder = fx.user("adm.hod.past")
		acting = fx.user("adm.hod.future")
		scope = fx.unit("KT Test Admin Office", namespace=NS)
		with self.exclusive_hod():
			_grant(
				holder,
				"Head of User Department",
				scope,
				effective_from="2097-01-01 00:00:00",
				effective_to="2097-06-30 23:59:59",
			)
			result = _grant(
				acting,
				"Head of User Department",
				scope,
				appointment_type="Acting",
				authority_reference="MOH/HR/ACT/2097/041",
				effective_from="2097-07-01 00:00:00",
				effective_to="2097-09-30 23:59:59",
			)
		self.assertTrue(result["created"])

	def test_the_preview_returns_the_exclusive_conflict_before_confirmation(self):
		"""§14.3 — the UI shows the holder and blocks the save; it never
		invents a precedence rule."""
		peter = fx.user("adm.prev.peter", "Peter Preview Test")
		julia = fx.user("adm.prev.julia")
		scope = fx.unit("KT Test Admin Preview Office", namespace=NS)
		with self.exclusive_hod():
			_grant(peter, "Head of User Department", scope)
			preview = administration.preview_assignment(
				user=julia, business_role="Head of User Department", organisation_unit=scope
			)
		self.assertFalse(preview["ok"])
		self.assertEqual(preview["conflict"]["kind"], "exclusive_office")
		self.assertEqual(preview["conflict"]["heading"], "This office is already held")
		self.assertIn("Peter Preview Test", preview["conflict"]["message"])


class TestRevoke(AdministrationTestCase):
	def test_revocation_records_actor_instant_and_reason(self):
		actor = fx.user("adm.revokee")
		granted = _grant(actor, "Departmental Author", self.child)["assignment"]
		result = administration.revoke(granted, reason="Officer transferred to another unit.")
		self.assertTrue(result["revoked"])
		row = frappe.db.get_value(
			"User Responsibility Assignment",
			granted,
			["status", "revoked_by", "revoked_at", "revocation_reason"],
			as_dict=True,
		)
		self.assertEqual(row.status, "Revoked")
		self.assertTrue(row.revoked_by)
		self.assertTrue(row.revoked_at)
		self.assertEqual(row.revocation_reason, "Officer transferred to another unit.")

	def test_a_short_reason_is_refused(self):
		actor = fx.user("adm.revokee.short")
		granted = _grant(actor, "Departmental Author", self.child)["assignment"]
		with self.assertRaises(ResponsibilityError) as caught:
			administration.revoke(granted, reason="too short")
		self.assertEqual(self.code(caught), "AUTH_CONFIGURATION_INVALID")

	def test_a_stale_version_is_refused(self):
		actor = fx.user("adm.revokee.stale")
		granted = _grant(actor, "Departmental Author", self.child)["assignment"]
		with self.assertRaises(ResponsibilityError) as caught:
			administration.revoke(
				granted,
				reason="A perfectly valid revocation reason.",
				expected_version="2000-01-01 00:00:00",
			)
		self.assertEqual(self.code(caught), "AUTH_STATE_CHANGED")

	def test_revoking_twice_is_a_no_op(self):
		actor = fx.user("adm.revokee.twice")
		granted = _grant(actor, "Departmental Author", self.child)["assignment"]
		administration.revoke(granted, reason="Officer transferred to another unit.")
		again = administration.revoke(granted, reason="Officer transferred to another unit.")
		self.assertFalse(again["revoked"])


class TestProjection(AdministrationTestCase):
	def test_grant_projects_and_revoke_removes_the_frappe_role(self):
		"""§5.7 — the Role is a projection of the assignment, in both directions."""
		actor = fx.user("adm.proj.one")
		granted = _grant(actor, "Strategy Author")["assignment"]
		self.assertIn("Strategy Author", frappe.get_roles(actor))
		administration.revoke(granted, reason="Projection round-trip test cleanup.")
		frappe.local.role_permissions = {}
		self.assertNotIn("Strategy Author", frappe.get_roles(actor))

	def test_a_role_still_needed_by_another_assignment_survives_revocation(self):
		actor = fx.user("adm.proj.two")
		keep = _grant(actor, "Departmental Author", self.unit)["assignment"]
		drop = _grant(actor, "Departmental Author", self.child)
		# Same tuple in a different unit is a separate assignment.
		self.assertTrue(drop["created"])
		administration.revoke(drop["assignment"], reason="Projection retention test cleanup.")
		frappe.local.role_permissions = {}
		self.assertIn("Departmental Author", frappe.get_roles(actor))
		administration.revoke(keep, reason="Projection retention test cleanup.")

	def test_the_scheduled_reconciliation_releases_expired_projections(self):
		"""§5.7/AUTH-AC-016 — an expired assignment leaves no orphan Role."""
		actor = fx.user("adm.proj.expired")
		granted = _grant(
			actor,
			"Strategy Approver",
			effective_from="2020-01-01 00:00:00",
			effective_to="2097-01-01 00:00:00",
		)["assignment"]
		self.assertIn("Strategy Approver", frappe.get_roles(actor))
		# Time passes: shrink the window so the assignment is now expired.
		frappe.db.set_value(
			"User Responsibility Assignment",
			granted,
			"effective_to",
			"2020-06-30 23:59:59",
			update_modified=False,
		)
		result = administration.reconcile_role_projections()
		frappe.local.role_permissions = {}
		self.assertNotIn("Strategy Approver", frappe.get_roles(actor))
		self.assertGreaterEqual(result["users_reconciled"], 1)


class TestRegisterPreviewAndDetail(AdministrationTestCase):
	def test_the_register_row_carries_scope_coverage_and_derived_status(self):
		actor = fx.user("adm.reg.one", "Registry Row Test")
		_grant(actor, "Head of User Department", self.unit)
		rows = administration.list_user_responsibilities(search="Registry Row Test")["rows"]
		self.assertEqual(len(rows), 1)
		row = rows[0]
		self.assertEqual(row["scope_label"], "KT Test Admin Unit")
		self.assertEqual(row["coverage"], "This unit and 1 descendant")
		self.assertEqual(row["status"], "Active")

	def test_a_site_wide_row_reads_entire_entity(self):
		actor = fx.user("adm.reg.two", "Sitewide Row Test")
		_grant(actor, "Procurement Planner")
		row = administration.list_user_responsibilities(search="Sitewide Row Test")["rows"][0]
		self.assertEqual(row["scope_label"], "Site-wide")
		self.assertEqual(row["coverage"], "Entire entity")

	def test_the_status_filter_uses_the_derived_vocabulary(self):
		actor = fx.user("adm.reg.three", "Scheduled Row Test")
		_grant(
			actor,
			"Head of User Department",
			self.child,
			appointment_type="Acting",
			authority_reference="MOH/HR/ACT/2097/042",
			effective_from="2097-10-01 00:00:00",
			effective_to="2097-11-30 23:59:59",
		)
		scheduled = administration.list_user_responsibilities(
			search="Scheduled Row Test", status="Scheduled"
		)
		self.assertEqual(scheduled["total"], 1)
		active = administration.list_user_responsibilities(
			search="Scheduled Row Test", status="Active"
		)
		self.assertEqual(active["total"], 0)

	def test_the_preview_reports_field_problems_per_variant(self):
		"""§14.3 — Acting requires start, end and authority reference."""
		actor = fx.user("adm.prev.fields")
		preview = administration.preview_assignment(
			user=actor,
			business_role="Head of User Department",
			organisation_unit=self.child,
			appointment_type="Acting",
		)
		self.assertFalse(preview["ok"])
		fields = {problem["field"] for problem in preview["problems"]}
		self.assertEqual(fields, {"effective_from", "effective_to", "authority_reference"})

	def test_the_preview_composes_the_summary_and_descendants_server_side(self):
		"""§14.3 — the client never composes the sentence or counts locally."""
		actor = fx.user("adm.prev.summary", "Summary Test")
		preview = administration.preview_assignment(
			user=actor, business_role="Head of User Department", organisation_unit=self.unit
		)
		self.assertTrue(preview["ok"])
		self.assertEqual(preview["descendant_count"], 1)
		self.assertEqual(preview["included_units"], ["KT Test Admin Child"])
		self.assertEqual(
			preview["summary"],
			"Summary Test will be Head of User Department for KT Test Admin Unit "
			"from now with no scheduled end.",
		)

	def test_an_inactive_unit_is_refused_in_the_preview(self):
		from kentender_core.services import organisation_structure as structure

		actor = fx.user("adm.prev.inactive")
		unit = fx.unit("KT Test Admin Inactive", namespace=NS)
		structure.set_organisation_unit_active(unit_id=unit, active=False)
		preview = administration.preview_assignment(
			user=actor, business_role="Departmental Author", organisation_unit=unit
		)
		self.assertFalse(preview["ok"])
		self.assertIn("organisation_unit", {p["field"] for p in preview["problems"]})

	def test_the_detail_is_immutable_with_revoke_only_while_effective(self):
		"""§14.4 — no Edit in any state; revoke only for Active/Scheduled."""
		actor = fx.user("adm.detail", "Detail Test")
		granted = _grant(actor, "Departmental Author", self.child)["assignment"]
		detail = administration.get_assignment_detail(granted)
		self.assertTrue(detail["can_revoke"])
		self.assertTrue(detail["diagnostics"]["projection_present"])
		administration.revoke(granted, reason="Detail immutability test cleanup.")
		detail = administration.get_assignment_detail(granted)
		self.assertFalse(detail["can_revoke"])
		self.assertEqual(detail["status"], "Revoked")
