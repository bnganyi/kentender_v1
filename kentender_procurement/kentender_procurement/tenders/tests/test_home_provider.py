# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — the Tenders feed to Home (`tenders/services/home_provider.py`).

One shared world for the whole module (built once, read by every test; the provider only reads), with the §10B fixtures'
timeline: Brian (Procurement Officer), Charles (Head of Procurement Function) and Amina (Accounting Officer) are the Tenders
test world's own actors. Tenders are inserted directly with their hand-offs (no command flows); the world and every row it
adds are removed afterwards and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.tenders.tests.test_home_provider
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import frappe
from kentender_core.services.command_write_guard import purge_doc
from frappe.tests import IntegrationTestCase

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import home_workspace as hw
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.tenders.services import envelope, handoffs, my_work_provider
from kentender_procurement.tenders.services.home_provider import entries
from kentender_procurement.tenders.tests import fixtures as fx
from kentender_procurement.tenders.tests import sample

NS = fx.NS
EXTRA = "tndt.home.extra@example.test"  # a second Head of Procurement Function, granted and revoked inside one test
EXTRA_NS = "KT_TEST_TNDHOME"
EARLY = "2027-05-15 07:55:00"  # the Tender clock when no submission deadline is too close
LATE = "2027-06-03 09:00:00"  # 5 June is then two days away: the minimum preparation period no longer fits
H1 = datetime(2027, 6, 17, 10, 0)
H12 = datetime(2027, 6, 18, 10, 0)
SPEC_PAGES = ("tenders", "procurement-requisitions")
WORLD: dict[str, dict] = {}


def _dt(text: str) -> datetime:
	return datetime.strptime(text, "%Y-%m-%d %H:%M")


def _tender(key: str, reference: str, title: str, *, status: str, unit: str = "", officer_title: bool = True, approved: bool = False, by: dict | None = None):
	"""A Tender and Version with the sample package, set to `status`; `by` fills the Version's people and instants."""
	values = sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE)
	values = {**values, "tender_title": title} if officer_title else {}
	tender, version = sample.insert_tender_with_version(reference=reference, values=values, fixture_namespace=NS)
	if by:
		envelope.bump(version, **by)
	fields = {"overall_status": status, "lead_org_unit": unit or None, "contributing_org_unit_ids": json.dumps([unit] if unit else [])}
	if approved:
		fields["approved_version"] = version.name
	envelope.bump(tender, **fields)
	WORLD[key] = {"tender": tender, "version": version}
	return tender, version


def _task(key: str, task_type: str, *, creation: str, holder: str = "", sender: str = "", subject_type: str = "", subject_id: str = ""):
	entry = WORLD[key]
	task = handoffs.open_task(entry["tender"], entry["version"], task_type=task_type, holder=holder, sender=sender, subject_type=subject_type, subject_id=subject_id, notify=False)
	frappe.db.set_value("Tender Task", task.name, "creation", _dt(creation), update_modified=False)
	entry.setdefault("tasks", {})[task_type] = task.name
	return task


def _decision(key: str, decision: str, *, actor: str, role: str, at: datetime) -> str:
	entry = WORLD[key]
	doc = envelope.insert(frappe.get_doc({
		"doctype": "Tender Decision", "tender": entry["tender"].name, "tender_version": entry["version"].name, "decision": decision, "actor": actor, "business_role": role,
		"authority_snapshot": "{}", "decided_at": at, "command_idempotency_key": fx.key(), "fixture_namespace": NS,
	}))
	entry.setdefault("decisions", {})[decision] = doc.name
	return doc.name


