# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.7 §10/§12 — read contracts backing STR-UI-01..04.

Targets the current schema only: `Strategic Plan` (identity) /
`Strategic Plan Version` (version + status) / `Strategy Node` (unified
hierarchy) / `Performance Indicator` / `Performance Target`.

Every entry point that takes a plan or version id accepts either the record
name or the generated reference (`MOH-SP-0007`, `MOH-SPV-0007`): §10 puts
the reference in the URL, and a screen loaded from that URL must resolve
it without a second round trip. Routes returned to the client are the §10
route arrays for `frappe.set_route`, never a client-side status map.

Page-load authorisation follows KT-STD-001 §3A: a read that the caller may
not perform returns `{"forbidden": True}` as data so the screen renders its
own inline Forbidden panel; it never raises the framework 403.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_strategy.services.strategy_audit import list_events
from kentender_strategy.services.strategy_authorization import (
	CAP_APPROVE,
	CAP_AUTHOR,
	ROLE_STRATEGY_APPROVER,
	ROLE_STRATEGY_AUTHOR,
	has_plan_create_capability,
	has_plan_version_capability,
	holds_approver_responsibility,
)
from kentender_strategy.services.strategy_readiness import get_version_readiness
from kentender_strategy.services.strategy_reference import resolve_plan_name, resolve_version_name
from kentender_strategy.services.strategy_transitions import available_actions

# §6 — read access is produced by the actor's assignments: the two Strategy
# governance responsibilities plus the registered Auditor business role.
# Administrator/System Manager get technical read (AUTH-ADR-001 v1.6 §8).
UNRESTRICTED_READ_ROLES = ("System Manager", "Auditor")
_LIFECYCLE_ROLES = (ROLE_STRATEGY_AUTHOR, ROLE_STRATEGY_APPROVER)

PAGE = "strategy"


def _can_read() -> bool:
	"""One site is one Procuring Entity, so read eligibility is a pure
	assignment-projection check (the Frappe Roles exist only as projections
	of Enabled Site-wide assignments, v1.6 §5.2) — no PE set, no working
	context, no User Permission scope."""
	roles = frappe.get_roles()
	return any(r in roles for r in UNRESTRICTED_READ_ROLES + _LIFECYCLE_ROLES)


def _plan_dto(plan) -> dict:
	return {
		"id": plan.name,
		"reference": plan.plan_id,
		"title": plan.title,
		"plan_role": plan.plan_role,
		"parent_primary_plan_id": plan.parent_primary_plan_id,
		"period_start": str(plan.period_start) if plan.period_start else None,
		"period_end": str(plan.period_end) if plan.period_end else None,
		"period_label": _period_label(plan.period_start, plan.period_end),
	}


def _actor_name(user: str | None) -> str | None:
	if not user:
		return None
	return frappe.utils.get_fullname(user) or user


def _when_label(value) -> str | None:
	"""Display form of an audit timestamp (site time), e.g. 24 Nov 2026, 16:20."""
	if not value:
		return None
	try:
		return frappe.utils.get_datetime(value).strftime("%d %b %Y, %H:%M")
	except Exception:
		return str(value)


def _result_label(comparison: str | None, value) -> str:
	number = frappe.utils.flt(value)
	shown = f"{number:g}" if number == int(number) or abs(number) < 1e6 else str(number)
	return f"{comparison} {shown}"


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
		"return_reason": version.return_reason or None,
		# KT-STD-001 §11 optimistic concurrency token every command carries.
		"expected_version": str(version.modified),
	}


# --------------------------------------------------------------------------
# §10 routes — the one place the client learns where a record lives
# --------------------------------------------------------------------------


def plan_route(plan_reference: str, *rest: str) -> list[str]:
	return [PAGE, "plan", plan_reference, *rest]


def approval_route(version_reference: str, *rest: str) -> list[str]:
	return [PAGE, "approval", version_reference, *rest]


# --------------------------------------------------------------------------
# STR-UI-01 Strategy Portfolio
# --------------------------------------------------------------------------

# §12.1: View / Continue draft / Approve follow the server-returned
# `available_action`; the browser never derives authority from status.
_STATUS_ACTION_LABELS: dict[str, str] = {
	"Draft": "Continue draft",
	"Submitted for approval": "Approve",
}


