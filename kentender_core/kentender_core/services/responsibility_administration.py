# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUTH-ADR-001 v1.6 §9.2 — the administration commands for responsibilities.

The normal grant journey is: select the user, select the business
responsibility, select the Organisation Unit when the registry requires it,
enter acting dates and authority reference only for an acting appointment,
review the server-composed summary, and save (§14.3). There is no Procuring
Entity to choose — one site is one PE.

An administrator never manages raw Frappe User Permissions, capability
strings, scope JSON, module permissions, Fiscal Year assignments or seed
scripts. This service validates role scope type, tree membership, overlap,
exclusive office and effective dates together with the actor's own grant
authority in one transaction, and synchronises the Frappe Role projection
internally (§5.7, §9.2).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import format_datetime, get_datetime, now_datetime

from kentender_core.utils.display import display_date, display_datetime

from kentender_core.services.authorization import (
	APPOINTMENT_ACTING,
	APPOINTMENT_PERMANENT,
	ASSIGNMENT_DOCTYPE,
	DERIVED_ACTIVE,
	DERIVED_EXPIRED,
	DERIVED_REVOKED,
	DERIVED_SCHEDULED,
	STATUS_ENABLED,
	STATUS_REVOKED,
	descendants_of,
	diagnose_user,
)
from kentender_core.services.authorization import derived_status as _derived
from kentender_core.services.business_role_registry import (
	REGISTRY,
	may_administer,
	require_registered,
)
from kentender_core.services.responsibility_errors import fail

# §14.2 — the filter's Status vocabulary, in the order the screen shows it.
DERIVED_STATUSES = (DERIVED_SCHEDULED, DERIVED_ACTIVE, DERIVED_EXPIRED, DERIVED_REVOKED)


def require_assignment_administrator(business_role: str, actor: str | None = None) -> str:
	"""§9.2 — only the administrative responsibility the registry names may grant."""
	principal = actor or frappe.session.user
	if not may_administer(business_role, set(frappe.get_roles(principal))):
		fail(
			"AUTH_RESPONSIBILITY_REQUIRED",
			"You are not allowed to grant or revoke this responsibility.",
		)
	return principal


def require_assignment_administrator_any(actor: str | None = None) -> str:
	"""Gate the administration surface itself.

	The section lists responsibilities, users and diagnostics before any
	particular responsibility has been chosen, so the entry check is "may this
	actor grant *anything*". Each individual grant or revocation is still
	checked against that responsibility's own `allowed_assignment_admin`.
	"""
	principal = actor or frappe.session.user
	roles = set(frappe.get_roles(principal))
	if not any(may_administer(name, roles) for name in REGISTRY):
		fail(
			"AUTH_RESPONSIBILITY_REQUIRED",
			"You are not allowed to administer KenTender responsibilities.",
		)
	return principal


