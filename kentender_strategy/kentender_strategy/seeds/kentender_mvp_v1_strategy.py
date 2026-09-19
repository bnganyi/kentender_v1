# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.7 §14 seed contract — the single Ministry of Health plan.

Rebuilt for AUTH-ADR-001 v1.6's one-site-one-PE model (2026-09-05, FU-10):
the previous version of this file built a two-Procuring-Entity world (MOH +
Kisumu) using the now-dropped per-plan Procuring Entity link field and
a bespoke `User Permission` grant — neither can exist on a one-PE site. This
version drives the plan through the real governed commands
(`save_strategy_plan_draft`, `save_strategy_structure_draft`,
`transition_plan_version`) as the named §14.1 actors, who are granted their
Site-wide Strategy responsibility by `kentender_core.seeds.site_setup` — this
seed creates no user and no assignment of its own.

Entry points (`upsert_kentender_mvp_v1_strategy`, `clear_kentender_mvp_v1_strategy`)
keep their existing names/signatures — kentender_core's seed orchestrator and
clear pipeline import them by these exact names.

Identifier note (tracker decision log, 2026-08-24, carried forward): §14.3
illustrates the plan/node/indicator/target identifiers in a
`STR-`/`PIL-`/`PRG-`/`OBJ-` style distinct from this rebuild's actual
`{PE}-{TYPE}-####` generator (strategy_reference.py). Forcing the seed to
carry those literal strings would require weakening
`strategy_reference.REF_RE`'s correction-format guard for every caller, not
just the seed. Titles, dates, actors, hierarchy shape and target values are
seeded exactly as specified; identifiers are whatever the real,
already-tested reference generator deterministically produces.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime

from kentender_strategy.services.strategy_transitions import transition_plan_version
from kentender_strategy.services.strategy_writes import (
	create_strategy_successor_version,
	save_strategy_plan_draft,
	save_strategy_structure_draft,
)

FY_2027_2028 = "2027-2028"
FIXTURE_NS = "str-chg-001-mvp1"

PLAN_TITLE = "Ministry of Health Strategic Plan"

# STR-CHG-001 v1.7 §14.1 / KT-STD-001 §8.3 — granted by site_setup.py, used
# here, never created or granted by this seed.
AUTHOR = "esther.muthoni@moh.example.test"
APPROVER = "alfred.ochieng@moh.example.test"


def _ensure_config_prerequisites() -> None:
	"""§14.2 — fail closed, never create/infer, never pick a fallback record."""
	if not frappe.db.exists("Fiscal Year", FY_2027_2028):
		frappe.throw(
			_("Missing Fiscal Year {0}").format(FY_2027_2028),
			frappe.ValidationError,
			title="STRATEGY_CONFIG_MISSING",
		)


def _run_as(user: str, fn, *args, **kwargs):
	frappe.set_user(user)
	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user("Administrator")


def _backdate_event(version_name: str, action: str, when: str) -> None:
	"""AGENTS.md §4.6 — narrow, documented timestamp-only direct write; the
	event itself is produced by the real transition service, only its
	recorded time is corrected to the seed's fixed fixture clock."""
	name = frappe.db.get_value(
		"Audit Event",
		{"document_type": "Strategic Plan Version", "document_name": version_name, "action": action},
		"name",
		order_by="creation desc",
	)
	if name:
		frappe.db.set_value("Audit Event", name, "timestamp", get_datetime(when), update_modified=False)


