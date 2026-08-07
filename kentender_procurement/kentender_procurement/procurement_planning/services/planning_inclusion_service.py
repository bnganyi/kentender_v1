# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 — Planning Inclusion via Procurement Handoff Card (DEV-002 Option A)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import DemandInclusion
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope

ALLOWED_DEMAND_STATUSES = frozenset(("Approved", "Planning Ready"))
_PLANNING_INCLUSION_TITLE = "Planning Inclusion Record"
_INCLUSION_BUSINESS_STATUS = "Included"
_INCLUSION_PACKAGED_STATUS = "Packaged"
_HANDOFF_STATUS_INCLUDED = "Handed Off"
_TERMINAL_INCLUSION_STATUSES = frozenset(("Cancelled", "Superseded"))

_DEMAND_FIELDS = (
	"name",
	"demand_id",
	"status",
	"budget_line",
)

_DEMAND_INCLUSION_FIELDS = (
	"name",
	"demand_id",
	"status",
	"title",
	"requisition_type",
	"total_amount",
	"budget_line",
)

_PLAN_FIELDS = ("name", "plan_code", "status", "currency")


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _check(check_id: str, label: str, ok: bool) -> dict[str, Any]:
	return {"id": check_id, "label": label, "ok": bool(ok)}


def _normalize_item_codes(demand_item_codes: list[str] | None) -> list[str]:
	return sorted({c.strip() for c in (demand_item_codes or []) if (c or "").strip()})


def _resolve_demand_row(demand_code: str) -> dict[str, Any] | None:
	demand_code = (demand_code or "").strip()
	if not demand_code or not frappe.db.exists("DocType", "Demand"):
		return None
	row = frappe.db.get_value("Demand", {"demand_id": demand_code}, _DEMAND_FIELDS, as_dict=True)
	if not row:
		row = frappe.db.get_value("Demand", demand_code, _DEMAND_FIELDS, as_dict=True)
	return row


def _load_demand_for_inclusion(demand_code: str) -> dict[str, Any] | None:
	demand_code = (demand_code or "").strip()
	if not demand_code or not frappe.db.exists("DocType", "Demand"):
		return None
	row = frappe.db.get_value(
		"Demand", {"demand_id": demand_code}, _DEMAND_INCLUSION_FIELDS, as_dict=True
	)
	if not row:
		row = frappe.db.get_value("Demand", demand_code, _DEMAND_INCLUSION_FIELDS, as_dict=True)
	return row


def _resolve_plan_row(plan_code: str) -> dict[str, Any] | None:
	plan_code = (plan_code or "").strip()
	if not plan_code:
		return None
	if not frappe.db.exists("Procurement Plan", plan_code):
		return None
	return frappe.db.get_value("Procurement Plan", plan_code, _PLAN_FIELDS, as_dict=True)


def _budget_line_business_code(budget_line_name: str | None) -> str:
	bl = (budget_line_name or "").strip()
	if not bl:
		return ""
	# Budget Line MVP-1 uses generated_reference (legacy budget_line_code removed).
	code = frappe.db.get_value("Budget Line", bl, "generated_reference")
	return (code or bl).strip()


def _demand_budget_ok(demand_row: dict[str, Any]) -> bool:
	budget_line = (demand_row.get("budget_line") or "").strip()
	if not budget_line or not frappe.db.exists("Budget Line", budget_line):
		return False
	bl_active = frappe.db.get_value("Budget Line", budget_line, "is_active")
	if bl_active is not None and int(bl_active) == 0:
		return False
	return True


def _active_package_line_for_demand(demand_name: str) -> str | None:
	if not demand_name:
		return None
	rows = frappe.db.sql(
		"""select name from `tabProcurement Package Line`
		where demand_id = %s and ifnull(is_active, 1) = 1 limit 1""",
		demand_name,
	)
	return rows[0][0] if rows else None


def _active_package_line_for_item_code(demand_item_code: str) -> str | None:
	code = (demand_item_code or "").strip()
	if not code:
		return None
	return frappe.db.get_value(
		"Procurement Package Line",
		{"demand_item_code": code, "is_active": 1},
		"name",
	)


