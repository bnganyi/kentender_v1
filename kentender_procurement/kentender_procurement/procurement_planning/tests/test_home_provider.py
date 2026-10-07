# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — the Planning feed to Home (`procurement_planning/services/home_provider.py`).

Planning's world is one Annual Plan per fiscal year, so each plan stage the provider answers for is its own shared world,
built once in `setUpClass` through the module's own commands (the test personas of `fixtures.py`) and read by every test of
that class; the provider only reads. After the build the events the provider reports are pinned to fixed instants, so the
timing strings are exact. Every world is wiped afterwards by the module's own purge and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.procurement_planning.tests.test_home_provider
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

import frappe
from kentender_core.services.command_write_guard import purge_doc
from frappe.tests import IntegrationTestCase

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import home_workspace as hw
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_finance,
	plan_governance,
	plan_read,
	plan_requisition,
	plan_workbench,
	publication_pipeline,
	treasury,
)
from kentender_procurement.procurement_planning.services import my_work_provider as work
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.home_provider import entries
from kentender_procurement.procurement_planning.tests import fixtures as fx

AT = datetime(2027, 6, 18, 10, 0)  # the read instant of every Home read in this module
SPEC_PAGES = ("annual-procurement-plan", "departmental-procurement-plan", "procurement-planning")
EXTRA = "plnt.home.extra@example.test"  # a second Accounting Officer, granted and revoked inside one test
EXTRA_NS = "KT_TEST_PLNHOME"
REGIONS = he.REGIONS


def _key() -> str:
	return uuid4().hex


def _dt(text: str) -> datetime:
	return datetime.strptime(text, "%Y-%m-%d %H:%M")


def _pin(doctype: str, name: str, field: str, text: str) -> None:
	frappe.db.set_value(doctype, name, field, _dt(text), update_modified=False)


# --------------------------------------------------------------------------
# the worlds: each is the module's own commands, driven as the fixture personas
# --------------------------------------------------------------------------


def _submitted_dpp(*, submitter: str = fx.HOD) -> dict:
	frappe.set_user(fx.AUTHOR)
	opened = dpp_lifecycle.open_departmental_plan(organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=_key(), fixture_namespace=fx.NS)
	added = dpp_lifecycle.save_direct_requirement(
		dpp_version=opened["current_version"], values=fx.direct_values(), expected_record_version=opened["record_version"], idempotency_key=_key(),
	)
	frappe.set_user(submitter)
	submitted = dpp_lifecycle.submit_departmental_plan(
		dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=added["record_version"], idempotency_key=_key(),
	)
	task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	return {"dpp": opened["departmental_plan"], "dpp_reference": opened["dpp_reference"], "entry": added["entry_id"], "task": task, "submission": task.submission}


def _accepted_dpp() -> dict:
	world = _submitted_dpp()
	frappe.set_user(fx.PLANNER)
	accepted = dpp_validation.accept_departmental_plan(
		task=world["task"].name, classifications={world["entry"]: "Goods"}, task_token=world["task"].task_token, idempotency_key=_key(),
	)
	return {**world, "plan": accepted["annual_plan"], "version": accepted["annual_plan_version"]}


def _accepted_item(*, amount: float = 1_000_000) -> dict:
	world = _accepted_dpp()
	accepted = {"annual_plan": world["plan"], "annual_plan_version": world["version"]}
	plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
	formed = plan_workbench.form_plan_items(
		plan_version=accepted["annual_plan_version"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]], mode="each",
		expected_record_version=plan["record_version"], idempotency_key=_key(),
	)
	item_id = formed["created_items"][0]
	item = plan_read.get_plan_item(plan_item_id=item_id)
	plan_workbench.save_plan_item(plan_item=item_id, values=fx.item_values(), expected_record_version=item["record_version"], idempotency_key=_key())
	return {**world, "item": item_id}


def _request_funding(world: dict, *, planner: str = fx.PLANNER) -> dict:
	frappe.set_user(planner)
	plan = plan_read.get_annual_plan(plan_reference=world["plan"])
	requested = plan_finance.request_plan_funding_confirmation(
		plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key(),
	)
	return {**world, "finance_task": frappe.get_doc("Plan Finance Task", requested["task"])}


def _confirm_funding(world: dict) -> dict:
	task = world["finance_task"]
	frappe.set_user(fx.FINANCE_OFFICER)
	confirmed = plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=_key())
	return {**world, "finance_decision": frappe.get_doc("Plan Finance Decision", {"decision_reference": confirmed["decision"]})}


def _sign_and_submit(world: dict) -> dict:
	frappe.set_user(fx.HOPF)
	plan = plan_read.get_annual_plan(plan_reference=world["plan"])
	submitted = plan_governance.submit_consolidated_plan(
		plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key(),
	)
	return {**world, "ao_task": frappe.get_doc("Plan Governance Task", submitted["task"])}


def _build_dpp_submitted() -> dict:
	# the Head of User Department who is also a Procurement Planner certifies it: the owner's rule stops them validating it
	return _submitted_dpp(submitter=fx.HYBRID)


def _build_dpp_returned() -> dict:
	world = _submitted_dpp()
	frappe.set_user(fx.PLANNER)
	dpp_validation.return_departmental_plan(
		task=world["task"].name, task_token=world["task"].task_token, idempotency_key=_key(),
		issues=[{"dpp_entry_id": None, "correction_required": "Add the delivery location to every requirement."}],
	)
	return world


def _build_accepted() -> dict:
	return _accepted_dpp()


def _build_funding() -> dict:
	frappe.set_user("Administrator")
	return _request_funding(_accepted_item())


def _build_finance_returned() -> dict:
	world = _request_funding(_accepted_item())
	task = world["finance_task"]
	frappe.set_user(fx.FINANCE_OFFICER)
	plan_finance.return_from_finance(task=task.name, reason="Split the laptops across two lines before resubmitting.", task_token=task.task_token, idempotency_key=_key())
	# the returned plan no longer fits its budget line: the Planner's turn is blocked
	for name in frappe.get_all("Plan Source Allocation", filters={"plan_version": world["version"]}, pluck="name"):
		frappe.db.set_value("Plan Source Allocation", name, "indicative_amount", 150_000_000, update_modified=False)
	return world