def _seed_moh_plan() -> dict[str, Any]:
	"""§14.3 — the one seeded plan, through the real domain/lifecycle
	services: draft, hierarchy, submit, approve (approve activates in the
	same transaction). Idempotent on the plan title; a second run returns
	the existing version untouched."""
	existing_plan = frappe.db.get_value("Strategic Plan", {"title": PLAN_TITLE}, "name")
	if existing_plan:
		existing_version = frappe.db.get_value(
			"Strategic Plan Version", {"plan_id": existing_plan, "version_number": 1}, "name"
		)
		# Heal a plan/version some other path left unstamped (found live: a
		# plan matching this exact title but fixture_namespace NULL, so
		# validate()'s namespace-scoped count found 0 despite the row
		# existing — the same "pre-existing unstamped row" gap Requisitions'
		# authorise_requisition() already had to heal for the same reason).
		if frappe.db.get_value("Strategic Plan", existing_plan, "fixture_namespace") != FIXTURE_NS:
			frappe.db.set_value("Strategic Plan", existing_plan, "fixture_namespace", FIXTURE_NS, update_modified=False)
		if existing_version and frappe.db.get_value("Strategic Plan Version", existing_version, "fixture_namespace") != FIXTURE_NS:
			frappe.db.set_value("Strategic Plan Version", existing_version, "fixture_namespace", FIXTURE_NS, update_modified=False)
		return {"ok": True, "plan": existing_plan, "plan_version": existing_version, "already_seeded": True}

	draft = _run_as(
		AUTHOR,
		save_strategy_plan_draft,
		{
			"title": PLAN_TITLE,
			"plan_role": "Primary",
			"period_start": "2023-07-01",
			"period_end": "2028-06-30",
			"effective_from": "2023-07-01",
			"effective_to": "2028-06-30",
		},
	)
	plan_id = draft["plan"]["plan_id"]
	version_id = draft["version"]["name"]

	_run_as(
		AUTHOR,
		save_strategy_structure_draft,
		version_id,
		nodes=[
			{"client_id": "$pillar", "node_type": "Pillar", "title": "Digital health systems", "display_order": 1},
			{
				"client_id": "$programme",
				"node_type": "Programme",
				"title": "Health policy, standards and regulation",
				"display_order": 2,
				"parent_node_id": "$pillar",
			},
			{
				"client_id": "$sub_programme",
				"node_type": "Sub-programme",
				"title": "Digital health governance",
				"display_order": 3,
				"parent_node_id": "$programme",
			},
			{
				"client_id": "$objective",
				"node_type": "Strategic Objective",
				"title": "Strengthen interoperable national digital health services",
				"display_order": 4,
				"parent_node_id": "$sub_programme",
			},
		],
		indicators=[
			{
				"client_id": "$indicator",
				"measures_node_id": "$objective",
				"indicator_name": "Percentage of priority facilities using interoperable digital health services",
				"definition": (
					"Priority facilities operating an approved interoperable digital health service "
					"divided by all priority facilities, expressed as a percentage."
				),
				"unit": "Percentage",
			}
		],
		targets=[
			{
				"indicator_id": "$indicator",
				"fiscal_year": FY_2027_2028,
				"comparison": "At least",
				"target_value": 80,
				"fixture_namespace": FIXTURE_NS,
			}
		],
	)

	_run_as(AUTHOR, transition_plan_version, version_id, "Submit for approval")
	_backdate_event(version_id, "Submit for approval", "2023-07-01 08:30:00")

	_run_as(APPROVER, transition_plan_version, version_id, "Approve")
	_backdate_event(version_id, "Approve", "2023-07-01 09:15:00")

	frappe.db.set_value("Strategic Plan", plan_id, "fixture_namespace", FIXTURE_NS, update_modified=False)
	frappe.db.set_value("Strategic Plan Version", version_id, "fixture_namespace", FIXTURE_NS, update_modified=False)

	return {"ok": True, "plan": plan_id, "plan_version": version_id}


def upsert_kentender_mvp_v1_strategy(*, reset: bool = False) -> dict[str, Any]:
	if reset:
		clear_kentender_mvp_v1_strategy()
	_ensure_config_prerequisites()
	moh = _seed_moh_plan()
	return {"ok": True, "moh": moh}


