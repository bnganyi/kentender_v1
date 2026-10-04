"""KT-STD-001 v1.8 §3B — the shared shape of workflow guidance.

Every record read returns one ``next_step`` answer for the signed-in actor
and, where the record sits on the process spine, one ``journey`` for the
tracker (§2.9). This module owns only the *shape*: guard results that carry
their reason (§3B.1), the answer and its fixed precedence (§3B.2), the
technical-reader rule (§3B.6), the journey markers (§2.9.2) and a validator
the dead-end test uses (§3B.7). Each module owns its own states, stages,
holders, blockers, fixes and wording; nothing here knows a module.

Everything is a plain dict so a read can return it unchanged and the shared
Vue components (``kt_industry_guidance.bundle.js``) can draw it without a
client-side status map (KT-STD-001 v1.8 §10: next-step wording is never
computed in the client).
"""

from __future__ import annotations

from typing import Any, Iterable

from frappe.utils import cstr

KIND_YOUR_TURN = "your_turn"
KIND_BLOCKED = "your_turn_blocked"
KIND_WAITING = "waiting"
# KT-STD-001 v1.10 §2.9.1 — a fixed future event held by the system (for
# example a deadline); never a person to wait on (BOP-CHG-001 v0.10 §5).
KIND_SCHEDULED = "timed"
KIND_DONE = "done"
KIND_NOT_INVOLVED = "not_involved"

# §3B.2 — fixed precedence: an available action, then a blocked action,
# then waiting, then done, then not involved.
PRECEDENCE = (KIND_YOUR_TURN, KIND_BLOCKED, KIND_WAITING, KIND_SCHEDULED, KIND_DONE, KIND_NOT_INVOLVED)
TURN_KINDS = frozenset({KIND_YOUR_TURN, KIND_BLOCKED})

# §2.9.1 — the words the boards draw before each headline ("Waiting on
# someone" is KT-STD-001 v1.8 §2.9.1's own name for the kind; TPR-CHG-001
# v0.12 plan OD-1 made the shared component say it for every module).
KIND_LABELS = {
	KIND_YOUR_TURN: "Your turn",
	KIND_BLOCKED: "Your turn, blocked",
	KIND_WAITING: "Waiting on someone",
	KIND_SCHEDULED: "Scheduled",
	KIND_DONE: "Done",
	KIND_NOT_INVOLVED: "",
}

# How a fix is carried out. ``command`` runs a governed command (a hand-off
# such as a budget revision request); ``route`` opens a page where the named
# responsibility can act; ``focus`` moves focus to a region of the same page;
# ``text`` is a recovery the actor cannot perform in the product, stated in
# words only (a setting that only an administrator can complete).
FIX_COMMAND = "command"
FIX_ROUTE = "route"
FIX_FOCUS = "focus"
FIX_TEXT = "text"
FIX_KINDS = frozenset({FIX_COMMAND, FIX_ROUTE, FIX_FOCUS, FIX_TEXT})

# The one-line reduced tracker (§2.9.2 rule 5). Each module's approved
# change unit fixes its own wording: Planning (PLN-CHG-001 v1.27) reads
# "Stage {n} of {N}: {label} — {holder}"; Tenders (TPR-CHG-001 v0.12 §10.17)
# reads "{label} · {n} of {N} · {holder}".
REDUCED_STAGE_OF = "stage_of"
REDUCED_POSITION = "position"

MARKER_DONE = "done"
MARKER_CURRENT = "current"
MARKER_BLOCKED = "blocked"
MARKER_NOT_STARTED = "not_started"
MARKER_LABELS = {
	MARKER_DONE: "Done",
	MARKER_CURRENT: "Current",
	MARKER_BLOCKED: "Blocked",
	MARKER_NOT_STARTED: "Not started",
}


# --------------------------------------------------------------------------
# Guards (§3B.1)
# --------------------------------------------------------------------------


