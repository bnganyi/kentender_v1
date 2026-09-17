# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 §4.3/§4.4/§9.1/§9.2/§12.2 — Budget Line drafting and the
eligible-line read contracts. Owns `save_budget_lines_draft`,
`list_eligible_budget_lines`, and the Budget Lines tab read models for the
version editor (BUD-UI-02) and the Active workspace (BUD-UI-03).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

from kentender_budget.services.budget_authorization import (
	CAP_EDIT,
	has_budget_version_capability,
	require_budget_version_capability,
	require_budget_version_read_scope,
)
from kentender_budget.services.budget_contracts import (
	_active_version,
	_line_position,
	_resolve_budget_version,
	_version_totals,
	format_kes_full,
)
from kentender_budget.services.budget_idempotency import run_idempotent
from kentender_budget.services.budget_reference import allocate_budget_line_reference, allocate_budget_line_version_reference


def _protected_amount(budget_line: str) -> float:
	pos = _line_position(budget_line, None)
	return pos["reserved"] + pos["committed"]


def _editor_totals(version, rows: list[dict[str, Any]]) -> dict[str, Any]:
	"""§11.3/§11.15 — Approved allocation vs Total entered with the exact
	positive still-to-assign / over-allocation figure, plus Total moved out /
	Total moved in for a successor."""
	from kentender_budget.services.budget_readiness_contracts import _reconcile

	line_total = sum(flt(r.get("approved_amount")) for r in rows)
	totals = _reconcile(version.authorised_total, line_total)
	if version.based_on_budget_version:
		moved_out = moved_in = 0.0
		for r in rows:
			delta = flt(r.get("approved_amount")) - flt(r.get("current_amount") or 0.0)
			if delta > 0:
				moved_in += delta
			elif delta < 0:
				moved_out += -delta
		totals.update({"total_moved_out": moved_out, "total_moved_in": moved_in, "transfer_balanced": abs(moved_out - moved_in) < 0.01})
	return totals


def _lines_previously_in_active(budget_version) -> dict[str, Any]:
	"""Budget Line names present in this version's `based_on_budget_version`,
	keyed by budget_line — the "previously Active line" identity-lock set
	(§12.2: "Removing or changing identity fields on a previously Active line
	is rejected")."""
	if not budget_version.based_on_budget_version:
		return {}
	rows = frappe.get_all(
		"Procurement Budget Line Version",
		filters={"budget_version": budget_version.based_on_budget_version},
		fields=["budget_line", "title", "owner_org_unit", "funding_source"],
	)
	return {r.budget_line: r for r in rows}


