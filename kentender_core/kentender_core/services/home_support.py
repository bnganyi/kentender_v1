"""HOME-CHG-001 v0.6 — helpers for owner providers.

Core calls a provider once per region, so a provider that scans its open cases
would scan five times per read. `memo` keeps one scan for the length of one
Home read: `home_workspace.get_workspace` calls `reset()` first, so nothing
outlives a read and no stale row can be shown (the page never serves cached
work past a permission change, HOME §7).
"""

from __future__ import annotations

from typing import Any, Callable

import frappe


def reset() -> None:
	frappe.local.home_memo = {}


def memo(key: str, build: Callable[[], Any], *, user: str | None = None) -> Any:
	cache = getattr(frappe.local, "home_memo", None)
	if cache is None:
		cache = frappe.local.home_memo = {}
	slot = (user or frappe.session.user, key)
	if slot not in cache:
		cache[slot] = build()
	return cache[slot]
