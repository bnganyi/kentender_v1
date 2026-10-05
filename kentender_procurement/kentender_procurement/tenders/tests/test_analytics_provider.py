# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — the Tenders feed to Procurement Analytics (`tenders/services/analytics_provider.py`).

One shared world for the whole module (built once, read by every test; the provider only reads), on the Tenders test world's
own actors: Brian (Procurement Officer), Charles (Head of Procurement Function), Amina (Accounting Officer), an Auditor, a
Departmental Author and a Head of User Department in one unit, and a Technical Operator. Tenders are inserted directly with a
synthetic Authorised Requisition Handoff each (money as Data strings, as Requisitions stores it), so the classifier's every
bucket is reached without building a Requisition, an Opening, an Evaluation or an Award. The three stage owners are replaced by
fakes through the one module-level indirection (`analytics_provider.stage_facts`); one test calls the real modules with no case
behind them to prove the wiring. The world and every row it adds are removed afterwards and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.tenders.tests.test_analytics_provider
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime

from kentender_core.services import analytics_contract as contract
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.tenders.services import analytics_provider as provider
from kentender_procurement.tenders.services import envelope, handoffs
from kentender_procurement.tenders.tests import fixtures as fx
from kentender_procurement.tenders.tests import sample

NS = fx.NS
_REAL_STAGE_FACTS = provider.stage_facts  # captured before any test replaces it
AT = datetime(2027, 6, 18, 10, 0)
TECH = "tndanl.techop@example.test"  # a Technical Operator (site-wide, no business action)
EXTRA = "tndanl.extra@example.test"  # a Head of User Department, granted and revoked inside one test
EXTRA_NS = "KT_TEST_TNDANL"
WORLD: dict[str, dict] = {}
HANDOFFS: list[str] = []
FAKE: dict[str, dict[str, dict]] = {"opening": {}, "evaluation": {}, "award": {}}
RAISE: dict[str, set[str]] = {"opening": set(), "evaluation": set(), "award": set()}
CALLS: list[tuple[str, str, tuple[str, ...]]] = []


def _dt(text: str) -> datetime:
	return get_datetime(text)


def _fiscal_year() -> str:
	return frappe.db.get_value("Fiscal Year", {}, "name", order_by="creation asc")


def _handoff(lines: list[tuple[str, str]], consumed_at: datetime | None) -> str:
	"""A synthetic Authorised Requisition Handoff: the drawdown lines of the Requisition Version a Tender consumed."""
	payload = {"handoff_version": "1.4", "drawdown_lines": [{"drawdown_line_id": f"DL-{i}", "contributing_org_unit": unit, "requested_value": value} for i, (unit, value) in enumerate(lines, 1)]}
	doc = frappe.get_doc({
		"doctype": "Authorised Requisition Handoff", "requisition": "PRQ-TNDANL", "requisition_version": "RQV-TNDANL", "payload_json": json.dumps(payload), "handoff_digest": "d" * 64,
		"handoff_version": "1.4", "generated_at": consumed_at or _dt("2027-05-01 08:00"), "consumed_at": consumed_at, "fixture_namespace": NS,
	})
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True)
	HANDOFFS.append(doc.name)
	return doc.name


def _tender(key: str, number: str, title: str, *, status: str, lead: str, contributors: list[str], lines: list[tuple[str, str]], consumed: str = "2027-05-10 08:00",
		published: str = "", deadline: str = "") -> None:
	values = {**sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE), "tender_title": title}
	tender, version = sample.insert_tender_with_version(reference=f"TNDANL-{number}", values=values, fixture_namespace=NS)
	handoff = _handoff(lines, _dt(consumed) if consumed else None)
	fields = {
		"overall_status": status, "lead_org_unit": lead, "contributing_org_unit_ids": json.dumps(contributors), "fiscal_year": _fiscal_year(),
		"published_at": _dt(published) if published else None, "submission_deadline": _dt(deadline) if deadline else None, "requisition_handoff": handoff,
	}
	envelope.bump(tender, **fields)
	WORLD[key] = {"tender": tender, "version": version, "handoff": handoff, "title": title, "reference": f"TNDANL-{number}"}


