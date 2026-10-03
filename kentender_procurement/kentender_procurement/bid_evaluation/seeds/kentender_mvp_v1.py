# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical `bid_evaluation` seed stage (EVL-CHG-001 v0.4 plan D18,
Phase 13): the canonical Tender's evaluation, told the way §11.1 tells it.

  11 Jun 2027 08:58  the evaluation is prepared from the published Tender
              09:00  Amina Hassan appoints Grace Wambui (chair), Peter Mugo
                     and Ruth Achieng; 09:05 Charles Mutiso assigns Brian
                     Wafula as secretary; 09:10–09:14 each member declares
  12 Jun 2027 11:10:33  the completed opening (four bids) is taken up and
                     checked: Pwani Tech Distributors Limited's 8 GB offer
                     fails the 16 GB memory requirement automatically
  14 Jun 2027 08:10–08:35  Ruth and Peter review the other bids' evidence:
                     Jirani's meets; Mlima's eligibility documents do not
                     (an expired tax compliance certificate), so Mlima is
                     not responsive either
              08:45–08:50  Ruth and Peter review Afya's evidence; Peter leaves
                     the service location as Needs review
              09:00–09:06  Grace starts the discussion, the members and Brian
                     join, Brian notes, Grace authorises the clarification
              09:10  Brian sends it
  15 Jun 2027 10:00  David Ouma replies for Afya Digital Supplies Limited
  16 Jun 2027 09:00–09:06  the committee records the reply outcome and its
                     no-additional-due-diligence basis
              13:55–14:00  Brian writes the summary and sends the report
              14:05–14:07  Grace, Peter and Ruth sign; the last signature
                     delivers the report to Charles Mutiso

Every step is the real command as its actor, with every clock at the
step's instant. It runs after the `bid_opening` stage. The signatures are the
test attestation service's, so the stage runs only on a test site."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr

NAMESPACE = "KENTENDER_MVP_1_R1_EVL"
DOMAIN = "moh.example.test"
AO = f"amina.hassan@{DOMAIN}"
HOP = f"charles.mutiso@{DOMAIN}"
SECRETARY = f"brian.wafula@{DOMAIN}"
CHAIR = f"grace.wambui@{DOMAIN}"
MEMBER = f"peter.mugo@{DOMAIN}"
MEMBER_2 = f"ruth.achieng@{DOMAIN}"
ROSTER = [
	{"user": CHAIR, "department": "Human Resource Management and Development", "capacity": "Chair"},
	{"user": MEMBER, "department": "ICT", "capacity": "Member"},
	{"user": MEMBER_2, "department": "Finance", "capacity": "Member"},
]
CLOCK = {
	"prepare": "2027-06-11 08:58:00", "appoint": "2027-06-11 09:00:00", "secretary": "2027-06-11 09:05:00",
	"declare": ("2027-06-11 09:10:00", "2027-06-11 09:12:00", "2027-06-11 09:14:00"), "intake": "2027-06-12 11:10:33",
	"eligibility": "2027-06-14 08:45:00", "technical": "2027-06-14 08:50:00", "start": "2027-06-14 09:00:00", "join": ("2027-06-14 09:02:00", "2027-06-14 09:03:00"),
	"note": "2027-06-14 09:04:00", "authorise": "2027-06-14 09:05:00", "end": "2027-06-14 09:06:00", "send": "2027-06-14 09:10:00",
	"deadline": "2027-06-15 17:00:00", "reply": "2027-06-15 10:00:00", "restart": "2027-06-16 09:00:00", "rejoin": ("2027-06-16 09:02:00", "2027-06-16 09:03:00"),
	"dispose": "2027-06-16 09:05:00", "basis": "2027-06-16 09:05:30", "end2": "2027-06-16 09:06:00", "narrative": "2027-06-16 13:55:00",
	"freeze": "2027-06-16 14:00:00", "sign": ("2027-06-16 14:05:00", "2027-06-16 14:06:00", "2027-06-16 14:07:00"),
}
Q1 = "Please identify the page and section of your submitted Kenya service-centre details that gives the Nairobi service address."
SCOPE = "Explain the submitted evidence. Do not change your offer or add a new service arrangement."
REPLY = "The service address is on page 2, section 3 of Kenya service-centre details: Westlands Business Park, Waiyaki Way, Nairobi."
NOTE = "Ask the bidder to identify the service address already recorded in its submitted evidence."
REASON = "The offered location meets the stated country requirement, but the supporting document is unclear."
OUTCOME = "The address is present in the original submitted document and is within Kenya."
BASIS = "No additional exercise undertaken; no separate exercise required by the published tender and no outstanding verification concern recorded by the committee."
SUMMARY = ("Four bids were received. Afya Digital Supplies Limited's is the lowest evaluated responsive bid; Jirani Office Supplies Limited's is also responsive "
	"and ranked second. Pwani Tech Distributors Limited's bid offers 8 GB of memory against the required 16 GB, and Mlima Computer Solutions Limited's eligibility "
	"documents include an expired tax compliance certificate, so neither is responsive. Afya's submitted service-location evidence was clarified without changing the offer.")
