# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 §7 — the Bid Evaluation owner's feed to Home (owner key `evaluation`).

Registered on the `kt_home_providers` hook; core never imports this app. One
function, `entries(*, user, region)`, answers for one actor (never the session
user) and only reads: no case is prepared, advanced or refreshed.

- **my_work** — the actor's assigned rows from `my_work_provider` (called, not
  copied: who holds a row and when it clears are that module's own answer), worded
  without the reference. The owner's answer never says "Your turn, blocked" for an
  evaluation, so no row is blocked.
- **waiting** — the owner's waiting rows, each with the holder the roster names and
  the hand-off instant the owner recorded. A row with no hand-off instant is skipped,
  and the supplier's reply is waited for only by someone who may read bids (the chair,
  the secretary and eligible members), never the Accounting Officer or the Head of
  Procurement Function.
- **oversight** — what the owner's disclosure rule allows, nothing more. Before a
  report is delivered the Accounting Officer, the Head of Procurement Function and a
  contributing Head of User Department are told one state-level fact: the committee's
  review is outstanding (no count, no bidder, no finding). After delivery nothing is
  outstanding unless the report was returned for correction. The disclosure is the
  owner's own `reads.access` and `stage_summary.for_tender`; a stage that failed to
  load is a failed read, not an empty one.
- **coming_up** — the evaluation deadline the owner records, for those who oversee or
  hold the evaluation, while the case is still open.
- **completed** — the actor's own appointment, secretary delegation, report sent for
  signing and report return of the last 30 days. The system's own delivery is not an
  action of a person.

Returns None where the region does not apply to the actor, [] where it applies and
there is nothing to show; a failed read raises.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import next_step as ns
from kentender_core.services.authorization import permitted_ou_scopes
from kentender_procurement.bid_evaluation.services import diligence, next_steps, oversight, people, reads, records, roster, signing, stage_summary, timers
from kentender_procurement.bid_evaluation.services import my_work_provider
from kentender_procurement.tenders.services import stage_summary as ss

OWNER = "evaluation"
PAGE = "tenders"
HEAD_OF_USER_DEPARTMENT = "Head of User Department"
CASE_STATES = ("Preparing", "Reviewing", "Signing", "Report sent")
OPEN_STATES = ("Preparing", "Reviewing", "Signing")
ENDED_STATES = ("Report sent", "No evaluation required", "Cancelled")
UNAVAILABLE = "unavailable"

#: The owner's action text per row key (`task_type` after "bid_evaluation."), the row title without " for {reference}". "Appoint the
#: evaluation committee" is the spec's own wording (the owner's headline; its action label is "Appoint committee").
ACTIONS: dict[str, str] = {
	"appoint": "Appoint the evaluation committee",
	"declare": "Declare interests",
	"resolve-appointment": "Resolve committee appointment",
	"review": "Review bids",
	"concern": "Resolve evaluation concern",
	"send": "Send clarification",
	"outcome": "Review clarification outcome",
	"observe": "Record verification findings",
	"prepare-verification": "Prepare verification report",
	"sign-verification": "Review and sign verification report",
	"verification-outcome": "Review verification outcome",
	"sign": "Review and sign report",
	"report-concern": "Resolve report concern",
	"correct": "Correct evaluation report",
	"review-report": "Review evaluation report",
	"supplement": "Review opening update",
	"correction": "Review report correction",
}
#: The owner's waiting rows: row key (before the first ":waiting") → the verb phrase after "Waiting for {holder} to …".
WAITING: dict[str, str] = {
	"appoint": "appoint the evaluation committee",
	"declare": "declare their interests",
	"resolve-appointment": "resolve the committee appointment",
	"concern": "respond to the concern",
	"send": "send the clarification",
	"reply": "reply to the clarification",
	"verify": "record their verification findings",
	"sign-verification": "sign the verification report",
	"verification-outcome": "record the committee's conclusion",
	"sign": "sign the evaluation report",
	"correct": "correct the evaluation report",
	"correction": "review the report correction",
}
#: The waits where every named person owes their part (not either of them): "A and B", not "A or B".
EVERY = ("declare", "verify", "sign-verification", "sign")
#: What the owner's holder role reads as when more than two people owe the same thing.
PLURAL = {"Appointed member": "the committee members"}
#: Recently completed actions: kind → (the action label, what "You …" says).
COMPLETED: dict[str, tuple[str, str]] = {
	"appointed": ("Appointed evaluation committee", "appointed the evaluation committee"),
	"secretary": ("Delegated secretary duties", "delegated the secretary duties"),
	"report": ("Sent report for signing", "sent the evaluation report for signing"),
	"returned": ("Returned evaluation report", "returned the evaluation report for correction"),
}
#: Kinds after which the owner's wait for other people is named: kind → (the state the case must be in, phrase).
AWAITING: dict[str, tuple[str, str]] = {"report": ("Signing", "signatures")}
REVIEW_ACTION = "Committee review outstanding"  # the spec's own wording: state-level, never a count, a bidder or a finding