def _world() -> None:
	"""The §10B timeline: Brian's cancellation compliance (034), the cancellation Amina is asked to consider (039), two clarifications
	(040 plain, 041 waiting on an addendum), Charles's approval and Amina's publication decision (047), a desktop-computers Tender
	Brian submitted (044), a returned Tender in the Human Resources unit (048), a Tender awaiting approval in another unit (049)
	and a requisition correction (050)."""
	officer, hopf, ao = fx.OFFICER, fx.HOPF, fx.AO
	by_brian = {"prepared_by": officer, "submitted_by": officer}
	cancelled, _v = _tender("t034", "TNDT-HOME-034", "Supply of hospital beds", status="Cancelled")
	cancelled_doc = envelope.insert(frappe.get_doc({
		"doctype": "Tender Cancellation", "tender": cancelled.name, "ground": "NEED_CEASED", "ground_label": "The procurement need has ceased", "reason": "The need has ceased entirely.",
		"decided_by": ao, "decided_at": _dt("2027-06-15 12:00"), "ppra_report_due_by": date(2027, 6, 18), "candidate_notice_due_by": date(2027, 6, 20), "record_version": 0, "fixture_namespace": NS,
		"obligations": [
			{"obligation_id": "NOTICE-WEB", "obligation_type": "Notice channel", "channel": "WEB", "label": "Cancellation notice — Web", "due_by": date(2027, 6, 16), "status": "Recorded", "evidence_reference": "EV-1"},
			{"obligation_id": "PPRA_REPORT", "obligation_type": "PPRA report", "channel": "PPRA_REPORT", "label": "PPRA report", "due_by": date(2027, 6, 18), "status": "Due"},
			{"obligation_id": "CANDIDATE_NOTICE", "obligation_type": "Candidate notice", "channel": "CANDIDATE_NOTICE", "label": "Candidate notice", "due_by": date(2027, 6, 20), "status": "Due"},
		],
	}))
	envelope.bump(cancelled, cancellation=cancelled_doc.name)
	_task("t034", handoffs.CANCELLATION_COMPLIANCE, creation="2027-06-15 12:00", holder=officer, sender=ao, subject_type="Tender Cancellation", subject_id=cancelled_doc.name)

	_tender("t039", "TNDT-HOME-039", "Supply of field laptops", status="Published — open")
	_task("t039", handoffs.CANCELLATION_REVIEW, creation="2027-06-16 14:00", sender=officer)

	for key, reference, title, status in (("t040", "TNDT-HOME-040", "Supply of clinic peripherals", "Awaiting response"), ("t041", "TNDT-HOME-041", "Supply of training tablets", "Awaiting addendum")):
		tender, _v = _tender(key, reference, title, status="Published — open")
		clarification = envelope.insert(frappe.get_doc({
			"doctype": "Tender Clarification", "tender": tender.name, "candidate_registration_id": f"CAND-{reference}", "question": "Is a 3-year warranty acceptable?", "status": status,
			"received_at": _dt("2027-06-16 10:00"), "record_version": 0, "fixture_namespace": NS,
		}))
		_task(key, handoffs.CLARIFICATION_RESPONSE, creation="2027-06-16 10:00" if key == "t040" else "2027-06-16 10:30", subject_type="Tender Clarification", subject_id=clarification.name)

	_tender("t044", "TNDT-HOME-044", "Supply of desktop computers", status="Approved", approved=True, by={**by_brian, "approved_by": hopf, "approved_at": _dt("2027-06-16 09:30")})
	_decision("t044", "Submit for approval", actor=officer, role="Procurement Officer", at=_dt("2027-06-16 09:00"))

	_tender("t047", "TNDT-HOME-047", "Supply of UPS units", status="Approved", approved=True, by={**by_brian, "approved_by": hopf, "approved_at": _dt("2027-06-16 15:30")})
	_task("t047", handoffs.AO_AUTHORISATION, creation="2027-06-16 15:30", sender=hopf)
	_decision("t047", "Approve Tender package", actor=hopf, role="Head of Procurement Function", at=_dt("2027-06-16 15:30"))

	_tender("t042", "TNDT-HOME-042", "Supply of network switches", status="Published — open")
	_decision("t042", "Respond to clarification", actor=officer, role="Procurement Officer", at=_dt("2027-06-17 11:00"))
	_decision("t042", "Discard addendum draft", actor=officer, role="Procurement Officer", at=_dt("2027-06-17 11:30"))

	alpha, beta = req_fx.ou_alpha(), req_fx.ou_beta()
	_tender("t048", "TNDT-HOME-048", "Supply of IT peripherals", status="Draft", unit=alpha)
	_task("t048", handoffs.CORRECT_RETURNED, creation="2027-06-16 09:00", holder=officer, sender=hopf)
	_tender("t049", "TNDT-HOME-049", "Supply of ward linen", status="Awaiting procurement approval", unit=beta, officer_title=False, by=by_brian)
	_task("t049", handoffs.HOPF_APPROVAL, creation="2027-06-17 10:00", sender=officer)
	_tender("t051", "TNDT-HOME-051", "Supply of dispensers", status="Approved", approved=True, by={**by_brian, "approved_by": hopf, "approved_at": _dt("2027-06-16 15:30")})
	_task("t051", handoffs.AO_AUTHORISATION, creation="2027-06-16 15:30", holder=ao, sender=hopf)
	_tender("t050", "TNDT-HOME-050", "Supply of cleaning materials", status="Requisition correction requested")
	_task("t050", handoffs.REQUISITION_CORRECTION, creation="2027-06-16 08:00", holder=fx.DEPARTMENTAL, sender=officer, subject_type="Procurement Requisition", subject_id="REQ-HOME-NOT-REAL")


