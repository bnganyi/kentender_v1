# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Committee discussion (EVL-CHG-001 v0.4 §5.2, §7.2; plan D15; tracker
EVL4-603, EVL4-604; boards D05, D05-START, D05-JOIN, D05-ABSENT…).

Individual work is asynchronous. For a collective decision the chair's
**Start discussion** creates the session and records the chair's own
attendance in the same action; every other member, and the secretary, join
and leave personally. Nobody records anyone else's attendance. Current
participation is kept by an authenticated heartbeat; when it cannot be
established the member is unavailable for collective decisions until they
rejoin. The lapse is a technical setting (`Bid Evaluation Settings`), not a
business timeout, and it is rechecked on every collective command. A pause
for absence stops only collective decisions: reading and discussion notes
continue. The secretary cannot manufacture attendance."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_procurement.bid_evaluation.services import clock, findings, guards, prc, prc_owner, records, roster
from kentender_procurement.bid_evaluation.services.errors import Guards, fail, invalid

CACHE = "kt_evl_presence"


def _key(case: str, user: str) -> str:
	return f"{case}:{user}"


def heartbeat(*, tender: str, user: str) -> dict[str, Any]:
	name = records.case_for(tender)
	if not name:
		raise frappe.DoesNotExistError("Not found")
	frappe.cache.hset(CACHE, _key(name, user), str(clock.now()))
	return {"ok": True}


def _seen(case: str, user: str):
	value = frappe.cache.hget(CACHE, _key(case, user))
	return get_datetime(value) if value else None


def lapse_seconds() -> int:
	return cint(frappe.db.get_single_value("Bid Evaluation Settings", "presence_lapse_seconds"))


def present(doc) -> list[str]:
	from kentender_procurement.proceedings.services import sessions

	return sessions.present(doc.proceeding) if doc.proceeding else []


def active_session(doc) -> str | None:
	from kentender_procurement.proceedings.services import sessions

	return sessions.active_session(doc.proceeding) if doc.proceeding else None


def check_lapses(doc, idempotency_key: str) -> list[str]:
	"""Record a lapse for everyone present whose participation is no longer
	established; returns who lapsed. A setting of 0 disables the check."""
	from kentender_procurement.proceedings.services import sessions

	limit = lapse_seconds()
	if not limit or not active_session(doc):
		return []
	now, lapsed = clock.now(), []
	for user in present(doc):
		seen = _seen(doc.name, user)
		if seen is None or (now - seen).total_seconds() > limit:
			with prc_owner.acting(doc.name):
				sessions.record_lapse(**prc.ref(doc), member=user, idempotency_key=prc.key(idempotency_key, f"lapse-{user}-{now.isoformat()}"), actor=prc.SYSTEM)
			lapsed.append(user)
	return lapsed


def _collective_guards(doc):
	checks = guards.open_case(doc)
	if doc.state != "Reviewing":
		checks.add("EVL_VERSION_CONFLICT", reason="not_reviewing", state=doc.state)
	return checks


def start_discussion(*, tender: str, subject: str, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import sessions

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.chair(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		findings.require_member(doc, user)
		_collective_guards(doc).raise_if_any()
		invalid({"subject": "Say what the committee will discuss."} if not cstr(subject).strip() else {})
		with prc_owner.acting(doc.name):
			out = sessions.start_session(**prc.ref(doc), subject=cstr(subject).strip(), idempotency_key=prc.key(idempotency_key, "start"), actor=user)
		frappe.cache.hset(CACHE, _key(doc.name, user), str(clock.now()))
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, session=out["session_id"])

	return records.command("StartDiscussion", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"subject": subject}, body=body)


def _capacity(doc, user: str) -> str:
	if user in roster.member_users(doc.name):
		findings.require_member(doc, user)
		return "Committee member"
	if user == roster.secretary(doc.name):
		return "Secretary"
	raise frappe.DoesNotExistError("Not found")


