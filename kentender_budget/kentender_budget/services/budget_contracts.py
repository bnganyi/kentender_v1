# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget portfolio / register contracts — BUD-UI-01 / BUD-FR-001–010 / Phase 2."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate

from kentender_budget.services.budget_permissions import (
	can_register_budget,
	can_review_budget,
	entity_for_user,
	require_any_role,
	user_roles,
	visible_statuses_for_user,
	ROLE_AUDITOR,
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
)
from kentender_budget.services.budget_reference import allocate_budget_reference
from kentender_budget.services.budget_authorization import (
	CAP_BUDGET_CREATE,
	CAP_BUDGET_EDIT,
	CAP_BUDGET_LIST,
	CAP_BUDGET_REVIEW,
	CAP_BUDGET_VIEW,
	authorized_budget_task,
	can_budget,
	require_budget_capability,
)

_FY_RE = re.compile(r"^(\d{4})/(\d{2})$")
_BLOCKING_STATUSES = ("Draft", "Submitted", "Returned", "Active")
_DEFAULT_FISCAL_PERIODS = (
	"2028/29",
	"2027/28",
	"2026/27",
	"2029/30",
	"2030/31",
	"2031/32",
	"2032/33",
	"2039/40",
	"2040/41",
	"2041/42",
	"2042/43",
	"2043/44",
)

# UI label for Submitted (pack Phase 1).
_STATUS_UI = {
	"Submitted": "Under review",
}

_SOURCE_UI = {
	"Direct capture": "Direct capture",
}


def _entity_label(pe_name: str | None) -> str:
	if not pe_name:
		return ""
	return (
		frappe.db.get_value("Procuring Entity", pe_name, "entity_name")
		or frappe.db.get_value("Procuring Entity", pe_name, "entity_code")
		or pe_name
	)


def format_kes_compact(amount: float | None, *, currency: str = "KES") -> str:
	"""Compact money for portfolio table (Stitch: KES 560M)."""
	val = flt(amount)
	if abs(val) >= 1_000_000:
		m = val / 1_000_000.0
		if abs(m - round(m)) < 0.05:
			return f"{currency} {int(round(m))}M"
		text = f"{m:.1f}".rstrip("0").rstrip(".")
		return f"{currency} {text}M"
	return f"{currency} {val:,.0f}"


def resolve_scoped_entity(
	requested: str | None = None,
	*,
	user_entity: str | None = None,
	roles: set[str] | None = None,
) -> str:
	"""BUD-FR-001/002 — hard entity scope; no unscoped / cross-entity list for officers."""
	explicit_roles = roles is not None
	roles = roles if roles is not None else user_roles()
	user_pe = user_entity if user_entity is not None else entity_for_user()
	req = (requested or "").strip() or None
	is_admin = "System Manager" in roles or "Administrator" in roles
	# When roles are injected (unit tests), do not also trust session Administrator.
	if not explicit_roles and frappe.session.user == "Administrator":
		is_admin = True
	if is_admin:
		return req or user_pe or ""
	if not user_pe:
		frappe.throw(_("No procuring entity assigned"), frappe.PermissionError)
	if req and req != user_pe:
		frappe.throw(_("Not permitted for this procuring entity"), frappe.PermissionError)
	return user_pe


def _line_totals(budget_name: str) -> dict[str, float]:
	rows = frappe.get_all(
		"Budget Line",
		filters={"budget": budget_name, "is_active": 1},
		fields=[
			"approved_amount",
			"amount_reserved",
			"amount_committed",
			"amount_actual",
			"primary_strategy_linked",
		],
	)
	approved = reserved = committed = actual = 0.0
	lines_total = 0
	lines_strategy_linked = 0
	for r in rows:
		approved += flt(r.approved_amount)
		reserved += flt(r.amount_reserved)
		committed += flt(r.amount_committed)
		actual += flt(getattr(r, "amount_actual", None))
		lines_total += 1
		if int(getattr(r, "primary_strategy_linked", 0) or 0):
			lines_strategy_linked += 1
	available = approved - reserved - committed
	outstanding = max(0.0, committed - actual)
	return {
		"approved": approved,
		"reserved": reserved,
		"committed": committed,
		"available": available,
		"actual": actual,
		"outstanding": outstanding,
		"lines_total": float(lines_total),
		"lines_strategy_linked": float(lines_strategy_linked),
	}