def _row_action(plan_reference: str, version_row: dict | None) -> dict:
	if not version_row:
		return {"label": _("View"), "route": plan_route(plan_reference)}
	status = version_row["status"]
	if status == "Submitted for approval" and available_actions(version_row["name"]):
		return {"label": _("Approve"), "route": approval_route(version_row["plan_version_id"])}
	if status == "Draft" and available_actions(version_row["name"]):
		return {
			"label": _(_STATUS_ACTION_LABELS["Draft"]),
			"route": plan_route(plan_reference, "version", str(version_row["version_number"]), "structure"),
		}
	return {"label": _("View"), "route": plan_route(plan_reference)}


def _latest_version_row(plan_name: str) -> dict | None:
	rows = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": plan_name},
		fields=["name", "plan_version_id", "version_number", "status"],
		order_by="version_number desc",
		limit=1,
	)
	return rows[0] if rows else None


def get_strategy_portfolio(
	search: str | None = None, plan_role: str | None = None, status: str | None = None
) -> dict:
	"""STR-UI-01 payload: plan register rows + My work + the site identity.
	`{"forbidden": True}` as data when the caller holds none of the
	read-eligible assignments (KT-STD-001 §3A). §12.1: search matches plan
	reference and title; plan role and status filters are server-side; the
	counts use the same predicate as the rows."""
	if not _can_read():
		return {"forbidden": True}

	filters: dict = {}
	if plan_role:
		filters["plan_role"] = plan_role
	or_filters = None
	if search:
		needle = f"%{search.strip()}%"
		or_filters = [["title", "like", needle], ["plan_id", "like", needle]]
	plans = frappe.get_all(
		"Strategic Plan",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "plan_id", "title", "plan_role", "parent_primary_plan_id", "period_start", "period_end"],
		order_by="modified desc",
		limit=200,
	)
	rows = []
	for p in plans:
		latest = _latest_version_row(p.name)
		row_status = latest["status"] if latest else "No version"
		if status and row_status != status:
			continue
		action = _row_action(p.plan_id, latest)
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
				"status": row_status,
				"available_action": action["label"],
				"action_route": action["route"],
			}
		)

	return {
		"forbidden": False,
		# Read-offer-vs-command parity: the create action is offered only
		# when save_strategy_plan_draft's own gate would pass.
		"can_create_plan": has_plan_create_capability(frappe.session.user),
		"plans": rows,
		"my_work": _my_work_versions(),
		"counts": {"plans": len(rows), "my_work": 0},
	}


def _my_work_versions() -> list[dict]:
	"""§12.1 — only live records on which the actor may perform the next
	command: Submitted versions this actor may return/approve, and Draft
	versions this actor may continue."""
	versions = frappe.get_all(
		"Strategic Plan Version",
		filters={"status": ["in", ("Submitted for approval", "Draft")]},
		fields=["name", "plan_version_id", "plan_id", "version_number", "status"],
		order_by="modified desc",
	)
	out = []
	for v in versions:
		plan = frappe.db.get_value("Strategic Plan", v.plan_id, ["plan_id", "title"], as_dict=True)
		if not plan:
			continue
		actions = available_actions(v.name)
		if not actions:
			continue
		route = (
			approval_route(v.plan_version_id)
			if v.status == "Submitted for approval"
			else plan_route(plan.plan_id, "version", str(v.version_number), "structure")
		)
		out.append(
			{
				"plan_id": v.plan_id,
				"plan_reference": plan.plan_id,
				"plan_title": plan.title,
				"version_id": v.name,
				"version_reference": v.plan_version_id,
				"version_number": v.version_number,
				"status": v.status,
				"allowed_actions": actions,
				"action_label": _("Review") if v.status == "Submitted for approval" else _("Continue draft"),
				"action_route": route,
			}
		)
	return out


# --------------------------------------------------------------------------
# Structure tree (shared by STR-UI-02 read view / STR-UI-03 editor / STR-UI-04)
# --------------------------------------------------------------------------


