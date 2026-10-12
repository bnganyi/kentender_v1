# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The appointment reference (EVL-CHG-001 v0.7 §3; AUTH-ADR-001 v1.12 not
involved). Nobody types it: the server generates it when an appointment action
commits, from the tender's own reference, under the case's row lock, so it is
unique, never reused and leaves no gap when an action is refused.

    committee      {entity}/EVAL/{number}/{year}
    replacement    {committee reference}-R{n}
    secretary      {entity}/EVAL/SEC/{number}/{year}      (a reassignment: -R{n})

`entity`, `year` and `number` come from the tender reference
`TND-{entity}-{year}-{number}`; the number is shown with at least three
digits. A tender reference that does not follow that form falls back to the
reference itself, so a reference is always produced."""

from __future__ import annotations

import re

from frappe.utils import cint, cstr

_TENDER = re.compile(r"^TND-([A-Z0-9]+)-(\d{4})-(\d+)$")


def _parts(tender_reference: str) -> tuple[str, str, str]:
	match = _TENDER.match(cstr(tender_reference).strip().upper())
	if match:
		entity, year, number = match.groups()
		return entity, year, f"{cint(number):03d}"
	cleaned = re.sub(r"[^A-Z0-9-]+", "-", cstr(tender_reference).strip().upper()).strip("-") or "TENDER"
	return "", "", cleaned


def committee(tender_reference: str) -> str:
	entity, year, number = _parts(tender_reference)
	return f"{entity}/EVAL/{number}/{year}" if entity else f"EVAL/{number}"


def replacement(tender_reference: str, count: int) -> str:
	return f"{committee(tender_reference)}-R{cint(count)}"


def secretary(tender_reference: str, count: int = 0) -> str:
	entity, year, number = _parts(tender_reference)
	base = f"{entity}/EVAL/SEC/{number}/{year}" if entity else f"EVAL/SEC/{number}"
	return f"{base}-R{cint(count)}" if count else base
