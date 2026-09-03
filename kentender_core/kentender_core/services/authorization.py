# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUTH-ADR-001 v1.6 §5/§9.1 — the one shared authorization predicate.

One site is one Procuring Entity, so KenTender adds exactly three things to
native Frappe authorization and nothing more (§5.2):

1. `User Responsibility Assignment` — the missing role-to-scope binding with
   effective dating;
2. one shared scope predicate, registered as Frappe
   `permission_query_conditions` / `has_permission` hooks for every DocType
   in the declarative scope map; and
3. one explicit command helper — `require_responsibility(doc, role)` —
   because Frappe cannot know which business role a command requires.

Because scoping is *registered* rather than called, ordinary
`frappe.get_list` and `frappe.has_permission` return the correct result by
default once a DocType enters the scope map (§5.3). Domain apps never query
the assignment DocType and never write module-local scope logic (§18.1).

**The scope map.** Each app declares which field carries the Organisation
Unit on which of its DocTypes, in its `hooks.py`:

    kentender_scope_map = {"Departmental Need": "organisation_unit"}

Which *business roles* are relevant to a DocType is not declared twice: the
DocType's own DocPerm rows already name the Frappe Roles that may read it,
and the registry names each business role's projected Frappe Roles, so the
predicate considers exactly the user's active assignments whose projection
intersects the DocType's read roles. A Site-wide assignment of an unrelated
role therefore never widens a departmental list (AUTH-AC-004), and a
projection held without an assignment grants nothing (AUTH-AC-007).

Deliberate asymmetries, both from the ADR:

- **Reads and commands split on technical status only.** §8 gives
  Administrator and System Manager read access to everything without any
  assignment, and denies them every business mutation without one.
- **There is no fallback.** §11.5: when no assignment matches, the correct
  result is a stable denial plus an administrator diagnostic — never a
  consultation of Frappe User Permission, `User Scope Assignment`, a
  capability profile, `kt_primary_department` or a browser context.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

from kentender_core.services.business_role_registry import (
	REGISTRY,
	SCOPE_OU,
	SCOPE_SITE,
	TECHNICAL_ROLES,
	require_registered,
)
from kentender_core.services.responsibility_errors import fail

ASSIGNMENT_DOCTYPE = "User Responsibility Assignment"

# §4.5 stored status and appointment vocabulary. Kept here rather than on the
# DocType controller so the controller, the administration service and every
# caller share one definition without importing a controller module.
STATUS_ENABLED = "Enabled"
STATUS_REVOKED = "Revoked"

# §4.6 derived display statuses. Only DERIVED_ACTIVE authorises.
DERIVED_SCHEDULED = "Scheduled"
DERIVED_ACTIVE = "Active"
DERIVED_EXPIRED = "Expired"
DERIVED_REVOKED = "Revoked"

APPOINTMENT_PERMANENT = "Permanent"
APPOINTMENT_ACTING = "Acting"

PURPOSE_COMMAND = "command"
PURPOSE_READ = "read"


@dataclass(frozen=True)
class Assignment:
	"""One active assignment, as the resolver hands it to a caller."""

	name: str
	user: str
	business_role: str
	organisation_unit: str
	appointment_type: str
	authority_reference: str
	effective_from: str
	effective_to: str


@dataclass(frozen=True)
class Decision:
	"""One allow/deny result with the exact matching assignment (§9.1)."""

	allowed: bool
	business_role: str
	reason_code: str = ""
	assignment: Assignment | None = None
	# True when a technical reader was allowed under §8 rather than by an
	# assignment. A caller must never treat this as authority to mutate.
	technical_read: bool = False

	@property
	def assignment_id(self) -> str:
		return self.assignment.name if self.assignment else ""


def is_technical(user: str) -> bool:
	"""§8 — Administrator and System Manager inspect without an assignment."""
	if user == "Administrator":
		return True
	return bool(TECHNICAL_ROLES & set(frappe.get_roles(user)))


def _actor(user: str | None) -> str:
	return user or frappe.session.user