def _build_signature() -> dict:
	return _confirm_funding(_request_funding(_accepted_item()))


def _build_adoption() -> dict:
	# a second Planner (who also holds the Accounting Officer responsibility) sends the plan to Finance: the owner's rule then
	# stops them adopting it
	world = _request_funding(_accepted_item(), planner=fx.HYBRID_AO)
	return _sign_and_submit(_confirm_funding(world))


def _build_statutory() -> dict:
	world = _sign_and_submit(_confirm_funding(_request_funding(_accepted_item())))
	task = world["ao_task"]
	frappe.set_user(fx.ACCOUNTING_OFFICER)
	adopted = plan_governance.adopt_and_submit_plan(task=task.name, task_token=task.task_token, idempotency_key=_key())
	return {**world, "statutory_task": frappe.get_doc("Plan Governance Task", adopted["statutory_task"])}


def _build_treasury() -> dict:
	world = _build_statutory()
	task = world["statutory_task"]
	frappe.set_user(fx.STATUTORY)
	plan_governance.approve_annual_plan(task=task.name, task_token=task.task_token, idempotency_key=_key())
	return world


def _build_active() -> dict:
	world = _build_treasury()
	frappe.set_user(fx.ACCOUNTING_OFFICER)
	recorded = treasury.record_treasury_submission(
		plan_version=world["version"], submitted_at="2101-11-01 09:00:00", channel="Email", destination="treasury@example.test",
		dispatch_reference="MOH/APP/2101/001", exact_document_confirmed=True, idempotency_key=_key(),
	)
	frappe.set_user("Administrator")
	publication_pipeline.publish_annual_plan(plan_version=world["version"], idempotency_key=_key())
	frappe.set_user(fx.HOD)  # the Head of User Department of a contributing unit asks for a correction
	received = plan_requisition.receive_plan_item_correction_request(
		plan_item_id=world["item"], requisition_reference="REQ-PLNT-HOME-1", requisition_version="RQV-PLNT-HOME-1",
		reason="The authorised warranty period does not match the department's actual need.", idempotency_key=_key(),
	)
	request = frappe.get_doc("Plan Item Correction Request", received["correction_request"])
	frappe.set_user(fx.PLANNER)
	plan_requisition.start_plan_item_correction(correction_request=request.name, expected_record_version=request.record_version, idempotency_key=_key())
	return {**world, "treasury": recorded, "correction_request": request}


def _pin_world(world: dict) -> None:
	"""Fix every event instant the provider reports, so the tests read exact strings."""
	if world.get("submission"):
		_pin("Departmental Plan Submission", world["submission"], "submitted_at", "2027-06-15 09:00")
		_pin("Departmental Plan Validation Task", world["task"].name, "creation", "2027-06-15 09:05")
		for name in frappe.get_all("Departmental Plan Validation Decision", filters={"task": world["task"].name}, pluck="name"):
			_pin("Departmental Plan Validation Decision", name, "decided_at", "2027-06-15 11:00")
	if world.get("finance_task"):
		_pin("Plan Finance Task", world["finance_task"].name, "creation", "2027-06-16 10:00")
		for name in frappe.get_all("Plan Finance Decision", filters={"task": world["finance_task"].name}, pluck="name"):
			_pin("Plan Finance Decision", name, "decided_at", "2027-06-16 14:00")
	if world.get("ao_task"):
		_pin("Plan Governance Task", world["ao_task"].name, "creation", "2027-06-16 15:30")
		for name in frappe.get_all("Plan Preparation Signature", filters={"plan_version": world["version"]}, pluck="name"):
			_pin("Plan Preparation Signature", name, "signed_at", "2027-06-16 15:30")
	if world.get("statutory_task"):
		_pin("Plan Governance Task", world["statutory_task"].name, "creation", "2027-06-17 09:00")
		for name in frappe.get_all("Plan Governance Decision", filters={"plan_version": world["version"], "stage": "Accounting Officer adoption"}, pluck="name"):
			_pin("Plan Governance Decision", name, "decided_at", "2027-06-17 09:00")
	for name in frappe.get_all("Plan Governance Decision", filters={"plan_version": world.get("version") or "", "stage": "Statutory approval"}, pluck="name"):
		_pin("Plan Governance Decision", name, "decided_at", "2027-06-17 16:00")
	if world.get("treasury"):
		for name in frappe.get_all("Treasury Submission Evidence", filters={"plan_version": world["version"]}, pluck="name"):
			_pin("Treasury Submission Evidence", name, "recorded_at", "2027-06-17 17:00")
	if world.get("correction_request"):
		_pin("Plan Item Correction Request", world["correction_request"].name, "requested_at", "2027-06-17 14:00")
		for name in frappe.get_all("Plan Item Correction Disposition", filters={"correction_request": world["correction_request"].name}, pluck="name"):
			_pin("Plan Item Correction Disposition", name, "disposed_at", "2027-06-18 08:00")


def _world_rows() -> dict[str, list[str]]:
	"""Every row of the two test fiscal years that a Planning world adds, by name: what the module's purge must remove."""
	years = (fx.FY_OPEN, fx.FY_CLOSED)
	plans = frappe.get_all("Annual Plan", filters={"fiscal_year": ("in", years)}, pluck="name")
	versions = frappe.get_all("Annual Plan Version", filters={"annual_plan": ("in", plans or ("",))}, pluck="name")
	roots = frappe.get_all("Departmental Plan", filters={"fiscal_year": ("in", years)}, pluck="name")
	dpp_versions = frappe.get_all("Departmental Plan Version", filters={"departmental_plan": ("in", roots or ("",))}, pluck="name")
	by_version = {"plan_version": ("in", versions or ("",))}
	finance_tasks = frappe.get_all("Plan Finance Task", filters=by_version, pluck="name")
	requests = frappe.get_all("Plan Item Correction Request", filters=by_version, pluck="name")
	return {
		"Annual Plan": plans,
		"Annual Plan Version": versions,
		"Departmental Plan": roots,
		"Departmental Plan Version": dpp_versions,
		"Departmental Plan Submission": frappe.get_all("Departmental Plan Submission", filters={"dpp_version": ("in", dpp_versions or ("",))}, pluck="name"),
		"Departmental Plan Validation Task": frappe.get_all("Departmental Plan Validation Task", filters={"fiscal_year": ("in", years)}, pluck="name"),
		"Plan Finance Task": finance_tasks,
		"Plan Finance Decision": frappe.get_all("Plan Finance Decision", filters={"task": ("in", finance_tasks or ("",))}, pluck="name"),
		"Plan Governance Task": frappe.get_all("Plan Governance Task", filters=by_version, pluck="name"),
		"Plan Governance Decision": frappe.get_all("Plan Governance Decision", filters=by_version, pluck="name"),
		"Plan Preparation Signature": frappe.get_all("Plan Preparation Signature", filters=by_version, pluck="name"),
		"Treasury Submission Evidence": frappe.get_all("Treasury Submission Evidence", filters=by_version, pluck="name"),
		"Plan Item Correction Request": requests,
		"Plan Item Correction Disposition": frappe.get_all("Plan Item Correction Disposition", filters={"correction_request": ("in", requests or ("",))}, pluck="name"),
		"Plan Publication": frappe.get_all("Plan Publication", filters=by_version, pluck="name"),
	}


