# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 §7 — the Award owner's feed to Home (owner key `award`).

Registered on the `kt_home_providers` hook; core never imports this app. One
function, `entries(*, user, region)`, answers for one actor (never the session
user) and only reads: no case is refreshed, no clock is swept, no signing is
retried.

- **my_work** — the work items the owner derives for the actor (`tasks.all_for_user`,
  the same source as `tasks.my_work_rows`, called and not copied). The row shows
  the Tender's title and reference, the owner's task wording without the
  reference, and the instant the item arose; "Decide award" has none of its own,
  so it carries the signed opinion's `signed_at` (the moment it reached the
  Accounting Officer). A row is blocked only where the owner's own answer for
  the actor (`next_steps.answer`) is Your turn, blocked for that exact item.
- **waiting** — the Head of Procurement Function waiting for the Accounting
  Officer's award decision. The Accounting Officer's wait for the opinion is
  not a waiting row: it is a record they oversee.
- **oversight** — for an actor Award lets read it (Head of Procurement Function,
  Accounting Officer, Auditor) or a Head of User Department of a contributing
  unit. What is outstanding is the owner's own disclosure (`stage_summary`); only
  a full reader also gets the unconfirmed-notice issue (`next_steps.outstanding`).
  A Head of User Department is never given the notice information.
- **coming_up** — none: Award records waiting-period and reply clocks but no
  scheduled answer an actor holds (owner decision if wanted).
- **completed** — the actor's own committed `Award Decision` rows, signed
  professional opinions and correction decisions of the last 30 days.

Returns None where the region does not apply to the actor, [] where it applies
and there is nothing to show; a failed read raises.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import next_step as ns
from kentender_core.services.authorization import permitted_ou_scopes
from kentender_procurement.award.services import guards, issues, next_steps, notices, people, records, stage_summary, state, tasks
from kentender_procurement.tenders.services.tender_roles import ROLE_HEAD_OF_USER_DEPARTMENT

OWNER = "award"
PAGE = "award"
CASE_FIELDS = ["name", "stage", "tender", "tender_reference", "tender_title", "received_at"]
#: The stages in which Award itself says who the case is with (`stage_summary.outstanding`) or holds a notice to confirm.
OVERSEEN_STAGES = ("Opinion", "Decision", "Notices")

#: My work wording, by the owner's own task name (spec §10B: Prepare professional opinion, Resolve notice delivery, Decide award). A task not
#: listed is the next action a "No award" decision named, which is the owner's recorded text and is shown as written.
ACTIONS: dict[str, str] = {
	"Prepare professional opinion": "Prepare professional opinion",
	"Resolve returned decision": "Resolve returned decision",
	"Resolve notice delivery": "Resolve notice delivery",
	"Resolve expired validity": "Resolve expired validity",
	"Resolve supplier response": "Resolve supplier response",
	"Review report correction": "Review report correction",
	"Review opening update": "Review opening update",
	"Resolve revised notice treatment": "Resolve revised notice treatment",
	"Review restriction": "Review restriction",
	"Resolve funding": "Resolve funding",
	"Resolve rules issue": "Resolve rules issue",
	"Respond to request": "Respond to request",
	"Decide award": "Decide award",
	"Decide correction": "Decide correction",
}
#: The owner's blocked answers (`reason_code`) and the work item each one stops. Any other blocked answer (a hold, revised-notice treatment)
#: is not that item's own block: its resolution is another item, or the whole case.
BLOCKS: dict[str, tuple[str, ...]] = {
	"AWD_NOTICE_FAILED": ("Resolve notice delivery",),
	"AWD_SOURCE_INCOMPLETE": ("Prepare professional opinion",),
	"AWD_RULE_UNVERIFIED": ("Prepare professional opinion",),
}
#: Recently completed: Award Decision outcome and kind → (the action label, what "You …" says).
DECISIONS: dict[tuple[str, str], tuple[str, str]] = {
	("Award", "Initial"): ("Recorded award decision", "recorded the award decision"),
	("No award", "Initial"): ("Recorded no award", "recorded that no award is made"),
	("Award", "Correction"): ("Recorded corrected award", "recorded the corrected award decision"),
	("No award", "Correction"): ("Recorded no award", "recorded that no award is made after the correction"),
}
SIGNED = ("Signed professional opinion", "signed the professional opinion")
CORRECTION = ("Recorded correction decision", "recorded a decision on the reported correction")
#: A correction command that also recorded a committed decision is that one row, not two.
SAME_ACTION = timedelta(seconds=60)


def _log(message: str, **values: Any) -> None:
	frappe.logger("kentender.home", allow_site=True).warning(f"award home: {message} {values}")


