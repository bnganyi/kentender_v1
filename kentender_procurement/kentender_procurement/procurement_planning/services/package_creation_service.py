# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 — Create Procurement Package from Planning Inclusion (P2-004)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

from kentender_procurement.procurement_lifecycle.evidence_links import normalize_evidence_links_raw
from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
	recompute_package_estimated_value,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CANCELLED,
	PKG_DRAFT,
	PKG_SUPERSEDED,
)
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	can_include_demand_in_plan,
	get_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.planning_references import (
	resolve_demand_name,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	DemandInclusion,
	PackageFromInclusion,
)
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope

_PLANNING_INCLUSION_TITLE = "Planning Inclusion Record"
_HANDOFF_STATUS_INCLUDED = "Handed Off"
_TERMINAL_INCLUSION_STATUSES = frozenset(("Cancelled", "Superseded"))
_TERMINAL_PACKAGE_STATUSES = frozenset((PKG_CANCELLED, PKG_SUPERSEDED))
_CATEGORY_VALUES = frozenset(("Works", "Goods", "Services", "Consultancy"))


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _check(check_id: str, label: str, ok: bool) -> dict[str, Any]:
	return {"id": check_id, "label": label, "ok": bool(ok)}


def _parse_json_list(raw: Any) -> list[str]:
	if raw in (None, ""):
		return []
	if isinstance(raw, str):
		try:
			parsed = json.loads(raw)
		except json.JSONDecodeError:
			return []
		raw = parsed
	if isinstance(raw, list):
		return [str(x).strip() for x in raw if str(x).strip()]
	return []


def _normalize_item_codes(demand_item_codes: list[str] | None) -> list[str]:
	return sorted({c.strip() for c in (demand_item_codes or []) if (c or "").strip()})


def _map_procurement_category(requisition_type: str | None) -> str:
	cat = (requisition_type or "").strip()
	if cat in _CATEGORY_VALUES:
		return cat
	lower = cat.lower()
	for value in _CATEGORY_VALUES:
		if value.lower() == lower:
			return value
	return "Goods"


def _package_line_code(package_code: str, seq: str = "001") -> str:
	code = (package_code or "").strip()
	if code.upper().startswith("PKG-"):
		return f"PKGLINE-{code[4:]}-{seq}"
	return f"PKGLINE-{code}-{seq}"


def _resolve_budget_line_name(budget_line_code: str) -> str | None:
	code = (budget_line_code or "").strip()
	if not code:
		return None
	if frappe.db.exists("Budget Line", code):
		return code
	return frappe.db.get_value("Budget Line", {"budget_line_code": code}, "name")


def _resolve_template_for_demand(demand_name: str) -> dict[str, Any] | None:
	req_type = (frappe.db.get_value("Demand", demand_name, "requisition_type") or "").strip()
	rows = frappe.get_all(
		"Procurement Template",
		filters={"is_active": 1},
		fields=[
			"name",
			"template_code",
			"default_method",
			"default_contract_type",
			"risk_profile_id",
			"kpi_profile_id",
			"decision_criteria_profile_id",
			"vendor_management_profile_id",
			"applicable_requisition_types",
			"procurement_cycle_days",
		],
		order_by="modified desc",
	)
	if not rows:
		return None
	for row in rows:
		types = _parse_json_list(row.get("applicable_requisition_types"))
		if not types or req_type in types:
			return row
	return rows[0]


def _template_usable(template: dict[str, Any] | None) -> bool:
	if not template:
		return False
	for field in ("risk_profile_id", "kpi_profile_id", "vendor_management_profile_id"):
		if not (template.get(field) or "").strip():
			return False
	return True


def _find_existing_package_for_inclusion(inclusion_code: str) -> str | None:
	code = (inclusion_code or "").strip()
	if not code:
		return None
	pkg_code = frappe.db.get_value(
		"Procurement Package",
		{
			"planning_inclusion_code": code,
			"is_active": 1,
			"status": ["not in", list(_TERMINAL_PACKAGE_STATUSES)],
		},
		"package_code",
		order_by="creation desc",
	)
	if pkg_code:
		return pkg_code
	inclusion = get_planning_inclusion(code) or {}
	linked = (inclusion.get("created_package_code") or "").strip()
	if linked and frappe.db.exists(
		"Procurement Package",
		{
			"package_code": linked,
			"is_active": 1,
			"status": ["not in", list(_TERMINAL_PACKAGE_STATUSES)],
		},
	):
		return linked
	return None