def _remove_world() -> None:
	frappe.set_user("Administrator")
	fx.wipe_tender_rows()
	for name in frappe.get_all("User Responsibility Assignment", filters={"user": EXTRA}, pluck="name"):
		purge_doc("User Responsibility Assignment", name)
	for name in frappe.get_all("Contact Email", filters={"email_id": EXTRA}, pluck="parent"):
		frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
	if frappe.db.exists("User", EXTRA):
		frappe.delete_doc("User", EXTRA, force=1, ignore_permissions=True)
	frappe.db.commit()
	left = {doctype: frappe.db.count(doctype, {"fixture_namespace": NS}) for doctype in ("Tender", "Tender Task", "Tender Decision", "Tender Cancellation", "Tender Clarification", "Tender Version")}
	if any(left.values()):
		raise AssertionError(f"Tenders Home test rows left behind: {left}")


class TestTendersHomeProvider(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)
		cls.addClassCleanup(_remove_world)
		fx.wipe_tender_rows()
		fx._user(EXTRA, "TNDT Extra Head of Procurement")
		frappe.flags.kt_tenders_clock = EARLY
		_world()
		frappe.flags.kt_tenders_clock = None
		frappe.db.commit()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		frappe.flags.kt_tenders_clock = EARLY
		home_support.reset()
		self.addCleanup(setattr, frappe.flags, "kt_tenders_clock", None)
		self.addCleanup(frappe.set_user, "Administrator")

	# ----- helpers -----

	def region(self, user: str, region: str):
		home_support.reset()
		return entries(user=user, region=region)

	def mine(self, rows):
		"""The rows about this world's Tenders (the test site also holds canonical Tenders)."""
		roots = {entry["tender"].name for entry in WORLD.values()}
		return [row for row in rows or [] if row["root"] in roots]

	def one(self, user: str, region: str, key: str):
		root = WORLD[key]["tender"].name
		rows = [row for row in self.region(user, region) or [] if row["root"] == root]
		self.assertEqual(len(rows), 1, f"{user} {region} {key}: {rows}")
		return rows[0]

	def task(self, key: str, task_type: str) -> str:
		return WORLD[key]["tasks"][task_type]

	def reference(self, key: str) -> str:
		return WORLD[key]["tender"].tender_reference

	def name(self, user: str) -> str:
		return frappe.db.get_value("User", user, "full_name")

	def home(self, user: str, at: datetime):
		return hw.get_workspace(user, providers=[entries], at=at)

	def all_rows(self, user: str, at: datetime, region: str) -> list[dict]:
		"""Every presented row of the region, following Show more (the test site also holds canonical Tenders)."""
		rows, cursor = [], None
		while True:
			page = hw.get_workspace(user, regions=[region], cursors={region: cursor} if cursor else None, providers=[entries], at=at)["regions"][region]
			rows += page["entries"]
			cursor = page["next_cursor"]
			if not cursor:
				return rows

	def row(self, user: str, at: datetime, region: str, key: str) -> dict:
		reference = self.reference(key)
		rows = [row for row in self.all_rows(user, at, region) if row["reference"] == reference]
		self.assertEqual(len(rows), 1, f"{region} {key}: {rows}")
		return rows[0]

	def holders(self, text: str, prefix: str, suffix: str, role: str) -> None:
		"""`text` is prefix + the people who hold `role` site-wide (either order) when there are two or fewer, otherwise the
		responsibility ("an Accounting Officer") + suffix. How many people hold it depends on the site."""
		self.assertTrue(text.startswith(prefix) and text.endswith(suffix), text)
		people = text[len(prefix) : len(text) - len(suffix)]
		holders = handoffs.users_with_site_role(role)
		if len(holders) <= 2:
			self.assertEqual(set(people.split(" or ")), {handoffs.full_name(user) for user in holders}, text)
		else:
			self.assertIn(people, (role, f"an {role}", f"a {role}"), text)

	# ----- My work -----

	def test_the_accounting_officers_work_is_worded_by_the_owner_without_the_reference(self):
		consider = self.one(fx.AO, he.MY_WORK, "t039")
		self.assertEqual((consider["title"], consider["action"], consider["reference"]), ("Supply of field laptops", "Consider cancellation", self.reference("t039")))
		self.assertEqual((consider["entered_at"], consider["entered_verb"], consider["action_id"]), (_dt("2027-06-16 14:00"), "Received", self.task("t039", handoffs.CANCELLATION_REVIEW)))
		self.assertEqual(consider["destination"], {"route": ["tenders", self.reference("t039"), "cancel"], "route_options": {}})
		authorise = self.one(fx.AO, he.MY_WORK, "t047")
		self.assertEqual((authorise["title"], authorise["action"], authorise["blocked"], authorise["reason"]), ("Supply of UPS units", "Authorise publication", False, ""))
		self.assertEqual((authorise["entered_at"], authorise["destination"]["route"]), (_dt("2027-06-16 15:30"), ["tenders", self.reference("t047")]))
		self.assertIsNone(authorise["due"])
		self.assertTrue(all(row["owner"] == "tenders" and row["region"] == he.MY_WORK for row in self.mine(self.region(fx.AO, he.MY_WORK))))

	def test_the_title_is_the_officers_own_and_falls_back_to_the_requisition_title(self):
		root = WORLD["t039"]["tender"]
		self.assertNotEqual(root.requirement_title, "Supply of field laptops")  # the data model really holds two titles
		self.assertEqual(self.one(fx.AO, he.MY_WORK, "t039")["title"], "Supply of field laptops")
		self.assertEqual(self.one(fx.HOPF, he.MY_WORK, "t049")["title"], WORLD["t049"]["tender"].requirement_title)

	def test_brians_cancellation_compliance_carries_the_earliest_unrecorded_obligation_as_a_date(self):
		compliance = self.one(fx.OFFICER, he.MY_WORK, "t034")
		self.assertEqual((compliance["action"], compliance["title"], compliance["reference"]), ("Record cancellation notices and PPRA report", "Supply of hospital beds", self.reference("t034")))
		self.assertEqual((compliance["due"], type(compliance["due"])), (date(2027, 6, 18), date))
		self.assertEqual((compliance["entered_at"], compliance["destination"]["route"]), (_dt("2027-06-15 12:00"), ["tenders", self.reference("t034"), "cancel"]))
		self.assertTrue(all(row["due"] is None for row in self.mine(self.region(fx.OFFICER, he.MY_WORK)) if row["action_id"] != compliance["action_id"]))

	def test_a_plain_clarification_is_not_blocked_and_one_waiting_on_an_addendum_says_why(self):
		plain = self.one(fx.OFFICER, he.MY_WORK, "t040")
		self.assertEqual((plain["action"], plain["blocked"], plain["reason"]), ("Respond to clarification", False, ""))
		self.assertEqual(plain["destination"]["route"][:3], ["tenders", self.reference("t040"), "clarifications"])
		blocked = self.one(fx.OFFICER, he.MY_WORK, "t041")
		self.assertEqual((blocked["action"], blocked["blocked"], blocked["reason"]), ("Respond to clarification", True, "Issue an addendum before sending this answer."))
		# the Head of Procurement Function shares the item (§6) and is told the same
		self.assertEqual(self.one(fx.HOPF, he.MY_WORK, "t041")["reason"], "Issue an addendum before sending this answer.")

	def test_the_returned_tender_and_the_requisition_correction_keep_the_owners_routes(self):
		returned = self.one(fx.OFFICER, he.MY_WORK, "t048")
		self.assertEqual(returned["action"], "Correct Tender — Supplier and contract requirements")
		self.assertEqual(returned["destination"]["route"][:2], ["tenders", self.reference("t048")])
		correction = self.one(fx.DEPARTMENTAL, he.MY_WORK, "t050")
		self.assertEqual((correction["action"], correction["destination"]["route"]), ("Correct Requisition REQ-HOME-NOT-REAL", ["procurement-requisitions", "REQ-HOME-NOT-REAL"]))

	def test_an_authorisation_blocked_by_the_preparation_period_says_so_and_the_derived_rows_appear(self):
		frappe.flags.kt_tenders_clock = LATE
		blocked = self.one(fx.AO, he.MY_WORK, "t047")
		self.assertTrue(blocked["blocked"])
		self.assertTrue(blocked["reason"].startswith("The submission deadline, ") and "are required" in blocked["reason"], blocked["reason"])
		self.assertEqual(blocked["action"], "Authorise publication")
		root = WORLD["t047"]["tender"].name
		reopen = [row for row in self.region(fx.HOPF, he.MY_WORK) if row["action_id"] == f"{root}:period"]
		self.assertEqual([(row["action"], row["title"], row["destination"]["route"]) for row in reopen], [("Reopen Tender — submission deadline too short", "Supply of UPS units", ["tenders", self.reference("t047")])])
		self.assertEqual(reopen[0]["entered_at"], _dt("2027-06-16 15:30"))
		waiting = [row for row in self.region(fx.AO, he.WAITING) if row["action_id"] == f"{root}:period"]
		self.assertEqual(len(waiting), 1)
		self.assertTrue(waiting[0]["action"].startswith("Waiting for ") and waiting[0]["action"].endswith(" to reopen this Tender"))
		self.assertEqual(waiting[0]["title"], "Supply of UPS units")

	# ----- Waiting -----

	def test_what_the_head_of_procurement_sent_to_the_accounting_officer_is_waiting_with_since(self):
		waiting = self.one(fx.HOPF, he.WAITING, "t047")
		self.assertEqual((waiting["title"], waiting["reference"], waiting["since"], waiting["due"]), ("Supply of UPS units", self.reference("t047"), _dt("2027-06-16 15:30"), None))
		self.holders(waiting["action"], "Waiting for ", " to decide publication", "Accounting Officer")
		self.holders(waiting["holder"], "", "", "Accounting Officer")
		self.assertEqual(waiting["action_id"], self.task("t047", handoffs.AO_AUTHORISATION))

	def test_a_named_holder_reads_exactly_as_the_spec_does(self):
		waiting = self.one(fx.HOPF, he.WAITING, "t051")
		self.assertEqual((waiting["action"], waiting["holder"]), (f"Waiting for {self.name(fx.AO)} to decide publication", self.name(fx.AO)))

	def test_brian_waits_for_the_accounting_officer_to_consider_cancellation(self):
		waiting = self.one(fx.OFFICER, he.WAITING, "t039")
		self.assertTrue(waiting["action"].startswith("Waiting for ") and waiting["action"].endswith(" to consider cancellation"), waiting["action"])
		self.assertEqual((waiting["since"], waiting["title"]), (_dt("2027-06-16 14:00"), "Supply of field laptops"))
		# the Procurement Officer's own held items are never a wait
		self.assertFalse([row for row in self.region(fx.OFFICER, he.WAITING) if row["root"] == WORLD["t034"]["tender"].name])

	def test_the_cancellation_the_accounting_officer_sent_is_waiting_on_brian_with_the_obligation_due(self):
		waiting = self.one(fx.AO, he.WAITING, "t034")
		self.assertEqual(waiting["action"], "Waiting for cancellation compliance evidence from " + self.name(fx.OFFICER))
		self.assertEqual((waiting["holder"], waiting["since"], waiting["due"]), (self.name(fx.OFFICER), _dt("2027-06-15 12:00"), date(2027, 6, 18)))

	def test_only_items_the_owner_defines_a_waiting_for_are_waiting(self):
		# the returned Tender (048) was sent by Charles to Brian, but the register has no sender's wait for a correction
		self.assertFalse([row for row in self.region(fx.HOPF, he.WAITING) if row["root"] == WORLD["t048"]["tender"].name])

	def test_waiting_applies_to_anyone_with_a_tenders_responsibility_and_to_no_one_else(self):
		self.assertIsInstance(self.region(fx.OFFICER, he.WAITING), list)
		self.assertIsInstance(self.region(fx.AUDITOR, he.WAITING), list)
		self.assertEqual(self.mine(self.region(fx.AUDITOR, he.WAITING)), [])
		self.assertIsNone(self.region(fx.NOBODY, he.WAITING))

	# ----- Records you oversee -----

	def test_the_auditor_and_the_accounting_officer_see_who_the_returned_tender_waits_on(self):
		for user in (fx.AUDITOR, fx.AO):
			row = self.one(user, he.OVERSIGHT, "t048")
			self.assertEqual(row["action"], f"Returned for correction; awaiting correction by {self.name(fx.OFFICER)}")
			self.assertEqual((row["outstanding"], row["since"], row["title"], row["holder"]), (True, _dt("2027-06-16 09:00"), "Supply of IT peripherals", self.name(fx.OFFICER)))
			self.assertEqual((row["action_id"], row["destination"]["route"]), (self.task("t048", handoffs.CORRECT_RETURNED), ["tenders", self.reference("t048")]))

	def test_an_item_the_actor_holds_or_sent_is_not_overseen_and_the_overseer_is_told_who_has_the_rest(self):
		# Amina holds 039 and 047 (My work) and sent 034 (Waiting); Charles sent 047 and 048
		overseen = {row["root"] for row in self.region(fx.AO, he.OVERSIGHT)}
		for key in ("t039", "t047", "t034"):
			self.assertNotIn(WORLD[key]["tender"].name, overseen, key)
		self.assertIn(WORLD["t040"]["tender"].name, overseen)
		clarification = self.one(fx.AO, he.OVERSIGHT, "t040")
		self.assertTrue(clarification["action"].startswith("Waiting for ") and clarification["action"].endswith(" to respond to a clarification"), clarification["action"])
		self.assertTrue(all(row["outstanding"] and row["since"] for row in self.mine(self.region(fx.AO, he.OVERSIGHT))))
		# one row per Tender
		roots = [row["root"] for row in self.region(fx.AO, he.OVERSIGHT)]
		self.assertEqual(len(roots), len(set(roots)))
		self.assertEqual(self.one(fx.HOPF, he.OVERSIGHT, "t034")["action"], "Waiting for cancellation compliance evidence from " + self.name(fx.OFFICER))
		self.assertNotIn(WORLD["t048"]["tender"].name, {row["root"] for row in self.region(fx.HOPF, he.OVERSIGHT)})  # Charles sent it back himself

	def test_a_procurement_officer_oversees_nothing_and_neither_does_someone_with_no_responsibility(self):
		self.assertIsNone(self.region(fx.OFFICER, he.OVERSIGHT))
		self.assertIsNone(self.region(fx.NOBODY, he.OVERSIGHT))
		self.assertIsNone(self.region(fx.DEPARTMENTAL, he.OVERSIGHT))  # a Departmental Author is not a Head of User Department

	def test_a_head_of_user_department_sees_the_neutral_row_for_their_own_unit_only_and_no_holder(self):
		row = self.one(req_fx.HOD, he.OVERSIGHT, "t048")
		self.assertEqual((row["action"], row["holder"], row["outstanding"], row["since"]), ("Returned for correction", "", True, _dt("2027-06-16 09:00")))
		self.assertNotIn(self.name(fx.OFFICER), json.dumps(row, default=str))
		overseen = {entry["root"] for entry in self.region(req_fx.HOD, he.OVERSIGHT)}
		self.assertNotIn(WORLD["t049"]["tender"].name, overseen)  # another unit's Tender
		self.assertTrue(overseen.isdisjoint({WORLD[key]["tender"].name for key in ("t034", "t039", "t040", "t041", "t047")}))  # no unit, nothing disclosed
		self.assertEqual(self.one(req_fx.HOD_BETA, he.OVERSIGHT, "t049")["action"], "Awaiting procurement approval")
		self.assertNotIn(WORLD["t048"]["tender"].name, {entry["root"] for entry in self.region(req_fx.HOD_BETA, he.OVERSIGHT)})

	# ----- Coming up -----

	def test_tenders_contribute_nothing_to_coming_up_in_v1(self):
		for user in (fx.OFFICER, fx.HOPF, fx.AO, fx.AUDITOR, req_fx.HOD, fx.NOBODY):
			self.assertIsNone(self.region(user, he.COMING_UP), user)

	# ----- Recently completed actions -----

	def test_charles_approval_names_who_publication_awaits(self):
		row = self.one(fx.HOPF, he.COMPLETED, "t047")
		self.assertEqual((row["title"], row["action"], row["completed_at"], row["reference"]), ("Supply of UPS units", "Approved Tender package", _dt("2027-06-16 15:30"), self.reference("t047")))
		self.assertTrue(row["sentence"].startswith("You approved this Tender package on 16 June 2027, 15:30 "), row["sentence"])
		clause = row["sentence"].split(". ", 1)[1]
		self.holders(clause, "It is awaiting publication authorisation by ", ".", "Accounting Officer")
		self.assertEqual((row["action_id"], row["destination"]["route"]), (WORLD["t047"]["decisions"]["Approve Tender package"], ["tenders", self.reference("t047")]))

	def test_brians_submission_says_publication_authorisation_is_awaited_and_a_clarification_answer_adds_nothing(self):
		submitted = self.one(fx.OFFICER, he.COMPLETED, "t044")
		self.assertEqual(submitted["action"], "Submitted Tender for approval")
		self.assertTrue(submitted["sentence"].startswith("You submitted this Tender on 16 June 2027, 09:00 ") and "It is awaiting publication authorisation by " in submitted["sentence"], submitted["sentence"])
		# 042 is open: the owner's answer for Brian is his own optional turn, not a wait, so the sentence stops
		answered = self.one(fx.OFFICER, he.COMPLETED, "t042")
		self.assertEqual(answered["action"], "Responded to clarification")
		self.assertTrue(answered["sentence"].startswith("You responded to a clarification on this Tender on 17 June 2027, 11:00 ") and answered["sentence"].endswith("."), answered["sentence"])
		self.assertNotIn("awaiting", answered["sentence"])

	def test_only_the_actors_own_whitelisted_decisions_inside_thirty_days_for_a_tender_they_can_read(self):
		# the discarded addendum draft is not a completed action; Charles did not take Brian's
		brians = [row["action_id"] for row in self.region(fx.OFFICER, he.COMPLETED)]
		self.assertNotIn(WORLD["t042"]["decisions"]["Discard addendum draft"], brians)
		self.assertNotIn(WORLD["t047"]["decisions"]["Approve Tender package"], brians)
		self.assertNotIn(WORLD["t044"]["decisions"]["Submit for approval"], [row["action_id"] for row in self.region(fx.HOPF, he.COMPLETED)])
		# the provider's own cutoff is 30 days before the read
		old = _decision("t039", "Request cancellation review", actor=fx.OFFICER, role="Procurement Officer", at=home_time.now() - timedelta(days=45))
		recent = _decision("t039", "Request cancellation review", actor=fx.OFFICER, role="Procurement Officer", at=home_time.now() - timedelta(days=5))
		self.addCleanup(frappe.db.rollback)
		ids = [row["action_id"] for row in self.region(fx.OFFICER, he.COMPLETED)]
		self.assertIn(recent, ids)
		self.assertNotIn(old, ids)
		# an actor who can no longer read the Tender sees nothing of it: a Departmental Author whose unit did not contribute
		stray = _decision("t039", "Request cancellation review", actor=fx.DEPARTMENTAL, role="Procurement Officer", at=home_time.now())
		self.assertNotIn(stray, [row["action_id"] for row in self.region(fx.DEPARTMENTAL, he.COMPLETED)])
		self.assertIsInstance(self.region(fx.DEPARTMENTAL, he.COMPLETED), list)

	def test_the_core_window_drops_a_completed_action_older_than_thirty_days(self):
		old = _decision("t039", "Cancel Tender", actor=fx.AO, role="Accounting Officer", at=datetime(2027, 5, 1, 9, 0))
		self.addCleanup(frappe.db.rollback)
		keys = [row["key"].split("|")[-1] for row in self.all_rows(fx.AO, H12, "completed")]
		self.assertNotIn(old, keys)

	# ----- applicability, personas, technical readers -----

	def test_none_versus_empty_by_responsibility(self):
		for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
			self.assertIsNone(self.region(fx.NOBODY, region), region)
			self.assertIsInstance(self.region(fx.OFFICER, region), list)
		self.assertIsNone(self.region(fx.OFFICER, he.OVERSIGHT))
		self.assertIsInstance(self.region(fx.AUDITOR, he.OVERSIGHT), list)
		self.assertEqual(self.mine(self.region(fx.AUDITOR, he.MY_WORK)), [])  # the Auditor holds no item

	def test_the_technical_reader_and_an_unrelated_internal_user_get_nothing(self):
		for region in he.REGIONS:
			self.assertIsNone(self.region("Administrator", region), region)
			self.assertIsNone(self.region(fx.NOBODY, region), region)
		view = self.home("Administrator", H12)
		self.assertEqual((view["empty"], view["regions"]["my_work"]["entries"]), (True, []))
		nobody = self.home(fx.NOBODY, H12)
		self.assertEqual(nobody["state"], "ready")
		self.assertFalse(any(region["entries"] for region in nobody["regions"].values()))
		self.assertEqual({region["coverage"] for region in nobody["regions"].values()}, {hw.NOT_APPLICABLE})

	def test_a_user_without_the_responsibility_sees_none_of_it_and_a_revoked_responsibility_removes_it(self):
		root = WORLD["t049"]["tender"].name
		administration.grant(user=EXTRA, business_role="Head of Procurement Function", fixture_namespace=EXTRA_NS, actor="Administrator")
		self.assertEqual(self.row(EXTRA, H12, "my_work", "t049")["action"], "Review Tender")
		self.assertEqual(self.home(EXTRA, H12)["regions"]["my_work"]["applicable"], True)
		assignment = frappe.get_all("User Responsibility Assignment", filters={"user": EXTRA}, pluck="name")[0]
		administration.revoke(assignment, reason="Revoked inside the Home provider test.", actor="Administrator")
		revoked = self.home(EXTRA, H12)
		self.assertEqual({region["coverage"] for region in revoked["regions"].values()}, {hw.NOT_APPLICABLE})
		self.assertFalse([row for region in revoked["regions"].values() for row in region["entries"] if row["reference"] == self.reference("t049")])
		self.assertIsNone(self.region(EXTRA, he.MY_WORK))
		self.assertEqual(root, WORLD["t049"]["tender"].name)

	def test_the_provider_writes_nothing(self):
		frappe.db.commit()
		before = frappe.db.transaction_writes
		for user in (fx.OFFICER, fx.HOPF, fx.AO, fx.AUDITOR, req_fx.HOD, fx.DEPARTMENTAL, fx.NOBODY, "Administrator"):
			for region in he.REGIONS:
				self.region(user, region)
		frappe.flags.kt_tenders_clock = LATE
		for region in he.REGIONS:  # the blocked authorisation and the derived rows read through guidance and the period check
			self.region(fx.AO, region)
			self.region(fx.HOPF, region)
		self.assertEqual(frappe.db.transaction_writes, before)

	def test_the_scan_runs_once_per_home_read(self):
		calls = []
		original = my_work_provider.my_work_rows

		def counting(**kwargs):
			calls.append(kwargs["user"])
			return original(**kwargs)

		my_work_provider.my_work_rows = counting
		self.addCleanup(setattr, my_work_provider, "my_work_rows", original)
		self.home(fx.AO, H12)
		self.assertEqual(calls, [fx.AO])

	# ----- destinations, tables -----

	def test_every_destination_opens_a_real_page_the_actor_may_open(self):
		for page in SPEC_PAGES:
			self.assertTrue(frappe.db.exists("Page", page), page)
		seen = set()
		for user in (fx.OFFICER, fx.HOPF, fx.AO, fx.AUDITOR, req_fx.HOD, fx.DEPARTMENTAL):
			for region in (he.MY_WORK, he.WAITING, he.OVERSIGHT, he.COMPLETED):
				for row in self.mine(self.region(user, region)):
					seen.add(row["destination"]["route"][0])
					self.assertIn(row["destination"]["route"][0], SPEC_PAGES)
					self.assertTrue(hw._page_permitted(row["destination"]["route"][0], user), (user, row["destination"]))
		self.assertEqual(seen, {"tenders", "procurement-requisitions"})

	def test_the_owners_tables_cover_every_register_row(self):
		self.assertEqual(set(handoffs.HOME_TEXT), set(handoffs.REGISTER))
		for task_type in handoffs.REGISTER:
			task = frappe._dict(task_type=task_type, business_role=handoffs.REGISTER[task_type][0], holder="", subject_type="", subject_id="", tender_version=None)
			root = frappe._dict(name="TDR-X", tender_reference="TND-X-1")
			action = handoffs.home_action_for(root, task)
			line = handoffs.home_line_for(root, task, "Someone")
			self.assertTrue(action and "{" not in action and "TND-X-1" not in action, (task_type, action))
			self.assertTrue(line and "{" not in line and "Someone" in line, (task_type, line))
		spec = {handoffs.AO_AUTHORISATION: "Authorise publication", handoffs.CANCELLATION_REVIEW: "Consider cancellation", handoffs.CANCELLATION_COMPLIANCE: "Record cancellation notices and PPRA report", handoffs.CLARIFICATION_RESPONSE: "Respond to clarification"}
		for task_type, wording in spec.items():
			self.assertEqual(handoffs.HOME_TEXT[task_type][0], wording)

	# ----- through the Home read -----

	def test_brians_home_renders_the_spec_timing_and_due_strings(self):
		compliance = self.row(fx.OFFICER, H1, "my_work", "t034")
		self.assertEqual((compliance["action"], compliance["due"], compliance["timing"]), ("Record cancellation notices and PPRA report", "Due tomorrow (18 June)", "Received 2 days ago (15 June, 12:00)"))
		self.assertEqual(compliance["module"], "Tenders")
		self.assertEqual(self.row(fx.OFFICER, H1, "waiting", "t039")["timing"], "Waiting 1 day (since 16 June, 14:00)")
		self.assertEqual(self.row(fx.OFFICER, H1, "my_work", "t040")["timing"], "Received yesterday (16 June, 10:00)")
		# the row with a recorded deadline leads this world's other work
		mine = {self.reference(key) for key in WORLD}
		order = [row["reference"] for row in self.all_rows(fx.OFFICER, H1, "my_work") if row["reference"] in mine]
		self.assertEqual(order[0], self.reference("t034"))

	def test_brians_blocked_clarification_renders_the_reason(self):
		blocked = self.row(fx.OFFICER, H1, "my_work", "t041")
		self.assertEqual((blocked["blocked"], blocked["reason"], blocked["action"]), (True, "Issue an addendum before sending this answer.", "Respond to clarification"))

	def test_aminas_home_renders_her_decisions_and_what_she_waits_for(self):
		consider, authorise = self.row(fx.AO, H12, "my_work", "t039"), self.row(fx.AO, H12, "my_work", "t047")
		self.assertEqual((consider["timing"], consider["action"]), ("Received 2 days ago (16 June, 14:00)", "Consider cancellation"))
		self.assertEqual((authorise["timing"], authorise["action"]), ("Received 2 days ago (16 June, 15:30)", "Authorise publication"))
		waiting = self.row(fx.AO, H12, "waiting", "t034")
		self.assertEqual((waiting["timing"], waiting["due"], waiting["holder"]), ("Waiting 3 days (since 15 June, 12:00)", "Due today (18 June)", self.name(fx.OFFICER)))
		self.assertEqual(waiting["action"], "Waiting for cancellation compliance evidence from " + self.name(fx.OFFICER))
		self.assertEqual(self.row(fx.AO, H12, "oversight", "t048")["timing"], "Outstanding 2 days (since 16 June, 09:00)")
		# the same item held and overseen is shown once, in My work
		overseen = {row["reference"] for row in self.all_rows(fx.AO, H12, "oversight")}
		self.assertTrue({self.reference("t039"), self.reference("t047")}.isdisjoint(overseen))

	def test_charles_home_shows_the_publication_wait_and_the_approval_he_gave(self):
		waiting = self.row(fx.HOPF, H12, "waiting", "t047")
		self.assertEqual(waiting["timing"], "Waiting 2 days (since 16 June, 15:30)")
		self.assertTrue(waiting["action"].endswith(" to decide publication"))
		done = self.row(fx.HOPF, H12, "completed", "t047")
		self.assertTrue(done["sentence"].startswith("You approved this Tender package on 16 June 2027, 15:30 "))
		self.assertTrue(done["sentence"].endswith("."))

	def test_a_head_of_departments_home_shows_the_neutral_wording_and_timing(self):
		row = self.row(req_fx.HOD, H12, "oversight", "t048")
		self.assertEqual((row["action"], row["timing"], row["holder"]), ("Returned for correction", "Outstanding 2 days (since 16 June, 09:00)", ""))