def _attention(row) -> dict[str, Any]:
	note = (row.attention_note or "").strip()
	issues = int(row.readiness_issue_count or 0)
	if note:
		return {
			"attention": note,
			"attention_kind": "warning",
			"has_exception": True,
		}
	if issues > 0:
		label = f"{issues} readiness issue{'s' if issues != 1 else ''}"
		return {
			"attention": label,
			"attention_kind": "info",
			"has_exception": True,
		}
	return {
		"attention": "None",
		"attention_kind": "none",
		"has_exception": False,
	}


def _action_for_status(status: str) -> dict[str, Any]:
	if status == "Active":
		return {"action": "open", "action_label": "Open", "action_muted": False}
	if status == "Submitted":
		return {"action": "review", "action_label": "Review", "action_muted": False}
	if status in ("Draft", "Returned"):
		return {"action": "open", "action_label": "Open", "action_muted": False}
	# Closed / Cancelled — Stitch muted View.
	return {"action": "view", "action_label": "View", "action_muted": True}


def _available_display(status: str, available: float, currency: str) -> str:
	# Stitch: Active shows remaining; Submitted "Not active"; Closed "KES 0".
	if status == "Active":
		return format_kes_compact(available, currency=currency)
	if status == "Closed":
		return format_kes_compact(available, currency=currency)
	return "Not active"


def _approved_for_portfolio(row, line_approved: float) -> float:
	"""Portfolio APPROVED = registered baseline (external), not line allocation sum.

	Drafts from Register have external_approved_total but no Budget Lines yet — using
	line totals alone showed KES 0 after a successful save.
	"""
	header = flt(getattr(row, "external_approved_total", None))
	if header > 0:
		return header
	return flt(line_approved)


def _row_dto(row) -> dict[str, Any]:
	totals = _line_totals(row.name)
	attn = _attention(row)
	action = {"action": "", "action_label": "", "action_muted": True}
	if can_budget(CAP_BUDGET_VIEW, row):
		action = {"action": "view", "action_label": "View", "action_muted": True}
	if row.status in ("Draft", "Returned") and can_budget(CAP_BUDGET_EDIT, row):
		action = {"action": "open", "action_label": "Open", "action_muted": False}
	elif row.status == "Active" and can_budget(CAP_BUDGET_VIEW, row):
		action = {"action": "open", "action_label": "Open", "action_muted": False}
	elif row.status == "Submitted":
		task, commands = authorized_budget_task(
			actor=frappe.session.user,
			subject_type="Budget",
			subject_id=row.name,
			capabilities=(CAP_BUDGET_REVIEW,),
		)
		if task and commands:
			action = {"action": "review", "action_label": "Review", "action_muted": False, "task_id": task.name}
	status_ui = _STATUS_UI.get(row.status, row.status)
	source_ui = _SOURCE_UI.get(row.registration_source, row.registration_source or "Direct capture")
	currency = row.currency or "KES"
	approved = _approved_for_portfolio(row, totals["approved"])
	return {
		"id": row.name,
		"code": row.generated_reference,
		"name": row.title,
		"title": row.title,
		"procuring_entity": row.procuring_entity,
		"procuring_entity_name": _entity_label(row.procuring_entity),
		"fiscal_period": row.fiscal_period,
		"start_date": row.start_date,
		"end_date": row.end_date,
		"currency": currency,
		"budget_owner": row.budget_owner,
		"registration_source": row.registration_source,
		"registration_source_label": source_ui,
		"authoritative_reference": row.authoritative_reference,
		"status": row.status,
		"status_label": status_ui,
		"approved_amount": approved,
		"available_amount": totals["available"],
		"approved_display": format_kes_compact(approved, currency=currency),
		"available_display": _available_display(row.status, totals["available"], currency),
		**attn,
		**action,
	}