AFYA = "Afya Digital Supplies Limited"
#: The other bids' evidence reviews: (tenderer, eligibility instant by Ruth Achieng, technical instant by Peter Mugo, the requirement mapping that
#: fails with its reason, or None). Every other row awaiting review meets.
REVIEWS = (
	("Jirani Office Supplies Limited", "2027-06-14 08:10:00", "2027-06-14 08:15:00", None),
	("Pwani Tech Distributors Limited", "2027-06-14 08:20:00", "2027-06-14 08:25:00", None),
	("Mlima Computer Solutions Limited", "2027-06-14 08:30:00", "2027-06-14 08:35:00",
		("DM-EVIDENCE-ELIGIBILITY-DOCUMENTS", "The tax compliance certificate in the eligibility documents expired on 30 April 2027, before the submission deadline.")),
)
#: The ranking the comparison must show: (tenderer, position, evaluated total).
RANKING = (
	(AFYA, 1, "46400000.00"), ("Jirani Office Supplies Limited", 2, "48720000.00"),
	("Pwani Tech Distributors Limited", "Not ranked", "Not assessed — mandatory requirement not met"),
	("Mlima Computer Solutions Limited", "Not ranked", "Not assessed — mandatory requirement not met"),
)
ELIGIBILITY = "EVG-ELIGIBILITY"
CLOCKS = ("kt_evl_clock", "kt_bop_clock", "kt_prc_clock", "kt_bds_clock", "kt_tenders_clock")


def _key(step: str) -> str:
	return f"evl-seed:{step}:{uuid4().hex[:8]}"


def _ok(result: dict[str, Any], step: str) -> dict[str, Any]:
	if not result or result.get("ok") is False:
		frappe.throw(f"The canonical bid evaluation could not {step}: {result}")
	return result


def _at(instant: str) -> None:
	for flag in CLOCKS:
		frappe.flags[flag] = instant


def _guard() -> None:
	from kentender_procurement.bid_evaluation.services import simulation

	if not simulation.enabled():
		frappe.throw("The canonical bid evaluation signs with the test attestation service, which exists only on a test site "
			"(site_config kt_bds_simulation_environment = 1).")


def canonical_tender() -> str:
	from kentender_procurement.bid_opening.seeds.kentender_mvp_v1 import canonical_tender as opening_tender

	return opening_tender()


