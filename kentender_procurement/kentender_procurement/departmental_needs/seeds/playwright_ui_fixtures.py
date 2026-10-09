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

from kentender_core.seeds.constants import TEST_PASSWORD
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
from kentender_procurement.departmental_needs.services.usage import (
	project_planning_disposition,
	project_planning_usage,
)

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
	"estimated_total_cost": 12000000,
	"required_by_date": "2028-03-31",
}

_NAMESPACED = (
	"Departmental Need Event",
	"Need Planning Usage Projection",
	"Departmental Need Decision",
	"Departmental Need Review Task",
	"Need Withdrawal Request",
	"Departmental Need Revision",
	"Departmental Need",
)


def _key() -> str:
	return f"nds-pw-{uuid4().hex}"


def now_marker() -> str:
	"""A `creation`-comparable timestamp for `purge_untagged_needs_since()`.

	`creation` is stored as a naive site-local (EAT) datetime string. A
	caller capturing "now" with something UTC-labelled (e.g. JavaScript's
	`Date.toISOString()`) is ~3 hours behind real EAT wall-clock once the
	'Z' is stripped by the DB comparison — the purge would then also catch
	everything created in that 3-hour gap, not just what ran after it.
	`frappe.utils.now()` is already in the right format and timezone."""
	return frappe.utils.now()


def _guard() -> None:
	"""Never build demo actors or fixtures on a production site."""
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"Departmental Needs Playwright fixtures are test data. Enable developer_mode "
		"or allow_tests on this site before building them."
	)


def _ensure_user(email: str, full_name: str) -> None:
	if not frappe.db.exists("User", email):
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
	# Every reset must leave the actor able to log in with the standard test
	# password, whether the User row is brand new or already existed — a plain
	# insert() sets no password at all, which silently made every NDS
	# Playwright actor unable to authenticate (found live: "Invalid Login" for
	# an actor `ensure_actors()` had already created). Matches
	# kentender_core.seeds._common.upsert_seed_user's own unconditional
	# `update_password(...)` call.
	from frappe.utils.password import update_password

	update_password(email, TEST_PASSWORD)


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


def purge_untagged_needs_since(since: str, *, commit: bool = True) -> dict[str, Any]:
	"""Remove `Departmental Need` rows (and everything under them) a UI-driven
	test minted directly through a real create/submit/propose-change click,
	never through a fixture builder — so never stamped with a namespace
	`reset_all()` can find.

	`departmental-needs-fidelity.spec.ts` reaches several states this way
	(NDS-DES-04/08/09). Each pass mints a brand-new, unstamped `Departmental
	Need` under the real `NDS-MOH-2027-####` series; left alone these
	accumulate forever. Scoped to `since` (an ISO timestamp, normally the
	spec's own start time) so the §14 canonical seed Needs — created long
	before any test runs, and already excluded by the namespace filter — are
	never at risk even if that filter were ever absent.
	"""
	_guard()
	needs = frappe.db.get_all(
		"Departmental Need",
		filters={"fixture_namespace": ["is", "not set"], "creation": [">=", since]},
		pluck="name",
	)
	removed: dict[str, int] = {}
	if needs:
		for doctype in _NAMESPACED:
			if doctype == "Departmental Need":
				names = needs
			else:
				names = frappe.db.get_all(doctype, filters={"departmental_need": ("in", needs)}, pluck="name")
			if names:
				frappe.db.delete(doctype, {"name": ("in", names)})
			removed[doctype] = len(names)
		# Not in `_NAMESPACED` — Planning-owned, but it links back to us and a
		# leaked Need would otherwise leave it pointing at a deleted row.
		projections = frappe.db.get_all(
			"Need Planning Disposition Projection", filters={"departmental_need": ("in", needs)}, pluck="name"
		)
		if projections:
			frappe.db.delete("Need Planning Disposition Projection", {"name": ("in", projections)})
		removed["Need Planning Disposition Projection"] = len(projections)
		removed["Need Planning Intake Projection"] = _delete_leaked_planning_positions(needs)
		frappe.db.delete("Notification Log", {"document_type": "Departmental Need", "document_name": ("in", needs)})
	if commit:
		frappe.db.commit()
	return {"since": since, "removed": removed}