def fix(
	label: str,
	*,
	responsibility: str,
	kind: str,
	fix_id: str = "",
	person: str = "",
	target: Any = None,
	primary: bool = False,
) -> dict[str, Any]:
	"""One way to clear a blocker, naming the responsibility that can do it.

	``fix_id`` is the stable handle the screen maps to its own handler (for a
	command) or focus target; ``target`` carries a route list or a region id.
	"""
	if kind not in FIX_KINDS:
		raise ValueError(f"unknown fix kind {kind!r}")
	return {
		"fix_id": cstr(fix_id) or cstr(label),
		"label": cstr(label),
		"responsibility": cstr(responsibility),
		"person": cstr(person),
		"kind": kind,
		"target": target,
		"primary": bool(primary),
	}


def guard(
	allowed: bool,
	*,
	reason_code: str = "",
	message: str = "",
	headline: str = "",
	figures: dict[str, Any] | None = None,
	fixes: Iterable[dict[str, Any]] = (),
	facts: Iterable[tuple[str, str]] = (),
) -> dict[str, Any]:
	"""A guard result: whether the action is available and, if not, why.

	``figures`` are the machine values behind the reason; ``facts`` are the
	few labelled values the blocked block shows beside it (a missing
	setting's Setting / Affected action / Responsible role).

	A refusal without a reason code is a defect (§3B.1), so it cannot be
	built: ``allowed=False`` requires ``reason_code``.
	"""
	if not allowed and not reason_code:
		raise ValueError("a refused guard must carry a reason code (KT-STD-001 v1.8 §3B.1)")
	return {
		"allowed": bool(allowed),
		"reason_code": cstr(reason_code),
		"message": cstr(message),
		"headline": cstr(headline) or cstr(message),
		"figures": dict(figures or {}),
		"fixes": list(fixes),
		"facts": [{"label": cstr(label), "value": cstr(value)} for label, value in facts],
	}


def allowed() -> dict[str, Any]:
	return guard(True)


def combine(*guards: dict[str, Any]) -> dict[str, Any]:
	"""Several guards that must all pass for one action.

	The result is allowed only when every guard is; otherwise it lists every
	refusal together under ``blockers`` (§3B.2: all blockers at once, never
	one at a time) and takes its own code from the first refusal.
	"""
	refused = [g for g in guards if g and not g["allowed"]]
	if not refused:
		return allowed()
	first = refused[0]
	result = guard(
		False,
		reason_code=first["reason_code"],
		message=first["message"],
		headline=first["headline"],
		figures=first["figures"],
		fixes=first["fixes"],
	)
	result["facts"] = first.get("facts") or []
	result["blockers"] = [blocker(g) for g in refused]
	return result


def blocker(g: dict[str, Any]) -> dict[str, Any]:
	"""The part of a refused guard the next-step answer carries."""
	return {
		"reason_code": g["reason_code"],
		"message": g["message"],
		"headline": g["headline"],
		"figures": g["figures"],
		"fixes": g["fixes"],
		"facts": g.get("facts") or [],
	}


def blockers_of(g: dict[str, Any]) -> list[dict[str, Any]]:
	"""Every blocker of a (possibly combined) refused guard, or none."""
	if not g or g["allowed"]:
		return []
	return list(g.get("blockers") or [blocker(g)])


# --------------------------------------------------------------------------
# The answer (§3B.2)
# --------------------------------------------------------------------------


def holder(role: str, people: Iterable[str] = ()) -> dict[str, Any]:
	"""Responsibility and the named people who hold it.

	With no resolvable person the role alone is named (PLN §6.5); the
	display follows the boards: "Josphat Mwangi (Budget Officer)".
	"""
	names = [cstr(p) for p in people if cstr(p)]
	if not names:
		display = cstr(role)
	else:
		display = f"{', '.join(names)} ({role})" if role else ", ".join(names)
	return {"role": cstr(role), "people": names, "display": display}


