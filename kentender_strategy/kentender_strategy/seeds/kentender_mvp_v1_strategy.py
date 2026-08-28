# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.5 §16 seed contract.

Rebuilt for the Phase 1-4 domain model. Entry points
(`upsert_kentender_mvp_v1_strategy`, `clear_kentender_mvp_v1_strategy`) keep
their existing names/signatures — kentender_core's seed orchestrator and
clear pipeline import them by these exact names.

Identifier note (tracker decision log, 2026-08-24): §16.3/§16.4 illustrate
plan/node/indicator/target identifiers in a `STR-`/`PIL-`/`PRG-`/`OBJ-`
style distinct from this rebuild's actual `{PE}-{TYPE}-####` generator
(strategy_reference.py). Forcing the seed to carry those literal strings
would require weakening `strategy_reference.REF_RE`'s correction-format
guard for every caller, not just the seed — out of proportion for a
cosmetic identifier match. Titles, dates, actors, hierarchy shape and
target values are seeded exactly as specified; identifiers are whatever
the real, already-tested reference generator deterministically produces,
following the same "spec literal is descriptive shorthand" precedent
CFG-CHG-002 set for `PE-CGK`/`PE-CGKIS`.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime

from kentender_strategy.services.strategy_authorization import ensure_strategy_governance_roles
from kentender_strategy.services.strategy_transitions import transition_plan_version

PE_MOH = "PE-MOH"
# STR-CHG-001 §16.1 names PE-CGK; the live seeded docname is PE-CGKIS
# (CFG-CHG-002 decision log, 2026-08-22 — kept verbatim here, same PE).
PE_CGK = "PE-CGKIS"
FY_2027_2028 = "FY-2027-2028"

FIXTURE_NS = "str-chg-001-mvp1"

ACTORS: dict[str, str] = {
	"author_moh": "str.author.moh@example.test",
	"approver_moh": "str.approver.moh@example.test",
	"viewer_moh": "str.viewer.moh@example.test",
	"author_kisumu": "str.author.kisumu@example.test",
	"approver_kisumu": "str.approver.kisumu@example.test",
	"viewer_kisumu": "str.viewer.kisumu@example.test",
	"auditor": "str.auditor@example.test",
}

_ACTOR_DISPLAY: dict[str, str] = {
	"author_moh": "MOH Strategy Author",
	"approver_moh": "MOH Strategy Approver",
	"viewer_moh": "MOH Strategy Viewer",
	"author_kisumu": "Kisumu Strategy Author",
	"approver_kisumu": "Kisumu Strategy Approver",
	"viewer_kisumu": "Kisumu Strategy Viewer",
	"auditor": "Strategy Auditor",
}

_ACTOR_ROLE: dict[str, str] = {
	"author_moh": "Strategy Author",
	"approver_moh": "Strategy Approver",
	"viewer_moh": "Strategy Viewer",
	"author_kisumu": "Strategy Author",
	"approver_kisumu": "Strategy Approver",
	"viewer_kisumu": "Strategy Viewer",
	"auditor": "Auditor",
}

# key -> procuring_entity_id — AUTH-ADR-001: the Role itself (already granted
# via _ACTOR_ROLE above) plus a native User Permission on this exact
# Procuring Entity is the whole authorization decision now; there is no
# Capability Profile to key a grant off any more. Viewer/Auditor have no
# lifecycle capability to grant (Phase 3 decision log — DocType-level read
# access from their Frappe Role is sufficient for a neutral viewer/auditor).
_ACTOR_SCOPE: dict[str, str] = {
	"author_moh": PE_MOH,
	"approver_moh": PE_MOH,
	"author_kisumu": PE_CGK,
	"approver_kisumu": PE_CGK,
}


def _ensure_config_prerequisites() -> None:
	"""STR-CHG-001 §16.1 — fail closed, never create/infer, never pick a
	fallback record."""
	missing = [
		ref
		for ref, exists in (
			(PE_MOH, frappe.db.exists("Procuring Entity", PE_MOH)),
			(PE_CGK, frappe.db.exists("Procuring Entity", PE_CGK)),
			(FY_2027_2028, frappe.db.exists("Financial Year", FY_2027_2028)),
		)
		if not exists
	]
	if missing:
		frappe.throw(
			_("Missing Configuration and Governance prerequisites: {0}").format(", ".join(missing)),
			frappe.ValidationError,
			title="STRATEGY_CONFIG_MISSING",
		)


