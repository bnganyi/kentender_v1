# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright-only Departmental Needs fixtures, isolated from the §14 seed.

DEBT-07. The browser specs decide real tasks and overwrite the Needs-
submission state, so pointing them at the §14.3 demo Needs left those
fixtures changed and the Python suite red until the seed was rebuilt — twice,
during Phase 9. Worse, re-applying the `default` profile does **not** restore
a decided Need (`upsert_departmental_needs` is idempotent, not restorative),
so "reseed afterwards" is not a repair.

Isolation is now by a dedicated **Organisation Unit**, not a dedicated
Procuring Entity: AUTH-ADR-001 v1.6 §1.1 makes the site exactly one implicit
Procuring Entity, so the old PE-CGKIS isolation trick this file used no
longer exists as a mechanism, and — since CFG-BR-010 keeps at most one
Fiscal Year Open at a time — these fixtures necessarily share the same open
Fiscal Year (`kentender_mvp_r1.FY`) as the §14.3 default profile. That means
`need_reference` numbers (`NDS-{PE code}-{FY start}-####`) are no longer
generated in a separate sequence: a Playwright run and the default profile
now draw from the *same* counter. Every fixture below therefore only ever
depends on the reference its own command returns, never on a hardcoded
number — see FU-16 in `FOLLOW_UPS.md` for the full note and why the default
profile must seed before any Playwright spec touches this Fiscal Year.

Every row is stamped with NS_PW and `reset_all()` removes exactly those, so a
failed run cannot leave a half-built fixture behind — the failure mode §14.7
already warned about for the demo profiles.

Fixtures are driven through the real §8.2 commands, never written directly.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import frappe

from kentender_core.services import organisation_structure as structure
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.departmental_needs.constants import (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	TASK_OPEN,
)
from kentender_procurement.departmental_needs.seeds import kentender_mvp_r1 as base
from kentender_procurement.departmental_needs.services import lifecycle
from kentender_procurement.departmental_needs.services.usage import project_planning_usage

NS_PW = "KENTENDER_NDS_PLAYWRIGHT"

OU_NAME = "Playwright — Departmental Needs"
FY = base.FY

# A stable withdrawal reference: NDS-UI-07 prints it in the record kicker, so a
# generated (deliberately unguessable) id would make the visual baseline differ
# on every rebuild. The §14.5 profile renames its own fixture for the same
# reason.
WITHDRAWAL_REQUEST_ID = "NDS-WDR-PW-0001"

AUTHOR = "nds.pw.author@example.test"
REVIEWER = "nds.pw.reviewer@example.test"
PLANNER = "nds.pw.planner@example.test"

CONTENT = {
	"title": "County health records digitisation",
	"description": "Digitise paper health records across county facilities.",
	"expected_operational_result": (
		"County facilities can retrieve a patient record without a paper search."
	),
	"indicative_quantity": 12,
	"unit": "Each",
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


def _ensure_user(email: str, full_name: str) -> None:
	if frappe.db.exists("User", email):
		return
	first, _, last = full_name.partition(" ")
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first,
			"last_name": last,
			"send_welcome_email": 0,
			"user_type": "System User",
			"enabled": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.add_roles("Desk User")


def _fixture_unit() -> str:
	existing = frappe.db.get_value("Organisation Unit", {"unit_name": OU_NAME}, "name")
	if existing:
		return existing
	outcome = structure.add_organisation_unit(parent_id=structure._root(), name=OU_NAME)
	return outcome["unit"]


def _actor(email: str, full_name: str, business_role: str, *, scoped: bool) -> None:
	"""Create the actor once and grant it its one responsibility, idempotently."""
	_ensure_user(email, full_name)
	administration.grant(
		user=email,
		business_role=business_role,
		# §6/NDS-BR-001 — a departmental role must name its department, or this
		# module denies access rather than falling back to unrestricted.
		organisation_unit=_fixture_unit() if scoped else "",
		fixture_namespace=NS_PW,
		actor="Administrator",
	)


CONTEXT_PREFERENCE_KEYS = ("kt_needs_org_unit", "kt_needs_financial_year")


def _clear_context_preferences(*users: str) -> None:
	"""CTX-CHG-001 — the working context is a per-user SERVER preference now,
	so it survives across the serial spec files the way localStorage never
	did. Every fixture reset clears the actors' remembered context, keeping
	each spec file's starting state deterministic."""
	for user in users or (AUTHOR, REVIEWER, PLANNER):
		for key in CONTEXT_PREFERENCE_KEYS:
			frappe.defaults.clear_user_default(key, user)


def ensure_actors() -> dict[str, str]:
	"""Three single-context actors, one per §6 role the specs log in as."""
	_guard()
	_actor(AUTHOR, "Playwright Author", ROLE_DEPARTMENTAL_AUTHOR, scoped=True)
	_actor(REVIEWER, "Playwright Reviewer", ROLE_HEAD_OF_USER_DEPARTMENT, scoped=True)
	# §14.2 — the Planner is Site-wide; requiring a department of them would
	# deny the read access §6 grants.
	_actor(PLANNER, "Playwright Planner", ROLE_PROCUREMENT_PLANNER, scoped=False)
	_clear_context_preferences()
	return {"author": AUTHOR, "reviewer": REVIEWER, "planner": PLANNER}


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


def _submitted_need() -> str:
	"""A Need driven to Submitted with one Open Initial acceptance task."""
	unit = _fixture_unit()
	with base._as(AUTHOR):
		created = lifecycle.create_need(
			organisation_unit=unit,
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
	with base._as(REVIEWER):
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
	with base._as(AUTHOR):
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
	with base._as(REVIEWER):
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
	with base._as(PLANNER):
		project_planning_usage(
			departmental_need=need,
			accepted_version=accepted_version,
			usage="Not included" if cleared else "Fully included",
			source_event_id=_key(),
			active_plan="" if cleared else "PLN-NDS-PW-0001",
			active_plan_item="" if cleared else "PPI-NDS-PW-0001",
		)
	with base._as(AUTHOR):
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
	"""NDS-UI-01/03 — one Draft, so the editor is reachable.

	§5.1 gates creation and initial submission on the Needs-submission flag
	being Open; §14.1 requires it already Open on `FY` before any seed runs
	(kentender_core.seeds.site_setup owns it), so this fixture only builds
	the Draft — it never opens or closes the flag itself.
	"""
	_guard()
	reset_all()
	ensure_actors()
	unit = _fixture_unit()
	with base._as(AUTHOR):
		created = lifecycle.create_need(
			organisation_unit=unit,
			financial_year=FY,
			idempotency_key=_key(),
			**CONTENT,
		)
	_stamp(("Departmental Need", created["need"]))
	_stamp_children(created["need"])
	if commit:
		frappe.db.commit()
	return {"need": created["need"], "state": "Draft"}
