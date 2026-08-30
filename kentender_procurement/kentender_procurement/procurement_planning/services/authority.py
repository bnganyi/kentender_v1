# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §6 — native authorisation checks.

One vocabulary for every Planning list, count, detail and command: a Frappe
Role names the kind of work, a User Permission row names the scope it applies
to, and a role label alone grants no cross-scope authority. Financial Year is
never assigned to a user (§6); it derives from configured records and the
operation's window or record state. Administrator and System Manager receive
no business-decision exception.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_planning.errors import fail


def not_found() -> None:
	"""§9: unauthorised detail/task reads look exactly like a missing record."""
	raise frappe.DoesNotExistError("Not found")


def has_role(actor: str, role: str) -> bool:
	return role in set(frappe.get_roles(actor))


def permitted_values(actor: str, allow: str) -> set[str]:
	"""The actor's User Permission scope for one doctype (empty = none granted)."""
	return {
		cstr(row)
		for row in frappe.get_all(
			"User Permission",
			filters={"user": actor, "allow": allow},
			pluck="for_value",
			limit_page_length=0,
		)
		if cstr(row)
	}


def permitted_org_units(actor: str) -> set[str]:
	return permitted_values(actor, "Organisation Unit")


def permitted_pes(actor: str) -> set[str]:
	return permitted_values(actor, "Procuring Entity")


def require_scope(
	actor: str,
	*,
	roles: tuple[str, ...],
	procuring_entity: str,
	organisation_unit: str | None = None,
	masked: bool = True,
) -> str:
	"""Assert the actor holds one of `roles` with a User Permission for the PE
	(and OU where the role is department-scoped). Returns the matched role.

	`masked=True` (reads and record-addressed commands) raises not-found;
	`masked=False` raises the §9 PLN_NO_CONTEXT result (context resolution)."""
	held = [role for role in roles if has_role(actor, role)]
	pes = permitted_pes(actor)
	ok = bool(held) and procuring_entity in pes
	if ok and organisation_unit is not None:
		ous = permitted_org_units(actor)
		# An OU-scoped role must hold the exact department; a user with no OU
		# rows has been granted no department at all.
		ok = organisation_unit in ous
	if not ok:
		if masked:
			not_found()
		fail(
			"PLN_NO_CONTEXT",
			"You do not have an assigned Procurement Planning scope, "
			"or no configured Financial Year is available.",
		)
	return held[0]


def authority_snapshot(
	actor: str, *, role: str, values: tuple[str, ...]
) -> str:
	"""§4.5/§4.6/§4.11/§4.12 — the native role and User Permission rows used
	for a decision, serialised for the immutable evidence record."""
	rows = frappe.get_all(
		"User Permission",
		filters={"user": actor},
		fields=["allow", "for_value"],
		limit_page_length=0,
	)
	relevant = sorted(
		f"{row.allow}:{row.for_value}"
		for row in rows
		if cstr(row.for_value) in {cstr(v) for v in values if v}
	)
	return json.dumps({"actor": actor, "role": role, "user_permissions": relevant})


def resolve_context_id(procuring_entity: str, financial_year: str) -> str:
	"""The PE Fiscal Year Context for an exact PE + FY; fail closed when absent
	or ambiguous (§3)."""
	rows = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"procuring_entity": procuring_entity, "financial_year": financial_year},
		pluck="name",
		limit_page_length=2,
	)
	if len(rows) != 1:
		fail(
			"PLN_NO_CONTEXT",
			"You do not have an assigned Procurement Planning scope, "
			"or no configured Financial Year is available.",
		)
	return rows[0]


def context_parts(pe_fy_context: str) -> dict[str, Any]:
	doc = frappe.db.get_value(
		"PE Fiscal Year Context",
		pe_fy_context,
		["procuring_entity", "financial_year"],
		as_dict=True,
	)
	if not doc:
		not_found()
	return doc
