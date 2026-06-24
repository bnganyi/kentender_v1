# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-005/P5-006 — Create Package modal business context drawer."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, fmt_money

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.services.approved_demand_drawer import (
	get_approved_demand_planning_drawer,
)
from kentender_procurement.procurement_planning.services.package_creation_service import (
	_find_existing_package_for_inclusion,
	_map_procurement_category,
	_resolve_template_for_demand,
	can_create_package_from_inclusion,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	_find_existing_inclusion,
)
from kentender_procurement.procurement_planning.services.planning_references import (
	resolve_demand_name,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageFromInclusion,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _value_label(amount: Any, currency: str | None = None) -> str:
	curr = (currency or "KES").strip() or "KES"
	return f"{fmt_money(flt(amount), currency=curr)} {curr}".strip()


def _funding_label(budget_line: dict[str, Any] | None) -> str:
	row = budget_line or {}
	if str(row.get("code") or row.get("id") or "").strip():
		return _("Budget linked")
	return _("Budget not linked")


def _budget_linked(budget_line: dict[str, Any] | None) -> bool:
	row = budget_line or {}
	return bool(str(row.get("code") or row.get("id") or "").strip())


def _resolve_inclusion_code(
	*,
	demand_code: str,
	plan_code: str | None,
	inclusion_code: str | None,
	demand_item_codes: list[str] | None,
) -> str:
	explicit = (inclusion_code or "").strip()
	if explicit:
		return explicit
	demand = (demand_code or "").strip()
	plan = (plan_code or "").strip()
	if not demand or not plan:
		return ""
	return (_find_existing_inclusion(demand, plan, demand_item_codes) or "").strip()


def _package_display_name(package_code: str) -> str:
	code = (package_code or "").strip()
	if not code:
		return ""
	row = frappe.db.get_value(
		"Procurement Package",
		{"package_code": code},
		("package_name", "package_code"),
		as_dict=True,
	)
	if not row:
		row = frappe.db.get_value(
			"Procurement Package",
			code,
			("package_name", "package_code"),
			as_dict=True,
		)
	if not row:
		return ""
	name = str(row.get("package_name") or "").strip()
	return name or code


def _evaluate_create_package_validation(
	*,
	resolved_inclusion: str,
	target_plan: dict[str, Any],
	budget_line: dict[str, Any],
	guard: dict[str, Any],
) -> dict[str, Any] | None:
	if not resolved_inclusion:
		return {
			"code": PackageFromInclusion.INCLUSION_REQUIRED,
			"message": _("Include this demand in the active procurement plan before creating a package."),
		}

	plan_code = str(target_plan.get("code") or "").strip()
	plan_status = str(
		frappe.db.get_value("Procurement Plan", {"plan_code": plan_code}, "status") or ""
	).strip()
	if not plan_code or plan_status != PLAN_ACTIVE:
		return {
			"code": PackageFromInclusion.ACTIVE_PLAN_REQUIRED,
			"message": _("Create or activate a procurement plan before creating a package."),
		}

	if not _budget_linked(budget_line):
		return {
			"code": PackageFromInclusion.FUNDING_REQUIRED,
			"message": _("Link an approved budget line before creating a package."),
		}

	existing_code = _find_existing_package_for_inclusion(resolved_inclusion)
	if existing_code:
		package_name = _package_display_name(existing_code)
		return {
			"code": PackageFromInclusion.PACKAGE_ALREADY_EXISTS,
			"message": _(
				"A procurement package already exists for this included demand. Open the existing package to continue."
			),
			"existing_package_code": existing_code,
			"existing_package_name": package_name,
			"duplicate_package": True,
		}

	if not guard.get("allowed"):
		blockers = guard.get("blockers") or []
		first = blockers[0] if blockers else {}
		return {
			"code": str(first.get("code") or PackageFromInclusion.INCLUSION_INVALID).strip(),
			"message": str(
				first.get("message") or _("This demand is not ready for package creation.")
			).strip(),
		}
	return None


def get_create_package_modal_drawer(
	*,
	demand_code: str | None = None,
	plan_code: str | None = None,
	inclusion_code: str | None = None,
	demand_item_codes: list[str] | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""Business labels and validation for Create Package modal (PP3 wireframe §13.2–13.3)."""
	actor_user = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key() or "auditor"
	if not pp_api_gates.check_profile_access(
		pp_api_gates.PLANNING_QUEUE_READ,
		require_demand_read=False,
	):
		return _fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to create procurement packages."),
			role_key=role_key,
		)

	resolved_demand = (demand_code or "").strip()
	resolved_plan = (plan_code or "").strip()
	resolved_inclusion = _resolve_inclusion_code(
		demand_code=resolved_demand,
		plan_code=resolved_plan,
		inclusion_code=inclusion_code,
		demand_item_codes=demand_item_codes,
	)
	if not resolved_inclusion:
		return {
			"ok": True,
			"role_key": role_key,
			"create_allowed": False,
			"blocker_code": PackageFromInclusion.INCLUSION_REQUIRED,
			"blocker_message": _(
				"Include this demand in the active procurement plan before creating a package."
			),
			"demand_code": resolved_demand,
		}

	drawer = get_approved_demand_planning_drawer(
		demand_code=resolved_demand,
		plan_code=resolved_plan or None,
		actor=actor_user,
	)
	if not drawer.get("ok"):
		return _fail(
			code=str(drawer.get("error_code") or "DRAWER_UNAVAILABLE"),
			message=str(drawer.get("message") or _("Demand planning context is unavailable.")),
			role_key=str(drawer.get("role_key") or role_key),
		)

	guard = can_create_package_from_inclusion(resolved_inclusion, actor_user)
	demand = drawer.get("demand") or {}
	target_plan = drawer.get("target_plan") or {}
	budget_line = (drawer.get("budget_context") or {}).get("budget_line") or {}
	blocker = _evaluate_create_package_validation(
		resolved_inclusion=resolved_inclusion,
		target_plan=target_plan,
		budget_line=budget_line,
		guard=guard,
	)

	demand_name = str(demand.get("name") or "").strip()
	demand_title = demand_name or resolved_demand
	category = str(demand.get("category") or "").strip()
	if not category:
		try:
			demand_docname = resolve_demand_name(resolved_demand)
			req_type = frappe.db.get_value("Demand", demand_docname, "requisition_type")
			category = _map_procurement_category(req_type)
		except Exception:
			category = category or "Goods"

	method_label = "Open Tender"
	try:
		demand_docname = resolve_demand_name(resolved_demand)
		template = _resolve_template_for_demand(demand_docname)
		if template and (template.get("default_method") or "").strip():
			method_label = str(template.get("default_method")).strip()
	except Exception:
		pass

	currency = str(demand.get("currency") or "KES").strip() or "KES"
	value_label = _value_label(demand.get("estimated_value"), currency)
	funding_label = _funding_label(budget_line)
	plan_name = str(target_plan.get("name") or "").strip()

	payload: dict[str, Any] = {
		"ok": True,
		"role_key": role_key,
		"create_allowed": blocker is None,
		"demand_name": demand_title,
		"demand_code": resolved_demand,
		"active_plan_name": plan_name,
		"active_plan_code": str(target_plan.get("code") or resolved_plan or "").strip(),
		"category_label": category,
		"method_label": method_label,
		"value_label": value_label,
		"funding_label": funding_label,
		"package_title_default": demand_title,
		"inclusion_code": resolved_inclusion,
	}
	if blocker:
		payload["blocker_code"] = blocker.get("code")
		payload["blocker_message"] = blocker.get("message")
		if blocker.get("duplicate_package"):
			payload["duplicate_package"] = True
			payload["existing_package_code"] = blocker.get("existing_package_code")
			payload["existing_package_name"] = blocker.get("existing_package_name")
	else:
		payload["blocker_code"] = ""
		payload["blocker_message"] = ""
	return payload