class _Story:
	def __init__(self, tender: str):
		self.tender = tender

	def case(self) -> str:
		return cstr(frappe.db.get_value("Evaluation Case", {"tender": self.tender}, "name"))

	def version(self) -> int:
		return int(frappe.db.get_value("Evaluation Case", self.case(), "record_version"))

	def bid(self, tenderer: str = AFYA) -> str:
		return cstr(frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case(), "tenderer_name": tenderer}, "name"))

	def review(self, tenderer: str, eligibility_at: str, technical_at: str, failing: tuple[str, str] | None) -> None:
		"""Ruth reviews a bid's eligibility evidence and Peter its technical
		evidence: every row awaiting review meets, except `failing`."""
		from kentender_procurement.bid_evaluation.services import aggregate, checks, findings

		case, bid = self.case(), self.bid(tenderer)
		failed = False
		for r in sorted(aggregate.bid_results(case, checks.current_run(case), bid)["requirements"], key=lambda r: r["group_id"] != ELIGIBILITY):
			if r["result"] != "Needs review":
				continue
			eligibility = r["group_id"] == ELIGIBILITY
			fails = bool(failing) and r["mapping_id"] == failing[0] and not failed
			failed = failed or fails
			service = r["label"] == "Service location"
			_at(eligibility_at if eligibility else technical_at)
			_ok(findings.record_evidence_finding(tender=self.tender, bid=bid, requirement_key=r["requirement_key"], result="Does not meet" if fails else "Meets",
				reason=failing[1] if fails else ("The submitted evidence identifies a service address in Kenya." if service else "Required evidence reviewed."),
				evidence_reference="Kenya service-centre details" if service else "Submitted evidence", idempotency_key=_key("finding"),
				user=MEMBER_2 if eligibility else MEMBER), f"review {tenderer}'s {r['label']}")
		if failing and not failed:
			frappe.throw(f"{tenderer}'s bid had no {failing[0]} row awaiting review to record as not met.")

	def request(self) -> str:
		return cstr(frappe.db.get_value("Evaluation Clarification", {"evaluation_case": self.case()}, "name", order_by="creation desc"))

	def session(self, instant: str, joins: tuple[str, str], subject: str) -> None:
		from kentender_procurement.bid_evaluation.services import discussion

		_at(instant)
		_ok(discussion.start_discussion(tender=self.tender, subject=subject, idempotency_key=_key("start"), user=CHAIR), "start the discussion")
		_ok(discussion.join_discussion(tender=self.tender, idempotency_key=_key("join-secretary"), user=SECRETARY), "join as the secretary")
		for user, at in zip((MEMBER, MEMBER_2), joins):
			_at(at)
			_ok(discussion.join_discussion(tender=self.tender, idempotency_key=_key(f"join-{user}"), user=user), f"join as {user}")

	def run(self) -> None:
		from kentender_procurement.bid_evaluation.services import (
			aggregate, appointment, checks, clarification, conclusion, declaration, discussion, findings, intake, preparation, report, secretary, signing,
		)
		from kentender_procurement.bid_submission.seeds import canonical as bds_canonical

		_at(CLOCK["prepare"])
		_ok(preparation.ensure_preparation(tender=self.tender), "prepare")
		_at(CLOCK["appoint"])
		_ok(appointment.appoint_committee(tender=self.tender, members=ROSTER, appointment_reference="MOH/EVAL/002/2027", expected_version=self.version(),
			idempotency_key=_key("appoint"), user=AO), "appoint the committee")
		_at(CLOCK["secretary"])
		_ok(secretary.assign_secretary(tender=self.tender, secretary=SECRETARY, appointment_reference="MOH/EVAL/SEC/002/2027", expected_version=self.version(),
			idempotency_key=_key("secretary"), user=HOP), "assign the secretary")
		for user, at in zip((CHAIR, MEMBER, MEMBER_2), CLOCK["declare"]):
			_at(at)
			_ok(declaration.declare_interest(tender=self.tender, choice="No conflict to declare", confidentiality_accepted=True, idempotency_key=_key(f"declare-{user}"),
				user=user), f"declare as {user}")
		_at(CLOCK["intake"])
		_ok(intake.receive_opening_package(tender=self.tender), "take up the completed opening")
		for tenderer, eligibility_at, technical_at, failing in REVIEWS:
			self.review(tenderer, eligibility_at, technical_at, failing)
		# 14 Jun: Ruth reviews the eligibility evidence, Peter the technical; the service location stays with the committee
		case = self.case()
		for r in aggregate.bid_results(case, checks.current_run(case), self.bid())["requirements"]:
			if r["result"] != "Needs review":
				continue
			service = r["label"] == "Service location"
			eligibility = r["group_id"] == ELIGIBILITY
			_at(CLOCK["eligibility"] if eligibility else CLOCK["technical"])
			_ok(findings.record_evidence_finding(tender=self.tender, bid=self.bid(), requirement_key=r["requirement_key"], result="Needs review" if service else "Meets",
				reason="The submitted evidence does not clearly identify the service address." if service else "Required evidence reviewed.",
				evidence_reference="Kenya service-centre details" if service else "Submitted evidence", idempotency_key=_key(f"finding-{r['requirement_key']}"),
				user=MEMBER_2 if eligibility else MEMBER), f"review {r['label']}")
		self.session(CLOCK["start"], CLOCK["join"], "Afya service-location evidence")
		_at(CLOCK["note"])
		_ok(discussion.record_note(tender=self.tender, subject="Afya service-location evidence", note=NOTE, reason=REASON, idempotency_key=_key("note"), user=SECRETARY),
			"record the note")
		_at(CLOCK["authorise"])
		service_key = next(r["requirement_key"] for r in aggregate.bid_results(case, checks.current_run(case), self.bid())["requirements"]
			if r["label"] == "Service location")
		_ok(clarification.authorise(tender=self.tender, bid=self.bid(), requirement_key=service_key, question=Q1, reply_scope=SCOPE, reply_deadline=CLOCK["deadline"],
			idempotency_key=_key("authorise"), user=CHAIR), "authorise the clarification")
		_at(CLOCK["end"])
		_ok(discussion.end_discussion(tender=self.tender, idempotency_key=_key("end"), user=CHAIR), "end the discussion")
		_at(CLOCK["send"])
		_ok(clarification.send(tender=self.tender, clarification=self.request(), idempotency_key=_key("send"), user=SECRETARY), "send the clarification")
		_at(CLOCK["reply"])
		_ok(clarification.submit_reply(tender=self.tender, clarification=self.request(), body=REPLY, idempotency_key=_key("reply"), user=bds_canonical.DAVID),
			"reply as David Ouma")
		self.session(CLOCK["restart"], CLOCK["rejoin"], "Resolve reply and complete findings")
		_at(CLOCK["dispose"])
		_ok(clarification.record_disposition(tender=self.tender, clarification=self.request(), disposition="Considered", result="Meets", reason=OUTCOME,
			idempotency_key=_key("dispose"), user=CHAIR), "record the reply outcome")
		_at(CLOCK["basis"])
		_ok(conclusion.record_case_conclusion(tender=self.tender, kind="Due diligence basis", reason=BASIS, idempotency_key=_key("basis"), user=CHAIR),
			"record the due-diligence basis")
		_at(CLOCK["end2"])
		_ok(discussion.end_discussion(tender=self.tender, idempotency_key=_key("end2"), user=CHAIR), "end the second discussion")
		_at(CLOCK["narrative"])
		draft = report.draft(frappe.get_doc("Evaluation Case", case))
		_ok(report.save_narrative(tender=self.tender, narrative=SUMMARY, expected_version=draft.record_version, idempotency_key=_key("narrative"), user=SECRETARY),
			"write the committee summary")
		_at(CLOCK["freeze"])
		draft.reload()
		_ok(signing.send_for_signing(tender=self.tender, expected_version=draft.record_version, idempotency_key=_key("freeze"), user=SECRETARY), "send for signing")
		for user, at in zip((CHAIR, MEMBER, MEMBER_2), CLOCK["sign"]):
			_at(at)
			version = signing.signing_version(frappe.get_doc("Evaluation Case", case)).name
			_ok(signing.sign(tender=self.tender, report_version=version, idempotency_key=_key(f"sign-{user}"), user=user), f"sign as {user}")