def derived_status(status: str, effective_from, effective_to, at=None) -> str:
	"""§4.6 — the display status derived from stored status and the period."""
	if status == STATUS_REVOKED:
		return DERIVED_REVOKED
	at = get_datetime(at or now_datetime())
	if effective_from and get_datetime(effective_from) > at:
		return DERIVED_SCHEDULED
	if effective_to and get_datetime(effective_to) < at:
		return DERIVED_EXPIRED
	return DERIVED_ACTIVE


# --------------------------------------------------------------------------
# Assignment resolution
# --------------------------------------------------------------------------

_ROW_FIELDS = [
	"name",
	"user",
	"business_role",
	"organisation_unit",
	"appointment_type",
	"authority_reference",
	"effective_from",
	"effective_to",
]


def _within_period(row: dict[str, Any], at) -> bool:
	if row.get("effective_from") and get_datetime(row["effective_from"]) > at:
		return False
	if row.get("effective_to") and get_datetime(row["effective_to"]) < at:
		return False
	return True


def _as_assignment(row: dict[str, Any]) -> Assignment:
	return Assignment(
		name=row["name"],
		user=row["user"],
		business_role=row["business_role"],
		organisation_unit=row.get("organisation_unit") or "",
		appointment_type=row.get("appointment_type") or "",
		authority_reference=row.get("authority_reference") or "",
		effective_from=str(row.get("effective_from") or ""),
		effective_to=str(row.get("effective_to") or ""),
	)


def _effective_rows(
	user: str, at, business_role: str = "", business_roles: tuple[str, ...] | None = None
) -> list[dict[str, Any]]:
	"""Enabled assignments whose effective period contains `at`.

	Expiry is evaluated here, at resolution time (§4.6): an assignment whose
	`effective_to` has passed stops authorising whether or not the scheduled
	reconciliation has run.
	"""
	at = get_datetime(at or now_datetime())
	filters: dict[str, Any] = {"user": user, "status": STATUS_ENABLED}
	if business_role:
		filters["business_role"] = business_role
	elif business_roles is not None:
		if not business_roles:
			return []
		filters["business_role"] = ("in", sorted(business_roles))
	rows = frappe.get_all(
		ASSIGNMENT_DOCTYPE,
		filters=filters,
		fields=_ROW_FIELDS,
		order_by="creation asc",
		limit_page_length=0,
	)
	return [row for row in rows if _within_period(row, at)]


def resolve_assignments(
	user: str | None = None, business_role: str = "", at=None
) -> tuple[Assignment, ...]:
	"""§9.1 — active assignments for one required role at one instant."""
	require_registered(business_role)
	rows = _effective_rows(_actor(user), at, business_role=business_role)
	return tuple(_as_assignment(row) for row in rows)


def permitted_ou_scopes(
	user: str | None = None, business_role: str = "", at=None
) -> set[str] | None:
	"""§9.1/§4.3 — assigned Organisation Units plus their descendants.

	`None` means unrestricted: a technical reader under §8, or a Site-wide
	assignment for the role (a Site-wide responsibility covers every unit).
	An ordinary user with no matching assignment gets an empty set, which is
	a denial — never Frappe's "no rows means unrestricted" default.

	Hierarchy expands where the assigned role applies and never creates
	another role: this returns the subtree of the OUs assigned *for this
	business role only*, so a Head of User Department assignment at a
	directorate never turns its holder into a Departmental Author there.
	"""
	principal = _actor(user)
	if is_technical(principal):
		return None
	entry = require_registered(business_role)
	active = resolve_assignments(principal, business_role, at)
	if not active:
		return set()
	if entry.scope_type == SCOPE_SITE:
		return None
	return descendants_of({a.organisation_unit for a in active if a.organisation_unit})


def descendants_of(roots: set[str]) -> set[str]:
	"""Every root plus its nested-set subtree (§4.3).

	A node whose range has not been stamped yet resolves to itself alone
	rather than to nothing, so a site that has not run the nested-set patch
	degrades to leaf-only scope instead of denying everything.
	"""
	if not roots:
		return set()
	bounds = frappe.get_all(
		"Organisation Unit",
		filters=[["Organisation Unit", "name", "in", sorted(roots)]],
		fields=["name", "lft", "rgt"],
		limit_page_length=0,
	)
	covered = set(roots)
	for row in bounds:
		if not row.get("rgt"):
			continue
		covered.update(
			frappe.get_all(
				"Organisation Unit",
				filters={"lft": (">=", row["lft"]), "rgt": ("<=", row["rgt"])},
				pluck="name",
				limit_page_length=0,
			)
		)
	return covered