def since(at: Any, display: str) -> dict[str, Any] | None:
	"""A recorded instant and its site-timezone display (§3). ``None`` when
	nothing was recorded — never a guessed value."""
	if not at or not display:
		return None
	return {"at": cstr(at), "display": cstr(display)}


def answer(
	kind: str,
	*,
	headline: str = "",
	sentence: str = "",
	stage: str = "",
	holder: dict[str, Any] | None = None,
	since: dict[str, Any] | None = None,
	blockers: Iterable[dict[str, Any]] = (),
	fixes: Iterable[dict[str, Any]] = (),
	primary_action: str = "",
) -> dict[str, Any]:
	if kind not in PRECEDENCE:
		raise ValueError(f"unknown next-step kind {kind!r}")
	blockers = list(blockers)
	fixes = list(fixes) or [f for b in blockers for f in b.get("fixes") or []]
	return {
		"kind": kind,
		"label": KIND_LABELS[kind],
		"headline": cstr(headline),
		"sentence": cstr(sentence),
		"stage": cstr(stage),
		"holder": holder,
		"since": since,
		"blockers": blockers,
		"fixes": fixes,
		"primary_action": cstr(primary_action),
	}


def not_involved(stage: str = "") -> dict[str, Any]:
	return answer(KIND_NOT_INVOLVED, stage=stage)


def choose(*candidates: dict[str, Any] | None) -> dict[str, Any]:
	"""The one answer to show when several could apply to a viewer (§3B.2)."""
	present = [c for c in candidates if c]
	if not present:
		return not_involved()
	return min(present, key=lambda c: PRECEDENCE.index(c["kind"]))


def for_viewer(
	result: dict[str, Any],
	*,
	technical: bool,
	reader: dict[str, Any] | None = None,
	allow_technical_turn: bool = False,
) -> dict[str, Any]:
	"""Apply §3B.6: a technical reader never gets Your turn or a fix.

	``reader`` is the answer any other reader of the record would see
	(waiting, done or not involved); it replaces a turn answer. A module
	passes ``allow_technical_turn=True`` only for an exception its owner
	has named (Planning's publication recovery, decision O4).
	"""
	if not technical or allow_technical_turn:
		return result
	if result["kind"] in TURN_KINDS:
		result = reader or not_involved(result["stage"])
		if result["kind"] in TURN_KINDS:
			raise ValueError("a technical reader's fallback answer cannot be a turn")
	stripped = dict(result)
	stripped["fixes"] = []
	stripped["primary_action"] = ""
	stripped["blockers"] = [{**b, "fixes": []} for b in result.get("blockers") or []]
	return stripped


def problems(result: dict[str, Any] | None, *, has_enabled_action: bool = False) -> list[str]:
	"""Why an answer would leave its actor at a dead end (§3B.7 rule 1).

	Empty means the answer is sound: an enabled action, or a named holder
	and a reason. Used by each module's dead-end matrix.
	"""
	if not result:
		return [] if has_enabled_action else ["no next-step answer"]
	kind = result.get("kind")
	out: list[str] = []
	if kind == KIND_YOUR_TURN:
		if not result.get("headline"):
			out.append("your turn without a headline")
		if not (has_enabled_action or result.get("primary_action") or result.get("fixes")):
			# "Your turn" with nothing to press is the dead end §3B.7 forbids
			# (found live 25 Sep 2026: a Budget Officer told to revise a line
			# on a page that offered no way to do it).
			out.append("your turn without an action or a way to act")
	elif kind == KIND_BLOCKED:
		if not result.get("headline"):
			out.append("blocked without a headline")
		if not result.get("blockers"):
			out.append("blocked without any blocker")
		for b in result.get("blockers") or []:
			if not b.get("reason_code"):
				out.append("a blocker without a reason code")
			if not b.get("fixes"):
				out.append(f"blocker {b.get('reason_code')} offers no fix")
	elif kind == KIND_WAITING:
		if not result.get("headline"):
			out.append("waiting without a headline")
		if not (result.get("holder") or {}).get("role"):
			out.append("waiting without a named holder")
	elif kind == KIND_SCHEDULED:
		if not result.get("headline"):
			out.append("scheduled without a headline")
		if result.get("fixes") or result.get("primary_action"):
			out.append("scheduled with an action")
	elif kind == KIND_DONE:
		if not result.get("headline"):
			out.append("done without a headline")
	elif kind == KIND_NOT_INVOLVED:
		pass
	else:
		out.append(f"unknown kind {kind!r}")
	return out