def _delete_leaked_disposition_projections(needs: list[str]) -> int:
	"""`Need Planning Disposition Projection` is Planning-owned (PLN-CHG-001
	v1.18 §5.1.4) and links back to us, but is deliberately not in
	`_NAMESPACED` (that tuple is this module's own doctypes) — so a plain
	per-doctype namespace sweep never touches it. Its own document name
	(`{need}-V{n}`) is deterministic, and a deleted Need's reference/revision
	names are free for the next `create_need()` to reuse (§14.7's reference
	counter only sees what currently exists) — so without this, an old
	fixture run's disposition (FU-31's `reset_disposition_*_fixture`s are the
	first callers here to actually create one) silently reattaches itself to
	whatever Need next lands on the same reused reference number. Found live
	2026-09-23: a `reset_disposition_none_fixture` rebuild inherited an
	earlier run's `Not proceeding` disposition through exactly this path."""
	if not needs:
		return 0
	rows = frappe.db.get_all(
		"Need Planning Disposition Projection", filters={"departmental_need": ("in", needs)}, pluck="name"
	)
	if rows:
		frappe.db.delete("Need Planning Disposition Projection", {"name": ("in", rows)})
	return len(rows)


def _delete_leaked_planning_positions(needs: list[str]) -> int:
	"""`Need Planning Intake Projection` — Planning's position for an accepted
	Need, named after the Need itself — has the same reused-reference hazard
	as the disposition projection above: left behind, it would tell the next
	Need to take that reference that it is missing from its plan."""
	if not needs:
		return 0
	rows = frappe.db.get_all("Need Planning Intake Projection", filters={"departmental_need": ("in", needs)}, pluck="name")
	if rows:
		frappe.db.delete("Need Planning Intake Projection", {"name": ("in", rows)})
	return len(rows)


def reset_all(*, commit: bool = False) -> dict[str, Any]:
	"""Remove every Playwright-owned row, leaving the §14 seed untouched."""
	_guard()
	needs = frappe.db.get_all("Departmental Need", filters={"fixture_namespace": NS_PW}, pluck="name")
	removed = {}
	for doctype in _NAMESPACED:
		names = frappe.db.get_all(doctype, filters={"fixture_namespace": NS_PW}, pluck="name")
		if names:
			frappe.db.delete(doctype, {"name": ("in", names)})
		removed[doctype] = len(names)
	removed["Need Planning Disposition Projection"] = _delete_leaked_disposition_projections(needs)
	removed["Need Planning Intake Projection"] = _delete_leaked_planning_positions(needs)
	# A deleted Need's reference is free for the next command to reuse (§14.7's
	# reference counter only sees what currently exists), so a stray
	# Notification Log row addressed to the old `document_name` would
	# otherwise leak into whatever Need is next assigned that same reference.
	if needs:
		frappe.db.delete("Notification Log", {"document_type": "Departmental Need", "document_name": ("in", needs)})
	if commit:
		frappe.db.commit()
	return {"namespace": NS_PW, "removed": removed}


def _stamp(*rows: tuple[str, str], namespace: str = NS_PW) -> None:
	for doctype, name in rows:
		if name:
			frappe.db.set_value(doctype, name, "fixture_namespace", namespace, update_modified=False)


def _stamp_children(need: str, namespace: str = NS_PW) -> None:
	"""Stamp everything the commands created for this Need, whatever its type."""
	for doctype in _NAMESPACED:
		if doctype == "Departmental Need":
			continue
		for name in frappe.db.get_all(doctype, filters={"departmental_need": need}, pluck="name"):
			frappe.db.set_value(doctype, name, "fixture_namespace", namespace, update_modified=False)


# --- fixtures a sibling module's browser specs ask NDS for -------------------
#
# Procurement Planning's Playwright world needs genuine accepted Needs in its
# own Organisation Unit and Fiscal Year (PLN-CHG-001 v1.12 D13). Planning may
# not drive this module's commands or tables (its architecture guard, D5),
# so NDS owns the builders: the caller names its unit, year, actors (who must
# hold the departmental responsibilities there) and content; NDS runs the real
# commands as those actors, stamps the rows with the caller's namespace and
# purges them on request.


