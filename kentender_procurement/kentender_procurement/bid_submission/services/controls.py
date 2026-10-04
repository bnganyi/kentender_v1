# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The released response controls (BDS-CHG-001 v0.8 §4.4.3; STD-TPL-001
§8.2): one canonical form per control, so the server stores and compares the
same value whatever the browser sent. `canonical(control, raw, parameters)`
returns `(value, None)`, `(None, None)` for "not answered", or
`(None, problem)` when the input cannot be read as that control: a message, or for
a table `{"table": [message], "rows": {position: {column: message}}}` (`flatten`
turns either into field errors). Range and
option checks are the named validations' job (`validation.py`)."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from frappe.utils import cstr

Problem = "str | dict[str, Any] | None"
Result = tuple[Any, Problem]
_BLANK = (None, None)


def _text(raw) -> str:
	return cstr(raw if raw is not None else "").strip()


def _confirmation(raw, _params) -> Result:
	if raw is True or _text(raw).lower() in ("true", "1", "yes"):
		return True, None
	if raw in (None, False, "") or _text(raw).lower() in ("false", "0"):
		return _BLANK
	return None, "Tick the box to confirm."


def _yes_no(raw, _params) -> Result:
	text = _text(raw)
	if not text:
		return _BLANK
	return (text, None) if text in ("Yes", "No") else (None, "Choose Yes or No.")


def _single_choice(raw, _params) -> Result:
	text = _text(raw)
	return (text, None) if text else _BLANK


def _multi_select(raw, _params) -> Result:
	if raw in (None, "", []):
		return _BLANK
	if not isinstance(raw, (list, tuple)):
		return None, "Choose from the listed options."
	out: list[str] = []
	for item in raw:
		text = _text(item)
		if text and text not in out:
			out.append(text)
	return (out, None) if out else _BLANK


def _short_text(raw, _params) -> Result:
	text = _text(raw)
	if not text:
		return _BLANK
	return (None, "Keep this to one line.") if "\n" in text or "\r" in text else (text, None)


def _long_text(raw, _params) -> Result:
	text = "\n".join(line.rstrip() for line in _text(raw).replace("\r\n", "\n").split("\n"))
	return (text, None) if text else _BLANK


def _integer(raw, _params) -> Result:
	if isinstance(raw, bool):
		return None, "Enter a whole number."
	if isinstance(raw, int):
		return raw, None
	text = _text(raw)
	if not text:
		return _BLANK
	return (int(text), None) if re.fullmatch(r"-?\d+", text) else (None, "Enter a whole number.")


def _decimal(raw, params) -> Result:
	text = _text(raw).replace(",", "")
	if not text:
		return _BLANK
	try:
		number = Decimal(text)
	except InvalidOperation:
		return None, "Enter a number."
	if not number.is_finite():
		return None, "Enter a number."
	scale = int((params or {}).get("scale", 2))
	quantum = Decimal(1).scaleb(-scale)
	if number != number.quantize(quantum):
		return None, f"Use at most {scale} decimal places."
	return str(number.quantize(quantum)), None


def _date(raw, _params) -> Result:
	text = _text(raw)
	if not text:
		return _BLANK
	try:
		return date.fromisoformat(text).isoformat(), None
	except ValueError:
		return None, "Enter a date as YYYY-MM-DD."


def _evidence(raw, _params) -> Result:
	"""Bid evidence identities; the service checks that each is this bid's own
	accepted file for this requirement."""
	if raw in (None, "", []):
		return _BLANK
	if not isinstance(raw, (list, tuple)):
		return None, "Choose uploaded files."
	out = [_text(item) for item in raw if _text(item)]
	return (list(dict.fromkeys(out)), None) if out else _BLANK


def _ports(raw, _params) -> Result:
	if raw in (None, "", []):
		return _BLANK
	if not isinstance(raw, (list, tuple)):
		return None, "Add each port type and how many."
	rows = []
	for item in raw:
		if not isinstance(item, dict):
			return None, "Add each port type and how many."
		port = _text(item.get("port_type"))
		count, error = _integer(item.get("count"), {})
		if not port or error or count is None or count < 1:
			return None, "Each port needs a type and a count of at least 1."
		rows.append({"port_type": port, "count": count})
	return rows, None


def _row_group(raw, params) -> Result:
	"""A bounded table (release 1.4): rows in column order, blank rows dropped. The
	table's own rules (minimum rows, totals) are its named validation's job."""
	from kentender_core.utils import row_tables

	if raw in (None, "", []):
		return _BLANK
	result = row_tables.normalise(params["columns"], raw, maximum_rows=int(params.get("maximum_rows", row_tables.MAX_ROWS)))
	if result.problems:
		return None, result.problems
	return (result.rows, None) if result.rows else _BLANK


def describe_rows(columns: list[dict[str, Any]], rows: Any) -> str:
	"""A table's rows as one line for a summary: each row's cells in column order, rows
	separated by a semicolon (the Review page and the receipt summary)."""
	if not isinstance(rows, list):
		return _text(rows)
	return "; ".join(" · ".join(_text(row.get(c["key"])) for c in columns if _text(row.get(c["key"]))) for row in rows if isinstance(row, dict))


def flatten(handle: str, problem: Problem) -> dict[str, str]:
	"""Field errors for one field: its own message, and `handle.position.column` for a table cell."""
	if isinstance(problem, str):
		return {handle: problem}
	out: dict[str, str] = {}
	if problem.get("table"):
		out[handle] = " ".join(problem["table"])
	for position, cells in (problem.get("rows") or {}).items():
		for column, message in cells.items():
			out[f"{handle}.{position}.{column}"] = message
	return out


CANONICALISERS: dict[str, Callable[[Any, dict], Result]] = {
	"CTL-CONFIRMATION": _confirmation,
	"CTL-YES-NO": _yes_no,
	"CTL-SINGLE-CHOICE": _single_choice,
	"CTL-MULTI-SELECT": _multi_select,
	"CTL-SHORT-TEXT": _short_text,
	"CTL-LONG-TEXT": _long_text,
	"CTL-INTEGER": _integer,
	"CTL-DECIMAL": _decimal,
	"CTL-MONEY": _decimal,
	"CTL-DATE": _date,
	"CTL-EVIDENCE-REFERENCE": _evidence,
	"CTL-PORTS-LIST": _ports,
	"CTL-ROW-GROUP": _row_group,
}

#: What the portal renders; never a released control identity (plan D11).
KINDS: dict[str, str] = {
	"CTL-CONFIRMATION": "confirmation", "CTL-YES-NO": "yes_no", "CTL-SINGLE-CHOICE": "single_choice", "CTL-MULTI-SELECT": "multi_select",
	"CTL-SHORT-TEXT": "short_text", "CTL-LONG-TEXT": "long_text", "CTL-INTEGER": "integer", "CTL-DECIMAL": "decimal", "CTL-MONEY": "money",
	"CTL-DATE": "date", "CTL-EVIDENCE-REFERENCE": "evidence", "CTL-PORTS-LIST": "ports",
	"CTL-ROW-GROUP": "row_group",
}


def canonical(control: str, raw, parameters: dict | None = None) -> Result:
	fn = CANONICALISERS.get(control)
	if fn is None:
		raise KeyError(f"No canonicaliser for released control {control!r}")
	return fn(raw, parameters or {})
