# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.3 Phase 7 — read contracts backing STR-UI-01..04.

Rebuilds the read-model surface that `strategy_contracts.py`'s
`get_strategy_portfolio` / `get_plan_overview` / `get_strategy_tree` never
recovered from before Phase 1 (they still reference the deleted Strategy
Programme/Sub-programme/Strategic Objective/Strategic Outcome doctypes and
`Strategic Plan.plan_code`/`.status` fields that moved to
`Strategic Plan Version` in Phase 1). This module targets the CURRENT
schema only: `Strategic Plan` (identity) / `Strategic Plan Version`
(version + status) / `Strategy Node` (unified hierarchy) /
`Performance Indicator` / `Performance Target`.

Kept in a new module rather than edited in place inside
`strategy_contracts.py`, following the Phase 4 precedent of separating a
freshly-correct contract surface from a legacy one still holding
not-yet-rebuilt functions (`list_strategy_value_commitments`,
`get_strategy_usage`, `list_active_targets` — out of this phase's named
scope, left as tracked, pre-existing gaps, not touched here).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_core.services.authorization_policy import resolve_effective_access
from kentender_strategy.services.strategy_audit import list_events
from kentender_strategy.services.strategy_authorization import (
	CAP_APPROVE,
	CAP_AUTHOR,
	CAP_REVIEW,
	has_plan_version_capability,
)
from kentender_strategy.services.strategy_readiness import get_version_readiness
from kentender_strategy.services.strategy_transitions import available_actions

UNRESTRICTED_READ_ROLES = ("System Manager", "Strategy Viewer", "Auditor")
_LIFECYCLE_CAPS = (CAP_AUTHOR, CAP_REVIEW, CAP_APPROVE)


def _ref(id_: str | None, name: str | None = None) -> dict | None:
	if not id_:
		return None
	return {"id": id_, "name": name or id_}


def _pe_label(pe_id: str | None) -> str | None:
	if not pe_id:
		return None
	row = frappe.db.get_value("Procuring Entity", pe_id, ["entity_name", "entity_code"], as_dict=True)
	if not row:
		return pe_id
	code = row.entity_code or pe_id
	name = row.entity_name or code
	return f"{code} — {name}" if name != code else code


def _allowed_pes() -> tuple[set[str], bool]:
	"""(pes, unrestricted). `unrestricted=True` means no PE filter applies —
	System Manager / Strategy Viewer / Auditor, per STR-302/STR-303's own
	documented deferral of PE-scoped read capabilities for those roles.
	Author/Reviewer/Approval Authority are scoped to whichever PE(s) their
	real Operational Scope Assignments grant."""
	roles = frappe.get_roles()
	if any(r in roles for r in UNRESTRICTED_READ_ROLES):
		return set(), True
	user = frappe.session.user
	pes: set[str] = set()
	for cap in _LIFECYCLE_CAPS:
		for grant in resolve_effective_access(user, cap):
			pe = grant.get("procuring_entity_id")
			if pe:
				pes.add(pe)
	return pes, False


def _user_can_view_plan(procuring_entity_id: str | None) -> bool:
	pes, unrestricted = _allowed_pes()
	if unrestricted:
		return True
	return bool(procuring_entity_id and procuring_entity_id in pes)


def _plan_dto(plan) -> dict:
	return {
		"id": plan.name,
		"reference": plan.plan_id,
		"title": plan.title,
		"plan_role": plan.plan_role,
		"procuring_entity": _ref(plan.procuring_entity_id, _pe_label(plan.procuring_entity_id)),
		"organisation_unit_id": plan.owner_org_unit_id,
		"period_start": str(plan.period_start) if plan.period_start else None,
		"period_end": str(plan.period_end) if plan.period_end else None,
		"period_label": _period_label(plan.period_start, plan.period_end),
	}


def _period_label(start, end) -> str | None:
	if not start or not end:
		return None
	sd, ed = frappe.utils.getdate(start), frappe.utils.getdate(end)
	return f"{sd.strftime('%d %b %Y')} – {ed.strftime('%d %b %Y')}"