def _who(names: list[str], phrase: str, joiner: str = " or ") -> str:
	"""The holder as a sentence subject: "Amina Hassan or Brian Wafula" for up to two people, otherwise the responsibility ("an Accounting Officer")."""
	return joiner.join(names) if names and len(names) <= 2 else phrase


def _display(names: list[str], role: str, joiner: str = " or ") -> str:
	"""The holder as a display: up to two names, otherwise the responsibility (never an invented person)."""
	return joiner.join(names) if names and len(names) <= 2 else role


def _destination(reference: str, *sub: str) -> dict[str, Any]:
	return {"route": [PAGE, reference, "evaluation", *sub]}


class _Facts:
	"""What one actor's Home read needs more than once: the cases, their access for the actor and their people."""

	def __init__(self, user: str):
		self.user = user
		self._cases: dict[str, Any] = {}
		self._access: dict[str, dict[str, Any]] = {}

	def case(self, name: str):
		if name not in self._cases:
			self._cases[name] = frappe.get_doc(records.CASE, name) if frappe.db.exists(records.CASE, name) else None
		return self._cases[name]

	def access(self, doc) -> dict[str, Any]:
		if doc.name not in self._access:
			self._access[doc.name] = reads.access(doc, self.user)
		return self._access[doc.name]

	def names(self, users: list[str]) -> list[str]:
		return [people.full_name(user) for user in users if user]


def _case_name(row: dict[str, Any]) -> str:
	return cstr(row["task_id"]).split(":", 1)[0]


def _route(row: dict[str, Any]) -> list[str]:
	"""The owner's route as Desk segments: it writes a record under a section as one "clarifications/{name}" part."""
	return [segment for part in row["route"] for segment in cstr(part).split("/") if segment]


def _key(row: dict[str, Any]) -> str:
	return cstr(row["task_type"]).removeprefix("bid_evaluation.")


# --------------------------------------------------------------------------
# applicability
# --------------------------------------------------------------------------


def _seat(user: str) -> bool:
	"""A seat on an evaluation: a current committee member, the secretary or the recipient of a delivered report."""
	if frappe.db.sql(
		"""select 1 from `tabEvaluation Committee Member` m join `tabEvaluation Appointment` a on a.name = m.parent and m.parenttype = 'Evaluation Appointment'
		where m.member_user = %s and m.status = 'Current' and a.status = 'Current' limit 1""", user):
		return True
	return bool(frappe.db.exists(roster.SECRETARY, {"secretary_user": user, "status": "Current"}) or frappe.db.exists(oversight.DELIVERY, {"recipient_user": user, "status": "Delivered"}))


def _offices(user: str) -> tuple[bool, bool]:
	return people.holds(user, people.ACCOUNTING_OFFICER), people.holds(user, people.HEAD_OF_PROCUREMENT)


def _applies(user: str) -> bool:
	"""Responsibility, not rows: an office of the module, the Auditor, or a seat on an evaluation."""
	def build() -> bool:
		if not user or user == "Guest" or people.technical(user):
			return False
		return any(_offices(user)) or people.holds(user, people.AUDITOR) or _seat(user)

	return home_support.memo("evaluation.applies", build, user=user)


