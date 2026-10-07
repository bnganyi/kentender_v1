# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — the Requisitions feed to Procurement Analytics (`procurement_requisitions/services/analytics_provider.py`;
plan Phase 2B, FU-ANL-03).

One synthetic world, built once: nine Requisition roots in the states Analytics counts, with the owner's own rows (versions,
drawdown lines stored as Data strings, decisions, a handoff consumed by a Tender, an open authorisation task). The provider
only reads, so no test rebuilds it. The Planning fixture actors are the owner's own roles; four more users (a clean Head of
Procurement Function, a Technical Operator, a Head of User Department whose responsibility is then revoked) are granted for
the class and removed after. Instants follow the A1 timeline of ANL §10A.2.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.procurement_requisitions.tests.test_analytics_provider
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import frappe

from kentender_core.services.command_write_guard import fixture_insert, purge_doc
from frappe.tests import IntegrationTestCase

from kentender_core.services import analytics_contract as ac
from kentender_core.services import responsibility_administration as administration
from kentender_core.utils.raw_delete import delete_rows
from kentender_procurement.procurement_planning.tests import fixtures as pln_fx
from kentender_procurement.procurement_requisitions.services import analytics_provider as provider
from kentender_procurement.procurement_requisitions.tests import fixtures as fx

AT = datetime(2027, 6, 18, 10, 0)
ANL_NS = "KT_TEST_REQANL"
HOPF_ONLY, TECH_OP, FORMER_HOD = "reqanl.hopf@example.test", "reqanl.techop@example.test", "reqanl.formerhod@example.test"
EXTRA_USERS = (HOPF_ONLY, TECH_OP, FORMER_HOD)
HOD, HOD_BETA, CONTRIBUTOR, AUTHOR = fx.HOD, fx.HOD_BETA, fx.CONTRIBUTOR, fx.AUTHOR
PLANNER, AUDITOR, AO, OUTSIDER, FINANCE = fx.PLANNER, fx.AUDITOR, fx.ACCOUNTING_OFFICER, fx.OUTSIDER, fx.FINANCE_OFFICER
SITE_WIDE_NON_DRAFT = ("clinic", "peripherals", "switches", "awaiting", "withdrawn", "revoked", "stopped")
TENDER_REFERENCE = "TND-ANL-041"


def _dt(text: str) -> datetime:
	return datetime.strptime(text, "%Y-%m-%d %H:%M")


def _remove_extra() -> None:
	frappe.set_user("Administrator")
	for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": ANL_NS}, pluck="name"):
		purge_doc("User Responsibility Assignment", name)
	for email in EXTRA_USERS:
		for name in frappe.get_all("Contact Email", filters={"email_id": email}, pluck="parent"):
			frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=1, ignore_permissions=True)
	frappe.db.commit()


def _left_behind() -> dict[str, int]:
	requisitions = fx.test_requisitions()
	versions = frappe.get_all("Requisition Version", filters={"requisition": ("in", requisitions or [""])}, pluck="name")
	left = {
		"requisitions": len(requisitions), "versions": len(versions),
		"decisions": frappe.db.count("Requisition Decision", {"requisition_version": ("in", versions or [""])}),
		"tasks": frappe.db.count("Requisition Task", {"requisition": ("in", requisitions or [""])}),
		"handoffs": frappe.db.count("Authorised Requisition Handoff", {"requisition": ("in", requisitions or [""])}),
		"tenders": frappe.db.count("Tender", {"fixture_namespace": ANL_NS}),
		"assignments": frappe.db.count("User Responsibility Assignment", {"fixture_namespace": ANL_NS}),
		"users": frappe.db.count("User", {"name": ("in", list(EXTRA_USERS))}),
	}
	return {name: count for name, count in left.items() if count}


def _remove_world() -> None:
	frappe.set_user("Administrator")
	fx.wipe_requisition_rows()
	delete_rows("Tender", {"fixture_namespace": ANL_NS})
	_remove_extra()
	frappe.db.commit()
	left = _left_behind()
	if left:
		raise AssertionError(f"Requisitions Analytics test rows left behind: {left}")