def can_create_package_from_inclusion(inclusion_code: str, actor: str) -> dict[str, Any]:
	"""Read-only guard — whether a package may be created from a Planning Inclusion."""
	blockers: list[dict[str, str]] = []
	checks: list[dict[str, Any]] = []

	inclusion = get_planning_inclusion((inclusion_code or "").strip())
	inclusion_ok = bool(inclusion)
	checks.append(_check("inclusion_exists", _("Planning inclusion exists"), inclusion_ok))
	if not inclusion:
		blockers.append(
			_blocker(
				PackageFromInclusion.INCLUSION_NOT_FOUND,
				_("Planning inclusion record was not found."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	handoff_status = (inclusion.get("handoff_status") or "").strip()
	handoff_valid = handoff_status not in _TERMINAL_INCLUSION_STATUSES
	checks.append(_check("inclusion_active", _("Planning inclusion is active"), handoff_valid))
	if not handoff_valid:
		blockers.append(
			_blocker(
				PackageFromInclusion.INCLUSION_INVALID,
				_("This planning inclusion is no longer eligible for packaging."),
			)
		)

	demand_code = (inclusion.get("demand_code") or "").strip()
	plan_code = (inclusion.get("procurement_plan_code") or "").strip()
	item_codes = _normalize_item_codes(inclusion.get("demand_item_codes"))
	inclusion_guard = can_include_demand_in_plan(demand_code, item_codes, plan_code, actor)
	checks.extend(inclusion_guard.get("checks") or [])
	if not inclusion_guard.get("allowed"):
		blockers.extend(inclusion_guard.get("blockers") or [])

	demand_name = None
	if demand_code:
		try:
			demand_name = resolve_demand_name(demand_code)
		except frappe.ValidationError:
			demand_name = None
	template = _resolve_template_for_demand(demand_name) if demand_name else None
	template_ok = _template_usable(template)
	checks.append(_check("template_available", _("Procurement template is available"), template_ok))
	if demand_name and not template_ok:
		blockers.append(
			_blocker(
				PackageFromInclusion.TEMPLATE_MISSING,
				_("No active procurement template is available for this demand."),
			)
		)

	return {
		"allowed": not blockers,
		"blockers": blockers,
		"checks": checks,
		"inclusion": inclusion,
	}


def _assert_can_create_or_throw(inclusion_code: str, actor: str) -> dict[str, Any]:
	guard = can_create_package_from_inclusion(inclusion_code, actor)
	if guard.get("allowed"):
		return guard["inclusion"]
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or _("Package cannot be created from this planning inclusion."),
		title=first.get("code") or PackageFromInclusion.INCLUSION_NOT_FOUND,
		exc=frappe.ValidationError,
	)


def _evidence_links_from_doc(doc) -> list[dict[str, str]]:
	raw = doc.evidence_links_json
	if not raw:
		return []
	try:
		wrapper = normalize_evidence_links_raw(raw)
	except ValueError:
		return []
	links = wrapper.get("links")
	return links if isinstance(links, list) else []


def _mark_inclusion_packaged(inclusion_code: str, package_code: str) -> None:
	if not frappe.db.exists("Procurement Handoff Card", inclusion_code):
		return
	doc = frappe.get_doc("Procurement Handoff Card", inclusion_code)
	locked = frappe.parse_json(doc.locked_summary or "{}")
	if not isinstance(locked, dict):
		locked = {}
	locked["created_package_code"] = package_code
	locked["inclusion_status"] = "Packaged"
	technical = frappe.parse_json(doc.technical_refs_json or "{}")
	if not isinstance(technical, dict):
		technical = {}
	payload = {
		"handoff_code": doc.handoff_code,
		"handoff_title": doc.handoff_title or _PLANNING_INCLUSION_TITLE,
		"journey_code": doc.journey_code,
		"source_module": doc.source_module,
		"target_module": doc.target_module,
		"source_object_type": doc.source_object_type,
		"source_object_code": doc.source_object_code,
		"target_object_type": doc.target_object_type,
		"target_object_code": doc.target_object_code,
		"status": doc.status or _HANDOFF_STATUS_INCLUDED,
		"generated_by": doc.generated_by,
		"generated_at": str(doc.generated_at) if doc.generated_at else None,
		"next_action": _("Review and complete the draft procurement package."),
		"locked_summary": locked,
		"passed_forward_summary": frappe.parse_json(doc.passed_forward_summary or "{}"),
		"evidence_links": _evidence_links_from_doc(doc),
		"technical_refs": technical,
		"is_master_seed": bool(doc.is_master_seed),
	}
	create_or_update_handoff_card(payload)


def _package_line_codes(package_code: str) -> list[str]:
	rows = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": package_code, "is_active": 1},
		pluck="package_line_code",
		order_by="creation asc",
	)
	return [c for c in rows if c]


def _format_package_response(
	*,
	action: str,
	inclusion_code: str,
	package_code: str,
	demand_code: str,
	budget_line_code: str,
) -> dict[str, Any]:
	line_codes = _package_line_codes(package_code)
	pkg_row = frappe.db.get_value(
		"Procurement Package",
		package_code,
		(
			"package_code",
			"package_name",
			"status",
			"planning_inclusion_code",
			"demand_id",
			"budget_line_id",
			"procurement_category",
			"estimated_value",
			"currency",
		),
		as_dict=True,
	)
	return {
		"ok": True,
		"action": action,
		"inclusion_code": inclusion_code,
		"package_code": package_code,
		"package_line_codes": line_codes,
		"demand_code": demand_code,
		"budget_line_code": budget_line_code,
		"status": PKG_DRAFT,
		"package": pkg_row or {"package_code": package_code},
		"inclusion": get_planning_inclusion(inclusion_code),
	}


def _resolve_procuring_entity_code(*, demand_name: str) -> str:
	"""Business entity code for package scope (falls back to Demand link name)."""
	name = (demand_name or "").strip()
	if not name:
		return ""
	entity_name = (frappe.db.get_value("Demand", name, "procuring_entity") or "").strip()
	if not entity_name:
		return ""
	if frappe.db.exists("Procuring Entity", entity_name):
		code = frappe.db.get_value("Procuring Entity", entity_name, "entity_code")
		return (code or entity_name).strip()
	return entity_name


def _demand_fields_for_package(demand_name: str) -> dict[str, Any]:
	return frappe.db.get_value(
		"Demand",
		demand_name,
		("title", "requisition_type", "total_amount", "budget_line", "requesting_department", "priority_level"),
		as_dict=True,
	) or {}


def create_package_with_lines(
	*,
	inclusions: list[dict[str, Any]],
	actor: str,
	package_overrides: dict[str, Any] | None = None,
	line_overrides_by_inclusion: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
	"""Create one `Procurement Package` with one `Procurement Package Line`
	per inclusion — the single canonical creation primitive shared by the
	legacy one-demand path (`create_package_from_planning_inclusion`) and
	the Package Creation Wizard's multi-demand packaging (PW6,
	`package_wizard_service.create_package_from_wizard`).

	The first inclusion is "primary" for plan/template/journey/procuring-
	entity defaults (the wizard's compatibility check already enforces
	same-entity/fiscal-year/category before this is called for >1 demand).
	`package_overrides` may set package_name/description/owner/priority/
	target_release_date/method override+reason at the package level.
	`line_overrides_by_inclusion` (keyed by inclusion_code) may set
	lot_group/delivery_location/line_title per line.
	"""
	if not inclusions:
		frappe.throw(
			_("At least one planning inclusion is required to create a package."),
			title=PackageFromInclusion.INCLUSION_NOT_FOUND,
		)
	overrides = package_overrides or {}
	line_overrides_by_inclusion = line_overrides_by_inclusion or {}

	primary = inclusions[0]
	primary_inclusion_code = (primary.get("inclusion_code") or "").strip()
	primary_demand_code = (primary.get("demand_code") or "").strip()
	plan_code = (primary.get("procurement_plan_code") or "").strip()
	journey_code = (primary.get("journey_code") or "").strip()

	primary_demand_name = resolve_demand_name(primary_demand_code)
	primary_demand = _demand_fields_for_package(primary_demand_name)

	template = _resolve_template_for_demand(primary_demand_name)
	if not _template_usable(template):
		frappe.throw(
			_("No active procurement template is available for this demand."),
			title=PackageFromInclusion.TEMPLATE_MISSING,
		)

	plan = frappe.db.get_value("Procurement Plan", plan_code, ("name", "currency"), as_dict=True)
	if not plan:
		frappe.throw(_("Procurement Plan not found."), title=DemandInclusion.PLAN_INACTIVE)

	primary_budget_line_code = (primary.get("budget_line_code") or "").strip()
	primary_budget_line_name = _resolve_budget_line_name(primary_budget_line_code) or primary_demand.get(
		"budget_line"
	)
	if not primary_budget_line_name:
		frappe.throw(_("Budget line could not be resolved."), title=DemandInclusion.BUDGET_MISSING)

	passed = primary.get("passed_forward_summary") or {}
	if not isinstance(passed, dict):
		passed = {}
	package_name = (
		(overrides.get("package_name") or "").strip()
		or (primary_demand.get("title") or "").strip()
		or (passed.get("package_candidate") or "").strip()
		or primary_demand_code
	)
	category = _map_procurement_category(primary_demand.get("requisition_type"))
	procuring_entity_code = _resolve_procuring_entity_code(demand_name=primary_demand_name)

	method_override_flag = 1 if overrides.get("method_override_flag") else 0
	procurement_method = (
		(overrides.get("procurement_method") or "").strip() or (template.get("default_method") or "Open Tender")
		if method_override_flag
		else (template.get("default_method") or "Open Tender")
	)
	package_priority = (overrides.get("package_priority") or "Normal").strip() or "Normal"

	pkg = frappe.get_doc(
		{
			"doctype": "Procurement Package",
			"plan_id": plan.name,
			"template_id": template["name"],
			"package_name": package_name,
			"package_description": (overrides.get("package_description") or "").strip() or None,
			"procurement_method": procurement_method,
			"contract_type": template.get("default_contract_type") or "Fixed Price",
			"currency": (plan.currency or "KES").strip(),
			"status": PKG_DRAFT,
			"is_active": 1,
			"method_override_flag": method_override_flag,
			"method_override_reason": (overrides.get("method_override_reason") or "").strip() or None,
			"is_emergency": 1 if package_priority == "Emergency" else 0,
			"planning_inclusion_code": primary_inclusion_code,
			"demand_id": primary_demand_name,
			"budget_line_id": primary_budget_line_name,
			"procurement_category": category,
			"journey_code": journey_code,
			"procuring_entity_code": procuring_entity_code or None,
			"package_owner": (overrides.get("package_owner") or "").strip() or actor or None,
			"target_release_date": overrides.get("target_release_date") or None,
			"package_priority": package_priority,
			"risk_profile_id": template.get("risk_profile_id"),
			"kpi_profile_id": template.get("kpi_profile_id"),
			"decision_criteria_profile_id": template.get("decision_criteria_profile_id"),
			"vendor_management_profile_id": template.get("vendor_management_profile_id"),
			"created_by": actor,
		}
	)
	pkg.insert(ignore_permissions=True)
	package_code = pkg.package_code or pkg.name

	line_codes: list[str] = []
	demand_codes: list[str] = []
	inclusion_codes: list[str] = []
	frappe.flags.skip_package_line_rollup = True
	try:
		for seq_idx, inclusion in enumerate(inclusions, start=1):
			inclusion_code = (inclusion.get("inclusion_code") or "").strip()
			demand_code = (inclusion.get("demand_code") or "").strip()
			demand_name = resolve_demand_name(demand_code)
			demand = (
				primary_demand
				if demand_name == primary_demand_name
				else _demand_fields_for_package(demand_name)
			)
			budget_line_code = (inclusion.get("budget_line_code") or "").strip()
			budget_line_name = _resolve_budget_line_name(budget_line_code) or demand.get("budget_line")
			if not budget_line_name:
				frappe.throw(
					_("Budget line could not be resolved for one of the selected demands."),
					title=DemandInclusion.BUDGET_MISSING,
				)
			item_codes = _normalize_item_codes(inclusion.get("demand_item_codes"))
			line_overrides = line_overrides_by_inclusion.get(inclusion_code) or {}
			line_code = _package_line_code(package_code, seq=f"{seq_idx:03d}")
			line = frappe.get_doc(
				{
					"doctype": "Procurement Package Line",
					"package_id": package_code,
					"package_line_code": line_code,
					"demand_id": demand_name,
					"budget_line_id": budget_line_name,
					"demand_item_code": item_codes[0] if item_codes else None,
					"amount": flt(demand.get("total_amount")),
					"quantity": 1.0,
					"line_title": (line_overrides.get("line_title") or "").strip() or (demand.get("title") or package_name),
					"procurement_category": _map_procurement_category(demand.get("requisition_type")),
					"department": demand.get("requesting_department"),
					"priority": demand.get("priority_level") or "Normal",
					"lot_group": (line_overrides.get("lot_group") or "").strip() or None,
					"delivery_location": (line_overrides.get("delivery_location") or "").strip() or None,
					"line_status": PKG_DRAFT,
					"is_active": 1,
				}
			)
			line.insert(ignore_permissions=True)
			line_codes.append(line_code)
			demand_codes.append(demand_code)
			inclusion_codes.append(inclusion_code)
	finally:
		frappe.flags.pop("skip_package_line_rollup", None)

	recompute_package_estimated_value(package_code)
	for inclusion_code in inclusion_codes:
		_mark_inclusion_packaged(inclusion_code, package_code)
	record_planning_audit_event(
		event_type="Package Created",
		object_type="Procurement Package",
		object_code=package_code,
		to_state=PKG_DRAFT,
		evidence_ref=primary_inclusion_code,
		journey_code=journey_code or None,
		actor=actor,
	)
	for line_code in line_codes:
		record_planning_audit_event(
			event_type="Package Line Created",
			object_type="Procurement Package Line",
			object_code=line_code,
			to_state=PKG_DRAFT,
			evidence_ref=package_code,
			journey_code=journey_code or None,
			actor=actor,
		)
	return {
		"package_code": package_code,
		"package_line_codes": line_codes,
		"demand_codes": demand_codes,
		"inclusion_codes": inclusion_codes,
	}


def _create_package_and_line(
	*,
	inclusion: dict[str, Any],
	actor: str,
) -> dict[str, Any]:
	inclusion_code = (inclusion.get("inclusion_code") or "").strip()
	demand_code = (inclusion.get("demand_code") or "").strip()
	budget_line_code = (inclusion.get("budget_line_code") or "").strip()
	result = create_package_with_lines(inclusions=[inclusion], actor=actor)
	return _format_package_response(
		action="created",
		inclusion_code=inclusion_code,
		package_code=result["package_code"],
		demand_code=demand_code,
		budget_line_code=budget_line_code,
	)


def create_package_from_planning_inclusion(inclusion_code: str, actor: str) -> dict[str, Any]:
	"""Create or return a Draft procurement package from a Planning Inclusion handoff."""
	inclusion_code = (inclusion_code or "").strip()
	actor_user = (actor or frappe.session.user or "").strip() or frappe.session.user

	inclusion = get_planning_inclusion(inclusion_code)
	if not inclusion:
		frappe.throw(
			_("Planning inclusion record was not found."),
			title=PackageFromInclusion.INCLUSION_NOT_FOUND,
			exc=frappe.ValidationError,
		)

	existing_code = _find_existing_package_for_inclusion(inclusion_code)
	if existing_code:
		pp_policy.assert_may_create_package_from_inclusion()
		pp_scope.assert_may_act_on_planning_inclusion(
			inclusion.get("demand_code") or inclusion.get("source_object_code") or "",
			inclusion.get("procurement_plan_code") or inclusion.get("target_object_code") or "",
		)
		return _format_package_response(
			action="existing",
			inclusion_code=inclusion_code,
			package_code=existing_code,
			demand_code=(inclusion.get("demand_code") or "").strip(),
			budget_line_code=(inclusion.get("budget_line_code") or "").strip(),
		)

	inclusion = _assert_can_create_or_throw(inclusion_code, actor_user)
	pp_policy.assert_may_create_package_from_inclusion()
	pp_scope.assert_may_act_on_planning_inclusion(
		inclusion.get("demand_code") or inclusion.get("source_object_code") or "",
		inclusion.get("procurement_plan_code") or inclusion.get("target_object_code") or "",
	)

	return _create_package_and_line(inclusion=inclusion, actor=actor_user)