def lifecycle_complete(tender: str) -> bool:
	return frappe.db.get_value("Evaluation Case", {"tender": tender}, "state") == "Report sent" and all(row["ok"] for row in validate_bid_evaluation_seed())


def upsert_bid_evaluation_base(*, commit: bool = False) -> dict[str, Any]:
	"""The `bid_evaluation` stage. A complete canonical evaluation is returned
	untouched; a partial one (an interrupted seed, or a browser pass) is removed
	and told again from the start."""
	from kentender_procurement.bid_evaluation.seeds import clear
	from kentender_procurement.bid_evaluation.services import simulation

	_guard()
	tender = canonical_tender()
	if not tender or frappe.db.get_value("Bid Opening Case", {"tender": tender}, "state") != "Opening complete":
		frappe.throw("The canonical Tender's opening is not complete. Seed through the bid_opening stage first.")
	if lifecycle_complete(tender):
		result = {"ok": True, "idempotent": True, "tender": tender, "evaluation": frappe.db.get_value("Evaluation Case", {"tender": tender}, "name")}
	else:
		clear.wipe(tenders=[tender], namespace=NAMESPACE)
		frappe.db.set_value("Evaluation Handoff", {"tender": tender, "consumer": "evaluation"}, "delivery_status", "Pending", update_modified=False)
		simulation.reset_controls()
		saved = {flag: frappe.flags.get(flag) for flag in (*CLOCKS, "kt_evl_fixture_namespace")}
		frappe.flags.kt_evl_fixture_namespace = NAMESPACE
		try:
			_Story(tender).run()
		finally:
			for flag, value in saved.items():
				frappe.flags[flag] = value
		result = {"ok": True, "idempotent": False, "tender": tender, "evaluation": frappe.db.get_value("Evaluation Case", {"tender": tender}, "name")}
	if commit:
		frappe.db.commit()
	return result