def _oversees(user: str) -> bool:
	"""An oversight-capable responsibility: the Accounting Officer, the Head of Procurement Function, or a Head of User Department
	(`None` from the scope helper is a site-wide assignment)."""
	def build() -> bool:
		scopes = permitted_ou_scopes(user, HEAD_OF_USER_DEPARTMENT)
		return any(_offices(user)) or scopes is None or bool(scopes)

	return home_support.memo("evaluation.oversees", build, user=user)


def _holds_evaluation(user: str) -> bool:
	"""Who has a Coming up: the offices that oversee the deadline, and those who hold the evaluation (committee, secretary)."""
	return home_support.memo("evaluation.holds", lambda: any(_offices(user)) or _seat(user), user=user)


# --------------------------------------------------------------------------
# My work, Waiting
# --------------------------------------------------------------------------


def _since(row: dict[str, Any]) -> Any:
	return get_datetime(row["received_at"]) if cstr(row.get("received_at")) else None


def _entered(doc, row: dict[str, Any]) -> Any:
	"""The raw instant the row was handed to the actor: the owner's own `since`; where the owner has none (an unset preparation
	instant, a replacement or a review that never recorded one) the nearest recorded instant of the same matter, else the case's creation."""
	since = _since(row)
	if since:
		return since
	key = _key(row)
	if key == "resolve-appointment":
		appointment = roster.current_appointment(doc.name)
		return appointment.appointed_at if appointment else doc.creation
	if key == "review":
		intake = frappe.db.get_value("Evaluation Source Intake", doc.source_intake, "received_at") if doc.source_intake else None
		return intake or doc.opening_completed_at or doc.creation
	return doc.prepared_at or doc.creation


def _action(row: dict[str, Any]) -> str:
	key = _key(row)
	return ACTIONS[key] if key in ACTIONS else cstr(row["title"]).split(" for ")[0].strip()