def list_budgets(
	procuring_entity: str | None = None,
	status: str | None = None,
	fiscal_period: str | None = None,
	search: str | None = None,
	registration_source: str | None = None,
) -> list[dict[str, Any]]:
	"""BUD-FR-001 / list_budgets — entity-scoped Budget portfolio rows."""
	require_any_role(
		ROLE_VIEWER, ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_AUDITOR, "System Manager"
	)
	pe = resolve_scoped_entity(procuring_entity)
	filters: dict[str, Any] = {}
	if pe:
		filters["procuring_entity"] = pe

	status_val = (status or "").strip()
	if status_val and status_val not in ("All Statuses", "All", "Status"):
		if status_val == "Under review":
			filters["status"] = "Submitted"
		else:
			filters["status"] = status_val
	else:
		allowed = visible_statuses_for_user()
		if allowed:
			filters["status"] = ["in", allowed]

	period_val = (fiscal_period or "").strip()
	if period_val and period_val not in ("All Periods", "All", "Fiscal Period"):
		period_norm = period_val.replace("FY ", "").strip()
		filters["fiscal_period"] = ["like", f"%{period_norm}%"]

	source_val = (registration_source or "").strip()
	if source_val and source_val not in ("All Sources", "All", "Source"):
		if source_val in ("Manual registration", "Direct capture"):
			filters["registration_source"] = "Direct capture"
		elif source_val == "Controlled import":
			filters["registration_source"] = "__none__"

	or_filters = None
	if search and search.strip():
		q = search.strip()
		or_filters = [
			["title", "like", f"%{q}%"],
			["authoritative_reference", "like", f"%{q}%"],
			["generated_reference", "like", f"%{q}%"],
		]

	rows = frappe.get_all(
		"Budget",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"generated_reference",
			"title",
			"procuring_entity",
			"fiscal_period",
			"start_date",
			"end_date",
			"currency",
			"budget_owner",
			"registration_source",
			"authoritative_reference",
			"status",
			"external_approved_total",
			"attention_note",
			"readiness_issue_count",
		],
		order_by="fiscal_period desc, modified desc",
		limit_page_length=200,
	)
	return [_row_dto(r) for r in rows if can_budget(CAP_BUDGET_LIST, r) and can_budget(CAP_BUDGET_VIEW, r)]


def get_budget_portfolio(procuring_entity: str | None = None) -> dict[str, Any]:
	"""Portfolio strip counts + capabilities for BUD-UI-01."""
	require_any_role(
		ROLE_VIEWER, ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_AUDITOR, "System Manager"
	)
	pe = resolve_scoped_entity(procuring_entity)
	filters: dict[str, Any] = {}
	if pe:
		filters["procuring_entity"] = pe
	allowed = visible_statuses_for_user()
	if allowed:
		filters["status"] = ["in", allowed]
	rows = frappe.get_all(
		"Budget",
		filters=filters,
		fields=["name", "procuring_entity", "fiscal_period", "status", "attention_note", "readiness_issue_count"],
	)
	counts = {
		"active": 0,
		"awaiting_review": 0,
		"returned": 0,
		"funding_exceptions": 0,
		"draft": 0,
		"closed": 0,
	}
	rows = [r for r in rows if can_budget(CAP_BUDGET_LIST, r) and can_budget(CAP_BUDGET_VIEW, r)]
	for r in rows:
		st = r.status or ""
		if st == "Active":
			counts["active"] += 1
		elif st == "Submitted":
			counts["awaiting_review"] += 1
		elif st == "Returned":
			counts["returned"] += 1
		elif st == "Draft":
			counts["draft"] += 1
		elif st == "Closed":
			counts["closed"] += 1
		note = (r.attention_note or "").strip()
		issues = int(r.readiness_issue_count or 0)
		if note or issues > 0:
			counts["funding_exceptions"] += 1

	return {
		"procuring_entity": pe,
		"procuring_entity_name": _entity_label(pe),
		"counts": counts,
		"capabilities": {
			"register_budget": bool(pe) and can_budget(CAP_BUDGET_CREATE, frappe._dict(name=pe, procuring_entity=pe, fiscal_period="", status="")),
			"review_budget": any((row.status == "Submitted" and _row_dto(row).get("action") == "review") for row in rows),
			"view_funding_performance": bool(rows),
		},
		"budgets": list_budgets(procuring_entity=pe),
	}


def normalize_fiscal_period(raw: str | None) -> str:
	"""Normalize `FY 2028/29` → `2028/29`."""
	text = (raw or "").strip()
	if text.upper().startswith("FY "):
		text = text[3:].strip()
	return text


