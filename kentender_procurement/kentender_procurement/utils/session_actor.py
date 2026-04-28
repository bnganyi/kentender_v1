# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""Safe optional “run as actor” for HTTP-bound code paths.

Frappe's ``frappe.set_user(username)`` sets ``frappe.local.session.user`` **and**
``frappe.local.session.sid`` to ``username`` (see ``frappe/__init__.py``).

A common helper pattern::

    try:
        if actor:
            frappe.set_user(actor)
        return fn()
    finally:
        frappe.set_user(prev)

always executes ``frappe.set_user(prev)``. That **replaces the real browser
session id** (a hash stored in the ``sid`` cookie) with the user's login
name. The response then emits ``Set-Cookie: sid=<email>``, the next request
cannot resume the session, and the user is treated as **Guest** — Desk shows
“Method Not Allowed / … is not whitelisted” for ordinary whitelisted methods.

This module restores **user and sid** without calling ``frappe.set_user`` for
the restore path.
"""

from __future__ import annotations

from typing import Callable, TypeVar

import frappe

T = TypeVar("T")


def with_optional_user_actor(actor: str | None, fn: Callable[[], T]) -> T:
	"""Run ``fn`` as ``actor`` if that User exists; otherwise run as current user.

	On exit, restores ``frappe.local.session.user`` and ``.sid`` to their
	pre-switch values and clears permission caches (mirrors ``set_user`` side
	effects except **does not** wipe ``form_dict`` — the HTTP request is still
	in flight).
	"""
	act = (actor or "").strip()
	if not act or not frappe.db.exists("User", act):
		return fn()

	prev_user = frappe.session.user
	prev_sid = frappe.session.sid
	try:
		frappe.set_user(act)
		return fn()
	finally:
		frappe.local.session.user = prev_user
		frappe.local.session.sid = prev_sid
		frappe.local.cache = {}
		frappe.local.jenv = None
		frappe.local.role_permissions = {}
		frappe.local.new_doc_templates = {}
		frappe.local.user_perms = None