def clear_kentender_mvp_v1_strategy(
	*, include_canonical: bool = True, include_playwright: bool = True
) -> dict[str, Any]:
	"""Delete fixture-tagged Strategy records only — no broad wipe, and no
	deletion of the shared-register actor users (stable identities, owned by
	kentender_core.seeds.site_setup, not this file)."""
	deleted: dict[str, int] = {}
	# The only namespace this seed owns is the canonical one; Playwright
	# worlds build their own strategy without it. A caller that keeps the
	# canonical rows (the Playwright purge) therefore has nothing to delete
	# here — on 2026-09-11 this path removed the live site's Active strategy.
	if not include_canonical:
		return {"ok": True, "deleted": deleted, "skipped": "canonical strategy retained"}

	plans = frappe.get_all("Strategic Plan", filters={"fixture_namespace": FIXTURE_NS}, pluck="name")
	versions: list[str] = []
	for p in plans:
		versions.extend(frappe.get_all("Strategic Plan Version", filters={"plan_id": p}, pluck="name"))
	versions.extend(frappe.get_all("Strategic Plan Version", filters={"fixture_namespace": FIXTURE_NS}, pluck="name"))
	versions = list(dict.fromkeys(versions))

	indicator_ids: list[str] = []
	for doctype, filters in (
		("Strategy Node", {"plan_version_id": ["in", versions or [""]]}),
		("Performance Indicator", {"plan_version_id": ["in", versions or [""]]}),
	):
		names = frappe.get_all(doctype, filters=filters, pluck="name")
		if doctype == "Performance Indicator":
			indicator_ids = names
		for name in names:
			frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
		deleted[doctype] = len(names)

	target_names = (
		frappe.get_all("Performance Target", filters={"indicator_id": ["in", indicator_ids]}, pluck="name")
		if indicator_ids
		else []
	)
	for name in target_names:
		frappe.delete_doc("Performance Target", name, force=1, ignore_permissions=True)
	deleted["Performance Target"] = len(target_names)

	for name in versions:
		if frappe.db.exists("Strategic Plan Version", name):
			frappe.delete_doc("Strategic Plan Version", name, force=1, ignore_permissions=True)
	deleted["Strategic Plan Version"] = len(versions)

	for p in plans:
		if frappe.db.exists("Strategic Plan", p):
			frappe.delete_doc("Strategic Plan", p, force=1, ignore_permissions=True)
	deleted["Strategic Plan"] = len(plans)

	return {"ok": True, "deleted": deleted}


# --- STR-CHG-001 v1.8 §14.4 isolated workflow and usability fixtures ------
# Artboard-only (KT-STD-001 §8.7) — never part of the default seed above.
# Every profile is a Version 2 of the §14.3 plan, created, edited and
# submitted by Esther through the real commands, with the recorded event
# instants corrected to the §14.4 clock (24 Nov 2026: created 13:10, Draft
# saved 15:55, submitted 16:20 EAT). The only content change is the FY
# 2027/28 target 80% → 85%; the applicability start changes in both
# profiles and is always a comparison row of its own.

PROFILE_FUTURE = "STR18-FX-FUTURE"
PROFILE_IMMEDIATE = "STR18-FX-IMMEDIATE"
PROFILE_EFFECTIVE_FROM = {PROFILE_FUTURE: "2027-07-01", PROFILE_IMMEDIATE: "2026-11-25"}
PROFILE_EFFECTIVE_TO = "2028-06-30"
V2_CREATED_AT = "2026-11-24 13:10:00"
V2_DRAFT_SAVED_AT = "2026-11-24 15:55:00"
V2_SUBMITTED_AT = "2026-11-24 16:20:00"
V2_RETURNED_AT = "2026-11-25 11:20:00"
RETURN_REASON = (
	"Explain how the revised target will be measured and confirm the date these changes should take effect."
)
NEW_PLAN_TITLE = "Ministry of Health Strategic Plan 2028–2033 (Demo)"
NEW_PLAN_PERIOD = ("2028-07-01", "2033-06-30")


def _moh_plan_name() -> str:
	moh_plan = frappe.db.get_value("Strategic Plan", {"title": PLAN_TITLE}, "name")
	if not moh_plan:
		frappe.throw(_("Seed the default MOH plan before creating a Version 2 fixture"))
	return moh_plan


def _v2_target(v2: str) -> tuple[str, str]:
	indicator = frappe.db.get_value("Performance Indicator", {"plan_version_id": v2}, "name")
	target = frappe.db.get_value("Performance Target", {"indicator_id": indicator}, "name")
	return indicator, target


