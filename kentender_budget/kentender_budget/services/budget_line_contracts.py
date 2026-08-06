# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget Lines / Line Editor contracts — BUD-UI-04 / BUD-UI-05 / BUD-FR-015–042."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, today

from kentender_budget.services.budget_contracts import (
	_resolve_budget,
	format_kes_compact,
	resolve_scoped_entity,
)
from kentender_budget.services.budget_permissions import (
	ROLE_AUDITOR,
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	require_any_role,
)
from kentender_budget.services.budget_reference import allocate_budget_line_reference

ACTUAL_STALE_DAYS = 2
_EDITABLE_STATUSES = ("Draft", "Returned")
_TREATMENTS_NEEDING_RATIONALE = ("No direct allocation required", "Not applicable")
_DEDICATED = "Dedicated allocation"


def format_kes_full(amount: float | None, *, currency: str = "KES") -> str:
	"""Full money with thousands separators (table / drawer): KES 480,000,000."""
	return f"{currency} {flt(amount):,.0f}"


def _lines_capabilities(status: str) -> dict[str, Any]:
	if status == "Active":
		return {
			"primary_action": "request_revision",
			"primary_label": "Request revision",
			"can_add_line": False,
			"can_edit_lines": False,
			"view_funding_performance": True,
		}
	if status in _EDITABLE_STATUSES:
		return {
			"primary_action": "add_line",
			"primary_label": "Add budget line",
			"can_add_line": True,
			"can_edit_lines": True,
			"view_funding_performance": True,
		}
	return {
		"primary_action": "view_funding_performance",
		"primary_label": "View funding performance",
		"can_add_line": False,
		"can_edit_lines": False,
		"view_funding_performance": True,
	}


def _actual_freshness(amount_actual, actual_as_at) -> dict[str, Any]:
	"""BUD-FR-082 — Fresh / Stale / Unknown (never fake zero when unknown)."""
	as_at = getdate(actual_as_at) if actual_as_at else None
	if as_at is None:
		return {
			"freshness": "Unknown",
			"label": "Unknown",
			"display": "Unknown",
			"days_ago": None,
			"has_value": False,
		}
	cutoff = getdate(add_days(today(), -ACTUAL_STALE_DAYS))
	days_ago = (getdate(today()) - as_at).days
	if as_at < cutoff:
		return {
			"freshness": "Stale",
			"label": "Stale",
			"display": format_kes_full(amount_actual),
			"days_ago": days_ago,
			"has_value": True,
		}
	return {
		"freshness": "Fresh",
		"label": "Fresh",
		"display": format_kes_full(amount_actual),
		"days_ago": days_ago,
		"has_value": True,
	}


def _funding_condition(approved: float, reserved: float, committed: float, available: float) -> str:
	"""BUD-FR-022 — derived funding condition."""
	if available <= 0:
		return "Exhausted"
	if reserved <= 0 and committed <= 0:
		return "Available"
	return "Partially available"


def _line_attention(
	*,
	freshness: dict[str, Any],
	reserved: float,
	committed: float,
	budget_status: str,
) -> dict[str, Any]:
	if freshness["freshness"] == "Stale":
		days = freshness.get("days_ago")
		text = (
			f"Actuals last synchronised {days} days ago"
			if days is not None
			else "Actual expenditure is stale"
		)
		return {
			"status_label": "Needs attention",
			"status_kind": "attention",
			"attention": text,
			"has_exception": True,
		}
	if freshness["freshness"] == "Unknown" and reserved <= 0 and committed <= 0:
		return {
			"status_label": "Complete",
			"status_kind": "complete",
			"attention": "No commitments or expenditure recorded",
			"has_exception": False,
		}
	return {
		"status_label": "Complete",
		"status_kind": "complete",
		"attention": "",
		"has_exception": False,
	}


def _line_action(budget_status: str, attention: dict[str, Any], can_edit: bool) -> dict[str, Any]:
	if can_edit:
		return {"action": "edit", "action_label": "Edit line", "action_icon": "edit"}
	if attention.get("has_exception"):
		return {"action": "review", "action_label": "Review line", "action_icon": "manage_search"}
	return {"action": "view", "action_label": "View line", "action_icon": "visibility"}


