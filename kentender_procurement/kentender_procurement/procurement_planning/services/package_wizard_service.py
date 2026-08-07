# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning Package Creation Wizard — backend services (PW2, PW3, PW4, PW5, PW6).

Implements `Planning Package Creation Wizard.md` §5/§8–§12 on top of the
existing PP2 planning-inclusion and package-creation primitives. Nothing
in Steps 1–2 persists to the database — the wizard is pure client-side
staged state until Step 3's final `create_pp_package_from_wizard` call
(Save Draft is explicitly deferred; see the Package Wizard tracker).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate

from kentender_procurement.procurement_planning.services.package_creation_service import (
	_map_procurement_category,
	_resolve_template_for_demand,
	_template_usable,
	create_package_with_lines,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	_inclusion_is_unpackaged,
	get_planning_inclusion,
	list_unpackaged_planning_inclusions,
)
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT, PLAN_ACTIVE
from kentender_procurement.procurement_planning.permissions import pp_policy
from kentender_budget.api.dia_budget_control import check_available_budget
from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	format_ambiguous_std_message,
	resolve_std_template_for_handoff,
)

_READY = "Ready"
_WARNING = "Warning"
_BLOCKED = "Blocked"

_STATUS_ADDED_TO_PLAN = "Added to Active Plan"


def _demand_name(demand_code: str) -> str | None:
	demand_code = (demand_code or "").strip()
	if not demand_code or not frappe.db.exists("DocType", "Demand"):
		return None
	name = frappe.db.get_value("Demand", {"demand_id": demand_code}, "name")
	return name or (demand_code if frappe.db.exists("Demand", demand_code) else None)


def _strategy_label_for_demand(demand_name: str | None = None) -> str:
	"""XMOD-STR-004 — Name (CODE) from Demand Strategy Reference."""
	if not demand_name or not frappe.db.exists("Demand", demand_name):
		return ""
	try:
		from kentender_strategy.services.strategy_consumer import strategy_fields_from_doc
	except ImportError:
		return ""
	doc = frappe.get_doc("Demand", demand_name)
	sf = strategy_fields_from_doc(doc) or {}
	name = (sf.get("performance_target_label") or "").strip()
	code = (sf.get("performance_target_code") or "").strip()
	if name and code:
		return f"{name} ({code})"
	return name or code or (getattr(doc, "strategy_snapshot_label", None) or "").strip()


def _documents_count(demand_name: str | None) -> int:
	if not demand_name:
		return 0
	return frappe.db.count(
		"File",
		{"attached_to_doctype": "Demand", "attached_to_name": demand_name},
	)


def _funding_label(demand_name: str | None) -> str:
	"""Business-readable funding status (§9.5 vocabulary). Eligibility for
	the wizard already requires a linked, active budget line, so eligible
	demands are always "Reserved"; kept as a function (not a constant) so
	PW4/PW5 can extend this with insufficient/blocked states once a real
	funding-shortfall signal exists."""
	if not demand_name:
		return _("Not confirmed")
	budget_line = frappe.db.get_value("Demand", demand_name, "budget_line")
	if not budget_line:
		return _("Not confirmed")
	return _("Reserved")


def _demand_card_fields(demand_code: str) -> dict[str, Any]:
	demand_name = _demand_name(demand_code)
	if not demand_name:
		return {}
	row = frappe.db.get_value(
		"Demand",
		demand_name,
		("required_by_date", "status"),
		as_dict=True,
	) or {}
	return {
		"demand_name": demand_name,
		"needed_by": str(row.get("required_by_date") or ""),
		"strategy_label": _strategy_label_for_demand(demand_name),
		"documents_count": _documents_count(demand_name),
		"funding_label": _funding_label(demand_name),
	}


def _matches_search(row: dict[str, Any], search_text: str) -> bool:
	q = (search_text or "").strip().lower()
	if not q:
		return True
	hay = " ".join(
		[
			str(row.get("title") or ""),
			str(row.get("demand_code") or ""),
			str(row.get("department_label") or ""),
			str(row.get("category") or ""),
		]
	).lower()
	return q in hay