def fiscal_period_dates(fiscal_period: str) -> tuple[str, str]:
	"""Kenya FY July–June: `2028/29` → 2028-07-01 … 2029-06-30."""
	norm = normalize_fiscal_period(fiscal_period)
	match = _FY_RE.match(norm)
	if not match:
		frappe.throw(_("Fiscal period must look like 2028/29"), frappe.ValidationError)
	start_year = int(match.group(1))
	end_yy = int(match.group(2))
	expected_yy = (start_year + 1) % 100
	if end_yy != expected_yy:
		frappe.throw(_("Fiscal period year pair is inconsistent"), frappe.ValidationError)
	end_year = start_year + 1
	return f"{start_year:04d}-07-01", f"{end_year:04d}-06-30"


def parse_money_amount(raw: Any) -> float | None:
	"""Parse approved total with optional thousands separators."""
	if raw is None:
		return None
	if isinstance(raw, (int, float)):
		return float(raw)
	text = str(raw).strip().replace(",", "").replace(" ", "")
	if not text:
		return None
	try:
		return float(text)
	except ValueError:
		return None


def _entity_ref(pe_name: str | None) -> dict[str, str] | None:
	if not pe_name:
		return None
	code = frappe.db.get_value("Procuring Entity", pe_name, "entity_code") or pe_name
	return {
		"id": pe_name,
		"code": str(code),
		"name": _entity_label(pe_name),
	}


def get_register_form_context() -> dict[str, Any]:
	"""Defaults for Register approved budget focused page."""
	if not can_register_budget():
		frappe.throw(_("Not permitted to register budgets"), frappe.PermissionError)
	pe = resolve_scoped_entity(None)
	periods = []
	for value in _DEFAULT_FISCAL_PERIODS:
		periods.append({"value": value, "label": f"FY {value}"})
	currencies = [c for c in ("KES", "USD") if frappe.db.exists("Currency", c)]
	if not currencies:
		currencies = ["KES"]
	return {
		"capabilities": {"register_budget": True},
		"procuring_entity": _entity_ref(pe),
		"fiscal_periods": periods,
		"currencies": currencies,
		"defaults": {
			"currency": "KES" if "KES" in currencies else currencies[0],
			"fiscal_period": "2028/29",
			"budget_owner": "",
			"title": "",
		},
	}


def _validate_register_payload(payload: dict) -> dict[str, str]:
	errors: dict[str, str] = {}
	title = (payload.get("title") or "").strip()
	fiscal_period = normalize_fiscal_period(payload.get("fiscal_period"))
	currency = (payload.get("currency") or "").strip()
	budget_owner = (payload.get("budget_owner") or "").strip()
	authoritative = (payload.get("authoritative_reference") or "").strip()
	approval_date = payload.get("approval_date")
	total = parse_money_amount(payload.get("external_approved_total"))

	if not title:
		errors["title"] = _("Budget title is required")
	if not fiscal_period:
		errors["fiscal_period"] = _("Fiscal period is required")
	elif not _FY_RE.match(fiscal_period):
		errors["fiscal_period"] = _("Fiscal period must look like 2028/29")
	else:
		try:
			fiscal_period_dates(fiscal_period)
		except Exception:
			errors["fiscal_period"] = _("Fiscal period is not valid")

	if not currency:
		errors["currency"] = _("Currency is required")
	elif not frappe.db.exists("Currency", currency):
		errors["currency"] = _("Currency is not valid")

	if not budget_owner:
		errors["budget_owner"] = _("Budget owner is required")
	if not authoritative:
		errors["authoritative_reference"] = _("External approval reference is required")
	if not approval_date:
		errors["approval_date"] = _("Approval date is required")
	else:
		try:
			getdate(approval_date)
		except Exception:
			errors["approval_date"] = _("Enter a valid approval date")

	if total is None:
		errors["external_approved_total"] = _("Approved total is required")
	elif total <= 0:
		errors["external_approved_total"] = _("Approved total must be greater than zero")

	# Approval evidence is optional at Draft registration (may be attached later).

	return errors


def _blocking_budget_for_period(pe: str, fiscal_period: str) -> str | None:
	"""Return generated_reference of Draft/Active/… aggregate for entity+period, if any."""
	norm = normalize_fiscal_period(fiscal_period)
	row = frappe.db.get_value(
		"Budget",
		{
			"procuring_entity": pe,
			"fiscal_period": norm,
			"status": ["in", list(_BLOCKING_STATUSES)],
		},
		["generated_reference", "status"],
		as_dict=True,
	)
	if not row:
		return None
	return row.generated_reference