def _target_ref(doc) -> dict[str, Any] | None:
	code = (getattr(doc, "primary_target_code", None) or "").strip()
	if not code:
		return None
	return {
		"id": getattr(doc, "primary_target_id", None) or "",
		"code": code,
		"name": getattr(doc, "primary_target_name", None) or code,
		"plan_version_id": getattr(doc, "primary_plan_version_id", None) or "",
		"snapshot_label": getattr(doc, "primary_snapshot_label", None) or "",
	}


def _supporting_dtos(doc) -> list[dict[str, Any]]:
	out = []
	for row in doc.get("supporting_targets") or []:
		out.append(
			{
				"id": row.target_id or "",
				"code": row.target_code or "",
				"name": row.target_name or "",
				"plan_version_id": row.plan_version_id or "",
				"snapshot_label": row.snapshot_label or "",
				"reason": row.reason or "",
			}
		)
	return out


def _treatment_dtos(doc) -> list[dict[str, Any]]:
	out = []
	for row in doc.get("value_treatments") or []:
		out.append(
			{
				"id": row.pvc_id or "",
				"code": row.pvc_code or "",
				"name": row.pvc_name or "",
				"requirement_level": row.requirement_level or "",
				"treatment": row.treatment or "",
				"dedicated_amount": flt(row.dedicated_amount),
				"dedicated_display": format_kes_full(row.dedicated_amount)
				if flt(row.dedicated_amount) > 0
				else "",
				"rationale": row.rationale or "",
				"reviewer_accepted": int(row.reviewer_accepted or 0),
			}
		)
	return out


def _dedicated_total(treatments: list[dict[str, Any]]) -> float:
	total = 0.0
	for t in treatments:
		if (t.get("treatment") or "") == _DEDICATED:
			total += flt(t.get("dedicated_amount"))
	return total


def _resolve_line(line: str):
	key = (line or "").strip()
	if not key:
		frappe.throw(_("Budget Line is required"), frappe.ValidationError)
	name = frappe.db.get_value("Budget Line", {"generated_reference": key}, "name")
	if not name and frappe.db.exists("Budget Line", key):
		name = key
	if not name:
		frappe.throw(_("Budget Line {0} not found").format(key), frappe.DoesNotExistError)
	return frappe.get_doc("Budget Line", name)


def _line_list_dto(doc, budget_status: str, currency: str) -> dict[str, Any]:
	approved = flt(doc.approved_amount)
	reserved = flt(doc.amount_reserved)
	committed = flt(doc.amount_committed)
	available = approved - reserved - committed
	freshness = _actual_freshness(doc.amount_actual, doc.actual_as_at)
	condition = _funding_condition(approved, reserved, committed, available)
	attn = _line_attention(
		freshness=freshness,
		reserved=reserved,
		committed=committed,
		budget_status=budget_status,
	)
	can_edit = budget_status in _EDITABLE_STATUSES
	action = _line_action(budget_status, attn, can_edit)
	primary = _target_ref(doc)
	return {
		"id": doc.name,
		"code": doc.generated_reference,
		"name": doc.title,
		"title": doc.title,
		"funding_source_type": doc.funding_source_type,
		"funding_source_name": doc.funding_source_name or "",
		"classification": getattr(doc, "classification", None) or "",
		"organisational_owner": doc.organisational_owner,
		"primary_target": primary,
		"primary_target_label": (primary or {}).get("name") or "—",
		"primary_target_code": (primary or {}).get("code") or "",
		"approved": approved,
		"reserved": reserved,
		"committed": committed,
		"available": available,
		"actual": flt(doc.amount_actual) if freshness["has_value"] else None,
		"approved_display": format_kes_full(approved, currency=currency),
		"reserved_display": format_kes_full(reserved, currency=currency),
		"committed_display": format_kes_full(committed, currency=currency),
		"available_display": format_kes_full(available, currency=currency),
		"actual_display": freshness["display"],
		"actual_freshness": freshness["freshness"],
		"actual_freshness_label": freshness["label"],
		"condition": condition,
		"status_label": attn["status_label"],
		"status_kind": attn["status_kind"],
		"attention": attn["attention"],
		"has_exception": attn["has_exception"],
		**action,
	}