def list_wizard_eligible_demands(plan_code: str, search: str | None = None) -> list[dict[str, Any]]:
	"""Step 1 data source — demands "Added to Active Plan" for `plan_code`
	with no package yet (§5/§8.2 eligibility note: "Only approved, funded
	demands in the active procurement plan are shown."). Same underlying
	set as the Workbench's "In Creation" placeholder rows
	(`list_unpackaged_planning_inclusions`), enriched with the §8.3 demand
	card fields. No technical codes are exposed (§15/§17)."""
	if not frappe.db.exists("DocType", "Demand"):
		return []
	base_rows = list_unpackaged_planning_inclusions(plan_code)
	out: list[dict[str, Any]] = []
	for row in base_rows:
		if not _matches_search(row, search or ""):
			continue
		demand_code = row.get("demand_code") or ""
		extra = _demand_card_fields(demand_code)
		out.append(
			{
				"inclusion_code": row.get("inclusion_code") or "",
				"demand": {
					"code": demand_code,
					"name": row.get("title") or demand_code,
				},
				"ref": demand_code,
				"department": row.get("department_label") or "",
				"category": row.get("category") or "",
				"estimated_value": flt(row.get("estimated_value")),
				"currency": row.get("currency") or "KES",
				"funding_label": extra.get("funding_label") or _("Not confirmed"),
				"strategy_label": extra.get("strategy_label") or "",
				"needed_by": extra.get("needed_by") or "",
				"documents_count": extra.get("documents_count") or 0,
				"status_label": _STATUS_ADDED_TO_PLAN,
				"created_on": row.get("created_on") or "",
			}
		)
	return out


def _compatibility_context(inclusion_code: str) -> dict[str, Any] | None:
	inclusion = _inclusion_is_unpackaged(inclusion_code)
	if not inclusion:
		return None
	demand_code = (inclusion.get("demand_code") or "").strip()
	demand_name = _demand_name(demand_code)
	if not demand_name:
		return None
	demand = frappe.db.get_value(
		"Demand",
		demand_name,
		("procuring_entity", "requisition_type", "budget_line", "required_by_date"),
		as_dict=True,
	) or {}
	plan_code = (inclusion.get("procurement_plan_code") or "").strip()
	plan = frappe.db.get_value("Procurement Plan", plan_code, ("fiscal_year",), as_dict=True) or {}
	template = _resolve_template_for_demand(demand_name)
	usable_template = template if _template_usable(template) else None
	recommended_method = (usable_template.get("default_method") or "").strip() if usable_template else ""
	procurement_cycle_days = frappe.utils.cint((usable_template or {}).get("procurement_cycle_days")) or None
	# MVP-1 Budget teardown: Budget Line DocType gone; linked Data value is enough.
	return {
		"inclusion_code": inclusion_code,
		"demand_code": demand_code,
		"title": (inclusion.get("passed_forward_summary") or {}).get("package_candidate") or demand_code,
		"procuring_entity": (demand.get("procuring_entity") or "").strip(),
		"fiscal_year": plan.get("fiscal_year"),
		"category": _map_procurement_category(demand.get("requisition_type")),
		"recommended_method": recommended_method,
		"required_by_date": demand.get("required_by_date"),
		"procurement_cycle_days": procurement_cycle_days,
		"funding_ok": bool(demand.get("budget_line")),
	}


