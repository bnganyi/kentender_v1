# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Planning workbench — landing shell (Phase D1).

KPIs are scoped to the **current plan** when one is selected (``plan`` arg or
default readable active plan). If there is no current plan, KPI numeric values
are zero and the plan bar prompts the user to select or create a plan.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"currency": "KES",
		"current_plan": None,
		"plans": [],
		"kpis": [],
		"queue_tabs": {},
		"show_new_plan": False,
		"show_new_package": False,
		"show_apply_template": False,
		"show_submit_plan": False,
		"show_approve_plan": False,
		"show_return_plan": False,
		"show_reject_plan": False,
		"show_lock_plan": False,
	}


def _plan_workbench_action_flags(role_key: str, cur: dict | None) -> dict[str, bool]:
	"""E2 — Plan-level workflow CTAs (Roles matrix §5.1 / §7.2)."""
	out = {
		"show_submit_plan": False,
		"show_approve_plan": False,
		"show_return_plan": False,
		"show_reject_plan": False,
		"show_lock_plan": False,
	}
	if not cur:
		return out
	st = str(cur.get("status") or "")
	if role_key in ("planner", "admin") and st in ("Draft", "Returned"):
		out["show_submit_plan"] = True
	if role_key in ("authority", "admin") and st == "Submitted":
		out["show_approve_plan"] = True
		out["show_return_plan"] = True
		out["show_reject_plan"] = True
	if role_key in ("authority", "admin") and st == "Approved":
		out["show_lock_plan"] = True
	return out


def resolve_pp_role_key(user: str | None = None) -> str | None:
	"""Map Frappe roles to workbench role_key (UI matrix §7)."""
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "Administrator" in roles or "System Manager" in roles:
		return "admin"
	if "Procurement Planner" in roles:
		return "planner"
	if "Planning Authority" in roles:
		return "authority"
	if "Procurement Officer" in roles:
		return "officer"
	if "Auditor" in roles:
		return "auditor"
	return None


def _can_read_planning() -> bool:
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return False
	try:
		return bool(frappe.has_permission("Procurement Plan", "read"))
	except Exception:
		return False


def _queue_def(
	qid: str,
	*,
	label_en: str,
	testid: str,
) -> dict:
	return {"id": qid, "label": _(label_en), "testid": testid}


# Stable data-testid slugs (UI spec §12 where named; extended for other queues).
_Q = {
	"all_packages": _queue_def(
		"all_packages",
		label_en="All packages",
		testid="pp-queue-all-packages",
	),
	"draft_packages": _queue_def(
		"draft_packages", label_en="Draft Packages", testid="pp-queue-draft-packages"
	),
	"structured_packages": _queue_def(
		"structured_packages",
		label_en="Completed Packages",
		testid="pp-queue-structured-packages",
	),
	"submitted_packages": _queue_def(
		"submitted_packages",
		label_en="Submitted Packages",
		testid="pp-queue-submitted-packages",
	),
	"high_risk_packages": _queue_def(
		"high_risk_packages",
		label_en="High-Risk Packages",
		testid="pp-queue-high-risk-packages",
	),
	"emergency_packages": _queue_def(
		"emergency_packages",
		label_en="Emergency Packages",
		testid="pp-queue-emergency-packages",
	),
	"pending_approval": _queue_def(
		"pending_approval",
		label_en="Pending Approval",
		testid="pp-queue-pending-approval",
	),
	"high_risk_escalation": _queue_def(
		"high_risk_escalation",
		label_en="High-Risk Requiring Escalation",
		testid="pp-queue-high-risk-escalation",
	),
	"method_override": _queue_def(
		"method_override",
		label_en="Method Override Cases",
		testid="pp-queue-method-override",
	),
	"ready_for_tender": _queue_def(
		"ready_for_tender",
		label_en="Ready for Tender",
		testid="pp-queue-ready-for-tender",
	),
	"approved_not_handed_off": _queue_def(
		"approved_not_handed_off",
		label_en="Approved Not Yet Handed Off",
		testid="pp-queue-approved-not-handed-off",
	),
}


