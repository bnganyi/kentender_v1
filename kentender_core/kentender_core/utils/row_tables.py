# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bounded tables of named columns, checked the same way everywhere.

A table is a short list of rows (at most ten) whose cells have one of four
types: text, integer, decimal and choice. The tenderer's business profile on
the supplier Account (partners and directors, with their shares) and the bid's
row-group response (persons with an interest, commission recipients) both use
it, so a table means the same thing on the Account and in the bid. The owner
decisions it carries: a first row may be required and the rest optional; a
blank row is dropped, not an error; a total can be required ("shares add up to
100"); every refusal names the row and the cell so the person can fix it.

Pure Python: no Frappe import. `normalise` returns the canonical rows only
when the table is right; otherwise `rows` is empty and `problems` says what is
wrong, as `{"table": [message, ...], "rows": {position: {column: message}}}`
(a position is the row's place in what was sent, blanks included)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, NamedTuple

TYPES = ("text", "integer", "decimal", "choice")
NUMERIC = ("integer", "decimal")
MAX_COLUMNS = 8
MAX_ROWS = 10
DEFAULT_TEXT = 160
_KEY = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


class Result(NamedTuple):
	rows: list[dict[str, Any]]
	problems: dict[str, Any]

	@property
	def ok(self) -> bool:
		return not self.problems


def _rows(count: int) -> str:
	return f"{count} row" + ("" if count == 1 else "s")


def _blank(value: Any) -> bool:
	return value is None or (isinstance(value, str) and not value.strip())


def _number(value: Any) -> Decimal | None:
	if isinstance(value, bool):
		return None
	try:
		number = Decimal(str(value).strip().replace(",", ""))
	except InvalidOperation:
		return None
	return number if number.is_finite() else None


def _cell(column: dict[str, Any], value: Any) -> tuple[Any, str | None]:
	"""One non-blank cell: its canonical value, or the message that refuses it."""
	kind = column["type"]
	if kind == "text":
		text = " ".join(str(value).split())
		limit = int(column.get("max_length") or DEFAULT_TEXT)
		return (text, None) if len(text) <= limit else (None, f"Use at most {limit} characters.")
	if kind == "choice":
		text = str(value).strip()
		return (text, None) if text in column["options"] else (None, "Choose one of the listed options.")
	number = _number(value)
	if kind == "integer":
		if number is None or number != number.to_integral_value():
			return None, "Enter a whole number."
		value_out: Any = int(number)
	else:
		if number is None:
			return None, "Enter a number."
		scale = int(column.get("scale", 2))
		quantum = Decimal(1).scaleb(-scale)
		if number != number.quantize(quantum):
			return None, f"Use at most {scale} decimal places."
		number = number.quantize(quantum)
		value_out = str(number)
	low, high = column.get("minimum"), column.get("maximum")
	if low is not None and number < Decimal(str(low)):
		return None, f"Enter {low} or more."
	if high is not None and number > Decimal(str(high)):
		return None, f"Enter {high} or less."
	return value_out, None


def normalise(columns: list[dict[str, Any]], raw: Any, *, minimum_rows: int = 0, maximum_rows: int = MAX_ROWS, totals: list[dict[str, Any]] | tuple = ()) -> Result:
	"""The canonical rows (column order, decimals at their scale), or what is wrong."""
	if raw is None:
		raw = []
	if not isinstance(raw, list):
		return Result([], {"table": ["Enter the rows as a list."]})
	if any(not isinstance(item, dict) for item in raw):
		return Result([], {"table": ["Each row must name its cells."]})
	table: list[str] = []
	problems: dict[int, dict[str, str]] = {}
	kept: list[dict[str, Any]] = []
	filled = 0
	for position, item in enumerate(raw):
		if all(_blank(item.get(c["key"])) for c in columns):
			continue  # a blank row is dropped, never an error
		filled += 1
		out: dict[str, Any] = {}
		bad: dict[str, str] = {}
		for column in columns:
			value = item.get(column["key"])
			if _blank(value):
				if column.get("required", True):
					bad[column["key"]] = f"Enter {column['label']}."
				else:
					out[column["key"]] = ""
				continue
			cell, message = _cell(column, value)
			if message:
				bad[column["key"]] = message
			else:
				out[column["key"]] = cell
		if bad:
			problems[position] = bad
		else:
			kept.append(out)
	if filled > maximum_rows:
		table.append(f"Enter at most {_rows(maximum_rows)}.")
	if filled < minimum_rows:
		table.append(f"Add at least {_rows(minimum_rows)}.")
	if not table and not problems:
		by_key = {c["key"]: c for c in columns}
		for total in totals:
			column = by_key[total["column"]]
			scale = int(column.get("scale", 2)) if column["type"] == "decimal" else 0
			added = sum((Decimal(str(r[total["column"]])) for r in kept), Decimal(0))
			if added != Decimal(str(total["equals"])):
				table.append(f"{column['label']} must add up to {total['equals']}; they add up to {added.quantize(Decimal(1).scaleb(-scale))}.")
	found: dict[str, Any] = {}
	if table:
		found["table"] = table
	if problems:
		found["rows"] = problems
	return Result([], found) if found else Result(kept, {})


def check_definition(columns: Any, *, minimum_rows: Any = 0, maximum_rows: Any = MAX_ROWS, totals: Any = ()) -> list[str]:
	"""What is wrong with a table's definition (for the template compiler); empty when it is usable."""
	problems: list[str] = []
	if not isinstance(columns, list) or not columns:
		return ["Define at least one column."]
	if len(columns) > MAX_COLUMNS:
		problems.append(f"Define at most {MAX_COLUMNS} columns.")
	seen: dict[str, dict[str, Any]] = {}
	for column in columns:
		if not isinstance(column, dict):
			problems.append("Each column must be an object.")
			continue
		key = column.get("key")
		if not isinstance(key, str) or not _KEY.match(key):
			problems.append("Column keys are lower-case letters, digits and underscores.")
			continue
		if key in seen:
			problems.append("Column keys must be unique.")
		seen[key] = column
		if not str(column.get("label") or "").strip():
			problems.append(f"Column {key} needs a label.")
		if column.get("type") not in TYPES:
			problems.append(f"Column {key} has an unknown type; use one of {', '.join(TYPES)}.")
		elif column["type"] == "choice" and not (isinstance(column.get("options"), list) and column["options"] and all(isinstance(o, str) and o for o in column["options"])):
			problems.append(f"Column {key} needs a list of options.")
	if not isinstance(maximum_rows, int) or isinstance(maximum_rows, bool) or maximum_rows < 1:
		problems.append("The maximum number of rows must be a whole number of at least 1.")
	elif maximum_rows > MAX_ROWS:
		problems.append(f"A table takes at most {MAX_ROWS} rows.")
	if not isinstance(minimum_rows, int) or isinstance(minimum_rows, bool) or minimum_rows < 0:
		problems.append("The minimum number of rows must be a whole number, 0 or more.")
	elif isinstance(maximum_rows, int) and minimum_rows > maximum_rows:
		problems.append("The minimum number of rows is more than the maximum.")
	for total in totals or ():
		column = seen.get(total.get("column")) if isinstance(total, dict) else None
		if column is None:
			problems.append("A total names an unknown column.")
		elif column.get("type") not in NUMERIC:
			problems.append("A total needs a numeric column.")
		elif _number(total.get("equals")) is None:
			problems.append("A total's 'equals' must be a number.")
	return problems
