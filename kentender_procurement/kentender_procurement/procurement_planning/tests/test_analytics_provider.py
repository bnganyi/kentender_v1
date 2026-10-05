# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §4, §4A, §7.1 — the Procurement Planning feed to Analytics (`procurement_planning/services/analytics_provider.py`,
kinds `departmental_plans` and `plan_items`).

One shared world, built once in `setUpClass` inside the module's own far-future test years (`fixtures.py`: 2101-2102 and 2103-2104)
and read by every test; the provider only reads, so the rows it reads are inserted directly, with the instants and amounts the
assertions name (the same practice as the Home provider test). The world:

- three departmental plans: Alpha's accepted plan with an update being prepared, Beta's accepted plan whose submission carries two
  accept decisions, and Alpha's not-yet-accepted plan in the closed year;
- Annual Plan X (year 2101-2102): Active Version 1 with five Active items and two items that are not (superseded, dissolved), and a
  candidate Version 2 that repeats one item at a different value and adds an item of its own; Annual Plan Y (closed year) with no
  Active Version at all;
- the combined two-department item, a Reversed drawdown, a drawdown with cents, a superseded invitation actual and two proceedings
  for one item.

The module's own personas (`fixtures.py`) are read as themselves, the seeded actors (Daniel Otieno, Brian Wafula) as themselves, and a
test-only user is granted and revoked inside one test. Everything the class made is removed by the module's own wipe and counted.

Run:
  flock /tmp/kt-test-site.lock bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.procurement_planning.tests.test_analytics_provider
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_core.services import analytics_contract as ac
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.procurement_planning.services import analytics_provider as provider
from kentender_procurement.procurement_planning.services import dpp_read
from kentender_procurement.procurement_planning.tests import fixtures as fx

NS = "KT_TEST_PLNANL"
TECHNICAL_OPERATOR = "daniel.otieno@moh.example.test"
OFFICER = "brian.wafula@moh.example.test"  # a Procurement Officer: no Planning responsibility
EXTRA = "plna.extra@example.test"  # a Departmental Author of Alpha, granted and revoked inside one test
PLAN = "PLN-ANLT-2101-001"
PLAN_Y = "PLN-ANLT-2103-001"
V1, V2 = f"{PLAN}-V1", f"{PLAN}-V2"
YEARS = (fx.FY_OPEN, fx.FY_CLOSED)

ACCEPTED_A = datetime(2101, 12, 2, 10, 0)
ACCEPTED_B_FIRST = datetime(2101, 12, 3, 10, 0)
ACCEPTED_B_LATEST = datetime(2101, 12, 4, 8, 30)

# stable item ids
SERVERS, PERIPHERALS, CLINIC, MONITORS, SUPERSEDED, DISSOLVED, CANDIDATE_ONLY = (f"PPI-ANLT-{n:03d}" for n in range(1, 8))
PLAN_TABLES = (
	"Departmental Plan", "Departmental Plan Version", "Departmental Plan Submission", "Departmental Plan Validation Task", "Departmental Plan Validation Decision",
	"Annual Plan", "Annual Plan Version", "Annual Plan Item", "Plan Item", "Plan Source Allocation", "Plan Drawdown Reference", "Milestone Actual Event",
	"Proceeding Coverage", "Planning Command Journal", "Plan Item Correction Request",
)


def _counts() -> dict[str, int]:
	counts = {doctype: frappe.db.count(doctype) for doctype in PLAN_TABLES}
	counts["DefaultValue"] = frappe.db.count("DefaultValue")  # a working-context preference would be written here
	counts["Notification Log"] = frappe.db.count("Notification Log")
	counts["assignments"] = frappe.db.count("User Responsibility Assignment")
	return counts


def _ins(doctype: str, **values: Any) -> str:
	"""A row as the module would hold it. Mandatory values the provider never reads and links to rows this world does not need
	(budget line, requirement type, the DPP entry behind an allocation) are not built."""
	doc = frappe.get_doc({"doctype": doctype, "fixture_namespace": fx.NS, **values})
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	return doc.name