class World:
	"""The synthetic Requisitions the provider reads, as the owner would have stored them."""

	def __init__(self):
		self.alpha, self.beta = fx.ou_alpha(), fx.ou_beta()
		self.roots: dict[str, str] = {}
		self.versions: dict[str, list[str]] = {}
		self.handoffs: dict[str, str] = {}
		self.tender = ""

	def insert(self, values: dict):
		doc = frappe.get_doc({**values, "fixture_namespace": ANL_NS if "fixture_namespace" in frappe.get_meta(values["doctype"]).get_valid_columns() else None})
		return fixture_insert(doc)

	def version(self, key: str, number: int, status: str, lines: list[tuple[str, str]], *, submitted: str = "", based_on: str = "") -> str:
		version = self.insert({
			"doctype": "Requisition Version", "requisition": self.roots[key], "version_number": number, "version_status": status,
			"requirement_title": f"Analytics {key} v{number}", "based_on_version": based_on or None, "record_version": 0,
			"submitted_at": _dt(submitted) if submitted else None,
			"drawdown_lines": [{"drawdown_line_id": f"{key}-{number}-{i}", "plan_item_line_id": f"{key}-pil-{i}", "source_line_id": f"{key}-src-{i}", "contributing_org_unit": unit,
				"requested_quantity": "10", "requested_value": value} for i, (unit, value) in enumerate(lines, 1)],
		}).name
		self.versions.setdefault(key, []).append(version)
		return version

	def decision(self, version: str, decision: str, at: str) -> None:
		self.insert({
			"doctype": "Requisition Decision", "requisition_version": version, "actor": "Administrator", "decision": decision, "authority_snapshot": "{}",
			"decided_at": _dt(at), "command_idempotency_key": uuid4().hex,
		})

	def root(self, key: str, state: str, lead: str, units: list[str]) -> str:
		name = self.insert({
			"doctype": "Procurement Requisition", "requisition_reference": f"REQ-ANL-{key}", "plan_id": "ANL-NO-PLAN", "plan_version_id": "ANL-NO-PLAN-V1",
			"plan_item_id": f"ANL-ITEM-{key}", "current_state": state, "lead_org_unit_id": lead, "record_version": 0,
			"contributing_org_units": [{"organisation_unit": unit} for unit in units],
		}).name
		self.roots[key] = name
		return name

	def point(self, key: str, *, current: str, authorised: str = "", consumed: str = "") -> None:
		values = {"current_version": current, "authorised_version": authorised or None, "handoff_consumed_at": _dt(consumed) if consumed else None}
		frappe.db.set_value("Procurement Requisition", self.roots[key], values, update_modified=False)

	def handoff(self, key: str, version: str, *, tender: str = "", consumed: str = "") -> str:
		name = self.insert({
			"doctype": "Authorised Requisition Handoff", "requisition": self.roots[key], "requisition_version": version, "payload_json": "{}",
			"handoff_digest": uuid4().hex, "generated_at": _dt("2027-03-15 11:00"), "tender": tender or None, "consumed_at": _dt(consumed) if consumed else None,
		}).name
		self.handoffs[key] = name
		return name

	def build(self) -> None:
		a, b = self.alpha, self.beta
		# R-A: submitted to Procurement, awaiting the Head of Procurement Function
		self.root("clinic", "Submitted to Procurement", a, [a])
		v = self.version("clinic", 1, "Submitted to Procurement", [(a, "12000000.00")], submitted="2027-06-16 11:00")
		self.decision(v, "Submit to Procurement", "2027-06-16 11:00")
		self.point("clinic", current=v)
		self.insert({"doctype": "Requisition Task", "requisition": self.roots["clinic"], "requisition_version": v, "business_role": "Head of Procurement Function",
			"status": "Open", "task_token": uuid4().hex, "record_version": 0})
		# R-B: authorised, two drawdown lines (A1: 4,000,000 + 2,500,000), consumed by a Tender
		self.tender = self.insert({"doctype": "Tender", "tender_reference": TENDER_REFERENCE, "overall_status": "Draft", "record_version": 0}).name
		self.root("peripherals", "Authorised", a, [a, b])
		v = self.version("peripherals", 1, "Authorised", [(a, "4000000.00"), (b, "2500000.00")], submitted="2027-03-09 10:00")
		self.decision(v, "Submit to Procurement", "2027-03-09 10:00")
		self.decision(v, "Authorise requisition", "2027-03-15 11:00")
		self.handoff("peripherals", v, tender=self.tender, consumed="2027-03-16 09:00")
		self.point("peripherals", current=v, authorised=v, consumed="2027-03-16 09:00")
		# R-C: returned once, then authorised on its second Version (not yet consumed)
		self.root("switches", "Authorised", b, [b])
		first = self.version("switches", 1, "Draft", [(b, "9000000.00")], submitted="2027-03-01 10:00")
		self.decision(first, "Submit to Procurement", "2027-03-01 10:00")
		second = self.version("switches", 2, "Authorised", [(b, "8000000.00")], submitted="2027-03-05 10:00", based_on=first)
		self.decision(second, "Submit to Procurement", "2027-03-05 10:00")
		self.decision(second, "Authorise requisition", "2027-03-09 11:00")
		self.handoff("switches", second)
		self.point("switches", current=second, authorised=second)
		# a Draft, one awaiting department approval, one withdrawn
		self.root("draft", "Draft", a, [a])
		self.point("draft", current=self.version("draft", 1, "Draft", [(a, "1000000.00")]))
		self.root("awaiting", "Awaiting Department Approval", b, [b])
		self.point("awaiting", current=self.version("awaiting", 1, "Awaiting Department Approval", [(b, "3000000.50")]))
		self.root("withdrawn", "Withdrawn", a, [a])
		self.point("withdrawn", current=self.version("withdrawn", 1, "Withdrawn", [(a, "500000.00")]))
		# revoked after authorisation, and stopped for a Planning correction after being submitted
		self.root("revoked", "Revoked", a, [a])
		v = self.version("revoked", 1, "Revoked", [(a, "700000.00")], submitted="2027-02-01 10:00")
		self.decision(v, "Submit to Procurement", "2027-02-01 10:00")
		self.decision(v, "Authorise requisition", "2027-02-05 11:00")
		self.point("revoked", current=v, authorised=v)
		self.root("stopped", "Upstream correction required", b, [b])
		v = self.version("stopped", 1, "Submitted to Procurement", [(b, "600000.00")], submitted="2027-02-10 10:00")
		self.decision(v, "Submit to Procurement", "2027-02-10 10:00")
		self.point("stopped", current=v)
		# a Version returned to a Draft: its earlier submission is history, the current Draft has none
		self.root("returned", "Draft", a, [a])
		first = self.version("returned", 1, "Draft", [(a, "400000.00")], submitted="2027-01-05 10:00")
		self.decision(first, "Return for correction", "2027-01-06 10:00")
		self.decision(first, "Submit to Procurement", "2027-01-05 10:00")
		self.point("returned", current=self.version("returned", 2, "Draft", [(a, "400000.00")], based_on=first))