# --------------------------------------------------------------------------
# Record decisions and the command helper
# --------------------------------------------------------------------------


def authorise_record(
	user: str | None = None,
	business_role: str = "",
	organisation_unit: str = "",
	at=None,
	purpose: str = PURPOSE_COMMAND,
) -> Decision:
	"""§9.1 — one allow/deny result with the exact matching assignment ID.

	`purpose=PURPOSE_READ` admits a technical reader under §8. The default,
	`PURPOSE_COMMAND`, does not: to exercise a business responsibility the
	person must hold the same active assignment as anyone else (AUTH-AC-018).
	"""
	principal = _actor(user)
	entry = require_registered(business_role)

	if purpose == PURPOSE_READ and is_technical(principal):
		return Decision(allowed=True, business_role=business_role, technical_read=True)

	active = resolve_assignments(principal, business_role, at)
	if not active:
		# The role is held by nobody at this instant, or held only outside its
		# effective period. §10 separates the two so a diagnostic can explain
		# an assignment that exists but has not started or has ended.
		return Decision(
			allowed=False,
			business_role=business_role,
			reason_code=(
				"AUTH_ASSIGNMENT_INACTIVE"
				if _has_any_assignment(principal, business_role)
				else "AUTH_RESPONSIBILITY_REQUIRED"
			),
		)

	if entry.scope_type == SCOPE_SITE:
		return Decision(allowed=True, business_role=business_role, assignment=active[0])

	# SCOPE_OU — the record's own unit must fall inside one assigned subtree.
	if not organisation_unit:
		return Decision(
			allowed=False, business_role=business_role, reason_code="AUTH_SCOPE_REQUIRED"
		)
	for assignment in active:
		# The overwhelmingly common case is an assignment on the record's own
		# unit, so settle that without touching the tree at all.
		if assignment.organisation_unit == organisation_unit:
			return Decision(allowed=True, business_role=business_role, assignment=assignment)
	for assignment in active:
		if organisation_unit in descendants_of({assignment.organisation_unit}):
			return Decision(allowed=True, business_role=business_role, assignment=assignment)
	return Decision(allowed=False, business_role=business_role, reason_code="AUTH_SCOPE_REQUIRED")


def _has_any_assignment(user: str, business_role: str) -> bool:
	return bool(
		frappe.db.exists(ASSIGNMENT_DOCTYPE, {"user": user, "business_role": business_role})
	)


def _record_organisation_unit(doc) -> str:
	"""The Organisation Unit a record carries, via the scope map or directly."""
	if doc is None:
		return ""
	if isinstance(doc, dict):
		doctype = doc.get("doctype", "")
		getter = doc.get
	else:
		doctype = getattr(doc, "doctype", "")
		getter = lambda field, default="": getattr(doc, field, default)  # noqa: E731
	field = scope_map().get(doctype) or "organisation_unit"
	return getter(field, "") or ""


def require_responsibility(
	doc, business_role: str, *, user: str | None = None, at=None
) -> Assignment:
	"""§5.5 — the one helper a protected command calls before it mutates.

	Resolves the Active assignment for that exact role, matches the record's
	Organisation Unit against the assignment's subtree, and raises the
	applicable §10 error on failure. Returns the matching assignment so the
	command can retain the §15 audit snapshot. The client never supplies an
	assignment ID or effective scope; whatever it sent, this resolves again.
	"""
	decision = authorise_record(
		user=user,
		business_role=business_role,
		organisation_unit=_record_organisation_unit(doc),
		at=at,
		purpose=PURPOSE_COMMAND,
	)
	if not decision.allowed:
		fail(decision.reason_code)
	return decision.assignment  # type: ignore[return-value]


# --------------------------------------------------------------------------
# The registered hooks (§5.3) — one predicate for lists, counts, reports
# and direct document access
# --------------------------------------------------------------------------


