"""Phase 4 contract tests for NDS-CHG-001 v1.1 §8 and §9.

Asserts that every §8.1 read and §8.2 command is whitelisted under its exact
contract name, that no writable DocType endpoint bypasses a command (§16.1),
that the §9 error contract is closed and reachable, and that the §4.7 planning
usage projection is idempotent and ordered.
"""

from __future__ import annotations

import inspect
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_procurement.departmental_needs import api
from kentender_procurement.departmental_needs.constants import (
	USAGE_FULL,
	USAGE_NOT_INCLUDED,
)
from kentender_procurement.departmental_needs.errors import ERROR_CODES, DepartmentalNeedError, fail
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	AUTHOR,
	FY,
	INTAKE_WINDOW,
	OU_DIGITAL_HEALTH,
	PE,
	PLANNER,
	REVIEWER,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services import lifecycle
from kentender_procurement.departmental_needs.services.usage import (
	planning_usage,
	project_planning_usage,
)

# §8.1 — every read contract, by its exact name.
READ_CONTRACTS = (
	"resolve_needs_contexts",
	"get_needs_workspace",
	"get_departmental_need",
	"get_departmental_review_task",
	"get_needs_intake_window",
	"get_current_accepted_need",
	"check_accepted_need_withdrawal_dependency",
)

# §8.2 — every command contract, by its exact name.
COMMAND_CONTRACTS = (
	"save_need_draft",
	"submit_need_version",
	"return_need_version",
	"accept_need_version",
	"decline_need_version",
	"withdraw_unaccepted_need",
	"create_accepted_need_successor",
	"cancel_accepted_need_successor",
	"request_accepted_need_withdrawal",
	"decide_accepted_need_withdrawal",
	"save_needs_intake_window",
	"project_need_planning_usage",
)


class ContractCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")
		now = now_datetime()
		frappe.db.set_value(
			"Needs Intake Window",
			INTAKE_WINDOW,
			{"opens_at": add_days(now, -1), "closes_at": add_days(now, 1)},
			update_modified=False,
		)

	def key(self) -> str:
		return f"nds-contract-{uuid4().hex}"

	def accepted_need(self):
		"""NDS-MOH-2027-0001 — Accepted for planning (§14.3)."""
		return frappe.get_doc("Departmental Need", "NDS-MOH-2027-0001")


class TestContractSurface(ContractCase):
	"""§8 — the exact names, whitelisted."""

	def test_every_read_contract_is_whitelisted_under_its_exact_name(self):
		for name in READ_CONTRACTS:
			handler = getattr(api, name, None)
			self.assertIsNotNone(handler, f"§8.1 contract {name} is missing")
			self.assertIn(handler, frappe.whitelisted, f"{name} is not whitelisted")

	def test_every_command_contract_is_whitelisted_under_its_exact_name(self):
		for name in COMMAND_CONTRACTS:
			handler = getattr(api, name, None)
			self.assertIsNotNone(handler, f"§8.2 contract {name} is missing")
			self.assertIn(handler, frappe.whitelisted, f"{name} is not whitelisted")

	def test_no_endpoint_outside_the_contract_is_whitelisted(self):
		# §16.1 — no writable DocType endpoint bypasses a command, and no
		# pre-v1.1 name survives as an alias (§17 forbids compatibility shims).
		exposed = {
			name
			for name, value in vars(api).items()
			if not name.startswith("_") and callable(value) and value in frappe.whitelisted
		}
		self.assertEqual(exposed, set(READ_CONTRACTS) | set(COMMAND_CONTRACTS))

	def test_every_mutating_command_requires_an_idempotency_key(self):
		exempt = {
			# §8.2 scopes these by role and record version rather than a decision
			# token: the window is a single PE/FY record, and a usage projection
			# is made idempotent by its own source event ID.
			"save_needs_intake_window",
			"project_need_planning_usage",
		}
		for name in COMMAND_CONTRACTS:
			if name in exempt:
				continue
			handler = getattr(api, name)
			target = getattr(handler, "__wrapped__", handler)
			params = inspect.signature(target).parameters
			if "kwargs" in params:
				continue  # delegates to a lifecycle command checked below
			self.assertIn("idempotency_key", params, f"{name} takes no idempotency key")

	def test_the_delegating_endpoints_reach_the_real_commands(self):
		for name in ("return_need_version", "accept_need_version", "decline_need_version"):
			source = inspect.getsource(getattr(api, name))
			self.assertIn("lifecycle.review_need", source)


