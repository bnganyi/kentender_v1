# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The dead-end rule for a built screen (CM-CHG-001 v0.8 sections 6.3 and 10.1A; KT-STD-001 3B.7; plan Phase 10, tracker CM8-1002).

A person must never be left on a screen that tells them what to do and gives them no way to do it, or that says they are blocked without saying who clears it, or that says someone else is acting without naming them.
`problems(board)` reads a **built board** (what the server sends the browser) and returns every way it would strand its reader; empty means sound. It mirrors `kentender_core.services.next_step.problems`, which judges the
shared answer, on the shape the board gives that answer: a "your turn" needs a primary action that exists in the board's actions (an action that is only drawn, with nothing behind it, is a dead end too); a blocked step
needs a fix that goes somewhere and a named holder; a wait needs its holder named; and every secondary action the board draws must do something."""

from __future__ import annotations

from typing import Any

#: the next-step kinds a board draws (kit.turn / wait / done / blk) and what each must carry
TURN, WAIT, DONE, BLOCKED = "turn", "wait", "done", "blk"


def _label(item: Any) -> str:
	text = str(item or "")
	return text[1:] if text.startswith("-") else text


def problems(board: dict[str, Any]) -> list[str]:
	"""Every way this board strands its reader. Empty means sound."""
	out: list[str] = []
	where = f"{board.get('id')}"
	actions = board.get("actions") or {}
	step = board.get("next")
	primary = board.get("p") or ""
	if primary and primary not in actions:
		out.append(f"{where}: the primary action {primary!r} is drawn but does nothing")
	for item in board.get("s2") or []:
		label = _label(item)
		if str(item).startswith("-"):  # a drawn-but-unavailable action carries its reason on the page (the design's leading dash)
			continue
		if label not in actions:
			out.append(f"{where}: the action {label!r} is drawn but does nothing")
	if not step:
		return out
	kind = step.get("k")
	if not step.get("h"):
		out.append(f"{where}: a {kind} step without a headline")
	if kind == TURN:
		if not (primary or any(_label(i) in actions and actions[_label(i)].get("do") in ("command", "dialog", "route", "tab") for i in board.get("s2") or [])):
			out.append(f"{where}: your turn ({step.get('h')!r}) with no action to take it")
	elif kind == BLOCKED:
		fixes = step.get("fixes") or []
		if not fixes:
			out.append(f"{where}: blocked ({step.get('h')!r}) without a fix")
		for fix in fixes:
			if fix not in actions:
				out.append(f"{where}: the fix {fix!r} goes nowhere")
		if not step.get("s"):
			out.append(f"{where}: blocked ({step.get('h')!r}) without the person who clears it")
	elif kind == WAIT:
		if not (step.get("s") or "").strip():
			out.append(f"{where}: waiting ({step.get('h')!r}) without naming who")
	return out


def assert_sound(case, board: dict[str, Any], who: str = "") -> None:
	found = problems(board)
	case.assertEqual(found, [], f"{who or 'the reader'} is stranded: {found}")
