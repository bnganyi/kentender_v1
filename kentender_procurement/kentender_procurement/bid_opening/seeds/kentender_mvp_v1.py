# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical `bid_opening` seed stage (BOP-CHG-001 v0.10 plan D14,
Phase 10): the canonical Tender's opening, told the way the boards tell it
(§10 main-path fixture, BOP-S01).

  10 Jun 2027 10:15  Amina Hassan appoints Charles Mutiso (chair and recorder),
                     Brian Wafula and Beatrice Kamau (independent member)
              10:20  and publishes how to attend
  12 Jun 2027 10:55–10:57  the three members join; 10:58 David Ouma joins
                     for Afya Digital Supplies Limited; 10:59 Jane Wanjiku
                     joins as a public observer
              11:00:12  Charles starts the opening; 11:01 the bid is opened
              11:01:45  what Brian read aloud at 11:01:30 is recorded
              11:02:20  David's 11:02:00 request to repeat the total, answered
              11:04  the opening ends; 11:07 the record is finished
              11:08–11:10:30  Brian, Beatrice and Charles sign; the last
                     signature completes the opening and hands the bid to
                     Evaluation

Every step is the real command as its actor, with Bid Opening's and
Proceedings' clocks at the step's instant. It runs after the `bid_submission`
stage, whose close at 11:00 left the sealed box for Bid Opening. The
signatures are the test attestation service's, so the stage runs only on a
test site. Daniel Otieno (KT-STD-001 v1.11 §8.3, seeded by the site stage) is
the Opening access support holder; the canonical opening needs no support."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, get_datetime

NAMESPACE = "KENTENDER_MVP_1_R1_BOP"
DOMAIN = "moh.example.test"
AO = f"amina.hassan@{DOMAIN}"
CHAIR = f"charles.mutiso@{DOMAIN}"
MEMBER = f"brian.wafula@{DOMAIN}"
INDEPENDENT = f"beatrice.kamau@{DOMAIN}"
OBSERVER = "jane.wanjiku@observer.example"  # KT-STD-001 v1.11 §8.3 public observer
SUPPORT = f"daniel.otieno@{DOMAIN}"  # KT-STD-001 v1.11 §8.3 technical operator
ROSTER = ({"user": CHAIR, "committee_role": "Chair and recorder"}, {"user": MEMBER, "committee_role": "Member"},
	{"user": INDEPENDENT, "committee_role": "Independent member"})
CLOCK = {
	"prepare": "2027-06-10 10:10:00", "appoint": "2027-06-10 10:15:00", "publish": "2027-06-10 10:20:00",
	"join_chair": "2027-06-12 10:55:10", "join_member": "2027-06-12 10:56:00", "join_independent": "2027-06-12 10:57:00", "join_david": "2027-06-12 10:58:00", "join_jane": "2027-06-12 10:59:00",
	"receive": "2027-06-12 11:00:05", "begin": "2027-06-12 11:00:12", "open": "2027-06-12 11:01:00", "spoken": "2027-06-12 11:01:30",
	"readout": "2027-06-12 11:01:45", "asked": "2027-06-12 11:02:00", "answered": "2027-06-12 11:02:20", "end": "2027-06-12 11:04:00",
	"freeze": "2027-06-12 11:07:00", "sign_member": "2027-06-12 11:08:00", "sign_independent": "2027-06-12 11:09:00", "sign_chair": "2027-06-12 11:10:30",
}
ARRANGEMENTS = {"attendance_method": "Attend the public bid opening online",
	"access_instructions": "Select Join public opening on this Tender’s page from 10:55 EAT on 12 Jun 2027. You can listen, ask for a figure to be repeated, "
		"or make a procedural comment."}
REQUEST = {"exception_class": "Repeat request", "speaker_name": "David Ouma", "what": "Asked for the submitted total to be repeated",
	"response": "Charles Mutiso asked Brian Wafula to repeat it. Brian Wafula repeated KES 46,400,000.00 at 11:02:15."}


