"""HOME-CHG-001 v0.6 §6 — who is looking at Home, and what they hold.

Home is for internal users; supplier and public users get the denied state.
A technical reader (Administrator, System Manager, Technical Operator) sees
the orientation without counts and receives no personal business action
solely from that status (§6, KT-STD-001 §3A.6). Home grants no record
permission: this module only describes the viewer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_core.services import authorization
from kentender_core.services.business_role_registry import SCOPE_SITE, scope_type
from kentender_core.services.support_issues import TECHNICAL_OPERATOR


def is_internal(user: str | None) -> bool:
	"""A signed-in System User. Supplier and public accounts are Website Users."""
	if not user or user == "Guest":
		return False
	return frappe.db.get_value("User", user, "user_type") == "System User"


def is_technical_reader(user: str, at: datetime) -> bool:
	"""Administrator and System Manager (AUTH §8), and a Technical Operator,
	whom HOME §6 and §10B treat the same way. A Technical Operator who also
	holds a business responsibility is still a technical reader here: that
	status adds no business action, and the other responsibility's work is
	reached through its own module."""
	return authorization.is_technical(user) or bool(authorization.resolve_assignments(user, TECHNICAL_OPERATOR, at))


_TITLES = {"dr", "prof", "professor", "hon", "mr", "mrs", "ms", "miss", "mx", "eng", "rev", "sir", "madam"}


def greeting_name(full_name: str, first_name: str = "", *, fallback: str = "") -> str:
	"""The name the greeting uses ("Good morning, Peter"): the first word of the full name once leading titles are
	skipped. A seeded user stores "Dr Peter Kimani" as first name "Dr" and last name "Peter Kimani", so the stored
	first name alone is not enough. A name that is only a title stays as it is."""
	words = cstr(full_name or first_name).split()
	while len(words) > 1 and words[0].rstrip(".").lower() in _TITLES:
		words.pop(0)
	return words[0] if words else cstr(fallback)


def first_name(user: str) -> str:
	row = frappe.db.get_value("User", user, ["full_name", "first_name"], as_dict=True) or {}
	return greeting_name(row.get("full_name"), row.get("first_name"), fallback=user)


def _scope_text(row: dict[str, Any]) -> str:
	if row.get("organisation_unit"):
		return cstr(frappe.db.get_value("Organisation Unit", row["organisation_unit"], "unit_name") or row["organisation_unit"])
	return _("site-wide") if scope_type(row["business_role"]) == SCOPE_SITE else ""


def responsibilities(user: str, at: datetime) -> dict[str, Any]:
	"""Every active responsibility with its scope (§5.1 item 2). Two rows for
	the same role and scope read once; there is no role-by-scope product."""
	items: list[dict[str, str]] = []
	seen: set[tuple[str, str]] = set()
	for row in authorization.active_assignment_rows(user, at):
		scope = _scope_text(row)
		if (row["business_role"], scope) in seen:
			continue
		seen.add((row["business_role"], scope))
		role = _(row["business_role"])
		items.append({"role": role, "scope": scope, "text": f"{role}, {scope}" if scope else role})
	if not items and authorization.is_technical(user):
		role = "Administrator" if user == "Administrator" else "System Manager"
		items.append({"role": role, "scope": _("site-wide"), "text": f"{role}, {_('site-wide')}"})
	return {"items": items, "line": "; ".join(item["text"] for item in items)}