def _remove_world() -> None:
	frappe.set_user("Administrator")
	rows = _world_rows()
	fx.wipe_planning_rows()
	for name in frappe.get_all("User Responsibility Assignment", filters={"user": EXTRA}, pluck="name"):
		purge_doc("User Responsibility Assignment", name)
	for name in frappe.get_all("Contact Email", filters={"email_id": EXTRA}, pluck="parent"):
		frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
	if frappe.db.exists("User", EXTRA):
		frappe.delete_doc("User", EXTRA, force=1, ignore_permissions=True)
	frappe.db.commit()
	left = {doctype: frappe.db.count(doctype, {"name": ("in", names)}) for doctype, names in rows.items() if names}
	left["Planning Command Journal"] = frappe.db.count("Planning Command Journal", {"actor": ("in", fx.ACTORS)})
	left = {doctype: count for doctype, count in left.items() if count}
	if left:
		raise AssertionError(f"Planning Home test rows left behind: {left}")


class PlanningHomeCase(IntegrationTestCase):
	"""One shared world per subclass (`BUILD`), pinned, read by every test; the provider only reads."""

	BUILD = None
	world: dict = {}

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)
		cls.addClassCleanup(_remove_world)
		fx.wipe_planning_rows()
		fx._user(EXTRA, "PLNT Extra Accounting Officer")
		for target, attr, value in (
			(needs_intake, "current_accepted_sources", []),
			(budget_gateway, "eligible_line_ids", {fx.BUDGET_LINE, fx.BUDGET_LINE_2}),
		):
			patched = patch.object(target, attr, return_value=value)
			patched.start()
			cls.addClassCleanup(patched.stop)
		cls.world = cls.BUILD()
		frappe.set_user("Administrator")
		_pin_world(cls.world)
		frappe.db.commit()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		home_support.reset()
		clock = patch.object(home_time, "now", return_value=AT)
		clock.start()
		self.addCleanup(clock.stop)
		self.addCleanup(frappe.set_user, "Administrator")

	# ----- helpers -----

	@property
	def roots(self) -> set[str]:
		return {value for key, value in self.world.items() if key in ("plan", "dpp")}

	def region(self, user: str, region: str):
		home_support.reset()
		return entries(user=user, region=region)

	def mine(self, rows):
		"""The rows about this world's plans (the test site also holds canonical Planning records)."""
		return [row for row in rows or [] if row["root"] in self.roots]

	def one(self, user: str, region: str, *, action_id: str | None = None, action: str | None = None) -> dict:
		rows = [row for row in self.mine(self.region(user, region)) if (action_id is None or row["action_id"] == action_id) and (action is None or row["action"] == action)]
		self.assertEqual(len(rows), 1, f"{user} {region} {action_id or action}: {rows}")
		return rows[0]

	def home(self, user: str, at: datetime = AT):
		return hw.get_workspace(user, providers=[entries], at=at)

	def all_rows(self, user: str, region: str, at: datetime = AT) -> list[dict]:
		"""Every presented row of the region, following Show more (the test site also holds canonical Planning records)."""
		rows, cursor = [], None
		while True:
			page = hw.get_workspace(user, regions=[region], cursors={region: cursor} if cursor else None, providers=[entries], at=at)["regions"][region]
			rows += page["entries"]
			cursor = page["next_cursor"]
			if not cursor:
				return rows

	def row(self, user: str, region: str, reference: str, *, action: str | None = None, at: datetime = AT) -> dict:
		rows = [row for row in self.all_rows(user, region, at) if row["reference"] == reference and (action is None or row["action"] == action)]
		self.assertEqual(len(rows), 1, f"{user} {region} {reference}: {rows}")
		return rows[0]

	def plan_title(self) -> str:
		return frappe.db.get_value("Annual Plan", self.world["plan"], "title")

	def plan_reference(self) -> str:
		version = frappe.db.get_value("Annual Plan Version", self.world["version"], ["annual_plan", "version_number"], as_dict=True)
		return f"{frappe.db.get_value('Annual Plan', version.annual_plan, 'plan_reference')} · Version {version.version_number}"

	def holder(self, text: str, role: str, label: str | None = None) -> None:
		"""`text` is the people who hold `role` site-wide (either order) when there are two or fewer, otherwise the
		responsibility's name. How many people hold it depends on the site."""
		holders = authz.users_with_site_role(role)
		if len(holders) <= 2:
			self.assertEqual(set(text.split(" or ")), {frappe.db.get_value("User", user, "full_name") for user in holders}, text)
		else:
			self.assertEqual(text, label or role)

	def name(self, user: str) -> str:
		return frappe.db.get_value("User", user, "full_name")



