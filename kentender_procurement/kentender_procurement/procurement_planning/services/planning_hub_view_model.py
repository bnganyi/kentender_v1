# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP4 — Planning Hub shell view-model (v4 hub wiring)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_procurement.procurement_planning.api.landing import (
	_plan_workbench_action_flags,
	resolve_pp_role_key,
)
from kentender_procurement.procurement_planning.services.active_plan_view_model import (
	_entity_label,
	get_active_plan_view_model,
)
from kentender_procurement.procurement_planning.services.procurement_plans_view_model import (
	_hub_ledger_row,
	_plan_blockers_count,
	_plan_counts,
	_entity_ref,
	get_planning_hub_plans_page,
)

_HERO_STAT_SPECS: tuple[tuple[str, str, str, str], ...] = (
	("planned_value", "account_balance_wallet", "primary", "Planned Value"),
	("planned_demands", "fact_check", "success", "Planned Demands"),
	("active_packages", "inventory_2", "works", "Active Packages"),
	("released_to_tender", "send", "goods", "Released to Tender"),
	("blocked_items", "warning", "error", "Blocked Items"),
)


def _format_currency_compact(amount: float, currency: str = "KES") -> str:
	value = flt(amount or 0)
	cur = (currency or "KES").strip() or "KES"
	if value >= 1_000_000_000:
		text = f"{value / 1_000_000_000:.1f}".rstrip("0").rstrip(".")
		return f"{cur} {text}B"
	if value >= 1_000_000:
		text = f"{value / 1_000_000:.1f}".rstrip("0").rstrip(".")
		return f"{cur} {text}M"
	if value >= 1_000:
		text = f"{value / 1_000:.1f}".rstrip("0").rstrip(".")
		return f"{cur} {text}K"
	if value <= 0:
		return f"{cur} 0"
	return f"{cur} {value:,.0f}"


def _format_currency_full(amount: float, currency: str = "KES") -> str:
	value = flt(amount or 0)
	cur = (currency or "KES").strip() or "KES"
	return f"{cur} {value:,.0f}"


def _hero_stats_for_plan(plan_code: str, *, actor: str, currency: str) -> list[dict[str, Any]]:
	code = (plan_code or "").strip()
	if not code:
		zeros = [
			{
				"id": spec[0],
				"icon": spec[1],
				"tone": spec[2],
				"label": spec[3],
				"value": "0" if spec[0] != "planned_value" else _format_currency_compact(0, currency),
				"raw_value": 0,
				"format": "currency_compact" if spec[0] == "planned_value" else "int",
				"testid": f"kt-pph-stat-{spec[0].replace('_', '-')}",
			}
			for spec in _HERO_STAT_SPECS
		]
		return zeros

	demands, packages, released = _plan_counts(code)
	active_packages = max(packages - released, 0)
	blocked = _plan_blockers_count(code, actor=actor)
	planned_value = flt(frappe.db.get_value("Procurement Plan", code, "total_planned_value") or 0)
	if planned_value <= 0 and frappe.db.exists("DocType", "Procurement Package"):
		rows = frappe.get_all(
			"Procurement Package",
			filters={"plan_id": code, "is_active": 1},
			fields=[{"SUM": "estimated_value", "as": "total"}],
			limit_page_length=1,
		)
		planned_value = flt((rows[0] or {}).get("total") if rows else 0)

	raw_map = {
		"planned_value": planned_value,
		"planned_demands": demands,
		"active_packages": active_packages,
		"released_to_tender": released,
		"blocked_items": blocked,
	}
	display_map = {
		"planned_value": _format_currency_compact(planned_value, currency),
		"planned_demands": f"{demands:,}",
		"active_packages": str(active_packages),
		"released_to_tender": str(released),
		"blocked_items": str(blocked),
	}
	out: list[dict[str, Any]] = []
	for stat_id, icon, tone, label in _HERO_STAT_SPECS:
		out.append(
			{
				"id": stat_id,
				"icon": icon,
				"tone": tone,
				"label": label,
				"value": display_map[stat_id],
				"raw_value": raw_map[stat_id],
				"format": "currency_compact" if stat_id == "planned_value" else "int",
				"testid": f"kt-pph-stat-{stat_id.replace('_', '-')}",
				"click_action": "open_blocked_queue" if stat_id == "blocked_items" else None,
			}
		)
	return out


def _enrich_active_plan(active: dict[str, Any], *, actor: str) -> dict[str, Any]:
	out = dict(active or {})
	if not out.get("has_active_plan"):
		return out
	plan_code = (out.get("plan_code") or "").strip()
	if not plan_code or not frappe.db.exists("Procurement Plan", plan_code):
		return out
	doc = frappe.get_doc("Procurement Plan", plan_code)
	entity_code = (doc.procuring_entity or "").strip()
	currency = (doc.currency or "KES").strip() or "KES"
	out.update(
		{
			"plan_id": plan_code,
			"code": plan_code,
			"name": (doc.plan_name or plan_code).strip(),
			"description": (doc.plan_description or "").strip(),
			"currency": currency,
			"total_planned_value": flt(doc.total_planned_value or 0),
			"entity": _entity_ref(entity_code),
			"entity_name": _entity_label(entity_code),
		}
	)
	return out


def get_planning_hub_shell_data(
	*,
	actor: str | None = None,
	procuring_entity: str | None = None,
	fiscal_year: str | int | None = None,
) -> dict[str, Any]:
	"""Return Planning Hub v4 shell envelope for desk page wiring."""
	user = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(user) or "auditor"

	active = get_active_plan_view_model(
		actor=user,
		procuring_entity=procuring_entity,
		fiscal_year=fiscal_year,
	)
	active = _enrich_active_plan(active, actor=user)

	plan_code = (active.get("plan_code") or active.get("code") or "").strip() if active.get("has_active_plan") else ""
	currency = (active.get("currency") or "KES").strip() if active.get("has_active_plan") else "KES"
	if not currency:
		currency = "KES"

	cur_status = {"status": "Active"} if active.get("has_active_plan") else None
	if plan_code:
		cur_status = {"status": frappe.db.get_value("Procurement Plan", plan_code, "status") or "Active"}
	flags = _plan_workbench_action_flags(role_key, cur_status)

	ledger = get_planning_hub_plans_page(actor=user, start=0, limit=20)

	return {
		"ok": True,
		"role_key": role_key,
		"currency": currency,
		"active_plan": active,
		"hero_stats": _hero_stats_for_plan(plan_code, actor=user, currency=currency),
		"header_actions": {
			"show_request_revision": False,
			"show_close_plan": bool(active.get("has_active_plan") and flags.get("show_close_plan")),
			"show_open_workbench": bool(active.get("has_active_plan")),
			"show_view_plan": bool(active.get("has_active_plan")),
		},
		"cta_actions": {
			"show_create_plan": role_key in ("planner", "admin"),
			"show_launch_wizard": role_key in ("planner", "admin"),
		},
		"ledger_preview": {
			"total": ledger.get("total") or 0,
			"start": ledger.get("start") or 0,
			"limit": ledger.get("limit") or 20,
			"rows": ledger.get("rows") or [],
		},
	}