def _holder() -> str:
	"""The Head of Procurement Function as the owner words a holder: names when two or fewer, else the responsibility. Read
	independently of the provider."""
	people: list[str] = []
	for row in frappe.get_all("User Responsibility Assignment", filters={"business_role": "Head of Procurement Function", "status": "Enabled"}, fields=["user", "organisation_unit"], order_by="creation asc"):
		if not row.organisation_unit and row.user not in people:
			people.append(row.user)
	names = [frappe.db.get_value("User", user, "full_name") or user for user in people]
	return " or ".join(names) if 0 < len(names) <= 2 else "Head of Procurement Function"


class TestRequisitionsAnalyticsProvider(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)
		cls.addClassCleanup(_remove_world)
		fx.wipe_requisition_rows()
		for email, name in ((HOPF_ONLY, "REQANL Head of Procurement"), (TECH_OP, "REQANL Technical Operator"), (FORMER_HOD, "REQANL Former Head")):
			pln_fx._user(email, name)
		for email, role, unit in ((HOPF_ONLY, "Head of Procurement Function", ""), (TECH_OP, "Technical Operator", ""), (FORMER_HOD, "Head of User Department", fx.ou_alpha())):
			outcome = administration.grant(user=email, business_role=role, organisation_unit=unit, fixture_namespace=ANL_NS, actor="Administrator")
			if email == FORMER_HOD:
				administration.revoke(outcome["assignment"], reason="Revoked inside the Analytics provider test.", actor="Administrator")
		cls.world = World()
		cls.world.build()
		frappe.db.commit()
		cls.ids = {key: name for key, name in cls.world.roots.items()}
		cls.by_id = {name: key for key, name in cls.ids.items()}

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.set_user("Administrator")

	# ----- reads -----

	def rows(self, user: str) -> dict[str, dict]:
		"""The actor's records that belong to this world, by key."""
		result = provider.facts(user=user, kind=ac.REQUISITIONS, at=AT)
		self.assertEqual(set(result), {"records"})
		return {self.by_id[rec["id"]]: rec for rec in result["records"] if rec["id"] in self.by_id}

	def row(self, key: str, user: str = "Administrator") -> dict:
		return self.rows(user)[key]

	def amounts(self, rec: dict) -> list[tuple[str, Decimal]]:
		return [(item["org_unit"], item["amount"]) for item in rec["value_lines"]]

	# ----- values by state -----

	def test_a_requisition_submitted_to_procurement_carries_its_requested_value(self):
		rec = self.row("clinic")
		self.assertEqual((rec["state"], rec["state_key"], rec["value_kind"]), ("Submitted to Procurement", "Submitted to Procurement", ac.REQUESTED))
		self.assertEqual(self.amounts(rec), [(self.world.alpha, Decimal("12000000.00"))])
		self.assertEqual((rec["title"], rec["reference"], rec["org_units"]), ("Analytics clinic v1", "REQ-ANL-clinic", [self.world.alpha]))
		self.assertEqual(rec["fiscal_year"], "")  # the synthetic plan is not a stored Annual Plan: no Fiscal Year is recorded

	def test_a_two_department_drawdown_keeps_each_line_with_its_department(self):
		rec = self.row("peripherals")
		self.assertEqual(rec["value_kind"], ac.AUTHORISED)
		self.assertEqual(self.amounts(rec), [(self.world.alpha, Decimal("4000000.00")), (self.world.beta, Decimal("2500000.00"))])
		self.assertEqual(sum(amount for _, amount in self.amounts(rec)), Decimal("6500000.00"))
		self.assertEqual(rec["org_units"], [self.world.alpha, self.world.beta])  # lead first, contributors after

	def test_an_authorised_requisition_is_valued_on_its_authorised_version_not_the_returned_one(self):
		rec = self.row("switches")
		self.assertEqual(self.amounts(rec), [(self.world.beta, Decimal("8000000.00"))])  # the first Version asked for 9,000,000.00

	def test_the_owners_strings_become_exact_decimals(self):
		rec = self.row("awaiting")
		(unit, amount), = self.amounts(rec)
		self.assertEqual((type(amount), amount), (Decimal, Decimal("3000000.50")))
		for each in self.rows("Administrator").values():
			for item in each["value_lines"]:
				self.assertIsInstance(item["amount"], Decimal)

	def test_every_state_maps_to_its_value_kind_and_the_rest_carry_no_total(self):
		expected = {
			"clinic": ac.REQUESTED, "awaiting": ac.REQUESTED, "peripherals": ac.AUTHORISED, "switches": ac.AUTHORISED,
			"draft": None, "withdrawn": None, "revoked": None, "stopped": None, "returned": None,
		}
		rows = self.rows(AUTHOR)  # holds both departments: reads every state
		self.assertEqual({key: rows[key]["value_kind"] for key in expected}, expected)
		for key, kind in expected.items():
			if kind is None:
				self.assertEqual(rows[key]["value_lines"], [], key)

	def test_the_state_is_the_owners_stored_state_and_a_returned_draft_is_returned(self):
		rows = self.rows(AUTHOR)
		self.assertEqual(
			{key: (rows[key]["state"], rows[key]["state_key"]) for key in self.ids},
			{
				"clinic": ("Submitted to Procurement",) * 2, "peripherals": ("Authorised",) * 2, "switches": ("Authorised",) * 2,
				"awaiting": ("Awaiting Department Approval",) * 2, "withdrawn": ("Withdrawn",) * 2, "revoked": ("Revoked",) * 2,
				"stopped": ("Upstream correction required",) * 2, "draft": ("Draft", "Draft"), "returned": ("Returned", "Draft"),
			},
		)

	# ----- instants and events -----

	def test_the_instants_of_a_requisition_that_reached_a_tender(self):
		rec = self.row("peripherals")
		self.assertEqual(rec["submitted_at"], _dt("2027-03-09 10:00"))
		self.assertEqual(rec["authorised_at"], _dt("2027-03-15 11:00"))
		self.assertEqual(rec["consumed_at"], _dt("2027-03-16 09:00"))
		self.assertEqual(rec["submission_events"], [_dt("2027-03-09 10:00")])
		self.assertEqual(rec["authorisation_events"], [_dt("2027-03-15 11:00")])

	def test_a_returned_then_authorised_requisition_counts_every_submission_but_times_the_authorised_one(self):
		rec = self.row("switches")
		self.assertEqual(rec["submitted_at"], _dt("2027-03-05 10:00"))  # the Version that was authorised
		self.assertEqual(rec["submission_events"], [_dt("2027-03-01 10:00"), _dt("2027-03-05 10:00")])
		self.assertEqual((rec["authorised_at"], rec["authorisation_events"]), (_dt("2027-03-09 11:00"), [_dt("2027-03-09 11:00")]))
		self.assertIsNone(rec["consumed_at"])

	def test_a_draft_returned_after_a_submission_keeps_the_event_but_has_no_current_submission(self):
		rec = self.row("returned", AUTHOR)
		self.assertEqual(rec["submission_events"], [_dt("2027-01-05 10:00")])
		self.assertEqual((rec["submitted_at"], rec["authorised_at"], rec["authorisation_events"]), (None, None, []))
		draft = self.row("draft", AUTHOR)
		self.assertEqual((draft["submitted_at"], draft["submission_events"], draft["authorisation_events"]), (None, [], []))

	def test_a_revoked_authorisation_keeps_its_instants_and_no_value(self):
		rec = self.row("revoked")
		self.assertEqual((rec["submitted_at"], rec["authorised_at"]), (_dt("2027-02-01 10:00"), _dt("2027-02-05 11:00")))
		self.assertEqual(rec["authorisation_events"], [_dt("2027-02-05 11:00")])
		self.assertEqual(rec["value_kind"], None)

	def test_a_requisition_submitted_and_stopped_keeps_its_submission(self):
		rec = self.row("stopped")
		self.assertEqual((rec["submitted_at"], rec["authorised_at"]), (_dt("2027-02-10 10:00"), None))

	# ----- the Tender and the route -----

	def test_the_tender_reference_is_that_of_the_tender_created_from_the_consumed_handoff(self):
		rows = self.rows("Administrator")
		self.assertEqual(rows["peripherals"]["tender_reference"], TENDER_REFERENCE)
		for key in ("clinic", "switches", "awaiting", "withdrawn", "revoked", "stopped"):
			self.assertEqual(rows[key]["tender_reference"], "", key)  # unconsumed or never authorised: no Tender

	def test_only_the_tender_name_is_used_when_the_tender_cannot_be_read(self):
		handoff = self.world.handoffs["switches"]
		self.addCleanup(frappe.db.set_value, "Authorised Requisition Handoff", handoff, {"tender": None, "consumed_at": None}, None, update_modified=False)
		frappe.db.set_value("Authorised Requisition Handoff", handoff, {"tender": "TDR-NO-SUCH-TENDER", "consumed_at": _dt("2027-03-12 09:00")}, update_modified=False)
		self.assertEqual(self.row("switches")["tender_reference"], "TDR-NO-SUCH-TENDER")

	def test_the_route_is_the_owners_exact_destination(self):
		rows = self.rows("Administrator")
		for key in ("peripherals", "switches", "revoked"):
			self.assertEqual(rows[key]["route"], ["procurement-requisitions", self.ids[key], "authorised"], key)
		for key in ("clinic", "awaiting", "withdrawn", "stopped"):
			self.assertEqual(rows[key]["route"], ["procurement-requisitions", self.ids[key]], key)

	# ----- outstanding -----

	def test_a_requisition_awaiting_authorisation_is_an_outstanding_matter_since_it_was_submitted(self):
		rec = self.row("clinic")
		holder = _holder()
		self.assertEqual(rec["outstanding"], {"text": f"Awaiting authorisation by {holder}.", "holder": holder, "since": _dt("2027-06-16 11:00")})
		self.assertEqual(rec["submitted_at"], rec["outstanding"]["since"])

	def test_nothing_else_is_outstanding(self):
		rows = self.rows(AUTHOR)
		self.assertEqual({key for key, rec in rows.items() if rec["outstanding"]}, {"clinic"})

	def test_a_submitted_requisition_whose_task_is_closed_is_not_awaiting_anyone(self):
		task = frappe.db.get_value("Requisition Task", {"requisition": self.ids["clinic"], "status": "Open"}, "name")
		self.addCleanup(frappe.db.set_value, "Requisition Task", task, "status", "Open", None, update_modified=False)
		frappe.db.set_value("Requisition Task", task, "status", "Completed", update_modified=False)
		self.assertIsNone(self.row("clinic")["outstanding"])

	# ----- who may know what -----

	def test_a_head_of_user_department_knows_only_the_requisitions_their_department_contributes_to(self):
		self.assertEqual(set(self.rows(HOD)), {"clinic", "peripherals", "draft", "withdrawn", "revoked", "returned"})
		self.assertEqual(set(self.rows(HOD_BETA)), {"peripherals", "switches", "awaiting", "stopped"})

	def test_a_departmental_author_knows_only_their_department(self):
		self.assertEqual(set(self.rows(CONTRIBUTOR)), {"peripherals", "switches", "awaiting", "stopped"})
		self.assertEqual(set(self.rows(AUTHOR)), set(self.ids))  # Grace holds both departments

	def test_the_department_reader_sees_exactly_what_the_owners_own_list_gives_them(self):
		for user in (HOD, HOD_BETA, CONTRIBUTOR):
			frappe.set_user(user)
			owner = {self.by_id[name] for name in frappe.get_list("Procurement Requisition", pluck="name", limit_page_length=0) if name in self.by_id}
			frappe.set_user("Administrator")
			self.assertEqual(set(self.rows(user)), owner, user)

	def test_the_site_wide_readers_know_every_state_but_a_draft(self):
		for user in (HOPF_ONLY, PLANNER, AUDITOR, AO, "Administrator", TECH_OP):
			self.assertEqual(set(self.rows(user)), set(SITE_WIDE_NON_DRAFT), user)

	def test_a_site_wide_reader_gets_the_same_figures_as_anyone_else(self):
		reference = self.rows("Administrator")
		for user in (HOPF_ONLY, AO, AUDITOR, TECH_OP):
			rows = self.rows(user)
			for key in SITE_WIDE_NON_DRAFT:
				self.assertEqual(rows[key], reference[key], f"{user} {key}")

	def test_a_draft_of_another_user_never_appears_to_a_site_wide_reader(self):
		for user in (HOPF_ONLY, PLANNER, AUDITOR, AO, "Administrator", TECH_OP):
			rows = self.rows(user)
			self.assertFalse({"draft", "returned"} & set(rows), user)
			self.assertNotIn("Draft", {rec["state"] for rec in rows.values()}, user)

	def test_a_department_reader_never_sees_another_departments_draft(self):
		for user in (HOD_BETA, CONTRIBUTOR):
			self.assertFalse({"draft", "returned"} & set(self.rows(user)), user)  # the Drafts belong to the Alpha department

	def test_the_accounting_officers_aggregate_read_is_wider_than_the_requisitions_they_may_open(self):
		"""OD-2: the Analytics aggregate covers every non-draft state, while the owner's own read grant stays Authorised and Revoked."""
		frappe.set_user(AO)
		opened = {self.by_id[name] for name in frappe.get_list("Procurement Requisition", pluck="name", limit_page_length=0) if name in self.by_id}
		frappe.set_user("Administrator")
		self.assertEqual(opened, {"peripherals", "switches", "revoked"})
		self.assertEqual(set(self.rows(AO)), set(SITE_WIDE_NON_DRAFT))
		self.assertTrue(provider.__doc__ and "OD-2" in provider.__doc__ and "Accounting Officer" in provider.__doc__)

	def test_an_unrelated_responsibility_gets_nothing(self):
		for user in (FINANCE, pln_fx.BUDGET_OFFICER, "Guest", ""):  # the Planning fixture's outsider is a Departmental Author in Beta: not unrelated
			self.assertEqual(provider.applies(user=user, at=AT), set(), user)
			with self.assertRaises(frappe.PermissionError):
				provider.facts(user=user, kind=ac.REQUISITIONS, at=AT)

	def test_a_revoked_responsibility_gives_nothing(self):
		self.assertEqual(frappe.db.get_value("User Responsibility Assignment", {"user": FORMER_HOD}, "status"), "Revoked")
		self.assertEqual(provider.applies(user=FORMER_HOD, at=AT), set())
		with self.assertRaises(frappe.PermissionError):
			provider.facts(user=FORMER_HOD, kind=ac.REQUISITIONS, at=AT)

	def test_applies_names_the_requisitions_kind_for_every_audience(self):
		for user in (HOD, HOD_BETA, CONTRIBUTOR, AUTHOR, HOPF_ONLY, PLANNER, AUDITOR, AO, "Administrator", TECH_OP):
			self.assertEqual(provider.applies(user=user, at=AT), {ac.REQUISITIONS}, user)

	def test_another_kind_is_refused(self):
		with self.assertRaises(ValueError):
			provider.facts(user="Administrator", kind=ac.TENDERS, at=AT)

	# ----- a read changes nothing -----

	def test_a_read_creates_and_changes_nothing(self):
		tables = ("Procurement Requisition", "Requisition Version", "Requisition Decision", "Requisition Task", "Authorised Requisition Handoff",
			"Requisition Event", "Requisition Command Journal", "Requisition Drawdown Line", "Requisition Contributing Unit", "Tender", "User Responsibility Assignment")

		def snapshot():
			return {t: frappe.db.count(t) for t in tables} | {"modified": frappe.db.get_value("Procurement Requisition", self.ids["clinic"], "modified")}

		before = snapshot()
		for user in ("Administrator", HOD, HOPF_ONLY, AO):
			provider.facts(user=user, kind=ac.REQUISITIONS, at=AT)
		self.assertEqual(snapshot(), before)

	def test_every_record_satisfies_the_contract(self):
		for rec in provider.facts(user="Administrator", kind=ac.REQUISITIONS, at=AT)["records"]:
			ac.validate(rec)  # raises on the first thing wrong