def _version_dto(version) -> dict:
	return {
		"id": version.name,
		"reference": version.plan_version_id,
		"version_number": version.version_number,
		"status": version.status,
		"effective_from": str(version.effective_from) if version.effective_from else None,
		"effective_to": str(version.effective_to) if version.effective_to else None,
		"effective_period_label": _period_label(version.effective_from, version.effective_to),
		"based_on_plan_version_id": version.based_on_plan_version_id,
	}


# --------------------------------------------------------------------------
# STR-UI-01 Strategy Portfolio
# --------------------------------------------------------------------------


# STR-CHG-001 v1.3 §13.1: the Portfolio row link must follow the server-
# returned action, not a client-side status map (AGENTS.md §6.2). Maps each
# transitionable status (strategy_transitions.TRANSITIONS) to the label the
# spec assigns it; a status with no matching entry (Active/Superseded/
# Archived, or "No version") falls back to plain "View".
_STATUS_ACTION_LABELS: dict[str, str] = {
	"Draft": "Continue draft",
	"Returned": "Continue draft",
	"In Review": "Review",
	"Awaiting Approval": "Approve",
	"Approved": "Activate",
}
_REVIEW_TASK_STATUSES = ("In Review", "Awaiting Approval")


def _row_action(plan_name: str, version_row: dict | None) -> dict:
	"""(label, route, target_id) for a Portfolio row's action link."""
	if not version_row:
		return {"label": _("View"), "route": "strategy-plan-workspace", "target_id": plan_name}
	status = version_row["status"]
	route = "strategy-review-task" if status in _REVIEW_TASK_STATUSES else "strategy-plan-workspace"
	target_id = version_row["name"] if route == "strategy-review-task" else plan_name
	if not available_actions(version_row["name"]):
		return {"label": _("View"), "route": route, "target_id": target_id}
	return {"label": _(_STATUS_ACTION_LABELS.get(status, "View")), "route": route, "target_id": target_id}


def _latest_version_row(plan_name: str) -> dict | None:
	rows = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": plan_name},
		fields=["name", "plan_version_id", "version_number", "status"],
		order_by="version_number desc",
		limit=1,
	)
	return rows[0] if rows else None


def get_strategy_portfolio(procuring_entity: str | None = None) -> dict:
	"""STR-UI-01 payload: plan table rows + My work + PE banner.

	Returns `{"forbidden": True}` rather than raising when the caller holds
	none of the read-eligible roles/capabilities — lets the Vue page render
	its own Forbidden state (STR-DES-12) instead of a raw exception."""
	pes, unrestricted = _allowed_pes()
	if not unrestricted and not pes:
		return {"forbidden": True}

	filters: dict[str, Any] = {}
	if procuring_entity:
		if not unrestricted and procuring_entity not in pes:
			return {"forbidden": True}
		filters["procuring_entity_id"] = procuring_entity
	elif not unrestricted:
		filters["procuring_entity_id"] = ["in", sorted(pes)]

	plans = frappe.get_all(
		"Strategic Plan",
		filters=filters,
		fields=[
			"name",
			"plan_id",
			"title",
			"plan_role",
			"procuring_entity_id",
			"owner_org_unit_id",
			"period_start",
			"period_end",
		],
		order_by="modified desc",
		limit=200,
	)
	rows = []
	for p in plans:
		latest = _latest_version_row(p.name)
		action = _row_action(p.name, latest)
		rows.append(
			{
				**_plan_dto(p),
				"current_version": (
					{
						"id": latest["name"],
						"reference": latest["plan_version_id"],
						"version_number": latest["version_number"],
						"status": latest["status"],
					}
					if latest
					else None
				),
				"status": latest["status"] if latest else "No version",
				"available_action": action["label"],
				"action_route": action["route"],
				"action_target_id": action["target_id"],
			}
		)

	shown_pe = None
	if procuring_entity:
		shown_pe = _ref(procuring_entity, _pe_label(procuring_entity))
	elif len(pes) == 1:
		only_pe = next(iter(pes))
		shown_pe = _ref(only_pe, _pe_label(only_pe))

	return {
		"forbidden": False,
		"procuring_entity": shown_pe,
		"plans": rows,
		"my_work": _my_work_versions(pes, unrestricted),
		"counts": {"plans": len(rows)},
	}


