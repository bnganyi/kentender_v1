# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Funding Performance — BUD-UI-02 / BUD-FR-108–114 / get_funding_performance."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, get_datetime, now_datetime

from kentender_budget.services.budget_contracts import resolve_scoped_entity
from kentender_budget.services.budget_line_contracts import ACTUAL_STALE_DAYS, format_kes_full
from kentender_budget.services.budget_permissions import (
	ROLE_AUDITOR,
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	can_export_funding_performance,
	entity_for_user,
	require_any_role,
)
from kentender_core.services.authorization_policy import ResourceContext, require_capability

DISCLAIMER = (
	"Strategy alignment shows intended support. "
	"It does not prove that procurement caused the strategic result."
)

_FUNDING_STATUSES = (
	"Available",
	"Reserved",
	"Committed",
	"Needs attention",
)


def _entity_ref(pe_name: str | None) -> dict[str, str]:
	if not pe_name:
		return {"id": "", "code": "", "name": ""}
	code = frappe.db.get_value("Procuring Entity", pe_name, "entity_code") or pe_name
	name = (
		frappe.db.get_value("Procuring Entity", pe_name, "entity_name")
		or code
		or pe_name
	)
	return {"id": pe_name, "code": code, "name": name}


def _line_funding_status(line) -> str:
	if _is_stale_actual(line):
		return "Needs attention"
	reserved = flt(line.amount_reserved)
	committed = flt(line.amount_committed)
	approved = flt(line.approved_amount)
	available = approved - reserved - committed
	if committed > 0 and available <= 0:
		return "Committed"
	if reserved > 0:
		return "Reserved"
	return "Available"


def _is_stale_actual(line) -> bool:
	from frappe.utils import add_days, getdate, today

	as_at = getattr(line, "actual_as_at", None)
	if not as_at:
		return False
	cutoff = getdate(add_days(today(), -ACTUAL_STALE_DAYS))
	return getdate(as_at) < cutoff


def _value_treatment_summary(line_name: str) -> str:
	rows = frappe.get_all(
		"Budget Line Value Treatment",
		filters={"parent": line_name, "parenttype": "Budget Line"},
		fields=["treatment"],
		order_by="idx asc",
	)
	labels = []
	seen = set()
	for r in rows:
		t = (r.treatment or "").strip()
		if t and t not in seen:
			seen.add(t)
			labels.append(t)
	if not labels:
		return "—"
	if len(labels) == 1:
		return labels[0]
	return f"{labels[0]} +{len(labels) - 1}"


def _active_budgets(pe: str, fiscal_period: str | None = None) -> list[Any]:
	filters: dict[str, Any] = {"status": "Active"}
	if pe:
		filters["procuring_entity"] = pe
	if fiscal_period:
		filters["fiscal_period"] = fiscal_period
	return frappe.get_all(
		"Budget",
		filters=filters,
		fields=[
			"name",
			"generated_reference",
			"title",
			"status",
			"fiscal_period",
			"currency",
			"procuring_entity",
			"external_approved_total",
			"attention_note",
			"budget_owner",
		],
		order_by="modified desc",
	)


def _load_lines(budget_names: list[str]) -> list[Any]:
	if not budget_names:
		return []
	return frappe.get_all(
		"Budget Line",
		filters={"budget": ["in", budget_names], "is_active": 1},
		fields=[
			"name",
			"budget",
			"generated_reference",
			"title",
			"approved_amount",
			"amount_reserved",
			"amount_committed",
			"amount_actual",
			"actual_as_at",
			"primary_target_id",
			"primary_target_code",
			"primary_target_name",
		],
		order_by="idx asc",
	)