def _ensure_user(email: str, first_name: str, role: str) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	if role not in {r.role for r in user.roles}:
		user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
	return email


def _ensure_pe_scope(user: str, pe: str) -> None:
	if frappe.db.exists("User Permission", {"user": user, "allow": "Procuring Entity", "for_value": pe}):
		return
	frappe.get_doc(
		{"doctype": "User Permission", "user": user, "allow": "Procuring Entity", "for_value": pe}
	).insert(ignore_permissions=True)


def ensure_strategy_governance_actors() -> dict[str, Any]:
	"""STR-CHG-001 v1.5 §16.2 — the 7 named test actors, their Frappe Role and
	(AUTH-ADR-001) their native Procuring Entity User Permission scope.
	No actor receives Strategy authority from Administrator/System Manager
	alone (§16.2's own closing line) — every grant here is an explicit Role
	plus an explicit scope, not implicit technical access."""
	_ensure_config_prerequisites()
	ensure_strategy_governance_roles()

	for key, email in ACTORS.items():
		_ensure_user(email, _ACTOR_DISPLAY[key], _ACTOR_ROLE[key])

	for key, pe in _ACTOR_SCOPE.items():
		_ensure_pe_scope(ACTORS[key], pe)

	return {"ok": True, "actors": list(ACTORS.values())}


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


def _seed_plan(
	*,
	title: str,
	pe: str,
	period_start: str,
	period_end: str,
	nodes: list[dict],
	indicators: list[dict],
	targets: list[dict],
	actors: dict[str, str],
	events: dict[str, str],
) -> dict[str, Any]:
	"""Upsert one Primary plan through the real domain/lifecycle services —
	draft, hierarchy, submit, approve (approve activates in the same
	transaction under v1.5) — matching §16.6 ("validate each plan through
	the same domain rules used by commands... seed lifecycle events use the
	named role actors, never Administrator"). Idempotent on the plan title
	within the fixture namespace; a second run returns the existing version
	untouched."""
	existing_plan = frappe.db.get_value(
		"Strategic Plan", {"title": title, "procuring_entity_id": pe}, "name"
	)
	if existing_plan:
		existing_version = frappe.db.get_value(
			"Strategic Plan Version", {"plan_id": existing_plan, "version_number": 1}, "name"
		)
		return {"ok": True, "plan": existing_plan, "plan_version": existing_version, "already_seeded": True}

	plan = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"title": title,
			"procuring_entity_id": pe,
			"plan_role": "Primary",
			"period_start": period_start,
			"period_end": period_end,
			"fixture_namespace": FIXTURE_NS,
		}
	)
	plan.insert(ignore_permissions=True)

	version = frappe.get_doc(
		{
			"doctype": "Strategic Plan Version",
			"plan_id": plan.name,
			"version_number": 1,
			"effective_from": period_start,
			"effective_to": period_end,
			"fixture_namespace": FIXTURE_NS,
		}
	)
	version.insert(ignore_permissions=True)

	id_map: dict[str, str] = {}
	for node in nodes:
		doc = frappe.get_doc(
			{
				"doctype": "Strategy Node",
				"plan_version_id": version.name,
				"node_type": node["node_type"],
				"title": node["title"],
				"display_order": node["display_order"],
				"parent_node_id": id_map.get(node.get("parent")),
				"fixture_namespace": FIXTURE_NS,
			}
		)
		doc.insert(ignore_permissions=True)
		id_map[node["key"]] = doc.name

	for ind in indicators:
		doc = frappe.get_doc(
			{
				"doctype": "Performance Indicator",
				"plan_version_id": version.name,
				"measures_node_id": id_map[ind["measures"]],
				"indicator_name": ind["name"],
				"definition": ind["definition"],
				"unit": ind["unit"],
				"fixture_namespace": FIXTURE_NS,
			}
		)
		doc.insert(ignore_permissions=True)
		id_map[ind["key"]] = doc.name

	for tgt in targets:
		data = {
			"doctype": "Performance Target",
			"indicator_id": id_map[tgt["indicator"]],
			"comparison": tgt["comparison"],
			"target_value": tgt["target_value"],
			"fixture_namespace": FIXTURE_NS,
		}
		if tgt.get("financial_year_id"):
			data["financial_year_id"] = tgt["financial_year_id"]
		if tgt.get("target_by_date"):
			data["target_by_date"] = tgt["target_by_date"]
		frappe.get_doc(data).insert(ignore_permissions=True)

	_run_as(actors["author"], transition_plan_version, version.name, "Submit for approval")
	_backdate_event(version.name, "Submit for approval", events["submitted_at"])

	_run_as(actors["approver"], transition_plan_version, version.name, "Approve")
	_backdate_event(version.name, "Approve", events["activated_at"])

	return {"ok": True, "plan": plan.name, "plan_version": version.name}