def _technical_refs_item_codes(raw: Any) -> list[str]:
	parsed = frappe.parse_json(raw) if isinstance(raw, str) else raw
	if not isinstance(parsed, dict):
		return []
	codes = parsed.get("demand_item_codes")
	if isinstance(codes, list):
		return _normalize_item_codes([str(c) for c in codes])
	single = parsed.get("demand_item_code")
	if single:
		return _normalize_item_codes([str(single)])
	return []


def _inclusion_is_unpackaged(handoff_code: str) -> dict[str, Any] | None:
	"""Return the inclusion dict if `handoff_code` has no package yet, else None."""
	code = (handoff_code or "").strip()
	if not code:
		return None
	inclusion = get_planning_inclusion(code)
	if not inclusion:
		return None
	if (inclusion.get("created_package_code") or "").strip():
		return None
	if frappe.db.get_value(
		"Procurement Package",
		{"planning_inclusion_code": code, "is_active": 1},
		"name",
	):
		return None
	return inclusion


def demand_has_unpackaged_planning_inclusion(demand_code: str) -> bool:
	"""True when demand has active planning inclusion not yet linked to a package."""
	demand_code = (demand_code or "").strip()
	if not demand_code:
		return False
	rows = frappe.get_all(
		"Procurement Handoff Card",
		filters={
			"handoff_title": _PLANNING_INCLUSION_TITLE,
			"source_object_code": demand_code,
			"status": ["not in", list(_TERMINAL_INCLUSION_STATUSES)],
		},
		fields=["handoff_code"],
		order_by="creation desc",
		limit=20,
	)
	for row in rows:
		if _inclusion_is_unpackaged(row.get("handoff_code") or ""):
			return True
	return False


def _inclusion_department_label(demand_code: str) -> str:
	demand_code = (demand_code or "").strip()
	if not demand_code:
		return ""
	dept_id = frappe.db.get_value("Demand", {"demand_id": demand_code}, "requesting_department")
	if not dept_id:
		dept_id = frappe.db.get_value("Demand", demand_code, "requesting_department")
	if not dept_id:
		return ""
	return (frappe.db.get_value("Procuring Department", dept_id, "department_name") or "").strip()


def list_unpackaged_planning_inclusions(plan_code: str) -> list[dict[str, Any]]:
	"""Demands "Added to Active Plan" under `plan_code` with no package yet.

	Fills the UX gap where a demand is deliberately excluded from Needs
	Planning the moment it gains an active Planning Inclusion (see
	`demand_has_unpackaged_planning_inclusion` / Operational Flow doc §9.4 —
	"must no longer appear as if it still needs planning") but has no
	`Procurement Package` yet either, so it would otherwise be unfindable on
	the Workbench. Powers placeholder rows in the "In Creation" queue.
	"""
	plan_code = (plan_code or "").strip()
	if not plan_code:
		return []
	rows = frappe.get_all(
		"Procurement Handoff Card",
		filters={
			"handoff_title": _PLANNING_INCLUSION_TITLE,
			"target_object_code": plan_code,
			"status": ["not in", list(_TERMINAL_INCLUSION_STATUSES)],
		},
		fields=["handoff_code", "creation"],
		order_by="creation desc",
		limit=500,
	)
	out: list[dict[str, Any]] = []
	for row in rows:
		inclusion = _inclusion_is_unpackaged(row.get("handoff_code") or "")
		if not inclusion:
			continue
		demand_code = (inclusion.get("demand_code") or "").strip()
		passed_forward = inclusion.get("passed_forward_summary") or {}
		out.append(
			{
				"inclusion_code": inclusion.get("handoff_code") or "",
				"demand_code": demand_code,
				"title": (passed_forward.get("package_candidate") or demand_code or "").strip(),
				"category": (passed_forward.get("category") or "").strip(),
				"estimated_value": flt(passed_forward.get("estimated_value") or 0),
				"currency": (passed_forward.get("currency") or "KES").strip() or "KES",
				"department_label": _inclusion_department_label(demand_code),
				"created_on": str(row.get("creation") or ""),
			}
		)
	return out