def _my_work(facts: _Facts, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for row in rows:
		doc = facts.case(_case_name(row))
		if not doc:
			continue
		out.append(he.make(
			region=he.MY_WORK, owner=OWNER, root=doc.name, action_id=row["task_id"], title=cstr(doc.tender_title), reference=cstr(doc.tender_reference),
			action=_action(row), destination={"route": _route(row)}, entered_at=_entered(doc, row), entered_verb="Received",
		))
	return out


def _unobserved(doc, plan) -> list[str]:
	observed = {o.participant_user for o in diligence.observations(plan)}
	return [user for user in diligence.participants(plan) if user not in observed]


def _holder(facts: _Facts, doc, row: dict[str, Any], kind: str) -> tuple[list[str], str, str, Any]:
	"""(the people who hold what the actor waits for, the responsibility as a sentence subject and as a display when there are more
	than two or none, a due instant), from the roster and the people the owner's rows are about."""
	if kind in ("appoint", "resolve-appointment"):
		return facts.names(people.holders(people.ACCOUNTING_OFFICER)), "an Accounting Officer", people.ACCOUNTING_OFFICER, None
	if kind == "declare":
		owed = [u for u in roster.member_users(doc.name) if not roster.declaration(doc.name, u)]
		return facts.names(owed), "the committee members", "Committee members", None
	if kind in ("concern", "verification-outcome"):
		return facts.names([roster.chair(doc.name)]), "the chair", "Chair", None
	if kind == "send":
		return facts.names([roster.secretary(doc.name)]), "the secretary", "Secretary", None
	if kind == "reply":
		request = frappe.db.get_value("Evaluation Clarification", cstr(row["task_id"]).rsplit(":", 1)[1], ["evaluation_bid", "reply_deadline"], as_dict=True)
		bidder = cstr(frappe.db.get_value("Evaluation Bid", request.evaluation_bid, "tenderer_name")) if request else ""
		return ([bidder] if bidder else []), "the supplier", "Supplier", request.reply_deadline if request else None
	if kind == "verify":
		plan = diligence.current_plan(doc.name)
		owed = _unobserved(doc, plan) if plan else []
		return facts.names(owed or ([plan.lead_user] if plan else [])), "the verification participants", "Verification participants", None
	if kind == "sign-verification":
		plan = diligence.current_plan(doc.name)
		owed = [u for u in diligence.participants(plan) if diligence.my_targets(doc, plan, u)] if plan else []
		return facts.names(owed), "the verification participants", "Verification participants", None
	if kind == "sign":
		version = signing.signing_version(doc)
		return facts.names([s["member"] for s in signing.signatures(version) if not s["signed_at"]]), "the committee members", "Committee members", None
	if kind == "correct":
		return facts.names([roster.chair(doc.name), roster.secretary(doc.name)]), "the chair or the secretary", "Chair or Secretary", None
	delivery = frappe.db.get_value(oversight.DELIVERY, {"evaluation_case": doc.name, "status": "Delivered"}, "recipient_user", order_by="delivered_at desc")
	return facts.names([delivery] if delivery else []), "the Head of Procurement Function", people.HEAD_OF_PROCUREMENT, None  # correction


def _waiting(facts: _Facts, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for row in rows:
		doc = facts.case(_case_name(row))
		task_id = cstr(row["task_id"])
		kind = task_id.split(":", 2)[1] if task_id.count(":") else ""
		if not doc or kind not in WAITING:
			continue
		since = _since(row)
		if kind == "appoint":
			since = since or doc.prepared_at or doc.creation  # an unset preparation instant: the case's own creation
		if not since:
			frappe.logger("kentender.home").info("evaluation waiting row has no since | row=%s", task_id)
			continue
		if kind == "reply" and not facts.access(doc)["bids"]:
			continue  # the supplier's reply is waited for only by someone who may read bids
		names, phrase, role, due = _holder(facts, doc, row, kind)
		joiner = " and " if kind in EVERY else " or "
		out.append(he.make(
			region=he.WAITING, owner=OWNER, root=doc.name, action_id=task_id, title=cstr(doc.tender_title), reference=cstr(doc.tender_reference),
			action=f"Waiting for {_who(names, phrase, joiner)} to {WAITING[kind]}", destination={"route": _route(row)}, holder=_display(names, role, joiner),
			since=since, due=due,
		))
	return out


def _register(user: str) -> dict[str, Any]:
	facts = _Facts(user)
	legacy = my_work_provider.my_work_rows(user)
	return {"my_work": _my_work(facts, legacy["assigned"]), "waiting": _waiting(facts, legacy["waiting"])}


# --------------------------------------------------------------------------
# Records you oversee
# --------------------------------------------------------------------------


def _review_since(doc) -> Any:
	appointment = roster.current_appointment(doc.name)
	return (appointment.appointed_at if appointment else None) or doc.prepared_at or doc.creation


def _oversight(user: str) -> list[dict[str, Any]]:
	facts = _Facts(user)
	out: list[dict[str, Any]] = []
	for name in frappe.get_all(records.CASE, filters={"state": ("in", CASE_STATES)}, pluck="name", order_by="creation asc"):
		doc = facts.case(name)
		access = facts.access(doc)
		if access["technical"] or not access["read"] or not (access["ao"] or access["hop"] or access["department"]):
			continue
		stages = stage_summary.for_tender(tender=doc.tender, user=user)
		if any(stage.get("state") == UNAVAILABLE for stage in stages):
			raise RuntimeError(f"The evaluation summary for {doc.tender_reference} is unavailable")  # a failed read, never an empty one
		summary = next((stage for stage in stages if stage.get("key") == stage_summary.KEY), None)
		if not summary:
			continue
		if not access["delivered"]:
			if doc.state not in OPEN_STATES or summary.get("disclosure") != ss.STATUS_ONLY:
				continue
			action, action_id, since = REVIEW_ACTION, f"{doc.name}:review", _review_since(doc)
		else:
			outstanding = summary.get("outstanding") or {}
			delivery = next(iter(oversight.deliveries(doc.name)), None)
			if not cstr(outstanding.get("text")) or not delivery or not delivery.returned_at:
				continue
			action, action_id, since = cstr(outstanding["text"]), f"{doc.name}:returned", delivery.returned_at
		out.append(he.make(
			region=he.OVERSIGHT, owner=OWNER, root=doc.name, action_id=action_id, title=cstr(doc.tender_title), reference=cstr(doc.tender_reference), action=action,
			destination=_destination(doc.tender_reference), since=since, outstanding=True,
		))
	return out


# --------------------------------------------------------------------------
# Coming up
# --------------------------------------------------------------------------


def _coming_up(user: str) -> list[dict[str, Any]]:
	facts = _Facts(user)
	out: list[dict[str, Any]] = []
	offices = any(_offices(user))
	for name in frappe.get_all(records.CASE, filters={"state": ("in", OPEN_STATES)}, pluck="name", order_by="creation asc"):
		doc = facts.case(name)
		if not offices and user not in roster.member_users(doc.name) and user != roster.secretary(doc.name):
			continue
		deadline = timers.dated(doc)["evaluation_deadline"]
		if not deadline or doc.state in ENDED_STATES:
			continue
		out.append(he.make(
			region=he.COMING_UP, owner=OWNER, root=doc.name, action_id=f"{doc.name}:deadline", title=cstr(doc.tender_title), reference=cstr(doc.tender_reference),
			action="Evaluation deadline", destination=_destination(doc.tender_reference), scheduled_at=deadline,
		))
	return out


# --------------------------------------------------------------------------
# Recently completed actions
# --------------------------------------------------------------------------


def _awaiting(facts: _Facts, doc, kind: str) -> str:
	""""It is awaiting signatures by A and B." — only while the owner's current answer for the actor is a wait, with the holders named,
	and the case is where the action leaves it."""
	expected = AWAITING.get(kind)
	if not expected or doc.state != expected[0]:
		return ""
	step = next_steps.answer(doc, facts.user)
	holder = step.get("holder") or {}
	names = list(holder.get("people") or [])
	if step.get("kind") != ns.KIND_WAITING or not names:
		return ""
	role = cstr(holder.get("role"))
	return home_time.awaiting(expected[1], _who(names, PLURAL.get(role, role), " and "))


def _completed(user: str) -> list[dict[str, Any]]:
	facts = _Facts(user)
	at = home_time.now()
	cutoff = datetime.combine((at - timedelta(days=home_time.COMPLETED_DAYS)).date(), time.min)
	made: list[dict[str, Any]] = []

	def add(case_name: str, action_id: str, kind: str, when: Any) -> None:
		doc = facts.case(case_name)
		if not doc or not facts.access(doc)["read"]:
			return
		wording = COMPLETED[kind]
		made.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=doc.name, action_id=action_id, title=cstr(doc.tender_title), reference=cstr(doc.tender_reference), action=wording[0],
			destination=_destination(doc.tender_reference), completed_at=when,
			sentence=home_time.completed_sentence(wording[1], when, follow=_awaiting(facts, doc, kind)),
		))

	def rows(doctype: str, who: str, when: str, **extra):
		return frappe.get_all(doctype, filters={who: user, when: (">=", cutoff), **extra}, fields=["name", "evaluation_case", when], order_by=f"{when} desc", limit_page_length=0)

	for row in rows(roster.APPOINTMENT, "appointed_by", "appointed_at"):
		add(row.evaluation_case, row.name, "appointed", row.appointed_at)
	# only the Head's written delegation is an action of a person; the by-office record is part of the Accounting Officer's appointment (EVL-CHG-001 v0.8 §3)
	for row in rows(roster.SECRETARY, "assigned_by", "assigned_at", basis="Written appointment"):
		add(row.evaluation_case, row.name, "secretary", row.assigned_at)
	for row in rows(signing.REPORT, "frozen_by", "frozen_at"):
		add(row.evaluation_case, row.name, "report", row.frozen_at)
	for row in rows(oversight.DELIVERY, "returned_by", "returned_at"):
		add(row.evaluation_case, row.name, "returned", row.returned_at)
	return sorted(made, key=lambda entry: entry["completed_at"], reverse=True)


# --------------------------------------------------------------------------
# the provider
# --------------------------------------------------------------------------


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	if region not in he.REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if not user or user == "Guest" or people.technical(user):
		return None
	if region == he.OVERSIGHT:
		return home_support.memo("evaluation.oversight", lambda: _oversight(user), user=user) if _oversees(user) else None
	if not _applies(user):
		return None
	if region == he.COMING_UP:
		return home_support.memo("evaluation.coming_up", lambda: _coming_up(user), user=user) if _holds_evaluation(user) else None
	if region == he.COMPLETED:
		return home_support.memo("evaluation.completed", lambda: _completed(user), user=user)
	return home_support.memo("evaluation.register", lambda: _register(user), user=user)[region]