def list_budget_lines(budget: str) -> dict[str, Any]:
	"""BUD-UI-04 — entity-scoped Budget Lines table DTO."""
	require_any_role(
		ROLE_VIEWER, ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_AUDITOR, "System Manager"
	)
	doc = _resolve_budget(budget)
	resolve_scoped_entity(doc.procuring_entity)
	currency = doc.currency or "KES"
	rows = frappe.get_all(
		"Budget Line",
		filters={"budget": doc.name, "is_active": 1},
		fields=["name"],
		order_by="order_index asc, creation asc",
	)
	lines = []
	for r in rows:
		line = frappe.get_doc("Budget Line", r.name)
		lines.append(_line_list_dto(line, doc.status, currency))
	return {
		"budget": {
			"id": doc.name,
			"code": doc.generated_reference,
			"name": doc.title,
			"title": doc.title,
			"status": doc.status,
			"status_label": "Under review" if doc.status == "Submitted" else doc.status,
			"currency": currency,
			"procuring_entity": doc.procuring_entity,
		},
		"lines": lines,
		"line_count": len(lines),
		"pagination": {
			"showing_from": 1 if lines else 0,
			"showing_to": len(lines),
			"total": len(lines),
			"label": f"Showing 1-{len(lines)} of {len(lines)} lines" if lines else "Showing 0 of 0 lines",
		},
		"capabilities": _lines_capabilities(doc.status),
	}


def get_budget_line(line: str) -> dict[str, Any]:
	"""BUD-UI-05 — full editor DTO + capabilities."""
	require_any_role(
		ROLE_VIEWER, ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_AUDITOR, "System Manager"
	)
	doc = _resolve_line(line)
	budget = frappe.get_doc("Budget", doc.budget)
	resolve_scoped_entity(budget.procuring_entity)
	currency = doc.currency or budget.currency or "KES"
	list_row = _line_list_dto(doc, budget.status, currency)
	treatments = _treatment_dtos(doc)
	dedicated = _dedicated_total(treatments)
	approved = flt(doc.approved_amount)
	can_edit = budget.status in _EDITABLE_STATUSES
	return {
		**list_row,
		"budget_code": budget.generated_reference,
		"budget_status": budget.status,
		"external_financial_line_reference": getattr(doc, "external_financial_line_reference", None)
		or "",
		"primary_target": _target_ref(doc),
		"supporting_targets": _supporting_dtos(doc),
		"value_treatments": treatments,
		"dedicated_total": dedicated,
		"not_dedicated": max(0.0, approved - dedicated),
		"dedicated_total_display": format_kes_compact(dedicated, currency=currency),
		"not_dedicated_display": format_kes_compact(max(0.0, approved - dedicated), currency=currency),
		"approved_compact_display": format_kes_compact(approved, currency=currency),
		"capabilities": {
			"can_edit": can_edit,
			"can_save": can_edit,
			"show_request_revision": budget.status == "Active",
			"read_only": not can_edit,
		},
	}