def purge_fixture_needs(*, namespace: str, commit: bool = True) -> dict[str, Any]:
	"""Remove every NDS row stamped with `namespace` (a sibling fixture world)."""
	_guard()
	if namespace == NS_PW:
		return reset_all(commit=commit)
	needs = frappe.db.get_all("Departmental Need", filters={"fixture_namespace": namespace}, pluck="name")
	removed = {}
	for doctype in _NAMESPACED:
		names = frappe.db.get_all(doctype, filters={"fixture_namespace": namespace}, pluck="name")
		if names:
			frappe.db.delete(doctype, {"name": ("in", names)})
		removed[doctype] = len(names)
	removed["Need Planning Disposition Projection"] = _delete_leaked_disposition_projections(needs)
	removed["Need Planning Intake Projection"] = _delete_leaked_planning_positions(needs)
	if needs:
		frappe.db.delete("Notification Log", {"document_type": "Departmental Need", "document_name": ("in", needs)})
	if commit:
		frappe.db.commit()
	return {"namespace": namespace, "removed": removed}


def reset_accepted_needs_for(
	*,
	organisation_unit_name: str,
	financial_year: str,
	author: str,
	reviewer: str,
	needs: list[dict[str, Any]] | str,
	namespace: str,
	commit: bool = True,
) -> dict[str, Any]:
	"""Purge the namespace, then drive each requested Need to Accepted for
	planning through the real commands as the caller's own actors."""
	import json

	_guard()
	if isinstance(needs, str):
		needs = json.loads(needs)
	purge_fixture_needs(namespace=namespace, commit=False)
	unit = frappe.db.get_value("Organisation Unit", {"unit_name": organisation_unit_name}, "name")
	if not unit:
		frappe.throw(f"Organisation Unit '{organisation_unit_name}' does not exist — build the caller's world first.")
	if not frappe.db.get_value("Fiscal Year", financial_year, "kentender_needs_submission_open"):
		frappe.throw(f"Fiscal Year {financial_year}'s Needs-submission flag is not Open — the caller's world must open it first.")
	accepted = []
	for content in needs:
		with base._as(author):
			created = lifecycle.create_need(organisation_unit=unit, financial_year=financial_year, idempotency_key=_key(), **content)
			lifecycle.submit_need(need=created["need"], expected_version=created["record_version"], idempotency_key=_key())
		task = _open_task(created["need"])
		with base._as(reviewer):
			lifecycle.review_need(
				need=created["need"], decision="accept", task=task["name"], expected_version=_record_version(created["need"]),
				decision_token=task["decision_token"], idempotency_key=_key(),
			)
		_stamp(("Departmental Need", created["need"]), namespace=namespace)
		_stamp_children(created["need"], namespace)
		accepted.append(created["need"])
	if commit:
		frappe.db.commit()
	return {"needs": accepted, "unit": unit}


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
	"""NDS-UI-06 — an accepted Need whose Revision 1 has been superseded.

	The pinned-revision path (`/{reference}/accepted/{n}`) only means anything
	once a superseded revision exists to pin: §12.4 requires the earlier revision
	to stay readable and to name the current one without redirecting.
	"""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	superseded = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
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
		"superseded_revision": superseded,
		"current_accepted_revision": frappe.db.get_value(
			"Departmental Need", need, "current_accepted_revision"
		),
	}