def _key(step: str) -> str:
	return f"bop-seed:{step}:{uuid4().hex[:8]}"


class _Clock:
	"""Bid Opening's and Proceedings' clocks, walked forward with the present
	members' pages beating every 30 s (the lapse is 60 s; plan D7)."""

	def __init__(self, tender: str):
		self.tender = tender
		self.present: list[str] = []
		self.now = None

	def at(self, instant: str) -> None:
		from kentender_procurement.bid_opening.services import presence

		target = get_datetime(instant)
		steps = []
		if self.present and self.now is not None:
			tick = self.now + timedelta(seconds=30)
			while tick < target:
				steps.append(tick)
				tick += timedelta(seconds=30)
		for moment in [*steps, target]:
			frappe.flags.kt_bop_clock = frappe.flags.kt_prc_clock = str(moment)
			for user in self.present:
				presence.heartbeat(tender=self.tender, user=user)
		self.now = target


def _ok(result: dict[str, Any], step: str) -> dict[str, Any]:
	if not result or result.get("ok") is False:
		frappe.throw(f"The canonical bid opening could not {step}: {result}")
	return result


def _guard() -> None:
	from kentender_procurement.bid_opening.services import simulation

	if not simulation.enabled():
		frappe.throw("The canonical bid opening signs with the test attestation service, which exists only on a test site "
			"(site_config kt_bds_simulation_environment = 1).")


def canonical_tender() -> str:
	from kentender_procurement.tenders.seeds import kentender_mvp_v1 as tenders_seed

	requisition = tenders_seed.verify_prerequisites()["requisition"]
	return cstr(frappe.db.get_value("Tender", {"requisition": requisition}, "name"))


def _version(tender: str) -> int:
	return int(frappe.db.get_value("Bid Opening Case", {"tender": tender}, "record_version"))


