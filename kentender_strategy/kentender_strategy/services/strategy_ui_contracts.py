# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.8 §10/§11/§12 — read contracts backing STR-UI-01..04.

Targets the current schema only: `Strategic Plan` (identity) /
`Strategic Plan Version` (version + status) / `Strategy Node` (unified
hierarchy) / `Performance Indicator` / `Performance Target`.

Every entry point that takes a plan or version id accepts either the record
name or the generated reference (`MOH-SP-0007`, `MOH-SPV-0007`): §10 puts
the reference in the URL, and a screen loaded from that URL must resolve
it without a second round trip. Routes returned to the client are the §10
route arrays for `frappe.set_route`, never a client-side status map.

v1.8 (§4.7, §11, plan D10): every visible label — plan type, status,
available action, review type, event wording — is produced here from the
stored enums and evidence. The Vue layer maps nothing from a raw enum, and
the stored enums, IDs and audit actions are never renamed.

Page-load authorisation follows KT-STD-001 v1.5 §3A: a read that the caller
may not perform returns `{"forbidden": True}` as data so the screen renders
its own inline Forbidden panel; it never raises the framework 403. Technical
readers (§3A.6) are never Forbidden and never masked as Not found.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_core.services.authorization import is_technical
from kentender_strategy.services.strategy_audit import list_events
from kentender_strategy.services.strategy_authorization import (
	CAP_APPROVE,
	CAP_AUTHOR,
	has_plan_create_capability,
	has_plan_version_capability,
	holds_approver_responsibility,
	holds_strategy_read_responsibility,
)
from kentender_strategy.services.strategy_readiness import (
	get_version_approval_blockers,
	get_version_readiness,
)
from kentender_strategy.services.strategy_reference import resolve_plan_name, resolve_version_name
from kentender_strategy.services.strategy_transitions import available_actions

PAGE = "strategy"

# §4.7 — presentation labels over the unchanged stored enums.
PLAN_TYPE_LABELS: dict[str, str] = {
	"Primary": "Main strategic plan",
	"Supporting Framework": "Supporting framework",
}
STATUS_ACTIVE, STATUS_SUBMITTED, STATUS_DRAFT, STATUS_SUPERSEDED = (
	"Active",
	"Submitted for approval",
	"Draft",
	"Superseded",
)


def _can_read() -> bool:
	"""§6/KT-STD-001 §3A.6 — read eligibility is a pure assignment-projection
	check plus the technical-read allowance. Delegates to the shared
	`strategy_authorization` gate rather than testing bare Frappe Roles."""
	return holds_strategy_read_responsibility(frappe.session.user)


# --------------------------------------------------------------------------
# Labels and formatting
# --------------------------------------------------------------------------


def plan_type_label(plan_role: str | None) -> str:
	return _(PLAN_TYPE_LABELS.get(plan_role or "", plan_role or ""))


def version_status_label(status: str | None, *, version_number: int | None = None, return_reason: str | None = None) -> str:
	"""§4.7 — Current / Previous version / Awaiting approval / Changes
	requested / Draft / Draft update. The stored status is untouched."""
	if status == STATUS_ACTIVE:
		return _("Current")
	if status == STATUS_SUPERSEDED:
		return _("Previous version")
	if status == STATUS_SUBMITTED:
		return _("Awaiting approval")
	if status == STATUS_DRAFT:
		if return_reason:
			return _("Changes requested")
		if version_number and int(version_number) > 1:
			return _("Draft update")
		return _("Draft")
	return status or ""


def status_tone(status: str | None) -> str:
	"""The `.kt-status` tone for a stored status."""
	if status == STATUS_ACTIVE:
		return "is-live"
	if status == STATUS_SUBMITTED:
		return "is-pending"
	if status == STATUS_SUPERSEDED:
		return "is-pending"
	return "is-draft"


def _tz_abbreviation() -> str:
	try:
		from zoneinfo import ZoneInfo

		tz = frappe.utils.get_system_timezone()
		return frappe.utils.now_datetime().replace(tzinfo=ZoneInfo(tz)).tzname() or ""
	except Exception:
		return ""


def _date_label(value) -> str | None:
	"""1 Jul 2023 — day without a leading zero, as every §11 fixture shows."""
	if not value:
		return None
	try:
		return frappe.utils.getdate(value).strftime("%-d %b %Y")
	except Exception:
		return str(value)


def _when_label(value) -> str | None:
	"""24 Nov 2026, 16:20 EAT — site time with the zone abbreviation."""
	if not value:
		return None
	try:
		dt = frappe.utils.get_datetime(value)
		abbr = _tz_abbreviation()
		return f"{dt.strftime('%-d %b %Y, %H:%M')}{' ' + abbr if abbr else ''}"
	except Exception:
		return str(value)


def _period_label(start, end) -> str | None:
	if not start or not end:
		return None
	return f"{_date_label(start)} – {_date_label(end)}"