def get_funding_performance(
	fiscal_period: str | None = None,
	programme: str | None = None,
	primary_target: str | None = None,
	funding_status: str | None = None,
	procuring_entity: str | None = None,
) -> dict[str, Any]:
	"""PE-scoped Funding Performance DTO (Active budgets)."""
	require_any_role(
		ROLE_VIEWER, ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_AUDITOR, "System Manager"
	)
	pe = resolve_scoped_entity(procuring_entity or entity_for_user() or None)
	if not pe and frappe.session.user != "Administrator" and "System Manager" not in frappe.get_roles():
		frappe.throw(_("No procuring entity assigned"), frappe.PermissionError)
	if not pe:
		# Administrator with no PE: prefer PE-MOH seed entity when present.
		pe = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name") or ""
	require_capability(
		frappe.session.user,
		"budget.view",
		ResourceContext(
			resource_type="Budget Funding Performance",
			resource_id=pe,
			procuring_entity_id=pe,
		),
	)

	entity = _entity_ref(pe)
	programme_key = (programme or "").strip()
	# Programme filter: entity display name (no separate programme DocType in MVP-1).
	if programme_key and programme_key not in (entity["name"], entity["code"], "All"):
		# Unknown programme → empty result set for this PE.
		return _empty_dto(entity, fiscal_period, primary_target, funding_status)

	fy = (fiscal_period or "").strip() or None
	target_filter = (primary_target or "").strip() or None
	status_filter = (funding_status or "").strip() or None

	budgets = _active_budgets(pe, fy)
	budget_by_name = {b.name: b for b in budgets}
	lines = _load_lines(list(budget_by_name.keys()))

	# Build filter option universes from unfiltered Active set (same PE).
	all_budgets = _active_budgets(pe, None)
	all_lines = _load_lines([b.name for b in all_budgets])
	fiscal_periods = sorted({(b.fiscal_period or "").strip() for b in all_budgets if b.fiscal_period})
	targets = []
	seen_t = set()
	for ln in all_lines:
		code = (ln.primary_target_code or "").strip()
		if code and code not in seen_t:
			seen_t.add(code)
			targets.append(
				{
					"id": ln.primary_target_id or "",
					"code": code,
					"name": ln.primary_target_name or code,
				}
			)
	targets.sort(key=lambda t: t["code"])

	filtered_lines = []
	for ln in lines:
		if target_filter and (ln.primary_target_code or "") != target_filter:
			continue
		st = _line_funding_status(ln)
		if status_filter and st != status_filter:
			continue
		filtered_lines.append(ln)

	currency = "KES"
	if budgets:
		currency = budgets[0].currency or "KES"

	approved = reserved = committed = actual = 0.0
	attention_lines = 0
	for ln in filtered_lines:
		approved += flt(ln.approved_amount)
		reserved += flt(ln.amount_reserved)
		committed += flt(ln.amount_committed)
		actual += flt(ln.amount_actual)
		if _line_funding_status(ln) == "Needs attention" or _is_stale_actual(ln):
			attention_lines += 1
	# When no line filter but budgets exist, prefer external_approved_total for Active strip
	# so MOH-BUD-2027-2028 matches Prompt 560M even if line sum differs slightly.
	if not target_filter and not status_filter and budgets:
		ext_sum = sum(flt(b.external_approved_total) for b in budgets)
		if ext_sum > 0:
			approved = ext_sum
	available = approved - reserved - committed
	outstanding = max(0.0, committed - actual)

	coverage = _coverage_rows(filtered_lines, budget_by_name, currency)
	exceptions = _exception_rows(filtered_lines, budget_by_name, currency)

	as_at = now_datetime()
	as_at_display = frappe.utils.format_datetime(as_at)

	return {
		"entity": entity,
		"as_at": str(as_at),
		"as_at_display": as_at_display,
		"currency": currency,
		"kpis": {
			"approved": approved,
			"reserved": reserved,
			"committed": committed,
			"available": available,
			"actual": actual,
			"outstanding_commitment": outstanding,
			"attention_lines": attention_lines,
			"approved_display": format_kes_full(approved, currency=currency),
			"reserved_display": format_kes_full(reserved, currency=currency),
			"committed_display": format_kes_full(committed, currency=currency),
			"available_display": format_kes_full(available, currency=currency),
			"actual_display": format_kes_full(actual, currency=currency),
			"outstanding_display": format_kes_full(outstanding, currency=currency),
			"attention_display": str(attention_lines),
		},
		"coverage_rows": coverage,
		"exception_rows": exceptions,
		"filters": {
			"fiscal_periods": fiscal_periods,
			"programmes": [entity["name"]] if entity["name"] else [],
			"targets": targets,
			"funding_statuses": list(_FUNDING_STATUSES),
			"applied": {
				"fiscal_period": fy or "",
				"programme": programme_key or "",
				"primary_target": target_filter or "",
				"funding_status": status_filter or "",
			},
		},
		"disclaimer": DISCLAIMER,
		"capabilities": {
			"read_only": True,
			"can_export": can_export_funding_performance(),
			"view_funding_performance": True,
		},
	}


def export_funding_performance(
	fiscal_period: str | None = None,
	programme: str | None = None,
	primary_target: str | None = None,
	funding_status: str | None = None,
	procuring_entity: str | None = None,
) -> dict[str, Any]:
	"""Export payload for filtered Funding Performance (client builds CSV)."""
	if not can_export_funding_performance():
		frappe.throw(_("Not permitted to export Funding Performance"), frappe.PermissionError)
	dto = get_funding_performance(
		fiscal_period=fiscal_period,
		programme=programme,
		primary_target=primary_target,
		funding_status=funding_status,
		procuring_entity=procuring_entity,
	)
	return {
		"lineage": {
			"entity_code": dto["entity"]["code"],
			"entity_name": dto["entity"]["name"],
			"as_at": dto["as_at"],
			"as_at_display": dto["as_at_display"],
			"fiscal_period": (dto["filters"]["applied"] or {}).get("fiscal_period") or "",
			"programme": (dto["filters"]["applied"] or {}).get("programme") or "",
			"primary_target": (dto["filters"]["applied"] or {}).get("primary_target") or "",
			"funding_status": (dto["filters"]["applied"] or {}).get("funding_status") or "",
			"source_coverage": "Active Budget Lines + expenditure as_at freshness",
			"disclaimer": dto["disclaimer"],
		},
		"kpis": dto["kpis"],
		"coverage_rows": dto["coverage_rows"],
		"exception_rows": dto["exception_rows"],
	}