def _task(key: str, task_type: str, *, creation: str, holder: str = "", sender: str = "", comment: str = "", subject_type: str = "", subject_id: str = "") -> str:
	entry = WORLD[key]
	task = handoffs.open_task(entry["tender"], entry["version"], task_type=task_type, holder=holder, sender=sender, comment=comment, subject_type=subject_type, subject_id=subject_id, notify=False)
	frappe.db.set_value("Tender Task", task.name, "creation", _dt(creation), update_modified=False)
	return task.name


def _cancel(key: str, *, at: str) -> str:
	tender = WORLD[key]["tender"]
	doc = envelope.insert(frappe.get_doc({
		"doctype": "Tender Cancellation", "tender": tender.name, "ground": "NEED_CEASED", "ground_label": "The procurement need has ceased", "reason": "The need has ceased entirely.",
		"decided_by": fx.AO, "decided_at": _dt(at), "ppra_report_due_by": date(2027, 6, 18), "candidate_notice_due_by": date(2027, 6, 20), "record_version": 0, "fixture_namespace": NS,
		"obligations": [{"obligation_id": "PPRA_REPORT", "obligation_type": "PPRA report", "channel": "PPRA_REPORT", "label": "PPRA report", "due_by": date(2027, 6, 18), "status": "Due"}],
	}))
	envelope.bump(tender, cancellation=doc.name)
	return doc.name


def _world() -> None:
	"""Eleven Tenders: one in every bucket, a past-deadline Tender the hourly job has not closed, a Tender whose Opening read fails,
	an empty opening, and two cancellations (one with its compliance evidence outstanding, one complete)."""
	alpha, beta = req_fx.ou_alpha(), req_fx.ou_beta()
	two = [(alpha, "4000000.00"), (alpha, "1000000.00"), (beta, "2500000.00")]
	# 041 returned for correction (alpha lead; the two alpha lines sum, the beta line stays its own)
	_tender("t041", "041", "Supply of IT peripherals", status="Draft", lead=alpha, contributors=[alpha, beta], lines=two)
	returned = WORLD["t041"]["version"]
	envelope.bump(returned, status="Returned", returned_by=fx.HOPF, returned_at=_dt("2027-06-16 09:00"), return_reason="State the warranty period required from suppliers.",
		return_affected_task="Supplier and contract requirements")
	draft = frappe.copy_doc(returned)
	draft.version_number, draft.status, draft.predecessor_version, draft.returned_at, draft.returned_by = 2, "Draft", returned.name, None, None
	draft.return_reason = draft.return_affected_task = ""
	envelope.insert(draft)
	envelope.bump(WORLD["t041"]["tender"], current_version=draft.name)
	WORLD["t041"]["version"] = draft
	_task("t041", handoffs.CORRECT_RETURNED, creation="2027-06-16 09:00:01", holder=fx.OFFICER, sender=fx.HOPF, comment="State the warranty period required from suppliers.")
	_tender("t042", "042", "Supply of network switches", status="Published — open", lead=alpha, contributors=[alpha], lines=[(alpha, "8000000.00")], published="2027-04-20 11:00", deadline="2027-06-25 11:00")
	_tender("t043", "043", "Supply of office desks", status="Submission period ended", lead=beta, contributors=[beta], lines=[(beta, "3500000.00")], published="2027-05-02 09:00", deadline="2027-06-01 11:00")
	_tender("t044", "044", "Supply of printers", status="Submission period ended", lead=beta, contributors=[beta, alpha], lines=[(beta, "3000000.00"), (alpha, "2000000.00")], published="2027-05-04 09:00", deadline="2027-06-02 11:00")
	_tender("t045", "045", "Supply of monitors", status="Submission period ended", lead=alpha, contributors=[alpha], lines=[(alpha, "7500000.00")], published="2027-05-06 09:00", deadline="2027-06-03 11:00")
	_tender("t046", "046", "Supply of servers", status="Cancelled", lead=beta, contributors=[beta], lines=[(beta, "25000000.00")], published="2027-05-08 09:00", deadline="2027-06-20 11:00")
	_cancel("t046", at="2027-06-16 12:00")
	_task("t046", handoffs.CANCELLATION_COMPLIANCE, creation="2027-06-16 12:00:01", holder=fx.OFFICER, sender=fx.AO, subject_type="Tender Cancellation", subject_id=WORLD["t046"]["tender"].cancellation)
	_tender("t047", "047", "Supply of routers", status="Published — open", lead=alpha, contributors=[alpha], lines=[(alpha, "1500000.00")], published="2027-05-10 09:00", deadline="2027-06-17 17:00")
	_tender("t048", "048", "Supply of cabling", status="Submission period ended", lead=beta, contributors=[beta], lines=[(beta, "900000.00")], published="2027-05-10 09:00", deadline="2027-06-05 11:00")
	_tender("t049", "049", "Supply of toner", status="Submission period ended", lead=beta, contributors=[beta], lines=[(beta, "600000.00")], published="2027-05-12 09:00", deadline="2027-06-06 11:00")
	_tender("t050", "050", "Supply of racks", status="Cancelled", lead=beta, contributors=[beta], lines=[(beta, "400000.00")], published="2027-05-12 09:00", deadline="2027-06-20 11:00")
	_cancel("t050", at="2027-06-15 10:00")
	_fakes()