def validate_bid_evaluation_seed() -> list[dict[str, Any]]:
	"""One row per §11.1 fact the canonical evaluation must carry. Never mutates."""
	from kentender_procurement.bid_evaluation.services import comparison, roster

	rows: list[dict[str, Any]] = []

	def check(ok: bool, label: str) -> None:
		rows.append({"ok": bool(ok), "check": label})

	tender = canonical_tender()
	doc = frappe.db.get_value("Evaluation Case", {"tender": tender}, ["name", "state", "source_intake"], as_dict=True) if tender else None
	check(bool(doc), "the canonical Tender has its bid evaluation")
	if not doc:
		return rows
	check(doc.state == "Report sent", f"the evaluation report was sent (got {doc.state!r})")
	members = {m["member_user"]: m["capacity"] for m in roster.current_members(doc.name)}
	check(members == {r["user"]: r["capacity"] for r in ROSTER}, "Grace Wambui (chair), Peter Mugo and Ruth Achieng were appointed")
	check(roster.secretary(doc.name) == SECRETARY, "Brian Wafula is the secretary")
	check(frappe.db.count("Evaluation Declaration", {"evaluation_case": doc.name, "choice": "No conflict to declare", "status": "Current"}) == 3,
		"each member declared no conflict")
	check(bool(doc.source_intake), "the completed opening was taken up")
	table = comparison.compare(doc.name, with_funding=False)
	recommended = table.get("recommended") or {}
	check(table.get("outcome") == "Recommendation" and recommended.get("bidder") == AFYA, "the comparison recommends Afya Digital Supplies Limited")
	by_bidder = {r["bidder"]: r for r in table.get("rows") or []}
	check(len(by_bidder) == len(RANKING), f"{len(RANKING)} bids were evaluated (got {len(by_bidder)})")
	for tenderer, position, total in RANKING:
		row = by_bidder.get(tenderer) or {}
		amount = cstr(row.get("evaluated_total"))
		same = amount == total or (amount.replace(".", "", 1).isdigit() and total.replace(".", "", 1).isdigit() and float(amount) == float(total))
		check(row.get("position") == position and same, f"{tenderer}: {position if position == 'Not ranked' else 'position ' + str(position)}, {total}")
	check(cstr(recommended.get("evaluated_total")) in ("46400000", "46400000.00", "46400000.0"), "at an evaluated total of KES 46,400,000.00")
	request = frappe.db.get_value("Evaluation Clarification", {"evaluation_case": doc.name}, ["status", "disposition", "disposition_result"], as_dict=True)
	check(bool(request) and (request.status, request.disposition, request.disposition_result) == ("Closed", "Considered", "Meets"),
		"the service-location clarification was answered and closed as Meets")
	delivery = frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": doc.name, "status": "Delivered"}, ["recipient_user", "delivered_at"], as_dict=True)
	check(bool(delivery) and delivery.recipient_user == HOP and cstr(delivery.delivered_at) == CLOCK["sign"][2],
		"the report was delivered to Charles Mutiso at 16 Jun 2027, 14:07 EAT")
	return rows