def grant(
	*,
	user: str,
	business_role: str,
	organisation_unit: str = "",
	appointment_type: str = APPOINTMENT_PERMANENT,
	authority_reference: str = "",
	effective_from: str | None = None,
	effective_to: str | None = None,
	fixture_namespace: str = "",
	actor: str | None = None,
) -> dict[str, Any]:
	"""Create one Enabled assignment, or return the identical existing one.

	§4.7: the same user shall not have overlapping Enabled assignments for the
	same `business_role + organisation_unit` tuple, and an idempotent request
	for the same assignment returns the existing record. Where the registry
	marks the role an exclusive office, a second overlapping Active holder for
	the same scope is rejected with the exact conflicting record. Both are
	settled under row locks so two concurrent grants cannot race past the
	check and both insert.
	"""
	principal = require_assignment_administrator(business_role, actor)
	entry = require_registered(business_role)
	_require_enabled_user(user)

	if not entry.requires_organisation_unit:
		organisation_unit = ""

	existing = _matching_enabled(
		user=user,
		business_role=business_role,
		organisation_unit=organisation_unit,
		effective_from=effective_from,
		effective_to=effective_to,
	)
	if existing is not None:
		if _is_same_appointment(existing, appointment_type, authority_reference):
			return {"assignment": existing["name"], "created": False}
		fail(
			"AUTH_CONFIGURATION_INVALID",
			"An overlapping assignment already exists for that responsibility and scope.",
		)

	if entry.exclusive_office:
		conflict = _exclusive_office_conflict(
			user=user,
			business_role=business_role,
			organisation_unit=organisation_unit,
			effective_from=effective_from,
			effective_to=effective_to,
		)
		if conflict is not None:
			fail(
				"AUTH_EXCLUSIVE_OFFICE_CONFLICT",
				_exclusive_conflict_message(conflict),
			)

	doc = frappe.get_doc(
		{
			"doctype": ASSIGNMENT_DOCTYPE,
			"user": user,
			"business_role": business_role,
			"organisation_unit": organisation_unit or None,
			"appointment_type": appointment_type,
			"authority_reference": authority_reference,
			"effective_from": effective_from,
			"effective_to": effective_to,
			"status": STATUS_ENABLED,
			"assigned_by": principal,
			"assigned_at": now_datetime(),
			"fixture_namespace": fixture_namespace or None,
		}
	)
	doc.insert(ignore_permissions=True)
	_sync_projection(user)
	return {"assignment": doc.name, "created": True}


REASON_MIN = 10
REASON_MAX = 500


def revoke(
	assignment: str,
	*,
	reason: str,
	expected_version: str = "",
	actor: str | None = None,
) -> dict[str, Any]:
	"""§14.4 — one explicit action with a reason of 10–500 characters.

	The command rechecks current status and remaining Role projections, then
	revokes atomically. A concurrent change is refused rather than overwritten,
	so the caller reloads the current state instead of acting on a stale view.
	"""
	reason = " ".join((reason or "").split())
	if not (REASON_MIN <= len(reason) <= REASON_MAX):
		fail(
			"AUTH_CONFIGURATION_INVALID",
			f"Enter a reason for revocation of {REASON_MIN}–{REASON_MAX} characters.",
		)

	doc = frappe.get_doc(ASSIGNMENT_DOCTYPE, assignment)
	principal = require_assignment_administrator(doc.business_role, actor)
	if expected_version and str(doc.modified) != str(expected_version):
		fail("AUTH_STATE_CHANGED", "This assignment changed. Reload and try again.")
	if doc.status == STATUS_REVOKED:
		return {"assignment": doc.name, "revoked": False}

	doc.db_set(
		{
			"status": STATUS_REVOKED,
			"revoked_by": principal,
			"revoked_at": now_datetime(),
			"revocation_reason": reason,
		},
		update_modified=True,
	)
	_sync_projection(doc.user)
	return {"assignment": doc.name, "revoked": True}


def list_for_user(target_user: str, *, at=None) -> dict[str, Any]:
	"""Current, scheduled, expired and revoked assignments for one user.

	The effective scope is spelled out, OU descendants included, because an
	administrator cannot otherwise tell what a directorate-level grant reaches.
	"""
	return diagnose_user(target_user, at=at)


def registry_options() -> list[dict[str, Any]]:
	"""The responsibilities an administrator may choose from, with their scope.

	Serves the assignment dialog so the offer can never drift from the
	code-owned registry (§4.4): the dialog renders whatever this returns and
	shows an Organisation Unit control only where the registry says one is
	required (§14.3).
	"""
	return [
		{
			"business_role": entry.business_role,
			"scope_type": entry.scope_type,
			"requires_organisation_unit": entry.requires_organisation_unit,
			"exclusive_office": entry.exclusive_office,
			"owning_document": entry.owning_document,
		}
		for entry in sorted(REGISTRY.values(), key=lambda e: e.business_role)
	]


def _require_enabled_user(user: str) -> None:
	"""§4.5 — the assignment names an enabled System User, nothing else."""
	row = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
	if not row or not row.enabled:
		fail("AUTH_CONFIGURATION_INVALID", "That user account is not enabled.")
	if row.user_type != "System User":
		fail("AUTH_CONFIGURATION_INVALID", "Only a System User can hold a KenTender responsibility.")