def _find_existing_inclusion(
	demand_code: str,
	plan_code: str,
	demand_item_codes: list[str] | None,
) -> str | None:
	demand_code = (demand_code or "").strip()
	plan_code = (plan_code or "").strip()
	if not demand_code or not plan_code:
		return None
	item_codes = _normalize_item_codes(demand_item_codes)
	rows = frappe.get_all(
		"Procurement Handoff Card",
		filters={
			"handoff_title": _PLANNING_INCLUSION_TITLE,
			"source_object_code": demand_code,
			"target_object_code": plan_code,
			"status": ["not in", list(_TERMINAL_INCLUSION_STATUSES)],
		},
		fields=["handoff_code", "technical_refs_json"],
		order_by="creation desc",
		limit=20,
	)
	for row in rows:
		if not item_codes:
			return row.get("handoff_code")
		if _technical_refs_item_codes(row.get("technical_refs_json")) == item_codes:
			return row.get("handoff_code")
	return None


def _assert_can_include_or_throw(
	demand_code: str,
	demand_item_codes: list[str],
	plan_code: str,
	actor: str,
) -> None:
	guard = can_include_demand_in_plan(demand_code, demand_item_codes, plan_code, actor)
	if guard.get("allowed"):
		return
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or _("Demand cannot be included in this procurement plan."),
		title=first.get("code") or DemandInclusion.DEMAND_NOT_APPROVED,
		exc=frappe.ValidationError,
	)


def can_include_demand_in_plan(
	demand_code: str,
	demand_item_codes: list[str],
	plan_code: str,
	actor: str,
) -> dict[str, Any]:
	"""Read-only guard — whether demand/items may be included in a procurement plan (PP2-VAL-001..003)."""
	# actor reserved for role/entity scope in P2-014 / P2-015
	blockers: list[dict[str, str]] = []
	checks: list[dict[str, Any]] = []

	plan_row = _resolve_plan_row(plan_code)
	plan_active = bool(plan_row and (plan_row.get("status") or "").strip() == PLAN_ACTIVE)
	checks.append(_check("plan_active", _("Procurement plan is active"), plan_active))
	if not plan_row or not plan_active:
		blockers.append(
			_blocker(
				DemandInclusion.PLAN_INACTIVE,
				_("The selected procurement plan is not active."),
			)
		)

	demand_row = _resolve_demand_row(demand_code)
	demand_status = (demand_row.get("status") or "").strip() if demand_row else ""
	demand_approved = bool(demand_row and demand_status in ALLOWED_DEMAND_STATUSES)
	checks.append(_check("demand_approved", _("Demand is approved"), demand_approved))
	if not demand_row:
		blockers.append(
			_blocker(
				DemandInclusion.DEMAND_NOT_APPROVED,
				_("This demand is not approved and cannot be planned."),
			)
		)
	elif not demand_approved:
		blockers.append(
			_blocker(
				DemandInclusion.DEMAND_NOT_APPROVED,
				_("This demand is not approved and cannot be planned."),
			)
		)

	budget_ok = bool(demand_row and _demand_budget_ok(demand_row))
	checks.append(_check("budget_linked", _("Budget line is linked"), budget_ok))
	if demand_row and not budget_ok:
		blockers.append(
			_blocker(
				DemandInclusion.BUDGET_MISSING,
				_("This demand has no approved budget line linked."),
			)
		)

	packaging_ok = True
	if demand_row:
		item_codes = _normalize_item_codes(demand_item_codes)
		if item_codes:
			for item_code in item_codes:
				if _active_package_line_for_item_code(item_code):
					packaging_ok = False
					break
		elif _active_package_line_for_demand(demand_row.get("name") or ""):
			packaging_ok = False
	checks.append(
		_check("not_already_packaged", _("Demand item not already packaged"), packaging_ok)
	)
	if demand_row and not packaging_ok:
		blockers.append(
			_blocker(
				DemandInclusion.DEMAND_ITEM_ALREADY_PACKAGED,
				_("This demand item is already included in an active package."),
			)
		)

	return {
		"allowed": not blockers,
		"blockers": blockers,
		"checks": checks,
	}


def _plan_evidence_link(plan_code: str) -> dict[str, str]:
	return {
		"label": "Procurement Plan",
		"object_type": "Procurement Plan",
		"object_code": plan_code,
		"module": "Procurement Planning",
		"route": f"/desk#Form/Procurement Plan/{plan_code}",
		"visibility": "Internal",
	}