def _seed_moh_plan() -> dict[str, Any]:
	"""STR-CHG-001 §16.3."""
	return _seed_plan(
		title="Ministry of Health Strategic Plan (Demo)",
		pe=PE_MOH,
		period_start="2023-07-01",
		period_end="2028-06-30",
		nodes=[
			{"key": "pillar", "node_type": "Pillar", "title": "Digital health systems", "display_order": 1},
			{
				"key": "programme",
				"node_type": "Programme",
				"title": "Health policy, standards and regulation",
				"display_order": 2,
				"parent": "pillar",
			},
			{
				"key": "sub_programme",
				"node_type": "Sub-programme",
				"title": "Digital health governance",
				"display_order": 3,
				"parent": "programme",
			},
			{
				"key": "objective",
				"node_type": "Strategic Objective",
				"title": "Strengthen interoperable national digital health services",
				"display_order": 4,
				"parent": "sub_programme",
			},
		],
		indicators=[
			{
				"key": "indicator",
				"measures": "objective",
				"name": "Percentage of priority facilities using interoperable digital health services",
				"definition": (
					"Priority facilities operating an approved interoperable digital health service "
					"divided by all priority facilities, expressed as a percentage."
				),
				"unit": "Percentage",
			}
		],
		targets=[
			{
				"indicator": "indicator",
				"financial_year_id": FY_2027_2028,
				"comparison": "At least",
				"target_value": 80,
			}
		],
		actors={
			"author": ACTORS["author_moh"],
			"approver": ACTORS["approver_moh"],
		},
		events={
			"submitted_at": "2023-06-28 09:10:00",
			"activated_at": "2023-07-01 00:00:00",
		},
	)


def _seed_kisumu_plan() -> dict[str, Any]:
	"""STR-CHG-001 §16.4 — cross-PE isolation fixture."""
	return _seed_plan(
		title="Kisumu County Development Strategy (Demo)",
		pe=PE_CGK,
		period_start="2023-01-01",
		period_end="2027-12-31",
		nodes=[
			{"key": "pillar", "node_type": "Pillar", "title": "Digital county services", "display_order": 1},
			{
				"key": "programme",
				"node_type": "Programme",
				"title": "County administration and digital services",
				"display_order": 2,
				"parent": "pillar",
			},
			{
				"key": "objective",
				"node_type": "Strategic Objective",
				"title": "Improve reliable access to priority county digital services",
				"display_order": 3,
				"parent": "programme",
			},
		],
		indicators=[
			{
				"key": "indicator",
				"measures": "objective",
				"name": "Percentage of priority county services available through approved digital channels",
				"definition": (
					"Priority county services available through an approved digital channel divided by "
					"all priority county services, expressed as a percentage."
				),
				"unit": "Percentage",
			}
		],
		targets=[
			{
				"indicator": "indicator",
				"target_by_date": "2027-12-31",
				"comparison": "At least",
				"target_value": 70,
			}
		],
		actors={
			"author": ACTORS["author_kisumu"],
			"approver": ACTORS["approver_kisumu"],
		},
		events={
			"submitted_at": "2022-12-28 09:00:00",
			"activated_at": "2023-01-01 00:00:00",
		},
	)