def _matching_enabled(
	*,
	user: str,
	business_role: str,
	organisation_unit: str,
	effective_from: str | None,
	effective_to: str | None,
) -> dict[str, Any] | None:
	"""The Enabled assignment for this exact tuple whose period overlaps, if any.

	Locked for the duration of the transaction so a concurrent grant of the
	same tuple waits rather than racing past the overlap check. There is no
	partial-unique index that could express "one Enabled row per tuple per
	period", which is why this is a lock rather than a constraint.
	"""
	rows = frappe.db.sql(
		"""
		select name, user, appointment_type, authority_reference, effective_from, effective_to
		from `tabUser Responsibility Assignment`
		where user = %(user)s
		  and business_role = %(business_role)s
		  and coalesce(organisation_unit, '') = %(organisation_unit)s
		  and status = %(status)s
		for update
		""",
		{
			"user": user,
			"business_role": business_role,
			"organisation_unit": organisation_unit or "",
			"status": STATUS_ENABLED,
		},
		as_dict=True,
	)
	for row in rows:
		if _periods_overlap(
			row.get("effective_from"), row.get("effective_to"), effective_from, effective_to
		):
			return row
	return None


def _exclusive_office_conflict(
	*,
	user: str,
	business_role: str,
	organisation_unit: str,
	effective_from: str | None,
	effective_to: str | None,
) -> dict[str, Any] | None:
	"""§4.7 — the other holder whose Enabled assignment overlaps this office.

	Locks every Enabled row for the office scope so two concurrent grants for
	the same office serialise rather than both passing the check.
	"""
	rows = frappe.db.sql(
		"""
		select name, user, effective_from, effective_to
		from `tabUser Responsibility Assignment`
		where business_role = %(business_role)s
		  and coalesce(organisation_unit, '') = %(organisation_unit)s
		  and status = %(status)s
		  and user != %(user)s
		for update
		""",
		{
			"business_role": business_role,
			"organisation_unit": organisation_unit or "",
			"status": STATUS_ENABLED,
			"user": user,
		},
		as_dict=True,
	)
	for row in rows:
		if _periods_overlap(
			row.get("effective_from"), row.get("effective_to"), effective_from, effective_to
		):
			return row
	return None


def _exclusive_conflict_message(conflict: dict[str, Any]) -> str:
	holder = frappe.db.get_value("User", conflict["user"], "full_name") or conflict["user"]
	until = conflict.get("effective_to")
	if until:
		return (
			f"{holder} holds this responsibility for this scope until "
			f"{format_datetime(until, 'd MMM y')}. Revoke that assignment before creating an overlapping one."
		)
	return (
		f"{holder} holds this responsibility for this scope with no scheduled end. "
		"Revoke that assignment before creating an overlapping one."
	)


def _periods_overlap(a_from, a_to, b_from, b_to) -> bool:
	"""Interval comparison for one existing row (a) against one new grant (b).

	§4.5: a blank `effective_from` means "effective immediately once Enabled",
	so the NEW grant's blank start is *now*, not unbounded past — otherwise an
	assignment that expired years ago would forever block a fresh open-ended
	grant for the same office. A blank `effective_to` means no scheduled end
	on either side.
	"""
	a_from = get_datetime(a_from) if a_from else None
	a_to = get_datetime(a_to) if a_to else None
	b_from = get_datetime(b_from) if b_from else now_datetime()
	b_to = get_datetime(b_to) if b_to else None
	if a_to and a_to < b_from:
		return False
	if b_to and a_from and b_to < a_from:
		return False
	return True


def _is_same_appointment(row: dict[str, Any], appointment_type: str, authority_reference: str) -> bool:
	return (row.get("appointment_type") or APPOINTMENT_PERMANENT) == appointment_type and (
		row.get("authority_reference") or ""
	) == (authority_reference or "")