def scope_map() -> dict[str, str]:
	"""The merged `kentender_scope_map` hook: DocType → OU fieldname.

	Declarative registration (§5.3): each app contributes entries from its
	own hooks.py; adding a scoped DocType is a configuration line, not new
	SQL. The map is empty of production DocTypes until each module's cutover
	slice lands (§11.3 step 4: hooks registered, no production caller
	switched).
	"""
	merged: dict[str, str] = {}
	for doctype, field in (frappe.get_hooks("kentender_scope_map") or {}).items():
		merged[doctype] = field[-1] if isinstance(field, (list, tuple)) else field
	return merged


def _relevant_business_roles(doctype: str) -> tuple[str, ...]:
	"""Registered roles whose Frappe Role projection may read this DocType.

	The DocType's own DocPerm rows are the declaration of which Frappe Roles
	read it (§5.1); the registry maps business roles onto those projections.
	Deriving relevance this way means a Site-wide assignment of an unrelated
	role can never widen this DocType's rows (AUTH-AC-004).
	"""
	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		return ()
	read_roles = {perm.role for perm in (meta.permissions or []) if perm.read}
	return tuple(
		sorted(
			name
			for name, entry in REGISTRY.items()
			if set(entry.frappe_roles) & read_roles
		)
	)


def scope_condition(doctype: str, user: str | None = None, business_role: str = "") -> str:
	"""§9.1 — the SQL predicate both permission hooks and report match
	conditions use.

	Returns `""` for unrestricted (a technical reader, or a relevant
	Site-wide assignment) and `"1=0"` for a denial, so a caller can
	concatenate the result without special-casing. Counts and rows share this
	string: §5.4 forbids a count that discloses records the rows cannot show.
	"""
	principal = _actor(user)
	if is_technical(principal):
		return ""

	ou_field = scope_map().get(doctype)
	if not ou_field:
		# Not a scoped DocType: this predicate adds nothing; DocPerm governs.
		return ""

	roles = (business_role,) if business_role else _relevant_business_roles(doctype)
	rows = _effective_rows(principal, None, business_roles=tuple(roles))
	if not rows:
		return "1=0"

	site_wide = [row for row in rows if not require_registered(row["business_role"]).requires_organisation_unit]
	if site_wide:
		return ""

	units = sorted(descendants_of({row["organisation_unit"] for row in rows if row["organisation_unit"]}))
	if not units:
		return "1=0"
	column = f"`tab{doctype}`.`{ou_field}`"
	return f"{column} in ({', '.join(frappe.db.escape(value) for value in units)})"


def permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	"""The `permission_query_conditions` hook target for every scoped DocType."""
	return scope_condition(doctype or "", user)


def has_permission(doc=None, ptype: str = "read", user: str | None = None):
	"""The `has_permission` hook target for every scoped DocType (§5.3).

	Registered alongside the query hook because query conditions only hide
	documents from lists; without this, a direct route to a known name would
	still open a filtered-out record. Returns False to deny; None to leave
	the decision to the framework's other checks. It only ever *restricts* —
	granting a business mutation is `require_responsibility`'s job.
	"""
	if doc is None:
		return None
	principal = _actor(user)
	if is_technical(principal):
		return None

	doctype = getattr(doc, "doctype", "") or (doc.get("doctype") if isinstance(doc, dict) else "")
	ou_field = scope_map().get(doctype)
	if not ou_field:
		return None

	record_unit = _record_organisation_unit(doc)
	rows = _effective_rows(principal, None, business_roles=_relevant_business_roles(doctype))
	if not rows:
		return False
	for row in rows:
		if not require_registered(row["business_role"]).requires_organisation_unit:
			return None
	units = descendants_of({row["organisation_unit"] for row in rows if row["organisation_unit"]})
	if record_unit and record_unit in units:
		return None
	return False


def report_match_conditions(doctype: str, user: str | None = None) -> str:
	"""§5.4 — the predicate a Query/Script Report over scoped data must apply.

	A report that cannot apply this is prohibited, not exempt.
	"""
	return scope_condition(doctype, user)


# --------------------------------------------------------------------------
# Audit snapshot and diagnostics
# --------------------------------------------------------------------------