def _validate_save_payload(payload: dict[str, Any], *, is_create: bool) -> dict[str, str]:
	errors: dict[str, str] = {}
	title = (payload.get("title") or "").strip()
	if not title:
		errors["title"] = _("Budget line title is required")
	owner = (payload.get("organisational_owner") or "").strip()
	if not owner:
		errors["organisational_owner"] = _("Responsible owner is required")
	classification = (payload.get("classification") or "").strip()
	if not classification:
		errors["classification"] = _("Classification is required")
	fst = (payload.get("funding_source_type") or "").strip()
	if not fst:
		errors["funding_source_type"] = _("Funding source is required")
	fsn = (payload.get("funding_source_name") or "").strip()
	if not fsn:
		errors["funding_source_name"] = _("Funding source name is required")
	approved = flt(payload.get("approved_amount"))
	if approved <= 0:
		errors["approved_amount"] = _("Approved amount must be positive")

	primary = payload.get("primary_target") or {}
	if not (primary.get("code") or primary.get("id") or "").strip():
		errors["primary_target"] = _("Primary strategic target is required")

	seen_targets: set[str] = set()
	p_code = (primary.get("code") or "").strip()
	if p_code:
		seen_targets.add(p_code)
	for i, st in enumerate(payload.get("supporting_targets") or []):
		code = (st.get("code") or "").strip()
		reason = (st.get("reason") or "").strip()
		if code and code in seen_targets:
			errors[f"supporting_targets.{i}"] = _("Duplicate target selection is not allowed")
		if code:
			seen_targets.add(code)
		if code and not reason:
			errors[f"supporting_targets.{i}.reason"] = _("Supporting targets require a reason")

	dedicated_sum = 0.0
	for i, tr in enumerate(payload.get("value_treatments") or []):
		treatment = (tr.get("treatment") or "").strip()
		level = (tr.get("requirement_level") or "").strip().lower()
		rationale = (tr.get("rationale") or "").strip()
		amount = flt(tr.get("dedicated_amount"))
		is_required = level.startswith("required")
		if is_required and not treatment:
			errors[f"value_treatments.{i}"] = _("Required value treatments must be complete")
		if treatment == _DEDICATED:
			if amount <= 0:
				errors[f"value_treatments.{i}.dedicated_amount"] = _(
					"Dedicated allocation requires a positive amount"
				)
			dedicated_sum += amount
		elif amount > 0:
			errors[f"value_treatments.{i}.dedicated_amount"] = _(
				"Only Dedicated allocation may claim a distinct amount"
			)
		if treatment in _TREATMENTS_NEEDING_RATIONALE and not rationale:
			errors[f"value_treatments.{i}.rationale"] = _("Rationale is required for this treatment")
		if treatment == "Not applicable" and not int(tr.get("reviewer_accepted") or 0):
			# Soft for Draft save — pack requires before activation; still flag for Required.
			if is_required:
				errors[f"value_treatments.{i}.reviewer_accepted"] = _(
					"Not applicable requires reviewer acceptance"
				)

	if dedicated_sum > approved + 0.0001:
		errors["dedicated_total"] = _("Dedicated treatments must not exceed the approved amount")

	# Ignore any client-supplied generated_reference on create/edit (BUD-FR-020).
	# is_create reserved for future create-only rules.
	return errors


def _apply_strategy_fields(doc, payload: dict[str, Any]) -> None:
	"""XMOD-STR-001 — resolve + validate Strategy Reference; write authoritative primary_*."""
	from kentender_strategy.services.strategy_consumer import (
		apply_budget_primary_strategy_reference,
		resolve_performance_target_id,
		validated_supporting_target_row,
	)

	primary = payload.get("primary_target") or {}
	resolved_primary = resolve_performance_target_id(
		target_id=(primary.get("id") or "").strip() or None,
		target_code=(primary.get("code") or "").strip() or None,
	)
	if not resolved_primary:
		frappe.throw(_("Unknown or missing primary Performance Target"), frappe.ValidationError)

	prior_primary = (getattr(doc, "primary_target_id", None) or "").strip()
	require_active = doc.is_new() or resolved_primary != prior_primary
	# Avoid double Active enforcement inside BudgetLine.validate after this apply.
	doc.flags.skip_budget_strategy_validate = True
	apply_budget_primary_strategy_reference(doc, resolved_primary, require_active=require_active)

	prior_supporting = {
		(getattr(row, "target_id", None) or "").strip()
		for row in (doc.get("supporting_targets") or [])
		if (getattr(row, "target_id", None) or "").strip()
	}
	doc.set("supporting_targets", [])
	for st in payload.get("supporting_targets") or []:
		code = (st.get("code") or "").strip()
		sid = (st.get("id") or "").strip()
		if not code and not sid:
			continue
		resolved_st = resolve_performance_target_id(target_id=sid or None, target_code=code or None)
		st_require_active = doc.is_new() or not resolved_st or resolved_st not in prior_supporting
		row = validated_supporting_target_row(
			target_id=resolved_st,
			target_code=code or None,
			reason=(st.get("reason") or "").strip(),
			require_active=st_require_active,
		)
		doc.append("supporting_targets", row)

	doc.set("value_treatments", [])
	for tr in payload.get("value_treatments") or []:
		code = (tr.get("code") or "").strip()
		if not code:
			continue
		doc.append(
			"value_treatments",
			{
				"pvc_id": (tr.get("id") or "").strip(),
				"pvc_code": code,
				"pvc_name": (tr.get("name") or "").strip() or code,
				"requirement_level": (tr.get("requirement_level") or "").strip(),
				"treatment": (tr.get("treatment") or "").strip(),
				"dedicated_amount": flt(tr.get("dedicated_amount")),
				"rationale": (tr.get("rationale") or "").strip(),
				"reviewer_accepted": int(tr.get("reviewer_accepted") or 0),
			},
		)