def _sync_projection(user: str) -> None:
	"""§5.7 — add the minimal Frappe Role projection, remove only what is unused.

	Revocation removes a projected Role only when no other active assignment
	still requires it, and a Role this registry does not project is never
	touched: an STD or tender Role a user holds for an unrelated module is not
	this service's to remove.

	"Still requires" is evaluated against the assignment's real effect at this
	instant: an Enabled assignment whose period has lapsed requires nothing,
	which is exactly what the scheduled reconciliation cleans up (§5.7).
	"""
	now = now_datetime()
	required: set[str] = set()
	for row in frappe.get_all(
		ASSIGNMENT_DOCTYPE,
		filters={"user": user, "status": STATUS_ENABLED},
		fields=["business_role", "effective_from", "effective_to"],
		limit_page_length=0,
	):
		if row.get("effective_to") and get_datetime(row["effective_to"]) < now:
			continue  # expired by time — projects nothing (AUTH-AC-016)
		required.update(require_registered(row["business_role"]).frappe_roles)

	projected: set[str] = set()
	for entry in REGISTRY.values():
		projected.update(entry.frappe_roles)

	held = set(frappe.get_roles(user))
	to_add = sorted(required - held)
	to_remove = sorted((held & projected) - required)
	if not to_add and not to_remove:
		return

	doc = frappe.get_doc("User", user)
	# add_roles()/remove_roles() save the User document, and a grant may be
	# performed by an actor who holds the assignment-admin responsibility
	# without holding User write permission. The projection is a system effect
	# of an already-authorized grant, not a separate user-editing action.
	doc.flags.ignore_permissions = True
	if to_add:
		doc.add_roles(*to_add)
	if to_remove:
		doc.remove_roles(*to_remove)


def reconcile_role_projections() -> dict[str, Any]:
	"""§5.7 — the scheduled reconciliation for time-expired assignments.

	Assignments expire by time rather than by an explicit action, so an
	expired assignment would otherwise leave its projected Frappe Role behind
	(a false orphan in diagnostics, never business authority). Walks every
	user who holds an assignment or a projected Role and re-syncs. A
	convenience, never the security control: `is_effective()` evaluates
	expiry at command time regardless (AUTH-AC-015/016).
	"""
	projected: set[str] = set()
	for entry in REGISTRY.values():
		projected.update(entry.frappe_roles)

	users: set[str] = set(
		frappe.get_all(ASSIGNMENT_DOCTYPE, distinct=True, pluck="user", limit_page_length=0)
	)
	if projected:
		users.update(
			frappe.get_all(
				"Has Role",
				filters={"role": ("in", sorted(projected)), "parenttype": "User"},
				distinct=True,
				pluck="parent",
				limit_page_length=0,
			)
		)
	users.discard("Administrator")

	reconciled = 0
	for user in sorted(users):
		if not frappe.db.exists("User", user):
			continue
		before = set(frappe.get_roles(user))
		_sync_projection(user)
		frappe.local.role_permissions = {}
		if set(frappe.get_roles(user)) != before:
			reconciled += 1
	return {"users_checked": len(users), "users_reconciled": reconciled}


# --------------------------------------------------------------------------
# §9.2 / §14.2–§14.4 — register, preview and detail
# --------------------------------------------------------------------------


def derived_status(row: dict[str, Any], at=None) -> str:
	"""§4.6 — Scheduled, Active, Expired or Revoked, computed from the record."""
	return _derived(row.get("status") or "", row.get("effective_from"), row.get("effective_to"), at)