def _pick_queues(role_key: str, tab: str) -> list[dict]:
	"""Which queue pills appear for (role, work tab). Mirrors matrix §7.1 at high level."""
	# Order: planner-style build queues → approval → handoff
	planner_build = [
		_Q["draft_packages"],
		_Q["structured_packages"],
		_Q["submitted_packages"],
		_Q["high_risk_packages"],
		_Q["emergency_packages"],
	]
	approver = [
		_Q["pending_approval"],
		_Q["high_risk_escalation"],
		_Q["method_override"],
	]
	handoff = [_Q["ready_for_tender"], _Q["approved_not_handed_off"]]

	if role_key == "admin":
		all_q = planner_build + approver + handoff
		if tab == "mywork":
			return planner_build + [_Q["pending_approval"]]
		if tab == "approved":
			return [_Q["submitted_packages"], _Q["high_risk_packages"], _Q["approved_not_handed_off"]]
		if tab == "ready":
			return handoff
		return all_q

	if role_key == "planner":
		if tab == "mywork":
			return planner_build
		if tab == "approved":
			return [_Q["submitted_packages"], _Q["high_risk_packages"]]
		if tab == "ready":
			return handoff
		return planner_build + handoff

	if role_key == "officer":
		# Draft/structured: Yes; approval + handoff surfaces
		if tab == "mywork":
			return planner_build[:2] + [_Q["pending_approval"], _Q["ready_for_tender"]]
		if tab == "approved":
			return [_Q["submitted_packages"], _Q["approved_not_handed_off"]]
		if tab == "ready":
			return handoff
		return planner_build + approver + handoff

	if role_key == "authority":
		if tab == "mywork":
			return approver + [_Q["high_risk_packages"]]
		if tab == "approved":
			return [_Q["submitted_packages"], _Q["high_risk_escalation"]]
		if tab == "ready":
			return handoff
		return planner_build + approver + handoff

	if role_key == "auditor":
		read_q = [
			_Q["submitted_packages"],
			_Q["high_risk_packages"],
			_Q["emergency_packages"],
			_Q["pending_approval"],
			_Q["ready_for_tender"],
		]
		if tab == "mywork":
			return read_q[:3]
		if tab == "ready":
			return handoff
		return read_q

	return planner_build


def _build_queue_tabs(role_key: str) -> dict:
	"""``all`` tab prepends **All packages** (union of all statuses) so users are not forced into Draft-only."""
	out = {}
	for tab in ("mywork", "all", "approved", "ready"):
		seen: set[str] = set()
		merged: list[dict] = []
		for q in _pick_queues(role_key, tab):
			if q["id"] in seen:
				continue
			seen.add(q["id"])
			merged.append(q)
		if tab == "all" and not any(x.get("id") == "all_packages" for x in merged):
			merged.insert(0, _Q["all_packages"])
		out[tab] = merged
	return out


def _plan_row(doc) -> dict:
	entity_label = doc.procuring_entity
	try:
		if doc.get("procuring_entity"):
			entity_label = frappe.db.get_value(
				"Procuring Entity", doc.procuring_entity, "entity_name"
			) or doc.procuring_entity
	except Exception:
		pass
	return {
		"name": doc.name,
		"plan_name": doc.plan_name,
		"plan_code": doc.plan_code,
		"fiscal_year": doc.fiscal_year,
		"procuring_entity": doc.procuring_entity,
		"procuring_entity_label": entity_label,
		"status": doc.status,
		"is_active": cint(doc.is_active),
		"currency": doc.currency or "KES",
	}


def _resolve_current_plan(plan_name: str | None) -> tuple[object | None, list[dict]]:
	"""Return (current_doc_or_none, plans_list_for_selector)."""
	filters: dict = {}
	plans_out: list[dict] = []
	try:
		plan_list = frappe.get_list(
			"Procurement Plan",
			filters=filters,
			fields=[
				"name",
				"plan_name",
				"plan_code",
				"fiscal_year",
				"procuring_entity",
				"currency",
				"status",
				"is_active",
			],
			order_by="is_active desc, modified desc",
			limit_page_length=200,
		)
	except frappe.PermissionError:
		return None, []

	for p in plan_list:
		plans_out.append(
			{
				"name": p.name,
				"label": f"{p.plan_code} — {p.plan_name}",
				"plan_code": p.plan_code,
				"status": p.status,
			}
		)

	chosen = None
	if plan_name:
		try:
			chosen = frappe.get_doc("Procurement Plan", plan_name)
		except Exception:
			chosen = None
	if chosen is None:
		for p in plan_list:
			if cint(p.get("is_active")):
				try:
					chosen = frappe.get_doc("Procurement Plan", p.name)
					break
				except Exception:
					continue
	if chosen is None and plan_list:
		try:
			chosen = frappe.get_doc("Procurement Plan", plan_list[0].name)
		except Exception:
			chosen = None

	return chosen, plans_out


def _high_risk_profile_names() -> list[str]:
	try:
		return frappe.get_all(
			"Risk Profile",
			filters={"risk_level": "High"},
			pluck="name",
			limit=500,
		) or []
	except Exception:
		return []