def _my_work_versions(pes: set[str], unrestricted: bool) -> list[dict]:
	versions = frappe.get_all(
		"Strategic Plan Version",
		filters={"status": ["in", ("In Review", "Awaiting Approval", "Returned")]},
		fields=["name", "plan_version_id", "plan_id", "version_number", "status"],
	)
	out = []
	for v in versions:
		plan = frappe.db.get_value(
			"Strategic Plan", v.plan_id, ["plan_id", "title", "procuring_entity_id"], as_dict=True
		)
		if not plan:
			continue
		if not unrestricted and plan.procuring_entity_id not in pes:
			continue
		actions = available_actions(v.name)
		if not actions:
			continue
		out.append(
			{
				"plan_id": v.plan_id,
				"plan_reference": plan.plan_id,
				"plan_title": plan.title,
				"version_id": v.name,
				"version_number": v.version_number,
				"status": v.status,
				"allowed_actions": actions,
			}
		)
	return out


# --------------------------------------------------------------------------
# Structure tree (shared by STR-UI-02 read view / STR-UI-03 editor / STR-UI-04)
# --------------------------------------------------------------------------


def get_strategy_tree(plan_version_id: str) -> dict:
	nodes = frappe.get_all(
		"Strategy Node",
		filters={"plan_version_id": plan_version_id},
		fields=["name", "strategy_node_id", "node_type", "parent_node_id", "title", "display_order"],
		order_by="display_order asc",
	)
	indicators = frappe.get_all(
		"Performance Indicator",
		filters={"plan_version_id": plan_version_id},
		fields=["name", "indicator_id", "measures_node_id", "indicator_name", "definition", "unit"],
	)
	indicator_names = [i.name for i in indicators]
	targets = (
		frappe.get_all(
			"Performance Target",
			filters={"indicator_id": ["in", indicator_names]},
			fields=[
				"name",
				"target_id",
				"indicator_id",
				"financial_year_id",
				"target_by_date",
				"comparison",
				"target_value",
			],
		)
		if indicator_names
		else []
	)

	targets_by_indicator: dict[str, list] = {}
	for t in targets:
		targets_by_indicator.setdefault(t.indicator_id, []).append(t)

	def target_node(t) -> dict:
		period = t.financial_year_id or (str(t.target_by_date) if t.target_by_date else None)
		return {
			"id": t.name,
			"reference": t.target_id,
			"node_type": "Performance Target",
			"title": f"{t.comparison} {t.target_value}",
			"financial_year_id": t.financial_year_id,
			"target_by_date": str(t.target_by_date) if t.target_by_date else None,
			"period_label": period,
			"comparison": t.comparison,
			"target_value": t.target_value,
			"children": [],
		}

	indicators_by_node: dict[str, list] = {}
	for i in indicators:
		indicators_by_node.setdefault(i.measures_node_id, []).append(i)

	def indicator_node(i) -> dict:
		return {
			"id": i.name,
			"reference": i.indicator_id,
			"node_type": "Performance Indicator",
			"title": i.indicator_name,
			"definition": i.definition,
			"unit": i.unit,
			"children": [target_node(t) for t in targets_by_indicator.get(i.name, [])],
		}

	children_by_parent: dict[str | None, list] = {}
	for n in nodes:
		children_by_parent.setdefault(n.parent_node_id or None, []).append(n)

	def structure_node(n) -> dict:
		child_nodes = [structure_node(c) for c in children_by_parent.get(n.name, [])]
		child_indicators = [indicator_node(i) for i in indicators_by_node.get(n.name, [])]
		return {
			"id": n.name,
			"reference": n.strategy_node_id,
			"node_type": n.node_type,
			"title": n.title,
			"display_order": n.display_order,
			"children": child_nodes + child_indicators,
		}

	roots = [structure_node(n) for n in children_by_parent.get(None, [])]

	counts = {
		"pillars": sum(1 for n in nodes if n.node_type == "Pillar"),
		"programmes": sum(1 for n in nodes if n.node_type == "Programme"),
		"sub_programmes": sum(1 for n in nodes if n.node_type == "Sub-programme"),
		"strategic_objectives": sum(1 for n in nodes if n.node_type == "Strategic Objective"),
		"strategic_outcomes": sum(1 for n in nodes if n.node_type == "Strategic Outcome"),
		"performance_indicators": len(indicators),
		"performance_targets": len(targets),
	}
	return {"tree": roots, "counts": counts}


