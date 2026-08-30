# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright-only Departmental Needs fixtures, isolated from the §14 seed.

DEBT-07. The browser specs decide real tasks and overwrite the intake window,
so pointing them at the §14.3 demo Needs left those fixtures changed and the
Python suite red until the seed was rebuilt — twice, during Phase 9. Worse,
re-applying the `default` profile does **not** restore a decided Need
(`upsert_departmental_needs` is idempotent, not restorative), so "reseed
afterwards" is not a repair.

`kentender_budget.seeds.playwright_ui_fixtures` solved the same problem by
giving the UI suite its own records; this is the Departmental Needs equivalent.

Isolation is by **Procuring Entity**, not just by namespace. `need_reference`
is generated per PE and financial year (`NDS-{PE code}-{FY start}-{4 digits}`),
and the §14 seed asserts it gets exactly NDS-MOH-2027-0001..0004 when built
from empty — so a Playwright Need created under PE-MOH would consume the next
reference in that same sequence and break a later clean reseed. PE-CGKIS has
its own sequence, its own intake window, and exactly one Active Organisation
Unit, which also means these actors resolve a single context and never meet the
§12.1 picker.

Every row is stamped with NS_PW and `reset_all()` removes exactly those, so a
failed run cannot leave a half-built fixture behind — the failure mode §14.7
already warned about for the demo profiles.

Fixtures are driven through the real §8.2 commands, never written directly.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import frappe

from kentender_procurement.departmental_needs.constants import ROLE_HEAD_OF_USER_DEPARTMENT
from kentender_procurement.departmental_needs.constants import (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_PROCUREMENT_PLANNER,
	TASK_OPEN,
	USAGE_FULL,
	USAGE_NOT_INCLUDED,
)
from kentender_procurement.departmental_needs.seeds import kentender_mvp_r1 as base
from kentender_procurement.departmental_needs.seeds.profiles import _as
from kentender_procurement.departmental_needs.services import lifecycle
from kentender_procurement.departmental_needs.services.usage import project_planning_usage

NS_PW = "KENTENDER_NDS_PLAYWRIGHT"

PE = "PE-CGKIS"
OU = "CGK-DEPT-HEALTH"
FY = "FY-2027-2028"
WINDOW = f"NDS-IW-{PE}-{FY}"
# A stable withdrawal reference: NDS-UI-07 prints it in the record kicker, so a
# generated (deliberately unguessable) id would make the visual baseline differ
# on every rebuild. The §14.5 profile renames its own fixture for the same
# reason.
WITHDRAWAL_REQUEST_ID = "NDS-WDR-CGKIS-PW-0001"

AUTHOR = "nds.pw.author@example.test"
REVIEWER = "nds.pw.reviewer@example.test"
PLANNER = "nds.pw.planner@example.test"

# The intake spec rewrites these freely; nothing else reads them.
# Far-future instants so the derived state ("Scheduled") and every rendered
# date stay identical run after run — the NDS-908 baselines capture them
# literally, so instants near *now* make the visual suite rot on a calendar
# boundary (the previous 2026-09-01 open would have flipped the DES-10 chip
# to "Open" on that day).
WINDOW_OPENS = "2097-07-01 00:00:00"
WINDOW_CLOSES = "2098-06-30 23:59:59"

CONTENT = {
	"title": "County health records digitisation",
	"description": "Digitise paper health records across county facilities.",
	"expected_operational_result": (
		"County facilities can retrieve a patient record without a paper search."
	),
	"indicative_quantity": 12,
	"unit": "UNIT-EACH",
	"required_by_date": "2028-03-31",
}

_NAMESPACED = (
	"Departmental Need Event",
	"Need Planning Usage Projection",
	"Departmental Need Decision",
	"Departmental Need Review Task",
	"Need Withdrawal Request",
	"Departmental Need Version",
	"Departmental Need",
)


def _key() -> str:
	return f"nds-pw-{uuid4().hex}"


def _guard() -> None:
	"""Never build demo actors or fixtures on a production site."""
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"Departmental Needs Playwright fixtures are test data. Enable developer_mode "
		"or allow_tests on this site before building them."
	)


def _actor(email: str, full_name: str, roles: tuple[str, ...], *, unit: bool) -> None:
	"""Create the actor once, then leave it alone.

	`base._user` saves the User twice (add_roles, then update_password), so
	re-running it for an actor that is already correct raises
	TimestampMismatchError on the second fixture build in the same request —
	every fixture calls `ensure_actors`, so that is the normal path, not an
	edge case.
	"""
	wanted_scope = [("Procuring Entity", PE), ("Financial Year", FY)]
	if unit:
		# §6/NDS-BR-001 — a departmental role must name its department, or this
		# module denies access rather than falling back to unrestricted.
		wanted_scope.append(("Organisation Unit", OU))

	if frappe.db.exists("User", email):
		held = {row.role for row in frappe.get_doc("User", email).roles}
		scoped = all(
			frappe.db.exists("User Permission", {"user": email, "allow": d, "for_value": v})
			for d, v in wanted_scope
		)
		if set(roles).issubset(held) and scoped:
			return

	base._user(email, full_name, roles)
	for doctype, value in wanted_scope:
		base._user_permission(email, doctype, value)