def _fakes() -> None:
	name = lambda key: WORLD[key]["tender"].name  # noqa: E731
	complete = {"opening_complete_at": _dt("2027-06-01 12:00"), "outcome": "Bids opened", "status": "Complete"}
	for key in ("t043", "t044", "t045"):
		FAKE["opening"][name(key)] = dict(complete)
	FAKE["opening"][name("t049")] = {"opening_complete_at": None, "outcome": "No bids", "status": "Complete"}
	FAKE["evaluation"][name("t043")] = {
		"case_state": "Reviewing", "no_evaluation_required": False, "report_sent_at": None, "opening_completed_at": _dt("2027-06-01 12:01"),
		"outstanding": contract.outstanding("Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee.", "Grace Wambui", _dt("2027-06-03 10:00")),
	}
	for key in ("t044", "t045"):
		FAKE["evaluation"][name(key)] = {"case_state": "Report sent", "no_evaluation_required": False, "report_sent_at": _dt("2027-06-10 09:00"), "opening_completed_at": _dt("2027-06-01 12:01"), "outstanding": None}
	FAKE["award"][name("t044")] = {
		"stage": "Opinion", "received_at": _dt("2027-06-16 14:07"), "decision_at": None, "decision_outcome": None, "decision_events": [], "award_amount": None, "award_amount_visible": True,
		"sent_to_contracting": False, "closed": False, "outstanding": contract.outstanding("Awaiting professional opinion by Charles Mutiso.", "Charles Mutiso", _dt("2027-06-16 14:07")), "cancelled": False,
	}
	FAKE["award"][name("t045")] = {
		"stage": "Notices", "received_at": _dt("2027-06-16 14:07"), "decision_at": _dt("2027-06-17 11:00"), "decision_outcome": "Award", "decision_events": [_dt("2027-06-17 11:00"), _dt("2027-06-17 15:30")],
		"award_amount": Decimal("7185000.00"), "award_amount_visible": True, "sent_to_contracting": False, "closed": False, "cancelled": False,
		"outstanding": contract.outstanding("Award decision recorded. Required bidder notices are awaiting delivery.", "Charles Mutiso", _dt("2027-06-17 11:00")),
	}
	RAISE["opening"].add(name("t048"))


def _fake_stage_facts(stage, *, user, tender_names, at):
	CALLS.append((stage, user, tuple(tender_names)))
	if set(tender_names) & RAISE[stage]:
		raise RuntimeError(f"{stage} owner failed for {sorted(set(tender_names) & RAISE[stage])}")
	return {n: FAKE[stage][n] for n in tender_names if n in FAKE[stage]}


