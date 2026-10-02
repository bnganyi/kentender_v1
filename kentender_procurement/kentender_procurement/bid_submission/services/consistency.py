# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Compliance against the offered value (owner decision 2 Oct 2026).

A requirement row asks one fact twice: the bidder's Compliance answer and the
offered value. Nothing in the published definition links them, so a bidder
could say "Do not comply" beside a value that meets the requirement, or
"Comply" beside one that falls short. The published requirement does say what
meets it — a minimum, a maximum, an exact answer, one of a list, every listed
option, a minimum count of each port — so where that can be decided the pair
must agree. A mismatch is a Must fix on both fields. A truthful "Do not comply"
with a value that falls short is left alone (it stays the Review note), and a
free-text requirement is never decided here: only an evaluator can judge it."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from frappe.utils import cstr

COMPLY, DO_NOT_COMPLY = "Comply", "Do not comply"

COMPLY_BUT_SHORT = "Your offered value does not meet this requirement ({requirement}).{shortfall} Choose Do not comply, or change the offered value."
NOT_COMPLY_BUT_MEETS = "Your offered value meets this requirement ({requirement}), so you cannot state that you do not comply. Choose Comply, or change the offered value."
OFFERED_SHORT = "This value does not meet the requirement ({requirement}), but you stated that you comply.{shortfall} Change the value, or choose Do not comply."
OFFERED_MEETS = "This value meets the requirement ({requirement}), but you stated that you do not comply. Change the value, or choose Comply."


def _number(value: Any) -> Decimal | None:
	if isinstance(value, bool):
		return None
	try:
		return Decimal(cstr(value).strip())
	except (InvalidOperation, ValueError):
		return None


def meets(facts: dict[str, Any], offered: Any) -> bool | None:
	"""Whether `offered` meets the published requirement: True, False, or None
	when it cannot be decided (no value, an unreadable value, free text)."""
	if offered in (None, "", []):
		return None
	control, comparison = cstr(facts.get("control")), cstr(facts.get("comparison"))
	required = facts.get("required_value") or {}
	if control in ("INTEGER", "DECIMAL"):
		want, got = _number(required.get("value")), _number(offered)
		if want is None or got is None:
			return None
		if comparison == "Minimum":
			return got >= want
		if comparison == "Maximum":
			return got <= want
		return got == want
	if control == "YES_NO":
		return None if required.get("value") is None else offered == required["value"]
	if control == "SELECT":
		allowed = required.get("values") or ([required["value"]] if required.get("value") is not None else [])
		return offered in allowed if allowed else None
	if control == "MULTI_SELECT":
		needed = required.get("values") or []
		return all(v in offered for v in needed) if needed and isinstance(offered, list) else None
	if control == "PORT_LIST":
		needed = required.get("ports") or []
		if not needed or not isinstance(offered, list):
			return None
		have: dict[str, int] = {}
		for row in offered:
			have[cstr(row.get("port_type"))] = have.get(cstr(row.get("port_type")), 0) + int(row.get("count") or 0)
		return all(have.get(cstr(p.get("port_type")), 0) >= int(p.get("minimum_count") or 0) for p in needed)
	return None  # free text, or a kind this does not know


def describe(facts: dict[str, Any]) -> str:
	"""The requirement as the Tender states it, for the message."""
	display = cstr(facts.get("required_value_display"))
	unit = cstr(facts.get("unit"))
	if unit and display and not display.endswith(unit):
		display = f"{display} {unit}"
	comparison = cstr(facts.get("comparison"))
	if comparison in ("Minimum", "Maximum") and cstr(facts.get("control")) in ("INTEGER", "DECIMAL"):
		return f"{comparison.lower()} {display}"
	return display


def shortfall(facts: dict[str, Any], offered: Any) -> str:
	"""A sentence saying what falls short of the published requirement, so a
	partial answer (one of three required ports) is not read as wholly refused;
	empty when nothing is short or this cannot be said."""
	control = cstr(facts.get("control"))
	required = facts.get("required_value") or {}
	unit = cstr(facts.get("unit"))
	if control in ("INTEGER", "DECIMAL", "YES_NO", "SELECT"):
		return f"You offered {(cstr(offered) + ' ' + unit).strip()}." if offered not in (None, "", []) else ""
	if control == "MULTI_SELECT" and isinstance(offered, list):
		missing = [cstr(v) for v in required.get("values") or [] if v not in offered]
		return f"Not offered: {', '.join(missing)}." if missing else ""
	if control == "PORT_LIST" and isinstance(offered, list):
		have: dict[str, int] = {}
		for row in offered:
			have[cstr(row.get("port_type"))] = have.get(cstr(row.get("port_type")), 0) + int(row.get("count") or 0)
		short = []
		for port in required.get("ports") or []:
			kind, need = cstr(port.get("port_type")), int(port.get("minimum_count") or 0)
			if have.get(kind, 0) < need:
				short.append(f"{kind} ×{need}" if not have.get(kind) else f"{kind} {have[kind]} of {need}")
		return f"Still needed: {', '.join(short)}." if short else ""
	return ""


def contradiction(facts: dict[str, Any], compliance: Any, offered: Any) -> dict[str, str] | None:
	"""The words for each field when the Compliance answer and the offered value
	disagree about whether the requirement is met; None when they agree or this
	cannot be decided."""
	if compliance not in (COMPLY, DO_NOT_COMPLY):
		return None
	met = meets(facts, offered)
	if met is None or (compliance == COMPLY) == met:
		return None
	requirement = describe(facts)
	if compliance == COMPLY:
		missing = shortfall(facts, offered)
		missing = f" {missing}" if missing else ""
		return {"compliance": COMPLY_BUT_SHORT.format(requirement=requirement, shortfall=missing), "offered": OFFERED_SHORT.format(requirement=requirement, shortfall=missing)}
	return {"compliance": NOT_COMPLY_BUT_MEETS.format(requirement=requirement), "offered": OFFERED_MEETS.format(requirement=requirement)}


def meeting_value(facts: dict[str, Any]) -> Any:
	"""A value that meets the published requirement, in the form the field
	takes (for seeds and tests that must fill a bid truthfully); None for free
	text, which only the caller can word."""
	control = cstr(facts.get("control"))
	required = facts.get("required_value") or {}
	if control == "INTEGER":
		return int(_number(required.get("value")))
	if control == "DECIMAL":
		return cstr(required.get("value"))
	if control in ("YES_NO", "SELECT"):
		return required.get("value") if required.get("value") is not None else (required.get("values") or [None])[0]
	if control == "MULTI_SELECT":
		return list(required.get("values") or [])
	if control == "PORT_LIST":
		return [{"port_type": cstr(p.get("port_type")), "count": int(p.get("minimum_count") or 1)} for p in required.get("ports") or []]
	return None