def _refresh_budget_pvc_counts(budget_name: str) -> None:
	"""Roll up unique PVC codes with treatments onto Budget header (Overview 4/4)."""
	line_names = frappe.get_all("Budget Line", filters={"budget": budget_name}, pluck="name")
	applicable: set[str] = set()
	treated: set[str] = set()
	for ln in line_names:
		doc = frappe.get_doc("Budget Line", ln)
		for row in doc.get("value_treatments") or []:
			code = (row.pvc_code or "").strip()
			if not code:
				continue
			applicable.add(code)
			if (row.treatment or "").strip():
				treated.add(code)
	frappe.db.set_value(
		"Budget",
		budget_name,
		{"strategy_pvc_treated": len(treated), "strategy_pvc_applicable": len(applicable)},
		update_modified=False,
	)


def save_budget_line(payload: dict | None = None) -> dict[str, Any]:
	"""BUD-UI-05 — Draft/Returned only; one transaction for funding + Strategy + PVC."""
	require_any_role(ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, "System Manager")
	payload = payload or {}
	budget_key = (payload.get("budget") or payload.get("budget_code") or "").strip()
	budget = _resolve_budget(budget_key)
	resolve_scoped_entity(budget.procuring_entity)

	if budget.status not in _EDITABLE_STATUSES:
		frappe.throw(
			_("Active Budgets and their lines cannot be edited directly. Request a revision."),
			frappe.PermissionError,
		)

	line_key = (payload.get("line") or payload.get("code") or payload.get("id") or "").strip()
	is_create = not line_key
	errors = _validate_save_payload(payload, is_create=is_create)
	if errors:
		return {"ok": False, "errors": errors}

	if is_create:
		ref = allocate_budget_line_reference(budget.procuring_entity)
		doc = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"budget": budget.name,
				"generated_reference": ref,
				"currency": budget.currency or "KES",
				"is_active": 1,
				"order_index": int(
					frappe.db.count("Budget Line", {"budget": budget.name}) or 0
				)
				+ 1,
			}
		)
	else:
		doc = _resolve_line(line_key)
		if doc.budget != budget.name:
			frappe.throw(_("Budget Line does not belong to this Budget"), frappe.ValidationError)

	# Never accept client-supplied generated_reference.
	doc.title = (payload.get("title") or "").strip()
	doc.organisational_owner = (payload.get("organisational_owner") or "").strip()
	doc.classification = (payload.get("classification") or "").strip()
	doc.funding_source_type = (payload.get("funding_source_type") or "").strip()
	doc.funding_source_name = (payload.get("funding_source_name") or "").strip()
	doc.external_financial_line_reference = (
		payload.get("external_financial_line_reference") or ""
	).strip()
	doc.approved_amount = flt(payload.get("approved_amount"))
	# Balances are system-derived from funding activity — preserve existing on edit.
	if is_create:
		doc.amount_reserved = 0
		doc.amount_committed = 0
		doc.amount_actual = 0
		doc.actual_as_at = None

	try:
		_apply_strategy_fields(doc, payload)
	except frappe.ValidationError as exc:
		msg = str(exc).strip() or _("Invalid strategy reference")
		# Prefer primary_target key; supporting failures still block save via same envelope.
		key = "primary_target"
		low = msg.lower()
		if "supporting" in low:
			key = "supporting_targets"
		return {"ok": False, "errors": {key: msg}}

	if is_create:
		doc.insert()
	else:
		doc.save()

	_refresh_budget_pvc_counts(budget.name)
	return {"ok": True, "line": get_budget_line(doc.generated_reference)}