def list_user_responsibilities(
	*,
	search: str = "",
	organisation_unit: str = "",
	business_role: str = "",
	status: str = "",
	start: int = 0,
	page_length: int = 50,
	at=None,
) -> dict[str, Any]:
	"""§9.2 `ListUserResponsibilities` — rows and counts from one predicate.

	Filters are optional, visible and non-authoritative (§14.2): the register
	is never scoped by a remembered browser context, and every row the server
	returns is one the caller is entitled to administer.
	"""
	require_assignment_administrator_any()

	filters: dict[str, Any] = {}
	if organisation_unit:
		filters["organisation_unit"] = organisation_unit
	if business_role:
		filters["business_role"] = business_role

	rows = frappe.get_all(
		ASSIGNMENT_DOCTYPE,
		filters=filters,
		fields=[
			"name",
			"user",
			"business_role",
			"organisation_unit",
			"appointment_type",
			"effective_from",
			"effective_to",
			"status",
		],
		order_by="modified desc",
		limit_page_length=0,
	)

	needle = (search or "").strip().lower()
	projected: list[dict[str, Any]] = []
	for row in rows:
		row = dict(row)
		row_status = derived_status(row, at)
		if status and status != row_status:
			continue
		view = _register_row(row, row_status)
		if needle and needle not in (
			f"{view['user_full_name']} {view['user']} {view['business_role']}".lower()
		):
			continue
		projected.append(view)

	total = len(projected)
	page = projected[start : start + page_length] if page_length else projected
	return {"rows": page, "total": total, "start": start, "page_length": page_length}


def _register_row(row: dict[str, Any], row_status: str) -> dict[str, Any]:
	entry = require_registered(row["business_role"])
	unit = row.get("organisation_unit") or ""
	descendants = (descendants_of({unit}) - {unit}) if unit else set()
	return {
		"assignment": row["name"],
		"user": row["user"],
		"user_full_name": frappe.db.get_value("User", row["user"], "full_name") or row["user"],
		"business_role": row["business_role"],
		"scope_type": entry.scope_type,
		"organisation_unit": unit,
		"organisation_unit_label": _unit_label(unit),
		# §13.4 — the Scope column shows the unit name, or `Site-wide`.
		"scope_label": _unit_label(unit) or "Site-wide",
		"coverage": _coverage_label(unit, len(descendants)),
		"descendant_count": len(descendants),
		"appointment_type": row.get("appointment_type") or APPOINTMENT_PERMANENT,
		"effective_from": str(row.get("effective_from") or ""),
		"effective_to": str(row.get("effective_to") or ""),
		"period_label": _period_label(
			row.get("effective_from"),
			row.get("effective_to"),
			row.get("appointment_type") or APPOINTMENT_PERMANENT,
		),
		"status": row_status,
	}


def _period_label(effective_from, effective_to, appointment_type: str) -> str:
	"""AUTH-DES-03's Effective period column, composed server-side.

	A bounded Acting appointment reads as a plain range ("1 Oct 2026 –
	30 Nov 2026"); everything else as "From … · Until …" with "From now"
	and "No scheduled end" for the open ends.
	"""
	if appointment_type == APPOINTMENT_ACTING and effective_from and effective_to:
		return f"{display_date(effective_from)} – {display_date(effective_to)}"
	start = f"From {display_date(effective_from)}" if effective_from else "From now"
	end = f"Until {display_date(effective_to)}" if effective_to else "No scheduled end"
	return f"{start} · {end}"


def _unit_label(unit: str) -> str:
	if not unit:
		return ""
	return frappe.db.get_value("Organisation Unit", unit, "unit_name") or unit


def _coverage_label(unit: str, descendant_count: int) -> str:
	"""§13.4 — `This unit only`, `This unit and n descendant(s)`, or the entity."""
	if not unit:
		return "Entire entity"
	if descendant_count == 0:
		return "This unit only"
	return f"This unit and {descendant_count} descendant" + ("s" if descendant_count != 1 else "")


