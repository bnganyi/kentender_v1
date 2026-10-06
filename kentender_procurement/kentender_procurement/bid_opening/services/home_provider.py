# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 §7 — the Bid Opening owner's feed to Home (owner key `bid_opening`).

Registered on the `kt_home_providers` hook; core never imports this app. One
function, `entries(*, user, region)`, answers for one actor (never the session
user) and only reads: no case is prepared, swept or advanced.

- **my_work** — the actor's assigned rows from `my_work_provider` (called, not
  copied: who holds a row and when it clears are that module's own answer), worded
  without the reference. The chair's "Start opening" row while its status is
  "Upcoming" is not My work: it is Coming up until the deadline, then the same row
  (`<case>:start`) is My work, so an entry is in exactly one of the two.
- **coming_up** — the appointed chair's "Start opening" at the case's effective
  deadline, while Upcoming.
- **waiting** — the Head of Procurement Function's wait for the Accounting Officer to
  appoint the opening committee. The owner's other waiting answers (a member waiting
  for the chair, the chair waiting for absent members) carry no hand-off instant, so
  they are not entries.
- **oversight** — none: Bid Opening has no outstanding concept (its stage summary is
  status and facts only), so the region never applies.
- **completed** — the actor's own committee appointment and arrangement publication,
  and the whitelisted commands in the Opening Command Journal (command, actor, case
  and time only; never the stored result) of the last 30 days.

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
from kentender_procurement.bid_opening.services import appointment, my_work_provider, next_steps, people, reads, records

OWNER = "bid_opening"
PAGE = "tenders"
CASE_FIELDS = ["name", "tender_title", "tender_reference", "effective_deadline", "creation"]
JOURNAL = "Opening Command Journal"
ARRANGEMENT = "Opening Arrangement"
UPCOMING = "Upcoming"
START = "start"

#: The owner's action text per row key (`task_type` after "bid_opening."), the row title without " for {reference}". "Start opening"
#: is the spec's own wording. A key not here is worded from the owner's title.
ACTIONS: dict[str, str] = {
	"appoint": "Appoint opening committee",
	"publish": "Publish how to attend",
	"decide": "Decide what happens next",
	"paused": "Decide how to proceed with the paused opening",
	"replacement": "Appoint replacement",
	"join": "Join opening",
	START: "Start opening",
	"prepare-record": "Prepare opening record",
	"sign": "Review and sign opening record",
	"register": "Provide opening register",
}
#: Recently completed actions from the command journal: command → (the action label, what "You …" says). Anything not here is not
#: shown. The appointment and the arrangements come from their own records, so their journal rows are not read twice.
COMPLETED: dict[str, tuple[str, str]] = {
	"BeginOpening": ("Started opening", "started the opening"),
	"FinishCeremony": ("Finished opening", "finished the opening"),
	"RecordOpeningNotHeld": ("Recorded opening not held", "recorded that the opening did not take place"),
	"ProvideOpeningRegister": ("Provided opening register", "provided the opening register"),
	"AttestOpeningTarget": ("Signed opening record", "signed the opening record"),
}
APPOINTED = ("Appointed opening committee", "appointed the opening committee")
PUBLISHED = ("Published how to attend", "published how to attend this opening")
#: Commands after which the owner's wait for other people is named: command → (the stage the owner's answer must be on, phrase).
AWAITING: dict[str, tuple[str, str]] = {"AttestOpeningTarget": ("record", "signature")}


def _people(names: list[str], role: str) -> str:
	"""The holder as a display: up to two names, otherwise the responsibility (never an invented person)."""
	return " or ".join(names) if names and len(names) <= 2 else cstr(role)


def _someone(names: list[str], role: str) -> str:
	if names and len(names) <= 2:
		return " or ".join(names)
	return f"{'an' if cstr(role)[:1] in 'AEIOU' else 'a'} {role}"


def _destination(reference: str) -> dict[str, Any]:
	return {"route": [PAGE, reference, "opening"]}