class CommonChecks:
	"""What every world must satisfy (a mixin: the base case itself has no tests, so it builds no world)."""

	def test_the_provider_writes_nothing(self):
		frappe.db.commit()
		before = frappe.db.transaction_writes
		for user in (fx.AUTHOR, fx.HOD, fx.PLANNER, fx.FINANCE_OFFICER, fx.ACCOUNTING_OFFICER, fx.STATUTORY, fx.AUDITOR, fx.HOPF, fx.OUTSIDER, fx.HYBRID_AO, fx.BUDGET_OFFICER, "Administrator"):
			for region in REGIONS:
				self.region(user, region)
			self.home(user)
		self.assertEqual(frappe.db.transaction_writes, before)

	def test_the_technical_reader_and_an_unrelated_internal_user_get_nothing(self):
		for user in ("Administrator", fx.BUDGET_OFFICER):
			for region in REGIONS:
				self.assertIsNone(self.region(user, region), (user, region))
		view = self.home("Administrator")
		self.assertEqual((view["empty"], view["regions"]["my_work"]["entries"]), (True, []))
		budget = self.home(fx.BUDGET_OFFICER)
		self.assertEqual(budget["state"], "ready")
		self.assertFalse(any(region["entries"] for region in budget["regions"].values()))
		self.assertEqual({region["coverage"] for region in budget["regions"].values()}, {hw.NOT_APPLICABLE})

	def test_none_versus_empty_by_responsibility_and_no_oversight_or_coming_up(self):
		for user in (fx.AUTHOR, fx.HOD, fx.PLANNER, fx.FINANCE_OFFICER, fx.ACCOUNTING_OFFICER, fx.STATUTORY, fx.AUDITOR, fx.HOPF):
			for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
				self.assertIsInstance(self.region(user, region), list, (user, region))
			for region in (he.OVERSIGHT, he.COMING_UP):
				self.assertIsNone(self.region(user, region), (user, region))
		for region in REGIONS:
			self.assertIsNone(self.region(fx.BUDGET_OFFICER, region), region)
		self.assertEqual(self.mine(self.region(fx.AUDITOR, he.MY_WORK)), [])  # an Auditor holds no item
		self.assertEqual(self.mine(self.region(fx.AUDITOR, he.WAITING)), [])

	def test_every_destination_is_a_page_the_actor_may_open(self):
		for page in SPEC_PAGES:
			self.assertTrue(frappe.db.exists("Page", page), page)
		for user in (fx.AUTHOR, fx.HOD, fx.PLANNER, fx.FINANCE_OFFICER, fx.ACCOUNTING_OFFICER, fx.STATUTORY, fx.HOPF, fx.HYBRID_AO):
			for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
				for row in self.mine(self.region(user, region)):
					self.assertIn(row["destination"]["route"][0], SPEC_PAGES, row)
					self.assertTrue(hw._page_permitted(row["destination"]["route"][0], user), (user, row["destination"]))

	def test_the_scan_runs_once_per_home_read(self):
		calls = []
		original = work.plan_handoff_items

		def counting(user):
			calls.append(user)
			return original(user)

		with patch.object(work, "plan_handoff_items", counting):
			self.home(fx.PLANNER)
		self.assertEqual(calls, [fx.PLANNER])

	def test_the_hand_off_scan_is_the_owners_own(self):
		"""Home's hand-off rows are `my_work_provider`'s: the same ids for the same actor."""
		for user in (fx.PLANNER, fx.HOPF, fx.ACCOUNTING_OFFICER, fx.STATUTORY, fx.HOD, fx.FINANCE_OFFICER):
			legacy = work.my_work_rows(user=user)
			mine = {row["action_id"] for region in (he.MY_WORK, he.WAITING) for row in self.region(user, region) or []}
			owned = {row["task_id"] for bucket in ("assigned", "waiting") for row in legacy[bucket]}
			self.assertLessEqual(mine, owned, user)  # a Home row never exists without the owner's own row


# --------------------------------------------------------------------------
# a departmental plan under Procurement's review
# --------------------------------------------------------------------------


class TestDepartmentalPlanSubmitted(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_dpp_submitted)

	def test_the_planners_validation_task_leads_with_the_department_and_says_when_it_was_received(self):
		row = self.one(fx.PLANNER, he.MY_WORK, action="Validate departmental plan")
		task = self.world["task"]
		self.assertEqual((row["title"], row["reference"], row["action_id"]), (fx.OU_ALPHA_NAME, task.task_reference, task.name))
		self.assertEqual((row["entered_at"], row["entered_verb"], row["blocked"], row["reason"]), (_dt("2027-06-15 09:05"), "Received", False, ""))
		self.assertEqual(row["destination"], {"route": ["procurement-planning", "dpp-review", task.name], "route_options": {}})
		presented = self.row(fx.PLANNER, "my_work", task.task_reference)
		self.assertEqual((presented["title"], presented["action"], presented["timing"], presented["module"]), (fx.OU_ALPHA_NAME, "Validate departmental plan", "Received 3 days ago (15 June, 09:05)", "Planning"))

	def test_the_planner_who_certified_it_is_not_asked_to_validate_it(self):
		# the owner's own segregation rule: HYBRID certified the plan and is also a Procurement Planner
		self.assertFalse(self.mine(self.region(fx.HYBRID, he.MY_WORK)))
		# …but is the Head of User Department who now waits on Procurement
		self.assertEqual(len(self.mine(self.region(fx.HYBRID, he.WAITING))), 1)

	def test_the_head_of_department_waits_on_the_planner_since_the_submission(self):
		waiting = self.one(fx.HOD, he.WAITING)
		self.assertEqual((waiting["action"], waiting["title"], waiting["reference"], waiting["since"]), ("Waiting for Procurement review", fx.OU_ALPHA_NAME, self.world["dpp_reference"], _dt("2027-06-15 09:00")))
		self.holder(waiting["holder"], "Procurement Planner")
		self.assertEqual((waiting["action_id"], waiting["destination"]["route"]), (f"{self.world['dpp']}:waiting:review", ["departmental-procurement-plan", self.world["dpp_reference"]]))
		presented = self.row(fx.HOD, "waiting", self.world["dpp_reference"])
		self.assertEqual(presented["timing"], "Waiting 3 days (since 15 June, 09:00)")

	def test_the_certifier_sees_what_they_did_and_who_it_awaits_and_the_others_do_not(self):
		done = self.one(fx.HYBRID, he.COMPLETED)
		self.assertEqual((done["title"], done["action"], done["completed_at"], done["reference"]), (fx.OU_ALPHA_NAME, "Submitted departmental plan", _dt("2027-06-15 09:00"), self.world["dpp_reference"]))
		prefix = "You certified and submitted this departmental plan to Procurement on 15 June 2027, 09:00 "
		self.assertTrue(done["sentence"].startswith(prefix), done["sentence"])
		clause = done["sentence"].split(". ", 1)[1]
		self.assertTrue(clause.startswith("It is awaiting Procurement review by ") and clause.endswith("."), clause)
		self.holder(clause[len("It is awaiting Procurement review by ") : -1], "Procurement Planner")
		# the Head of Department who did not certify it has taken no decision
		self.assertEqual(self.mine(self.region(fx.HOD, he.COMPLETED)), [])
		self.assertEqual(self.mine(self.region(fx.PLANNER, he.COMPLETED)), [])

	def test_an_author_an_auditor_and_another_departments_author_hold_nothing_of_it(self):
		for user in (fx.AUTHOR, fx.AUDITOR, fx.OUTSIDER, fx.FINANCE_OFFICER, fx.ACCOUNTING_OFFICER):
			self.assertEqual(self.mine(self.region(user, he.MY_WORK)), [], user)
			self.assertEqual(self.mine(self.region(user, he.WAITING)), [], user)


