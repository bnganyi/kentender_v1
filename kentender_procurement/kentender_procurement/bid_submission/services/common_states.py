# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The BDS-DES-16 common-state catalogue (BDS-CHG-001 v0.8 §10.17; plan
Phase 11, slice 11.15) as the server reads it: the same
`bid_submission/common_states.json` the portal's CommonState renders, so a
state's heading, message and action are written once.

`state(key, **figures)` names a state for a read to hand the page;
`for_code(code)` finds the state a §8 refusal answers to. The §8 message for
each code is the state's heading (held in step by the tests)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

from frappe.utils import cstr

CATALOGUE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common_states.json")


@lru_cache(maxsize=1)
def catalogue() -> dict[str, dict[str, Any]]:
	with open(CATALOGUE, encoding="utf-8") as handle:
		return {entry["key"]: entry for entry in json.load(handle)["states"]}


def state(key: str, *, href: str = "", retry: bool = False, **figures) -> dict[str, Any]:
	"""A state for the page: its key, the figures its message names, where its
	action leads (empty: the page handles the action itself) and whether the
	retry action applies."""
	entry = catalogue()[key]
	return {"key": key, "figures": {name: cstr(value) for name, value in figures.items()}, "href": href, "retry": bool(retry and entry.get("retry_action"))}


def for_code(code: str) -> str:
	"""The state a §8 refusal answers to, or "" when it has none."""
	return next((key for key, entry in catalogue().items() if entry.get("code") == code), "")