def _withdrawal_fixture(*, cleared: bool) -> dict[str, Any]:
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	accepted_revision = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")

	# §5.3 — only an Effective allocation on the exact accepted version blocks
	# the decision, and Needs learns it from the §4.7 projection, never from
	# Planning's tables (firm D1 boundary). So report it the way Planning does.
	with base._as(PLANNER):
		project_planning_usage(
			departmental_need=need,
			accepted_revision=accepted_revision,
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
	return {"need": need, "accepted_revision": accepted_revision, "cleared": cleared}


def reset_withdrawal_blocked_fixture() -> dict[str, Any]:
	"""NDS-UI-07 / NDS-DES-12a — an Active Plan dependency blocks the decision."""
	return _withdrawal_fixture(cleared=False)


def reset_withdrawal_cleared_fixture() -> dict[str, Any]:
	"""NDS-UI-07 / NDS-DES-12b — no dependency, so Approve and Decline stand."""
	return _withdrawal_fixture(cleared=True)


def reset_declined_need_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-DES-TERMINAL (decline) — a Submitted Need declined outright ("Do
	not take forward"), the terminal `Not taken forward` state a real
	initial-acceptance decline leaves behind, reason and decider intact."""
	_guard()
	reset_all()
	ensure_actors()
	need = _submitted_need()
	task = _open_task(need)
	with base._as(REVIEWER):
		lifecycle.review_need(
			need=need,
			decision="decline",
			task=task["name"],
			expected_version=_record_version(need),
			decision_token=task["decision_token"],
			idempotency_key=_key(),
			reason="This requirement is already covered by an existing enterprise service.",
		)
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need}


def reset_withdrawn_need_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-DES-TERMINAL (withdrawal) — a Submitted Need returned for
	correction, then withdrawn by its own Author before resubmission (§5.1) —
	the terminal `Withdrawn` state a real self-service withdrawal leaves
	behind. No reason: §5.1's withdraw command collects none."""
	_guard()
	reset_all()
	ensure_actors()
	need = _submitted_need()
	task = _open_task(need)
	with base._as(REVIEWER):
		lifecycle.review_need(
			need=need,
			decision="return",
			task=task["name"],
			expected_version=_record_version(need),
			decision_token=task["decision_token"],
			idempotency_key=_key(),
			reason="Confirm the figures before resubmitting.",
		)
	with base._as(AUTHOR):
		lifecycle.withdraw_need(
			need=need,
			expected_version=_record_version(need),
			idempotency_key=_key(),
		)
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need}


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


# --- NDS-CHG-001 v1.14 §11.8A Planning-status variants (FOLLOW_UPS FU-31) --
#
# `NeedDetailScreen.vue`/`WithdrawalReviewScreen.vue` distinguish REFRESHING/
# UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT/OLDER/DES-12-UNAVAILABLE by how a spec
# treats the network response for `get_need_planning_status` (or, for
# DES-12-UNAVAILABLE, `check_accepted_need_withdrawal_dependency`) on top of
# one of the plain data profiles below — never by a different data shape of
# their own (the artboards' own fixture notes say exactly this: "refresh in
# progress from STILL-ACTIVE", "failed refresh from STILL-ACTIVE", "same
# unavailable profile with no supplied snapshot"). These builders exist so a
# spec has that plain data profile to reuse; the route-level failure/delay is
# the spec's own concern (`page.route()`), not the fixture's.


def reset_disposition_none_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-SC-DISPOSITION-NONE (§14.6A) — an Accepted Need Planning has never
	reported on at all: empty accepted-disposition history, no Active
	inclusion. `NeedDetailScreen.vue`'s `hasPlanningSnapshot` is false for
	this Need (`disposition.recorded`/`usage.recorded` both false, no
	`olderUsage`), which is exactly what turns a failed
	`get_need_planning_status` re-check into UNAVAILABLE-NO-SNAPSHOT rather
	than plain UNAVAILABLE."""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	if commit:
		frappe.db.commit()
	return {
		"need": need,
		"accepted_revision": frappe.db.get_value("Departmental Need", need, "current_accepted_revision"),
	}


def reset_disposition_still_active_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-SC-EXCLUDED-STILL-ACTIVE (§14.6A) — the accepted departmental
	disposition is `Not proceeding`, but the current annual plan still
	reports the same accepted revision `Fully included` (Planning has not
	yet caught up). `NeedDetailScreen.vue`'s `stillActive`/`hasPlanningSnapshot`
	are both true for this Need — the real base NDS-DES-07A-STILL-ACTIVE
	renders from, and (per the artboard's own fixture notes) what
	NDS-DES-07A-REFRESHING/UNAVAILABLE mock the `get_need_planning_status`
	route on top of, rather than building a separate data shape."""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	accepted_revision = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
	with base._as(PLANNER):
		project_planning_usage(
			departmental_need=need,
			accepted_revision=accepted_revision,
			usage="Fully included",
			source_event_id=_key(),
			active_plan="PLN-NDS-PW-STILL-ACTIVE",
			active_plan_item="PPI-NDS-PW-STILL-ACTIVE",
		)
		project_planning_disposition(
			departmental_need=need,
			need_revision=accepted_revision,
			dpp_submission="DPP-NDS-PW-STILL-ACTIVE",
			disposition="Not proceeding",
			source_event_id=_key(),
			producer_sequence=1,
			reason="The department no longer requires this line in the current annual plan.",
		)
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need, "accepted_revision": accepted_revision}