def check_package_compatibility(inclusion_codes: list[str]) -> dict[str, Any]:
	"""§8.4 compatibility checks across selected demands before they can be
	packaged together (9 checks total). Real-data checks implemented here:
	same procuring entity, same fiscal year, compatible category,
	compatible procurement method, compatible funding source (linked
	active Budget Line), compatible delivery/procurement timeline
	(`required_by_date` spread vs. the template's `procurement_cycle_days`).

	Two checks have no backing data model on this site and are documented,
	always-pass stubs: donor/funding-restriction-conflict and
	confidentiality-conflict. See the Package Wizard tracker's scope
	decisions — do not silently invent a data model for these.

	Package-value-threshold-conflict is intentionally *not* evaluated
	against invented numeric bands: `Procurement Template.threshold_rules`
	exists but its interpretation is already a documented v1 no-op
	site-wide ("threshold bands deferred", see
	`procurement_package.py::_apply_template_defaults`); duplicating a
	one-off interpreter here for the wizard would contradict that existing
	precedent, so this check also always passes for now.
	"""
	codes = [c.strip() for c in (inclusion_codes or []) if (c or "").strip()]
	if len(codes) <= 1:
		return {"compatible": True, "reasons": [], "demands": []}

	contexts = []
	for code in codes:
		ctx = _compatibility_context(code)
		if not ctx:
			return {
				"compatible": False,
				"reasons": [_("One of the selected demands is no longer eligible for packaging.")],
				"demands": [],
			}
		contexts.append(ctx)

	reasons: list[str] = []

	entities = {c["procuring_entity"] for c in contexts if c["procuring_entity"]}
	if len(entities) > 1:
		reasons.append(_("These demands cannot be packaged together because they belong to different procuring entities."))

	fiscal_years = {c["fiscal_year"] for c in contexts if c["fiscal_year"] is not None}
	if len(fiscal_years) > 1:
		reasons.append(_("These demands cannot be packaged together because they belong to different fiscal years."))

	categories = {c["category"] for c in contexts if c["category"]}
	if len(categories) > 1:
		reasons.append(_("These demands cannot be packaged together because they use different procurement categories."))

	methods = {c["recommended_method"] for c in contexts if c["recommended_method"]}
	if len(methods) > 1:
		reasons.append(
			_("These demands cannot be packaged together because they recommend different procurement methods.")
		)

	if any(not c["funding_ok"] for c in contexts):
		reasons.append(_("One or more selected demands do not have confirmed funding."))

	required_dates = [getdate(c["required_by_date"]) for c in contexts if c.get("required_by_date")]
	cycle_windows = [c["procurement_cycle_days"] for c in contexts if c.get("procurement_cycle_days")]
	if len(required_dates) == len(contexts) and cycle_windows:
		spread_days = date_diff(max(required_dates), min(required_dates))
		allowed_window = min(cycle_windows)
		if spread_days > allowed_window:
			reasons.append(
				_(
					"These demands cannot be packaged together because their required-by dates are "
					"too far apart for a shared procurement timeline."
				)
			)

	return {
		"compatible": not reasons,
		"reasons": reasons,
		"demands": [{"inclusion_code": c["inclusion_code"], "title": c["title"]} for c in contexts],
	}


_VALID_PACKAGE_PRIORITIES = frozenset(("Normal", "High", "Emergency"))


def _line_preview(inclusion: dict[str, Any], line_override: dict[str, Any] | None) -> dict[str, Any] | None:
	demand_code = (inclusion.get("demand_code") or "").strip()
	demand_name = _demand_name(demand_code)
	if not demand_name:
		return None
	demand = frappe.get_doc("Demand", demand_name)
	line_override = line_override or {}
	item_count = len(demand.items or [])
	scope_summary = (
		(demand.items[0].item_description or "").strip()
		if item_count == 1
		else _("{0} items").format(item_count)
	)
	return {
		"inclusion_code": inclusion.get("inclusion_code") or inclusion.get("handoff_code") or "",
		"demand_code": demand_code,
		"line_title": (line_override.get("line_title") or "").strip() or demand.title or demand_code,
		"source_demand_item": demand_code,
		"scope_quantity": scope_summary or _("No items"),
		"estimated_value": flt(demand.total_amount),
		"budget_line_code": _budget_line_business_code_safe(demand.budget_line),
		"lot_group": (line_override.get("lot_group") or "").strip(),
		"delivery_location": (line_override.get("delivery_location") or "").strip(),
	}


def _budget_line_business_code_safe(budget_line_name: str | None) -> str:
	if not budget_line_name:
		return ""
	# MVP-1 Budget teardown: field is free-text / code; DocType may be absent.
	if not frappe.db.exists("DocType", "Budget Line"):
		return (budget_line_name or "").strip()
	return (
		frappe.db.get_value("Budget Line", budget_line_name, "generated_reference")
		or budget_line_name
		or ""
	).strip()