def _plan_submit_gate(plan_name: str | None) -> dict:
	"""Strict plan submit (governance): every active package must be Approved."""
	from kentender_procurement.procurement_planning.services.pp_governance_codes import PlanSubmit

	if not plan_name:
		return {
			"plan_submit_ready": False,
			"plan_submit_blockers": [],
			"plan_submit_blocker_codes": [],
		}
	try:
		rows = frappe.get_all(
			"Procurement Package",
			filters={"plan_id": plan_name, "is_active": 1},
			fields=["package_code", "status"],
			limit=500,
		)
	except frappe.PermissionError:
		return {
			"plan_submit_ready": False,
			"plan_submit_blockers": [_("Cannot read packages for this plan.")],
			"plan_submit_blocker_codes": [PlanSubmit.NO_ACTIVE_PACKAGES],
		}
	if not rows:
		return {
			"plan_submit_ready": False,
			"plan_submit_blockers": [_("At least one active package is required before submitting the plan.")],
			"plan_submit_blocker_codes": [PlanSubmit.NO_ACTIVE_PACKAGES],
		}
	blockers = []
	codes = []
	for r in rows:
		st = (r.status or "").strip()
		if st != "Approved":
			pc = (r.package_code or r.name or "").strip()
			blockers.append(_("{0} is {1} (must be Approved).").format(pc or _("Package"), st or _("unknown")))
			codes.append(PlanSubmit.NOT_ALL_PACKAGES_APPROVED)
	return {
		"plan_submit_ready": len(blockers) == 0,
		"plan_submit_blockers": blockers,
		"plan_submit_blocker_codes": codes,
	}


def _kpis_for_plan(plan_name: str | None, currency: str) -> list[dict]:
	"""Four KPI cards; values scoped to ``plan_id`` when plan_name set."""
	filters: dict = {}
	if plan_name:
		filters["plan_id"] = plan_name

	def cnt(extra: dict | None = None) -> int:
		f = dict(filters)
		if extra:
			f.update(extra)
		try:
			rows = frappe.get_list(
				"Procurement Package",
				filters=f,
				fields=[{"COUNT": "*", "as": "c"}],
				limit_page_length=1,
			)
			return cint((rows[0] or {}).get("c") if rows else 0)
		except frappe.PermissionError:
			return 0

	def sum_estimated() -> float:
		try:
			rows = frappe.get_list(
				"Procurement Package",
				filters=filters,
				fields=[{"SUM": "estimated_value", "as": "total"}],
				limit_page_length=1,
			)
			return flt((rows[0] or {}).get("total") if rows else 0)
		except frappe.PermissionError:
			return 0.0

	high_profiles = _high_risk_profile_names()
	high_extra: dict = {"risk_profile_id": ("in", high_profiles)} if high_profiles else {"name": ("=", "__none__")}

	return [
		{
			"id": "total_packages",
			"label": _("Total Packages"),
			"value": cnt(),
			"format": "int",
			"testid": "pp-kpi-total-packages",
		},
		{
			"id": "total_planned_value",
			"label": _("Total Planned Value"),
			"value": sum_estimated(),
			"format": "currency",
			"currency": currency,
			"testid": "pp-kpi-total-value",
		},
		{
			"id": "approved_packages",
			"label": _("Approved Packages"),
			"value": cnt({"status": "Approved"}),
			"format": "int",
			"testid": "pp-kpi-approved-packages",
		},
		{
			"id": "ready_for_tender",
			"label": _("Ready for Tender"),
			"value": cnt({"status": "Ready for Tender"}),
			"format": "int",
			"testid": "pp-kpi-ready-for-tender",
		},
		{
			"id": "high_risk_packages",
			"label": _("High-Risk Packages"),
			"value": cnt(high_extra),
			"format": "int",
			"testid": "pp-kpi-high-risk",
		},
	]


@frappe.whitelist()
def get_pp_landing_shell_data(plan: str | None = None) -> dict:
	"""Workbench shell: role, plan context, KPI strip, queue layout (D1)."""
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
			role_key="auditor",
		)

	role_key = resolve_pp_role_key()
	if not role_key or not _can_read_planning():
		return _fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to the Procurement Planning workbench."),
			role_key=role_key or "auditor",
		)

	plan_doc, plans_min = _resolve_current_plan(plan)
	cur = None
	currency = "KES"
	if plan_doc:
		cur = _plan_row(plan_doc)
		currency = (plan_doc.currency or "KES").strip() or "KES"

	show_new_plan = role_key in ("planner", "admin")
	show_new_package = False
	show_apply_template = False
	if cur and role_key in ("planner", "admin"):
		if str(cur["status"] or "") in ("Draft", "Returned"):
			show_new_package = True
			show_apply_template = True

	kpis = _kpis_for_plan(cur["name"] if cur else None, currency)

	plan_actions = _plan_workbench_action_flags(role_key, cur)
	submit_gate = _plan_submit_gate(cur["name"] if cur else None)

	return {
		"ok": True,
		"role_key": role_key,
		"currency": currency,
		"current_plan": cur,
		"plans": plans_min,
		"kpis": kpis,
		"queue_tabs": _build_queue_tabs(role_key),
		"show_new_plan": show_new_plan,
		"show_new_package": show_new_package,
		"show_apply_template": show_apply_template,
		**plan_actions,
		**submit_gate,
	}