def assignment_snapshot(assignment: Assignment | None, *, at=None) -> str:
	"""§15 — the immutable authority snapshot a decision record retains.

	Later changes to the assignment must not rewrite historical decision
	evidence, so this copies the values rather than storing a link alone.
	"""
	if assignment is None:
		return json.dumps({"assignment_id": "", "evaluated_at": str(get_datetime(at or now_datetime()))})
	payload = asdict(assignment)
	payload["assignment_id"] = payload.pop("name")
	payload["evaluated_at"] = str(get_datetime(at or now_datetime()))
	return json.dumps(payload, sort_keys=True)


def diagnose_user(user: str, at=None) -> dict[str, Any]:
	"""§9.1 — read-only explanation of one user's effective authority.

	Never repairs and never broadens: it reports what is there, including the
	rows still awaiting migration, so an administrator can see why a record is
	allowed or denied without being shown protected record content.
	"""
	at = get_datetime(at or now_datetime())
	rows = frappe.get_all(
		ASSIGNMENT_DOCTYPE,
		filters=[[ASSIGNMENT_DOCTYPE, "user", "=", user]],
		fields=[*_ROW_FIELDS, "status"],
		order_by="business_role asc, organisation_unit asc",
		limit_page_length=0,
	)

	buckets: dict[str, list[dict[str, Any]]] = {
		"active": [],
		"scheduled": [],
		"expired": [],
		"revoked": [],
	}
	required_projections: set[str] = set()
	for row in rows:
		row = dict(row)
		state = derived_status(row["status"], row["effective_from"], row["effective_to"], at)
		if state == DERIVED_REVOKED:
			buckets["revoked"].append(row)
		elif state == DERIVED_SCHEDULED:
			buckets["scheduled"].append(row)
		elif state == DERIVED_EXPIRED:
			buckets["expired"].append(row)
		else:
			row["covers_org_units"] = (
				sorted(descendants_of({row["organisation_unit"]})) if row["organisation_unit"] else []
			)
			buckets["active"].append(row)
			required_projections.update(require_registered(row["business_role"]).frappe_roles)

	held_roles = set(frappe.get_roles(user))
	registered_projections = {
		projected for entry in REGISTRY.values() for projected in entry.frappe_roles
	}

	return {
		"user": user,
		"evaluated_at": str(at),
		"technical_read_all": is_technical(user),
		"assignments": buckets,
		"projection_missing": sorted(required_projections - held_roles),
		# §5.7 — a Frappe Role held without a matching assignment grants no
		# business authority. Reported as an orphan, never silently honoured.
		"projection_orphaned": sorted((held_roles & registered_projections) - required_projections),
		"overlapping": _overlapping(buckets["active"]),
		"obsolete_rows": _obsolete_rows(user),
	}


def _overlapping(active: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""§4.7 — two Enabled assignments for the same role and exact scope."""
	seen: dict[tuple[str, str], str] = {}
	clashes: list[dict[str, Any]] = []
	for row in active:
		key = (row["business_role"], row["organisation_unit"] or "")
		if key in seen:
			clashes.append({"first": seen[key], "second": row["name"], "scope": list(key)})
		else:
			seen[key] = row["name"]
	return clashes


def _obsolete_rows(user: str) -> dict[str, int]:
	"""Retired authority stores still holding rows for this user (§11.1).

	Counted, never read as authority. Only KenTender-owned User Permission
	rows count — ERPNext and HRMS User Permissions are load-bearing and are
	not KenTender migration debt (§11.4).
	"""
	counts: dict[str, int] = {}
	kt_owned_allows = (
		"Procuring Entity",
		"Organisation Unit",
		"Financial Year",
		"PE Fiscal Year Context",
		"Procuring Department",
	)
	if frappe.db.exists("DocType", "User Permission"):
		counts["User Permission"] = frappe.db.count(
			"User Permission", {"user": user, "allow": ("in", kt_owned_allows)}
		)
	for doctype, filters in (
		("User Scope Assignment", {"user": user}),
		("Operational Scope Assignment", {"user_id": user}),
	):
		if frappe.db.exists("DocType", doctype):
			counts[doctype] = frappe.db.count(doctype, filters)
	return counts
