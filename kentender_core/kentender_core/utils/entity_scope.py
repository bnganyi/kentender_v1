"""Entity scope and permission helpers (Phase G — stubs).

Future: resolve procuring entity from User / role / assignment records and apply
`procuring_entity` filters to ORM queries. Phase G intentionally does not enforce access.
"""

from __future__ import annotations

from typing import Any


def get_user_entity(user: str | None = None) -> str | None:
	"""Return the procuring entity name for *user* (User.name).

	Stub: returns ``None`` until User (or related) metadata carries entity scope.
	When *user* is omitted, ``frappe.session.user`` is the implied context only for docs.
	"""
	return None


def get_user_departments(user: str | None = None) -> list[str]:
	"""Return Procuring Department names (or IDs) visible to *user*.

	Stub: returns an empty list until department membership is modeled.
	"""
	return []


def filter_by_entity(query: Any, entity: str | None) -> Any:
	"""Placeholder: narrow *query* to rows for *entity* (e.g. ``procuring_entity`` column).

	Returns *query* unchanged. Callers may chain the result in later phases.
	"""
	return query