def get_strategy_tree(plan_version_id: str) -> dict:
	plan_version_id = resolve_version_name(plan_version_id) or plan_version_id
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
			fields=["name", "target_id", "indicator_id", "fiscal_year", "target_by_date", "comparison", "target_value"],
			order_by="fiscal_year asc, target_by_date asc",
		)
		if indicator_names
		else []
	)

	targets_by_indicator: dict[str, list] = {}
	for t in targets:
		targets_by_indicator.setdefault(t.indicator_id, []).append(t)

	def target_node(t) -> dict:
		period = t.fiscal_year or (str(t.target_by_date) if t.target_by_date else None)
		return {
			"id": t.name,
			"reference": t.target_id,
			"node_type": "Performance Target",
			"title": _result_label(t.comparison, t.target_value),
			"fiscal_year": t.fiscal_year,
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
		"performance_indicators": len(indicators),
		"performance_targets": len(targets),
	}
	version = frappe.db.get_value(
		"Strategic Plan Version", plan_version_id, ["name", "plan_version_id", "status", "modified"], as_dict=True
	)
	return {
		"tree": roots,
		"counts": counts,
		"version_id": version.name if version else plan_version_id,
		"version_reference": version.plan_version_id if version else None,
		"status": version.status if version else None,
		# §12.3 — one expected version token for the whole Draft tree.
		"expected_version": str(version.modified) if version else None,
	}


# --------------------------------------------------------------------------
# STR-UI-02 Plan workspace
# --------------------------------------------------------------------------


def _authority_from_events(version_name: str, actions: tuple[str, ...]) -> dict[str, dict | None]:
	rows = list_events("Strategic Plan Version", version_name)
	out: dict[str, dict | None] = {a: None for a in actions}
	for row in rows:  # newest first; keep the most recent occurrence of each action
		action = row.get("action")
		if action in out and out[action] is None:
			out[action] = {
				"actor": row.get("performed_by"),
				"actor_name": _actor_name(row.get("performed_by")),
				"at": str(row.get("timestamp")),
				"at_label": _when_label(row.get("timestamp")),
			}
	return out


def get_plan_workspace(plan_id: str) -> dict:
	plan_name = resolve_plan_name(plan_id)
	if not plan_name:
		return {"not_found": True}
	if not _can_read():
		return {"forbidden": True}
	plan = frappe.get_doc("Strategic Plan", plan_name)

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
			"return_reason",
		],
		order_by="version_number desc",
	)
	if not versions:
		return {"forbidden": False, "not_found": False, "plan": _plan_dto(plan), "versions": [], "no_version": True}

	by_status = {v.status: v for v in versions}
	active = by_status.get("Active")
	# An open (Draft/Submitted for approval) successor always takes priority
	# over the steady-state Active version: a plan can hold one Active and
	# one open version at a time, and the open one is the one being worked.
	open_statuses = ("Draft", "Submitted for approval")
	open_version = next((v for v in versions if v.status in open_statuses), None)
	current = open_version or active or versions[0]

	tree = get_strategy_tree(current.name)
	events = _authority_from_events(current.name, ("Approve", "Submit for approval", "Return"))

	current_authority = {"approved_by": events["Approve"]} if active else None
	readiness = get_version_readiness(current.name) if current.status in open_statuses else None

	is_editable_draft = current.status == "Draft" and has_plan_version_capability(
		frappe.session.user, CAP_AUTHOR, current.name
	)

	open_successor_exists = any(v.status in open_statuses for v in versions)
	can_create_successor = (
		bool(active)
		and not open_successor_exists
		and has_plan_version_capability(frappe.session.user, CAP_AUTHOR, current.name)
	)
	# §12.2 — plan identity is editable only while its first version is Draft.
	identity_editable = (
		len(versions) == 1 and versions[0].status == "Draft" and is_editable_draft
	)

	return {
		"forbidden": False,
		"not_found": False,
		"no_version": False,
		"plan": _plan_dto(plan),
		"current_version": _version_dto(frappe.get_doc("Strategic Plan Version", current.name)),
		"active_version": _version_dto(frappe.get_doc("Strategic Plan Version", active.name)) if active else None,
		"versions": [_version_dto(frappe.get_doc("Strategic Plan Version", v.name)) for v in versions],
		"structure_summary": tree["counts"],
		"current_authority": current_authority,
		"submission_authority": {"submitted_by": events["Submit for approval"], "returned_by": events["Return"]},
		"readiness": readiness,
		"is_editable_draft": is_editable_draft,
		"capabilities": {
			"create_successor": can_create_successor,
			"edit_identity": identity_editable,
			"submit": is_editable_draft,
		},
		"routes": {
			"overview": plan_route(plan.plan_id),
			"structure": plan_route(plan.plan_id, "version", str(current.version_number), "structure"),
			"history": plan_route(plan.plan_id, "history"),
			"approval": approval_route(current.plan_version_id) if current.status == "Submitted for approval" else None,
		},
	}