def reset_older_revision_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-SC-OLDER-REVISION-ACTIVE (§14.6A) — Revision 2 is accepted while
	Revision 1's own inclusion is still `Fully included` and Revision 2 has
	no projection of its own yet, so the current annual plan still uses the
	previously accepted details (§11.8A OLDER). Reuses, through the fixture
	layer, the exact command sequence
	`test_older_revision_usage_walks_back_when_current_revision_is_unprojected`
	(test_departmental_needs_lifecycle.py) already proves at the service
	layer: accept Revision 1, project its usage Fully included, open and
	accept a successor Revision 2, and never project Revision 2 itself."""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	revision_1 = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
	with base._as(PLANNER):
		project_planning_usage(
			departmental_need=need,
			accepted_revision=revision_1,
			usage="Fully included",
			source_event_id=_key(),
			active_plan="PLN-NDS-PW-OLDER",
			active_plan_item="PPI-NDS-PW-OLDER",
		)
	with base._as(AUTHOR):
		opened = lifecycle.create_accepted_need_successor(
			need=need, expected_version=_record_version(need), idempotency_key=_key()
		)
		saved = lifecycle.update_need(
			need=need,
			expected_version=opened["record_version"],
			idempotency_key=_key(),
			**{**CONTENT, "required_by_date": "2028-06-30"},
		)
		lifecycle.submit_need(need=need, expected_version=saved["record_version"], idempotency_key=_key())
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
	revision_2 = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need, "revision_1": revision_1, "revision_2": revision_2}


# --- more NDS-DES-07A Planning-status variants (structural fidelity only) --
#
# These three complete the 5-variant set FU-27/FU-31 named as shipped
# (NONE/PROCEEDING/EXCLUDED/STILL-ACTIVE/RESTORED); NONE and STILL-ACTIVE
# already exist above. Every state here is a plain, already-built data
# profile — no REFRESHING/UNAVAILABLE/OLDER route mocking involved.


def reset_disposition_proceeding_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-DES-07A-PROCEEDING — the accepted departmental disposition is
	`Proceeding` (in the departmental plan), but Planning has not reported
	any Active-plan inclusion for this revision yet."""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	accepted_revision = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
	with base._as(PLANNER):
		project_planning_disposition(
			departmental_need=need,
			need_revision=accepted_revision,
			dpp_submission="DPP-NDS-PW-PROCEEDING",
			disposition="Proceeding",
			source_event_id=_key(),
			producer_sequence=1,
		)
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need, "accepted_revision": accepted_revision}


def reset_disposition_excluded_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-DES-07A-EXCLUDED — the accepted departmental disposition is `Not
	proceeding`, with no Active-plan inclusion at all (distinct from
	STILL-ACTIVE, where the annual plan has not caught up to the exclusion
	yet)."""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	accepted_revision = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
	with base._as(PLANNER):
		project_planning_disposition(
			departmental_need=need,
			need_revision=accepted_revision,
			dpp_submission="DPP-NDS-PW-EXCLUDED",
			disposition="Not proceeding",
			source_event_id=_key(),
			producer_sequence=1,
			reason="The department will pursue this requirement in a later annual planning cycle.",
		)
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need, "accepted_revision": accepted_revision}


def reset_disposition_restored_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-DES-07A-RESTORED — a later departmental submission restores a
	previously `Not proceeding` disposition back to `Proceeding` (two
	disposition events, newest `producer_sequence` wins), and the current
	annual plan already reports this revision `Fully included` — so
	`stillActive` is false (the annual plan reads plain "Included", not
	"Still included") and both "View annual plan item" facts apply."""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	accepted_revision = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
	with base._as(PLANNER):
		project_planning_disposition(
			departmental_need=need,
			need_revision=accepted_revision,
			dpp_submission="DPP-NDS-PW-RESTORED-2",
			disposition="Not proceeding",
			source_event_id=_key(),
			producer_sequence=1,
			reason="The department will pursue this requirement in a later annual planning cycle.",
		)
		project_planning_disposition(
			departmental_need=need,
			need_revision=accepted_revision,
			dpp_submission="DPP-NDS-PW-RESTORED-3",
			disposition="Proceeding",
			source_event_id=_key(),
			producer_sequence=2,
		)
		project_planning_usage(
			departmental_need=need,
			accepted_revision=accepted_revision,
			usage="Fully included",
			source_event_id=_key(),
			active_plan="PLN-NDS-PW-RESTORED",
			active_plan_item="PPI-NDS-PW-RESTORED",
		)
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need, "accepted_revision": accepted_revision}