def _period_fy_label(start, end) -> str | None:
	"""§11.1 register column: `2023/24–2027/28` — the July-to-June financial
	years a plan period spans, from its first to its last."""
	if not start or not end:
		return None
	sd, ed = frappe.utils.getdate(start), frappe.utils.getdate(end)
	first = sd.year if sd.month >= 7 else sd.year - 1
	last = ed.year if ed.month >= 7 else ed.year - 1
	return f"{first}/{(first + 1) % 100:02d}–{last}/{(last + 1) % 100:02d}"


def fiscal_year_label(name: str | None) -> str | None:
	"""`2027-2028` → `FY 2027/28`; any other catalogue name is shown as
	`FY {name}`."""
	if not name:
		return None
	parts = str(name).split("-")
	if len(parts) == 2 and all(p.isdigit() for p in parts) and len(parts[1]) == 4:
		return f"FY {parts[0]}/{parts[1][-2:]}"
	return f"FY {name}"


def target_period_label(fiscal_year: str | None, target_by_date) -> str | None:
	if fiscal_year:
		return fiscal_year_label(fiscal_year)
	if target_by_date:
		return _("By {0}").format(_date_label(target_by_date))
	return None


def _unit_suffix(unit: str | None) -> str:
	return "%" if (unit or "").strip().lower() == "percentage" else ""


def _number(value) -> str:
	number = frappe.utils.flt(value)
	return f"{number:g}" if number == int(number) or abs(number) < 1e6 else str(number)


def _result_label(comparison: str | None, value, unit: str | None = None) -> str:
	"""`At least 80%` for a Percentage indicator, `At least 80` otherwise."""
	return f"{comparison} {_number(value)}{_unit_suffix(unit)}"


def _actor_name(user: str | None) -> str | None:
	if not user:
		return None
	return frappe.utils.get_fullname(user) or user


# --------------------------------------------------------------------------
# DTOs
# --------------------------------------------------------------------------


def _plan_dto(plan) -> dict:
	return {
		"id": plan.name,
		"reference": plan.plan_id,
		"title": plan.title,
		"plan_role": plan.plan_role,
		"plan_type_label": plan_type_label(plan.plan_role),
		"parent_primary_plan_id": plan.parent_primary_plan_id,
		"parent_primary_plan_title": (
			frappe.db.get_value("Strategic Plan", plan.parent_primary_plan_id, "title")
			if plan.parent_primary_plan_id
			else None
		),
		"period_start": str(plan.period_start) if plan.period_start else None,
		"period_end": str(plan.period_end) if plan.period_end else None,
		"period_label": _period_label(plan.period_start, plan.period_end),
		"period_fy_label": _period_fy_label(plan.period_start, plan.period_end),
	}


def _has_been_submitted(version_name: str) -> bool:
	"""§5.1 — "Records are never deleted after first submission": a Draft
	that was returned still carries its submission in the audit trail."""
	return any(row.get("action") == "Submit for approval" for row in list_events("Strategic Plan Version", version_name))


def _version_dto(version) -> dict:
	return {
		"id": version.name,
		"reference": version.plan_version_id,
		"version_number": version.version_number,
		"status": version.status,
		"status_label": version_status_label(
			version.status, version_number=version.version_number, return_reason=version.return_reason
		),
		"status_tone": status_tone(version.status),
		"is_update": int(version.version_number or 1) > 1,
		"effective_from": str(version.effective_from) if version.effective_from else None,
		"effective_to": str(version.effective_to) if version.effective_to else None,
		"effective_from_label": _date_label(version.effective_from),
		"effective_to_label": _date_label(version.effective_to),
		"effective_period_label": _period_label(version.effective_from, version.effective_to),
		"based_on_plan_version_id": version.based_on_plan_version_id,
		"return_reason": version.return_reason or None,
		"has_been_submitted": _has_been_submitted(version.name),
		# KT-STD-001 §11 optimistic concurrency token every command carries.
		"expected_version": str(version.modified),
	}


# --------------------------------------------------------------------------
# §10 routes — the one place the client learns where a record lives
# --------------------------------------------------------------------------


def plan_route(plan_reference: str, *rest: str) -> list[str]:
	return [PAGE, "plan", plan_reference, *rest]


def version_route(plan_reference: str, version_number, *rest: str) -> list[str]:
	return [PAGE, "plan", plan_reference, "version", str(version_number), *rest]


def approval_route(version_reference: str, *rest: str) -> list[str]:
	return [PAGE, "approval", version_reference, *rest]


# --------------------------------------------------------------------------
# STR-UI-01 Strategic plans
# --------------------------------------------------------------------------


def _row_action(plan_reference: str, version_row: dict | None) -> dict:
	"""§11.1/§12.1 — Continue draft / Correct and resubmit / Review / View,
	from the server's own available_actions; never guessed from status."""
	if not version_row:
		return {"label": _("View"), "route": plan_route(plan_reference)}
	status = version_row["status"]
	if status == STATUS_SUBMITTED and available_actions(version_row["name"]):
		return {"label": _("Review"), "route": approval_route(version_row["plan_version_id"])}
	if status == STATUS_DRAFT and available_actions(version_row["name"]):
		label = _("Correct and resubmit") if version_row.get("return_reason") else _("Continue draft")
		return {"label": label, "route": version_route(plan_reference, version_row["version_number"], "structure")}
	return {"label": _("View"), "route": plan_route(plan_reference)}