def _remove_world() -> None:
	frappe.set_user("Administrator")
	fx.wipe_tender_rows()
	for name in HANDOFFS:
		if frappe.db.exists("Authorised Requisition Handoff", name):
			frappe.delete_doc("Authorised Requisition Handoff", name, force=1, ignore_permissions=True)
	for user in (TECH, EXTRA):
		for name in frappe.get_all("User Responsibility Assignment", filters={"user": user}, pluck="name"):
			frappe.delete_doc("User Responsibility Assignment", name, force=1, ignore_permissions=True)
		for name in frappe.get_all("Contact Email", filters={"email_id": user}, pluck="parent"):
			frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
		if frappe.db.exists("User", user):
			frappe.delete_doc("User", user, force=1, ignore_permissions=True)
	frappe.db.commit()
	left = {doctype: frappe.db.count(doctype, {"fixture_namespace": NS}) for doctype in ("Tender", "Tender Task", "Tender Cancellation", "Tender Version", "Authorised Requisition Handoff")}
	left["handoffs by name"] = sum(1 for name in HANDOFFS if frappe.db.exists("Authorised Requisition Handoff", name))
	left["users"] = frappe.db.count("User", {"name": ("in", [TECH, EXTRA])})
	left = {name: count for name, count in left.items() if count}
	if left:
		raise AssertionError(f"Tenders Analytics test rows left behind: {left}")


