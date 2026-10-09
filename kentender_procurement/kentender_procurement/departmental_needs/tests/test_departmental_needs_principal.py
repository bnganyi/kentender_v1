"""The acting principal of a Departmental Needs endpoint is the session user.

AUD-XC-001 (a request field `user=` chose who acted), AUD-XC-016 (Planning's
projection commands were web endpoints), AUD-XC-140 (an unknown field was an
HTTP 500) and AUD-NDS-011 (the withdrawal-dependency read had no permission
check).

Endpoints are called through `frappe.call`, which filters the request fields
by the endpoint's signature exactly as the HTTP handler does; calling the
service directly would hide the defect.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.departmental_needs import api
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds import playwright_ui_fixtures as pw_fixtures
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	AUTHOR,
	DEPARTMENTAL_AUTHOR,
	FY,
	PLANNER,
	REVIEWER,
	_granted_units,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.tests import support
from kentender_procurement.departmental_needs.tests.test_departmental_needs_permissions import NO_GRANT_USER

ACCEPTED_NEED = "NDS-MOH-2027-0001"

CONTENT = {
	"title": "Clinical deployment laptops for rollout",
	"description": "Laptop computers for deployment at priority health facilities.",
	"expected_operational_result": "Facilities can use the deployed digital health services.",
	"indicative_quantity": 10,
	"unit": "Each",
	"estimated_total_cost": 1000000,
	"required_by_date": "2027-12-31",
}


class PrincipalCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()
		support.ensure_transitional_reviewer_grant(cls)
		cls.ou = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)["Digital Health"]

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		started = frappe.utils.now()
		self.addCleanup(frappe.set_user, "Administrator")
		self.addCleanup(self._purge, started)

	def _purge(self, started: str) -> None:
		frappe.set_user("Administrator")
		pw_fixtures.purge_untagged_needs_since(started)

	def key(self) -> str:
		return f"nds-principal-{uuid4().hex}"

	def submitted_need(self) -> dict:
		"""A fresh Need the author has submitted, with its open review task."""
		frappe.set_user(AUTHOR)
		created = frappe.call(
			api.save_need_draft,
			organisation_unit=self.ou,
			financial_year=FY,
			idempotency_key=self.key(),
			**CONTENT,
		)
		submitted = frappe.call(
			api.submit_need_revision,
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=self.key(),
		)
		token = frappe.db.get_value("Departmental Need Review Task", submitted["task"], "decision_token")
		return {**submitted, "decision_token": token}


class TestEndpointsActAsTheSessionUser(PrincipalCase):
	def test_a_read_endpoint_ignores_a_supplied_user(self):
		"""AUD-XC-001 — the Planner cannot read a Need under review by naming the reviewer."""
		need = self.submitted_need()["need"]
		frappe.set_user(PLANNER)
		with self.assertRaises(DepartmentalNeedError) as caught:
			frappe.call(api.get_departmental_need, need=need, user=REVIEWER)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_the_review_task_read_does_not_hand_the_token_to_another_account(self):
		submitted = self.submitted_need()
		frappe.set_user(PLANNER)
		with self.assertRaises(DepartmentalNeedError):
			frappe.call(api.get_departmental_review_task, task=submitted["task"], user=REVIEWER)

	def test_a_command_endpoint_refuses_a_supplied_user_and_changes_nothing(self):
		"""AUD-XC-001 — the author cannot accept their own Need by naming the reviewer."""
		submitted = self.submitted_need()
		state_before = frappe.db.get_value("Departmental Need", submitted["need"], "current_state")
		with self.assertRaises(DepartmentalNeedError):
			frappe.call(
				api.accept_need_revision,
				need=submitted["need"],
				task=submitted["task"],
				expected_version=submitted["record_version"],
				decision_token=submitted["decision_token"],
				idempotency_key=self.key(),
				user=REVIEWER,
			)
		self.assertEqual(frappe.db.get_value("Departmental Need", submitted["need"], "current_state"), state_before)

	def test_a_command_endpoint_with_a_fixed_signature_still_acts_as_the_session_user(self):
		"""`submit_need_revision` has no `**kwargs`: a supplied `user` is dropped, never obeyed."""
		frappe.set_user(AUTHOR)
		created = frappe.call(
			api.save_need_draft,
			organisation_unit=self.ou,
			financial_year=FY,
			idempotency_key=self.key(),
			**CONTENT,
		)
		frappe.set_user(PLANNER)
		with self.assertRaises(DepartmentalNeedError) as caught:
			frappe.call(
				api.submit_need_revision,
				need=created["need"],
				expected_version=created["record_version"],
				idempotency_key=self.key(),
				user=AUTHOR,
			)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")
		self.assertEqual(frappe.db.get_value("Departmental Need", created["need"], "current_state"), "Draft")

	def test_the_endpoint_does_not_take_a_user_parameter_at_all(self):
		import inspect

		for name in (
			"resolve_needs_scope",
			"list_needs_financial_years",
			"list_need_create_targets",
			"list_need_units",
			"get_needs_workspace",
			"get_departmental_need",
			"get_departmental_review_task",
			"get_current_accepted_need",
			"check_accepted_need_withdrawal_dependency",
			"get_need_planning_status",
			"submit_need_revision",
			"withdraw_unaccepted_need",
			"create_accepted_need_successor",
			"cancel_accepted_need_successor",
			"request_accepted_need_withdrawal",
			"decide_accepted_need_withdrawal",
		):
			self.assertIn(getattr(api, name), frappe.whitelisted, name)
			self.assertNotIn("user", inspect.signature(getattr(api, name)).parameters, name)

	def test_direct_python_use_of_an_endpoint_cannot_name_another_principal_either(self):
		frappe.set_user(PLANNER)
		with self.assertRaises(DepartmentalNeedError):
			api.get_departmental_need(need=ACCEPTED_NEED, user=REVIEWER)


class TestUnknownFieldsAreRefused(PrincipalCase):
	def test_save_need_draft_refuses_an_unknown_field_with_a_typed_error(self):
		"""AUD-XC-140 — was `TypeError` and HTTP 500."""
		frappe.set_user(AUTHOR)
		with self.assertRaises(DepartmentalNeedError) as caught:
			frappe.call(
				api.save_need_draft,
				organisation_unit=self.ou,
				financial_year=FY,
				idempotency_key=self.key(),
				foo="1",
				**CONTENT,
			)
		self.assertIn("foo", str(caught.exception))

	def test_a_review_endpoint_refuses_an_unknown_field_with_a_typed_error(self):
		submitted = self.submitted_need()
		frappe.set_user(REVIEWER)
		for endpoint in (api.return_need_revision, api.accept_need_revision, api.decline_need_revision):
			with self.subTest(endpoint=endpoint.__name__), self.assertRaises(DepartmentalNeedError):
				frappe.call(
					endpoint,
					need=submitted["need"],
					task=submitted["task"],
					expected_version=submitted["record_version"],
					decision_token=submitted["decision_token"],
					idempotency_key=self.key(),
					bogus="x",
				)

	def test_the_frameworks_transport_fields_are_still_dropped(self):
		frappe.set_user(AUTHOR)
		created = frappe.call(
			api.save_need_draft,
			cmd="kentender_procurement.departmental_needs.api.save_need_draft",
			csrf_token="present-on-every-post",
			_="1759999999999",
			organisation_unit=self.ou,
			financial_year=FY,
			idempotency_key=self.key(),
			**CONTENT,
		)
		self.assertTrue(created["ok"])


class TestPlanningProjectionsAreNotWebEndpoints(PrincipalCase):
	def test_no_projection_command_is_reachable_over_http(self):
		"""AUD-XC-016 — Planning projects in-process through the service seam only."""
		from kentender_procurement.departmental_needs.services import usage

		for name in ("project_need_planning_usage", "project_need_planning_disposition", "project_need_planning_intake"):
			handler = getattr(api, name, None)
			self.assertTrue(handler is None or handler not in frappe.whitelisted, name)
		for fn in (usage.project_planning_usage, usage.project_planning_disposition, usage.project_planning_intake):
			self.assertNotIn(fn, frappe.whitelisted, fn.__name__)


class TestWithdrawalDependencyRead(PrincipalCase):
	def test_a_person_who_cannot_read_the_need_is_refused(self):
		"""AUD-NDS-011."""
		revision = frappe.db.get_value("Departmental Need", ACCEPTED_NEED, "current_accepted_revision")
		frappe.set_user(NO_GRANT_USER)
		with self.assertRaises(DepartmentalNeedError) as caught:
			frappe.call(
				api.check_accepted_need_withdrawal_dependency,
				need=ACCEPTED_NEED,
				accepted_revision=revision,
			)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_the_owner_still_reads_it(self):
		revision = frappe.db.get_value("Departmental Need", ACCEPTED_NEED, "current_accepted_revision")
		frappe.set_user(AUTHOR)
		result = frappe.call(
			api.check_accepted_need_withdrawal_dependency,
			need=ACCEPTED_NEED,
			accepted_revision=revision,
		)
		self.assertEqual(result["need"], ACCEPTED_NEED)

	def test_an_unknown_need_is_refused_without_saying_so(self):
		frappe.set_user(AUTHOR)
		with self.assertRaises(DepartmentalNeedError) as caught:
			frappe.call(api.check_accepted_need_withdrawal_dependency, need="NDS-NO-SUCH", accepted_revision="x")
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")
