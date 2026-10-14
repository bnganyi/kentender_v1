# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Read models: audience-projected fields and authority-filtered pages (CM-CHG-001 v0.8 §6.2, plan D11; tracker CM8-311).

A read model declares `FIELDS`, each tagged with the field set it belongs to (`audience.FIELD_SETS`). `project` returns only the fields the reader's
audiences allow, so a field no audience of theirs reaches is never in the answer and cannot be filtered out by the browser. `page` filters the
candidate contracts by authority **before** counting and slicing, so a total never leaks the existence of a contract the reader cannot read."""

from __future__ import annotations

from typing import Any, Iterable

from kentender_contracts.services import audience


def project(fields: dict[str, str], values: dict[str, Any], found: list[audience.Grant]) -> dict[str, Any]:
	"""`fields`: name -> field set. Unknown field sets are a programming error, caught here."""
	unknown = set(fields.values()) - set(audience.FIELD_SETS)
	if unknown:
		raise ValueError(f"unknown field sets {sorted(unknown)}")
	allowed = audience.field_sets(found)
	return {name: values.get(name) for name, field_set in fields.items() if field_set in allowed}


def page(user: str, cases: Iterable[str], *, number: int = 1, size: int = 20, at=None) -> dict[str, Any]:
	"""The cases this user may read, counted and sliced after the authority filter. `rows` carry the case and the audiences that let it through."""
	readable = [(case, audience.readable(user, case, at=at)) for case in cases]
	readable = [(case, found) for case, found in readable if found]
	size = max(1, int(size))
	number = max(1, int(number))
	start = (number - 1) * size
	return {"total": len(readable), "page": number, "page_size": size, "rows": [{"case": case, "audiences": [g.audience for g in found]} for case, found in readable[start:start + size]]}