class _Facts:
	"""What one actor's Home read needs more than once: the cases' own titles and references."""

	def __init__(self, user: str):
		self.user = user
		self._cases: dict[str, Any] = {}

	def case(self, name: str):
		if name not in self._cases:
			self._cases[name] = frappe.db.get_value(records.CASE, name, CASE_FIELDS, as_dict=True)
		return self._cases[name]

	def can_read(self, name: str) -> bool:
		return reads.can_read(name, self.user)


# --------------------------------------------------------------------------
# applicability
# --------------------------------------------------------------------------


def _member_of(user: str, *, chair: bool = False, open_only: bool = False) -> bool:
	"""Whether the actor is on a current opening committee (as chair; of a case not yet ended)."""
	rows = frappe.db.sql(
		f"""select 1 from `tabOpening Committee Member` m
		join `tabOpening Committee Appointment` a on a.name = m.parent and m.parenttype = 'Opening Committee Appointment'
		join `tabBid Opening Case` c on c.name = a.opening_case
		where m.member_user = %(user)s and a.status = 'Active'
		{'and m.is_chair = 1' if chair else ''}
		{'and c.state not in %(ended)s' if open_only else ''} limit 1""",
		{"user": user, "ended": records.TERMINAL},
	)
	return bool(rows)


def _applies(user: str) -> bool:
	"""Responsibility, not rows: a reader role of the module, or a seat on an opening committee."""
	def build() -> bool:
		if not user or user == "Guest" or people.technical(user):
			return False
		return any(people.holds(user, role) for role in reads.READER_ROLES) or _member_of(user)

	return home_support.memo("bid_opening.applies", build, user=user)


def _chairs(user: str) -> bool:
	return home_support.memo("bid_opening.chairs", lambda: _member_of(user, chair=True, open_only=True), user=user)


# --------------------------------------------------------------------------
# My work, Coming up, Waiting
# --------------------------------------------------------------------------


def _key(row: dict[str, Any]) -> str:
	return cstr(row["task_type"]).removeprefix("bid_opening.")


def _action(row: dict[str, Any]) -> str:
	key = _key(row)
	if key in ACTIONS:
		return ACTIONS[key]
	return cstr(row["title"]).split(" for ")[0].strip()


def _case_name(row: dict[str, Any]) -> str:
	return cstr(row["task_id"]).rsplit(":", 1)[0]


def _entered(row: dict[str, Any], case) -> Any:
	"""The raw instant the row was handed to the actor (the owner's own `since`), else the case's own creation."""
	since = row.get("since") or {}
	return get_datetime(since["at"]) if since.get("at") else case.creation


def _blocked(facts: _Facts, row: dict[str, Any], case) -> tuple[bool, str]:
	"""Blocked only where the owner's own answer for the chair's start is Your turn, blocked; its headline is the reason."""
	if _key(row) != START:
		return False, ""
	step = next_steps.answer_for(frappe.get_doc(records.CASE, case.name), facts.user)
	headline = cstr(step.get("headline")).strip()
	return (True, headline) if step.get("kind") == ns.KIND_BLOCKED and headline else (False, "")


def _register(user: str) -> dict[str, Any]:
	"""One scan of the owner's rows for one Home read: {"my_work", "coming_up", "waiting"}."""
	facts = _Facts(user)
	legacy = my_work_provider.my_work_rows(user)
	my_work: list[dict[str, Any]] = []
	coming_up: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []
	for row in legacy["assigned"]:
		case = facts.case(_case_name(row))
		if not case:
			continue
		if _key(row) == START and row["status"] == UPCOMING:
			coming_up.append(he.make(
				region=he.COMING_UP, owner=OWNER, root=case.name, action_id=row["task_id"], title=cstr(case.tender_title), reference=cstr(case.tender_reference),
				action=ACTIONS[START], destination=_destination(case.tender_reference), scheduled_at=get_datetime(case.effective_deadline),
			))
			continue
		blocked, reason = _blocked(facts, row, case)
		my_work.append(he.make(
			region=he.MY_WORK, owner=OWNER, root=case.name, action_id=row["task_id"], title=cstr(case.tender_title), reference=cstr(case.tender_reference),
			action=_action(row), destination=_destination(case.tender_reference), entered_at=_entered(row, case), entered_verb="Received", blocked=blocked, reason=reason,
		))
	for row in legacy["waiting"]:
		holder = row.get("holder") or {}
		names, role = list(holder.get("people") or []), cstr(holder.get("role"))
		case = facts.case(_case_name(row))
		since = (row.get("since") or {}).get("at")
		if not case or not since or not (names or role):
			frappe.logger("kentender.home").info("bid opening waiting row has no since or holder | row=%s", row.get("task_id"))
			continue
		waiting.append(he.make(
			region=he.WAITING, owner=OWNER, root=case.name, action_id=row["task_id"], title=cstr(case.tender_title), reference=cstr(case.tender_reference),
			action=f"Waiting for {_someone(names, role)} to appoint the opening committee", destination=_destination(case.tender_reference),
			holder=_people(names, role), since=get_datetime(since),
		))
	return {"my_work": my_work, "coming_up": coming_up, "waiting": waiting}