def get_plan_history(plan_id: str) -> list[dict]:
	plan_name = resolve_plan_name(plan_id)
	if not plan_name or not _can_read():
		return []
	version_names = frappe.get_all("Strategic Plan Version", filters={"plan_id": plan_name}, pluck="name")
	out: list[dict] = []
	for v in version_names:
		for row in list_events("Strategic Plan Version", v):
			out.append(
				{
					"at": str(row.get("timestamp")),
					"at_label": _when_label(row.get("timestamp")),
					"event": row.get("action"),
					"actor": row.get("performed_by"),
					"actor_name": _actor_name(row.get("performed_by")),
					"reason": (row.get("metadata") or {}).get("reason") if isinstance(row.get("metadata"), dict) else None,
					"version_id": v,
				}
			)
	out.sort(key=lambda r: r["at"], reverse=True)
	return out


def get_version_history(plan_version_id: str) -> list[dict]:
	"""§12.2/§12.4 — chronological, append-only lifecycle and draft-save
	events for ONE version, newest first, with the required return reason."""
	version_name = resolve_version_name(plan_version_id)
	if not version_name or not _can_read():
		return []
	out = []
	for row in list_events("Strategic Plan Version", version_name):
		metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
		out.append(
			{
				"at": str(row.get("timestamp")),
				"at_label": _when_label(row.get("timestamp")),
				"event": row.get("action"),
				"actor": row.get("performed_by"),
				"actor_name": _actor_name(row.get("performed_by")),
				"reason": metadata.get("reason"),
				"version_id": version_name,
			}
		)
	out.sort(key=lambda r: r["at"], reverse=True)
	return out


# --------------------------------------------------------------------------
# STR-UI-04 Approval task
# --------------------------------------------------------------------------


def get_version_review_overview(plan_version_id: str) -> dict:
	version_name = resolve_version_name(plan_version_id)
	if not version_name:
		return {"not_found": True}
	if not _can_read():
		return {"forbidden": True}
	version = frappe.get_doc("Strategic Plan Version", version_name)
	plan = frappe.get_doc("Strategic Plan", version.plan_id)

	user = frappe.session.user
	# §12.4 — a direct task route requires an Active Strategy Approver
	# assignment; a read-only user is denied rather than shown a disabled
	# workflow form. The no-self-approval rule is a per-version command
	# block, not an access rule: the submitter who also holds Approver may
	# open the task and sees no decision actions on it.
	if not holds_approver_responsibility(user):
		return {"forbidden": True, "reason": "approver_required"}
	is_approver = has_plan_version_capability(user, CAP_APPROVE, version)

	tree = get_strategy_tree(version.name)
	events = _authority_from_events(version.name, ("Submit for approval", "Return"))
	readiness = get_version_readiness(version.name)

	active_version_row = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": plan.name, "status": "Active", "name": ["!=", version.name]},
		fields=["name", "plan_version_id", "version_number"],
		limit=1,
	)

	return {
		"forbidden": False,
		"not_found": False,
		"role": "approver" if is_approver else None,
		"plan": _plan_dto(plan),
		"version": _version_dto(version),
		"active_version": active_version_row[0] if active_version_row else None,
		"structure_summary": tree["counts"],
		"submission_authority": {"submitted_by": events["Submit for approval"]},
		"readiness": readiness,
		"allowed_actions": available_actions(version.name),
		"expected_version": str(version.modified),
		"routes": {
			"plan": plan_route(plan.plan_id),
			"overview": approval_route(version.plan_version_id),
			"structure": approval_route(version.plan_version_id, "structure"),
			"changes": approval_route(version.plan_version_id, "changes"),
			"history": approval_route(version.plan_version_id, "history"),
		},
	}


# --------------------------------------------------------------------------
# STR-UI-04 Changes tab — server-side diff between baseline and submitted
# --------------------------------------------------------------------------