class TestDepartmentalPlanReturned(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_dpp_returned)

	def test_the_head_of_department_and_the_author_are_asked_to_correct_it_since_the_return(self):
		for user in (fx.HOD, fx.AUTHOR):
			row = self.one(user, he.MY_WORK)
			self.assertEqual((row["title"], row["action"], row["reference"], row["entered_at"]), (fx.OU_ALPHA_NAME, "Correct and resubmit departmental plan", self.world["dpp_reference"], _dt("2027-06-15 11:00")), user)
			self.assertEqual((row["action_id"], row["destination"]["route"], row["blocked"]), (f"{self.world['dpp']}:dpp_return", ["departmental-procurement-plan", self.world["dpp_reference"]], False), user)
		presented = self.row(fx.AUTHOR, "my_work", self.world["dpp_reference"])
		self.assertEqual(presented["timing"], "Received 3 days ago (15 June, 11:00)")

	def test_the_planner_who_returned_it_sees_it_and_the_head_of_department_no_longer_waits(self):
		done = self.one(fx.PLANNER, he.COMPLETED)
		self.assertEqual((done["action"], done["title"], done["completed_at"]), ("Returned departmental plan", fx.OU_ALPHA_NAME, _dt("2027-06-15 11:00")))
		self.assertTrue(done["sentence"].startswith("You returned this departmental plan to the department on 15 June 2027, 11:00 ") and done["sentence"].endswith("."), done["sentence"])
		self.assertEqual(self.mine(self.region(fx.HOD, he.WAITING)), [])
		# the certification is a past action and the plan is not waiting on anyone now: no awaiting clause
		certified = self.one(fx.HOD, he.COMPLETED)
		self.assertNotIn("awaiting", certified["sentence"])
		self.assertEqual(self.mine(self.region(fx.PLANNER, he.MY_WORK)), [])  # the task is closed


class TestDepartmentalPlanAcceptedNotYetInThePlan(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_accepted)

	def test_the_planner_is_asked_to_add_the_accepted_requirements_since_a_fallback_instant(self):
		row = self.one(fx.PLANNER, he.MY_WORK)
		version = frappe.db.get_value("Annual Plan Version", self.world["version"], "modified")
		self.assertEqual((row["title"], row["action"], row["reference"], row["blocked"]), (self.plan_title(), "Add accepted requirements to the annual plan", self.plan_reference(), False))
		# nothing records when a requirement became unallocated: the Version's own `modified`, the owner's approximation
		self.assertEqual((row["entered_at"], row["action_id"]), (version, f"{self.world['version']}:add_requirements"))

	def test_the_head_of_department_waits_for_planning_since_the_plan_was_accepted(self):
		waiting = self.one(fx.HOD, he.WAITING)
		self.assertEqual((waiting["action"], waiting["title"], waiting["reference"], waiting["since"]), ("Waiting for planning", fx.OU_ALPHA_NAME, self.world["dpp_reference"], _dt("2027-06-15 11:00")))
		self.holder(waiting["holder"], "Procurement Planner")
		self.assertEqual(waiting["action_id"], f"{self.world['dpp']}:waiting:planning")
		self.assertEqual(self.row(fx.HOD, "waiting", self.world["dpp_reference"])["timing"], "Waiting 3 days (since 15 June, 11:00)")


# --------------------------------------------------------------------------
# the annual plan with Finance
# --------------------------------------------------------------------------


class TestPlanWithFinance(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_funding)

	def test_the_funding_task_leads_with_the_plan_title_and_the_task_reference(self):
		task = self.world["finance_task"]
		row = self.one(fx.FINANCE_OFFICER, he.MY_WORK)
		self.assertEqual((row["title"], row["action"], row["reference"], row["action_id"]), (self.plan_title(), "Confirm plan funding", task.task_reference, task.name))
		self.assertTrue(row["title"] and "Confirm" not in row["title"] and task.task_reference not in row["title"])
		self.assertEqual((row["entered_at"], row["entered_verb"], row["blocked"], row["reason"]), (_dt("2027-06-16 10:00"), "Received", False, ""))
		self.assertEqual(row["destination"], {"route": ["procurement-planning", "finance", task.name], "route_options": {}})
		presented = self.row(fx.FINANCE_OFFICER, "my_work", task.task_reference)
		self.assertEqual((presented["action"], presented["timing"]), ("Confirm plan funding", "Received 2 days ago (16 June, 10:00)"))
		self.assertEqual(self.mine(self.region(fx.AUDITOR, he.MY_WORK)), [])
		self.assertEqual(self.mine(self.region(fx.ACCOUNTING_OFFICER, he.MY_WORK)), [])

	def test_the_planner_waits_for_finance_since_the_task_was_opened(self):
		waiting = self.one(fx.PLANNER, he.WAITING)
		self.assertEqual((waiting["action"], waiting["title"], waiting["reference"], waiting["since"]), ("Waiting for Finance", self.plan_title(), self.plan_reference(), _dt("2027-06-16 10:00")))
		self.holder(waiting["holder"], "Finance Confirmation Officer")
		self.assertEqual((waiting["action_id"], waiting["destination"]["route"]), (f"{self.world['version']}:waiting:funding", ["annual-procurement-plan", frappe.db.get_value("Annual Plan", self.world["plan"], "plan_reference")]))
		presented = self.row(fx.PLANNER, "waiting", self.plan_reference())
		self.assertEqual(presented["timing"], "Waiting 2 days (since 16 June, 10:00)")
		# the officer who holds the task does not wait for themselves
		self.assertEqual(self.mine(self.region(fx.FINANCE_OFFICER, he.WAITING)), [])

	def test_the_planner_sees_the_acceptance_they_gave(self):
		done = self.one(fx.PLANNER, he.COMPLETED)
		self.assertEqual((done["action"], done["title"], done["reference"]), ("Accepted departmental plan", fx.OU_ALPHA_NAME, self.world["dpp_reference"]))
		self.assertTrue(done["sentence"].startswith("You accepted this departmental plan on 15 June 2027, 11:00 ") and done["sentence"].endswith("."), done["sentence"])

	def test_an_accepted_plan_missing_a_later_need_asks_the_department_to_update_it(self):
		# a Need accepted after the plan was: the department's prompt has no recorded event of its own here, so it falls back to the
		# departmental plan's own `modified`
		root = frappe.db.get_value("Departmental Plan", self.world["dpp"], ["modified", "dpp_reference"], as_dict=True)
		with patch.object(needs_intake, "current_accepted_sources", return_value=[fx.accepted_source()]):
			for user in (fx.HOD, fx.AUTHOR):
				row = self.one(user, he.MY_WORK, action_id=f"{self.world['dpp']}:update-required")
				self.assertEqual((row["title"], row["action"], row["reference"]), (fx.OU_ALPHA_NAME, "Update departmental plan", root.dpp_reference), user)
				self.assertEqual((row["entered_at"], row["destination"]["route"], row["blocked"]), (root.modified, ["departmental-procurement-plan", root.dpp_reference], False), user)
		self.assertFalse([row for row in self.mine(self.region(fx.HOD, he.MY_WORK)) if row["action_id"].endswith(":update-required")])