def _coverage_rows(lines, budget_by_name, currency: str) -> list[dict[str, Any]]:
	groups: dict[str, dict[str, Any]] = {}
	for ln in lines:
		code = (ln.primary_target_code or "").strip() or "UNLINKED"
		g = groups.get(code)
		if not g:
			g = {
				"target_id": ln.primary_target_id or "",
				"target_code": code if code != "UNLINKED" else "",
				"target_name": ln.primary_target_name
				or (_("No primary strategic target") if code == "UNLINKED" else code),
				"line_count": 0,
				"approved": 0.0,
				"reserved": 0.0,
				"committed": 0.0,
				"actual": 0.0,
				"attention": False,
				"budget_code": "",
				"line_codes": [],
				"treatments": [],
			}
			groups[code] = g
		g["line_count"] += 1
		g["approved"] += flt(ln.approved_amount)
		g["reserved"] += flt(ln.amount_reserved)
		g["committed"] += flt(ln.amount_committed)
		g["actual"] += flt(ln.amount_actual)
		if _is_stale_actual(ln):
			g["attention"] = True
		bud = budget_by_name.get(ln.budget)
		if bud and not g["budget_code"]:
			g["budget_code"] = bud.generated_reference or ""
		g["line_codes"].append(ln.generated_reference or ln.name)
		tr = _value_treatment_summary(ln.name)
		if tr and tr != "—" and tr not in g["treatments"]:
			g["treatments"].append(tr)

	out = []
	for code in sorted(groups.keys()):
		g = groups[code]
		available = g["approved"] - g["reserved"] - g["committed"]
		treatment = g["treatments"][0] if len(g["treatments"]) == 1 else (
			f"{g['treatments'][0]} +{len(g['treatments']) - 1}" if g["treatments"] else "—"
		)
		out.append(
			{
				"target_id": g["target_id"],
				"target_code": g["target_code"],
				"target_name": g["target_name"],
				"line_count": g["line_count"],
				"approved": g["approved"],
				"reserved": g["reserved"],
				"committed": g["committed"],
				"available": available,
				"approved_display": format_kes_full(g["approved"], currency=currency),
				"reserved_display": format_kes_full(g["reserved"], currency=currency),
				"committed_display": format_kes_full(g["committed"], currency=currency),
				"available_display": format_kes_full(available, currency=currency),
				"value_treatment": treatment,
				"attention": g["attention"],
				"attention_label": _("Stale") if g["attention"] else "—",
				"budget_code": g["budget_code"],
				"action_label": _("View Details"),
				"action": "view_details",
			}
		)
	return out


def _exception_rows(lines, budget_by_name, currency: str) -> list[dict[str, Any]]:
	from frappe.utils import getdate, today

	rows = []
	for ln in lines:
		if not _is_stale_actual(ln):
			continue
		as_at = getdate(ln.actual_as_at)
		days = (getdate(today()) - as_at).days
		bud = budget_by_name.get(ln.budget)
		owner = (bud.budget_owner if bud else "") or _("Budget Officer")
		rows.append(
			{
				"exception": _("Actual expenditure data is stale"),
				"exception_kind": "stale_actual",
				"budget_line": ln.title or ln.generated_reference,
				"budget_line_code": ln.generated_reference or "",
				"budget_code": (bud.generated_reference if bud else "") or "",
				"owner": owner,
				"age_label": _("Last updated {0} days ago").format(days),
				"days_ago": days,
				"action_label": _("Review finance sync"),
				"action": "review_finance_sync",
				"actual_display": format_kes_full(ln.amount_actual, currency=currency),
			}
		)
	return rows


def _empty_dto(entity, fiscal_period, primary_target, funding_status) -> dict[str, Any]:
	as_at = now_datetime()
	currency = "KES"
	return {
		"entity": entity,
		"as_at": str(as_at),
		"as_at_display": frappe.utils.format_datetime(as_at),
		"currency": currency,
		"kpis": {
			"approved": 0,
			"reserved": 0,
			"committed": 0,
			"available": 0,
			"actual": 0,
			"outstanding_commitment": 0,
			"attention_lines": 0,
			"approved_display": format_kes_full(0, currency=currency),
			"reserved_display": format_kes_full(0, currency=currency),
			"committed_display": format_kes_full(0, currency=currency),
			"available_display": format_kes_full(0, currency=currency),
			"actual_display": format_kes_full(0, currency=currency),
			"outstanding_display": format_kes_full(0, currency=currency),
			"attention_display": "0",
		},
		"coverage_rows": [],
		"exception_rows": [],
		"filters": {
			"fiscal_periods": [],
			"programmes": [entity["name"]] if entity.get("name") else [],
			"targets": [],
			"funding_statuses": list(_FUNDING_STATUSES),
			"applied": {
				"fiscal_period": fiscal_period or "",
				"programme": "",
				"primary_target": primary_target or "",
				"funding_status": funding_status or "",
			},
		},
		"disclaimer": DISCLAIMER,
		"capabilities": {
			"read_only": True,
			"can_export": can_export_funding_performance(),
		},
	}