DIFF_LIMITATION_NOTE = (
	"Compares Performance Target value/comparison changes and Strategy Node/"
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
		fields=["indicator_id", "fiscal_year", "target_by_date", "comparison", "target_value"],
	)
	out = []
	for t in targets:
		out.append(
			{
				"indicator_name": by_name.get(t.indicator_id),
				"fiscal_year": t.fiscal_year,
				"target_by_date": str(t.target_by_date) if t.target_by_date else None,
				"comparison": t.comparison,
				"target_value": t.target_value,
			}
		)
	return out


def diff_strategy_versions(base_version_id: str | None, compare_version_id: str) -> dict:
	"""STR-UI-04 Changes tab: computed server-side between
	`based_on_plan_version_id` and the submitted version (§12.4). When the
	caller passes no base, the submitted version's own recorded baseline is
	used; a first version has none and every item reads as new."""
	compare_version_id = resolve_version_name(compare_version_id) or compare_version_id
	base_version_id = resolve_version_name(base_version_id) if base_version_id else None
	if not base_version_id:
		base_version_id = frappe.db.get_value("Strategic Plan Version", compare_version_id, "based_on_plan_version_id")
	changes: list[dict] = []

	if base_version_id:
		base_targets = _target_rows(base_version_id)
		compare_targets = _target_rows(compare_version_id)

		def tkey(t):
			return (t["indicator_name"], t["fiscal_year"], t["target_by_date"])

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
							"active": _result_label(bt["comparison"], bt["target_value"]),
							"submitted": _result_label(ct["comparison"], ct["target_value"]),
						}
					)
			else:
				changes.append(
					{"item": label, "active": "—", "submitted": f"{_result_label(ct['comparison'], ct['target_value'])} (added)"}
				)
		for key, bt in base_by_key.items():
			if key not in compare_by_key:
				changes.append(
					{
						"item": f"Target: {bt['indicator_name']}",
						"active": _result_label(bt["comparison"], bt["target_value"]),
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

		base_indicators = {
			(n.indicator_name)
			for n in frappe.get_all(
				"Performance Indicator", filters={"plan_version_id": base_version_id}, fields=["indicator_name"]
			)
		}
		compare_indicators = {
			(n.indicator_name)
			for n in frappe.get_all(
				"Performance Indicator", filters={"plan_version_id": compare_version_id}, fields=["indicator_name"]
			)
		}
		for title in sorted(compare_indicators - base_indicators):
			changes.append({"item": f"Performance Indicator: {title}", "active": "—", "submitted": "Added"})
		for title in sorted(base_indicators - compare_indicators):
			changes.append({"item": f"Performance Indicator: {title}", "active": "Present", "submitted": "Removed"})
	else:
		for t in _target_rows(compare_version_id):
			changes.append(
				{
					"item": f"Target: {t['indicator_name']}",
					"active": "—",
					"submitted": f"{_result_label(t['comparison'], t['target_value'])} (new plan)",
				}
			)

	return {"changes": changes, "base_version_id": base_version_id, "limitation": DIFF_LIMITATION_NOTE}


def list_available_fiscal_years(plan_id: str | None = None) -> list[dict]:
	"""§12.3 — Period offers only ERPNext Fiscal Years overlapping the plan
	period (plus the plan-period date option the client adds itself).
	`ignore_permissions` is safe here: Fiscal Year rows carry only date
	ranges, and Strategy has no write path onto the doctype."""
	rows = frappe.get_all(
		"Fiscal Year",
		fields=["name", "year_start_date", "year_end_date"],
		filters={"disabled": 0},
		order_by="year_start_date asc",
		limit_page_length=0,
		ignore_permissions=True,
	)
	plan_name = resolve_plan_name(plan_id) if plan_id else None
	if plan_name:
		period = frappe.db.get_value("Strategic Plan", plan_name, ["period_start", "period_end"], as_dict=True)
		if period and period.period_start and period.period_end:
			start, end = frappe.utils.getdate(period.period_start), frappe.utils.getdate(period.period_end)
			rows = [
				r
				for r in rows
				if frappe.utils.getdate(r.year_start_date) <= end and frappe.utils.getdate(r.year_end_date) >= start
			]
	return [
		{"name": r.name, "start": str(r.year_start_date), "end": str(r.year_end_date)}
		for r in rows
	]