# --- NDS-DES-01/08/11 structural-variant fixtures ---------------------------


def reset_author_returned_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-DES-01-RETURNED — the Author's own "My needs" register with a
	Submitted need and a Returned (awaiting correction) need both visible
	(also covers NDS-DES-01-SUBMITTED's single-row case)."""
	_guard()
	reset_all()
	ensure_actors()
	submitted_need = _submitted_need()
	returned_need = _submitted_need()
	task = _open_task(returned_need)
	with base._as(REVIEWER):
		lifecycle.review_need(
			need=returned_need,
			decision="return",
			task=task["name"],
			expected_version=_record_version(returned_need),
			decision_token=task["decision_token"],
			idempotency_key=_key(),
			reason="Confirm the quantity against the current cohort.",
		)
	_stamp_children(returned_need)
	if commit:
		frappe.db.commit()
	return {"submitted_need": submitted_need, "returned_need": returned_need}


def reset_successor_draft_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-DES-08-DRAFT / NDS-DES-11-OPEN-UPDATE — an accepted Need with an
	open successor left at Draft (created, never submitted)."""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	with base._as(AUTHOR):
		lifecycle.create_accepted_need_successor(
			need=need, expected_version=_record_version(need), idempotency_key=_key()
		)
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need}


def reset_successor_submitted_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-DES-08-SUBMITTED / NDS-DES-08-OTHER-AUTHOR — an accepted Need with
	an open successor submitted for review (an open Successor-acceptance
	task nobody has decided yet)."""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	with base._as(AUTHOR):
		opened = lifecycle.create_accepted_need_successor(
			need=need, expected_version=_record_version(need), idempotency_key=_key()
		)
		saved = lifecycle.update_need(
			need=need,
			expected_version=opened["record_version"],
			idempotency_key=_key(),
			**{**CONTENT, "required_by_date": "2028-06-30"},
		)
		lifecycle.submit_need(need=need, expected_version=saved["record_version"], idempotency_key=_key())
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need, "task": _open_task(need)["name"]}


def reset_withdrawal_requested_still_active_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""NDS-DES-11-REQUESTED — a withdrawal request already open against a
	STILL-ACTIVE accepted Need (departmental disposition `Not proceeding`,
	current annual plan still `Fully included`), so the request itself is
	blocked pending a Planning change."""
	_guard()
	reset_all()
	ensure_actors()
	need = _accepted_need()
	accepted_revision = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
	with base._as(PLANNER):
		project_planning_usage(
			departmental_need=need,
			accepted_revision=accepted_revision,
			usage="Fully included",
			source_event_id=_key(),
			active_plan="PLN-NDS-PW-REQUESTED",
			active_plan_item="PPI-NDS-PW-REQUESTED",
		)
		project_planning_disposition(
			departmental_need=need,
			need_revision=accepted_revision,
			dpp_submission="DPP-NDS-PW-REQUESTED",
			disposition="Not proceeding",
			source_event_id=_key(),
			producer_sequence=1,
			reason="The department will pursue this requirement in a later annual planning cycle.",
		)
	with base._as(AUTHOR):
		lifecycle.request_withdrawal(
			need=need,
			expected_version=_record_version(need),
			idempotency_key=_key(),
			reason=(
				"The programme will not proceed in FY 2027/28 because implementation "
				"responsibility has moved outside the department."
			),
		)
	_stamp_children(need)
	if commit:
		frappe.db.commit()
	return {"need": need, "accepted_revision": accepted_revision}
