# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The case's next step in the shared shape (CM-CHG-001 v0.8 §6.3; KT-STD-001 §3B; tracker CM8-312).

`tasks.view` decides which item leads; this maps it onto `kentender_core.services.next_step` so the shared Vue components draw it and no wording is computed in
the browser: actionable work is *Your turn*, a blocked duty is *Your turn, blocked* with its fix owner, work held by someone else is *Waiting on someone* naming
the holder and when it was assigned, and a fixed future event is *Scheduled* with no person to wait on. A reader with no personal task block is *Not involved*.
The headline wording for each command is the owning package's (`headline_for`); this skeleton owns only the mapping."""

from __future__ import annotations

from typing import Any, Callable

from kentender_contracts.services import clock, tasks
from kentender_core.services import next_step as shared


def answer(view: dict[str, Any], *, headline_for: Callable[[dict[str, Any]], str]) -> dict[str, Any]:
	lead = view["leading"]
	if lead is None:
		return shared.not_involved() if view.get("neutral") else shared.answer(shared.KIND_DONE)
	since = shared.since(lead["assigned_at"], clock.when(lead["assigned_at"]))
	headline = headline_for(lead)
	if lead["state"] == tasks.SCHEDULED:
		return shared.answer(shared.KIND_SCHEDULED, headline=headline, since=since)
	if view["leading_is_waiting_on_someone_else"] or lead["state"] == tasks.WAITING:
		return shared.answer(shared.KIND_WAITING, headline=headline, holder=shared.holder(lead.get("holder_role", ""), [lead["holder"]]), since=since)
	if lead["state"] == tasks.BLOCKED:
		info = lead.get("blocker") or {}
		fixes = [shared.fix(info.get("fix_label") or "Resolve", responsibility=info.get("responsibility", ""), kind="route", primary=True)]
		refused = shared.guard(False, reason_code=info.get("reason_code", "CM_HOLD"), message=info.get("message", ""), headline=headline, fixes=fixes)
		return shared.answer(shared.KIND_BLOCKED, headline=headline, since=since, blockers=[shared.blocker(refused)])
	return shared.answer(shared.KIND_YOUR_TURN, headline=headline, since=since, primary_action=lead["command"])
