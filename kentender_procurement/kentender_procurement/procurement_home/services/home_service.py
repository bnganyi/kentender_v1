# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — orchestrates context + section projections."""

from __future__ import annotations

from typing import Any, Callable

import frappe
from frappe import _

from kentender_procurement.procurement_home.services.home_actions import get_home_actions
from kentender_procurement.procurement_home.services.home_context import resolve_home_context
from kentender_procurement.procurement_home.services.home_deadlines import get_home_deadlines
from kentender_procurement.procurement_home.services.home_pipeline import get_home_pipeline
from kentender_procurement.procurement_home.services.home_portfolio import get_home_portfolio


def _safe_section(name: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	try:
		result = fn()
		if not isinstance(result, dict):
			return {
				"ok": False,
				"error": True,
				"message": _("This section is temporarily unavailable."),
			}
		result.setdefault("ok", True)
		return result
	except frappe.PermissionError:
		raise
	except Exception as exc:
		frappe.log_error(title=f"Procurement Home section {name}", message=str(exc))
		return {
			"ok": False,
			"error": True,
			"message": _("This section is temporarily unavailable."),
		}


def build_procurement_home(
	procuring_entity: str | None = None,
	fiscal_year: int | str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Full Home payload with per-section soft-fail (except unauthorized context)."""
	user = (user or frappe.session.user or "").strip()
	if not user or user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	context = resolve_home_context(procuring_entity, fiscal_year, user=user)
	pe_id = context["procuring_entity"]["id"]
	fy = int(context["fiscal_year"])

	actions = _safe_section("actions", lambda: get_home_actions(pe_id, fy, user=user))
	pipeline = _safe_section("pipeline", lambda: get_home_pipeline(pe_id, fy, user=user))
	deadlines = _safe_section("deadlines", lambda: get_home_deadlines(pe_id, fy, user=user))
	portfolio = _safe_section("portfolio", lambda: get_home_portfolio(pe_id, fy, user=user))

	visibility = {
		"actions": True,
		"pipeline": True,
		"deadlines": True,
		"portfolio": bool(portfolio.get("visible", True)) if portfolio.get("ok") else False,
	}
	if portfolio.get("visible") is False:
		visibility["portfolio"] = False

	# Bid confidentiality guard — strip any accidental bidder keys
	forbidden = ("bidder", "bid_count", "submission_count", "bid_price", "sealed")
	for section in (actions, pipeline, deadlines, portfolio):
		blob = frappe.as_json(section).lower()
		for key in forbidden:
			if f'"{key}"' in blob and key in ("bid_count", "submission_count"):
				# hard strip if present at top level
				section.pop(key, None)

	return {
		"ok": True,
		"context": context,
		"visibility": visibility,
		"actions": actions,
		"pipeline": pipeline,
		"deadlines": deadlines,
		"portfolio": portfolio,
	}