# --------------------------------------------------------------------------
# STR-UI-02 Plan workspace
# --------------------------------------------------------------------------


def _authority_from_events(version_name: str, actions: tuple[str, ...]) -> dict[str, dict | None]:
	rows = list_events("Strategic Plan Version", version_name)
	out: dict[str, dict | None] = {a: None for a in actions}
	for row in rows:  # newest first; keep the most recent occurrence of each action
		action = row.get("action")
		if action in out and out[action] is None:
			out[action] = {"actor": row.get("performed_by"), "at": str(row.get("timestamp"))}
	return out


def get_plan_workspace(plan_id: str) -> dict:
	if not frappe.db.exists("Strategic Plan", plan_id):
		return {"not_found": True}
	plan = frappe.get_doc("Strategic Plan", plan_id)
	if not _user_can_view_plan(plan.procuring_entity_id):
		return {"forbidden": True}

	versions = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": plan.name},
		fields=[
			"name",
			"plan_version_id",
			"version_number",
			"status",
			"effective_from",
			"effective_to",
			"based_on_plan_version_id",
		],
		order_by="version_number desc",
	)
	if not versions:
		return {"forbidden": False, "not_found": False, "plan": _plan_dto(plan), "no_version": True}

	by_status = {v.status: v for v in versions}
	active = by_status.get("Active")
	pending = by_status.get("Approved")
	# An open (Draft/In Review/Returned/Awaiting Approval) successor always
	# takes priority over the steady-state Active version — before Create
	# successor version existed in this UI, a plan could only ever have one
	# non-Active version at a time, so `pending or active or versions[0]`
	# never had to consider Draft/In Review/Returned; now that a Draft can
	# coexist with an Active version, that fallback chain would silently
	# keep showing the old Active version's Overview/Structure/History
	# forever instead of the newly created Draft (found live 2026-08-24
	# while verifying the successor-version fix in a browser).
	open_statuses = ("Draft", "In Review", "Returned", "Awaiting Approval", "Approved")
	open_version = next((v for v in versions if v.status in open_statuses), None)
	current = open_version or active or versions[0]

	tree = get_strategy_tree(current.name)
	events = _authority_from_events(current.name, ("Approve", "Activate", "Submit for review", "Recommend for approval"))

	current_authority = None
	version_authority = None
	readiness = None
	if pending:
		version_authority = {
			"approved_by": events["Approve"],
			"current_active_version": _version_dto(frappe.get_doc("Strategic Plan Version", active.name))
			if active
			else None,
		}
		readiness = get_version_readiness(pending.name)
	elif active:
		current_authority = {"approved_by": events["Approve"], "activated": events["Activate"]}

	can_activate = bool(pending) and has_plan_version_capability(frappe.session.user, CAP_APPROVE, pending.name)
	is_editable_draft = current.status in ("Draft", "Returned")

	open_successor_exists = any(
		v.status in ("Draft", "In Review", "Returned", "Awaiting Approval") for v in versions
	)
	can_create_successor = (
		bool(active or pending)
		and not open_successor_exists
		and has_plan_version_capability(frappe.session.user, CAP_AUTHOR, current.name)
	)

	return {
		"forbidden": False,
		"not_found": False,
		"no_version": False,
		"plan": _plan_dto(plan),
		"current_version": _version_dto(frappe.get_doc("Strategic Plan Version", current.name)),
		"active_version": _version_dto(frappe.get_doc("Strategic Plan Version", active.name)) if active else None,
		"pending_version": _version_dto(frappe.get_doc("Strategic Plan Version", pending.name)) if pending else None,
		"structure_summary": tree["counts"],
		"current_authority": current_authority,
		"version_authority": version_authority,
		"readiness": readiness,
		"is_editable_draft": is_editable_draft,
		"capabilities": {"activate": can_activate, "create_successor": can_create_successor},
	}