def ensure_actors() -> dict[str, str]:
	"""Three single-context actors, one per §6 role the specs log in as."""
	_guard()
	_actor(AUTHOR, "Playwright Author", (ROLE_DEPARTMENTAL_AUTHOR,), unit=True)
	_actor(REVIEWER, "Playwright Reviewer", (ROLE_HEAD_OF_USER_DEPARTMENT,), unit=True)
	# §14.2 — the Planner is scoped by PE and FY only; requiring a department
	# of them would deny the read access §6 grants.
	_actor(PLANNER, "Playwright Planner", (ROLE_PROCUREMENT_PLANNER,), unit=False)
	return {"author": AUTHOR, "reviewer": REVIEWER, "planner": PLANNER}


def ensure_window(opens_at: str = WINDOW_OPENS, closes_at: str = WINDOW_CLOSES) -> str:
	"""The fixture PE/FY's own intake window, free for the specs to rewrite."""
	if frappe.db.exists("Needs Intake Window", WINDOW):
		frappe.db.set_value(
			"Needs Intake Window",
			WINDOW,
			{"opens_at": opens_at, "closes_at": closes_at},
			update_modified=False,
		)
		return WINDOW
	frappe.get_doc(
		{
			"doctype": "Needs Intake Window",
			"needs_intake_window_id": WINDOW,
			"procuring_entity": PE,
			"financial_year": FY,
			"opens_at": opens_at,
			"closes_at": closes_at,
			"record_version": 0,
			"fixture_namespace": NS_PW,
		}
	).insert(ignore_permissions=True)
	return WINDOW


def reset_all(*, commit: bool = False) -> dict[str, Any]:
	"""Remove every Playwright-owned row, leaving the §14 seed untouched."""
	_guard()
	removed = {}
	for doctype in _NAMESPACED:
		names = frappe.db.get_all(doctype, filters={"fixture_namespace": NS_PW}, pluck="name")
		if names:
			frappe.db.delete(doctype, {"name": ("in", names)})
		removed[doctype] = len(names)
	if commit:
		frappe.db.commit()
	return {"namespace": NS_PW, "removed": removed}


def _stamp(*rows: tuple[str, str]) -> None:
	for doctype, name in rows:
		if name:
			frappe.db.set_value(doctype, name, "fixture_namespace", NS_PW, update_modified=False)


def _stamp_children(need: str) -> None:
	"""Stamp everything the commands created for this Need, whatever its type."""
	for doctype in _NAMESPACED:
		if doctype == "Departmental Need":
			continue
		for name in frappe.db.get_all(doctype, filters={"departmental_need": need}, pluck="name"):
			frappe.db.set_value(doctype, name, "fixture_namespace", NS_PW, update_modified=False)


def _open_window_now() -> None:
	"""§5.1 gates creation and initial submission on an Open window.

	The instants are fixed, not derived from *now*: the workspace chip renders
	the literal close instant ("Open until 30 Aug 2026, 10:59 AM EAT"), so a
	rolling ``now + 1 day`` close bakes the capture minute into the NDS-908
	visual baselines — they could only ever match again on the day (and near
	the minute) they were recorded. A close far in the future keeps the state
	Open for every run and the rendered text identical.
	"""
	ensure_window("2026-07-01 00:00:00", "2098-06-30 23:59:59")


def _submitted_need() -> str:
	"""A Need driven to Submitted with one Open Initial acceptance task."""
	_open_window_now()
	with _as(AUTHOR):
		created = lifecycle.create_need(
			procuring_entity=PE,
			organisation_unit=OU,
			financial_year=FY,
			idempotency_key=_key(),
			**CONTENT,
		)
		lifecycle.submit_need(
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=_key(),
		)
	_stamp(("Departmental Need", created["need"]))
	_stamp_children(created["need"])
	return created["need"]


def _open_task(need: str) -> dict[str, str]:
	return frappe.db.get_value(
		"Departmental Need Review Task",
		{"departmental_need": need, "status": TASK_OPEN},
		["name", "decision_token"],
		as_dict=True,
	)


def _record_version(need: str) -> int:
	return int(frappe.db.get_value("Departmental Need", need, "record_version") or 0)


def _accepted_need() -> str:
	need = _submitted_need()
	task = _open_task(need)
	with _as(REVIEWER):
		lifecycle.review_need(
			need=need,
			decision="accept",
			task=task["name"],
			expected_version=_record_version(need),
			decision_token=task["decision_token"],
			idempotency_key=_key(),
		)
	_stamp_children(need)
	return need


