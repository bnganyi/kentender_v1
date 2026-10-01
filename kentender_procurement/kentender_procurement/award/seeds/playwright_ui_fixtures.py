# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award browser worlds (AWD-CHG-001 v0.4 §10, §13; plan OD-B, D16; tracker
rule 10).

Each stage is one isolated branch of the §13 fixture chronology, built from
the synthetic upstream sources by the real Award commands as the real
personas, at the spec's instants — no tender, bid, opening or evaluation is
built, so a stage takes about a second. `reset_award_fixture(stage)` builds
one for a Playwright spec and leaves the site's test clock at the stage's
viewing instant; `capture_all()` writes every viewer's server answers for
every stage to `public/js/award/fixtures/` for the fidelity spec.
`restore_site()` removes every browser-world row. Test environment only."""

from __future__ import annotations

import json
import os
from typing import Any, Callable

import frappe

from kentender_procurement.award.seeds import clear
from kentender_procurement.award.services import (
	corrections, decision, eligibility, explanation, opinion, profile, reads, records, restrictions, simulation, state, supplier, tender_events,
)
from kentender_procurement.award.test_services import sources as syn

NS = "PW_AWARD"
HOP = "charles.mutiso@moh.example.test"
AO = "amina.hassan@moh.example.test"
MARY = "mary.wanjiku@afyadigital.example"
DAVID = "david.ouma@afyadigital.example"
DANIEL = "daniel.otieno@moh.example.test"
NAOMI = "naomi.chebet@moh.example.test"
VIEWERS = {"hop": HOP, "ao": AO, "mary": MARY, "david": DAVID, "daniel": DANIEL, "naomi": NAOMI}
D02R = ("The signed report identifies Afya Digital Supplies Limited as the lowest evaluated responsive tenderer. No unresolved issue prevents the "
	"proposed award.")
DECR = "I accept the recommendation in the signed evaluation report and professional opinion."
CORRECTION = {"source_event": "PW-CN:1", "kind": "Report correction", "reference": "PW-CN-1", "reason": "Evaluation reported a material calculation issue.",
	"detail": "The line total was recalculated.", "effective_at": "2027-06-18 09:30:00"}
CORR_REASON = "The reported calculation issue may affect the recommendation."
_n = [0]


def _key(prefix: str) -> str:
	_n[0] += 1
	return f"pw-awd-{prefix}-{_n[0]}-{frappe.generate_hash(length=6)}"


class World:
	def __init__(self, world: str = "033"):
		self.world = world
		self.award = f"AWD-MOH-2027-{world}"
		self.reference = f"TND-MOH-2027-{world}"

	def at(self, instant: str) -> "World":
		frappe.flags.kt_awd_clock = instant
		return self

	def as_(self, user: str, fn: Callable, **kwargs) -> dict[str, Any]:
		frappe.set_user(user)
		try:
			return fn(user=user, idempotency_key=_key(fn.__name__), **kwargs)
		finally:
			frappe.set_user("Administrator")

	def v(self) -> int:
		return int(frappe.db.get_value(records.CASE, self.award, "record_version"))

	def deliver(self, **kwargs) -> "World":
		self.at(kwargs.pop("at", "2027-06-16 14:07:01"))
		syn.deliver(self.world, reference=self.reference, **kwargs)
		return self

	def save(self, conclusion="Recommend award", reason=D02R) -> "World":
		self.as_(HOP, opinion.save, award=self.award, conclusion=conclusion, reason=reason, expected_version=self.v())
		return self

	def sign(self, conclusion="Recommend award", reason=D02R, at="2027-06-17 09:10:00") -> "World":
		self.at("2027-06-17 09:00:00").save(conclusion, reason).at(at)
		self.as_(HOP, opinion.sign, award=self.award, expected_version=self.v())
		return self

	def decide(self, outcome="Award", reason=DECR, next_action="", at="2027-06-17 10:00:00") -> "World":
		self.at(at)
		self.as_(AO, decision.record, award=self.award, outcome=outcome, reason=reason, next_action=next_action, expected_version=self.v())
		return self

	def notice(self):
		return state.successful_notice(state.current_batch(frappe.get_doc(records.CASE, self.award)))

	def respond(self, response="Accept", reason="", at="2027-06-18 09:00:00") -> "World":
		self.at(at)
		self.as_(MARY, supplier.respond, notice=self.notice().name, response=response, reason=reason, notice_version=self.notice().version)
		return self

	def issue(self, **filters) -> str:
		return frappe.get_all(state.ISSUE, filters={"award_case": self.award, "state": "Open", **filters}, pluck="name")[0]

	def correction(self, at="2027-06-18 10:00:00") -> "World":
		self.at(at)
		syn.add_correction(frappe.db.get_value(records.CASE, self.award, "tender"), CORRECTION)
		corrections.pull_case(self.award)
		return self

	def propose(self) -> "World":
		self.as_(HOP, restrictions.disposition, award=self.award, issue=self.issue(issue_type="Source correction"), outcome="Request corrected evaluation",
			reason=CORR_REASON, evidence="PW-CN-1", next_action="Request a corrected evaluation report addressing the calculation issue.")
		return self

	def instruct(self, at="2027-06-18 10:05:00") -> "World":
		self.at(at)
		self.as_(AO, corrections.record, award=self.award, outcome="Request corrected evaluation", reason=CORR_REASON, expected_version=self.v())
		return self

	def corrected_report(self, **kwargs) -> "World":
		self.at("2027-06-19 09:00:00")
		syn.deliver(self.world, reference=self.reference, version=2, delivered_at="2027-06-19 09:00:00", **kwargs)
		return self


def _awarded(w: World) -> World:
	return w.deliver().sign().decide()


def _cycle_two(w: World, **kwargs) -> World:
	return _awarded(w).correction().propose().instruct().corrected_report(**kwargs)


# stage: (builder, viewing instant, switches left on for the browser)
STAGES: dict[str, tuple[Callable[[], World], str, dict[str, Any]]] = {
	"received": (lambda: World().deliver(), "2027-06-17 09:00:00", {}),
	"signed": (lambda: World().deliver().sign(), "2027-06-17 10:00:00", {}),
	"notified": (lambda: _awarded(World()), "2027-06-17 10:10:00", {}),
	"accepted": (lambda: _awarded(World()).respond(), "2027-06-18 09:05:00", {}),
	"delivered": (lambda: _deliver(_awarded(World()).respond()), "2027-07-02 09:00:00", {}),
	"request": (lambda: _request(_awarded(World()).respond()), "2027-06-18 10:00:00", {}),
	"request-closed": (lambda: _request(_awarded(World()).respond(), close=True), "2027-06-18 10:15:00", {}),
	"returned": (lambda: _returned(World().deliver().sign()), "2027-06-18 10:00:00", {}),
	"source-incomplete": (lambda: World().deliver(overrides={"missing_annex": True}), "2027-06-18 10:00:00", {}),
	"expired": (lambda: _expired(World()), "2027-10-11 09:00:00", {}),
	"no-award": (lambda: _no_award(_expired(World())), "2027-10-11 09:00:00", {}),
	"notice-failed": (lambda: _failing(World()), "2027-06-18 10:00:00", {"email_failure_organisations": "Afya Digital Supplies Limited"}),
	"declined": (lambda: _awarded(World()).respond("Decline", "We cannot meet the delivery commitment."), "2027-06-18 10:00:00", {}),
	"no-response": (lambda: _no_response(_awarded(World())), "2027-06-24 17:01:00", {}),
	"order-hold": (lambda: _order(_awarded(World()).respond()), "2027-06-20 11:00:00", {}),
	"challenge-hold": (lambda: _order(_awarded(World()).respond(), basis="Reported challenge"), "2027-06-20 11:00:00", {}),
	"post-decision-correction": (lambda: _awarded(World()).respond().correction(), "2027-06-18 10:00:00", {}),
	"correction-decision": (lambda: _awarded(World()).respond().correction().propose(), "2027-06-18 10:00:00", {}),
	"receiver-down": (lambda: _receiver_down(_awarded(World()).respond()), "2027-07-02 09:01:00", {"contracting_down": 1}),
	"cancelled": (lambda: _cancelled(World().deliver().sign()), "2027-06-17 09:30:00", {}),
	"signing-unavailable": (lambda: _signing_down(World().deliver()), "2027-06-18 10:00:00", {"signing_outcome": "Unavailable"}),
	"unsuccessful": (lambda: _awarded_037(), "2027-06-17 10:10:00", {}),
	"rules-unverified": (lambda: _rules(World()), "2027-06-18 10:00:00", {"rule_unverified": 1}),
	"status-unknown": (lambda: _status(World()), "2027-06-18 10:00:00", {"status_service_down": 1}),
	"technical": (lambda: _service_down(World()), "2027-06-18 10:00:00", {"email_service_down": 1}),
	"tie": (lambda: World("036").deliver(), "2027-06-17 09:00:00", {}),
	"correction-authorised": (lambda: _awarded(World()).respond().correction().propose().instruct(), "2027-06-18 10:05:00", {}),
	"corrected-report": (lambda: _cycle_two(World(), outcome="Qualified report", reason="The calculation discrepancy remains unresolved."), "2027-06-19 09:05:00", {}),
	"closed-correction": (lambda: _no_award(_expired(World())).correction(at="2027-10-11 10:00:00"), "2027-10-11 10:00:00", {}),
	"late-response": (lambda: _awarded(World()).respond(at="2027-06-24 17:01:00"), "2027-06-24 17:05:00", {}),
	"corrected-opinion": (lambda: _cycle_two(World(), outcome="Qualified report",
		reason="The calculation discrepancy remains unresolved.").sign("No current recommendation", "The calculation discrepancy remains unresolved.",
		at="2027-06-19 09:10:00"), "2027-06-19 09:15:00", {}),
	"corrected-opinion-positive": (lambda: _cycle_two(World()).sign("Recommend award", "The corrected report confirms the recommendation.", at="2027-06-19 09:10:00"),
		"2027-06-19 09:15:00", {}),
	"revised-held": (lambda: _revised(World()), "2027-06-19 10:00:00", {"revised_treatment_unverified": 1}),
	"revised-ready": (lambda: _revised(World(), release=True), "2027-06-19 10:00:00", {}),
}


def _deliver(w: World) -> World:
	w.at("2027-07-02 09:00:00")
	eligibility.refresh_case(w.award)
	return w


def _request(w: World, close: bool = False) -> World:
	w.at("2027-06-18 10:00:00")
	req = w.as_(DAVID, supplier.request_explanation, notice=w.notice().name, request="Please explain the recorded award result.")["request"]
	if close:
		w.at("2027-06-18 10:15:00")
		w.as_(HOP, explanation.send, award=w.award, request=req,
			reply="The recorded result follows the signed evaluation report. Your tender was successful at KES 46,400,000.")
	return w


def _returned(w: World) -> World:
	w.at("2027-06-17 10:00:00")
	w.as_(AO, decision.record, award=w.award, outcome="Return for correction", reason="Explain the unresolved funding concern before recommending an award.",
		expected_version=w.v())
	return w


def _expired(w: World) -> World:
	return w.deliver(overrides={"validity_end": "2027-10-10 11:00:00"}).at("2027-10-11 09:00:00")


def _no_award(w: World) -> World:
	w.sign("No current recommendation", "Tender validity expired before an award could be notified.", at="2027-10-11 09:00:00")
	return w.decide("No award", "Tender validity expired before an award could be notified.", "Review whether the tender should be cancelled", at="2027-10-11 09:00:00")


def _failing(w: World) -> World:
	simulation.set_controls(email_failure_organisations="Afya Digital Supplies Limited")
	return _awarded(w)


def _no_response(w: World) -> World:
	w.at("2027-06-24 17:01:00")
	eligibility.refresh_case(w.award)
	return w


def _order(w: World, basis: str = "Authoritative order") -> World:
	w.at("2027-06-20 11:00:00")
	w.as_(HOP, restrictions.record_external, award=w.award, basis=basis, source="Review Board suspension notice" if basis == "Authoritative order" else "Complaint letter",
		received_at="2027-06-20 11:00:00", evidence="PPARB/2027/33" if basis == "Authoritative order" else "", reason="Received by the procuring entity.")
	return w


def _receiver_down(w: World) -> World:
	simulation.set_controls(contracting_down=1)
	return _deliver(w).at("2027-07-02 09:01:00")


def _cancelled(w: World) -> World:
	tender = frappe.db.get_value(records.CASE, w.award, "tender")
	syn.set_fact(tender, cancelled=True)
	syn.add_event(tender, {"event_key": "PW-CANCEL-1", "kind": "Cancellation", "source": "Tenders", "source_reference": "TCN-PW-1", "authority": AO,
		"reason": "The procurement is no longer required.", "effective_at": "2027-06-17 09:30:00"})
	w.at("2027-06-17 09:30:00")
	tender_events.consume_case(w.award)
	return w


def _signing_down(w: World) -> World:
	w.at("2027-06-18 09:55:00").save()
	simulation.set_controls(signing_outcome="Unavailable")
	w.at("2027-06-18 10:00:00")
	w.as_(HOP, opinion.sign, award=w.award, expected_version=w.v())
	return w


def _awarded_037() -> World:
	return _awarded(World("037"))


def _rules(w: World) -> World:
	simulation.set_controls(rule_unverified=1)
	return w.deliver()


def _status(w: World) -> World:
	simulation.set_controls(status_service_down=1)
	return w.deliver()


def _service_down(w: World) -> World:
	simulation.set_controls(email_service_down=1)
	return _awarded(w)


def _revised(w: World, release: bool = False) -> World:
	_cycle_two(w).sign("Recommend award", "The corrected report confirms the recommendation.", at="2027-06-19 09:10:00")
	simulation.set_controls(revised_treatment_unverified=1)
	w.at("2027-06-19 10:00:00")
	w.as_(AO, corrections.record, award=w.award, outcome="Record corrected award", reason="The corrected report confirms the recommendation.", expected_version=w.v())
	if release:
		simulation.set_controls(revised_treatment_unverified=0)
		eligibility.refresh_case(w.award)
	return w


# -- entry points ------------------------------------------------------------------
def _require_test_site() -> None:
	if not simulation.enabled():
		frappe.throw("Award browser worlds exist on a test environment only.")


def _wipe() -> None:
	clear.wipe(namespace=NS)
	syn.clear()
	simulation.reset_controls()
	frappe.flags.kt_awd_clock = None


def reset_award_fixture(*, stage: str, commit: bool = True) -> dict[str, Any]:
	"""Build one stage; leave the site's test clock at its viewing instant."""
	from kentender_core.services.test_clock import set_instant

	_require_test_site()
	if stage not in STAGES:
		frappe.throw(f"Unknown Award stage {stage!r}.")
	frappe.set_user("Administrator")
	_wipe()
	frappe.flags.kt_awd_fixture_namespace = NS
	profile.install_test_profile(contracting_owner=HOP, technical_operator=DANIEL)
	build, instant, switches = STAGES[stage]
	w = build()
	frappe.flags.kt_awd_clock = None
	simulation.set_controls(**{k: v for k, v in switches.items()}) if switches else None
	set_instant(instant)
	doc = frappe.get_doc(records.CASE, w.award)
	notice = state.successful_notice(state.current_batch(doc))
	notices = frappe.get_all(state.NOTICE, filters={"award_case": doc.name}, fields=["name", "organisation_name"], order_by="notice_number asc")
	requests = frappe.get_all(state.CORRESPONDENCE, filters={"award_case": doc.name}, pluck="name")
	if commit:
		frappe.db.commit()
	return {"stage": stage, "award": doc.name, "tender_reference": doc.tender_reference, "instant": instant, "notice": notice.name if notice else "",
		"notices": {n.organisation_name: n.name for n in notices}, "requests": requests}