def upsert_kentender_mvp_v1_strategy(*, reset: bool = False) -> dict[str, Any]:
	if reset:
		clear_kentender_mvp_v1_strategy()
	_ensure_config_prerequisites()
	actors = ensure_strategy_governance_actors()
	moh = _seed_moh_plan()
	kisumu = _seed_kisumu_plan()
	return {"ok": True, "actors": actors, "moh": moh, "kisumu": kisumu}


def clear_kentender_mvp_v1_strategy(
	*, include_canonical: bool = True, include_playwright: bool = True
) -> dict[str, Any]:
	"""Delete fixture-tagged Strategy records only — no broad PE wipe, and
	no deletion of the 9 seeded actor users (stable identities, same as
	CFG-CHG-002's own governance-actor seed convention)."""
	deleted: dict[str, int] = {}
	if not (include_canonical or include_playwright):
		return {"ok": True, "deleted": deleted}

	plans = frappe.get_all("Strategic Plan", filters={"fixture_namespace": FIXTURE_NS}, pluck="name")
	versions: list[str] = []
	for p in plans:
		versions.extend(
			frappe.get_all("Strategic Plan Version", filters={"plan_id": p}, pluck="name")
		)
	versions.extend(
		frappe.get_all("Strategic Plan Version", filters={"fixture_namespace": FIXTURE_NS}, pluck="name")
	)
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


# --- STR-CHG-001 §16.5 isolated design/workflow fixture -------------------------


def seed_str_des_v2_fixture() -> dict[str, Any]:
	"""STR-CHG-001 v1.5 §16.5 — an isolated Version 2 test fixture for the
	STR-DES-04..11 artboards, NOT part of the default upsert above. Reaches
	Submitted for approval (the last event §16.5 names under the v1.5
	4-status model); the caller may transition it further and MUST tear it
	down with teardown_str_des_v2_fixture().

	Reuses create_strategy_successor_version (the same real command §10.1
	exposes) to clone the full hierarchy rather than hand-cloning only the
	indicator/target — a hand-clone left the indicator pointing at the V1
	outcome node, which validate_performance_indicator correctly rejects
	as a cross-version reference (found live while first building this
	fixture, fixed by reuse instead of a second, narrower clone path)."""
	from kentender_strategy.services.strategy_writes import create_strategy_successor_version

	moh_plan = frappe.db.get_value(
		"Strategic Plan", {"title": "Ministry of Health Strategic Plan (Demo)", "procuring_entity_id": PE_MOH}, "name"
	)
	if not moh_plan:
		frappe.throw(_("Seed the default MOH plan before creating the V2 fixture"))

	out = _run_as(ACTORS["author_moh"], create_strategy_successor_version, moh_plan)
	v2 = out["name"]
	frappe.db.set_value(
		"Strategic Plan Version", v2, {"effective_from": "2027-07-01", "effective_to": "2028-06-30"}
	)
	_backdate_event(v2, "Successor Version Created", "2027-03-15 13:10:00")

	new_indicator = frappe.db.get_value("Performance Indicator", {"plan_version_id": v2}, "name")
	new_target = frappe.db.get_value("Performance Target", {"indicator_id": new_indicator}, "name")
	frappe.db.set_value("Performance Target", new_target, "target_value", 85)  # §16.5's only content change

	_run_as(ACTORS["author_moh"], transition_plan_version, v2, "Submit for approval")
	_backdate_event(v2, "Submit for approval", "2027-03-15 16:20:00")

	return {"ok": True, "plan_version": v2, "indicator": new_indicator, "target": new_target}


def teardown_str_des_v2_fixture(plan_version_id: str) -> None:
	"""Removes an isolated V2 fixture created by seed_str_des_v2_fixture —
	§16.5's own requirement: "must remove or roll it back after the test"."""
	for indicator in frappe.get_all(
		"Performance Indicator", filters={"plan_version_id": plan_version_id}, pluck="name"
	):
		for target in frappe.get_all("Performance Target", filters={"indicator_id": indicator}, pluck="name"):
			frappe.delete_doc("Performance Target", target, force=1, ignore_permissions=True)
		frappe.delete_doc("Performance Indicator", indicator, force=1, ignore_permissions=True)
	if frappe.db.exists("Strategic Plan Version", plan_version_id):
		frappe.delete_doc("Strategic Plan Version", plan_version_id, force=1, ignore_permissions=True)