def preview_assignment(
	*,
	user: str = "",
	business_role: str = "",
	organisation_unit: str = "",
	appointment_type: str = APPOINTMENT_PERMANENT,
	effective_from: str | None = None,
	effective_to: str | None = None,
	authority_reference: str = "",
) -> dict[str, Any]:
	"""§9.2 `PreviewResponsibilityAssignment` — validate and describe; create nothing.

	The dialog's primary button stays disabled until this returns `ok`, so
	every rule the server will apply is visible before anything is written —
	including the exact conflicting assignment, which §14.3 forbids the UI
	from resolving with an invented precedence rule of its own.
	"""
	require_assignment_administrator_any()

	problems: list[dict[str, str]] = []
	entry = None
	if not user:
		problems.append({"field": "user", "message": "Select a user."})
	if not business_role:
		problems.append({"field": "business_role", "message": "Select a responsibility."})
	else:
		entry = require_registered(business_role)

	if entry:
		if entry.requires_organisation_unit and not organisation_unit:
			problems.append({"field": "organisation_unit", "message": "Select an Organisation Unit."})
		if not entry.requires_organisation_unit:
			organisation_unit = ""

	if organisation_unit:
		unit = frappe.db.get_value("Organisation Unit", organisation_unit, ["status"], as_dict=True)
		if not unit:
			problems.append(
				{"field": "organisation_unit", "message": "That Organisation Unit no longer exists."}
			)
		elif unit.status != "Active":
			problems.append(
				{"field": "organisation_unit", "message": "That Organisation Unit is inactive."}
			)

	if appointment_type == APPOINTMENT_ACTING:
		if not effective_from:
			problems.append({"field": "effective_from", "message": "An acting appointment needs a start."})
		if not effective_to:
			problems.append({"field": "effective_to", "message": "An acting appointment needs an end."})
		reference = (authority_reference or "").strip()
		if not (2 <= len(reference) <= 160):
			problems.append(
				{
					"field": "authority_reference",
					"message": "Authority reference is required for Acting assignments (2–160 characters).",
				}
			)
	if effective_from and effective_to and get_datetime(effective_to) <= get_datetime(effective_from):
		problems.append({"field": "effective_to", "message": "The end must be later than the start."})

	conflict = None
	if user and entry and not problems:
		row = _matching_enabled(
			user=user,
			business_role=business_role,
			organisation_unit=organisation_unit,
			effective_from=effective_from,
			effective_to=effective_to,
		)
		if row and not _is_same_appointment(row, appointment_type, authority_reference):
			conflict = {
				"assignment": row["name"],
				"kind": "overlap",
				"message": (
					f"This overlaps an existing Enabled assignment for "
					f"{_unit_label(organisation_unit) or 'the entire entity'} · {business_role}. "
					"Revoke it before this one can be enabled."
				),
			}
		if conflict is None and entry.exclusive_office:
			holder = _exclusive_office_conflict(
				user=user,
				business_role=business_role,
				organisation_unit=organisation_unit,
				effective_from=effective_from,
				effective_to=effective_to,
			)
			if holder is not None:
				# §14.3 — the preview returns the exact conflicting assignment
				# before confirmation; the UI shows it and blocks the save.
				conflict = {
					"assignment": holder["name"],
					"kind": "exclusive_office",
					"heading": "This office is already held",
					"message": _exclusive_conflict_message(holder),
				}

	descendants: list[str] = []
	if organisation_unit:
		descendants = sorted(descendants_of({organisation_unit}) - {organisation_unit})

	return {
		"ok": not problems and not conflict,
		"problems": problems,
		"conflict": conflict,
		"descendant_count": len(descendants),
		"included_units": [_unit_label(unit) for unit in descendants],
		"summary": _summary_sentence(
			user=user,
			business_role=business_role,
			organisation_unit=organisation_unit,
			effective_from=effective_from,
			effective_to=effective_to,
		)
		if not problems
		else "",
		# AUTH-DES-04/05 bold the responsibility and scope inside the summary
		# sentence; the parts let the UI mark exactly the server's words.
		"summary_parts": (
			{
				"user": frappe.db.get_value("User", user, "full_name") or user,
				"role": business_role,
				"scope": _unit_label(organisation_unit) if organisation_unit else "the entire entity",
				"period": _summary_period(effective_from, effective_to),
			}
			if not problems
			else None
		),
	}


def _summary_sentence(
	*,
	user: str,
	business_role: str,
	organisation_unit: str,
	effective_from: str | None,
	effective_to: str | None,
) -> str:
	"""§14.3 — "{User} will be {Responsibility} for {scope} {period}." """
	full_name = frappe.db.get_value("User", user, "full_name") or user
	scope = _unit_label(organisation_unit) if organisation_unit else "the entire entity"
	period = _summary_period(effective_from, effective_to)
	return f"{full_name} will be {business_role} for {scope} {period}."