def _funding_preview(inclusions: list[dict[str, Any]]) -> dict[str, Any]:
	budget_lines: list[dict[str, Any]] = []
	blockers: list[str] = []
	package_value = 0.0
	reserved_total = 0.0
	currency = "KES"
	seen_budget_lines: set[str] = set()
	any_missing_budget_line = False

	for inclusion in inclusions:
		demand_code = (inclusion.get("demand_code") or "").strip()
		demand_name = _demand_name(demand_code)
		demand = frappe.db.get_value(
			"Demand", demand_name, ("budget_line", "total_amount"), as_dict=True
		) if demand_name else None
		if not demand:
			continue
		package_value += flt(demand.get("total_amount"))
		budget_line_name = demand.get("budget_line")
		if not budget_line_name:
			any_missing_budget_line = True
			blockers.append(_("A selected demand has no linked budget line."))
			continue
		check = check_available_budget(budget_line_name, flt(demand.get("total_amount")) or 0.01)
		if not check.get("ok"):
			any_missing_budget_line = True
			blockers.append(_("A selected demand's budget line is unavailable ({0}).").format(check.get("message") or ""))
			continue
		data = check.get("data") or {}
		currency = data.get("currency") or currency
		if not data.get("is_sufficient"):
			blockers.append(
				_("Budget line {0} has insufficient available funds for this package.").format(
					_budget_line_business_code_safe(budget_line_name)
				)
			)
		if budget_line_name not in seen_budget_lines:
			seen_budget_lines.add(budget_line_name)
			reserved_row: dict[str, Any] = {}
			if frappe.db.exists("DocType", "Budget Line"):
				reserved_row = (
					frappe.db.get_value(
						"Budget Line",
						budget_line_name,
						("amount_reserved", "budget_line_name"),
						as_dict=True,
					)
					or {}
				)
			reserved_total += flt(reserved_row.get("amount_reserved"))
			budget_lines.append(
				{
					"budget_line_code": _budget_line_business_code_safe(budget_line_name),
					"budget_line_name": (reserved_row.get("budget_line_name") or budget_line_name or "").strip(),
					"amount_reserved": flt(reserved_row.get("amount_reserved")),
					"amount_available": flt(data.get("amount_available")),
				}
			)

	funding_difference = reserved_total - package_value
	if any_missing_budget_line:
		funding_status = _("Blocked")
	elif not frappe.db.exists("DocType", "Budget Line"):
		# MVP-1 Budget teardown: no live balances; linked Data value is enough.
		funding_status = _("Reserved")
		funding_difference = 0.0
	elif funding_difference < 0:
		funding_status = _("Insufficient")
	else:
		funding_status = _("Reserved")

	return {
		"budget_lines": budget_lines,
		"currency": currency,
		"package_estimated_value": flt(package_value),
		"reserved_amount": flt(reserved_total),
		"funding_difference": flt(funding_difference),
		"funding_status": funding_status,
		"funding_blockers": blockers,
	}