def _inclusion_code_prefix(plan_code: str) -> str:
	parts = [p for p in (plan_code or "").strip().upper().split("-") if p]
	if len(parts) >= 3 and parts[0] == "PP":
		return f"PLANINCL-{parts[1]}-{parts[2]}-"
	entity = parts[1] if len(parts) > 1 else "GEN"
	year = parts[2] if len(parts) > 2 else "0000"
	return f"PLANINCL-{entity}-{year}-"


def _next_inclusion_seq(plan_code: str) -> str:
	"""Next free 3-digit sequence for `plan_code`'s PLANINCL prefix.

	A plan's active procurement inclusion is not limited to a single demand
	(the Package Creation Wizard's multi-demand packaging, PW2/PW6, needs
	several concurrent Planning Inclusions per plan) — a fixed "001" here
	would silently upsert/overwrite an earlier demand's handoff card
	(`create_or_update_handoff_card` is a by-code upsert), which corrupts
	traceability. Scans existing codes for the prefix and returns max+1;
	starts at "001" when the plan has none yet (backward compatible with
	every pre-existing single-inclusion-per-plan test/seed).
	"""
	prefix = _inclusion_code_prefix(plan_code)
	existing_codes = frappe.get_all(
		"Procurement Handoff Card",
		filters={"handoff_code": ["like", f"{prefix}%"]},
		pluck="handoff_code",
	)
	max_seq = 0
	for code in existing_codes:
		suffix = (code or "")[len(prefix) :]
		if suffix.isdigit():
			max_seq = max(max_seq, int(suffix))
	return f"{max_seq + 1:03d}"


def _inclusion_handoff_code(plan_code: str, seq: str | None = None) -> str:
	"""Derive PLANINCL code from plan code (PP-MOH-2026 → PLANINCL-MOH-2026-NNN)."""
	resolved_seq = (seq or "").strip() or _next_inclusion_seq(plan_code)
	return f"{_inclusion_code_prefix(plan_code)}{resolved_seq}"


def _resolve_journey_code(demand_code: str) -> str | None:
	demand_code = (demand_code or "").strip()
	if not demand_code:
		return None
	jc = frappe.db.get_value(
		"Procurement Journey",
		{"demand_ref": demand_code},
		"journey_code",
		order_by="modified desc",
	)
	if jc:
		return jc
	row = _resolve_demand_row(demand_code)
	if not row:
		return None
	return frappe.db.get_value(
		"Procurement Journey",
		{"demand_ref": row.get("name")},
		"journey_code",
		order_by="modified desc",
	)


def get_planning_inclusion(handoff_code: str) -> dict[str, Any] | None:
	"""Return handoff card row as inclusion dict if it exists."""
	if not handoff_code or not frappe.db.exists("Procurement Handoff Card", handoff_code):
		return None
	doc = frappe.get_doc("Procurement Handoff Card", handoff_code)
	locked = frappe.parse_json(doc.locked_summary or "{}")
	if not isinstance(locked, dict):
		locked = {}
	technical = frappe.parse_json(doc.technical_refs_json or "{}")
	if not isinstance(technical, dict):
		technical = {}
	item_codes = _technical_refs_item_codes(technical)
	budget_line_code = (
		locked.get("budget_line")
		or technical.get("budget_line_code")
		or ""
	)
	created_package_code = (locked.get("created_package_code") or "").strip()
	business_status = (
		_INCLUSION_PACKAGED_STATUS if created_package_code else _INCLUSION_BUSINESS_STATUS
	)
	return {
		"inclusion_code": doc.handoff_code,
		"handoff_code": doc.handoff_code,
		"status": business_status,
		"created_package_code": created_package_code,
		"handoff_status": doc.status,
		"journey_code": doc.journey_code,
		"demand_code": doc.source_object_code or locked.get("included_demand"),
		"procurement_plan_code": doc.target_object_code or locked.get("procurement_plan"),
		"budget_line_code": budget_line_code,
		"demand_item_codes": item_codes,
		"source_object_code": doc.source_object_code,
		"target_object_code": doc.target_object_code,
		"locked_summary": locked,
		"passed_forward_summary": frappe.parse_json(doc.passed_forward_summary or "{}"),
	}


