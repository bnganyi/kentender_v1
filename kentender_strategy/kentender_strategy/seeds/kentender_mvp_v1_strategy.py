# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.8 §14.3 seed contract (v1.7 §14 until 26 Sep 2026) — the
single Ministry of Health plan.

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
already-tested reference generator produces (`make seed-canonical` resets
its counter on every rebuild, so a rebuilt world starts at 0001 again).

Version 1's commands run at the §14.3 instants under the frozen seed clock
(`kentender_core.seeds.clock`, KT-STD-001 v1.8 §8.6): nothing is
back-stamped afterwards. Until 26 Sep 2026 the draft events carried the
seeding day and only submission and approval were back-stamped to 1 Jul
2023, so the history showed the draft created after its own approval.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime

from kentender_core.seeds import clock
from kentender_core.services.command_write_guard import maintenance_write
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

# §14.3 gives the submission and approval instants; it gives none for the
# draft, so the draft and its structure are saved half an hour before the
# submission (fixture choice, 26 Sep 2026).
V1_DRAFT_AT = "2023-07-01 08:00:00"
V1_SUBMITTED_AT = "2023-07-01 08:30:00"
V1_APPROVED_AT = "2023-07-01 09:15:00"

PERIOD = ("2023-07-01", "2028-06-30")
#: (client id, node type, title), each the parent of the next.
NODES = (
	("$pillar", "Pillar", "Digital health systems"),
	("$programme", "Programme", "Health policy, standards and regulation"),
	("$sub_programme", "Sub-programme", "Digital health governance"),
	("$objective", "Strategic Objective", "Strengthen interoperable national digital health services"),
)
INDICATOR_NAME = "Percentage of priority facilities using interoperable digital health services"
INDICATOR_DEFINITION = (
	"Priority facilities operating an approved interoperable digital health service "
	"divided by all priority facilities, expressed as a percentage."
)


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
	same transaction), each at its §14.3 instant. Idempotent on the plan
	title; a second run returns the existing version untouched. A plan with
	that title outside the canonical namespace is conflicting data and fails
	the run (KT-STD-001 v1.8 §8.6: seeds never adopt or repair) — `reset`
	removes such a plan before the seed runs."""
	existing_plan = frappe.db.get_value("Strategic Plan", {"title": PLAN_TITLE}, "name")
	if existing_plan:
		if frappe.db.get_value("Strategic Plan", existing_plan, "fixture_namespace") != FIXTURE_NS:
			frappe.throw(
				_("A Strategic Plan titled {0} exists outside the canonical seed ({1}); run make seed-canonical to remove it.").format(PLAN_TITLE, existing_plan),
				title="STRATEGY_SEED_CONFLICT",
			)
		existing_version = frappe.db.get_value(
			"Strategic Plan Version", {"plan_id": existing_plan, "version_number": 1}, "name"
		)
		return {"ok": True, "plan": existing_plan, "plan_version": existing_version, "already_seeded": True}

	with clock.at(V1_DRAFT_AT):
		draft = _run_as(
			AUTHOR,
			save_strategy_plan_draft,
			{
				"title": PLAN_TITLE,
				"plan_role": "Primary",
				"period_start": PERIOD[0],
				"period_end": PERIOD[1],
				"effective_from": PERIOD[0],
				"effective_to": PERIOD[1],
			},
		)
		plan_id = draft["plan"]["plan_id"]
		version_id = draft["version"]["name"]

		_run_as(
			AUTHOR,
			save_strategy_structure_draft,
			version_id,
			nodes=[
				{
					"client_id": client_id,
					"node_type": node_type,
					"title": title,
					"display_order": index + 1,
					**({"parent_node_id": NODES[index - 1][0]} if index else {}),
				}
				for index, (client_id, node_type, title) in enumerate(NODES)
			],
			indicators=[
				{
					"client_id": "$indicator",
					"measures_node_id": NODES[-1][0],
					"indicator_name": INDICATOR_NAME,
					"definition": INDICATOR_DEFINITION,
					"unit": "Percentage",
				}
			],
			targets=[
				{
					"indicator_id": "$indicator",
					"fiscal_year": FY_2027_2028,
					"comparison": "At least",
					"target_value": 80,
				}
			],
		)

	with clock.at(V1_SUBMITTED_AT):
		_run_as(AUTHOR, transition_plan_version, version_id, "Submit for approval")

	with clock.at(V1_APPROVED_AT):
		_run_as(APPROVER, transition_plan_version, version_id, "Approve")

	frappe.db.set_value("Strategic Plan", plan_id, "fixture_namespace", FIXTURE_NS, update_modified=False)
	frappe.db.set_value("Strategic Plan Version", version_id, "fixture_namespace", FIXTURE_NS, update_modified=False)
	# The Strategy command accepts only a target's own content fields (AUD-STR-008),
	# so the namespace is stamped here, like the plan's and the version's.
	for indicator in frappe.get_all("Performance Indicator", filters={"plan_version_id": version_id}, pluck="name"):
		for target in frappe.get_all("Performance Target", filters={"indicator_id": indicator}, pluck="name"):
			frappe.db.set_value("Performance Target", target, "fixture_namespace", FIXTURE_NS, update_modified=False)

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
	versions = frappe.get_all("Strategic Plan Version", filters={"fixture_namespace": FIXTURE_NS}, pluck="name")
	return {"ok": True, "deleted": _delete_plans(plans, versions)}


def _delete_plans(plans: list[str], versions: list[str]) -> dict[str, int]:
	"""These plans with every version, and these further versions, each
	with its nodes, indicators and targets."""
	versions = list(dict.fromkeys(versions + frappe.get_all("Strategic Plan Version", filters={"plan_id": ["in", plans or [""]]}, pluck="name")))
	indicators = frappe.get_all("Performance Indicator", filters={"plan_version_id": ["in", versions or [""]]}, pluck="name")
	deleted: dict[str, int] = {}
	for doctype, names in (
		("Performance Target", frappe.get_all("Performance Target", filters={"indicator_id": ["in", indicators or [""]]}, pluck="name")),
		("Performance Indicator", indicators),
		("Strategy Node", frappe.get_all("Strategy Node", filters={"plan_version_id": ["in", versions or [""]]}, pluck="name")),
		("Strategic Plan Version", versions),
		("Strategic Plan", plans),
	):
		for name in names:
			if frappe.db.exists(doctype, name):
				with maintenance_write("Strategy", reason="canonical seed reset"):
					frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
		if names:
			deleted[doctype] = len(names)
	return deleted


def strategy_rows_to_clear() -> dict[str, list[str]]:
	"""What `reset` removes (STR-CHG-001 v1.8 §14.3 "There is no second
	seeded plan"; §14.4 Version 2 profiles are isolated): every plan outside
	the canonical namespace, and every version of the canonical plan other
	than Version 1. Read-only."""
	out: dict[str, list[str]] = {}
	plans = [row.name for row in frappe.get_all("Strategic Plan", fields=["name", "fixture_namespace"]) if row.fixture_namespace != FIXTURE_NS]
	if plans:
		out["Strategic Plan"] = plans
	canonical = frappe.get_all("Strategic Plan", filters={"fixture_namespace": FIXTURE_NS}, pluck="name")
	extra = frappe.get_all("Strategic Plan Version", filters={"plan_id": ["in", canonical or [""]], "version_number": ["!=", 1]}, pluck="name")
	if extra:
		out["Strategic Plan Version"] = extra
	return out


def clear_non_canonical_strategy() -> dict[str, Any]:
	rows = strategy_rows_to_clear()
	return {"ok": True, "deleted": _delete_plans(rows.get("Strategic Plan", []), rows.get("Strategic Plan Version", []))}


def validate_strategy_seed() -> list[dict[str, Any]]:
	"""One row per STR-CHG-001 v1.8 §14.3 fact. Never mutates."""
	rows: list[dict[str, Any]] = []

	def check(ok: bool, label: str) -> None:
		rows.append({"ok": bool(ok), "check": label, "detail": "" if ok else "failed"})

	plans = frappe.get_all("Strategic Plan", fields=["name", "title", "plan_role", "period_start", "period_end", "fixture_namespace"])
	check(len(plans) == 1, f"exactly one Strategic Plan exists (got {len(plans)})")
	plan = next((row for row in plans if row.fixture_namespace == FIXTURE_NS), None)
	check(bool(plan), f"the plan carries the {FIXTURE_NS} stamp")
	if not plan:
		return rows
	check(plan.title == PLAN_TITLE, f"the plan title is {PLAN_TITLE!r} (got {plan.title!r})")
	check(plan.plan_role == "Primary", "the plan is the Primary plan")
	check((str(plan.period_start), str(plan.period_end)) == PERIOD, f"the plan period is {PERIOD[0]} to {PERIOD[1]}")
	versions = frappe.get_all("Strategic Plan Version", filters={"plan_id": plan.name}, fields=["name", "version_number", "status", "effective_from", "effective_to"])
	check([(v.version_number, v.status) for v in versions] == [(1, "Active")], f"Version 1 is the only version and is Active (got {[(v.version_number, v.status) for v in versions]})")
	if not versions:
		return rows
	version = versions[0]
	check((str(version.effective_from), str(version.effective_to)) == PERIOD, "Version 1 applies for the plan period")
	nodes = {row.name: row for row in frappe.get_all("Strategy Node", filters={"plan_version_id": version.name}, fields=["name", "node_type", "title", "parent_node_id"])}
	chain, parent = [], None
	for _step in range(len(nodes)):
		child = next((row for row in nodes.values() if (row.parent_node_id or None) == parent), None)
		if not child:
			break
		chain.append((child.node_type, child.title))
		parent = child.name
	check(len(nodes) == len(NODES) and chain == [(t, title) for _c, t, title in NODES], f"the hierarchy is Pillar → Programme → Sub-programme → Objective with the §14.3 titles (got {chain})")
	indicators = frappe.get_all("Performance Indicator", filters={"plan_version_id": version.name}, fields=["name", "indicator_name", "definition", "unit", "measures_node_id"])
	objective = parent
	check(
		len(indicators) == 1 and (indicators[0].indicator_name, indicators[0].definition, indicators[0].unit, indicators[0].measures_node_id) == (INDICATOR_NAME, INDICATOR_DEFINITION, "Percentage", objective),
		"one indicator, exactly as §14.3 states, measuring the objective",
	)
	targets = frappe.get_all("Performance Target", filters={"indicator_id": ["in", [i.name for i in indicators] or [""]]}, fields=["fiscal_year", "comparison", "target_value"])
	check([(t.fiscal_year, t.comparison, float(t.target_value or 0)) for t in targets] == [(FY_2027_2028, "At least", 80.0)], f"one target: at least 80% in FY {FY_2027_2028}")
	events = {
		row.action: row
		for row in frappe.get_all("Audit Event", filters={"document_type": "Strategic Plan Version", "document_name": version.name}, fields=["action", "timestamp", "performed_by"])
	}
	for action, actor, at in (("Submit for approval", AUTHOR, V1_SUBMITTED_AT), ("Approve", APPROVER, V1_APPROVED_AT)):
		event = events.get(action)
		check(bool(event) and event.performed_by == actor and str(event.timestamp)[:16] == at[:16], f"{action} by {actor} at {at[:16]} EAT")
	return rows


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
	with maintenance_write("Strategy", reason="teardown of an isolated V2 fixture"):
		for indicator in frappe.get_all("Performance Indicator", filters={"plan_version_id": plan_version_id}, pluck="name"):
			for target in frappe.get_all("Performance Target", filters={"indicator_id": indicator}, pluck="name"):
				frappe.delete_doc("Performance Target", target, force=1, ignore_permissions=True)
			frappe.delete_doc("Performance Indicator", indicator, force=1, ignore_permissions=True)
		for node in frappe.get_all("Strategy Node", filters={"plan_version_id": plan_version_id}, pluck="name"):
			frappe.delete_doc("Strategy Node", node, force=1, ignore_permissions=True)
		if frappe.db.exists("Strategic Plan Version", plan_version_id):
			frappe.delete_doc("Strategic Plan Version", plan_version_id, force=1, ignore_permissions=True)