class TestErrorContract(ContractCase):
	"""§9 — a closed set of stable codes."""

	def test_the_contract_holds_exactly_the_fifteen_specified_codes(self):
		self.assertEqual(
			ERROR_CODES,
			frozenset(
				{
					"NDS_CONTEXT_REQUIRED",
					"NDS_SCOPE_DENIED",
					"NDS_INTAKE_NOT_OPEN",
					"NDS_FIELD_REQUIRED",
					"NDS_REQUIRED_BY_OUTSIDE_FY",
					"NDS_UNIT_INELIGIBLE",
					"NDS_MAKER_CHECKER",
					"NDS_STATE_CONFLICT",
					"NDS_OPEN_SUCCESSOR_EXISTS",
					"NDS_STALE_WRITE",
					"NDS_WITHDRAWAL_ALREADY_OPEN",
					"NDS_ACTIVE_PLAN_DEPENDENCY",
					"NDS_IDEMPOTENCY_CONFLICT",
					"NDS_SOURCE_STALE",
					"NDS_NOT_ACCEPTED",
				}
			),
		)

	def test_an_off_contract_code_cannot_be_raised(self):
		with self.assertRaises(ValueError):
			fail("NDS_MADE_UP_CODE", "Not part of §9.")

	def test_the_module_emits_no_code_outside_the_contract(self):
		import pathlib
		import re

		module = pathlib.Path(lifecycle.__file__).parent.parent
		used = set()
		for path in module.rglob("*.py"):
			if "__pycache__" in path.parts or "tests" in path.parts:
				continue
			used |= set(re.findall(r'"(NDS_[A-Z_]+)"', path.read_text()))
		self.assertEqual(used - ERROR_CODES, set())


class TestIdempotencyConflict(ContractCase):
	"""§9 `NDS_IDEMPOTENCY_CONFLICT` — reuse with a different payload."""

	def create(self, key: str, **overrides):
		frappe.set_user(AUTHOR)
		values = {
			"title": "Clinical deployment laptops for rollout",
			"description": "Laptop computers for deployment at priority health facilities.",
			"expected_operational_result": "Facilities can use the deployed digital health services.",
			"indicative_quantity": 10,
			"unit": "UNIT-EACH",
			"required_by_date": "2027-12-31",
		}
		values.update(overrides)
		return lifecycle.create_need(
			procuring_entity=PE,
			organisation_unit=OU_DIGITAL_HEALTH,
			financial_year=FY,
			idempotency_key=key,
			**values,
		)

	def test_the_same_key_with_the_same_payload_replays(self):
		key = self.key()
		first = self.create(key)
		second = self.create(key)
		self.assertFalse(first["idempotent"])
		self.assertTrue(second["idempotent"])
		self.assertEqual(first["need"], second["need"])

	def test_the_same_key_with_a_different_payload_is_rejected(self):
		key = self.key()
		self.create(key)
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.create(key, title="A materially different requirement title")
		self.assertEqual(caught.exception.code, "NDS_IDEMPOTENCY_CONFLICT")
		self.assertEqual(
			frappe.db.count("Departmental Need Decision", {"idempotency_key": key}), 1
		)