def restore_site(commit: bool = True) -> dict[str, Any]:
	from kentender_core.services.test_clock import set_instant

	_require_test_site()
	_wipe()
	set_instant("")
	if commit:
		frappe.db.commit()
	return {"ok": True}


def capture(stage: str) -> dict[str, Any]:
	"""Every viewer's server answers for one stage (the fidelity oracle)."""
	info = reset_award_fixture(stage=stage, commit=False)
	out: dict[str, Any] = {"info": info}
	from kentender_core.services.test_clock import current_instant

	frappe.flags.kt_awd_clock = current_instant()
	for key, user in VIEWERS.items():
		frappe.set_user(user)
		try:
			if key in ("mary", "david"):
				views = {}
				for n in info["notices"].values():
					try:
						views[n] = supplier.notice_view(notice=n, user=user)
					except frappe.DoesNotExistError:
						continue
				out[key] = views
			else:
				out[key] = {"record": reads.record(award=info["award"], user=user), "workspace": reads.workspace(user=user)}
		except frappe.DoesNotExistError:
			out[key] = None
		except Exception as exc:  # pragma: no cover - recorded for the capture log
			out[key] = {"error": str(exc)}
		finally:
			frappe.set_user("Administrator")
	frappe.flags.kt_awd_clock = None
	return json.loads(json.dumps(out, default=str))