class TestTendersAnalyticsProvider(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)
		cls.addClassCleanup(_remove_world)
		fx.wipe_tender_rows()
		fx._user(TECH, "TNDANL Technical Operator")
		fx._grant(TECH, "Technical Operator")
		fx._user(EXTRA, "TNDANL Extra Head of Department")
		_world()
		frappe.db.commit()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		del CALLS[:]
		patcher = mock.patch.object(provider, "stage_facts", side_effect=_fake_stage_facts)
		patcher.start()
		self.addCleanup(patcher.stop)
		self.addCleanup(frappe.set_user, "Administrator")

	# ----- helpers -----

	def read(self, user: str) -> dict[str, dict]:
		"""This world's records by key (the test site also holds canonical Tenders)."""
		by_id = {entry["tender"].name: key for key, entry in WORLD.items()}
		result = provider.facts(user=user, kind="tenders", at=AT)
		return {by_id[r["id"]]: r for r in result["records"] if r["id"] in by_id}

	def rec(self, key: str, user: str = fx.HOPF) -> dict:
		return self.read(user)[key]

	# ----- who may read -----

	def test_every_tenders_reader_applies_and_an_unrelated_user_does_not(self):
		for user in (fx.OFFICER, fx.HOPF, fx.AO, fx.AUDITOR, fx.BOTH, TECH, "Administrator", fx.DEPARTMENTAL, fx.OUTSIDER, req_fx.HOD):
			self.assertEqual(provider.applies(user=user, at=AT), {"tenders"}, user)
		for user in (fx.NOBODY, fx.PRODUCER, "Guest", ""):
			self.assertEqual(provider.applies(user=user, at=AT), set(), user)
			self.assertEqual(provider.facts(user=user, kind="tenders", at=AT)["records"], [], user)

	def test_site_wide_readers_and_technical_readers_see_every_tender_once(self):
		for user in (fx.OFFICER, fx.HOPF, fx.AO, fx.AUDITOR, "Administrator", TECH):
			records = self.read(user)
			self.assertEqual(set(records), set(WORLD), user)
		ids = [r["id"] for r in provider.facts(user=fx.AO, kind="tenders", at=AT)["records"]]
		self.assertEqual(len(ids), len(set(ids)))

	def test_a_technical_operator_reads_what_the_head_of_procurement_reads(self):
		def figures(user):
			return {key: (r["bucket"], r["position"], r["authorised_lines"], r["award_amount"], r["award_amount_visible"], r["decision_events"]) for key, r in self.read(user).items()}

		self.assertEqual(figures(TECH), figures(fx.HOPF))
		self.assertEqual(figures("Administrator"), figures(fx.HOPF))

	def test_a_department_reader_sees_only_a_tender_whose_lead_or_contributing_unit_is_in_scope(self):
		alpha_only = {"t041", "t042", "t044", "t045", "t047"}  # 044 is led by Beta; Alpha contributes
		beta_side = {"t041", "t043", "t044", "t046", "t048", "t049", "t050"}  # 041 is led by Alpha; Beta contributes
		for user in (fx.DEPARTMENTAL, req_fx.HOD):
			self.assertEqual(set(self.read(user)), alpha_only, user)
		self.assertEqual(set(self.read(fx.OUTSIDER)), beta_side)

	def test_the_head_of_user_department_is_never_given_an_award_amount_and_a_site_reader_is(self):
		for user in (fx.DEPARTMENTAL, req_fx.HOD):
			record = self.rec("t045", user)
			self.assertEqual((record["award_amount"], record["award_amount_visible"]), (None, False), user)
			# the decision itself is a fact the actor may know
			self.assertEqual(record["decision_outcome"], "Award")
		for user in (fx.HOPF, fx.AO, fx.AUDITOR, TECH, "Administrator"):
			record = self.rec("t045", user)
			self.assertEqual((record["award_amount"], record["award_amount_visible"]), (Decimal("7185000.00"), True), user)
		# a Tender with no Award case has no amount; a department reader still reads False
		self.assertEqual((self.rec("t042")["award_amount"], self.rec("t042", req_fx.HOD)["award_amount_visible"]), (None, False))

	def test_a_department_reader_gets_no_award_matter_and_a_generic_award_position_a_site_reader_gets_both(self):
		# OVS-CHG-001 v0.6 §4.1: unissued notices and the professional opinion stay outside the Head of User Department's read
		for user in (fx.DEPARTMENTAL, req_fx.HOD):
			decided, opinion = self.rec("t045", user), self.rec("t044", user)
			self.assertEqual((decided["bucket"], decided["position"], decided["outstanding"]), ("award", "Award — decision recorded", None), user)
			self.assertEqual((opinion["bucket"], opinion["position"], opinion["outstanding"]), ("award", "Award", None), user)
		self.assertEqual(self.rec("t045")["outstanding"]["text"], "Award decision recorded. Required bidder notices are awaiting delivery.")
		self.assertEqual(self.rec("t044")["position"], "Award — awaiting professional opinion by Charles Mutiso")
		# Evaluation's administrative progress before delivery stays for a department reader whose unit contributes (Beta)
		self.assertEqual(self.rec("t043", fx.OUTSIDER)["position"], "Evaluation — automatic checks complete; committee review outstanding")
		self.assertEqual(self.rec("t043", fx.OUTSIDER)["outstanding"]["holder"], "Grace Wambui")

	def test_a_revoked_scope_removes_the_tenders(self):
		administration.grant(user=EXTRA, business_role="Head of User Department", organisation_unit=req_fx.ou_alpha(), fixture_namespace=EXTRA_NS, actor="Administrator")
		self.assertEqual(provider.applies(user=EXTRA, at=AT), {"tenders"})
		self.assertEqual(set(self.read(EXTRA)), {"t041", "t042", "t044", "t045", "t047"})
		assignment = frappe.get_all("User Responsibility Assignment", filters={"user": EXTRA, "status": "Enabled"}, pluck="name")[0]
		administration.revoke(assignment, reason="Revoked inside the Tenders Analytics test.", actor="Administrator")
		self.assertEqual(provider.applies(user=EXTRA, at=AT), set())
		self.assertEqual(provider.facts(user=EXTRA, kind="tenders", at=AT)["records"], [])

	# ----- the record -----

	def test_a_record_carries_identity_year_units_and_the_modules_own_route(self):
		record = self.rec("t041")
		entry = WORLD["t041"]
		self.assertEqual((record["kind"], record["id"], record["title"], record["reference"]), ("tenders", entry["tender"].name, "Supply of IT peripherals", "TNDANL-041"))
		self.assertEqual(record["fiscal_year"], _fiscal_year())
		self.assertEqual(record["org_units"], [req_fx.ou_alpha(), req_fx.ou_beta()])  # lead first, then the other contributor, no duplicate
		self.assertEqual(record["route"], ["tenders", "TNDANL-041"])
		self.assertEqual(self.rec("t044")["org_units"], [req_fx.ou_beta(), req_fx.ou_alpha()])

	def test_authorised_lines_are_the_consumed_versions_value_by_department_parsed_from_data_strings(self):
		lines = self.rec("t041")["authorised_lines"]
		self.assertEqual(lines, [{"org_unit": req_fx.ou_alpha(), "amount": Decimal("5000000.00")}, {"org_unit": req_fx.ou_beta(), "amount": Decimal("2500000.00")}])
		self.assertTrue(all(isinstance(line["amount"], Decimal) for r in self.read(fx.AO).values() for line in r["authorised_lines"]))
		self.assertEqual(self.rec("t046")["authorised_lines"], [{"org_unit": req_fx.ou_beta(), "amount": Decimal("25000000.00")}])

	def test_the_instants_tenders_owns(self):
		self.assertEqual(self.rec("t041")["started_at"], _dt("2027-05-10 08:00"))
		self.assertIsNone(self.rec("t041")["published_at"])
		self.assertEqual(self.rec("t042")["published_at"], _dt("2027-04-20 11:00"))
		self.assertIsNone(self.rec("t042")["cancelled_at"])
		cancelled = self.rec("t046")
		self.assertEqual((cancelled["cancelled_at"], cancelled["cancellation_events"]), (_dt("2027-06-16 12:00"), [_dt("2027-06-16 12:00")]))
		self.assertEqual(self.rec("t042")["cancellation_events"], [])

	def test_the_stage_owners_instants_are_mapped_and_a_tender_without_cases_has_none(self):
		evaluating, deciding = self.rec("t044"), self.rec("t045")
		self.assertEqual((evaluating["opening_complete_at"], evaluating["report_sent_at"], evaluating["award_received_at"]), (_dt("2027-06-01 12:00"), _dt("2027-06-10 09:00"), _dt("2027-06-16 14:07")))
		self.assertEqual((deciding["decision_at"], deciding["decision_outcome"], deciding["decision_events"]), (_dt("2027-06-17 11:00"), "Award", [_dt("2027-06-17 11:00"), _dt("2027-06-17 15:30")]))
		empty = self.rec("t049")  # an empty opening has no completion instant, no report and no award
		self.assertEqual((empty["opening_complete_at"], empty["report_sent_at"], empty["award_received_at"], empty["decision_events"]), (None, None, None, []))

	# ----- buckets and positions through the provider -----

	def test_every_tender_is_classified_once_in_the_owners_words(self):
		expected = {
			"t041": ("preparation", "Tender preparation — supplier and contract requirements returned for correction"),
			"t042": ("open", "Open for bids"),
			"t043": ("evaluation", "Evaluation — automatic checks complete; committee review outstanding"),
			"t044": ("award", "Award — awaiting professional opinion by Charles Mutiso"),
			"t045": ("award", "Award — required bidder notices are awaiting delivery"),
			"t046": ("closed", "Closed — cancelled; cancellation compliance evidence outstanding"),
			"t047": ("opening", "Opening — submission closed; opening not yet started"),
			"t048": ("unavailable", "Status unavailable"),
			"t049": ("closed", "Closed — no bids received; no evaluation required"),
			"t050": ("closed", "Closed — cancelled; cancellation compliance evidence complete"),
		}
		records = self.read(fx.HOPF)
		self.assertEqual({key: (r["bucket"], r["position"]) for key, r in records.items()}, expected)
		self.assertTrue(all(r["bucket"] in contract.BUCKETS for r in records.values()))

	def test_a_past_deadline_tender_the_hourly_job_has_not_closed_reads_opening_not_open_for_bids(self):
		tender = WORLD["t047"]["tender"]
		self.assertEqual(frappe.db.get_value("Tender", tender.name, "overall_status"), "Published — open")
		self.assertEqual(self.rec("t047")["bucket"], "opening")
		# the same Tender read before its deadline is open for bids
		before = provider.facts(user=fx.HOPF, kind="tenders", at=_dt("2027-06-17 16:59"))["records"]
		self.assertEqual({r["id"]: r["bucket"] for r in before}[tender.name], "open")

	# ----- outstanding matters -----

	def test_a_returned_tender_reads_the_return_comment_and_who_corrects_it_since_the_return(self):
		matter = self.rec("t041")["outstanding"]
		officer = frappe.db.get_value("User", fx.OFFICER, "full_name")
		self.assertEqual(matter, {"text": f"State the warranty period required from suppliers. Awaiting correction by {officer}.", "holder": officer, "since": _dt("2027-06-16 09:00")})

	def test_one_matter_from_the_latest_stage_that_holds_it(self):
		self.assertEqual(self.rec("t043")["outstanding"]["text"], "Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee.")
		self.assertEqual(self.rec("t044")["outstanding"], {"text": "Awaiting professional opinion by Charles Mutiso.", "holder": "Charles Mutiso", "since": _dt("2027-06-16 14:07")})
		self.assertEqual(self.rec("t045")["outstanding"]["text"], "Award decision recorded. Required bidder notices are awaiting delivery.")
		# nothing outstanding where nothing is held
		self.assertIsNone(self.rec("t042")["outstanding"])
		self.assertIsNone(self.rec("t049")["outstanding"])

	def test_a_cancelled_tender_keeps_only_its_own_compliance_follow_up(self):
		matter = self.rec("t046")["outstanding"]
		officer = frappe.db.get_value("User", fx.OFFICER, "full_name")
		self.assertEqual((matter["text"], matter["holder"], matter["since"]), (f"Waiting for cancellation compliance evidence from {officer}.", officer, _dt("2027-06-16 12:00:01")))
		self.assertIsNone(self.rec("t050")["outstanding"])

	def test_a_stage_owners_matter_wins_over_the_tenders_own_and_a_tenders_own_shows_when_the_stage_has_none(self):
		task = _task("t045", handoffs.CLARIFICATION_RESPONSE, creation="2027-06-17 12:00", subject_type="Tender Clarification", subject_id="CLR-NONE")
		try:
			self.assertEqual(self.rec("t045")["outstanding"]["text"], "Award decision recorded. Required bidder notices are awaiting delivery.")
			saved = FAKE["award"][WORLD["t045"]["tender"].name]
			with mock.patch.dict(FAKE["award"], {WORLD["t045"]["tender"].name: {**saved, "outstanding": None}}):
				self.assertTrue(self.rec("t045")["outstanding"]["text"].startswith("Waiting for"), self.rec("t045")["outstanding"])
		finally:
			doc = frappe.get_doc("Tender Task", task)
			doc.flags.kt_fixture_wipe = True
			doc.delete(ignore_permissions=True, force=True)

	# ----- failure and wiring -----

	def test_a_stage_owner_failing_for_one_tender_makes_only_that_tender_unavailable(self):
		records = self.read(fx.HOPF)
		self.assertEqual(records["t048"]["bucket"], "unavailable")
		self.assertEqual(records["t048"]["position"], "Status unavailable")
		for key in WORLD:
			if key != "t048":
				self.assertNotEqual(records[key]["bucket"], "unavailable", key)
		# the batch was tried first, then Tender by Tender: the failing one was asked alone
		opening_calls = [call for call in CALLS if call[0] == "opening"]
		self.assertGreater(len(opening_calls), 1)
		self.assertIn((WORLD["t048"]["tender"].name,), [call[2] for call in opening_calls])

	def test_a_missing_stage_module_is_a_failed_read_for_the_tenders_that_need_it_and_never_an_import_error(self):
		modules = {**provider.STAGE_MODULES, "evaluation": "kentender_procurement.bid_evaluation.services.analytics_facts_does_not_exist"}

		def real_for_evaluation(stage, *, user, tender_names, at):
			if stage == "evaluation":
				return _REAL_STAGE_FACTS(stage, user=user, tender_names=tender_names, at=at)
			return _fake_stage_facts(stage, user=user, tender_names=tender_names, at=at)

		with mock.patch.dict(provider.STAGE_MODULES, modules), mock.patch.object(provider, "stage_facts", side_effect=real_for_evaluation):
			records = self.read(fx.HOPF)
		# 043, 044 and 045 have a complete opening, so Evaluation is needed; 047 and 049 do not need it
		for key in ("t043", "t044", "t045"):
			self.assertEqual(records[key]["bucket"], "unavailable", key)
		self.assertEqual(records["t049"]["bucket"], "closed")
		self.assertEqual(records["t047"]["bucket"], "opening")
		self.assertEqual(records["t041"]["bucket"], "preparation")

	def test_unusable_owner_facts_for_a_tender_make_it_unavailable_never_a_guess(self):
		name = WORLD["t045"]["tender"].name
		saved = FAKE["award"][name]
		for bad in ({**saved, "decision_outcome": "Return for correction"}, {**saved, "award_amount": "not money"}, {**saved, "outstanding": {"text": "", "holder": "", "since": None}}, "garbage"):
			with mock.patch.dict(FAKE["award"], {name: bad}):
				records = self.read(fx.HOPF)
			self.assertEqual(records["t045"]["bucket"], "unavailable", bad)
			self.assertEqual(records["t044"]["bucket"], "award")

	def test_the_real_stage_owners_are_wired_and_a_tender_with_no_case_is_pending_not_failed(self):
		# no fakes: the real Bid Opening and Award `facts_for` (and Evaluation's, once it exists) are called with no case behind any
		# world Tender; a failed or missing owner is only fatal where the classification needs it, and none does here
		with mock.patch.object(provider, "stage_facts", _REAL_STAGE_FACTS):
			records = self.read("Administrator")
		self.assertEqual(set(records), set(WORLD))
		for key in ("t043", "t044", "t045", "t047", "t048", "t049"):
			self.assertEqual(records[key]["bucket"], "opening", key)
		self.assertEqual(records["t046"]["bucket"], "closed")
		self.assertEqual(records["t041"]["bucket"], "preparation")

	def test_the_owners_are_asked_only_about_tenders_past_submission_and_with_the_actor(self):
		self.read(fx.AO)
		asked = {name for _stage, user, names in CALLS for name in names}
		for key in ("t041", "t042"):
			self.assertNotIn(WORLD[key]["tender"].name, asked, key)
		for key in ("t043", "t046", "t047"):
			self.assertIn(WORLD[key]["tender"].name, asked, key)
		self.assertEqual({user for _stage, user, _names in CALLS}, {fx.AO})
		self.assertEqual({stage for stage, _user, _names in CALLS}, {"opening", "evaluation", "award"})

	def test_an_unreadable_requisition_handoff_fails_the_read_it_is_never_a_zero(self):
		tender = WORLD["t042"]["tender"]
		frappe.db.set_value("Tender", tender.name, "requisition_handoff", "RQH-DOES-NOT-EXIST", update_modified=False)
		try:
			with self.assertRaises(ValueError):
				provider.facts(user=fx.HOPF, kind="tenders", at=AT)
		finally:
			frappe.db.set_value("Tender", tender.name, "requisition_handoff", WORLD["t042"]["handoff"], update_modified=False)

	def test_only_the_tenders_kind_is_served_and_every_record_passes_the_contract(self):
		with self.assertRaises(ValueError):
			provider.facts(user=fx.HOPF, kind="needs", at=AT)
		for rec in provider.facts(user=fx.HOPF, kind="tenders", at=AT)["records"]:
			contract.validate(rec)

	# ----- a read changes nothing -----

	def test_reading_creates_and_changes_nothing(self):
		doctypes = ("Tender", "Tender Version", "Tender Task", "Tender Decision", "Tender Event", "Tender Cancellation", "Tender Command Journal", "Tender Submission Handoff",
			"Authorised Requisition Handoff", "Notification Log", "Error Log")
		frappe.db.commit()
		counts = {d: frappe.db.count(d) for d in doctypes}
		modified = {name: frappe.db.get_value("Tender", name, "modified") for name in [e["tender"].name for e in WORLD.values()]}
		writes = frappe.db.transaction_writes
		for user in (fx.OFFICER, fx.HOPF, fx.AO, fx.AUDITOR, TECH, "Administrator", fx.DEPARTMENTAL, req_fx.HOD, fx.NOBODY):
			provider.applies(user=user, at=AT)
			provider.facts(user=user, kind="tenders", at=AT)
		with mock.patch.object(provider, "stage_facts", _REAL_STAGE_FACTS):
			provider.facts(user="Administrator", kind="tenders", at=AT)
		self.assertEqual(frappe.db.transaction_writes, writes)
		self.assertEqual({d: frappe.db.count(d) for d in doctypes}, counts)
		self.assertEqual(modified, {name: frappe.db.get_value("Tender", name, "modified") for name in modified})
		for key, expected in (("t042", "Published — open"), ("t047", "Published — open")):
			self.assertEqual(frappe.db.get_value("Tender", WORLD[key]["tender"].name, "overall_status"), expected)  # the hourly close was not run