class TestFinanceReturnedAndOverBudget(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_finance_returned)

	def test_the_returned_plan_is_the_planners_turn_blocked_by_the_owners_own_reason(self):
		row = self.one(fx.PLANNER, he.MY_WORK)
		self.assertEqual((row["title"], row["action"], row["reference"]), (self.plan_title(), "Correct the plan returned by Finance", self.plan_reference()))
		self.assertEqual((row["blocked"], row["reason"]), (True, "Over budget by KES 50,000,000 on Digital health programme"))
		self.assertEqual((row["entered_at"], row["action_id"]), (_dt("2027-06-16 14:00"), f"{self.world['version']}:finance_return"))
		self.assertEqual(row["destination"]["route"], ["annual-procurement-plan", frappe.db.get_value("Annual Plan", self.world["plan"], "plan_reference")])
		# the reason is the owner's: the guidance for the same actor says it, word for word
		version = frappe.get_doc("Annual Plan Version", self.world["version"])
		step = plan_read._guidance_for(version, frappe.get_doc("Annual Plan", version.annual_plan), fx.PLANNER)["next_step"]
		self.assertEqual((step["kind"], step["blockers"][0]["headline"]), ("your_turn_blocked", row["reason"]))
		presented = self.row(fx.PLANNER, "my_work", self.plan_reference())
		self.assertEqual((presented["blocked"], presented["reason"], presented["timing"]), (True, row["reason"], "Received 2 days ago (16 June, 14:00)"))

	def test_the_finance_officer_who_returned_it_sees_so_and_waits_for_nothing(self):
		done = self.one(fx.FINANCE_OFFICER, he.COMPLETED)
		self.assertEqual((done["action"], done["title"], done["completed_at"], done["reference"]), ("Returned plan to the Planner", self.plan_title(), _dt("2027-06-16 14:00"), self.plan_reference()))
		self.assertTrue(done["sentence"].startswith("You returned this plan to the Procurement Planner on 16 June 2027, 14:00 ") and done["sentence"].endswith("."), done["sentence"])
		self.assertEqual(self.mine(self.region(fx.FINANCE_OFFICER, he.MY_WORK)), [])


# --------------------------------------------------------------------------
# the signature
# --------------------------------------------------------------------------


class TestPlanAwaitingSignature(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_signature)

	def test_the_signer_is_asked_to_sign_since_finance_confirmed(self):
		row = self.one(fx.HOPF, he.MY_WORK)
		self.assertEqual((row["title"], row["action"], row["reference"], row["blocked"], row["reason"]), (self.plan_title(), "Sign and submit the annual plan", self.plan_reference(), False, ""))
		self.assertEqual((row["entered_at"], row["action_id"]), (_dt("2027-06-16 14:00"), f"{self.world['version']}:sign"))
		presented = self.row(fx.HOPF, "my_work", self.plan_reference())
		self.assertEqual(presented["timing"], "Received 2 days ago (16 June, 14:00)")
		self.assertEqual(self.mine(self.region(fx.PLANNER, he.MY_WORK)), [])

	def test_the_planner_waits_for_the_signature_since_finance_confirmed(self):
		waiting = self.one(fx.PLANNER, he.WAITING)
		self.assertEqual((waiting["action"], waiting["since"], waiting["title"]), ("Waiting for signature", _dt("2027-06-16 14:00"), self.plan_title()))
		self.holder(waiting["holder"], "Head of Procurement Function")
		self.assertEqual(self.row(fx.PLANNER, "waiting", self.plan_reference())["timing"], "Waiting 2 days (since 16 June, 14:00)")

	def test_the_finance_officer_sees_the_confirmation_and_no_awaiting_clause(self):
		# the owner's answer for the officer is not a wait they hold, so the sentence stops
		done = self.one(fx.FINANCE_OFFICER, he.COMPLETED)
		self.assertEqual((done["action"], done["reference"]), ("Confirmed plan funding", self.plan_reference()))
		self.assertTrue(done["sentence"].startswith("You confirmed funding for this plan on 16 June 2027, 14:00 ") and done["sentence"].endswith("."), done["sentence"])
		self.assertNotIn("awaiting", done["sentence"])


# --------------------------------------------------------------------------
# the Accounting Officer's adoption
# --------------------------------------------------------------------------