# --- the fixtures each spec asks for ---------------------------------------


def reset_review_task_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-UI-05 — one Submitted Need with an open acceptance decision."""
	_guard()
	reset_all()
	ensure_actors()
	need = _submitted_need()
	if commit:
		frappe.db.commit()
	return {"need": need, "reference": need, "task": _open_task(need)["name"]}


def reset_accepted_source_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-UI-06 — an accepted Need whose Version 1 has been superseded.

	The pinned-version path (`/{reference}/accepted/{n}`) only means anything
	once a superseded version exists to pin: §12.4 requires the earlier version
	to stay readable and to name the current one without redirecting.
	"""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	superseded = frappe.db.get_value("Departmental Need", need, "current_accepted_version")
	with _as(AUTHOR):
		opened = lifecycle.create_accepted_need_successor(
			need=need, expected_version=_record_version(need), idempotency_key=_key()
		)
		saved = lifecycle.update_need(
			need=need,
			expected_version=opened["record_version"],
			idempotency_key=_key(),
			**{**CONTENT, "required_by_date": "2028-05-31"},
		)
		lifecycle.submit_need(
			need=need, expected_version=saved["record_version"], idempotency_key=_key()
		)
	task = _open_task(need)
	with _as(REVIEWER):
		lifecycle.review_need(
			need=need,
			decision="accept",
			task=task["name"],
			expected_version=_record_version(need),
			decision_token=task["decision_token"],
			idempotency_key=_key(),
		)
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {
		"need": need,
		"superseded_version": superseded,
		"current_accepted_version": frappe.db.get_value(
			"Departmental Need", need, "current_accepted_version"
		),
	}


def _withdrawal_fixture(*, cleared: bool) -> dict[str, Any]:
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	accepted_version = frappe.db.get_value("Departmental Need", need, "current_accepted_version")

	# §5.3 — only an Effective allocation on the exact accepted version blocks
	# the decision, and Needs learns it from the §4.7 projection, never from
	# Planning's tables (firm D1 boundary). So report it the way Planning does.
	with _as(PLANNER):
		project_planning_usage(
			departmental_need=need,
			accepted_version=accepted_version,
			usage=USAGE_NOT_INCLUDED if cleared else USAGE_FULL,
			source_event_id=_key(),
			active_plan="" if cleared else "PLN-NDS-PW-0001",
			active_plan_item="" if cleared else "PPI-NDS-PW-0001",
		)
	with _as(AUTHOR):
		requested = lifecycle.request_withdrawal(
			need=need,
			expected_version=_record_version(need),
			idempotency_key=_key(),
			reason=(
				"The county no longer requires this digitisation in the target financial year."
			),
		)
	generated = requested["withdrawal_request"]
	if generated != WITHDRAWAL_REQUEST_ID:
		# rename_doc repoints the review task and decision links with it.
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
	_stamp_children(need)
	frappe.db.commit()
	return {"need": need, "accepted_version": accepted_version, "cleared": cleared}


def reset_withdrawal_blocked_fixture() -> dict[str, Any]:
	"""NDS-UI-07 / NDS-DES-12a — an Active Plan dependency blocks the decision."""
	return _withdrawal_fixture(cleared=False)


def reset_withdrawal_cleared_fixture() -> dict[str, Any]:
	"""NDS-UI-07 / NDS-DES-12b — no dependency, so Approve and Decline stand."""
	return _withdrawal_fixture(cleared=True)


def reset_open_intake_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-UI-01/03 — an Open window plus one Draft, so the editor is reachable.

	§5.1 gates creation and initial submission on an Open window, and the
	fixture PE's default window is Scheduled (it exists to be rewritten by the
	NDS-UI-08 spec). This one is opened around *now* so the author can actually
	create and submit.
	"""
	_guard()
	reset_all()
	ensure_actors()
	_open_window_now()
	with _as(AUTHOR):
		created = lifecycle.create_need(
			procuring_entity=PE,
			organisation_unit=OU,
			financial_year=FY,
			idempotency_key=_key(),
			**CONTENT,
		)
	_stamp(("Departmental Need", created["need"]))
	_stamp_children(created["need"])
	if commit:
		frappe.db.commit()
	return {"need": created["need"], "state": "Draft"}


def reset_intake_window_fixture() -> dict[str, Any]:
	"""NDS-UI-08 — the fixture PE/FY window at known instants.

	Separate from the §14.1 MoH window precisely so the spec can save over it.
	"""
	_guard()
	ensure_actors()
	window = ensure_window()
	frappe.db.commit()
	return {"window": window, "opens_at": WINDOW_OPENS, "closes_at": WINDOW_CLOSES}