def join_discussion(*, tender: str, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import sessions

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		capacity = _capacity(doc, user)
		guards.closed(doc, Guards()).raise_if_any()
		with prc_owner.acting(doc.name):
			out = sessions.join_session(**prc.ref(doc), capacity=capacity, idempotency_key=prc.key(idempotency_key, "join"), actor=user)
		frappe.cache.hset(CACHE, _key(doc.name, user), str(clock.now()))
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, session=out["session_id"])

	return records.command("JoinDiscussion", tender=tender, idempotency_key=idempotency_key, actor=user, payload={}, body=body)


def leave_discussion(*, tender: str, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import sessions

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		capacity = "Secretary" if user == roster.secretary(doc.name) and user not in roster.member_users(doc.name) else "Committee member"
		if user not in roster.member_users(doc.name) and user != roster.secretary(doc.name):
			raise frappe.DoesNotExistError("Not found")
		with prc_owner.acting(doc.name):
			out = sessions.leave_session(**prc.ref(doc), capacity=capacity, idempotency_key=prc.key(idempotency_key, "leave"), actor=user)
		frappe.cache.hdel(CACHE, _key(doc.name, user))
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, session=out["session_id"])

	return records.command("LeaveDiscussion", tender=tender, idempotency_key=idempotency_key, actor=user, payload={}, body=body)


def end_discussion(*, tender: str, note: str = "", idempotency_key: str, user: str) -> dict[str, Any]:
	"""The chair ends the session; a paused session may end without a conclusion."""
	from kentender_procurement.proceedings.services import sessions

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.chair(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		with prc_owner.acting(doc.name):
			out = sessions.end_session(**prc.ref(doc), note=cstr(note), idempotency_key=prc.key(idempotency_key, "end"), actor=user)
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, session=out["session_id"])

	return records.command("EndDiscussion", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"note": note}, body=body)


def record_note(*, tender: str, subject: str, note: str, reason: str = "", idempotency_key: str, user: str) -> dict[str, Any]:
	"""RecordDiscussionNote: the chair's or secretary's factual note; no
	decision authority and no words attributed to a member. Available while
	collective decisions are paused."""

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if user not in (roster.chair(doc.name), roster.secretary(doc.name)):
			raise frappe.DoesNotExistError("Not found")
		guards.closed(doc, Guards()).raise_if_any()
		if not active_session(doc):
			fail("EVL_VERSION_CONFLICT", {"reason": "no_active_session"})
		invalid({"note": "Write the discussion note."} if not cstr(note).strip() else {})
		event = prc.owner_event(doc, "DiscussionNote", f"note:{idempotency_key}", {"subject": cstr(subject).strip(), "reason": cstr(reason).strip(),
			"recorded_by": user}, idempotency_key=idempotency_key, note=cstr(note).strip())
		records.bump(doc, last_committed_event=event)
		# the note's words are returned (and journalled) for the committee record
		return records.summary(doc, event=event, session=active_session(doc), subject=cstr(subject).strip(), note=cstr(note).strip(), reason=cstr(reason).strip(),
			recorded_by=user)

	return records.command("RecordDiscussionNote", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"subject": subject, "note": note, "reason": reason}, body=body)


def recheck_presence(tender: str) -> list[str]:
	"""The participation recheck before a collective command (§5.2), committed
	on its own so a refused decision never undoes a recorded lapse."""
	name = records.case_for(tender)
	if not name or not lapse_seconds():
		return []
	doc = frappe.get_doc(records.CASE, name)
	if not active_session(doc):
		return []
	key = f"presence:{name}:{clock.now().isoformat()}"
	out = records.command("RecordPresenceLapse", tender=tender, idempotency_key=key, actor="system", payload={},
		body=lambda: records.summary(records.lock(tender), lapsed=check_lapses(records.lock(tender), key)))
	return out.get("lapsed") or []