def _someone(names: list[str], role: str) -> str:
	"""The holder as a sentence subject: "Amina Hassan", or "an Accounting Officer" (never an invented person)."""
	if names and len(names) <= 2:
		return " or ".join(names)
	return f"{'an' if cstr(role)[:1] in 'AEIOU' else 'a'} {role}"


def _people(names: list[str], role: str) -> str:
	return " or ".join(names) if names and len(names) <= 2 else cstr(role)


class _Facts:
	"""What one actor's Home read needs more than once: the cases and the owner's answers."""

	def __init__(self, user: str):
		self.user = user
		self._docs: dict[str, Any] = {}
		self._answers: dict[str, dict[str, Any]] = {}

	def doc(self, name: str):
		if name not in self._docs:
			self._docs[name] = frappe.get_doc(records.CASE, name)
		return self._docs[name]

	def answer(self, name: str) -> dict[str, Any]:
		if name not in self._answers:
			self._answers[name] = next_steps.answer(self.doc(name), self.user)
		return self._answers[name]

	def signed_at(self, name: str):
		signed = state.signed_opinion(self.doc(name))
		return signed.signed_at if signed else None

	def blocked(self, item: dict[str, Any]) -> tuple[bool, str]:
		"""Blocked only where the owner's answer for the actor is Your turn, blocked and it names this item; its headline is the reason."""
		codes = [code for code, tasks_ in BLOCKS.items() if item["task"] in tasks_]
		if not codes:
			return False, ""
		answer = self.answer(item["award"])
		reasons = [cstr(b.get("reason_code")) for b in answer.get("blockers") or []]
		headline = cstr(answer.get("headline")).strip()
		if answer.get("kind") == ns.KIND_BLOCKED and headline and any(code in reasons for code in codes):
			return True, headline
		return False, ""


def _record(name: str) -> dict[str, Any]:
	return {"route": [PAGE, name]}


# --------------------------------------------------------------------------
# My work, Waiting, Records you oversee
# --------------------------------------------------------------------------


def _work(facts: _Facts) -> tuple[list[dict[str, Any]], set[str]]:
	entries: list[dict[str, Any]] = []
	held: set[str] = set()
	for item in tasks.all_for_user(facts.user):
		held.add(item["award"])
		entered = get_datetime(item["since"]) if item["since"] else facts.signed_at(item["award"]) if item["task"] in ("Decide award", "Decide correction") else None
		if not entered:
			_log("skipped a work item with no instant", item=item["key"], task=item["task"])
			continue
		blocked, reason = facts.blocked(item)
		entries.append(he.make(
			region=he.MY_WORK, owner=OWNER, root=item["award"], action_id=item["key"], title=item["tender_title"], reference=item["tender_reference"],
			action=ACTIONS.get(item["task"], item["task"]), destination=_record(item["award"]), entered_at=entered, entered_verb="Received",
			blocked=blocked, reason=reason,
		))
	return entries, held


def _waiting(facts: _Facts, cases: list[Any], *, hop: bool) -> tuple[list[dict[str, Any]], set[str]]:
	"""The Head of Procurement Function waits for the Accounting Officer's decision (and for nothing else Award records)."""
	entries: list[dict[str, Any]] = []
	waits: set[str] = set()
	if not hop:
		return entries, waits
	holders = [user for user in people.holders(people.ACCOUNTING_OFFICER) if user != facts.user]
	names = [people.full_name(user) for user in holders]
	for case in cases:
		if case.stage != "Decision" or people.holds(facts.user, people.ACCOUNTING_OFFICER):
			continue
		doc = facts.doc(case.name)
		signed = state.signed_opinion(doc)
		if not signed or not signed.signed_at:
			_log("skipped a wait with no instant", case=case.name)
			continue
		waits.add(case.name)
		decide = "the correction" if cint(state.cycle(doc).number) > 1 or state.latest_committed(doc) else "the award"
		entries.append(he.make(
			region=he.WAITING, owner=OWNER, root=case.name, action_id=f"{case.name}:{doc.current_cycle}:waiting:decide:{state.cycle(doc).opinion}", title=case.tender_title,
			reference=case.tender_reference, action=f"Waiting for {_someone(names, people.ACCOUNTING_OFFICER)} to decide {decide}", destination=_record(case.name),
			holder=_people(names, people.ACCOUNTING_OFFICER), since=signed.signed_at,
		))
	return entries, waits