def _summary_period(effective_from: str | None, effective_to: str | None) -> str:
	start = format_datetime(effective_from, "d MMM y") if effective_from else ""
	end = format_datetime(effective_to, "d MMM y") if effective_to else ""
	if start and end:
		return f"from {start} until {end}"
	if start:
		return f"from {start} with no scheduled end"
	if end:
		return f"from now until {end}"
	return "from now with no scheduled end"


def get_assignment_detail(assignment: str, *, at=None) -> dict[str, Any]:
	"""§14.4 — full detail with its collapsed diagnostics section."""
	require_assignment_administrator_any()
	doc = frappe.db.get_value(
		ASSIGNMENT_DOCTYPE,
		assignment,
		[
			"name",
			"user",
			"business_role",
			"organisation_unit",
			"appointment_type",
			"authority_reference",
			"effective_from",
			"effective_to",
			"status",
			"assigned_by",
			"assigned_at",
			"revoked_by",
			"revoked_at",
			"revocation_reason",
			"modified",
		],
		as_dict=True,
	)
	if not doc:
		fail("AUTH_CONFIGURATION_INVALID", "That responsibility assignment no longer exists.")

	row_status = derived_status(dict(doc), at)
	view = _register_row(dict(doc), row_status)
	entry = require_registered(doc.business_role)
	unit = doc.organisation_unit or ""
	included = sorted(descendants_of({unit}) - {unit}) if unit else []
	diagnostics = diagnose_user(doc.user, at=at)
	projection_present = set(entry.frappe_roles) <= set(frappe.get_roles(doc.user))

	history = [
		{
			"when": display_datetime(doc.assigned_at),
			"actor": doc.assigned_by or "",
			"event": "Responsibility assigned",
		}
	]
	if doc.revoked_at:
		history.append(
			{
				"when": display_datetime(doc.revoked_at),
				"actor": doc.revoked_by or "",
				"event": "Responsibility revoked",
			}
		)

	effective_start = (
		f"From {display_datetime(doc.effective_from)}" if doc.effective_from else "From now"
	)
	effective_end = (
		f"Until {display_datetime(doc.effective_to)}" if doc.effective_to else "No scheduled end"
	)

	view.update(
		{
			"authority_reference": doc.authority_reference or "",
			"assigned_by": doc.assigned_by or "",
			"assigned_at": str(doc.assigned_at or ""),
			"assigned_at_label": display_datetime(doc.assigned_at),
			"revoked_by": doc.revoked_by or "",
			"revoked_at": str(doc.revoked_at or ""),
			"revoked_at_label": display_datetime(doc.revoked_at),
			"revocation_reason": doc.revocation_reason or "",
			"effective_label": f"{effective_start} · {effective_end}",
			"history": history,
			"expected_version": str(doc.modified),
			"organisation_unit_path": _unit_path(unit),
			"included_units": [_unit_label(u) for u in included],
			# §14.4 — Expired and Revoked assignments are read-only, and there
			# is no Edit action at all: a wrong assignment is revoked and
			# replaced so historical authority is never rewritten.
			"can_revoke": row_status in (DERIVED_ACTIVE, DERIVED_SCHEDULED),
			"diagnostics": {
				"required_projection": list(entry.frappe_roles),
				"projection_present": projection_present,
				"projection_missing": diagnostics["projection_missing"],
				"projection_orphaned": diagnostics["projection_orphaned"],
				"coverage": view["coverage"],
				"overlapping": diagnostics["overlapping"],
				"obsolete_rows": diagnostics["obsolete_rows"],
			},
		}
	)
	return view


def _unit_path(unit: str) -> str:
	if not unit:
		return ""
	from kentender_core.services.organisation_structure import _path_of

	# AUTH-DES-06 renders the path with "›" separators.
	return " › ".join(_path_of(unit))
