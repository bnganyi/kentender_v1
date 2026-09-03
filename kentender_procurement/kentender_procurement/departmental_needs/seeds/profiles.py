"""Selectable Departmental Needs seed profiles (NDS-CHG-001 v1.1 §14).

§14.7 requires seeds to *call domain builders or public commands that enforce
the same invariants as production setup*, and requires the default, Planning
usage, successor, withdrawal and negative profiles to be independently
selectable and resettable. This module provides both.

Every profile therefore drives the real §8.2 commands rather than writing rows.
Two consequences follow, and both are deliberate:

- The §14.1 intake window is `Scheduled` until 1 Sep 2026 and `Closed` after
  25 Nov 2026, so `create_need` would be refused outside that period. Seeding
  opens the window for the duration of the build and restores the exact §14.1
  instants afterwards (`_intake_open`). The fixture is unchanged once seeding
  finishes; only the commands ran against a temporarily open window.
- Commands stamp decisions with the wall clock, so the §14.3 design-clock times
  are applied afterwards by `_stamp`. Nothing else is rewritten: the states,
  versions, hashes, tasks and published events are exactly what the commands
  produced.

Each profile owns a fixture namespace so `reset_profile` removes precisely what
it created. Resets use `frappe.db.delete`, which bypasses the controllers that
retain business records permanently (§13) — correct for a fixture reset and for
nothing else.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable

import frappe
from frappe.utils import add_days, now_datetime

from kentender_core.seeds import kebs_foundation
from kentender_procurement.departmental_needs.constants import (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	STATE_ACCEPTED,
	USAGE_FULL,
	USAGE_NOT_INCLUDED,
)
from kentender_procurement.departmental_needs.services import lifecycle
from kentender_procurement.departmental_needs.services.usage import project_planning_usage

from . import kentender_mvp_r1 as base

# --- §14.4 integrated Planning usage fixture --------------------------------
ACTIVE_PLAN = "PLN-MOH-2027-001"
ACTIVE_PLAN_ITEM = "PPI-MOH-2027-021"

# --- §14.5 isolated successor and withdrawal fixtures -----------------------
SUCCESSOR_NEED = "NDS-MOH-2027-0001"
SUCCESSOR_REQUIRED_BY = "2027-09-15"

# §14.5 fixes the fixture request identifier exactly.
WITHDRAWAL_REQUEST_ID = "NDS-WDR-MOH-2027-0001"

# The exact NDS-DES-11 reason (§11.12).
WITHDRAWAL_REASON = (
	"The programme will not proceed in FY 2027/28 because implementation "
	"responsibility has moved outside the department."
)

NS_USAGE = f"{base.NS}_USAGE"
NS_SUCCESSOR = f"{base.NS}_SUCCESSOR"
NS_WITHDRAWAL = f"{base.NS}_WITHDRAWAL"
NS_KEBS = f"{base.NS}_KEBS"


# --- seeding helpers --------------------------------------------------------


@contextmanager
def _as(user: str):
	"""Run commands as a real seeded actor, so `owner` and maker-checker hold."""
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


@contextmanager
def _intake_open():
	"""Open the §14.1 window for the build, then restore its exact instants."""
	base._intake_window()
	now = now_datetime()
	frappe.db.set_value(
		"Needs Intake Window",
		base.INTAKE_WINDOW,
		{"opens_at": add_days(now, -1), "closes_at": add_days(now, 1)},
		update_modified=False,
	)
	try:
		yield
	finally:
		frappe.db.set_value(
			"Needs Intake Window",
			base.INTAKE_WINDOW,
			{"opens_at": base.INTAKE_OPENS_AT, "closes_at": base.INTAKE_CLOSES_AT},
			update_modified=False,
		)


def key(*parts: str) -> str:
	"""An idempotency key derived from the state the command acts on.

	A *fixed* key per profile step looked deterministic but was wrong: the
	payload of a command that takes `expected_version` changes whenever the
	record version does, so re-applying a profile after a reset raised
	`NDS_IDEMPOTENCY_CONFLICT` — the §9 control correctly reporting that the
	same key had been reused with a different request. Deriving the key from the
	state instead means a true repeat replays, while a genuinely different state
	is a different command.

	Fixture *identifiers* are still fixed exactly where §14 names them; this is
	an internal command control, not one of them.
	"""
	return "nds-seed:" + ":".join(str(part) for part in parts)


def _stamp(need: str, action: str, when: str) -> None:
	"""Apply a §14.3 design-clock timestamp to the decision a command wrote."""
	name = frappe.db.get_value(
		"Departmental Need Decision",
		{"departmental_need": need, "action": action},
		"name",
		order_by="creation desc",
	)
	if name:
		frappe.db.set_value(
			"Departmental Need Decision", name, "occurred_at", when, update_modified=False
		)


def _namespace(doctype: str, name: str, namespace: str) -> None:
	if frappe.db.has_column(doctype, "fixture_namespace"):
		frappe.db.set_value(doctype, name, "fixture_namespace", namespace, update_modified=False)


def _open_task(need: str, task_type: str) -> tuple[str, str]:
	row = frappe.db.get_value(
		"Departmental Need Review Task",
		{"departmental_need": need, "task_type": task_type, "status": "Open"},
		["name", "decision_token"],
		order_by="opened_at desc",
		as_dict=True,
	)
	if not row:
		frappe.throw(f"No open {task_type} task for {need}; the profile is out of order.")
	return row.name, row.decision_token


def _record_version(need: str) -> int:
	return int(frappe.db.get_value("Departmental Need", need, "record_version") or 0)


# --- §14.4 Planning usage ---------------------------------------------------


def apply_planning_usage() -> dict[str, Any]:
	"""Project NDS-MOH-2027-0001 Version 1 as Fully included in an Active Plan.

	Used by NDS-DES-07 and NDS-DES-12. §14.4 is explicit that it is *not* loaded
	into tests expecting the design-clock default of `Not included`, which is why
	it is a separate profile rather than part of the default build.
	"""
	need = frappe.get_doc("Departmental Need", SUCCESSOR_NEED)
	if not need.current_accepted_version:
		frappe.throw(f"{SUCCESSOR_NEED} has no accepted version; apply the default profile first.")
	with _as(base.PLANNER):
		result = project_planning_usage(
			departmental_need=need.name,
			accepted_version=need.current_accepted_version,
			usage=USAGE_FULL,
			source_event_id=key("usage", need.name, need.current_accepted_version),
			active_plan=ACTIVE_PLAN,
			active_plan_item=ACTIVE_PLAN_ITEM,
		)
	_namespace("Need Planning Usage Projection", need.current_accepted_version, NS_USAGE)
	return {"profile": "planning_usage", "usage": result["usage"], "plan_item": ACTIVE_PLAN_ITEM}


def reset_planning_usage() -> dict[str, Any]:
	removed = frappe.get_all(
		"Need Planning Usage Projection", filters={"fixture_namespace": NS_USAGE}, pluck="name"
	)
	frappe.db.delete("Need Planning Usage Projection", {"fixture_namespace": NS_USAGE})
	return {"profile": "planning_usage", "removed": removed}


# --- §14.5 successor --------------------------------------------------------


def apply_successor() -> dict[str, Any]:
	"""Copy Version 1 into Version 2 changing only the required-by date.

	§14.5: acceptance emits the exact supersession event without altering
	Version 1, which is asserted by the Phase 5 event tests rather than assumed
	here.
	"""
	need = frappe.get_doc("Departmental Need", SUCCESSOR_NEED)
	version_one = need.current_accepted_version
	if str(frappe.db.get_value("Departmental Need Version", version_one, "required_by_date")) == SUCCESSOR_REQUIRED_BY:
		return {"profile": "successor", "idempotent": True, "accepted_version": version_one}
	source = frappe.get_doc("Departmental Need Version", version_one)
	with _as(base.AUTHOR):
		opened = lifecycle.create_accepted_need_successor(
			need=need.name,
			expected_version=_record_version(need.name),
			idempotency_key=key("successor", "create", need.name, _record_version(need.name)),
		)
		saved = lifecycle.update_need(
			need=need.name,
			expected_version=opened["record_version"],
			idempotency_key=key("successor", "save", need.name, opened["record_version"]),
			title=source.title,
			description=source.description,
			expected_operational_result=source.expected_operational_result,
			indicative_quantity=source.indicative_quantity,
			unit=source.unit,
			required_by_date=SUCCESSOR_REQUIRED_BY,
		)
		submitted = lifecycle.submit_need(
			need=need.name,
			expected_version=saved["record_version"],
			idempotency_key=key("successor", "submit", need.name, saved["record_version"]),
		)
	task, token = _open_task(need.name, "Successor acceptance")
	with _as(base.REVIEWER):
		accepted = lifecycle.review_need(
			need=need.name,
			decision="accept",
			task=task,
			expected_version=submitted["record_version"],
			decision_token=token,
			idempotency_key=key("successor", "accept", need.name, submitted["record_version"]),
		)
	_namespace("Departmental Need Version", opened["successor_version"], NS_SUCCESSOR)
	return {
		"profile": "successor",
		"superseded_version": accepted["superseded_version"],
		"accepted_version": opened["successor_version"],
		"event_id": accepted["event_id"],
	}


def reset_successor() -> dict[str, Any]:
	"""Return NDS-MOH-2027-0001 to its §14.3 single-version accepted state."""
	versions = frappe.get_all(
		"Departmental Need Version", filters={"fixture_namespace": NS_SUCCESSOR}, pluck="name"
	)
	if not versions:
		return {"profile": "successor", "removed": []}
	need = frappe.get_doc("Departmental Need", SUCCESSOR_NEED)
	original = frappe.db.get_value(
		"Departmental Need Version",
		{"departmental_need": need.name, "version_number": 1},
		"name",
	)
	frappe.db.delete("Departmental Need Event", {"need_version": ("in", versions)})
	frappe.db.delete("Departmental Need Event", {"superseded_version": ("in", versions)})
	frappe.db.delete("Departmental Need Decision", {"need_version": ("in", versions)})
	frappe.db.delete("Departmental Need Review Task", {"need_version": ("in", versions)})
	frappe.db.delete("Need Planning Usage Projection", {"accepted_version": ("in", versions)})
	frappe.db.delete("Departmental Need Version", {"name": ("in", versions)})
	frappe.db.set_value(
		"Departmental Need Version", original, "version_status", "Accepted", update_modified=False
	)
	frappe.db.set_value(
		"Departmental Need",
		need.name,
		{
			"current_version": original,
			"current_accepted_version": original,
			"current_state": STATE_ACCEPTED,
		},
		update_modified=False,
	)
	return {"profile": "successor", "removed": versions}


# --- §14.5 withdrawal -------------------------------------------------------


def apply_withdrawal(*, cleared: bool = False) -> dict[str, Any]:
	"""Open `NDS-WDR-MOH-2027-0001` with the exact NDS-DES-11 reason.

	The blocked variant uses the §14.4 Active Plan dependency; the cleared
	variant supplies `Not included` and no Plan references. Only the projection
	differs — the request itself is identical, which is what makes the two
	NDS-DES-12 variants comparable.
	"""
	need = frappe.get_doc("Departmental Need", SUCCESSOR_NEED)
	if need.current_state != STATE_ACCEPTED:
		frappe.throw(f"{need.name} is not Accepted for planning; apply the default profile first.")
	if cleared:
		reset_planning_usage()
		with _as(base.PLANNER):
			project_planning_usage(
				departmental_need=need.name,
				accepted_version=need.current_accepted_version,
				usage=USAGE_NOT_INCLUDED,
				source_event_id=key("usage", "cleared", need.current_accepted_version),
			)
		_namespace("Need Planning Usage Projection", need.current_accepted_version, NS_USAGE)
	else:
		apply_planning_usage()
	existing = frappe.db.get_value(
		"Need Withdrawal Request",
		{"departmental_need": need.name, "status": ("in", ["Awaiting review", "Awaiting planning clearance"])},
		"name",
	)
	if not existing:
		with _as(base.AUTHOR):
			requested = lifecycle.request_withdrawal(
				need=need.name,
				expected_version=_record_version(need.name),
				idempotency_key=key("withdrawal", "request", need.name, _record_version(need.name)),
				reason=WITHDRAWAL_REASON,
			)
		existing = _rename_request(requested["withdrawal_request"])
	_namespace("Need Withdrawal Request", existing, NS_WITHDRAWAL)
	return {
		"profile": "withdrawal_cleared" if cleared else "withdrawal_blocked",
		"withdrawal_request": existing,
		"usage": USAGE_NOT_INCLUDED if cleared else USAGE_FULL,
	}


def _rename_request(generated: str) -> str:
	"""§14.5 names the fixture request exactly; the command generates an opaque ID.

	Production identifiers are deliberately unguessable, so the seed renames its
	own fixture rather than making the generator predictable. `rename_doc`
	repoints the decision and review-task links with it.
	"""
	if generated == WITHDRAWAL_REQUEST_ID:
		return generated
	if frappe.db.exists("Need Withdrawal Request", WITHDRAWAL_REQUEST_ID):
		return WITHDRAWAL_REQUEST_ID
	frappe.rename_doc(
		"Need Withdrawal Request",
		generated,
		WITHDRAWAL_REQUEST_ID,
		force=True,
		show_alert=False,
	)
	frappe.db.set_value(
		"Need Withdrawal Request",
		WITHDRAWAL_REQUEST_ID,
		"withdrawal_request_id",
		WITHDRAWAL_REQUEST_ID,
		update_modified=False,
	)
	return WITHDRAWAL_REQUEST_ID


def apply_withdrawal_blocked() -> dict[str, Any]:
	return apply_withdrawal(cleared=False)


def apply_withdrawal_cleared() -> dict[str, Any]:
	return apply_withdrawal(cleared=True)


def reset_withdrawal() -> dict[str, Any]:
	"""Remove the withdrawal fixture and any task it left open.

	Scoped to the fixture Need rather than to the namespace alone: a profile that
	failed part-way through leaves rows the namespace stamp never reached, and
	§4.4 allows only one open review task per Need — so a namespace-only reset
	would make the profile permanently un-appliable. This profile only ever
	touches NDS-MOH-2027-0001, so the Need is the precise scope.
	"""
	requests = frappe.get_all(
		"Need Withdrawal Request", filters={"departmental_need": SUCCESSOR_NEED}, pluck="name"
	)
	if requests:
		frappe.db.delete("Departmental Need Decision", {"withdrawal_request": ("in", requests)})
		frappe.db.delete("Need Withdrawal Request", {"name": ("in", requests)})
	frappe.db.delete(
		"Departmental Need Review Task",
		{"departmental_need": SUCCESSOR_NEED, "task_type": "Withdrawal"},
	)
	reset_planning_usage()
	return {"profile": "withdrawal", "removed": requests}


# --- §14.6 KEBS first slice -------------------------------------------------

# Actors are Needs-owned; the PE/OU/FY/context are not (see kebs_foundation).
KEBS_AUTHOR = "requester.kebs@example.test"
KEBS_REVIEWER = "head.kebs@example.test"

# Inside FY 2026/27, which is the canonical KEBS financial year.
KEBS_REQUIRED_BY = "2027-03-31"
KEBS_INTAKE_OPENS_AT = "2026-07-01 00:00:00"
KEBS_INTAKE_CLOSES_AT = "2026-09-30 23:59:59"

KEBS_NEEDS = (
	{
		"source_line": "SRC-KEBS-ICT-001",
		"title": "Business laptops",
		"description": "Business laptop computers for mobile officers in the Coast Region office.",
		"indicative_quantity": 25,
		"unit": "UNIT-EACH",
		"expected_operational_result": "Mobile officers can run approved office and standards applications securely.",
	},
	{
		"source_line": "SRC-KEBS-ICT-002",
		"title": "Desktop computers with monitors",
		"description": "Desktop computers with monitors replacing unsupported Coast Region workstations.",
		"indicative_quantity": 15,
		"unit": "UNIT-EACH",
		"expected_operational_result": "Fixed workstations replace unsupported equipment at the Coast Region office.",
	},
	{
		"source_line": "SRC-KEBS-ICT-003",
		"title": "Business tablets",
		"description": "Business tablets for field officers carrying out inspections away from the office.",
		"indicative_quantity": 10,
		"unit": "UNIT-EACH",
		"expected_operational_result": "Field officers can capture and review inspection information away from the office.",
	},
)


def apply_kebs() -> dict[str, Any]:
	"""§14.6 — the KEBS first-slice, built as real Accepted Needs.

	NDS-AC-045 is about the Needs-origin route preserving the same source facts,
	so it is proved by driving three Needs through the real §5.1 lifecycle to
	Accepted against the canonical KEBS context — never by creating the facts as
	direct Planning entries, which would bypass the very flow the criterion
	exists to test. The direct-entry equivalence is Procurement Planning's own
	test under PLN-CHG-001.

	The PE, OU, FY and PE Fiscal Year Context come from the shared
	Configuration & Governance fixture and are never created here (§14.1).
	"""
	kebs_foundation.require_installed()
	author = base._user(KEBS_AUTHOR, "KEBS ICT Requester", (ROLE_DEPARTMENTAL_AUTHOR,))
	reviewer = base._user(KEBS_REVIEWER, "KEBS ICT Head", (ROLE_HEAD_OF_USER_DEPARTMENT,))
	for user in (author, reviewer):
		base._user_permission(user, "Procuring Entity", kebs_foundation.PE)
		base._user_permission(user, "Organisation Unit", kebs_foundation.OU)
		base._user_permission(user, "Financial Year", kebs_foundation.FY)

	window = _kebs_window()
	built = []
	for spec in KEBS_NEEDS:
		built.append(_build_kebs_need(spec))
	frappe.db.set_value(
		"Needs Intake Window",
		window,
		{"opens_at": KEBS_INTAKE_OPENS_AT, "closes_at": KEBS_INTAKE_CLOSES_AT},
		update_modified=False,
	)
	return {"profile": "kebs", "needs": built, "context": kebs_foundation.CONTEXT}


def _kebs_window() -> str:
	"""The PE/FY intake window the KEBS Needs are created inside (§4.1)."""
	name = f"NDS-IW-{kebs_foundation.PE}-{kebs_foundation.FY}"
	now = now_datetime()
	if not frappe.db.exists("Needs Intake Window", name):
		frappe.get_doc(
			{
				"doctype": "Needs Intake Window",
				"needs_intake_window_id": name,
				"procuring_entity": kebs_foundation.PE,
				"financial_year": kebs_foundation.FY,
				"opens_at": add_days(now, -1),
				"closes_at": add_days(now, 1),
				"record_version": 1,
				"fixture_namespace": NS_KEBS,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value(
			"Needs Intake Window",
			name,
			{"opens_at": add_days(now, -1), "closes_at": add_days(now, 1)},
			update_modified=False,
		)
	return name


def _build_kebs_need(spec: dict[str, Any]) -> dict[str, Any]:
	"""Drive one KEBS Need to Accepted through the real commands."""
	title = spec["title"]
	# Idempotent by title within the KEBS entity: the reference is generated by
	# the command, so the source line is matched on what it produced.
	already = frappe.db.sql(
		"""
		select n.name from `tabDepartmental Need` n
		join `tabDepartmental Need Version` v on v.departmental_need = n.name
		where n.procuring_entity = %s and v.title = %s limit 1
		""",
		(kebs_foundation.PE, title),
	)
	if already:
		need = already[0][0]
		return {"source_line": spec["source_line"], "need": need, "idempotent": True}

	with _as(KEBS_AUTHOR):
		created = lifecycle.create_need(
			procuring_entity=kebs_foundation.PE,
			organisation_unit=kebs_foundation.OU,
			financial_year=kebs_foundation.FY,
			title=title,
			description=spec["description"],
			expected_operational_result=spec["expected_operational_result"],
			indicative_quantity=spec["indicative_quantity"],
			unit=spec["unit"],
			required_by_date=KEBS_REQUIRED_BY,
			idempotency_key=key("kebs", "create", spec["source_line"]),
		)
		submitted = lifecycle.submit_need(
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=key("kebs", "submit", spec["source_line"], created["record_version"]),
		)
	task, token = _open_task(created["need"], "Initial acceptance")
	with _as(KEBS_REVIEWER):
		accepted = lifecycle.review_need(
			need=created["need"],
			decision="accept",
			task=task,
			expected_version=submitted["record_version"],
			decision_token=token,
			idempotency_key=key("kebs", "accept", spec["source_line"], submitted["record_version"]),
		)
	_namespace("Departmental Need", created["need"], NS_KEBS)
	_namespace("Departmental Need Version", accepted["current_accepted_version"], NS_KEBS)
	return {
		"source_line": spec["source_line"],
		"need": created["need"],
		"accepted_version": accepted["current_accepted_version"],
		"event_id": accepted["event_id"],
	}


def reset_kebs() -> dict[str, Any]:
	needs = frappe.get_all(
		"Departmental Need", filters={"procuring_entity": kebs_foundation.PE}, pluck="name"
	)
	if needs:
		for doctype in (
			"Departmental Need Event",
			"Departmental Need Decision",
			"Departmental Need Review Task",
			"Need Withdrawal Request",
		):
			frappe.db.delete(doctype, {"departmental_need": ("in", needs)})
		frappe.db.delete("Need Planning Usage Projection", {"departmental_need": ("in", needs)})
		frappe.db.delete("Departmental Need Version", {"departmental_need": ("in", needs)})
		frappe.db.delete("Departmental Need", {"name": ("in", needs)})
	frappe.db.delete("Needs Intake Window", {"fixture_namespace": NS_KEBS})
	return {"profile": "kebs", "removed": needs}


# --- registry ---------------------------------------------------------------

PROFILES: dict[str, tuple[Callable[[], Any], Callable[[], Any]]] = {
	"default": (lambda: base.upsert_departmental_needs(), lambda: {"profile": "default", "removed": []}),
	"planning_usage": (apply_planning_usage, reset_planning_usage),
	"successor": (apply_successor, reset_successor),
	"withdrawal_blocked": (apply_withdrawal_blocked, reset_withdrawal),
	"withdrawal_cleared": (apply_withdrawal_cleared, reset_withdrawal),
	"kebs": (apply_kebs, reset_kebs),
}


def _resolve(profile: str) -> tuple[Callable[[], Any], Callable[[], Any]]:
	if profile not in PROFILES:
		frappe.throw(
			f"Unknown Departmental Needs seed profile {profile!r}. "
			f"Available: {', '.join(sorted(PROFILES))}."
		)
	return PROFILES[profile]


def apply_profile(profile: str = "default", *, commit: bool = False) -> dict[str, Any]:
	"""§14.7 — apply one independently selectable profile."""
	apply_fn, _ = _resolve(profile)
	with _intake_open():
		result = apply_fn()
	if commit:
		frappe.db.commit()
	return result


def reset_profile(profile: str, *, commit: bool = False) -> dict[str, Any]:
	"""§14.7 — remove exactly what one profile created."""
	_, reset_fn = _resolve(profile)
	result = reset_fn()
	if commit:
		frappe.db.commit()
	return result
