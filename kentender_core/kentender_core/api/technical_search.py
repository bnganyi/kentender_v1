"""AUTH-ADR-001 §10 — whitelisted endpoints for Technical record search.

Thin wrappers over :mod:`kentender_core.services.technical_search`. Every
authority check (technical status), search and ranking rule lives in the
service; nothing here trusts a client-supplied value as authority.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import technical_search


@frappe.whitelist()
def search_technical_records(query: str = "", limit: int | str = 25) -> list[dict[str, Any]]:
	return technical_search.search(query=query or "", limit=int(limit or 25))


@frappe.whitelist()
def resolve_technical_reference(reference: str = "") -> dict[str, Any] | None:
	return technical_search.resolve(reference=reference or "")