def save_budget_lines_draft(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `save_budget_lines_draft` — create, update or remove Draft lines
	as one validated change set."""
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	payload = payload or {}

	return run_idempotent(payload=payload, fn=lambda: _save_budget_lines_draft(payload), budget_for=lambda r: (r.get("version") or {}).get("budget"))


def _save_budget_lines_draft(payload: dict[str, Any]) -> dict[str, Any]:
	from kentender_budget.services.budget_contracts import _version_summary

	version = _resolve_budget_version(payload.get("budget_version") or "")
	require_budget_version_capability(frappe.session.user, CAP_EDIT, version)
	if version.status != "Draft":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	expected = payload.get("expected_modified")
	if expected and str(version.modified) != str(expected):
		return {"ok": False, "code": "BUDGET_STALE_WRITE", "errors": {"expected_modified": _("This budget has changed since you opened it. Refresh to see the current details.")}, "version": _version_summary(version)}

	budget = frappe.get_doc("Procurement Budget", version.budget)
	locked = _lines_previously_in_active(version)
	rows = payload.get("lines") or []
	errors: dict[str, str] = {}

	existing_versions = {
		lv.budget_line: lv
		for lv in frappe.get_all(
			"Procurement Budget Line Version", filters={"budget_version": version.name}, fields=["name", "budget_line"]
		)
	}
	seen: set[str] = set()

	for i, row in enumerate(rows):
		budget_line_key = (row.get("budget_line") or "").strip()
		remove = bool(row.get("remove"))
		omit = bool(row.get("omit"))

		if omit:
			# BUD-BR-020 / §12.2 — omission from the proposed Version only,
			# permitted while the line has no remaining reservation or active
			# commitment (rechecked again at approval). The line identity and
			# its history are untouched; only this Draft's Line Version goes.
			if budget_line_key not in locked:
				errors[f"lines.{i}"] = _("Only a previously approved line can be omitted from an update")
				continue
			protected = _protected_amount(budget_line_key)
			if protected > 0:
				errors[f"lines.{i}"] = _("{0} has {1} reserved or committed and cannot be omitted from this update").format(
					locked[budget_line_key].title, format_kes_full(protected, currency=budget.currency or "KES")
				)
				continue
			if budget_line_key in existing_versions:
				frappe.delete_doc("Procurement Budget Line Version", existing_versions[budget_line_key].name, ignore_permissions=True)
			continue

		if remove:
			if budget_line_key in locked:
				errors[f"lines.{i}"] = _("A previously approved line cannot be removed; omit it from this update instead")
				continue
			if budget_line_key and budget_line_key in existing_versions:
				frappe.delete_doc("Procurement Budget Line Version", existing_versions[budget_line_key].name, ignore_permissions=True)
			continue

		title = (row.get("title") or "").strip()
		owner_org_unit = (row.get("owner_org_unit") or "").strip()
		funding_source = (row.get("funding_source") or "").strip()
		approved_amount = flt(row.get("approved_amount"))

		if not title:
			errors[f"lines.{i}.title"] = _("Line title is required")
		if not funding_source:
			errors[f"lines.{i}.funding_source"] = _("Funding source is required")
		if approved_amount <= 0:
			errors[f"lines.{i}.approved_amount"] = _("Approved amount must be positive")
		# owner_org_unit is BUD-BR-007 line-eligibility data, never a user-scope
		# or permission check (§17.1/§18) — only existence is validated here.
		if owner_org_unit and not frappe.db.exists("Organisation Unit", owner_org_unit):
			errors[f"lines.{i}.owner_org_unit"] = _("Organisation unit not found")

		if budget_line_key and budget_line_key in locked:
			prior = locked[budget_line_key]
			# BUD-BR-019 — identity fields are immutable once previously Active;
			# only approved_amount may change. Silently hold the prior identity
			# rather than accept a client-supplied change.
			title = prior.title
			owner_org_unit = prior.owner_org_unit
			funding_source = prior.funding_source

		seen.add(budget_line_key)
		if errors:
			continue

		if budget_line_key and budget_line_key in existing_versions:
			line_version = frappe.get_doc("Procurement Budget Line Version", existing_versions[budget_line_key].name)
			line_version.title = title
			line_version.owner_org_unit = owner_org_unit or None
			line_version.funding_source = funding_source
			line_version.approved_amount = approved_amount
			line_version.save(ignore_permissions=True)
		else:
			if not budget_line_key:
				line_ref = allocate_budget_line_reference()
				budget_line = frappe.get_doc(
					{"doctype": "Procurement Budget Line", "generated_reference": line_ref, "budget": budget.name}
				)
				budget_line.insert(ignore_permissions=True)
				budget_line_key = budget_line.name
			else:
				budget_line = frappe.get_doc("Procurement Budget Line", budget_line_key)
				if budget_line.budget != budget.name:
					errors[f"lines.{i}"] = _("Budget Line does not belong to this Budget")
					continue

			frappe.get_doc(
				{
					"doctype": "Procurement Budget Line Version",
					"generated_reference": allocate_budget_line_version_reference(budget_line.generated_reference, version.version_number),
					"budget_version": version.name,
					"budget_line": budget_line.name,
					"title": title,
					"owner_org_unit": owner_org_unit or None,
					"funding_source": funding_source,
					"approved_amount": approved_amount,
					"currency": budget.currency,
				}
			).insert(ignore_permissions=True)

	if errors:
		return {"ok": False, "errors": errors}

	from kentender_budget.services.budget_audit_contracts import EVENT_DRAFT_LINES_SAVED, safe_record_event

	safe_record_event(
		budget=budget.name,
		budget_version=version.name,
		event_type=EVENT_DRAFT_LINES_SAVED,
		actor=frappe.session.user,
		correlation_id=frappe.generate_hash(length=12),
		calling_module="Budget & Funding",
	)

	version.reload()
	editor = get_budget_version_lines_editor(version.name)
	return {"ok": True, "saved_scope": "budget_lines", "totals": editor["totals"], "rows": editor["rows"], "version": _version_summary(version)}


def get_budget_version_lines_editor(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-02 Budget Lines tab — BUD-DES-03 (baseline) / BUD-DES-15 (successor)."""
	from kentender_budget.services.budget_contracts import _org_unit_label

	version = _resolve_budget_version(budget_version)
	require_budget_version_read_scope(version)
	# KT-STD-001 v1.5 §3A.6 — this is a read route open to a technical
	# reader (Administrator/System Manager) via `require_budget_version_read_scope`
	# above. `can_remove` per row must therefore reflect the caller's actual
	# write capability, not only the line's own lock state, or a technical
	# reader's read-only payload would carry a decision authority they do
	# not have (caught live 2026-09-12 by the technical-read conformance
	# gate). The Vue editor already re-checks this against its own
	# `canEdit`; this closes the same gap at the server, which is where
	# AGENTS.md requires every material action to be enforced.
	may_edit = has_budget_version_capability(frappe.session.user, CAP_EDIT, version)
	locked = _lines_previously_in_active(version)

	rows = frappe.get_all(
		"Procurement Budget Line Version",
		filters={"budget_version": version.name},
		fields=["name", "budget_line", "title", "owner_org_unit", "funding_source", "approved_amount"],
		order_by="title asc",
	)
	codes = (
		{
			r.name: r.generated_reference
			for r in frappe.get_all(
				"Procurement Budget Line", filters={"name": ["in", [row.budget_line for row in rows]]}, fields=["name", "generated_reference"]
			)
		}
		if rows
		else {}
	)
	out = []
	for r in rows:
		is_locked = r.budget_line in locked
		row_dto: dict[str, Any] = {
			"budget_line": r.budget_line,
			"budget_line_code": codes.get(r.budget_line, ""),
			"title": r.title,
			# Entity-wide is stored as NULL but travels as "" — the same value
			# the save contract accepts and the editor's "Entity-wide" option
			# carries. A null here left the <select> matching no option, so a
			# reloaded Entity-wide line looked blank/unset (2026-09-11).
			"owner_org_unit": r.owner_org_unit or "",
			"owner_org_unit_label": _org_unit_label(r.owner_org_unit),
			"funding_source": r.funding_source,
			"approved_amount": flt(r.approved_amount),
			"identity_locked": is_locked,
			"can_remove": may_edit and not is_locked,
		}
		if version.based_on_budget_version:
			active_amount = 0.0
			if is_locked:
				active_amount = flt(
					frappe.db.get_value(
						"Procurement Budget Line Version",
						{"budget_version": version.based_on_budget_version, "budget_line": r.budget_line},
						"approved_amount",
					)
				)
			row_dto["active_amount"] = active_amount
			row_dto["current_amount"] = active_amount
			row_dto["change"] = flt(r.approved_amount) - active_amount
			protected = _protected_amount(r.budget_line) if is_locked else 0.0
			row_dto["protected_amount"] = protected
			# §11.15 Omit from this update — only when nothing is reserved or committed.
			row_dto["can_omit"] = may_edit and is_locked and protected <= 0
		out.append(row_dto)

	omitted = []
	if version.based_on_budget_version:
		present = {r.budget_line for r in rows}
		for line_name, prior in locked.items():
			if line_name not in present:
				omitted.append({"budget_line": line_name, "title": prior.title, "current_amount": flt(frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version.based_on_budget_version, "budget_line": line_name}, "approved_amount"))})
	totals = _editor_totals(version, out)
	if omitted and "total_moved_out" in totals:
		totals["total_moved_out"] += sum(o["current_amount"] for o in omitted)
		totals["transfer_balanced"] = abs(totals["total_moved_out"] - totals["total_moved_in"]) < 0.01

	return {
		"rows": out,
		"omitted": omitted,
		"is_successor": bool(version.based_on_budget_version),
		"can_edit": may_edit and version.status == "Draft",
		"totals": totals,
	}