class TestPlanAwaitingAdoption(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_adoption)

	def test_the_adoption_task_is_worded_by_the_owner_without_the_plan_title(self):
		task = self.world["ao_task"]
		row = self.one(fx.ACCOUNTING_OFFICER, he.MY_WORK)
		self.assertEqual((row["title"], row["action"], row["reference"], row["action_id"]), (self.plan_title(), "Adopt Annual Procurement Plan", task.task_reference, task.name))
		self.assertEqual((row["entered_at"], row["entered_verb"], row["blocked"], row["reason"]), (_dt("2027-06-16 15:30"), "Received", False, ""))
		self.assertEqual(row["destination"], {"route": ["procurement-planning", "review", task.name], "route_options": {}})
		presented = self.row(fx.ACCOUNTING_OFFICER, "my_work", task.task_reference)
		self.assertEqual((presented["action"], presented["timing"], presented["blocked"]), ("Adopt Annual Procurement Plan", "Received 2 days ago (16 June, 15:30)", False))

	def test_no_one_else_holds_the_adoption(self):
		for user in (fx.FINANCE_OFFICER, fx.AUDITOR, fx.STATUTORY, fx.HOPF, fx.PLANNER):
			self.assertEqual(self.mine(self.region(user, he.MY_WORK)), [], user)

	def test_a_planner_who_prepared_the_plan_and_holds_the_office_is_not_asked_to_adopt_it_but_waits(self):
		# the owner's segregation rule: HYBRID_AO sent the plan to Finance
		self.assertEqual(self.mine(self.region(fx.HYBRID_AO, he.MY_WORK)), [])
		waiting = self.one(fx.HYBRID_AO, he.WAITING)
		self.assertEqual(waiting["action"], "Waiting for adoption")

	def test_a_missing_approval_authority_blocks_the_adoption_with_the_owners_reason(self):
		with patch.object(plan_governance, "statutory_route_configured", return_value=False):
			row = self.one(fx.ACCOUNTING_OFFICER, he.MY_WORK)
			version = frappe.get_doc("Annual Plan Version", self.world["version"])
			step = plan_read._guidance_for(version, frappe.get_doc("Annual Plan", version.annual_plan), fx.ACCOUNTING_OFFICER)["next_step"]
		self.assertEqual((step["kind"], row["blocked"]), ("your_turn_blocked", True))
		self.assertEqual(row["reason"], step["blockers"][0]["headline"])
		self.assertTrue(row["reason"])
		self.assertEqual(row["action"], "Adopt Annual Procurement Plan")

	def test_stale_funding_evidence_blocks_the_adoption_and_says_to_return_the_plan(self):
		with patch.object(plan_finance, "funding_is_current", return_value=False):
			row = self.one(fx.ACCOUNTING_OFFICER, he.MY_WORK)
			presented = self.row(fx.ACCOUNTING_OFFICER, "my_work", self.world["ao_task"].task_reference)
		self.assertEqual((row["blocked"], row["reason"]), (True, "Return the plan for a new funding check"))
		self.assertEqual((presented["blocked"], presented["reason"]), (True, "Return the plan for a new funding check"))

	def test_the_planner_and_the_signer_wait_for_the_adoption_since_the_task_was_opened(self):
		for user in (fx.PLANNER, fx.HOPF):
			waiting = self.one(user, he.WAITING)
			self.assertEqual((waiting["action"], waiting["title"], waiting["reference"], waiting["since"]), ("Waiting for adoption", self.plan_title(), self.plan_reference(), _dt("2027-06-16 15:30")), user)
			self.holder(waiting["holder"], "Accounting Officer")
			self.assertEqual(waiting["action_id"], f"{self.world['version']}:waiting:ao", user)
		self.assertEqual(self.row(fx.HOPF, "waiting", self.plan_reference())["timing"], "Waiting 2 days (since 16 June, 15:30)")
		# the officer who holds the adoption does not wait for it
		self.assertEqual(self.mine(self.region(fx.ACCOUNTING_OFFICER, he.WAITING)), [])

	def test_the_signer_sees_the_signature_and_who_adoption_awaits(self):
		done = self.one(fx.HOPF, he.COMPLETED)
		self.assertEqual((done["action"], done["title"], done["reference"], done["completed_at"]), ("Signed and submitted annual plan", self.plan_title(), self.plan_reference(), _dt("2027-06-16 15:30")))
		prefix = "You signed and submitted this annual plan on 16 June 2027, 15:30 "
		self.assertTrue(done["sentence"].startswith(prefix), done["sentence"])
		clause = done["sentence"].split(". ", 1)[1]
		self.assertTrue(clause.startswith("It is awaiting adoption by ") and clause.endswith("."), clause)
		self.holder(clause[len("It is awaiting adoption by ") : -1], "Accounting Officer")

	def test_a_responsibility_granted_shows_the_task_and_one_revoked_removes_it(self):
		reference = self.world["ao_task"].task_reference
		administration.grant(user=EXTRA, business_role="Accounting Officer", fixture_namespace=EXTRA_NS, actor="Administrator")
		self.assertEqual(self.row(EXTRA, "my_work", reference)["action"], "Adopt Annual Procurement Plan")
		self.assertTrue(self.home(EXTRA)["regions"]["my_work"]["applicable"])
		assignment = frappe.get_all("User Responsibility Assignment", filters={"user": EXTRA}, pluck="name")[0]
		administration.revoke(assignment, reason="Revoked inside the Home provider test.", actor="Administrator")
		revoked = self.home(EXTRA)
		self.assertEqual({region["coverage"] for region in revoked["regions"].values()}, {hw.NOT_APPLICABLE})
		self.assertFalse([row for region in revoked["regions"].values() for row in region["entries"] if row["reference"] == reference])
		self.assertIsNone(self.region(EXTRA, he.MY_WORK))


# --------------------------------------------------------------------------
# the statutory approval
# --------------------------------------------------------------------------