def _format_include_response(
	*,
	action: str,
	handoff_code: str,
	demand_code: str,
	plan_code: str,
	budget_line_code: str,
	demand_item_codes: list[str],
) -> dict[str, Any]:
	inclusion = get_planning_inclusion(handoff_code)
	return {
		"ok": True,
		"action": action,
		"inclusion_code": handoff_code,
		"demand_code": demand_code,
		"procurement_plan_code": plan_code,
		"budget_line_code": budget_line_code,
		"demand_item_codes": demand_item_codes,
		"status": _INCLUSION_BUSINESS_STATUS,
		"inclusion": inclusion,
	}


def _create_planning_inclusion_handoff(
	*,
	demand_code: str,
	plan_code: str,
	demand_item_codes: list[str] | None = None,
	budget_line_code: str | None = None,
	inclusion_code: str | None = None,
	journey_code: str | None = None,
	actor: str | None = None,
	is_master_seed: bool = False,
	skip_guard: bool = False,
) -> dict[str, Any]:
	"""Create Planning Inclusion handoff card; caller handles idempotency lookup."""
	demand_code = (demand_code or "").strip()
	plan_code = (plan_code or "").strip()
	item_codes = _normalize_item_codes(demand_item_codes)
	actor_user = (actor or frappe.session.user or "").strip() or frappe.session.user

	if not skip_guard:
		_assert_can_include_or_throw(demand_code, item_codes, plan_code, actor_user)

	if not frappe.db.exists("Procurement Plan", plan_code):
		frappe.throw(_("Procurement Plan not found."), title=_("Invalid plan"))
	plan = frappe.get_doc("Procurement Plan", plan_code)

	demand = _load_demand_for_inclusion(demand_code)
	if not demand:
		frappe.throw(_("Demand not found."), title=_("Invalid demand"))
	if skip_guard and (demand.status or "").strip() not in ALLOWED_DEMAND_STATUSES:
		frappe.throw(_("Demand must be approved before planning inclusion."), title=_("Demand not approved"))

	handoff_code = (inclusion_code or _inclusion_handoff_code(plan_code)).strip()
	journey_code = (journey_code or _resolve_journey_code(demand_code) or "").strip()
	if not journey_code:
		frappe.throw(_("Journey code could not be resolved for demand."), title=_("Missing journey"))

	bl_code = (budget_line_code or "").strip()
	if not bl_code:
		bl_code = _budget_line_business_code(demand.budget_line)

	now = now_datetime()
	payload = {
		"handoff_code": handoff_code,
		"handoff_title": _PLANNING_INCLUSION_TITLE,
		"journey_code": journey_code,
		"source_module": "Procurement Planning",
		"target_module": "Procurement Planning",
		"source_object_type": "Demand",
		"source_object_code": demand.demand_id or demand_code,
		"target_object_type": "Procurement Plan",
		"target_object_code": plan_code,
		"status": _HANDOFF_STATUS_INCLUDED,
		"generated_by": actor_user,
		"generated_at": str(now),
		"next_action": "Prepare a procurement package for the approved demand.",
		"locked_summary": {
			"procurement_plan": plan_code,
			"included_demand": demand.demand_id or demand_code,
			"budget_line": bl_code,
			"demand_item_codes": item_codes,
		},
		"passed_forward_summary": {
			"package_candidate": demand.title or demand_code,
			"category": demand.requisition_type or "",
			"estimated_value": flt(demand.total_amount),
			"currency": (plan.currency or "KES").strip(),
		},
		"evidence_links": [_plan_evidence_link(plan_code)],
		"technical_refs": {
			"inclusion_code": handoff_code,
			"demand_item_codes": item_codes,
			"budget_line_code": bl_code,
		},
		"is_master_seed": is_master_seed,
	}
	result = create_or_update_handoff_card(payload)
	record_planning_audit_event(
		event_type="Demand Included in Plan",
		object_type="Planning Inclusion Record",
		object_code=handoff_code,
		to_state=_INCLUSION_BUSINESS_STATUS,
		evidence_ref=handoff_code,
		journey_code=journey_code,
		actor=actor_user,
		is_master_seed=is_master_seed,
	)
	return _format_include_response(
		action=result.get("action", "created"),
		handoff_code=handoff_code,
		demand_code=demand.demand_id or demand_code,
		plan_code=plan_code,
		budget_line_code=bl_code,
		demand_item_codes=item_codes,
	)