class TestPlanningAnalytics(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)
		fx.wipe_planning_rows()  # whatever a crashed earlier run left in the test years
		cls.before = _counts()
		cls.addClassCleanup(cls.check_clean)
		cls.addClassCleanup(cls.remove_extra)
		cls.build_departmental_plans()
		cls.build_annual_plan()
		frappe.db.commit()
		cls.at = now_datetime()

	@classmethod
	def check_clean(cls) -> None:
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		frappe.db.commit()
		after = _counts()
		if after != cls.before:
			raise AssertionError(f"Planning Analytics test rows left behind: before {cls.before}, after {after}")

	@classmethod
	def remove_extra(cls) -> None:
		frappe.set_user("Administrator")
		for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": NS}, pluck="name"):
			if frappe.db.get_value("User Responsibility Assignment", name, "status") == "Enabled":
				administration.revoke(name, reason="Revoked inside the Planning Analytics test.", actor="Administrator")
			frappe.delete_doc("User Responsibility Assignment", name, force=1, ignore_permissions=True)
		for name in frappe.get_all("Contact Email", filters={"email_id": EXTRA}, pluck="parent"):
			frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
		if frappe.db.exists("User", EXTRA):
			frappe.delete_doc("User", EXTRA, force=1, ignore_permissions=True)
		frappe.db.delete("DefaultValue", {"parent": EXTRA})
		frappe.db.commit()

	# ----- the world: departmental plans -----

	@classmethod
	def dpp(cls, suffix: str, unit: str, year: str, *, state: str, accepted: list[datetime] = (), candidate: bool = False) -> str:
		"""A departmental plan root; with `accepted` decisions its version 1 is Accepted and carries them on its submission."""
		reference = f"DPP-ANLT-{suffix}"
		v1 = f"{reference}-V1"
		_ins("Departmental Plan", dpp_reference=reference, organisation_unit=unit, fiscal_year=year, current_state=state, record_version=1,
			current_version=f"{reference}-V2" if candidate else v1, current_accepted_version=v1 if accepted else None)
		submission = f"{reference}-S1"
		_ins("Departmental Plan Version", version_reference=v1, departmental_plan=reference, version_number=1, record_version=1,
			version_status="Accepted" if accepted else "Submitted", submission=submission)
		if candidate:
			_ins("Departmental Plan Version", version_reference=f"{reference}-V2", departmental_plan=reference, version_number=2, version_status="Draft", record_version=1, based_on_version=v1)
		_ins("Departmental Plan Submission", submission_reference=submission, dpp_version=v1, submission_number=1, entry_snapshots="[]", content_hash="x" * 8,
			attestation_text="Certified for the analytics fixture.", submitted_by_user="Administrator", authority_snapshot="{}", submitted_at=datetime(2101, 11, 30, 9, 0))
		task = f"{reference}-T1"
		_ins("Departmental Plan Validation Task", task_reference=task, submission=submission, dpp_version=v1, organisation_unit=unit, fiscal_year=year,
			status="Completed" if accepted else "Open", task_token="t" * 8, record_version=1)
		for index, at in enumerate(accepted):
			_ins("Departmental Plan Validation Decision", decision_reference=f"{reference}-D{index}", task=task, submission=submission, decision="Accept departmental plan",
				actor="Administrator", authority_snapshot="{}", decided_at=at, command_idempotency_key=f"plna-{suffix}-{index}")
		# a Return decision never counts as an acceptance
		_ins("Departmental Plan Validation Decision", decision_reference=f"{reference}-R", task=task, submission=submission, decision="Return to department",
			actor="Administrator", authority_snapshot="{}", decided_at=datetime(2101, 12, 20, 9, 0), command_idempotency_key=f"plna-{suffix}-return")
		return reference

	@classmethod
	def build_departmental_plans(cls) -> None:
		cls.dpps = {
			"alpha": cls.dpp("ALPHA", fx.OU_ALPHA, fx.FY_OPEN, state="Accepted", accepted=[ACCEPTED_A], candidate=True),
			"beta": cls.dpp("BETA", fx.OU_BETA, fx.FY_OPEN, state="Accepted", accepted=[ACCEPTED_B_FIRST, ACCEPTED_B_LATEST]),
			"alpha_closed": cls.dpp("ALPHA-CLOSED", fx.OU_ALPHA, fx.FY_CLOSED, state="Submitted"),
		}

	# ----- the world: the annual plan -----

	@classmethod
	def item(cls, item_id: str, title: str, version: str, *, state: str = "Active", baseline: date | None = None, allocations: list[tuple[str, str, str]] = ()) -> str:
		"""An Annual Plan Item in `version` with its source allocations: (unit, amount, allocation_state)."""
		name = _ins("Annual Plan Item", plan_item_id=item_id, plan_version=version, plan_item=item_id, title=title, description="Procure the analytics fixture item.",
			item_state=state, baseline_invitation_date=baseline, record_version=1)
		for index, (unit, amount, allocation_state) in enumerate(allocations):
			cls.allocations[(item_id, version, index)] = _ins(
				"Plan Source Allocation", allocation_id=f"{item_id}-{version[-2:]}-A{index}", plan_item=name, plan_item_id=item_id, plan_version=version,
				source_origin="Direct departmental requirement", organisation_unit=unit, quantity=1, unit="Each", required_by_date=date(2102, 4, 30),
				budget_line=fx.BUDGET_LINE, indicative_amount=amount, allocation_state=allocation_state,
			)
		cls.items[(item_id, version)] = name
		return name

	@classmethod
	def draw(cls, item_id: str, index: int, amount: str, *, state: str = "Active") -> str:
		allocation = cls.allocations[(item_id, V1, index)]
		unit = frappe.db.get_value("Plan Source Allocation", allocation, "organisation_unit")
		cls.drawn += 1
		return _ins("Plan Drawdown Reference", plan_item=cls.items[(item_id, V1)], plan_item_id=item_id, allocation=allocation, requisition_reference=f"REQ-ANLT-{cls.drawn}",
			requesting_org_unit=unit, quantity="1", amount=amount, drawdown_state=state, record_version=1)

	@classmethod
	def invitation(cls, item_id: str, proceeding: str, actual: date, *, event_id: str, sequence: int = 1, supersedes: str = "") -> str:
		return _ins("Milestone Actual Event", producer="tenders", event_id=event_id, schema_version="MilestoneActualEvent.v1", proceeding_type="Tender", proceeding_id=proceeding,
			plan_version=V1, plan_item=item_id, plan_item_id=item_id, milestone="invitation", actual_date=actual, recorded_at=datetime(2101, 10, 20, 9, 0),
			producer_sequence=sequence, supersedes_event_id=supersedes)

	@classmethod
	def build_annual_plan(cls) -> None:
		cls.items, cls.allocations, cls.drawn = {}, {}, 0
		alpha, beta = fx.OU_ALPHA, fx.OU_BETA
		_ins("Annual Plan", plan_reference=PLAN, title="Test Procurement Plan 2101/02", fiscal_year=fx.FY_OPEN, active_version=V1, open_successor_version=V2, record_version=1)
		_ins("Annual Plan Version", version_reference=V1, annual_plan=PLAN, version_number=1, version_status="Active", funding_state="Confirmed", record_version=1, activated_at=datetime(2101, 12, 10, 15, 0))
		_ins("Annual Plan Version", version_reference=V2, annual_plan=PLAN, version_number=2, version_status="Draft", funding_state="Not requested", record_version=1, based_on_version=V1)
		for item_id in (SERVERS, PERIPHERALS, CLINIC, MONITORS, SUPERSEDED, DISSOLVED, CANDIDATE_ONLY):
			_ins("Plan Item", plan_item_id=item_id, plan_item_reference=item_id, annual_plan=PLAN, record_version=1)
		# --- the operative Active Version
		cls.item(SERVERS, "Servers", V1, baseline=date(2101, 9, 1), allocations=[(alpha, "80000000", "Active")])
		cls.item(PERIPHERALS, "IT peripherals", V1, baseline=date(2101, 9, 15), allocations=[(beta, "25000000", "Active"), (alpha, "40000000", "Active")])  # combined; Alpha leads
		cls.item(CLINIC, "Clinic equipment", V1, allocations=[(alpha, "12000000", "Active"), (beta, "5000000", "Released")])
		cls.item(MONITORS, "Monitors", V1, baseline=date(2101, 10, 1), allocations=[(beta, "7500000", "Active")])
		cls.item(SUPERSEDED, "Superseded purchase", V1, state="Superseded", allocations=[(alpha, "1000000", "Superseded")])
		cls.item(DISSOLVED, "Dissolved purchase", V1, state="Dissolved", allocations=[(alpha, "2000000", "Draft")])
		# --- the candidate Version 2: the same stable item at another value, and an item of its own
		cls.item(SERVERS, "Servers (candidate)", V2, state="Draft", allocations=[(alpha, "99000000", "Draft")])
		cls.item(CANDIDATE_ONLY, "Candidate only purchase", V2, state="Draft", allocations=[(alpha, "3000000", "Draft")])
		# --- authorised drawdowns (the U14 basis)
		cls.draw(SERVERS, 0, "80000000")
		cls.draw(PERIPHERALS, 0, "25000000", state="Reversed")  # Beta's drawdown was reversed: covers nothing...
		cls.draw(PERIPHERALS, 0, "10000000.50")  # ...until a smaller one is authorised
		cls.draw(PERIPHERALS, 1, "40000000")
		cls.draw(MONITORS, 0, "7500000")
		# --- invitation actuals: Servers 7 days late; Monitors two proceedings, the first corrected by a later event; nothing for the others
		cls.invitation(SERVERS, "TND-ANLT-1", date(2101, 9, 8), event_id="e1")
		cls.invitation(MONITORS, "TND-ANLT-2", date(2101, 10, 10), event_id="m1")
		cls.invitation(MONITORS, "TND-ANLT-2", date(2101, 10, 1), event_id="m2", sequence=2, supersedes="m1")  # on the approved date
		cls.invitation(MONITORS, "TND-ANLT-3", date(2101, 11, 5), event_id="m3")  # a second Tender, 35 days late
		# --- a plan with no Active Version (closed year)
		_ins("Annual Plan", plan_reference=PLAN_Y, title="Closed-year Plan", fiscal_year=fx.FY_CLOSED, record_version=1)
		_ins("Annual Plan Version", version_reference=f"{PLAN_Y}-V1", annual_plan=PLAN_Y, version_number=1, version_status="Draft", funding_state="Not requested", record_version=1)
		_ins("Annual Plan Item", plan_item_id="PPI-ANLT-Y01", plan_version=f"{PLAN_Y}-V1", title="Unapproved purchase", description="Procure the analytics fixture item.", item_state="Active", record_version=1)

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")

	# ----- helpers -----

	def read(self, user: str, kind: str) -> list[dict[str, Any]]:
		"""The records the actor gets, as the actor, validated, then only the test years' (the seeded plan is not under test here)."""
		result = provider.facts(user=user, kind=kind, at=self.at)
		for record in result["records"]:
			ac.validate(record)
		return [record for record in result["records"] if record["fiscal_year"] in YEARS]

	def by_ref(self, user: str, kind: str) -> dict[str, dict[str, Any]]:
		return {record["reference"]: record for record in self.read(user, kind)}

	def plan_items(self, user: str = "Administrator") -> dict[str, dict[str, Any]]:
		return self.by_ref(user, ac.PLAN_ITEMS)

	ALL_KINDS = {ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS}

	# ----- departmental plans -----

	def test_one_accepted_record_per_root_with_its_accepted_submissions_decision_instant(self):
		records = self.by_ref("Administrator", ac.DEPARTMENTAL_PLANS)
		self.assertEqual(set(records), {self.dpps["alpha"], self.dpps["beta"]})  # the plan whose first submission is still open has none
		alpha = records[self.dpps["alpha"]]
		self.assertEqual(
			(alpha["kind"], alpha["id"], alpha["state"], alpha["fiscal_year"], alpha["org_units"], alpha["route"], alpha["accepted_at"]),
			("departmental_plans", self.dpps["alpha"], "Accepted", fx.FY_OPEN, [fx.OU_ALPHA], ["departmental-procurement-plan", self.dpps["alpha"]], ACCEPTED_A),
		)
		self.assertEqual(alpha["title"], f"{frappe.db.get_value('Organisation Unit', fx.OU_ALPHA, 'unit_name')} departmental plan")

	def test_an_update_in_preparation_does_not_replace_the_accepted_instant_and_a_return_is_not_an_acceptance(self):
		# Alpha has a Draft Version 2 beside its accepted Version 1, and a Return decision dated after the accept
		self.assertEqual(self.by_ref("Administrator", ac.DEPARTMENTAL_PLANS)[self.dpps["alpha"]]["accepted_at"], ACCEPTED_A)

	def test_when_a_submission_has_several_accept_decisions_the_latest_is_used(self):
		self.assertEqual(self.by_ref("Administrator", ac.DEPARTMENTAL_PLANS)[self.dpps["beta"]]["accepted_at"], ACCEPTED_B_LATEST)

	# ----- plan items -----

	def test_only_the_active_versions_active_items_are_counted_never_the_candidate(self):
		records = self.plan_items()
		self.assertEqual(set(records), {"PPI-ANLT-001", "PPI-ANLT-002", "PPI-ANLT-003", "PPI-ANLT-004"})  # not the superseded, dissolved, candidate-only or unapproved ones
		self.assertEqual(records[SERVERS]["planned_value"], Decimal("80000000"))  # not the candidate's 99,000,000
		self.assertEqual(records[SERVERS]["title"], "Servers")
		for record in records.values():
			self.assertEqual((record["kind"], record["plan_title"], record["plan_version"], record["fiscal_year"]), ("plan_items", "Test Procurement Plan 2101/02", 1, fx.FY_OPEN))
			self.assertEqual(record["route"], ["procurement-plan-item", record["reference"]])

	def test_planned_value_is_the_sum_of_active_allocations_in_exact_decimals(self):
		records = self.plan_items()
		self.assertEqual(records[PERIPHERALS]["planned_value"], Decimal("65000000"))
		self.assertEqual(records[CLINIC]["planned_value"], Decimal("12000000"))  # its Released 5,000,000 is not planned scope
		for record in records.values():
			self.assertIsInstance(record["planned_value"], Decimal)
			self.assertEqual(record["planned_value"], sum((a["planned"] for a in record["allocations"]), Decimal(0)))

	def test_a_combined_item_splits_by_department_largest_share_first(self):
		item = self.plan_items()[PERIPHERALS]
		self.assertEqual(item["org_units"], [fx.OU_ALPHA, fx.OU_BETA])  # Alpha leads with 40,000,000 though Beta was recorded first
		self.assertEqual(
			item["allocations"],
			[{"org_unit": fx.OU_ALPHA, "planned": Decimal("40000000"), "covered": Decimal("40000000")},
			{"org_unit": fx.OU_BETA, "planned": Decimal("25000000"), "covered": Decimal("10000000.50")}],
		)
		self.assertEqual(self.plan_items()[CLINIC]["org_units"], [fx.OU_ALPHA])

	def test_covered_is_authorised_drawdown_by_allocation_and_a_reversed_drawdown_covers_nothing(self):
		records = self.plan_items()
		self.assertEqual(records[SERVERS]["allocations"], [{"org_unit": fx.OU_ALPHA, "planned": Decimal("80000000"), "covered": Decimal("80000000")}])
		# Beta's 25,000,000 drawdown was reversed: only the 10,000,000.50 one that followed counts
		self.assertEqual({a["org_unit"]: a["covered"] for a in records[PERIPHERALS]["allocations"]}[fx.OU_BETA], Decimal("10000000.50"))
		self.assertEqual(records[CLINIC]["allocations"], [{"org_unit": fx.OU_ALPHA, "planned": Decimal("12000000"), "covered": Decimal(0)}])
		self.assertEqual(frappe.db.count("Proceeding Coverage", {"plan_item_id": ("in", [SERVERS, PERIPHERALS, CLINIC, MONITORS])}), 0)  # not the table it reads from

	def test_has_proceeding_means_an_authorised_drawdown_exists_whether_or_not_a_tender_is_published(self):
		records = self.plan_items()
		self.assertTrue(records[PERIPHERALS]["has_proceeding"])  # authorised, no invitation actual
		self.assertIsNone(records[PERIPHERALS]["invitation_days"])  # "No date recorded"
		self.assertFalse(records[CLINIC]["has_proceeding"])  # nothing authorised: left out of the timing chart
		self.assertIsNone(records[CLINIC]["invitation_days"])
		self.assertTrue(records[SERVERS]["has_proceeding"])

	def test_invitation_days_is_plannings_baseline_lateness_per_item(self):
		records = self.plan_items()
		self.assertEqual(records[SERVERS]["invitation_days"], 7)  # 8 Sep actual against the 1 Sep approved date
		self.assertEqual(records[SERVERS]["invitation_actuals"], [{"proceeding_id": "TND-ANLT-1", "days": 7}])

	def test_a_superseded_actual_is_not_used_and_the_earliest_of_several_proceedings_is_the_items_value(self):
		item = self.plan_items()[MONITORS]
		self.assertEqual(item["invitation_days"], 0)  # the corrected 1 Oct actual, not the superseded 10 Oct one; and not the second Tender's +35
		self.assertEqual(item["invitation_actuals"], [{"proceeding_id": "TND-ANLT-2", "days": 0}, {"proceeding_id": "TND-ANLT-3", "days": 35}])

	def test_a_plan_with_no_active_version_yields_no_records_and_no_active_plan_is_an_empty_set(self):
		self.assertFalse([r for r in self.plan_items() if r.startswith("PPI-ANLT-Y")])
		self.assertNotIn(fx.FY_CLOSED, {r["fiscal_year"] for r in self.plan_items().values()})
		frappe.db.set_value("Annual Plan", PLAN, "active_version", None, update_modified=False)
		self.addCleanup(frappe.db.set_value, "Annual Plan", PLAN, "active_version", V1, update_modified=False)
		self.assertEqual(self.plan_items(), {})
		self.assertIn(ac.PLAN_ITEMS, provider.applies(user="Administrator", at=self.at))  # core reports "No Active Plan" from the empty set plus applies()

	# ----- a read changes nothing, and calls no writing read -----

	def test_a_read_creates_and_persists_nothing(self):
		before = _counts()
		for user in ("Administrator", fx.HOD, fx.HYBRID, fx.AUTHOR, fx.OUTSIDER, fx.PLANNER, fx.HOPF, fx.ACCOUNTING_OFFICER, fx.AUDITOR, fx.FINANCE_OFFICER, OFFICER):
			provider.applies(user=user, at=self.at)
			for kind in (ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS):
				provider.facts(user=user, kind=kind, at=self.at)
		frappe.db.commit()
		self.assertEqual(_counts(), before)

	def test_no_writing_owner_read_is_called(self):
		from kentender_procurement.procurement_planning.services import workspace

		with patch.object(dpp_read, "get_departmental_plan", side_effect=AssertionError("get_departmental_plan writes")), \
			patch.object(workspace, "get_planning_workspace", side_effect=AssertionError("workspace read")):
			for kind in (ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS):
				provider.facts(user="Administrator", kind=kind, at=self.at)

	def test_another_kind_is_refused_not_answered_with_zero(self):
		with self.assertRaises(ValueError):
			provider.facts(user="Administrator", kind=ac.NEEDS, at=self.at)

	# ----- personas -----

	def test_a_head_of_department_and_an_author_see_only_their_own_departments_plan(self):
		from kentender_core.services.authorization import permitted_ou_scopes

		for user, role in ((fx.HOD, "Head of User Department"), (fx.AUTHOR, "Departmental Author")):
			scope = permitted_ou_scopes(user, role)
			expected = {self.dpps[key] for key, unit in (("alpha", fx.OU_ALPHA), ("beta", fx.OU_BETA)) if unit in scope}
			self.assertIn(self.dpps["alpha"], expected, user)
			self.assertEqual(set(self.by_ref(user, ac.DEPARTMENTAL_PLANS)), expected, user)
		# the Head of Alpha is not given Beta's plan (Beta is outside their scope), whatever else the shared test personas hold
		self.assertEqual(set(self.by_ref(fx.HOD, ac.DEPARTMENTAL_PLANS)), {self.dpps["alpha"]})

	def test_a_departmental_author_gets_departmental_plans_only_and_no_plan_items(self):
		for user in (fx.AUTHOR, fx.OUTSIDER):
			self.assertEqual(provider.applies(user=user, at=self.at), {ac.DEPARTMENTAL_PLANS}, user)
			self.assertEqual(self.read(user, ac.PLAN_ITEMS), [], user)
			self.assertEqual(provider.facts(user=user, kind=ac.PLAN_ITEMS, at=self.at)["records"], [], user)

	# ----- the department view of plan items (OD-2): the Head of User Department -----

	def grant_head(self, unit: str) -> str:
		"""EXTRA as a Head of User Department of `unit`; the user and the grant are removed with the class."""
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", EXTRA):
			frappe.get_doc({"doctype": "User", "email": EXTRA, "first_name": "PLNA Extra", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
		granted = administration.grant(user=EXTRA, business_role="Head of User Department", organisation_unit=unit, fixture_namespace=NS, actor="Administrator")
		frappe.db.commit()
		return granted["assignment"]

	def test_a_head_of_department_gets_plan_items_for_their_own_department_only(self):
		self.assertEqual(provider.applies(user=fx.HOD, at=self.at), self.ALL_KINDS)
		records = self.plan_items(fx.HOD)
		self.assertEqual(set(records), {SERVERS, PERIPHERALS, CLINIC})  # Monitors has no Alpha allocation: absent
		for record in records.values():
			self.assertEqual({a["org_unit"] for a in record["allocations"]}, {fx.OU_ALPHA}, record["reference"])
			self.assertEqual(record["org_units"], [fx.OU_ALPHA], record["reference"])
		self.assertNotIn(fx.OU_BETA, str(list(records.values())))  # no other department's id leaves the provider

	def test_the_department_view_keeps_the_whole_planned_value_and_only_the_departments_share(self):
		item = self.plan_items(fx.HOD)[PERIPHERALS]
		self.assertEqual(item["planned_value"], Decimal("65000000"))  # the whole: core prints "<department> share of <whole>"
		self.assertEqual(item["allocations"], [{"org_unit": fx.OU_ALPHA, "planned": Decimal("40000000"), "covered": Decimal("40000000")}])
		self.assertTrue(item["has_proceeding"])
		self.assertIsNone(item["invitation_days"])
		self.assertEqual(self.plan_items(fx.HOD)[CLINIC]["allocations"], [{"org_unit": fx.OU_ALPHA, "planned": Decimal("12000000"), "covered": Decimal(0)}])

	def test_the_other_departments_head_sees_the_other_share_and_not_alphas_items(self):
		self.addCleanup(self.remove_extra)
		self.grant_head(fx.OU_BETA)
		self.assertEqual(provider.applies(user=EXTRA, at=self.at), {ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS})
		records = self.plan_items(EXTRA)
		self.assertEqual(set(records), {PERIPHERALS, MONITORS})  # Servers and Clinic equipment have no Beta allocation
		self.assertEqual(records[PERIPHERALS]["planned_value"], Decimal("65000000"))
		self.assertEqual(records[PERIPHERALS]["allocations"], [{"org_unit": fx.OU_BETA, "planned": Decimal("25000000"), "covered": Decimal("10000000.50")}])
		self.assertNotIn(fx.OU_ALPHA, str(list(records.values())))
		self.assertEqual(records[MONITORS]["invitation_days"], 0)

	def test_a_head_of_department_who_is_also_a_site_wide_reader_gets_the_whole_plan(self):
		# the Planner-and-Head persona reads under its widest role: every item, every allocation
		self.assertEqual(self.plan_items(fx.HYBRID), self.plan_items())

	def test_a_heads_revoked_scope_sees_no_plan_items_on_the_next_read(self):
		self.addCleanup(self.remove_extra)
		assignment = self.grant_head(fx.OU_ALPHA)
		self.assertEqual(set(self.plan_items(EXTRA)), {SERVERS, PERIPHERALS, CLINIC})
		administration.revoke(assignment, reason="Revoked inside the Planning Analytics test.", actor="Administrator")
		frappe.db.commit()
		self.assertEqual(provider.applies(user=EXTRA, at=self.at), set())
		self.assertEqual(provider.facts(user=EXTRA, kind=ac.PLAN_ITEMS, at=self.at)["records"], [])

	def test_an_author_of_another_department_sees_that_departments_plan_only(self):
		self.assertEqual(set(self.by_ref(fx.OUTSIDER, ac.DEPARTMENTAL_PLANS)), {self.dpps["beta"]})

	def test_the_planner_keeps_the_module_reading_scope_and_reads_both_kinds(self):
		self.assertEqual(provider.applies(user=fx.PLANNER, at=self.at), self.ALL_KINDS)
		self.assertEqual(set(self.by_ref(fx.PLANNER, ac.DEPARTMENTAL_PLANS)), {self.dpps["alpha"], self.dpps["beta"]})
		self.assertEqual(len(self.plan_items(fx.PLANNER)), 4)

	def test_the_finance_and_statutory_readers_keep_their_plan_read_and_get_no_departmental_plans(self):
		for user in (fx.FINANCE_OFFICER, fx.STATUTORY):
			self.assertEqual(provider.applies(user=user, at=self.at), {ac.PLAN_ITEMS}, user)
			self.assertEqual(len(self.plan_items(user)), 4, user)
			self.assertEqual(self.read(user, ac.DEPARTMENTAL_PLANS), [], user)

	def test_the_offices_and_technical_readers_get_the_site_wide_aggregate_of_both_kinds(self):
		expected_items = self.plan_items()
		for user in (fx.HOPF, fx.ACCOUNTING_OFFICER, fx.AUDITOR, "Administrator", TECHNICAL_OPERATOR):
			self.assertEqual(provider.applies(user=user, at=self.at), self.ALL_KINDS, user)
			self.assertEqual(set(self.by_ref(user, ac.DEPARTMENTAL_PLANS)), {self.dpps["alpha"], self.dpps["beta"]}, user)
			self.assertEqual(self.plan_items(user), expected_items, user)

	def test_an_unrelated_role_gets_nothing(self):
		self.assertEqual(provider.applies(user=OFFICER, at=self.at), set())
		for kind in (ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS):
			self.assertEqual(provider.facts(user=OFFICER, kind=kind, at=self.at)["records"], [])
		self.assertEqual(provider.applies(user="Guest", at=self.at), set())

	def test_a_revoked_scope_sees_nothing_on_the_next_read(self):
		self.addCleanup(self.remove_extra)
		frappe.set_user("Administrator")
		frappe.get_doc({"doctype": "User", "email": EXTRA, "first_name": "PLNA Extra", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
		granted = administration.grant(user=EXTRA, business_role="Departmental Author", organisation_unit=fx.OU_ALPHA, fixture_namespace=NS, actor="Administrator")
		self.assertEqual(provider.applies(user=EXTRA, at=self.at), {ac.DEPARTMENTAL_PLANS})
		self.assertEqual(set(self.by_ref(EXTRA, ac.DEPARTMENTAL_PLANS)), {self.dpps["alpha"]})
		administration.revoke(granted["assignment"], reason="Revoked inside the Planning Analytics test.", actor="Administrator")
		frappe.db.commit()
		self.assertEqual(provider.applies(user=EXTRA, at=self.at), set())
		self.assertEqual(provider.facts(user=EXTRA, kind=ac.DEPARTMENTAL_PLANS, at=self.at)["records"], [])