def _notice_row(facts: _Facts, case) -> dict[str, Any] | None:
	"""The unconfirmed-notice matter, for a full reader only: the owner's own outstanding list, with the issue's real instant."""
	doc = facts.doc(case.name)
	for row in next_steps.outstanding(doc):
		if row.get("subtype") != notices.DELIVERY_SUBTYPE or not row.get("issue"):
			continue
		since = frappe.db.get_value(issues.ISSUE, row["issue"], "received_at")
		if not since:
			_log("skipped a notice matter with no instant", case=case.name, issue=row["issue"])
			return None
		return he.make(
			region=he.OVERSIGHT, owner=OWNER, root=case.name, action_id=f"{case.name}:oversight", title=case.tender_title, reference=case.tender_reference,
			action=f"A required notice is not yet confirmed; resolution by {row['owner']}", destination=_record(case.name), holder=cstr(row["owner"]), since=since,
			outstanding=True,
		)
	return None


def _summary_row(facts: _Facts, case, *, tender: str) -> dict[str, Any] | None:
	"""The stage the case is with, from Award's own summary for this reader; a failed read is raised, not hidden."""
	found = stage_summary.for_tender(tender=tender, user=facts.user)
	if not found:
		return None
	shown = found[0]
	if shown.get("state") != "ok":
		raise RuntimeError(f"The award stage for {case.name} could not be read for {facts.user}: {shown.get('message')}")
	outstanding = shown.get("outstanding")
	if not outstanding:
		return None
	who = cstr(outstanding.get("holder"))
	if case.stage == "Opinion":
		since, role = case.received_at, people.HEAD_OF_PROCUREMENT
		action = f"Awaiting professional opinion by {who or 'the Head of Procurement Function'}"
	else:
		doc = facts.doc(case.name)
		since, role = facts.signed_at(case.name), people.ACCOUNTING_OFFICER
		correction = "correction" if cint(state.cycle(doc).number) > 1 or state.latest_committed(doc) else "award"
		action = f"Awaiting {correction} decision by {who or 'the Accounting Officer'}"
	if not since:
		_log("skipped an oversight row with no instant", case=case.name, stage=case.stage)
		return None
	return he.make(
		region=he.OVERSIGHT, owner=OWNER, root=case.name, action_id=f"{case.name}:oversight", title=case.tender_title, reference=case.tender_reference, action=action,
		destination=_record(case.name), holder=who or role, since=since, outstanding=True, **_delivered_report(facts, case, tender=tender),
	)


def _delivered_report(facts: _Facts, case, *, tender: str) -> dict[str, Any]:
	"""Evaluation's own View report link for this reader, with the instant the report was delivered (HOME-AC-07). The link is
	Evaluation's published one (its stage summary offers it only to a reader who may read the delivered report), not a route
	built here; no link, or an Evaluation read that fails, leaves Award's own row as it is."""
	from kentender_procurement.bid_evaluation.services import stage_summary as evaluation

	try:
		shown = (evaluation.for_tender(tender=tender, user=facts.user) or [{}])[0]
		offered = next((link for link in shown.get("links") or [] if link.get("key") == "view-report"), None) if shown.get("state") == "ok" else None
		delivered = state.snapshot(state.current_report(facts.doc(case.name))).get("delivered_at")
	except Exception:
		_log("could not read the delivered report link", case=case.name)
		return {}
	if not offered or not delivered:
		return {}
	return {"link": {"label": "View report", "destination": offered["route"]}, "fact": "Evaluation report delivered", "fact_at": get_datetime(delivered)}


def _oversight(facts: _Facts, cases: list[Any], *, skip: set[str], full: bool) -> list[dict[str, Any]]:
	"""One row per case the actor neither holds nor waits on. A reader gets the owner's summary and (full readers only) the notice matter; a
	Head of User Department of a contributing unit gets only the summary's outstanding line."""
	entries: list[dict[str, Any]] = []
	for case in cases:
		if case.name in skip:
			continue
		if full:
			row = _notice_row(facts, case) if case.stage == "Notices" else None
			if not row and case.stage in ("Opinion", "Decision"):
				row = _summary_row(facts, case, tender=case.tender)
		elif case.stage in ("Opinion", "Decision") and frappe.db.exists("Tender", case.tender) and stage_summary.department_of(case.tender, facts.user):
			row = _summary_row(facts, case, tender=case.tender)
		else:
			row = None
		if row:
			entries.append(row)
	return entries


def _applies(user: str) -> dict[str, bool]:
	def build() -> dict[str, bool]:
		if not user or user == "Guest" or people.technical(user):
			return {"work": False, "read": False, "department": False, "hop": False}
		hop = people.holds(user, people.HEAD_OF_PROCUREMENT)
		ao = people.holds(user, people.ACCOUNTING_OFFICER)
		return {"work": hop or ao, "hop": hop, "ao": ao, "read": guards.can_read(user), "department": bool(permitted_ou_scopes(user, ROLE_HEAD_OF_USER_DEPARTMENT))}

	return home_support.memo("award.applies", build, user=user)