class TestAcceptedSourceContract(ContractCase):
	"""§8.1 `get_current_accepted_need` — §7.1 payload, typed staleness."""

	def read(self, **kwargs):
		frappe.set_user(PLANNER)
		return api.get_current_accepted_need(need="NDS-MOH-2027-0001", **kwargs)

	def test_the_payload_carries_the_seven_one_field_set(self):
		payload = self.read()
		self.assertEqual(payload["contract"], "DepartmentalNeedAccepted.v2")
		for field in (
			"need",
			"need_reference",
			"accepted_version",
			"version_number",
			"content_hash",
			"procuring_entity",
			"organisation_unit",
			"financial_year",
			"title",
			"description",
			"expected_operational_result",
			"indicative_quantity",
			"unit",
			"unit_label",
			"required_by_date",
		):
			self.assertIn(field, payload)

	def test_the_payload_carries_nothing_the_spec_excludes(self):
		# NDS-AC-024 — no Budget Line, amount, funding source, currency,
		# Strategy, requirement type, location, attachment or evidence.
		payload = self.read()
		for excluded in (
			"budget_line",
			"indicative_cost",
			"amount",
			"funding_source",
			"currency",
			"strategy",
			"requirement_type",
			"procurement_method",
			"delivery_or_use_location",
			"attachments",
			"source_reference",
			"notes",
		):
			self.assertNotIn(excluded, payload)

	def test_a_stale_content_hash_is_rejected(self):
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.read(expected_content_hash="0" * 64)
		self.assertEqual(caught.exception.code, "NDS_SOURCE_STALE")

	def test_a_need_with_no_accepted_version_is_typed(self):
		# Read as the HoD: a Planner cannot see a non-accepted Need at all, so
		# for them the correct answer is the scope denial asserted below.
		frappe.set_user(REVIEWER)
		with self.assertRaises(DepartmentalNeedError) as caught:
			# NDS-MOH-2027-0002 is Submitted, never accepted.
			api.get_current_accepted_need(need="NDS-MOH-2027-0002")
		self.assertEqual(caught.exception.code, "NDS_NOT_ACCEPTED")

	def test_a_planner_cannot_read_a_need_that_is_not_accepted(self):
		frappe.set_user(PLANNER)
		with self.assertRaises(DepartmentalNeedError) as caught:
			api.get_current_accepted_need(need="NDS-MOH-2027-0002")
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_a_mismatched_expected_context_is_rejected(self):
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.read(expected_financial_year="FY-2099-2100")
		self.assertEqual(caught.exception.code, "NDS_CONTEXT_REQUIRED")


class TestPlanningUsageProjection(ContractCase):
	"""§4.7 / §8.2 `project_need_planning_usage` — idempotent and ordered."""

	def project(self, **kwargs):
		frappe.set_user(PLANNER)
		need = self.accepted_need()
		values = {
			"departmental_need": need.name,
			"accepted_version": need.current_accepted_version,
			"usage": USAGE_FULL,
			"source_event_id": self.key(),
			"active_plan": "PLN-MOH-2027-001",
			"active_plan_item": "PPI-MOH-2027-021",
		}
		values.update(kwargs)
		return project_planning_usage(**values)

	def test_a_projection_sets_usage_and_the_plan_references(self):
		result = self.project()
		self.assertFalse(result["idempotent"])
		self.assertEqual(result["usage"], USAGE_FULL)
		self.assertEqual(result["active_plan_item"], "PPI-MOH-2027-021")
		self.assertEqual(planning_usage(self.accepted_need().name), USAGE_FULL)

	def test_replaying_the_same_event_is_a_no_op(self):
		event = self.key()
		self.project(source_event_id=event)
		replay = self.project(source_event_id=event)
		self.assertTrue(replay["idempotent"])
		self.assertEqual(
			frappe.db.count(
				"Need Planning Usage Projection",
				{"accepted_version": self.accepted_need().current_accepted_version},
			),
			1,
		)

	def test_an_older_event_cannot_overwrite_a_newer_projection(self):
		now = now_datetime()
		self.project(source_event_time=now)
		late = self.project(
			usage=USAGE_NOT_INCLUDED, source_event_time=add_days(now, -1), active_plan_item=""
		)
		self.assertTrue(late.get("superseded"))
		self.assertEqual(planning_usage(self.accepted_need().name), USAGE_FULL)

	def test_clearing_an_inclusion_empties_the_plan_references(self):
		self.project()
		cleared = self.project(usage=USAGE_NOT_INCLUDED, active_plan="", active_plan_item="")
		self.assertEqual(cleared["usage"], USAGE_NOT_INCLUDED)
		self.assertEqual(cleared["active_plan"], "")
		self.assertEqual(cleared["active_plan_item"], "")

	def test_only_planning_may_project_usage(self):
		frappe.set_user(REVIEWER)
		need = self.accepted_need()
		with self.assertRaises(DepartmentalNeedError) as caught:
			project_planning_usage(
				departmental_need=need.name,
				accepted_version=need.current_accepted_version,
				usage=USAGE_FULL,
				source_event_id=self.key(),
				active_plan_item="PPI-MOH-2027-021",
			)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_a_fully_included_projection_must_name_the_plan_item(self):
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.project(active_plan="", active_plan_item="")
		self.assertEqual(caught.exception.code, "NDS_FIELD_REQUIRED")

	def test_usage_is_not_lifecycle_state(self):
		# NDS-BR-014 / NDS-AC-015 — projecting usage changes no Need state.
		need = self.accepted_need()
		before = (need.current_state, need.record_version)
		self.project()
		after = frappe.db.get_value(
			"Departmental Need", need.name, ["current_state", "record_version"]
		)
		self.assertEqual(before, after)
