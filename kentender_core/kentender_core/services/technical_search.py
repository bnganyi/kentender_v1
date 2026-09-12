"""AUTH-ADR-001 §10 / §8 — technical-only, read-only cross-app record search.

Administrator and System Manager ("technical" users, per
`kentender_core.services.authorization.is_technical`) can look up any
KenTender record by its business reference or title, from one place,
without knowing which app or DocType owns it. This module owns no data of
its own: each app publishes its own set of searchable references through the
`kt_technical_reference_resolvers` hook (a list of dotted paths to a
zero-argument function returning a list of resolver dicts), and this module
only aggregates, filters and ranks what those resolvers report.

Every public function is guarded by `require_technical`, which raises a
masked `frappe.DoesNotExistError` for a non-technical caller rather than a
`frappe.PermissionError` — per §10, the existence of this page must not be
confirmed to a caller who is not entitled to use it.
"""

from __future__ import annotations

from typing import Any, Callable

import frappe

from kentender_core.services.authorization import is_technical

HOOK_NAME = "kt_technical_reference_resolvers"

# A resolver dict, published by an app's hooks.py:
#   {
#       "doctype": "Departmental Need",
#       "label": "Departmental Need",
#       "reference_field": "need_reference",
#       "title_field": "title",
#       "status_field": "current_state",   # or None
#       "route": callable(name) -> list[str],
#   }
Resolver = dict[str, Any]


def _resolvers() -> list[Resolver]:
	resolvers: list[Resolver] = []
	for dotted_path in frappe.get_hooks(HOOK_NAME):
		fn: Callable[[], list[Resolver]] = frappe.get_attr(dotted_path)
		resolvers.extend(fn() or [])
	return resolvers


def require_technical(user: str | None = None) -> str:
	"""AUTH-ADR-001 §10 — a non-technical caller gets a masked not-found,
	never a permission-error that would confirm this surface's existence."""
	user = user or frappe.session.user
	if not is_technical(user):
		raise frappe.DoesNotExistError("Not found")
	return user


def _fields(resolver: Resolver) -> list[str]:
	fields = ["name", resolver["reference_field"]]
	if resolver.get("title_field"):
		fields.append(resolver["title_field"])
	if resolver.get("status_field"):
		fields.append(resolver["status_field"])
	return fields


def _row(resolver: Resolver, match: dict[str, Any]) -> dict[str, Any]:
	title_field = resolver.get("title_field")
	status_field = resolver.get("status_field")
	name = match["name"]
	return {
		"reference": match.get(resolver["reference_field"]),
		"record_type": resolver["label"],
		"doctype": resolver["doctype"],
		"name": name,
		"title": match.get(title_field) if title_field else None,
		"status": match.get(status_field) if status_field else None,
		"route": resolver["route"](name),
	}


def search(query: str = "", limit: int = 25, user: str | None = None) -> list[dict[str, Any]]:
	"""Reference-or-title match across every published resolver.

	Exact (case-insensitive) reference matches sort first, then by record
	type, then by reference. Capped at `limit` (default and max 25)."""
	require_technical(user)
	q = (query or "").strip()
	if not q:
		return []
	limit = max(1, min(int(limit or 25), 25))

	rows: list[dict[str, Any]] = []
	for resolver in _resolvers():
		reference_field = resolver["reference_field"]
		title_field = resolver.get("title_field")
		match_filters = [[reference_field, "like", f"%{q}%"]]
		if title_field:
			match_filters.append([title_field, "like", f"%{q}%"])
		matches = frappe.get_all(
			resolver["doctype"],
			or_filters=match_filters,
			fields=_fields(resolver),
			ignore_permissions=False,
			limit_page_length=limit,
		)
		rows.extend(_row(resolver, match) for match in matches)

	q_fold = q.casefold()

	def sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
		reference = row["reference"] or ""
		exact = 0 if reference.casefold() == q_fold else 1
		return (exact, row["record_type"] or "", reference)

	rows.sort(key=sort_key)
	return rows[:limit]


def resolve(reference: str, user: str | None = None) -> dict[str, Any] | None:
	"""Exact match on `reference_field` across every published resolver;
	the first hit wins (resolver iteration order, not ranked)."""
	require_technical(user)
	ref = (reference or "").strip()
	if not ref:
		return None
	for resolver in _resolvers():
		matches = frappe.get_all(
			resolver["doctype"],
			filters=[[resolver["reference_field"], "=", ref]],
			fields=_fields(resolver),
			ignore_permissions=False,
			limit_page_length=1,
		)
		if matches:
			return _row(resolver, matches[0])
	return None