def _latest_version_row(plan_name: str) -> dict | None:
	rows = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": plan_name},
		fields=["name", "plan_version_id", "version_number", "status", "return_reason"],
		order_by="version_number desc",
		limit=1,
	)
	return rows[0] if rows else None


def _register_status_row(plan_name: str) -> dict | None:
	"""The version whose status the register row shows: the open successor
	when one exists (that is where the work is), else the latest."""
	rows = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": plan_name},
		fields=["name", "plan_version_id", "version_number", "status", "return_reason"],
		order_by="version_number desc",
	)
	if not rows:
		return None
	for r in rows:
		if r.status in (STATUS_DRAFT, STATUS_SUBMITTED):
			return r
	return rows[0]


def get_strategy_portfolio(
	search: str | None = None, plan_role: str | None = None, status: str | None = None
) -> dict:
	"""STR-UI-01 payload: plan register rows + the Actions projection.
	`{"forbidden": True}` as data when the caller holds none of the
	read-eligible assignments (KT-STD-001 §3A). §12.1: search matches plan
	reference and title; plan type and status filters are server-side; the
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
		latest = _register_status_row(p.name)
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
				"status_label": (
					version_status_label(
						latest["status"], version_number=latest["version_number"], return_reason=latest.get("return_reason")
					)
					if latest
					else _("No version")
				),
				"status_tone": status_tone(latest["status"]) if latest else "is-pending",
				"available_action": action["label"],
				"action_route": action["route"],
			}
		)

	my_work = _my_work_versions()
	return {
		"forbidden": False,
		# Read-offer-vs-command parity: the create action is offered only
		# when save_strategy_plan_draft's own gate would pass.
		"can_create_plan": has_plan_create_capability(frappe.session.user),
		"plans": rows,
		"my_work": my_work,
		"counts": {"plans": len(rows), "my_work": len(my_work)},
		"status_options": [
			{"value": STATUS_DRAFT, "label": _("Draft")},
			{"value": STATUS_SUBMITTED, "label": _("Awaiting approval")},
			{"value": STATUS_ACTIVE, "label": _("Current")},
			{"value": STATUS_SUPERSEDED, "label": _("Previous version")},
		],
		"plan_type_options": [{"value": k, "label": _(v)} for k, v in PLAN_TYPE_LABELS.items()],
	}


def _my_work_versions() -> list[dict]:
	"""§11.1/§12.1 Actions — only live records on which the actor may
	perform the next command: Submitted versions this actor may return or
	approve (Review), and Draft versions this actor may continue. Technical
	readers decide nothing, so their queue is empty (KT-STD-001 §3A.6)."""
	versions = frappe.get_all(
		"Strategic Plan Version",
		filters={"status": ["in", (STATUS_SUBMITTED, STATUS_DRAFT)]},
		fields=["name", "plan_version_id", "plan_id", "version_number", "status", "return_reason"],
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
		submitted = _authority_from_events(v.name, ("Submit for approval",))["Submit for approval"]
		if v.status == STATUS_SUBMITTED:
			route = approval_route(v.plan_version_id)
			action_label = _("Review")
			status_label = _("Awaiting review")
		else:
			route = version_route(plan.plan_id, v.version_number, "structure")
			action_label = _("Correct and resubmit") if v.return_reason else _("Continue draft")
			status_label = version_status_label(v.status, version_number=v.version_number, return_reason=v.return_reason)
		out.append(
			{
				"plan_id": v.plan_id,
				"plan_reference": plan.plan_id,
				"plan_title": plan.title,
				"version_id": v.name,
				"version_reference": v.plan_version_id,
				"version_number": v.version_number,
				"status": v.status,
				"status_label": status_label,
				"status_tone": status_tone(v.status),
				"review_type": _("New plan") if int(v.version_number or 1) == 1 else _("Plan changes"),
				"submitted_by": submitted["actor_name"] if submitted else None,
				"submitted_at_label": submitted["at_label"] if submitted else None,
				"allowed_actions": actions,
				"action_label": action_label,
				"action_route": route,
			}
		)
	return out


# --------------------------------------------------------------------------
# Structure tree (shared by STR-UI-02 read view / STR-UI-03 editor / STR-UI-04)
# --------------------------------------------------------------------------


def get_strategy_tree(plan_version_id: str) -> dict:
	# §6 — a whitelisted endpoint in its own right (not only reached via an
	# already-gated caller), so it carries the same read gate; a non-reader
	# gets a masked not-found rather than a Forbidden that would confirm the
	# version exists. Technical readers always pass.
	if not _can_read():
		return {"not_found": True}
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
		order_by="creation asc",
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

	def target_node(t, unit) -> dict:
		return {
			"id": t.name,
			"reference": t.target_id,
			"node_type": "Performance Target",
			"title": _result_label(t.comparison, t.target_value, unit),
			"fiscal_year": t.fiscal_year,
			"target_by_date": str(t.target_by_date) if t.target_by_date else None,
			"period_label": target_period_label(t.fiscal_year, t.target_by_date),
			"result_label": _result_label(t.comparison, t.target_value, unit),
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
			"unit_suffix": _unit_suffix(i.unit),
			"children": [target_node(t, i.unit) for t in targets_by_indicator.get(i.name, [])],
		}

	children_by_parent: dict[str | None, list] = {}
	for n in nodes:
		children_by_parent.setdefault(n.parent_node_id or None, []).append(n)

	def structure_node(n, path: list[str]) -> dict:
		child_nodes = [structure_node(c, [*path, n.title]) for c in children_by_parent.get(n.name, [])]
		child_indicators = [indicator_node(i) for i in indicators_by_node.get(n.name, [])]
		return {
			"id": n.name,
			"reference": n.strategy_node_id,
			"node_type": n.node_type,
			"title": n.title,
			"display_order": n.display_order,
			"parent_node_id": n.parent_node_id or None,
			"path": path,
			"children": child_nodes + child_indicators,
		}

	roots = [structure_node(n, []) for n in children_by_parent.get(None, [])]

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
		"objectives": _objectives_from_tree(roots),
		"counts": counts,
		"version_id": version.name if version else plan_version_id,
		"version_reference": version.plan_version_id if version else None,
		"status": version.status if version else None,
		# §12.3 — one expected version token for the whole Draft tree.
		"expected_version": str(version.modified) if version else None,
	}


def _objectives_from_tree(roots: list[dict]) -> list[dict]:
	"""§11.3/§11.6 — the strategy's meaning, objective by objective: every
	Strategic Objective with its full ancestor path, its Indicators, their
	complete definitions and units, and every Target."""
	out: list[dict] = []

	def walk(node):
		if node["node_type"] == "Strategic Objective":
			out.append(
				{
					"id": node["id"],
					"reference": node.get("reference"),
					"title": node["title"],
					"path": node.get("path") or [],
					"path_label": " / ".join(node.get("path") or []),
					"indicators": [
						{
							"id": ind["id"],
							"reference": ind.get("reference"),
							"name": ind["title"],
							"definition": ind.get("definition"),
							"unit": ind.get("unit"),
							"targets": [
								{
									"id": t["id"],
									"reference": t.get("reference"),
									"period_label": t["period_label"],
									"result_label": t["result_label"],
									"value_label": f"{_number(t['target_value'])}{_unit_suffix(ind.get('unit'))}",
									"comparison": t["comparison"],
								}
								for t in ind["children"]
							],
						}
						for ind in node["children"]
						if ind["node_type"] == "Performance Indicator"
					],
				}
			)
			return
		for child in node.get("children", []):
			if child["node_type"] not in ("Performance Indicator", "Performance Target"):
				walk(child)

	for root in roots:
		walk(root)
	return out


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


def _pending_update(plan_reference: str, versions: list, active) -> dict | None:
	"""§11.3 — an open successor of the Current version, shown separately
	from the current facts and never in their place."""
	if not active:
		return None
	open_version = next((v for v in versions if v.status in (STATUS_DRAFT, STATUS_SUBMITTED)), None)
	if not open_version:
		return None
	if open_version.status == STATUS_SUBMITTED:
		return {
			"kind": "submitted",
			"version_number": open_version.version_number,
			"version_id": open_version.name,
			"message": _("Update awaiting Strategy Approver review. The current plan remains in use."),
			"route": version_route(plan_reference, open_version.version_number),
			"approval_route": approval_route(open_version.plan_version_id),
			"action_label": None,
		}
	continue_allowed = has_plan_version_capability(frappe.session.user, CAP_AUTHOR, open_version.name)
	return {
		"kind": "draft",
		"version_number": open_version.version_number,
		"version_id": open_version.name,
		"message": _("Update in progress. The current plan remains in use until the changes are approved."),
		"route": version_route(plan_reference, open_version.version_number),
		"structure_route": version_route(plan_reference, open_version.version_number, "structure"),
		"action_label": (_("Correct and resubmit") if open_version.return_reason else _("Continue draft"))
		if continue_allowed
		else None,
		"return_reason": open_version.return_reason or None,
	}


def get_plan_workspace(plan_id: str, version_number: str | int | None = None) -> dict:
	"""STR-UI-02 — the plan, the selected version (the Current version by
	default; an exact version when the route names one) and its readable
	content. Never silently substitutes the latest content for a version
	the route asked for (§12.2)."""
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
		return {
			"forbidden": False,
			"not_found": False,
			"plan": _plan_dto(plan),
			"versions": [],
			"no_version": True,
			"capabilities": {"update_plan": False, "edit_identity": False, "edit_version_dates": False, "submit": False},
			"routes": {"overview": plan_route(plan.plan_id)},
		}

	active = next((v for v in versions if v.status == STATUS_ACTIVE), None)
	open_statuses = (STATUS_DRAFT, STATUS_SUBMITTED)
	open_version = next((v for v in versions if v.status in open_statuses), None)

	selected = None
	if version_number not in (None, ""):
		selected = next((v for v in versions if str(v.version_number) == str(version_number)), None)
		if not selected:
			return {"not_found": True}
	else:
		# The Current version leads; a plan with no Current version yet shows
		# its open version (first Draft / first submission).
		selected = active or open_version or versions[0]

	tree = get_strategy_tree(selected.name)
	events = _authority_from_events(selected.name, ("Approve", "Submit for approval", "Return"))

	current_authority = {"approved_by": events["Approve"]} if selected.status in (STATUS_ACTIVE, STATUS_SUPERSEDED) else None
	readiness = get_version_readiness(selected.name) if selected.status in open_statuses else None

	is_editable_draft = selected.status == STATUS_DRAFT and has_plan_version_capability(
		frappe.session.user, CAP_AUTHOR, selected.name
	)
	can_update_plan = (
		bool(active)
		and not open_version
		and has_plan_version_capability(frappe.session.user, CAP_AUTHOR, active.name)
	)
	# §12.2 — plan identity is editable only while its first version is Draft.
	identity_editable = (
		len(versions) == 1 and versions[0].status == STATUS_DRAFT and is_editable_draft and selected.name == versions[0].name
	)
	# §11.3A — a successor Draft exposes Use from / Use until.
	version_dates_editable = is_editable_draft and int(selected.version_number) > 1

	selected_doc = frappe.get_doc("Strategic Plan Version", selected.name)
	version_dtos = []
	for v in versions:
		dto = _version_dto(frappe.get_doc("Strategic Plan Version", v.name))
		dto["route"] = version_route(plan.plan_id, v.version_number)
		dto["structure_route"] = version_route(plan.plan_id, v.version_number, "structure")
		version_dtos.append(dto)

	return {
		"forbidden": False,
		"not_found": False,
		"no_version": False,
		"plan": _plan_dto(plan),
		"current_version": _version_dto(selected_doc),
		"selected_is_current": bool(active) and selected.name == active.name,
		"active_version": _version_dto(frappe.get_doc("Strategic Plan Version", active.name)) if active else None,
		"versions": version_dtos,
		"objectives": tree["objectives"],
		"structure_summary": tree["counts"],
		"current_authority": current_authority,
		"approval_details": (
			{
				**events["Approve"],
				"label": _("Approved and activated Version {0}").format(selected.version_number),
			}
			if events["Approve"]
			else None
		),
		"submission_authority": {"submitted_by": events["Submit for approval"], "returned_by": events["Return"]},
		"pending_update": _pending_update(plan.plan_id, versions, active),
		"readiness": readiness,
		"is_editable_draft": is_editable_draft,
		"is_technical_reader": is_technical(frappe.session.user),
		"capabilities": {
			"update_plan": can_update_plan,
			"edit_identity": identity_editable,
			"edit_version_dates": version_dates_editable,
			"submit": is_editable_draft,
		},
		"routes": {
			"overview": plan_route(plan.plan_id) if (not active or selected.name == active.name) and version_number in (None, "") else version_route(plan.plan_id, selected.version_number),
			"structure": version_route(plan.plan_id, selected.version_number, "structure"),
			"history": version_route(plan.plan_id, selected.version_number, "history"),
			"current": plan_route(plan.plan_id) if active else None,
			"approval": approval_route(selected.plan_version_id) if selected.status == STATUS_SUBMITTED else None,
		},
	}


EVENT_LABELS: dict[str, str] = {
	"Submit for approval": "Submitted for approval",
	"Return": "Returned for correction",
	"Approve": "Approved and activated",
	"Approve successor": "Replaced by a later version",
	"Draft saved": "Draft saved",
	"Draft structure saved": "Draft saved",
	"Successor Version Created": "Draft update created from Version {0}",
}


def _event_label(action: str | None, version_name: str) -> str:
	template = EVENT_LABELS.get(action or "")
	if not template:
		return action or ""
	if "{0}" in template:
		baseline = frappe.db.get_value("Strategic Plan Version", version_name, "based_on_plan_version_id")
		baseline_number = frappe.db.get_value("Strategic Plan Version", baseline, "version_number") if baseline else None
		return _(template).format(baseline_number or "")
	return _(template)


def _event_tone(action: str | None) -> str:
	if action in ("Approve", "Approve successor"):
		return "is-live"
	if action == "Submit for approval":
		return "is-pending"
	if action == "Return":
		return "is-attention"
	return "is-draft"


def get_plan_history(plan_id: str) -> list[dict]:
	plan_name = resolve_plan_name(plan_id)
	if not plan_name or not _can_read():
		return []
	version_names = frappe.get_all("Strategic Plan Version", filters={"plan_id": plan_name}, pluck="name")
	out: list[dict] = []
	for v in version_names:
		out.extend(get_version_history(v))
	out.sort(key=lambda r: r["at"], reverse=True)
	return out


def get_version_history(plan_version_id: str) -> list[dict]:
	"""§11.9/§12.2/§12.4 — chronological, append-only lifecycle and draft-save
	events for ONE version, newest first, with the required return reason.
	Stored actions stay verbatim in `event`; `event_label` is the readable
	form (§4.7: historical evidence is never rewritten)."""
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
				"event_label": _event_label(row.get("action"), version_name),
				"tone": _event_tone(row.get("action")),
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
	user = frappe.session.user
	if not _can_read():
		return {"forbidden": True}
	version = frappe.get_doc("Strategic Plan Version", version_name)
	plan = frappe.get_doc("Strategic Plan", version.plan_id)

	# §12.4/STR-AC-021 — a direct task route requires an Active Strategy
	# Approver assignment; a read-only business user without it — Auditor
	# included — is denied rather than shown a disabled workflow form. The
	# sole exception is KT-STD-001 §3A.6's technical reader: Administrator/
	# System Manager open the same read-only overview with every capability
	# False. The no-self-approval rule stays a per-version command block,
	# not an access rule: the submitter who also holds Approver may open the
	# task and is told another Approver must review it.
	if not is_technical(user) and not holds_approver_responsibility(user):
		return {"forbidden": True, "reason": "approver_required"}
	is_approver = has_plan_version_capability(user, CAP_APPROVE, version)
	self_blocked = (
		version.status == STATUS_SUBMITTED
		and holds_approver_responsibility(user)
		and not is_approver
		and not is_technical(user)
	)

	tree = get_strategy_tree(version.name)
	events = _authority_from_events(version.name, ("Submit for approval", "Return"))
	readiness = get_version_readiness(version.name)
	blockers = get_version_approval_blockers(version)

	active_version_row = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": plan.name, "status": STATUS_ACTIVE, "name": ["!=", version.name]},
		fields=["name", "plan_version_id", "version_number"],
		limit=1,
	)
	is_update = bool(version.based_on_plan_version_id)
	baseline_number = (
		frappe.db.get_value("Strategic Plan Version", version.based_on_plan_version_id, "version_number")
		if is_update
		else None
	)

	comparison = None
	if is_update:
		try:
			comparison = diff_strategy_versions(version.based_on_plan_version_id, version.name)
			comparison["available"] = True
		except Exception:
			# §11.8 — a failed comparison is never presented as "No changes".
			frappe.log_error(title="STRATEGY_COMPARISON_FAILED")
			comparison = {"available": False, "changes": [], "base_version_number": baseline_number}

	actions = available_actions(version.name)
	can_approve = "Approve" in actions and not blockers["blocked"]
	return {
		"forbidden": False,
		"not_found": False,
		"role": "approver" if is_approver else None,
		"is_technical_reader": is_technical(user),
		"self_approval_blocked": self_blocked,
		"review_type": _("Plan changes") if is_update else _("New plan"),
		"title": _("Review plan changes") if is_update else _("Review strategic plan"),
		"plan": _plan_dto(plan),
		"version": _version_dto(version),
		"baseline_version_number": baseline_number,
		"active_version": active_version_row[0] if active_version_row else None,
		"objectives": tree["objectives"],
		"structure_summary": tree["counts"],
		"submission_authority": {"submitted_by": events["Submit for approval"], "returned_by": events["Return"]},
		"readiness": readiness,
		"blockers": blockers,
		"comparison": comparison,
		"decision": {
			"approve_label": _("Approve changes and use plan") if is_update else _("Approve and use plan"),
			"return_label": _("Return for correction"),
			"consequence": (
				_(
					"Approval replaces the current strategy version for new planning selections. "
					"Existing approved records keep their saved strategy details."
				)
				if is_update
				else _(
					"Approval makes this plan available for new budget and procurement planning. "
					"It does not approve a budget or procurement."
				)
			),
			"can_approve": can_approve,
			"can_return": "Return" in actions,
		},
		"allowed_actions": actions,
		"expected_version": str(version.modified),
		"routes": {
			"plan": plan_route(plan.plan_id),
			"version": version_route(plan.plan_id, version.version_number),
			"overview": approval_route(version.plan_version_id),
			"structure": approval_route(version.plan_version_id, "structure"),
			"changes": approval_route(version.plan_version_id, "changes"),
			"history": approval_route(version.plan_version_id, "history"),
		},
	}


# --------------------------------------------------------------------------
# STR-UI-04 Changes — server-side comparison between baseline and submitted
# --------------------------------------------------------------------------


def _node_index(plan_version_id: str) -> dict[tuple, dict]:
	"""Nodes keyed by (node_type, ancestor-title path, title) — the structural
	identity that survives a successor clone (plan D5)."""
	rows = frappe.get_all(
		"Strategy Node",
		filters={"plan_version_id": plan_version_id},
		fields=["name", "strategy_node_id", "node_type", "parent_node_id", "title", "display_order"],
		order_by="display_order asc",
	)
	by_name = {r.name: r for r in rows}

	def path_of(r) -> tuple:
		out = []
		cur = r
		while cur and cur.parent_node_id and cur.parent_node_id in by_name:
			cur = by_name[cur.parent_node_id]
			out.append(cur.title)
		return tuple(reversed(out))

	index: dict[tuple, dict] = {}
	for r in rows:
		path = path_of(r)
		siblings = [s for s in rows if (s.parent_node_id or None) == (r.parent_node_id or None)]
		siblings.sort(key=lambda s: (s.display_order or 0, s.name))
		position = next((i for i, s in enumerate(siblings) if s.name == r.name), 0) + 1
		index[(r.node_type, path, r.title)] = {
			"name": r.name,
			"reference": r.strategy_node_id,
			"node_type": r.node_type,
			"title": r.title,
			"path": path,
			"position": position,
			"sibling_count": len(siblings),
		}
	return index


def _indicator_index(plan_version_id: str, nodes: dict[tuple, dict]) -> dict[tuple, dict]:
	node_key_by_name = {v["name"]: k for k, v in nodes.items()}
	rows = frappe.get_all(
		"Performance Indicator",
		filters={"plan_version_id": plan_version_id},
		fields=["name", "indicator_id", "measures_node_id", "indicator_name", "definition", "unit"],
	)
	out: dict[tuple, dict] = {}
	for r in rows:
		objective_key = node_key_by_name.get(r.measures_node_id)
		if not objective_key:
			continue
		out[(objective_key, r.indicator_name)] = {
			"name": r.name,
			"reference": r.indicator_id,
			"indicator_name": r.indicator_name,
			"definition": r.definition or "",
			"unit": r.unit or "",
			"objective_title": objective_key[2],
			"path": (*objective_key[1], objective_key[2]),
		}
	return out


def _target_index(indicators: dict[tuple, dict]) -> dict[tuple, dict]:
	if not indicators:
		return {}
	ind_by_name = {v["name"]: k for k, v in indicators.items()}
	rows = frappe.get_all(
		"Performance Target",
		filters={"indicator_id": ["in", list(ind_by_name.keys())]},
		fields=["name", "target_id", "indicator_id", "fiscal_year", "target_by_date", "comparison", "target_value"],
	)
	out: dict[tuple, dict] = {}
	for r in rows:
		ind_key = ind_by_name[r.indicator_id]
		period = r.fiscal_year or (str(r.target_by_date) if r.target_by_date else "")
		out[(ind_key, period)] = {
			"name": r.name,
			"reference": r.target_id,
			"indicator": indicators[ind_key],
			"period_label": target_period_label(r.fiscal_year, r.target_by_date),
			"comparison": r.comparison,
			"target_value": r.target_value,
			"unit": indicators[ind_key]["unit"],
		}
	return out


def _path_label(path) -> str:
	return " / ".join(path) if path else ""


def diff_strategy_versions(base_version_id: str | None, compare_version_id: str) -> dict:
	"""§8.3/§11.6/§11.8 — the exact submitted version against its fixed
	`based_on_plan_version_id`, calculated on the server: applicability
	dates, plan identity, structure additions/removals/order, Indicator
	definitions and units, and Target comparisons/values, each with exact
	IDs for evidence and readable paths for review. A first version has no
	baseline and is reported as such, never as an empty comparison."""
	if not _can_read():
		return {"not_found": True}
	compare_version_id = resolve_version_name(compare_version_id) or compare_version_id
	base_version_id = resolve_version_name(base_version_id) if base_version_id else None
	if not base_version_id:
		base_version_id = frappe.db.get_value("Strategic Plan Version", compare_version_id, "based_on_plan_version_id")

	compare = frappe.db.get_value(
		"Strategic Plan Version",
		compare_version_id,
		["plan_id", "version_number", "effective_from", "effective_to"],
		as_dict=True,
	)
	if not compare:
		return {"not_found": True}
	if not base_version_id:
		return {
			"first_version": True,
			"changes": [],
			"base_version_id": None,
			"base_version_number": None,
			"compare_version_id": compare_version_id,
			"message": _("This is the first version of this plan."),
		}
	base = frappe.db.get_value(
		"Strategic Plan Version",
		base_version_id,
		["plan_id", "version_number", "effective_from", "effective_to"],
		as_dict=True,
	)
	if not base:
		frappe.throw(_("The changes could not be loaded."), frappe.ValidationError, title="STRATEGY_COMPARISON_UNAVAILABLE")

	changes: list[dict] = []

	def add(kind, tag, item, previous, proposed, *, path=None, previous_id=None, proposed_id=None):
		changes.append(
			{
				"kind": kind,
				"tag": tag,
				"item": item,
				"path": _path_label(path) if path else "",
				"previous": previous,
				"proposed": proposed,
				"previous_id": previous_id,
				"proposed_id": proposed_id,
			}
		)

	# Applicability dates — always compared, never omitted (STR18-AC-012).
	if str(base.effective_from or "") != str(compare.effective_from or ""):
		add("date", _("Date"), _("Version effective from"), _date_label(base.effective_from) or "—", _date_label(compare.effective_from) or "—", previous_id=base_version_id, proposed_id=compare_version_id)
	if str(base.effective_to or "") != str(compare.effective_to or ""):
		add("date", _("Date"), _("Version effective until"), _date_label(base.effective_to) or "—", _date_label(compare.effective_to) or "—", previous_id=base_version_id, proposed_id=compare_version_id)

	# Plan identity is shared by both versions of one plan; it can only
	# differ when the plan itself changed between the two — reported so a
	# reviewer never misses it.
	base_nodes = _node_index(base_version_id)
	comp_nodes = _node_index(compare_version_id)
	for key in sorted(set(comp_nodes) - set(base_nodes), key=lambda k: (k[1], k[2])):
		n = comp_nodes[key]
		add("node", _("Structure"), f"{n['node_type']}: {n['title']}", "—", _("Added"), path=n["path"], proposed_id=n["name"])
	for key in sorted(set(base_nodes) - set(comp_nodes), key=lambda k: (k[1], k[2])):
		n = base_nodes[key]
		add("node", _("Structure"), f"{n['node_type']}: {n['title']}", _("Present"), _("Removed"), path=n["path"], previous_id=n["name"])
	for key in sorted(set(base_nodes) & set(comp_nodes), key=lambda k: (k[1], k[2])):
		b, c = base_nodes[key], comp_nodes[key]
		if b["sibling_count"] == c["sibling_count"] and b["position"] != c["position"]:
			add(
				"order",
				_("Order"),
				f"{c['node_type']}: {c['title']}",
				_("Position {0} of {1}").format(b["position"], b["sibling_count"]),
				_("Position {0} of {1}").format(c["position"], c["sibling_count"]),
				path=c["path"],
				previous_id=b["name"],
				proposed_id=c["name"],
			)

	base_ind = _indicator_index(base_version_id, base_nodes)
	comp_ind = _indicator_index(compare_version_id, comp_nodes)
	for key in sorted(set(comp_ind) - set(base_ind), key=lambda k: k[1]):
		i = comp_ind[key]
		add("indicator", _("Indicator"), _("Indicator: {0}").format(i["indicator_name"]), "—", _("Added"), path=i["path"], proposed_id=i["name"])
	for key in sorted(set(base_ind) - set(comp_ind), key=lambda k: k[1]):
		i = base_ind[key]
		add("indicator", _("Indicator"), _("Indicator: {0}").format(i["indicator_name"]), _("Present"), _("Removed"), path=i["path"], previous_id=i["name"])
	for key in sorted(set(base_ind) & set(comp_ind), key=lambda k: k[1]):
		b, c = base_ind[key], comp_ind[key]
		if (b["definition"] or "").strip() != (c["definition"] or "").strip():
			add("definition", _("Indicator"), _("How {0} is measured").format(c["indicator_name"]), b["definition"] or "—", c["definition"] or "—", path=c["path"], previous_id=b["name"], proposed_id=c["name"])
		if (b["unit"] or "").strip() != (c["unit"] or "").strip():
			add("unit", _("Indicator"), _("Unit of {0}").format(c["indicator_name"]), b["unit"] or "—", c["unit"] or "—", path=c["path"], previous_id=b["name"], proposed_id=c["name"])

	base_tgt = _target_index(base_ind)
	comp_tgt = _target_index(comp_ind)
	for key in sorted(set(comp_tgt) - set(base_tgt), key=lambda k: (k[0][1], k[1])):
		t = comp_tgt[key]
		add("target", _("Target"), _("Target for {0}").format(t["period_label"]), "—", _result_label(t["comparison"], t["target_value"], t["unit"]) + " " + _("(added)"), path=(*t["indicator"]["path"], t["indicator"]["indicator_name"]), proposed_id=t["name"])
	for key in sorted(set(base_tgt) - set(comp_tgt), key=lambda k: (k[0][1], k[1])):
		t = base_tgt[key]
		add("target", _("Target"), _("Target for {0}").format(t["period_label"]), _result_label(t["comparison"], t["target_value"], t["unit"]), _("Removed"), path=(*t["indicator"]["path"], t["indicator"]["indicator_name"]), previous_id=t["name"])
	for key in sorted(set(base_tgt) & set(comp_tgt), key=lambda k: (k[0][1], k[1])):
		b, c = base_tgt[key], comp_tgt[key]
		if b["comparison"] != c["comparison"] or frappe.utils.flt(b["target_value"]) != frappe.utils.flt(c["target_value"]):
			add("target", _("Target"), _("Target for {0}").format(c["period_label"]), _result_label(b["comparison"], b["target_value"], b["unit"]), _result_label(c["comparison"], c["target_value"], c["unit"]), path=(*c["indicator"]["path"], c["indicator"]["indicator_name"]), previous_id=b["name"], proposed_id=c["name"])

	return {
		"first_version": False,
		"changes": changes,
		"base_version_id": base_version_id,
		"base_version_number": base.version_number,
		"compare_version_id": compare_version_id,
		"heading": _("Changes from Version {0}").format(base.version_number),
		"message": (
			_("No submitted identity, effective-date or structure values differ from Version {0}.").format(base.version_number)
			if not changes
			else None
		),
	}


def list_available_fiscal_years(plan_id: str | None = None) -> list[dict]:
	"""§12.3 — Period offers only ERPNext Fiscal Years overlapping the plan
	period. `ignore_permissions` is safe here: Fiscal Year rows carry only
	date ranges, and Strategy has no write path onto the doctype."""
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
		{"name": r.name, "label": fiscal_year_label(r.name), "start": str(r.year_start_date), "end": str(r.year_end_date)}
		for r in rows
	]