def include_demand_in_procurement_plan(
	demand_code: str,
	demand_item_codes: list[str],
	procurement_plan_code: str,
	actor: str,
) -> dict[str, Any]:
	"""Create or return Planning Inclusion for approved demand in an active procurement plan."""
	demand_code = (demand_code or "").strip()
	procurement_plan_code = (procurement_plan_code or "").strip()
	item_codes = _normalize_item_codes(demand_item_codes)
	actor_user = (actor or frappe.session.user or "").strip() or frappe.session.user

	from kentender_procurement.procurement_lifecycle.demand_journey_bootstrap import (
		ensure_procurement_journey_for_demand_code,
	)

	ensure_procurement_journey_for_demand_code(demand_code)
	_assert_can_include_or_throw(demand_code, item_codes, procurement_plan_code, actor_user)
	pp_policy.assert_may_include_demand_in_plan()
	pp_scope.assert_may_act_on_planning_inclusion(demand_code, procurement_plan_code)

	existing_code = _find_existing_inclusion(demand_code, procurement_plan_code, item_codes)
	if existing_code:
		demand = _load_demand_for_inclusion(demand_code) or {}
		bl_code = _budget_line_business_code(demand.get("budget_line"))
		return _format_include_response(
			action="existing",
			handoff_code=existing_code,
			demand_code=demand.get("demand_id") or demand_code,
			plan_code=procurement_plan_code,
			budget_line_code=bl_code,
			demand_item_codes=item_codes,
		)

	return _create_planning_inclusion_handoff(
		demand_code=demand_code,
		plan_code=procurement_plan_code,
		demand_item_codes=item_codes,
		actor=actor_user,
		skip_guard=True,
	)


def create_planning_inclusion(
	*,
	demand_code: str,
	plan_code: str,
	budget_line_code: str | None = None,
	inclusion_code: str | None = None,
	journey_code: str | None = None,
	actor: str | None = None,
	demand_item_codes: list[str] | None = None,
	is_master_seed: bool = False,
) -> dict[str, Any]:
	"""Create or return Planning Inclusion handoff card (seed/back-compat entrypoint)."""
	demand_code = (demand_code or "").strip()
	plan_code = (plan_code or "").strip()
	item_codes = _normalize_item_codes(demand_item_codes)

	if not is_master_seed:
		return include_demand_in_procurement_plan(
			demand_code,
			item_codes,
			plan_code,
			(actor or frappe.session.user or "").strip(),
		)

	existing_code = _find_existing_inclusion(demand_code, plan_code, item_codes)
	if existing_code:
		demand = _load_demand_for_inclusion(demand_code) or {}
		bl_code = (budget_line_code or "").strip() or _budget_line_business_code(demand.get("budget_line"))
		return _format_include_response(
			action="existing",
			handoff_code=existing_code,
			demand_code=demand.get("demand_id") or demand_code,
			plan_code=plan_code,
			budget_line_code=bl_code,
			demand_item_codes=item_codes,
		)

	if inclusion_code and frappe.db.exists("Procurement Handoff Card", inclusion_code):
		demand = _load_demand_for_inclusion(demand_code) or {}
		bl_code = (budget_line_code or "").strip() or _budget_line_business_code(demand.get("budget_line"))
		return _format_include_response(
			action="existing",
			handoff_code=inclusion_code,
			demand_code=demand.get("demand_id") or demand_code,
			plan_code=plan_code,
			budget_line_code=bl_code,
			demand_item_codes=item_codes,
		)

	return _create_planning_inclusion_handoff(
		demand_code=demand_code,
		plan_code=plan_code,
		demand_item_codes=item_codes,
		budget_line_code=budget_line_code,
		inclusion_code=inclusion_code,
		journey_code=journey_code,
		actor=actor,
		is_master_seed=True,
		skip_guard=True,
	)