# --------------------------------------------------------------------------
# Journey tracker (§2.9.2)
# --------------------------------------------------------------------------


def journey(
	stages: Iterable[tuple[str, str]],
	*,
	current: str = "",
	blocked: bool = False,
	holder_display: str = "",
	complete: bool = False,
	reduced: bool = False,
	upstream: dict[str, Any] | None = None,
	downstream: dict[str, Any] | None = None,
	reduced_style: str = REDUCED_STAGE_OF,
) -> dict[str, Any]:
	"""One row of a record's own formal stages with one marker each.

	``stages`` is ``[(code, label), …]`` in order. Stages before ``current``
	are Done, ``current`` is Current (or Blocked), later ones Not started;
	``complete`` marks every stage Done (the end state). Only the current
	stage names its holder. ``reduced`` asks for the one-line form
	"Stage {n} of {N}: {label} — {holder}".
	"""
	stages = [(cstr(code), cstr(label)) for code, label in stages]
	codes = [code for code, _label in stages]
	if current and current not in codes:
		raise ValueError(f"unknown stage {current!r}")
	index = codes.index(current) if current else (len(codes) - 1 if complete else -1)
	rows = []
	for position, (code, label) in enumerate(stages):
		if complete or position < index:
			marker = MARKER_DONE
		elif position == index:
			marker = MARKER_BLOCKED if blocked else MARKER_CURRENT
		else:
			marker = MARKER_NOT_STARTED
		rows.append(
			{
				"code": code,
				"label": label,
				"marker": marker,
				"marker_label": MARKER_LABELS[marker],
				"holder": cstr(holder_display) if position == index and not complete else "",
			}
		)
	current_row = rows[index] if 0 <= index < len(rows) else None
	reduced_text = ""
	reduced_parts = None
	if current_row:
		# The reduced line styles the stage label on its own, so its parts are
		# sent too; the client joins them and never composes the wording.
		if reduced_style == REDUCED_POSITION:
			qualifier = " (blocked)" if current_row["marker"] == MARKER_BLOCKED else (" (done)" if current_row["marker"] == MARKER_DONE else "")
			reduced_parts = {
				"prefix": "",
				"label": current_row["label"] + qualifier,
				"suffix": f" · {index + 1} of {len(rows)}" + (f" · {current_row['holder']}" if current_row["holder"] else ""),
			}
		else:
			reduced_parts = {
				"prefix": f"Stage {index + 1} of {len(rows)}: ",
				"label": current_row["label"],
				"suffix": f" — {current_row['holder']}" if current_row["holder"] else "",
			}
		reduced_text = reduced_parts["prefix"] + reduced_parts["label"] + reduced_parts["suffix"]
	return {
		"stages": rows,
		"current": current_row["code"] if current_row else "",
		"reduced_style": reduced_style,
		"reduced": bool(reduced),
		"reduced_text": reduced_text,
		"reduced_parts": reduced_parts,
		"upstream": upstream,
		"downstream": downstream,
	}


def link(label: str, *, kind: str, target: Any = None) -> dict[str, Any]:
	"""The tracker's single upstream or downstream text link (§2.9.2)."""
	if kind not in (FIX_ROUTE, FIX_FOCUS):
		raise ValueError("a tracker link navigates or moves focus; it never mutates")
	return {"label": cstr(label), "kind": kind, "target": target}