def seed_str_des_v2_draft(
	*, profile: str = PROFILE_IMMEDIATE, effective_from: str | None = None, target_by_date: bool = False
) -> dict[str, Any]:
	"""A Draft Version 2 in the named profile: successor created 13:10, the
	FY 2027/28 target raised to 85% through save_strategy_structure_draft at
	15:55, dates set by profile (or an explicit `effective_from`). With
	`target_by_date`, the target is anchored to 30 Jun 2028 instead of the
	financial year (STR18-FX-DATE-TARGET)."""
	if profile not in PROFILE_EFFECTIVE_FROM:
		frappe.throw(_("Unknown Strategy fixture profile {0}").format(profile))
	moh_plan = _moh_plan_name()
	out = _run_as(AUTHOR, create_strategy_successor_version, moh_plan)
	v2 = out["name"]
	_backdate_event(v2, "Successor Version Created", V2_CREATED_AT)

	# AGENTS.md §4.6 — narrow, documented fixture-only direct write: the
	# profile's applicability dates are set without a second "Draft saved"
	# event so the §11.9 evidence stays exactly three rows (created, saved,
	# submitted). The domain validation still runs through the structure
	# save below, which reloads and re-validates the version.
	frappe.db.set_value(
		"Strategic Plan Version",
		v2,
		{"effective_from": effective_from or PROFILE_EFFECTIVE_FROM[profile], "effective_to": PROFILE_EFFECTIVE_TO},
		update_modified=False,
	)
	indicator, target = _v2_target(v2)
	target_change = {"name": target, "comparison": "At least", "target_value": 85}
	if target_by_date:
		target_change.update({"fiscal_year": None, "target_by_date": PROFILE_EFFECTIVE_TO})
	_run_as(AUTHOR, save_strategy_structure_draft, v2, targets=[target_change])
	_backdate_event(v2, "Draft structure saved", V2_DRAFT_SAVED_AT)
	return {"ok": True, "profile": profile, "plan": moh_plan, "plan_version": v2, "indicator": indicator, "target": target}


def seed_str_des_v2_fixture(*, profile: str = PROFILE_IMMEDIATE, effective_from: str | None = None) -> dict[str, Any]:
	"""§14.4 — Version 2 Submitted for approval by Esther at 16:20 in the
	named profile (FUTURE: 1 Jul 2027 start, the negative approval example;
	IMMEDIATE: 25 Nov 2026 start, the positive one). The caller MUST tear it
	down with teardown_str_des_v2_fixture()."""
	fixture = seed_str_des_v2_draft(profile=profile, effective_from=effective_from)
	v2 = fixture["plan_version"]
	_run_as(AUTHOR, transition_plan_version, v2, "Submit for approval")
	_backdate_event(v2, "Submit for approval", V2_SUBMITTED_AT)
	return fixture


def seed_str_des_v2_returned_fixture(*, effective_from: str | None = None) -> dict[str, Any]:
	"""STR18-FX-RETURN — the immediate profile returned by Alfred at 25 Nov
	2026 11:20 EAT with the exact §11.9 reason; the same version is Draft
	again and Version 1 stays Current."""
	fixture = seed_str_des_v2_fixture(profile=PROFILE_IMMEDIATE, effective_from=effective_from)
	v2 = fixture["plan_version"]
	_run_as(APPROVER, transition_plan_version, v2, "Return", reason=RETURN_REASON)
	_backdate_event(v2, "Return", V2_RETURNED_AT)
	return {**fixture, "profile": "STR18-FX-RETURN", "return_reason": RETURN_REASON}


def teardown_str_des_v2_fixture(plan_version_id: str) -> None:
	"""Removes an isolated V2 fixture — §14.4's own requirement: profiles
	reset independently and never touch the default Version 1."""
	for indicator in frappe.get_all("Performance Indicator", filters={"plan_version_id": plan_version_id}, pluck="name"):
		for target in frappe.get_all("Performance Target", filters={"indicator_id": indicator}, pluck="name"):
			frappe.delete_doc("Performance Target", target, force=1, ignore_permissions=True)
		frappe.delete_doc("Performance Indicator", indicator, force=1, ignore_permissions=True)
	for node in frappe.get_all("Strategy Node", filters={"plan_version_id": plan_version_id}, pluck="name"):
		frappe.delete_doc("Strategy Node", node, force=1, ignore_permissions=True)
	if frappe.db.exists("Strategic Plan Version", plan_version_id):
		frappe.delete_doc("Strategic Plan Version", plan_version_id, force=1, ignore_permissions=True)
