# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The named, code-owned validations and rules of the released product profile
(BDS-CHG-001 v0.8 §4.4.2 "Validation", §4.4.5; STD-TPL-001 §8.4). Each takes
only its published parameters and a canonical value (`controls.py`); none
runs an expression. `check()` returns the bidder-facing message or None.
`rule_holds()` evaluates a required or visibility rule over the values of
the same response group."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Callable

from frappe.utils import cstr

from kentender_procurement.bid_submission.services.labels import date_label


def _none(_params, _value):
	return None


def _confirmed(_params, value):
	return None if value is True else "Tick the box to confirm."


def _text_length(params, value):
	length = len(cstr(value))
	low, high = int(params.get("min_length", 0)), int(params.get("max_length", 10**9))
	if length < low:
		return f"Enter at least {low} characters."
	if length > high:
		return f"Keep this to {high:,} characters or fewer."
	return None


def _integer_range(params, value):
	if "minimum" in params and value < int(params["minimum"]):
		return f"Enter {int(params['minimum']):,} or more."
	if "maximum" in params and value > int(params["maximum"]):
		return f"Enter {int(params['maximum']):,} or less."
	return None


def _decimal_range(params, value):
	number = Decimal(cstr(value))
	if "minimum" in params and number < Decimal(cstr(params["minimum"])):
		return f"Enter {Decimal(cstr(params['minimum'])):,} or more."
	if "maximum" in params and number > Decimal(cstr(params["maximum"])):
		return f"Enter {Decimal(cstr(params['maximum'])):,} or less."
	return None


def _money(params, value):
	number = Decimal(cstr(value))
	currency = cstr(params.get("currency"))
	low = Decimal(cstr(params["minimum"])) if params.get("minimum") not in (None, "") else None
	high = Decimal(cstr(params["maximum"])) if params.get("maximum") not in (None, "") else None
	if low is not None and high is not None and low == high and number != low:
		return f"Enter exactly {currency} {low:,.2f}."
	if low is not None and number < low:
		return f"Enter {currency} {low:,.2f} or more."
	if high is not None and number > high:
		return f"Enter {currency} {high:,.2f} or less."
	return None


def _date_range(params, value):
	day = date.fromisoformat(value)
	if params.get("not_before") and day < date.fromisoformat(cstr(params["not_before"])):
		return f"Enter {date_label(params['not_before'])} or later."
	if params.get("not_after") and day > date.fromisoformat(cstr(params["not_after"])):
		return f"Enter {date_label(params['not_after'])} or earlier."
	return None


def _option_in_list(params, value):
	return None if value in (params.get("options") or []) else "Choose one of the listed options."


def _options_subset(params, value):
	allowed = params.get("options") or []
	return None if all(v in allowed for v in value) else "Choose only from the listed options."


def _ports(params, value):
	allowed = params.get("port_options") or []
	types = [row["port_type"] for row in value]
	if any(t not in allowed for t in types):
		return "Choose port types from the list."
	if len(set(types)) != len(types):
		return "List each port type once, with its total count."
	if any(not isinstance(row.get("count"), int) or isinstance(row.get("count"), bool) or row["count"] < 1 for row in value):
		return "Enter how many ports of each type, from 1."
	return None


def _evidence_count(params, value):
	count = len(value or [])
	low, high = int(params.get("minimum", 0)), int(params.get("maximum", 10**6))
	if count < low:
		return f"Add at least {low} file{'s' if low != 1 else ''}."
	if count > high:
		return f"Add no more than {high} file{'s' if high != 1 else ''}."
	return None


def _row_group(params, value):
	"""The table's own rules over rows already in canonical form: the minimum number
	of rows and any total ("shares add up to 100")."""
	from kentender_core.utils import row_tables

	result = row_tables.normalise(params["columns"], value, minimum_rows=int(params.get("minimum_rows", 0)), maximum_rows=int(params.get("maximum_rows", row_tables.MAX_ROWS)), totals=params.get("totals") or [])
	return " ".join((result.problems.get("table") or [])) or None


VALIDATIONS: dict[str, Callable[[dict, Any], "str | None"]] = {
	"VAL-NONE": _none,
	"VAL-CONFIRMED": _confirmed,
	"VAL-TEXT-LENGTH": _text_length,
	"VAL-INTEGER-RANGE": _integer_range,
	"VAL-DECIMAL-RANGE": _decimal_range,
	"VAL-MONEY": _money,
	"VAL-DATE-RANGE": _date_range,
	"VAL-OPTION-IN-LIST": _option_in_list,
	"VAL-OPTIONS-SUBSET": _options_subset,
	"VAL-PORTS": _ports,
	"VAL-EVIDENCE-COUNT": _evidence_count,
	"VAL-ROW-GROUP": _row_group,
}


def check(validation_id: str, parameters: dict | None, value) -> "str | None":
	fn = VALIDATIONS.get(validation_id)
	if fn is None:
		raise KeyError(f"No implementation for released validation {validation_id!r}")
	return fn(parameters or {}, value)


def _equals(rule: dict, values: dict) -> bool:
	return values.get(rule.get("field_key")) == rule.get("value")


def _any_equals(rule: dict, values: dict) -> bool:
	return any(values.get(key) == rule.get("value") for key in rule.get("field_keys") or [])


RULES: dict[str, Callable[[dict, dict], bool]] = {
	"RQ-ALWAYS": lambda _r, _v: True,
	"RQ-NEVER": lambda _r, _v: False,
	"RQ-WHEN-FIELD-EQUALS": _equals,
	"RQ-WHEN-ANY-FIELD-EQUALS": _any_equals,
	"VS-ALWAYS": lambda _r, _v: True,
	"VS-WHEN-FIELD-EQUALS": _equals,
	"VS-WHEN-ANY-FIELD-EQUALS": _any_equals,
}


def rule_holds(rule: dict | None, group_values: dict) -> bool:
	"""`group_values` maps the same group's field keys to canonical values."""
	rule = rule or {"rule_id": "VS-ALWAYS"}
	fn = RULES.get(rule.get("rule_id"))
	if fn is None:
		raise KeyError(f"No implementation for released rule {rule.get('rule_id')!r}")
	return fn(rule, group_values)