def get_plan_history(plan_id: str) -> list[dict]:
	if not frappe.db.exists("Strategic Plan", plan_id):
		return []
	plan = frappe.get_doc("Strategic Plan", plan_id)
	if not _user_can_view_plan(plan.procuring_entity_id):
		return []
	version_names = frappe.get_all(
		"Strategic Plan Version", filters={"plan_id": plan.name}, pluck="name"
	)
	out: list[dict] = []
	for v in version_names:
		for row in list_events("Strategic Plan Version", v):
			out.append(
				{
					"at": str(row.get("timestamp")),
					"event": row.get("action"),
					"actor": row.get("performed_by"),
					"version_id": v,
				}
			)
	out.sort(key=lambda r: r["at"], reverse=True)
	return out


def get_version_history(plan_version_id: str) -> list[dict]:
	"""STR-CHG-001 v1.3 spec: "History returns only lifecycle and draft-save
	events for the submitted version" — unlike get_plan_history (plan-wide,
	used by the Portfolio's implicit "all activity" reads), the Review task
	and the Plan workspace's own-version History tab must show only this
	one version's events, not every version of the plan merged together."""
	if not frappe.db.exists("Strategic Plan Version", plan_version_id):
		return []
	version = frappe.get_doc("Strategic Plan Version", plan_version_id)
	plan = frappe.get_doc("Strategic Plan", version.plan_id)
	if not _user_can_view_plan(plan.procuring_entity_id):
		return []
	out = [
		{
			"at": str(row.get("timestamp")),
			"event": row.get("action"),
			"actor": row.get("performed_by"),
			"version_id": plan_version_id,
		}
		for row in list_events("Strategic Plan Version", plan_version_id)
	]
	out.sort(key=lambda r: r["at"], reverse=True)
	return out


# --------------------------------------------------------------------------
# STR-UI-04 Review task
# --------------------------------------------------------------------------


def get_version_review_overview(plan_version_id: str) -> dict:
	if not frappe.db.exists("Strategic Plan Version", plan_version_id):
		return {"not_found": True}
	version = frappe.get_doc("Strategic Plan Version", plan_version_id)
	plan = frappe.get_doc("Strategic Plan", version.plan_id)
	if not _user_can_view_plan(plan.procuring_entity_id):
		return {"forbidden": True}

	user = frappe.session.user
	is_reviewer = has_plan_version_capability(user, CAP_REVIEW, version)
	is_approver = has_plan_version_capability(user, CAP_APPROVE, version)
	role = "approver" if is_approver else ("reviewer" if is_reviewer else None)

	tree = get_strategy_tree(version.name)
	events = _authority_from_events(
		version.name, ("Submit for review", "Recommend for approval", "Return")
	)
	readiness = get_version_readiness(version.name)

	active_version_row = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": plan.name, "status": "Active"},
		fields=["name", "plan_version_id", "version_number"],
		limit=1,
	)

	return {
		"forbidden": False,
		"not_found": False,
		"role": role,
		"plan": _plan_dto(plan),
		"version": _version_dto(version),
		"active_version": active_version_row[0] if active_version_row else None,
		"structure_summary": tree["counts"],
		"submission_authority": {
			"submitted_by": events["Submit for review"],
			"reviewed_by": events["Recommend for approval"] if is_approver else None,
		},
		"readiness": readiness,
		"allowed_actions": available_actions(version.name),
	}