def _budget_dto(doc) -> dict[str, Any]:
	return {
		"id": doc.name,
		"code": doc.generated_reference,
		"name": doc.title,
		"title": doc.title,
		"status": doc.status,
		"procuring_entity": doc.procuring_entity,
		"procuring_entity_name": _entity_label(doc.procuring_entity),
		"fiscal_period": doc.fiscal_period,
		"start_date": doc.start_date,
		"end_date": doc.end_date,
		"currency": doc.currency,
		"budget_owner": doc.budget_owner,
		"registration_source": doc.registration_source,
		"authoritative_reference": doc.authoritative_reference,
		"approval_date": doc.approval_date,
		"external_approved_total": flt(doc.external_approved_total),
		"approval_evidence": doc.approval_evidence,
	}


def register_budget(payload: dict | None = None) -> dict[str, Any]:
	"""Create a Draft Budget via direct capture (BUD-FR-003–006). No lines."""
	if not can_register_budget():
		frappe.throw(_("Not permitted to register budgets"), frappe.PermissionError)

	payload = payload or {}
	errors = _validate_register_payload(payload)
	if errors:
		return {"ok": False, "errors": errors}

	pe = resolve_scoped_entity((payload.get("procuring_entity") or "").strip() or None)
	if not pe:
		return {"ok": False, "errors": {"procuring_entity": _("Procuring entity is required")}}

	fiscal_period = normalize_fiscal_period(payload.get("fiscal_period"))
	blocking = _blocking_budget_for_period(pe, fiscal_period)
	if blocking:
		return {
			"ok": False,
			"errors": {
				"fiscal_period": _(
					"A Draft, Submitted, Returned or Active budget already exists for this entity and fiscal period ({0})"
				).format(blocking)
			},
		}

	start_date, end_date = fiscal_period_dates(fiscal_period)
	# Optional client dates must match derived FY bounds when provided.
	if payload.get("start_date") and str(getdate(payload.get("start_date"))) != start_date:
		return {
			"ok": False,
			"errors": {"start_date": _("Start date must match the selected fiscal period")},
		}
	if payload.get("end_date") and str(getdate(payload.get("end_date"))) != end_date:
		return {
			"ok": False,
			"errors": {"end_date": _("End date must match the selected fiscal period")},
		}

	total = parse_money_amount(payload.get("external_approved_total"))
	# Ignore any client-supplied generated_reference / code (BUD-FR-003).
	ref = allocate_budget_reference(pe)
	doc = frappe.get_doc(
		{
			"doctype": "Budget",
			"generated_reference": ref,
			"title": (payload.get("title") or "").strip(),
			"procuring_entity": pe,
			"status": "Draft",
			"fiscal_period": fiscal_period,
			"start_date": start_date,
			"end_date": end_date,
			"currency": (payload.get("currency") or "KES").strip(),
			"budget_owner": (payload.get("budget_owner") or "").strip(),
			"registration_source": "Direct capture",
			"authoritative_reference": (payload.get("authoritative_reference") or "").strip(),
			"approval_date": getdate(payload.get("approval_date")),
			"external_approved_total": total,
			"approval_evidence": (payload.get("approval_evidence") or "").strip(),
		}
	)
	doc.insert()
	try:
		from kentender_budget.services.budget_audit_contracts import (
			EVENT_BASELINE,
			safe_record_event,
		)

		safe_record_event(
			budget=doc.name,
			event_type=EVENT_BASELINE,
			record_code=doc.generated_reference,
			record_doctype="Budget",
			actor=frappe.session.user,
			actor_kind="user",
			before_summary="",
			after_summary="Initial baseline",
			change_summary="Initial baseline",
			source_reference=doc.authoritative_reference or "",
		)
	except Exception:
		pass
	return {"ok": True, "budget": _budget_dto(doc)}


def _resolve_budget(budget: str):
	"""Resolve Budget by generated_reference or document name."""
	key = (budget or "").strip()
	if not key:
		frappe.throw(_("Budget is required"), frappe.ValidationError)
	name = frappe.db.get_value("Budget", {"generated_reference": key}, "name")
	if not name and frappe.db.exists("Budget", key):
		name = key
	if not name:
		frappe.throw(_("Budget {0} not found").format(key), frappe.DoesNotExistError)
	return frappe.get_doc("Budget", name)