class TestPlanAwaitingApproval(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_statutory)

	def test_the_approver_is_asked_to_approve_since_the_adoption(self):
		task = self.world["statutory_task"]
		row = self.one(fx.STATUTORY, he.MY_WORK)
		self.assertEqual((row["title"], row["action"], row["reference"], row["action_id"]), (self.plan_title(), "Approve Annual Procurement Plan", task.task_reference, task.name))
		self.assertEqual((row["entered_at"], row["blocked"]), (_dt("2027-06-17 09:00"), False))
		self.assertEqual(row["destination"], {"route": ["procurement-planning", "review", task.name], "route_options": {}})
		self.assertEqual(self.row(fx.STATUTORY, "my_work", task.task_reference)["timing"], "Received yesterday (17 June, 09:00)")
		# the adopter does not approve their own adoption, and the Accounting Officer has no item now
		self.assertEqual(self.mine(self.region(fx.ACCOUNTING_OFFICER, he.MY_WORK)), [])

	def test_the_accounting_officer_waits_for_the_approval_and_the_sentence_says_who_it_awaits(self):
		waiting = self.one(fx.ACCOUNTING_OFFICER, he.WAITING)
		self.assertEqual((waiting["action"], waiting["since"], waiting["title"], waiting["reference"]), ("Waiting for approval", _dt("2027-06-17 09:00"), self.plan_title(), self.plan_reference()))
		label = plan_governance.STATUTORY_HOLDER_LABEL.get(plan_governance.statutory_route(), "Statutory authority")
		self.holder(waiting["holder"], "Plan Statutory Approver", label)
		done = self.one(fx.ACCOUNTING_OFFICER, he.COMPLETED)
		self.assertEqual((done["action"], done["completed_at"]), ("Adopted Annual Procurement Plan", _dt("2027-06-17 09:00")))
		self.assertTrue(done["sentence"].startswith("You adopted this Annual Procurement Plan and submitted it for approval on 17 June 2027, 09:00 "), done["sentence"])
		clause = done["sentence"].split(". ", 1)[1]
		self.assertTrue(clause.startswith("It is awaiting approval by ") and clause.endswith("."), clause)
		self.holder(clause[len("It is awaiting approval by ") : -1], "Plan Statutory Approver", label)


class TestPlanApprovedAwaitingTreasury(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_treasury)

	def test_the_accounting_officer_is_asked_to_record_the_treasury_submission_since_the_approval(self):
		row = self.one(fx.ACCOUNTING_OFFICER, he.MY_WORK)
		self.assertEqual((row["title"], row["action"], row["reference"], row["blocked"]), (self.plan_title(), "Record the Treasury submission", self.plan_reference(), False))
		self.assertEqual((row["entered_at"], row["action_id"]), (_dt("2027-06-17 16:00"), f"{self.world['version']}:treasury"))
		self.assertEqual(self.row(fx.ACCOUNTING_OFFICER, "my_work", self.plan_reference())["timing"], "Received yesterday (17 June, 16:00)")

	def test_the_approver_sees_the_approval(self):
		done = self.one(fx.STATUTORY, he.COMPLETED)
		self.assertEqual((done["action"], done["completed_at"]), ("Approved Annual Procurement Plan", _dt("2027-06-17 16:00")))
		self.assertTrue(done["sentence"].startswith("You approved this Annual Procurement Plan on 17 June 2027, 16:00 ") and done["sentence"].endswith("."), done["sentence"])


# --------------------------------------------------------------------------
# the plan in force
# --------------------------------------------------------------------------


class TestPlanInForce(CommonChecks, PlanningHomeCase):
	BUILD = staticmethod(_build_active)

	def test_a_correction_request_is_the_planners_review_titled_by_the_plan_item(self):
		request = self.world["correction_request"]
		row = self.one(fx.PLANNER, he.MY_WORK, action_id=request.name)
		self.assertEqual((row["title"], row["action"], row["reference"]), ("Test procurement package", "Review correction request", "REQ-PLNT-HOME-1"))
		self.assertEqual((row["entered_at"], row["blocked"], row["destination"]["route"]), (_dt("2027-06-17 14:00"), False, ["procurement-planning", "correction-request", request.name]))
		self.assertEqual(self.row(fx.PLANNER, "my_work", "REQ-PLNT-HOME-1")["timing"], "Received yesterday (17 June, 14:00)")
		self.assertEqual(self.mine(self.region(fx.AUDITOR, he.MY_WORK)), [])

	def test_the_planner_sees_the_work_they_started_and_the_officer_the_treasury_record(self):
		started = [row for row in self.mine(self.region(fx.PLANNER, he.COMPLETED)) if row["action"] == "Started correction request"]
		self.assertEqual(len(started), 1)
		self.assertEqual((started[0]["title"], started[0]["reference"], started[0]["completed_at"]), ("Test procurement package", "REQ-PLNT-HOME-1", _dt("2027-06-18 08:00")))
		self.assertTrue(started[0]["sentence"].startswith("You started work on this plan item correction request on 18 June 2027, 08:00 ") and started[0]["sentence"].endswith("."), started[0]["sentence"])
		recorded = self.one(fx.ACCOUNTING_OFFICER, he.COMPLETED, action="Recorded Treasury submission")
		self.assertEqual((recorded["title"], recorded["reference"], recorded["completed_at"]), (self.plan_title(), self.plan_reference(), _dt("2027-06-17 17:00")))
		self.assertTrue(recorded["sentence"].startswith("You recorded the Treasury submission of this Annual Procurement Plan on 17 June 2027, 17:00 "), recorded["sentence"])

	def test_an_actor_who_can_no_longer_read_the_plan_sees_none_of_what_they_did(self):
		# the Planner's start of the correction is theirs; a user with no Planning read gets nothing, and an old action is outside 30 days
		request = self.world["correction_request"]
		disposition = frappe.get_all("Plan Item Correction Disposition", filters={"correction_request": request.name}, pluck="name")[0]
		frappe.db.set_value("Plan Item Correction Disposition", disposition, "actor", fx.OUTSIDER, update_modified=False)
		self.addCleanup(frappe.db.set_value, "Plan Item Correction Disposition", disposition, "actor", fx.PLANNER, update_modified=False)
		self.assertEqual([row for row in self.mine(self.region(fx.OUTSIDER, he.COMPLETED)) if row["action"] == "Started correction request"], [])
		frappe.db.set_value("Plan Item Correction Disposition", disposition, {"actor": fx.PLANNER, "disposed_at": _dt("2027-05-01 08:00")}, update_modified=False)
		self.addCleanup(frappe.db.set_value, "Plan Item Correction Disposition", disposition, "disposed_at", _dt("2027-06-18 08:00"), update_modified=False)
		self.assertEqual([row for row in self.mine(self.region(fx.PLANNER, he.COMPLETED)) if row["action"] == "Started correction request"], [])