def _register(user: str) -> dict[str, Any]:
	"""One scan of the open cases for one Home read: {"my_work", "waiting", "oversight"} (a region None where it does not apply)."""
	applies = _applies(user)
	facts = _Facts(user)
	my_work, held = _work(facts) if applies["work"] else (None, set())
	cases = frappe.get_all(records.CASE, filters={"stage": ("in", OVERSEEN_STAGES), "cancelled": 0}, fields=CASE_FIELDS, order_by="creation asc", limit_page_length=0)
	waiting, waits = _waiting(facts, cases, hop=applies.get("hop", False)) if applies["work"] else (None, set())
	oversight = _oversight(facts, cases, skip=held | waits, full=applies["read"]) if applies["read"] or applies["department"] else None
	return {"my_work": my_work, "waiting": waiting, "oversight": oversight}


# --------------------------------------------------------------------------
# Recently completed actions
# --------------------------------------------------------------------------


def _follow(case: str, decision) -> str:
	"""What is still open after the actor's decision, in the owner's words, only while that decision is the case's current one."""
	current = frappe.db.get_value(records.CASE, case, ["current_decision", "cancelled"], as_dict=True)
	if not current or current.cancelled or current.current_decision != decision.name:
		return ""
	if decision.outcome == "Award":
		batch = frappe.db.get_value(state.BATCH, {"decision": decision.name}, ["name", "given_complete_at"], as_dict=True)
		return "Required bidder notices are not yet confirmed." if batch and not batch.given_complete_at else ""
	if decision.outcome == "No award" and decision.next_action_state == "Open" and decision.next_action:
		action = cstr(decision.next_action).strip().rstrip(".")
		return f"Next: {people.full_name(decision.next_action_owner)} to {action[:1].lower() + action[1:]}." if decision.next_action_owner else ""
	return ""


def _completed(user: str) -> list[dict[str, Any]]:
	at = home_time.now()
	cutoff = at - timedelta(days=home_time.COMPLETED_DAYS)
	cutoff = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
	readable = guards.can_read(user)
	cases: dict[str, Any] = {}

	def case(name: str):
		if name not in cases:
			cases[name] = frappe.db.get_value(records.CASE, name, ["name", "tender_title", "tender_reference"], as_dict=True) if readable and name else None
		return cases[name]

	entries: list[dict[str, Any]] = []
	decided: list[tuple[str, Any]] = []
	for row in frappe.get_all(state.DECISION, filters={"decided_by": user, "committed": 1, "decided_at": (">=", cutoff)}, order_by="decided_at desc", limit_page_length=0,
			fields=["name", "award_case", "outcome", "kind", "decided_at", "next_action", "next_action_owner", "next_action_state"]):
		wording = DECISIONS.get((cstr(row.outcome), cstr(row.kind)))
		found = case(row.award_case) if wording else None
		if not found:
			continue
		decided.append((row.award_case, get_datetime(row.decided_at)))
		entries.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=found.name, action_id=row.name, title=found.tender_title, reference=found.tender_reference, action=wording[0],
			destination=_record(found.name), completed_at=row.decided_at, sentence=home_time.completed_sentence(wording[1], row.decided_at, follow=_follow(found.name, row)),
		))
	# The journal holds the commands that leave no Award Decision of their own; only command, actor, case and time are read (never the result).
	for row in frappe.get_all(records.JOURNAL, filters={"actor": user, "command": ("in", ("SignProfessionalOpinion", "RecordAwardCorrectionDecision")), "recorded_at": (">=", cutoff)},
			fields=["name", "command", "award_case", "recorded_at"], order_by="recorded_at desc", limit_page_length=0):
		found = case(row.award_case)
		if not found:
			continue
		if row.command == "RecordAwardCorrectionDecision":
			if any(name == row.award_case and abs(get_datetime(row.recorded_at) - when) <= SAME_ACTION for name, when in decided):
				continue
			label, did = CORRECTION
		else:
			label, did = SIGNED
		entries.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=found.name, action_id=row.name, title=found.tender_title, reference=found.tender_reference, action=label,
			destination=_record(found.name), completed_at=row.recorded_at, sentence=home_time.completed_sentence(did, row.recorded_at),
		))
	return sorted(entries, key=lambda entry: entry["completed_at"], reverse=True)


# --------------------------------------------------------------------------
# the provider
# --------------------------------------------------------------------------


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	if region not in he.REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if not user or user == "Guest" or region == he.COMING_UP:
		return None
	applies = _applies(user)
	if region == he.COMPLETED:
		return home_support.memo("award.completed", lambda: _completed(user), user=user) if applies["work"] else None
	return home_support.memo("award.register", lambda: _register(user), user=user)[region]
