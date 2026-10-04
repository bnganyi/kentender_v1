# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The order of a bid's tasks, and where each button leads (owner request, 2
Oct 2026).

A bid has five tasks in a fixed order: Tender documents, Company, Requirements,
Price, Review and submit. A bidder may work out of order, so the task to do
"next" is the next one still to do: after the current task, then any earlier
one left unfinished, then Review. Every button that moves on names where it
leads, every task page says which step it is, and the bid page says how much of
the preparation is done. Pure functions over the task navigation rows
(`projection.task_nav`): no database, no state."""

from __future__ import annotations

from typing import Any

REVIEW = "review"
COMPLETE = "Complete"
# short names for buttons and links; the full task label stays the page's own title
SHORT = {
	"documents": "Tender documents", "company": "Company and declarations", "requirements": "Requirements", "price": "Price", REVIEW: "Review and submit",
}
TONES = {"Complete": "live", "Needs attention": "attention", "In progress": "pending", "Not started": "draft"}


def short_name(row: dict[str, Any]) -> str:
	return SHORT.get(row["key"], row["label"])


def _preparation(nav: list[dict[str, Any]]) -> list[dict[str, Any]]:
	return [row for row in nav if row["key"] != REVIEW]


def handed_over(nav: list[dict[str, Any]], hand_over: list[str] | None) -> bool:
	"""The preparer's part is finished and someone else must sign: every task before
	Review is done and the viewer is not the person who submits."""
	return bool(hand_over) and all(row["status"] == COMPLETE for row in _preparation(nav))


def _signs(hand_over: list[str] | None) -> str:
	return f"{', '.join(hand_over or [])} signs and submits"


def progress(nav: list[dict[str, Any]], hand_over: list[str] | None = None) -> dict[str, Any]:
	"""How much of the preparation (every task before Review) is done, and what is
	left: the next task, or, when the preparer has finished, who signs."""
	prep = _preparation(nav)
	done = sum(1 for row in prep if row["status"] == COMPLETE)
	out = {"done": done, "of": len(prep), "text": f"{done} of {len(prep)} tasks done", "next": short_name(_by_key(nav, next_key(nav)))}
	if handed_over(nav, hand_over):
		out.update(next="", waiting=_signs(hand_over))
	return out


def next_key(nav: list[dict[str, Any]], after: str | None = None) -> str:
	"""The task to do next: the first unfinished one after `after` (or the first
	unfinished one, from the bid page), then any earlier unfinished one, then
	Review. A finished task is never walked through."""
	prep = _preparation(nav)
	keys = [row["key"] for row in prep]
	start = keys.index(after) + 1 if after in keys else 0
	for row in prep[start:] + prep[:start]:
		if row["status"] != COMPLETE and row["key"] != after:
			return row["key"]
	return REVIEW


def _by_key(nav: list[dict[str, Any]], key: str) -> dict[str, Any]:
	return next(row for row in nav if row["key"] == key)


def footer(nav: list[dict[str, Any]], current: str, base: str, hand_over: list[str] | None = None) -> dict[str, Any]:
	"""Save and continue, naming the task it leads to. The button does what it says:
	it never promises Review while this task is itself unfinished (Review would only
	send the bidder straight back), so when no other task is left it says Save and
	stays here, where the page shows what is missing. When the preparer has finished
	and someone else must sign, there is nothing further for them to do: it says
	Save and finish and returns to the bid page, which says who signs."""
	key = next_key(nav, current)
	if key == REVIEW and current != REVIEW and _by_key(nav, current)["status"] != COMPLETE:
		return {"save_label": "Save", "next_href": f"{base}/{current}", "stays": True}
	if key == REVIEW and handed_over(nav, hand_over):
		return {"save_label": "Save and finish", "next_href": base}
	return {"save_label": f"Save and continue to {short_name(_by_key(nav, key))}", "next_href": f"{base}/{key}"}


def _hint(nav: list[dict[str, Any]], row: dict[str, Any], hand_over: list[str] | None = None) -> str:
	"""What hovering a step says: its state, and for Review whether it is ready, or who signs."""
	if row["key"] == REVIEW and handed_over(nav, hand_over):
		return _signs(hand_over)
	if row["key"] == REVIEW and row["status"] != COMPLETE:
		return "Not ready: finish the other tasks first"
	return row["status"]


def step(nav: list[dict[str, Any]], current: str, base: str, hand_over: list[str] | None = None) -> dict[str, Any]:
	"""A task page's place in the bid: its number, its neighbours in the fixed
	order, and the whole row of tasks with their states."""
	index = next(i for i, row in enumerate(nav) if row["key"] == current)
	link = lambda row: {"label": short_name(row), "href": f"{base}/{row['key']}"}  # noqa: E731
	return {
		"number": index + 1, "of": len(nav), "label": nav[index]["label"],
		"previous": link(nav[index - 1]) if index > 0 else None,
		"next": link(nav[index + 1]) if index < len(nav) - 1 else None,
		"tasks": [
			{"number": i + 1, "key": row["key"], "label": row["label"], "short": short_name(row), "status": row["status"], "hint": _hint(nav, row, hand_over), "tone": TONES.get(row["status"], "draft"), "href": f"{base}/{row['key']}", "current": row["key"] == current}
			for i, row in enumerate(nav)
		],
	}


def rows(nav: list[dict[str, Any]], base: str, hand_over: list[str] | None = None) -> list[dict[str, Any]]:
	"""The bid page's task rows: numbered, one marked Next with the only primary
	action, each action worded by the task's state (Start, Continue, Review). When
	the preparer has finished and someone else must sign, no row is Next and Review
	is only a view that says who signs."""
	waiting = handed_over(nav, hand_over)
	upcoming = None if waiting else next_key(nav)
	out = []
	for i, row in enumerate(nav, start=1):
		is_next = row["key"] == upcoming
		note = {}
		if row["key"] == REVIEW:
			if waiting:
				action, note = {"label": "View", "primary": False}, {"note": _signs(hand_over)}
			else:
				action = {"label": "Review bid", "primary": True} if row["status"] == COMPLETE else {"label": "View", "primary": False}
		elif row["status"] == COMPLETE:
			action = {"label": "Review", "primary": False}
		else:
			action = {"label": "Start" if row["status"] == "Not started" else "Continue", "primary": is_next}
		out.append({**row, "number": i, "next": is_next, **note, "action": {**action, "href": f"{base}/{row['key']}"}})
	return out