def _overview_capabilities(status: str) -> dict[str, Any]:
	"""Status-aware header CTAs for Budget workspace Overview."""
	if status == "Active":
		return {
			"primary_action": "request_revision",
			"primary_label": "Request revision",
			"view_funding_performance": True,
			"open_lines": True,
		}
	if status in ("Draft", "Returned"):
		return {
			"primary_action": "open_lines",
			"primary_label": "Budget lines",
			"view_funding_performance": True,
			"open_lines": True,
		}
	return {
		"primary_action": "view_funding_performance",
		"primary_label": "View funding performance",
		"view_funding_performance": True,
		"open_lines": True,
	}


def _utilization_bar(approved: float, reserved: float, committed: float, available: float) -> dict[str, Any]:
	base = approved if approved > 0 else 1.0
	r_pct = round((reserved / base) * 100.0, 2)
	c_pct = round((committed / base) * 100.0, 2)
	a_pct = round(max(0.0, 100.0 - r_pct - c_pct), 2)
	return {
		"reserved_pct": r_pct,
		"committed_pct": c_pct,
		"available_pct": a_pct,
		"total_pct": 100.0,
		"total_display": format_kes_compact(approved),
	}


def get_budget_overview(budget: str) -> dict[str, Any]:
	"""BUD-UI-03 — entity-scoped Overview DTO with derived funding totals."""
	require_any_role(
		ROLE_VIEWER, ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_AUDITOR, "System Manager"
	)
	doc = _resolve_budget(budget)
	require_budget_capability(CAP_BUDGET_VIEW, doc)
	# Hard PE scope for non-admin session users.
	resolve_scoped_entity(doc.procuring_entity)

	line = _line_totals(doc.name)
	currency = doc.currency or "KES"
	approved = _approved_for_portfolio(doc, line["approved"])
	reserved = line["reserved"]
	committed = line["committed"]
	available = approved - reserved - committed
	actual = line["actual"]
	outstanding = max(0.0, committed - actual)
	status_ui = _STATUS_UI.get(doc.status, doc.status)
	source_ui = _SOURCE_UI.get(doc.registration_source, doc.registration_source or "Direct capture")
	attn = _attention(doc)
	lines_total = int(line["lines_total"])
	lines_linked = int(line["lines_strategy_linked"])
	pvc_treated = int(getattr(doc, "strategy_pvc_treated", 0) or 0)
	pvc_applicable = int(getattr(doc, "strategy_pvc_applicable", 0) or 0)

	return {
		"id": doc.name,
		"code": doc.generated_reference,
		"name": doc.title,
		"title": doc.title,
		"status": doc.status,
		"status_label": status_ui,
		"procuring_entity": _entity_ref(doc.procuring_entity),
		"fiscal_period": doc.fiscal_period,
		"fiscal_period_label": f"FY {doc.fiscal_period}" if doc.fiscal_period else "",
		"currency": currency,
		"registration_source": doc.registration_source,
		"registration_source_label": source_ui,
		"authoritative_reference": doc.authoritative_reference or "",
		"budget_owner": doc.budget_owner or "",
		"approval_date": str(doc.approval_date) if doc.approval_date else "",
		"last_synchronised": None,
		"totals": {
			"approved": approved,
			"reserved": reserved,
			"committed": committed,
			"available": available,
			"actual": actual,
			"outstanding": outstanding,
			"approved_display": format_kes_compact(approved, currency=currency),
			"reserved_display": format_kes_compact(reserved, currency=currency),
			"committed_display": format_kes_compact(committed, currency=currency),
			"available_display": format_kes_compact(available, currency=currency),
			"actual_display": format_kes_compact(actual, currency=currency),
			"outstanding_display": format_kes_compact(outstanding, currency=currency),
		},
		"utilization_bar": _utilization_bar(approved, reserved, committed, available),
		"strategy": {
			"lines_linked": lines_linked,
			"lines_total": lines_total,
			"lines_summary": f"{lines_linked} of {lines_total} lines linked to an Active primary target",
			"pvc_treated": pvc_treated,
			"pvc_applicable": pvc_applicable,
			"pvc_summary": f"{pvc_treated} applicable Strategy Value Commitments treated",
		},
		"attention": {
			"kind": attn["attention_kind"],
			"text": attn["attention"] if attn["attention"] != "None" else "",
			"has_exception": attn["has_exception"],
		},
		"definitional_note": (
			"Available equals approved funding less active reservations and contract commitments. "
			"Actual expenditure is shown separately because it is already included within commitments."
		),
		"capabilities": _overview_capabilities(doc.status),
	}
