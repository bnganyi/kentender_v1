"""The record picker's two endpoints, over :mod:`kentender_core.services.record_picker`.

Explicit signatures (no ``**kwargs``) so Frappe filters the transport fields (``cmd``,
``csrf_token``) out of the call itself, and there is no actor argument anywhere: the actor is the
session user, and each source's provider decides what that user may see."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import record_picker


@frappe.whitelist()
def search(source: str, query: str | None = None, context: str | dict | None = None, recent: str | list | None = None, limit: int | str = 20) -> dict[str, Any]:
	"""A page of matches for one registered source: ``{"rows", "total", "limit", "typed"}``."""
	return record_picker.search(source, query, context, recent, limit)


@frappe.whitelist()
def resolve(source: str, ids: str | list | None = None, context: str | dict | None = None) -> dict[str, Any]:
	"""The rows for ids already chosen, so a saved choice shows its name: ``{"rows"}``."""
	return record_picker.resolve(source, ids, context)