def _build(tender: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import (
		appointment, arrangements, case, ceremony, close_intake, finish, interventions, presence, public, readout, record, signing,
	)
	from kentender_procurement.bid_submission.seeds import canonical as bds_canonical

	clock = _Clock(tender)
	clock.at(CLOCK["prepare"])
	case.prepare_opening_case(tender=tender)
	clock.at(CLOCK["appoint"])
	_ok(appointment.appoint_opening_committee(tender=tender, members=[dict(r) for r in ROSTER], expected_version=_version(tender), idempotency_key=_key("appoint"),
		user=AO), "appoint the committee")
	clock.at(CLOCK["publish"])
	_ok(arrangements.publish_opening_arrangements(tender=tender, expected_version=_version(tender), idempotency_key=_key("publish"), user=AO, **ARRANGEMENTS),
		"publish how to attend")
	for user, instant in ((CHAIR, "join_chair"), (MEMBER, "join_member"), (INDEPENDENT, "join_independent")):
		clock.at(CLOCK[instant])
		_ok(presence.join_opening(tender=tender, idempotency_key=_key(f"join-{user}"), user=user), f"join as {user}")
		clock.present.append(user)
	clock.at(CLOCK["join_david"])
	_ok(public.join_public_opening(tender=tender, idempotency_key=_key("join-david"), user=bds_canonical.DAVID), "join as David Ouma")
	clock.at(CLOCK["join_jane"])
	_ok(public.join_public_opening(tender=tender, idempotency_key=_key("join-jane"), user=OBSERVER), "join as Jane Wanjiku")
	clock.at(CLOCK["receive"])
	close_intake.receive_closed_box(tender=tender)
	clock.at(CLOCK["begin"])
	_ok(ceremony.begin_opening(tender=tender, expected_version=_version(tender), idempotency_key=_key("begin"), user=CHAIR), "start the opening")
	clock.at(CLOCK["open"])
	entry = _ok(ceremony.open_next_tender(tender=tender, expected_version=_version(tender), idempotency_key=_key("open"), user=CHAIR), "open the bid")["entry"]
	clock.at(CLOCK["readout"])
	_ok(readout.record_readout(tender=tender, entry=entry, speaker=MEMBER, designated_pages=[1], expected_version=_version(tender), idempotency_key=_key("readout"),
		user=CHAIR, reported_speech_at=CLOCK["spoken"]), "record what was read aloud")
	clock.at(CLOCK["answered"])
	_ok(interventions.record_intervention(tender=tender, idempotency_key=_key("request"), user=CHAIR, entry=entry, reported_at=CLOCK["asked"], **REQUEST),
		"record the request")
	clock.at(CLOCK["end"])
	_ok(finish.finish_ceremony(tender=tender, expected_version=_version(tender), idempotency_key=_key("end"), user=CHAIR), "end the opening")
	clock.present = []
	clock.at(CLOCK["freeze"])
	_ok(record.freeze_opening_minutes(tender=tender, expected_version=_version(tender), idempotency_key=_key("freeze"), user=CHAIR), "finish the record")
	doc = frappe.get_doc("Bid Opening Case", {"tender": tender})
	for user, instant in ((MEMBER, "sign_member"), (INDEPENDENT, "sign_independent"), (CHAIR, "sign_chair")):
		clock.at(CLOCK[instant])
		version, mine = signing.my_targets(doc, user)
		_ok(signing.sign_opening_record(tender=tender, minutes_version=version, targets=[{"target_id": t["target_id"], "target_digest": t["target_digest"]}
			for t in mine], idempotency_key=_key(f"sign-{user}"), user=user), f"sign as {user}")
	return {"entry": entry}


def lifecycle_complete(tender: str) -> bool:
	"""Complete and carrying every canonical fact (an opening told before a
	fact was added, such as Jane Wanjiku's attendance, is told again)."""
	case = frappe.db.get_value("Bid Opening Case", {"tender": tender}, "state")
	return case == "Opening complete" and all(row["ok"] for row in validate_bid_opening_seed())


def upsert_bid_opening_base(*, commit: bool = False) -> dict[str, Any]:
	"""The `bid_opening` stage. A completed canonical opening is returned
	untouched; a partial one (an interrupted earlier seed, or a browser pass)
	is removed and told again from the start."""
	from kentender_procurement.bid_opening.seeds import clear

	_guard()
	tender = canonical_tender()
	if not tender or not frappe.db.exists("Bid Submission Close", {"tender": tender}):
		frappe.throw("The canonical Tender has not been closed by Bid Submission. Seed through the bid_submission stage first.")
	if lifecycle_complete(tender):
		result = {"ok": True, "idempotent": True, "tender": tender, "opening": frappe.db.get_value("Bid Opening Case", {"tender": tender}, "name")}
	else:
		clear.wipe(tenders=[tender], namespace=NAMESPACE)  # its command journal too, or a retold Prepare replays the old answer
		saved = {flag: frappe.flags.get(flag) for flag in ("kt_bop_clock", "kt_prc_clock", "kt_bop_fixture_namespace", "kt_prc_fixture_namespace")}
		frappe.flags.kt_bop_fixture_namespace = frappe.flags.kt_prc_fixture_namespace = NAMESPACE
		try:
			built = _build(tender)
		finally:
			for flag, value in saved.items():
				frappe.flags[flag] = value
		result = {"ok": True, "idempotent": False, "tender": tender, "opening": frappe.db.get_value("Bid Opening Case", {"tender": tender}, "name"), **built}
	if commit:
		frappe.db.commit()
	return result


def validate_bid_opening_seed() -> list[dict[str, Any]]:
	"""One row per BOP-S01 fact the canonical opening must carry. Never mutates."""
	from kentender_procurement.bid_opening.services import appointment, finish
	from kentender_procurement.bid_submission.seeds import canonical as bds_canonical

	rows: list[dict[str, Any]] = []

	def check(ok: bool, label: str) -> None:
		rows.append({"ok": bool(ok), "check": label})

	tender = canonical_tender()
	doc = frappe.db.get_value("Bid Opening Case", {"tender": tender}, ["name", "state", "started_at", "ended_at", "completed_at", "evaluation_handoff", "proceeding",
		"outcome"], as_dict=True) if tender else None
	check(bool(doc), "the canonical Tender has its bid opening")
	if not doc:
		return rows
	check(doc.state == "Opening complete", f"the opening is complete (got {doc.state!r})")
	roster = {m["member_user"]: m["committee_role"] for m in appointment.roster(doc.name)}
	check(roster == {r["user"]: r["committee_role"] for r in ROSTER}, "Charles Mutiso (chair and recorder), Brian Wafula and Beatrice Kamau (independent member) were appointed")
	check(appointment.is_excluded_from_evaluation(tender, INDEPENDENT), "Beatrice Kamau cannot later be appointed to evaluate this Tender")
	appointed = frappe.db.get_value("Opening Committee Appointment", {"opening_case": doc.name, "status": "Active"}, ["appointed_at", "appointed_by"], as_dict=True)
	check(bool(appointed) and cstr(appointed.appointed_at) == CLOCK["appoint"] and appointed.appointed_by == AO, "Amina Hassan appointed the committee at 10 Jun 2027, 10:15 EAT")
	published = frappe.db.get_value("Opening Arrangement", {"opening_case": doc.name, "status": "Published"}, "published_at")
	check(cstr(published) == CLOCK["publish"], "how to attend was published at 10 Jun 2027, 10:20 EAT")
	check(cstr(doc.started_at) == CLOCK["begin"], "the opening started at 12 Jun 2027, 11:00:12 EAT")
	register = finish.register_rows(doc.name)
	check(len(register) == 1 and cstr(register[0]["recorded_at"]) == CLOCK["readout"], "one bid was read aloud and recorded at 11:01:45 EAT")
	check(len(register) == 1 and register[0]["submitted_total"] == "KES 46,400,000.00", "the register shows KES 46,400,000.00")
	check(frappe.db.count("Opening Exception", {"opening_case": doc.name, "exception_class": "Repeat request", "outcome": "Answered during opening"}) == 1,
		"David Ouma's request to repeat the total was answered during the opening")
	david = frappe.db.get_value("Proceeding Attendance", {"proceeding": doc.proceeding, "user": bds_canonical.DAVID, "movement": "Arrival"},
		["capacity", "represented_tenderer"], as_dict=True)
	check(bool(david) and david.capacity == "Tenderer representative" and david.represented_tenderer == "Afya Digital Supplies Limited",
		"David Ouma joined for Afya Digital Supplies Limited")
	jane = frappe.db.get_value("Proceeding Attendance", {"proceeding": doc.proceeding, "user": OBSERVER, "movement": "Arrival"}, ["capacity", "occurred_at"], as_dict=True)
	check(bool(jane) and jane.capacity == "Public observer" and cstr(jane.occurred_at) == CLOCK["join_jane"], "Jane Wanjiku joined as a public observer at 10:59 EAT")
	check(SUPPORT in frappe.get_all("User Responsibility Assignment", filters={"business_role": "Technical Operator", "status": "Enabled"}, pluck="user"),
		"Daniel Otieno holds Opening access support (Technical Operator)")
	check(cstr(doc.ended_at) == CLOCK["end"], "the opening ended at 11:04 EAT")
	check(frappe.db.get_value("Proceeding Minutes Version", {"proceeding": doc.proceeding, "version_number": 1}, "state") == "Finalized", "opening record version 1 is final")
	check(cstr(doc.completed_at) == CLOCK["sign_chair"], "the last signature completed the opening at 11:10:30 EAT")
	check(bool(doc.evaluation_handoff) and frappe.db.get_value("Evaluation Handoff", doc.evaluation_handoff, "delivery_status") == "Pending",
		"the opened bid was handed to Evaluation, waiting for its uptake")
	return rows