# --------------------------------------------------------------------------
# STR-UI-04 Changes tab — reduced-scope version diff
# --------------------------------------------------------------------------

DIFF_LIMITATION_NOTE = (
	"Reduced-scope diff (STR-CHG-001 v1.3 Phase 7 decision log): compares "
	"Performance Target value/comparison changes and Strategy Node/"
	"Performance Indicator additions or removals by (node type, title) "
	"identity. Field-level changes to indicator definition/unit, node "
	"display order, or a same-identity title rename are not reported."
)


def _target_rows(plan_version_id: str) -> list[dict]:
	indicators = frappe.get_all(
		"Performance Indicator",
		filters={"plan_version_id": plan_version_id},
		fields=["name", "indicator_name"],
	)
	by_name = {i.name: i.indicator_name for i in indicators}
	if not by_name:
		return []
	targets = frappe.get_all(
		"Performance Target",
		filters={"indicator_id": ["in", list(by_name.keys())]},
		fields=["indicator_id", "financial_year_id", "target_by_date", "comparison", "target_value"],
	)
	out = []
	for t in targets:
		out.append(
			{
				"indicator_name": by_name.get(t.indicator_id),
				"financial_year_id": t.financial_year_id,
				"target_by_date": str(t.target_by_date) if t.target_by_date else None,
				"comparison": t.comparison,
				"target_value": t.target_value,
			}
		)
	return out


def diff_strategy_versions(base_version_id: str | None, compare_version_id: str) -> dict:
	"""STR-UI-04 Changes tab. `base_version_id` is None when the submitted
	version is v1 (no prior Active version to diff against)."""
	changes: list[dict] = []

	if base_version_id:
		base_targets = _target_rows(base_version_id)
		compare_targets = _target_rows(compare_version_id)

		def tkey(t):
			return (t["indicator_name"], t["financial_year_id"], t["target_by_date"])

		base_by_key = {tkey(t): t for t in base_targets}
		compare_by_key = {tkey(t): t for t in compare_targets}

		for key, ct in compare_by_key.items():
			bt = base_by_key.get(key)
			label = f"Target: {ct['indicator_name']}"
			if bt:
				if bt["comparison"] != ct["comparison"] or bt["target_value"] != ct["target_value"]:
					changes.append(
						{
							"item": label,
							"active": f"{bt['comparison']} {bt['target_value']}",
							"submitted": f"{ct['comparison']} {ct['target_value']}",
						}
					)
			else:
				changes.append(
					{"item": label, "active": "—", "submitted": f"{ct['comparison']} {ct['target_value']} (added)"}
				)
		for key, bt in base_by_key.items():
			if key not in compare_by_key:
				changes.append(
					{
						"item": f"Target: {bt['indicator_name']}",
						"active": f"{bt['comparison']} {bt['target_value']}",
						"submitted": "(removed)",
					}
				)

		base_nodes = {
			(n.node_type, n.title)
			for n in frappe.get_all(
				"Strategy Node", filters={"plan_version_id": base_version_id}, fields=["node_type", "title"]
			)
		}
		compare_nodes = {
			(n.node_type, n.title)
			for n in frappe.get_all(
				"Strategy Node", filters={"plan_version_id": compare_version_id}, fields=["node_type", "title"]
			)
		}
		for node_type, title in sorted(compare_nodes - base_nodes):
			changes.append({"item": f"{node_type}: {title}", "active": "—", "submitted": "Added"})
		for node_type, title in sorted(base_nodes - compare_nodes):
			changes.append({"item": f"{node_type}: {title}", "active": "Present", "submitted": "Removed"})
	else:
		for t in _target_rows(compare_version_id):
			changes.append(
				{
					"item": f"Target: {t['indicator_name']}",
					"active": "—",
					"submitted": f"{t['comparison']} {t['target_value']} (new plan)",
				}
			)

	return {"changes": changes, "limitation": DIFF_LIMITATION_NOTE}