def capture_all(*, stages: list[str] | None = None) -> dict[str, Any]:
	"""Write `public/js/award/fixtures/<stage>.json` for every stage (seconds)."""
	_require_test_site()
	target = os.path.join(frappe.get_app_path("kentender_procurement"), "public", "js", "award", "fixtures")
	os.makedirs(target, exist_ok=True)
	done = []
	for stage in stages or list(STAGES):
		data = capture(stage)
		with open(os.path.join(target, f"{stage}.json"), "w", encoding="utf-8") as fh:
			json.dump(data, fh, indent=1, sort_keys=True, ensure_ascii=False)
			fh.write("\n")
		done.append(stage)
		frappe.db.rollback()
	restore_site(commit=True)
	return {"captured": done}


# -- browser-world helpers (test environment only) -----------------------------------
def set_controls(**values) -> dict[str, Any]:
	_require_test_site()
	out = simulation.set_controls(**values)
	frappe.db.commit()
	return out


def set_instant(*, instant: str = "") -> dict[str, Any]:
	from kentender_core.services.test_clock import current_instant
	from kentender_core.services.test_clock import set_instant as _set

	_require_test_site()
	previous = current_instant()
	_set(instant)
	frappe.db.commit()
	return {"previous": str(previous or "")}


def simulate_contact_correction(*, award: str, email: str = "bids@afyadigital.example") -> dict[str, Any]:
	"""The supplier corrects its notice contact through its own contact form."""
	_require_test_site()
	failed = frappe.get_all(state.NOTICE, filters={"award_case": award, "status": "Failed"}, fields=["name", "bid"])
	for n in failed:
		syn.correct_contact(n.bid, email)
	simulation.set_controls(email_failure_organisations="")
	frappe.db.commit()
	return {"corrected": [n.name for n in failed]}


def refresh(*, award: str) -> dict[str, Any]:
	"""The scheduled eligibility check, run now (at the site's test instant)."""
	_require_test_site()
	out = eligibility.refresh_case(award)
	frappe.db.commit()
	return {"stage": out.get("stage")}
