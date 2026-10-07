"""The Departmental Needs scope hooks (AUTH-ADR-001 §5.3, §9; NDS §6, NDS-BR-019;
AUD-XC-015).

`has_permission` and `permission_query_conditions` for every Need doctype that
can be reached through a standard Frappe route (the Decision rows included: RG-09). They narrow the generic
Organisation-Unit predicate to the Needs read matrix of NDS §6, so a direct
`/api/resource` read, a list, a count and a report all see exactly what the
service layer's `permissions.can_view` shows:

* Departmental Author: the Needs they own, inside the Organisation Unit they
  hold the responsibility for;
* Head of User Department: every Need in the assigned Organisation Unit subtree;
* Procurement Planner (Site-wide): current accepted Needs only, and of their
  revisions only the accepted source (and the earlier accepted ones it
  superseded), never a Draft or Returned revision;
* Auditor: scoped read of all of it;
* Accounting Officer / Head of Procurement Function: decided or submitted
  Needs (a Need root and its projections, never an unsent Draft);
* a technical reader (Administrator / System Manager): everything.

One predicate, written once as SQL and once as a record test over the same
inputs (`_tags`); a test pins that they agree. Child records (Revision, Review
Task, Withdrawal Request, Decision, the three Planning projections) resolve to their
parent Need.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_core.services import authorization as core_authz
from kentender_procurement.departmental_needs.constants import (
	OVERSIGHT_READ_ROLES,
	OVERSIGHT_READ_STATES,
	REVISION_ACCEPTED,
	REVISION_SUPERSEDED,
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	STATE_ACCEPTED,
)

NEED = "Departmental Need"

#: child DocType -> the field that names its parent Need
PARENT_FIELD = {
	"Departmental Need Revision": "departmental_need",
	"Departmental Need Review Task": "departmental_need",
	"Need Withdrawal Request": "departmental_need",
	"Departmental Need Decision": "departmental_need",
	"Need Planning Usage Projection": "departmental_need",
	"Need Planning Intake Projection": "departmental_need",
	"Need Planning Disposition Projection": "departmental_need",
}

#: which reader tags may read which DocType.
#:   full    = author (own Needs), head of department, auditor
#:   planner = the Site-wide Planner (current accepted Needs only)
#:   office  = Accounting Officer / Head of Procurement Function
_ALLOWED_TAGS = {
	NEED: {"full", "planner", "office"},
	"Departmental Need Revision": {"full", "planner"},
	"Departmental Need Review Task": {"full"},
	"Need Withdrawal Request": {"full"},
	# RG-09 / AUD-XC-015: a decision row carries the reason, actor, assignment,
	# source address and session of a department's decision, so it is read like
	# the department's other decision records (NDS-AC-043: the Planner receives
	# no Need decision).
	"Departmental Need Decision": {"full"},
	"Need Planning Usage Projection": {"full", "planner", "office"},
	"Need Planning Intake Projection": {"full", "planner", "office"},
	"Need Planning Disposition Projection": {"full", "planner", "office"},
}

#: a reader tag that only sees some revisions of a Need
_REVISION_STATUSES = {"planner": (REVISION_ACCEPTED, REVISION_SUPERSEDED)}

_READ_PTYPES = frozenset({"read", "select", "report", "export", "print", "email", "share"})


def _quote(value: str) -> str:
	return frappe.db.escape(value)


# -- the predicate as a record test ------------------------------------------


def _allowed(user: str, role: str, unit: str) -> bool:
	return core_authz.authorise_record(
		user=user, business_role=role, organisation_unit=unit, purpose=core_authz.PURPOSE_READ
	).allowed


def _tags(need, user: str) -> set[str]:
	"""The reader tags `user` holds over this Need row (owner, organisation_unit,
	current_state)."""
	tags: set[str] = set()
	unit = cstr(need.organisation_unit)
	if cstr(need.owner) == user and _allowed(user, ROLE_DEPARTMENTAL_AUTHOR, unit):
		tags.add("full")
	if _allowed(user, ROLE_HEAD_OF_USER_DEPARTMENT, unit) or _allowed(user, ROLE_AUDITOR, ""):
		tags.add("full")
	if cstr(need.current_state) == STATE_ACCEPTED and _allowed(user, ROLE_PROCUREMENT_PLANNER, ""):
		tags.add("planner")
	if cstr(need.current_state) in OVERSIGHT_READ_STATES and any(_allowed(user, role, "") for role in OVERSIGHT_READ_ROLES):
		tags.add("office")
	return tags


def _need_row(name: str):
	return frappe.db.get_value(NEED, name, ["name", "owner", "organisation_unit", "current_state"], as_dict=True)


def can_read(doctype: str, doc, user: str) -> bool:
	"""Whether `user` may read this record under the Needs matrix."""
	if core_authz.is_technical(user):
		return True
	allowed = _ALLOWED_TAGS.get(doctype)
	if allowed is None:
		return True
	if doctype == NEED:
		need = doc if getattr(doc, "organisation_unit", None) is not None and getattr(doc, "owner", None) else _need_row(cstr(doc.get("name")))
	else:
		parent = cstr(doc.get(PARENT_FIELD[doctype]))
		need = _need_row(parent) if parent else None
	if not need:
		return False
	tags = _tags(need, user) & allowed
	if not tags:
		return False
	statuses = _REVISION_STATUSES if doctype == "Departmental Need Revision" else {}
	if "full" in tags or not statuses:
		return True
	# only the restricted tags remain: they see only some revisions
	return cstr(doc.get("revision_status")) in {s for tag in tags for s in statuses.get(tag, ())}


# -- the predicate as SQL ------------------------------------------------------


def _need_clauses(user: str) -> list[tuple[str, str]]:
	"""(tag, SQL over `tabDepartmental Need`) for every way `user` may read a Need."""
	table = f"`tab{NEED}`"
	clauses: list[tuple[str, str]] = []

	def scoped(role: str) -> str | None:
		condition = core_authz.scope_condition(NEED, user, business_role=role)
		return None if condition == "1=0" else (condition or "1=1")

	author = scoped(ROLE_DEPARTMENTAL_AUTHOR)
	if author:
		clauses.append(("full", f"({table}.`owner` = {_quote(user)} and {author})"))
	for role in (ROLE_HEAD_OF_USER_DEPARTMENT, ROLE_AUDITOR):
		condition = scoped(role) if role == ROLE_HEAD_OF_USER_DEPARTMENT else _site_wide(role, user)
		if condition:
			clauses.append(("full", f"({condition})"))
	planner = _site_wide(ROLE_PROCUREMENT_PLANNER, user)
	if planner:
		clauses.append(("planner", f"({table}.`current_state` = {_quote(STATE_ACCEPTED)} and {planner})"))
	if any(_site_wide(role, user) for role in OVERSIGHT_READ_ROLES):
		states = ", ".join(_quote(state) for state in OVERSIGHT_READ_STATES)
		clauses.append(("office", f"({table}.`current_state` in ({states}))"))
	return clauses


def _site_wide(role: str, user: str) -> str | None:
	"""`1=1` when `user` holds the Site-wide `role` now (read purpose), else None."""
	return "1=1" if _allowed(user, role, "") else None


def permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	"""The `permission_query_conditions` hook for every Needs DocType."""
	principal = cstr(user or frappe.session.user)
	if core_authz.is_technical(principal):
		return ""
	doctype = doctype or NEED
	allowed = _ALLOWED_TAGS.get(doctype)
	if allowed is None:
		return ""
	clauses = [(tag, sql) for tag, sql in _need_clauses(principal) if tag in allowed]
	if not clauses:
		return "1=0"
	if doctype == NEED:
		return "(" + " or ".join(sql for _tag, sql in clauses) + ")"
	table = f"`tab{doctype}`"
	parent = PARENT_FIELD[doctype]
	statuses = _REVISION_STATUSES if doctype == "Departmental Need Revision" else {}
	parts = []
	for tag, sql in clauses:
		inside = f"{table}.`{parent}` in (select `name` from `tab{NEED}` where {sql})"
		if tag in statuses:
			listed = ", ".join(_quote(s) for s in statuses[tag])
			inside = f"({inside} and {table}.`revision_status` in ({listed}))"
		parts.append(inside)
	return "(" + " or ".join(parts) + ")"


def has_permission(doc=None, ptype: str = "read", user: str | None = None):
	"""The `has_permission` hook for every Needs DocType. Read-type checks use
	the Needs matrix; a write-type check keeps the Organisation-Unit veto of the
	shared predicate (DocPerm and the command-write guard decide the rest)."""
	if doc is None:
		return True
	principal = cstr(user or frappe.session.user)
	doctype = getattr(doc, "doctype", "") or (doc.get("doctype") if isinstance(doc, dict) else "")
	if ptype not in _READ_PTYPES:
		return core_authz.has_permission(doc, ptype, principal)
	if not hasattr(doc, "get"):
		return True
	return can_read(doctype, doc, principal)