def _resolve_inclusions_or_error(inclusion_codes: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
	codes = [c.strip() for c in (inclusion_codes or []) if (c or "").strip()]
	if not codes:
		return [], {
			"ok": False,
			"error_code": "NO_DEMANDS_SELECTED",
			"message": _("Select at least one demand to configure a package."),
		}
	inclusions: list[dict[str, Any]] = []
	for code in codes:
		inclusion = _inclusion_is_unpackaged(code)
		if not inclusion:
			return [], {
				"ok": False,
				"error_code": "INCLUSION_NOT_ELIGIBLE",
				"message": _("One of the selected demands is no longer eligible for packaging."),
			}
		inclusions.append(inclusion)
	return inclusions, None


def _primary_template_context(inclusions: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
	primary = inclusions[0]
	primary_demand_name = _demand_name(primary.get("demand_code") or "")
	primary_demand = frappe.get_doc("Demand", primary_demand_name) if primary_demand_name else None
	default_title = (primary_demand.title if primary_demand else "") or (primary.get("demand_code") or "")

	template = _resolve_template_for_demand(primary_demand_name) if primary_demand_name else None
	usable_template = template if _template_usable(template) else None
	recommended_method = (usable_template.get("default_method") or "").strip() if usable_template else ""
	category = _map_procurement_category(primary_demand.requisition_type) if primary_demand else ""

	requested_method = (config.get("procurement_method") or "").strip()
	is_override = bool(requested_method) and bool(recommended_method) and requested_method != recommended_method
	contract_type_expectation = (
		(config.get("contract_type_expectation") or "").strip()
		or ((usable_template.get("default_contract_type") or "").strip() if usable_template else "")
	)
	return {
		"primary_demand_name": primary_demand_name,
		"default_title": default_title,
		"template_name": (usable_template or {}).get("name") if usable_template else None,
		"recommended_method": recommended_method,
		"category": category,
		"requested_method": requested_method,
		"is_override": is_override,
		"contract_type_expectation": contract_type_expectation,
	}


def preview_package_configuration(
	inclusion_codes: list[str],
	config: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""§9 Step 2 pre-create configuration preview — pure computation over the
	demands selected in Step 1 plus the planner's in-progress form input.
	Never persists anything (Save Draft is deferred; only Step 3's final
	create call writes to the DB).
	"""
	config = config or {}
	inclusions, err = _resolve_inclusions_or_error(inclusion_codes)
	if err:
		return err
	codes = [i.get("inclusion_code") or "" for i in inclusions]

	ctx = _primary_template_context(inclusions, config)
	recommended_method = ctx["recommended_method"]
	requested_method = ctx["requested_method"]
	is_override = ctx["is_override"]
	method_override_reason = (config.get("method_override_reason") or "").strip()

	priority = (config.get("package_priority") or "Normal").strip()
	if priority not in _VALID_PACKAGE_PRIORITIES:
		priority = "Normal"

	package_identity = {
		"package_title": (config.get("package_title") or "").strip() or ctx["default_title"],
		"package_description": (config.get("package_description") or "").strip(),
		"package_owner": (config.get("package_owner") or "").strip() or frappe.session.user,
		"target_release_date": config.get("target_release_date") or "",
		"package_priority": priority,
	}

	category_method = {
		"category": ctx["category"],
		"procurement_method": requested_method or recommended_method,
		"recommended_method": recommended_method,
		"method_basis": "Manual Confirmation" if is_override else "Template",
		"method_override_flag": is_override,
		"method_override_reason": method_override_reason,
		"method_justification_required": is_override,
		"contract_type_expectation": ctx["contract_type_expectation"],
	}

	line_overrides = config.get("line_overrides") or {}
	lines = []
	for inclusion in inclusions:
		line = _line_preview(inclusion, line_overrides.get(inclusion.get("inclusion_code") or ""))
		if line:
			lines.append(line)

	funding = _funding_preview(inclusions)

	warnings: list[str] = []
	if funding["funding_difference"] < 0:
		warnings.append(_("Package value exceeds reserved funding."))
	if is_override and not method_override_reason:
		warnings.append(_("Procurement method override requires justification."))
	for inclusion in inclusions:
		demand_name = _demand_name(inclusion.get("demand_code") or "")
		if demand_name and not (frappe.db.get_value("Demand", demand_name, "specification_summary") or "").strip():
			warnings.append(_("One selected demand has missing specifications."))
			break

	return {
		"ok": True,
		"inclusion_codes": codes,
		"package_identity": package_identity,
		"category_method": category_method,
		"funding": funding,
		"lines": lines,
		"warnings": warnings,
	}


def preview_document_std_path(
	inclusion_codes: list[str],
	config: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""§9.7 Document / STD Path Section — read-only surfacing for Step 2.

	Reuses the **canonical** planning-to-tender STD resolution
	(`resolve_std_template_for_handoff`, doc 2 sec. 12.1) rather than a
	one-off wizard interpreter — a plain dict stands in for the not-yet-
	created `Procurement Package` since that function only calls `.get()`
	on its argument. Specification-attachment count is inherited from the
	selected demand(s), matching §9.7's "N documents inherited from
	demand" copy.
	"""
	config = config or {}
	inclusions, err = _resolve_inclusions_or_error(inclusion_codes)
	if err:
		return err

	ctx = _primary_template_context(inclusions, config)
	virtual_package = {
		"template_id": ctx["template_name"],
		"procurement_method": ctx["requested_method"] or ctx["recommended_method"],
		"contract_type": ctx["contract_type_expectation"],
	}
	resolution = resolve_std_template_for_handoff(virtual_package)

	std_template_code = ""
	std_template_name = ""
	if resolution.std_name:
		std_row = frappe.db.get_value(
			"STD Template", resolution.std_name, ("template_code", "template_name"), as_dict=True
		) or {}
		std_template_code = (std_row.get("template_code") or "").strip()
		std_template_name = (std_row.get("template_name") or "").strip()

	method_label = (ctx["requested_method"] or ctx["recommended_method"] or "").strip()
	category_label = (ctx["category"] or "").strip()
	if resolution.path in ("default_std_template", "mapping_service", "works_poc_fallback"):
		std_path_resolved = True
		std_path_label = " ".join(p for p in (category_label, method_label) if p) or std_template_name
	else:
		std_path_resolved = False
		std_path_label = ""

	documents_count = sum(_documents_count(_demand_name(i.get("demand_code") or "")) for i in inclusions)
	missing_documents: list[str] = [] if documents_count > 0 else [_("Specification attachments")]

	warnings: list[str] = []
	if resolution.path == "ambiguous":
		warnings.append(
			_("Multiple standard tender document paths match this package; select one explicitly ({0}).").format(
				format_ambiguous_std_message(resolution.ambiguous_candidates)
			)
		)
	elif resolution.path == "invalid_default":
		warnings.append(_("The linked standard tender document path could not be found."))
	elif resolution.path == "unresolved":
		warnings.append(_("Tender document path has not been selected."))
	if not documents_count:
		warnings.append(_("One or more selected demands has no specification attachments."))

	return {
		"ok": True,
		"required_document_family": category_label,
		"std_path_resolved": std_path_resolved,
		"std_path_label": std_path_label,
		"std_template_code": std_template_code,
		"std_template_name": std_template_name,
		"resolution_path": resolution.path,
		"specification_attachments_count": documents_count,
		"missing_documents": missing_documents,
		"warnings": warnings,
	}


def _readiness_check(key: str, label: str, status: str, message: str = "") -> dict[str, str]:
	return {"key": key, "label": label, "status": status, "message": message}


def evaluate_wizard_readiness(
	inclusion_codes: list[str],
	config: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""§10.3 Readiness Preview + §10.5 blocking conditions for Step 3.

	Composes PW2's eligibility/inclusion lookups, PW3's configuration
	preview, and PW4's document-path preview into the 7-row readiness
	checklist (`checks`) plus an overall `create_allowed` flag and
	business-readable `blocking_reasons` — the single source of truth the
	"Create Package" button's disabled state reads from. Never persists.
	"""
	config = config or {}
	codes = [c.strip() for c in (inclusion_codes or []) if (c or "").strip()]
	checks: list[dict[str, Any]] = []
	blockers: list[str] = []

	if not codes:
		checks.append(
			_readiness_check("demand_selected", _("Approved demand selected"), _BLOCKED, _("Select at least one demand."))
		)
		blockers.append(_("Select at least one demand to create a package."))
		return {"ok": True, "checks": checks, "create_allowed": False, "blocking_reasons": blockers}

	inclusions: list[dict[str, Any]] = []
	for code in codes:
		inclusion = _inclusion_is_unpackaged(code)
		if not inclusion:
			checks.append(
				_readiness_check(
					"demand_selected",
					_("Approved demand selected"),
					_BLOCKED,
					_("One of the selected demands is already fully packaged or no longer eligible."),
				)
			)
			blockers.append(_("One of the selected demands is already fully packaged or no longer eligible."))
			return {"ok": True, "checks": checks, "create_allowed": False, "blocking_reasons": blockers}
		inclusions.append(inclusion)

	all_approved = True
	for inclusion in inclusions:
		demand_name = _demand_name(inclusion.get("demand_code") or "")
		status = frappe.db.get_value("Demand", demand_name, "status") if demand_name else None
		if status != "Approved":
			all_approved = False
	if all_approved:
		checks.append(_readiness_check("demand_selected", _("Approved demand selected"), _READY))
	else:
		checks.append(
			_readiness_check(
				"demand_selected", _("Approved demand selected"), _BLOCKED, _("One or more selected demands is not Approved.")
			)
		)
		blockers.append(_("One or more selected demands is not Approved."))

	plan_code = (inclusions[0].get("procurement_plan_code") or "").strip()
	plan_status = frappe.db.get_value("Procurement Plan", plan_code, "status") if plan_code else None
	if plan_code and plan_status == PLAN_ACTIVE:
		checks.append(_readiness_check("plan_active", _("Active procurement plan exists"), _READY))
	else:
		checks.append(
			_readiness_check(
				"plan_active",
				_("Active procurement plan exists"),
				_BLOCKED,
				_("No active procurement plan found for the selected demand(s)."),
			)
		)
		blockers.append(_("No active procurement plan found for the selected demand(s)."))

	preview = preview_package_configuration(codes, config)
	if not preview.get("ok"):
		checks.append(
			_readiness_check(
				"configuration", _("Package configuration valid"), _BLOCKED, preview.get("message") or ""
			)
		)
		blockers.append(preview.get("message") or _("Package configuration is invalid."))
		return {"ok": True, "checks": checks, "create_allowed": False, "blocking_reasons": blockers}

	funding = preview["funding"]
	if funding["funding_blockers"]:
		checks.append(
			_readiness_check("funding", _("Funding linked / reserved"), _BLOCKED, "; ".join(funding["funding_blockers"]))
		)
		blockers.extend(funding["funding_blockers"])
	elif funding["funding_status"] == _("Insufficient"):
		checks.append(
			_readiness_check(
				"funding", _("Funding linked / reserved"), _WARNING, _("Package value exceeds reserved funding.")
			)
		)
	else:
		checks.append(_readiness_check("funding", _("Funding linked / reserved"), _READY))

	category = preview["category_method"]["category"]
	if category:
		checks.append(_readiness_check("category", _("Category selected"), _READY))
	else:
		checks.append(_readiness_check("category", _("Category selected"), _BLOCKED, _("Procurement category is missing.")))
		blockers.append(_("Procurement category is missing."))

	method = preview["category_method"]["procurement_method"]
	if not method:
		checks.append(_readiness_check("method", _("Method selected"), _BLOCKED, _("Procurement method is missing.")))
		blockers.append(_("Procurement method is missing."))
	elif preview["category_method"]["method_override_flag"] and not preview["category_method"]["method_override_reason"]:
		checks.append(
			_readiness_check(
				"method", _("Method selected"), _WARNING, _("Procurement method override requires justification.")
			)
		)
	else:
		checks.append(_readiness_check("method", _("Method selected"), _READY))

	lines = preview["lines"]
	invalid_lines = [line for line in lines if not (line.get("estimated_value") or 0) > 0]
	if lines and not invalid_lines:
		checks.append(_readiness_check("lines", _("Package lines will be created"), _READY))
	else:
		checks.append(
			_readiness_check(
				"lines",
				_("Package lines will be created"),
				_BLOCKED,
				_("One or more selected demands cannot produce a package line."),
			)
		)
		blockers.append(_("One or more selected demands cannot produce a package line."))

	if not (preview["package_identity"]["package_title"] or "").strip():
		blockers.append(_("Package title is missing."))

	doc_preview = preview_document_std_path(codes, config)
	doc_count = doc_preview.get("specification_attachments_count", 0) if doc_preview.get("ok") else 0
	if doc_count > 0:
		checks.append(_readiness_check("documents", _("Documents inherited or identified"), _READY))
	else:
		checks.append(
			_readiness_check(
				"documents",
				_("Documents inherited or identified"),
				_WARNING,
				_("No specification documents found for the selected demand(s)."),
			)
		)

	try:
		pp_policy.assert_may_create_package_from_inclusion()
	except frappe.PermissionError as exc:
		blockers.append(str(exc) or _("You do not have permission to create a package."))

	return {
		"ok": True,
		"checks": checks,
		"create_allowed": not blockers,
		"blocking_reasons": blockers,
	}


def _package_overrides_from_config(preview: dict[str, Any]) -> dict[str, Any]:
	identity = preview["package_identity"]
	category_method = preview["category_method"]
	return {
		"package_name": identity["package_title"],
		"package_description": identity["package_description"],
		"package_owner": identity["package_owner"],
		"target_release_date": identity["target_release_date"] or None,
		"package_priority": identity["package_priority"],
		"method_override_flag": category_method["method_override_flag"],
		"procurement_method": category_method["procurement_method"],
		"method_override_reason": category_method["method_override_reason"],
	}


def create_package_from_wizard(
	inclusion_codes: list[str],
	config: dict[str, Any] | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""§10.4 "Create Package" commit + §12 data-created contract — the
	wizard's single write call.

	Re-runs PW5's readiness evaluation as the authoritative gate (never
	trusts client-side staged state), then delegates the actual insert to
	the canonical `create_package_with_lines` primitive shared with the
	legacy one-demand path — no duplicated creation logic. On success,
	records the wizard-specific "Package Wizard Completed" evidence
	required by §12.3 (the primitive already records "Package Created"/
	"Package Line Created") and shapes the response the Step 4 success
	screen needs (§11.2/§11.3).
	"""
	config = config or {}
	actor_user = (actor or frappe.session.user or "").strip() or frappe.session.user
	codes = [c.strip() for c in (inclusion_codes or []) if (c or "").strip()]

	readiness = evaluate_wizard_readiness(codes, config)
	if not readiness.get("create_allowed"):
		blockers = readiness.get("blocking_reasons") or []
		return {
			"ok": False,
			"error_code": "WIZARD_NOT_READY",
			"message": blockers[0] if blockers else _("Package is not ready to be created."),
			"blocking_reasons": blockers,
			"checks": readiness.get("checks") or [],
		}

	pp_policy.assert_may_create_package_from_inclusion()

	inclusions, err = _resolve_inclusions_or_error(codes)
	if err:
		return err

	preview = preview_package_configuration(codes, config)
	if not preview.get("ok"):
		return preview

	package_overrides = _package_overrides_from_config(preview)
	line_overrides_by_inclusion = config.get("line_overrides") or {}

	result = create_package_with_lines(
		inclusions=inclusions,
		actor=actor_user,
		package_overrides=package_overrides,
		line_overrides_by_inclusion=line_overrides_by_inclusion,
	)
	package_code = result["package_code"]

	journey_code = (inclusions[0].get("journey_code") or "").strip() or None
	record_planning_audit_event(
		event_type="Package Wizard Completed",
		object_type="Procurement Package",
		object_code=package_code,
		to_state=PKG_DRAFT,
		evidence_ref=",".join(result["inclusion_codes"]),
		journey_code=journey_code,
		actor=actor_user,
	)

	pkg_row = frappe.db.get_value(
		"Procurement Package",
		package_code,
		(
			"package_code",
			"package_name",
			"status",
			"plan_id",
			"procurement_category",
			"procurement_method",
			"estimated_value",
			"currency",
			"package_owner",
			"target_release_date",
		),
		as_dict=True,
	) or {}
	plan_row = (
		frappe.db.get_value("Procurement Plan", pkg_row.get("plan_id"), ("plan_code", "plan_name"), as_dict=True)
		if pkg_row.get("plan_id")
		else None
	) or {}
	demand_titles = [
		(frappe.db.get_value("Demand", _demand_name(i.get("demand_code") or ""), "title") or i.get("demand_code") or "")
		for i in inclusions
	]

	return {
		"ok": True,
		"package_code": package_code,
		"package_line_codes": result["package_line_codes"],
		"demand_codes": result["demand_codes"],
		"inclusion_codes": result["inclusion_codes"],
		"package": pkg_row,
		"plan": plan_row,
		"demand_titles": [t for t in demand_titles if t],
	}