def get_budget_lines_active(budget: str) -> dict[str, Any]:
	"""BUD-UI-03 Budget Lines tab — BUD-DES-05: Active line positions + Total row."""
	from kentender_budget.services.budget_contracts import _resolve_budget

	doc = _resolve_budget(budget)
	version = _active_version(doc.name)
	if not version:
		frappe.throw(_("No Active Budget Version"), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	require_budget_version_read_scope(version)

	totals = _version_totals(version.name)
	currency = doc.currency or "KES"
	rows = []
	for line in totals["lines"]:
		pos = line["positions"]
		rows.append(
			{
				"budget_line": line["budget_line"],
				"code": line.get("code", ""),
				"title": line["title"],
				"owner_org_unit": line.get("owner_org_unit_label", ""),
				"funding_source": line.get("funding_source_label", ""),
				"approved": pos["approved"],
				"reserved": pos["reserved"],
				"committed": pos["committed"],
				"available": pos["available"],
				"approved_display": format_kes_full(pos["approved"], currency=currency),
				"reserved_display": format_kes_full(pos["reserved"], currency=currency),
				"committed_display": format_kes_full(pos["committed"], currency=currency),
				"available_display": format_kes_full(pos["available"], currency=currency),
			}
		)
	return {
		"rows": rows,
		"total": {
			"approved": totals["approved"],
			"reserved": totals["reserved"],
			"committed": totals["committed"],
			"available": totals["available"],
		},
	}


def list_eligible_budget_lines(
	fiscal_year: str,
	source_org_unit: str | None = None,
	funding_source: str | None = None,
	search: str | None = None,
) -> list[dict[str, Any]]:
	"""§9.1 `list_eligible_budget_lines` — Active eligible lines only
	(BUD-BR-007: Entity-wide or matching the source Need's organisation
	unit), no Draft lines."""
	budget_name = frappe.db.get_value("Procurement Budget", {"fiscal_year": fiscal_year}, "name")
	if not budget_name:
		return []
	version = _active_version(budget_name)
	if not version:
		return []
	require_budget_version_read_scope(version)

	filters: dict[str, Any] = {"budget_version": version.name}
	if funding_source:
		filters["funding_source"] = funding_source
	if search:
		filters["title"] = ["like", f"%{search}%"]

	rows = frappe.get_all(
		"Procurement Budget Line Version",
		filters=filters,
		fields=["budget_line", "title", "owner_org_unit", "funding_source", "approved_amount"],
		order_by="title asc",
	)
	references = _line_references([r.budget_line for r in rows])
	out = []
	for r in rows:
		if r.owner_org_unit and source_org_unit and r.owner_org_unit != source_org_unit:
			continue
		pos = _line_position(r.budget_line, r)
		out.append(
			{
				"id": r.budget_line,
				# BUD v1.5 §9.1 / PLN FU-02 — the human business reference
				# (`MOH-BL-DHI-2027`), so consumers never display the hash id.
				"reference": references.get(r.budget_line, ""),
				"title": r.title,
				"owner_org_unit": r.owner_org_unit,
				"funding_source": r.funding_source,
				"approved": pos["approved"],
				"reserved": pos["reserved"],
				"committed": pos["committed"],
				"available": pos["available"],
			}
		)
	return out


def _line_references(budget_lines: list[str]) -> dict[str, str]:
	if not budget_lines:
		return {}
	rows = frappe.get_all(
		"Procurement Budget Line",
		filters={"name": ("in", budget_lines)},
		fields=["name", "generated_reference"],
	)
	return {r.name: r.generated_reference or "" for r in rows}


def check_plan_affordability(
	fiscal_year: str,
	planned_totals: dict[str, float] | list[dict[str, Any]] | str | None = None,
) -> dict[str, Any]:
	"""BUD-CHG-001 v1.5 §8.2 / §9.1 `check_plan_affordability` — non-mutating.

	Receives a Fiscal Year and the plan's per-Procurement-Budget-Line planned
	totals; returns, for every Active line of that year's Active version, the
	approved amount, the plan's planned total, the current positions with an
	`as_at` instant and the two verdicts:

	- **within approved amount** — planned ≤ approved (the blocking one: a plan
	  exceeding a line's approved amount cannot lawfully be executed);
	- **within currently available** — planned ≤ approved − reserved −
	  committed (advisory only; planning and drawdown run on different horizons).

	Locks nothing, writes nothing, creates no token, produces no ledger event
	(BUD-BR-012). Repeating it returns a fresh statement at a new `as_at`.
	A planned total for a line that is not Active in this year is reported
	as `unknown_lines` and fails the blocking verdict, because nothing can be
	executed against it.
	"""
	from frappe.utils import now_datetime

	if isinstance(planned_totals, str):
		planned_totals = frappe.parse_json(planned_totals)
	totals: dict[str, float] = {}
	if isinstance(planned_totals, dict):
		totals = {str(k): flt(v) for k, v in planned_totals.items()}
	else:
		for row in planned_totals or []:
			key = str(row.get("budget_line") or row.get("id") or "")
			if key:
				totals[key] = totals.get(key, 0.0) + flt(row.get("planned") if "planned" in row else row.get("amount"))

	as_at = now_datetime()
	budget_name = frappe.db.get_value("Procurement Budget", {"fiscal_year": fiscal_year}, "name")
	version = _active_version(budget_name) if budget_name else None
	if not version:
		return {
			"fiscal_year": fiscal_year,
			"as_at": str(as_at),
			"active_version": "",
			"lines": [],
			"unknown_lines": sorted(totals),
			"within_approved": not totals,
			"within_available": not totals,
			"failing_lines": [],
		}
	require_budget_version_read_scope(version)

	rows = frappe.get_all(
		"Procurement Budget Line Version",
		filters={"budget_version": version.name},
		fields=["budget_line", "title", "owner_org_unit", "funding_source", "approved_amount"],
		order_by="title asc",
	)
	references = _line_references([r.budget_line for r in rows])
	currency = frappe.db.get_value("Procurement Budget", budget_name, "currency") or "KES"
	lines = []
	failing = []
	seen = set()
	all_within_approved = True
	all_within_available = True
	for r in rows:
		seen.add(r.budget_line)
		pos = _line_position(r.budget_line, r)
		planned = flt(totals.get(r.budget_line, 0.0))
		within_approved = planned <= pos["approved"] + 1e-9
		within_available = planned <= pos["available"] + 1e-9
		excess = max(0.0, planned - pos["approved"])
		if not within_approved:
			all_within_approved = False
			failing.append({"budget_line": r.budget_line, "reference": references.get(r.budget_line, ""), "excess": excess})
		if not within_available:
			all_within_available = False
		lines.append(
			{
				"budget_line": r.budget_line,
				"reference": references.get(r.budget_line, ""),
				"title": r.title,
				"owner_org_unit": r.owner_org_unit,
				"funding_source": r.funding_source,
				"currency": currency,
				"approved": pos["approved"],
				"planned": planned,
				"reserved": pos["reserved"],
				"committed": pos["committed"],
				"available": pos["available"],
				"within_approved": within_approved,
				"within_available": within_available,
				"excess_over_approved": excess,
			}
		)
	unknown = sorted(k for k in totals if k not in seen and flt(totals[k]) > 0)
	if unknown:
		all_within_approved = False
		all_within_available = False
		for key in unknown:
			failing.append({"budget_line": key, "reference": "", "excess": flt(totals[key])})
	return {
		"fiscal_year": fiscal_year,
		"as_at": str(as_at),
		"active_version": version.name,
		"currency": currency,
		"lines": lines,
		"unknown_lines": unknown,
		"within_approved": all_within_approved,
		"within_available": all_within_available,
		"failing_lines": failing,
	}



# --------------------------------------------------------------------------
# PLN-CHG-001 v1.18 §5.3.3 / §7.3 — the two Budget contracts Planning's
# Finance decision and reservation calculation consume (BUD-CHG-001 v1.8 is
# owed: Budget FOLLOW_UPS FU-14). Amounts on these contracts are decimal
# strings in currency units (v1.18 §4.1); nothing here writes, reserves or
# produces a ledger event.
# --------------------------------------------------------------------------

import hashlib
import json
from decimal import Decimal

CURRENCY_PRECISION = 2  # KES; BUD-CHG-001's currency contract carries the precision


def money(value) -> str:
	"""Exact decimal string in currency units (never a binary float)."""
	return str(Decimal(repr(round(flt(value), CURRENCY_PRECISION))).quantize(Decimal(1).scaleb(-CURRENCY_PRECISION)))


def _planned_totals(planned_totals) -> dict[str, float]:
	if isinstance(planned_totals, str):
		planned_totals = frappe.parse_json(planned_totals)
	totals: dict[str, float] = {}
	if isinstance(planned_totals, dict):
		return {str(k): flt(v) for k, v in planned_totals.items()}
	for row in planned_totals or []:
		key = str(row.get("budget_line") or row.get("id") or "")
		if key:
			totals[key] = totals.get(key, 0.0) + flt(row.get("planned") if "planned" in row else row.get("amount"))
	return totals


def get_annual_procurement_budget_basis(fiscal_year: str, as_of=None) -> dict[str, Any]:
	"""v1.18 §5.5.3.1 — the complete approved annual procurement budget and
	the exact Version it comes from: the reservation-allocation denominator.
	Never the Plan total, never only the lines a Plan uses. The Active
	Version of the year answers; a year with no Active Version reports
	`available = False` and the consumer fails closed."""
	from frappe.utils import now_datetime

	fiscal_year = (fiscal_year or "").strip()
	budget_name = frappe.db.get_value("Procurement Budget", {"fiscal_year": fiscal_year}, "name") if fiscal_year else None
	version = _active_version(budget_name) if budget_name else None
	if not version:
		return {"fiscal_year": fiscal_year, "available": False, "as_of": str(as_of or now_datetime())}
	require_budget_version_read_scope(version)
	rows = frappe.get_all(
		"Procurement Budget Line Version",
		filters={"budget_version": version.name},
		fields=["name", "budget_line", "approved_amount"],
	)
	lines_total = sum(flt(r.approved_amount) for r in rows)
	annual = flt(version.authorised_total) or lines_total
	budget = frappe.db.get_value("Procurement Budget", budget_name, ["generated_reference", "currency"], as_dict=True)
	return {
		"fiscal_year": fiscal_year,
		"available": True,
		"budget": budget_name,
		"budget_reference": budget.generated_reference or "",
		"budget_version": version.name,
		"version_reference": version.generated_reference or "",
		"version_number": int(version.version_number or 0),
		"approval_date": str(version.approval_date or ""),
		"currency": budget.currency or "KES",
		"currency_precision": CURRENCY_PRECISION,
		"annual_approved_amount": money(annual),
		"lines_approved_total": money(lines_total),
		"line_count": len(rows),
		"as_of": str(as_of or now_datetime()),
	}


def validate_plan_affordability_for_decision(
	fiscal_year: str,
	planned_totals,
	expected_revisions=None,
	correlation: str = "",
) -> dict[str, Any]:
	"""v1.18 §5.3.3 — the decision-time counterpart of
	`check_plan_affordability`. Called *inside* the Finance decision's own
	transaction: it serialises the year's Active Budget Version and its line
	versions (`SELECT … FOR UPDATE`), validates the line revisions the caller
	reviewed (`expected_revisions`: `{budget_line: line_version_name}` and
	optionally `budget_version`), and returns the comparison statement the
	caller records verbatim. A Budget change since the review fails the
	positive decision atomically (`BUD_BASIS_STALE`); nothing is written,
	reserved or journaled here. `check_plan_affordability` stays the
	non-locking display read.
	"""
	from frappe.utils import now_datetime

	fiscal_year = (fiscal_year or "").strip()
	totals = _planned_totals(planned_totals)
	if isinstance(expected_revisions, str):
		expected_revisions = frappe.parse_json(expected_revisions or "{}")
	expected = dict(expected_revisions or {})
	expected_version = expected.pop("budget_version", "") or ""

	budget_name = frappe.db.get_value("Procurement Budget", {"fiscal_year": fiscal_year}, "name") if fiscal_year else None
	version = _active_version(budget_name) if budget_name else None
	if not version:
		frappe.throw(f"No Active Procurement Budget Version exists for {fiscal_year}.", title="BUD_BASIS_UNAVAILABLE")
	require_budget_version_read_scope(version)

	# Serialise the authoritative basis for the rest of the caller's transaction.
	frappe.db.sql("select name from `tabProcurement Budget Version` where name = %s for update", version.name)
	frappe.db.sql("select name from `tabProcurement Budget Line Version` where budget_version = %s for update", version.name)
	if frappe.db.get_value("Procurement Budget Version", version.name, "status") != "Active":
		frappe.throw("The Budget basis changed while the decision was being recorded.", title="BUD_BASIS_STALE")
	if expected_version and expected_version != version.name:
		frappe.throw(
			f"The reviewed Budget Version {expected_version} is no longer the Active one ({version.name}).",
			title="BUD_BASIS_STALE",
		)

	rows = frappe.get_all(
		"Procurement Budget Line Version",
		filters={"budget_version": version.name},
		fields=["name", "budget_line", "title", "owner_org_unit", "funding_source", "approved_amount", "modified"],
		order_by="title asc",
	)
	line_versions = {r.budget_line: r.name for r in rows}
	stale = sorted(line for line, reviewed in expected.items() if line_versions.get(line) != reviewed)
	if stale:
		frappe.throw(
			"The reviewed Budget Line revision has changed for: " + ", ".join(stale) + ".",
			title="BUD_BASIS_STALE",
		)

	as_at = now_datetime()
	references = _line_references([r.budget_line for r in rows])
	currency = frappe.db.get_value("Procurement Budget", budget_name, "currency") or "KES"
	lines = []
	failing = []
	seen = set()
	all_within_approved = True
	all_within_available = True
	digest_rows = []
	for r in rows:
		seen.add(r.budget_line)
		pos = _line_position(r.budget_line, r)
		planned = flt(totals.get(r.budget_line, 0.0))
		within_approved = planned <= pos["approved"] + 1e-9
		within_available = planned <= pos["available"] + 1e-9
		excess = max(0.0, planned - pos["approved"])
		if not within_approved:
			all_within_approved = False
			failing.append({"budget_line": r.budget_line, "reference": references.get(r.budget_line, ""), "excess": money(excess)})
		if not within_available:
			all_within_available = False
		lines.append(
			{
				"budget_line": r.budget_line,
				"line_version": r.name,
				"reference": references.get(r.budget_line, ""),
				"title": r.title,
				"owner_org_unit": r.owner_org_unit,
				"funding_source": r.funding_source,
				"currency": currency,
				"approved": money(pos["approved"]),
				"planned": money(planned),
				"reserved": money(pos["reserved"]),
				"committed": money(pos["committed"]),
				"available": money(pos["available"]),
				"within_approved": within_approved,
				"within_available": within_available,
				"excess_over_approved": money(excess),
				"eligible": True,
			}
		)
		digest_rows.append([r.budget_line, r.name, money(pos["approved"]), money(planned), r.funding_source or "", currency])
	unknown = sorted(k for k in totals if k not in seen and flt(totals[k]) > 0)
	if unknown:
		all_within_approved = False
		all_within_available = False
		for key in unknown:
			failing.append({"budget_line": key, "reference": "", "excess": money(totals[key])})
			digest_rows.append([key, "", "0.00", money(totals[key]), "", currency])
	digest_rows.sort()
	digest = hashlib.sha256(json.dumps(digest_rows, separators=(",", ":")).encode("utf-8")).hexdigest()
	return {
		"fiscal_year": fiscal_year,
		"as_at": str(as_at),
		"decision_basis": True,
		"correlation": correlation or "",
		"budget": budget_name,
		"budget_version": version.name,
		"version_reference": version.generated_reference or "",
		"version_number": int(version.version_number or 0),
		"currency": currency,
		"currency_precision": CURRENCY_PRECISION,
		"line_versions": line_versions,
		"basis_digest": digest,
		"lines": lines,
		"unknown_lines": unknown,
		"within_approved": all_within_approved,
		"within_available": all_within_available,
		"failing_lines": failing,
	}