# --------------------------------------------------------------------------
# Recently completed actions
# --------------------------------------------------------------------------


def _awaiting(facts: _Facts, case, command: str) -> str:
	""""It is awaiting signature by Fred Odhiambo." — only while the owner's current answer for the actor is a wait, with the holder named,
	on the stage the command leaves the case at."""
	expected = AWAITING.get(command)
	if not expected:
		return ""
	step = next_steps.answer_for(frappe.get_doc(records.CASE, case.name), facts.user)
	holder = step.get("holder") or {}
	names = list(holder.get("people") or [])
	if step.get("kind") != ns.KIND_WAITING or cstr(step.get("stage")) != expected[0] or not names:
		return ""
	return home_time.awaiting(expected[1], _people(names, cstr(holder.get("role"))))


def _completed(user: str) -> list[dict[str, Any]]:
	facts = _Facts(user)
	at = home_time.now()
	cutoff = datetime.combine((at - timedelta(days=home_time.COMPLETED_DAYS)).date(), time.min)
	made: list[dict[str, Any]] = []

	def add(case_name: str, action_id: str, wording: tuple[str, str], when: Any, command: str = "") -> None:
		case = facts.case(case_name)
		if not case or not facts.can_read(case.name):
			return
		made.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=case.name, action_id=action_id, title=cstr(case.tender_title), reference=cstr(case.tender_reference), action=wording[0],
			destination=_destination(case.tender_reference), completed_at=when,
			sentence=home_time.completed_sentence(wording[1], when, follow=_awaiting(facts, case, command)),
		))

	for row in frappe.get_all(appointment.APPOINTMENT, filters={"appointed_by": user, "appointed_at": (">=", cutoff)}, fields=["name", "opening_case", "appointed_at"],
			order_by="appointed_at desc", limit_page_length=0):
		add(row.opening_case, row.name, APPOINTED, row.appointed_at)
	for row in frappe.get_all(ARRANGEMENT, filters={"published_by": user, "published_at": (">=", cutoff)}, fields=["name", "opening_case", "published_at"],
			order_by="published_at desc", limit_page_length=0):
		add(row.opening_case, row.name, PUBLISHED, row.published_at)
	# the journal (no index on actor or time: bounded by the cutoff; never the stored result). One line per case and command, the latest.
	latest: dict[tuple[str, str], Any] = {}
	for row in frappe.get_all(JOURNAL, filters={"actor": user, "command": ("in", list(COMPLETED)), "recorded_at": (">=", cutoff)},
			fields=["name", "command", "opening_case", "recorded_at"], order_by="recorded_at desc", limit_page_length=0):
		latest.setdefault((cstr(row.opening_case), cstr(row.command)), row)
	for (case_name, command), row in latest.items():
		add(case_name, row.name, COMPLETED[command], row.recorded_at, command)
	return sorted(made, key=lambda entry: entry["completed_at"], reverse=True)


# --------------------------------------------------------------------------
# the provider
# --------------------------------------------------------------------------


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	if region not in he.REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if not user or user == "Guest" or region == he.OVERSIGHT or not _applies(user):
		return None
	if region == he.COMING_UP and not _chairs(user):
		return None
	if region == he.COMPLETED:
		return home_support.memo("bid_opening.completed", lambda: _completed(user), user=user)
	return home_support.memo("bid_opening.register", lambda: _register(user), user=user)[region]
