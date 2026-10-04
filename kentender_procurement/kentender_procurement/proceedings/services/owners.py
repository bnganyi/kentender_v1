# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The owner seam (PRC-CHG-001 v0.9 §3, §6; BOP-CHG-001 v0.10 plan D1).

Proceedings never imports its owner. An owner module registers an adapter
for its owner type on the `kt_prc_owner_adapters` hook (a list of dotted
paths to functions returning `{owner_type: adapter}`); tests inject
`frappe.flags.kt_prc_owner_adapters`. An adapter answers two questions:

- `exists(owner_id)`: does this owner record exist?
- `allows(owner_id, user, capacity)`: may `user` act in `capacity` for it?
  Capacities: "owner" (the owner's own guarded commands), "recorder",
  "member" and "reader".

Technical users (Administrator, System Manager) receive no Proceedings
business action and no content read (PRC-CHG-001 v0.9 §6, PRC-N03). A
protected record's existence is never confirmed (KT-STD-001 §11)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.proceedings.services.errors import fail

HOOK = "kt_prc_owner_adapters"
#: The owner's internal transitions (for example CompleteOpening) act as the
#: system, never as a person (BOP-CHG-001 v0.10 §7 CompleteOpening).
SYSTEM_ACTOR = "system"
CAPACITIES = ("owner", "recorder", "member", "reader")


def adapters() -> dict[str, Any]:
	injected = frappe.flags.get(HOOK)
	if injected:
		return dict(injected)
	found: dict[str, Any] = {}
	for path in frappe.get_hooks(HOOK) or []:
		found.update(frappe.get_attr(path)() or {})
	return found


def _technical(user: str) -> bool:
	from kentender_core.services.authorization import is_technical

	return is_technical(user)


def require(owner_type: str, owner_id: str, actor: str, capacity: str) -> Any:
	if capacity not in CAPACITIES:
		raise ValueError(f"Unknown capacity {capacity!r}")
	refused = "PRC_MEMBER_REQUIRED" if capacity == "member" else "PRC_OWNER_UNAVAILABLE"
	adapter = adapters().get(owner_type)
	if adapter is None or not adapter.exists(owner_id):
		fail("PRC_OWNER_UNAVAILABLE")
	if actor == SYSTEM_ACTOR:
		if capacity != "owner" or not adapter.allows(owner_id, actor, capacity):
			fail(refused)
		return adapter
	if not actor or _technical(actor) or not adapter.allows(owner_id, actor, capacity):
		fail(refused)
	return adapter


def user_or_none(actor: str) -> str | None:
	"""A Link to User for a person; the system actor is recorded by source."""
	return actor if actor and actor != SYSTEM_ACTOR and frappe.db.exists("User", actor) else None
