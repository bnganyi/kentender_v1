# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Task identity, de-duplication and the §6.3 ordering (CM-CHG-001 v0.8 §6.3, §6.4; tracker CM8-312; CM-AC-59 started).

A task is one **obligation of one holder**: one logical item per command subject, version and required holder. A delivery retry or an event replay
therefore never creates a second item (`dedupe` keeps the first assignment). A reassignment keeps the previous holder and the time it ended; the old task
identity confers no authority, because authority is AUTH's at the moment of the command, and `may_act` says only whose task it is now.

For the actor, actionable work is ordered: a protective, legal or security deadline **at risk**; then other verified overdue duty; then the earliest verified
upcoming due instant; then undated work by assignment instant and stable task id. An unverified date is not an urgency and shows "Not established"; no
urgency score is invented. A blocked duty stays visible with its fix owner but never leads while actionable work exists, and waiting and scheduled rows sit
below in the same ordering. The case shows one leading item and an Other work region without the leading item.

Tasks here are plain dicts; the record that stores them arrives with the first package that creates real work (Phase 4). Keys: task_id, case, subject, version,
command, holder, state (actionable | blocked | waiting | scheduled), due, due_verified (default true), assigned_at, protective, at_risk, plus optional holder_role
and blocker. The deadline's "at risk" is decided by the rule that calculates the deadline, not here."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

ACTIONABLE, BLOCKED, WAITING, SCHEDULED = "actionable", "blocked", "waiting", "scheduled"
GROUP = {ACTIONABLE: 0, BLOCKED: 1, WAITING: 2, SCHEDULED: 3}
NOT_ESTABLISHED = "Not established"


def identity(task: dict[str, Any]) -> str:
	return f"{task['case']}|{task['subject']}|{task['version']}|{task['command']}|{task['holder']}"


def dedupe(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""One item per identity; the first assignment (then the lowest id) is kept, so a replay changes nothing."""
	by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
	for task in tasks:
		by_identity[identity(task)].append(task)
	return [min(group, key=lambda t: (t["assigned_at"], t["task_id"])) for group in by_identity.values()]


def reassign(task: dict[str, Any], new_holder: str, *, at: datetime) -> dict[str, Any]:
	moved = dict(task)
	moved["history"] = [*task.get("history", []), {"holder": task["holder"], "from": task["assigned_at"], "until": at}]
	moved["holder"], moved["assigned_at"] = new_holder, at
	return moved


def may_act(task: dict[str, Any], user: str) -> bool:
	"""Whose task this is now. Not an authority grant: the command still checks AUTH."""
	return bool(user) and task["holder"].lower() == user.lower()


def due_verified(task: dict[str, Any]) -> bool:
	return bool(task.get("due")) and task.get("due_verified", True)


def due_display(task: dict[str, Any], now: datetime) -> str:
	return task["due"].strftime("%Y-%m-%d %H:%M") if due_verified(task) else NOT_ESTABLISHED


def rank(task: dict[str, Any], now: datetime) -> int:
	if due_verified(task) and task.get("protective") and task.get("at_risk"):
		return 0
	if due_verified(task) and task["due"] < now:
		return 1
	return 2 if due_verified(task) else 3


def sort_key(task: dict[str, Any], now: datetime) -> tuple:
	r = rank(task, now)
	# Two obligations assigned at the same instant (a simulated clock holds still; a batch is assigned in one moment) are led by the one recorded first, never by the order of their random names.
	return (GROUP[task["state"]], r, task["due"] if r < 3 else task["assigned_at"], task.get("created") or task["assigned_at"], task["task_id"])


def order(tasks: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
	return sorted(tasks, key=lambda t: sort_key(t, now))


def view(tasks: list[dict[str, Any]], actor: str, now: datetime, *, neutral: bool = False) -> dict[str, Any]:
	"""The leading item and Other work for one actor. `neutral` is a read-only reader with no personal task block."""
	if neutral:
		return {"leading": None, "other": [], "leading_is_waiting_on_someone_else": False, "neutral": True}
	items = dedupe(tasks)
	mine = [t for t in items if may_act(t, actor)]
	active = [t for t in mine if t["state"] in (ACTIONABLE, BLOCKED)]
	rest_mine = [t for t in mine if t not in active]
	theirs = [t for t in items if not may_act(t, actor)]
	if active:
		ordered = order(active, now) + order(rest_mine, now) + order(theirs, now)
	else:
		# nothing the actor can do: the next holder is the leading item, then everything else in the same ordering
		ordered = order(rest_mine + theirs, now)
	leading = ordered[0] if ordered else None
	return {"leading": leading, "other": ordered[1:], "leading_is_waiting_on_someone_else": bool(leading) and not may_act(leading, actor), "neutral": False}
