# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 §4.3/§4.4/§9.1/§9.2/§12.2 — Budget Line drafting and the
eligible-line read contracts. Owns `save_budget_lines_draft`,
`list_eligible_budget_lines`, and the Budget Lines tab read models for the
version editor (BUD-UI-02) and the Active workspace (BUD-UI-03).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe import _

from kentender_budget.services.budget_authorization import (
	CAP_EDIT,
	has_budget_version_capability,
	require_budget_version_capability,
	require_budget_version_read_scope,
)
from kentender_budget.services.budget_contracts import (
	_active_version,
	_line_position,
	_line_position_exact,
	_resolve_budget_version,
	_version_totals,
	catalogue_problem,
	format_kes_full,
	stale_write_result,
	stamp_is_stale,
)
from kentender_budget.services.budget_idempotency import run_idempotent
from kentender_budget.services.budget_locking import lock_budget, locked_doc
from kentender_budget.services.budget_money import MONEY_ERROR, as_float, check_money, currency_basis, parse_money, scale_for
from kentender_budget.services.budget_money import stored as money_stored
from kentender_budget.services.budget_write_family import budget_write
from kentender_budget.services.budget_reference import allocate_budget_line_reference, allocate_budget_line_version_reference


def _protected_amount(budget_line: str) -> Decimal:
	"""The exact floor of a line (reserved plus committed)."""
	pos = _line_position_exact(budget_line, None)
	return pos["reserved"] + pos["committed"]


def _editor_totals(version, rows: list[dict[str, Any]]) -> dict[str, Any]:
	"""§11.3/§11.15 — Approved allocation vs Total entered with the exact
	positive still-to-assign / over-allocation figure, plus Total moved out /
	Total moved in for a successor. Exact decimals, no tolerance (AUD-XC-117)."""
	from kentender_budget.services.budget_readiness_contracts import _reconcile

	line_total = sum((money_stored(r.get("approved_amount")) for r in rows), Decimal(0))
	totals = _reconcile(version.authorised_total, line_total)
	if version.based_on_budget_version:
		moved_out = moved_in = Decimal(0)
		for r in rows:
			delta = money_stored(r.get("approved_amount")) - money_stored(r.get("current_amount") or 0)
			if delta > 0:
				moved_in += delta
			elif delta < 0:
				moved_out += -delta
		totals.update({"total_moved_out": as_float(moved_out), "total_moved_in": as_float(moved_in), "transfer_balanced": moved_out == moved_in})
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
	"""One validated change set (BUD §9.2, AUD-BUD-006): the stamp is checked
	under the Budget's Version lock, every row is validated, and the rows are
	written inside one savepoint that is rolled back if any row is refused, so a
	rejected save leaves the Draft exactly as it was. A successful save advances
	the Version's stamp (AUD-XC-119/AUD-BUD-007), so a second save carrying the
	pre-first stamp is `BUDGET_STALE_WRITE`."""
	from kentender_budget.services.budget_contracts import _version_summary

	version = _resolve_budget_version(payload.get("budget_version") or "")
	require_budget_version_capability(frappe.session.user, CAP_EDIT, version)
	if version.status != "Draft":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	if stamp_is_stale(version, payload):
		return stale_write_result(version)

	# The stamp decides on the latest committed row, under the Version lock: two
	# saves that read the same stamp cannot both pass.
	lock_budget(version.budget, lines=False)
	version = locked_doc("Procurement Budget Version", version.name)
	if version.status != "Draft":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	if stamp_is_stale(version, payload):
		return stale_write_result(version)

	savepoint = f"kt_bud_lines_{frappe.generate_hash(length=8)}"
	frappe.db.savepoint(savepoint)
	try:
		errors, codes = _apply_line_changes(version, payload.get("lines") or [])
		if not errors:
			# Advance the Version's stamp: the line set is part of the Version.
			with budget_write():
				version.save(ignore_permissions=True)
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		raise
	if errors:
		frappe.db.rollback(save_point=savepoint)
		result: dict[str, Any] = {"ok": False, "errors": errors}
		if codes and len(set(codes.values())) == 1 and len(codes) == len(errors):
			result["code"] = next(iter(codes.values()))
		return result

	budget = frappe.get_doc("Procurement Budget", version.budget)
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


def _apply_line_changes(version, rows: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
	"""Validate every row, writing as it goes; the caller rolls the whole set
	back when `errors` is not empty. Returns (errors, error codes by key)."""
	budget = frappe.get_doc("Procurement Budget", version.budget)
	scale = scale_for(budget.currency)
	locked = _lines_previously_in_active(version)
	errors: dict[str, str] = {}
	codes: dict[str, str] = {}

	existing_versions = {
		lv.budget_line: lv
		for lv in frappe.get_all(
			"Procurement Budget Line Version", filters={"budget_version": version.name}, fields=["name", "budget_line"]
		)
	}

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
					locked[budget_line_key].title, format_kes_full(protected, currency=budget.currency)
				)
				continue
			if budget_line_key in existing_versions and not errors:
				with budget_write():
					frappe.delete_doc("Procurement Budget Line Version", existing_versions[budget_line_key].name, ignore_permissions=True)
			continue

		if remove:
			if budget_line_key in locked:
				errors[f"lines.{i}"] = _("A previously approved line cannot be removed; omit it from this update instead")
				continue
			if budget_line_key and budget_line_key in existing_versions and not errors:
				with budget_write():
					frappe.delete_doc("Procurement Budget Line Version", existing_versions[budget_line_key].name, ignore_permissions=True)
			continue

		title = (row.get("title") or "").strip()
		owner_org_unit = (row.get("owner_org_unit") or "").strip()
		funding_source = (row.get("funding_source") or "").strip()
		# AUD-XC-117 — an exact amount at the currency's scale; NaN/Infinity,
		# exponent notation, excess scale and overflow are refused, not rounded.
		approved_amount, money_message = check_money(row.get("approved_amount"), scale=scale, allow_zero=True, allow_negative=True)

		# BUD-BR-019 — identity fields are immutable once previously Active;
		# only approved_amount may change. This substitution must run before
		# the required-field checks below: a locked row is "silently held" to
		# its prior identity regardless of what the client sent, so a blank
		# or stale client value for title/owner/funding on a locked row is
		# never a validation failure (2026-09-19 regression — the client's
		# own omit-then-restore round trip does not remember a row's owner
		# unit or funding source, so a real resubmission sent both blank;
		# the checks below used to run against that blank payload before this
		# substitution ever reached it).
		if budget_line_key and budget_line_key in locked:
			prior = locked[budget_line_key]
			title = prior.title
			owner_org_unit = prior.owner_org_unit or ""
			funding_source = prior.funding_source

		row_errors = False
		if not title:
			errors[f"lines.{i}.title"] = _("Line title is required")
			row_errors = True
		if not funding_source:
			errors[f"lines.{i}.funding_source"] = _("Funding source is required")
			row_errors = True
		if money_message:
			errors[f"lines.{i}.approved_amount"] = money_message
			codes[f"lines.{i}.approved_amount"] = MONEY_ERROR
			row_errors = True
		elif approved_amount <= 0:
			errors[f"lines.{i}.approved_amount"] = _("Approved amount must be positive")
			row_errors = True
		# owner_org_unit is BUD-BR-007 line-eligibility data, never a user-scope
		# or permission check (§17.1/§18) — only existence is validated here.
		if owner_org_unit and not frappe.db.exists("Organisation Unit", owner_org_unit):
			errors[f"lines.{i}.owner_org_unit"] = _("Organisation unit not found")
			row_errors = True
		elif not (budget_line_key and budget_line_key in locked):
			# AUD-BUD-010 / BUD18-AC-056 — a NEW line may not name an inactive
			# unit or an unavailable funding source; a previously approved line
			# keeps its frozen identity.
			problem = catalogue_problem(owner_org_unit, funding_source) if funding_source else ""
			if problem:
				errors[f"lines.{i}.owner_org_unit" if "rganisation" in str(problem) else f"lines.{i}.funding_source"] = problem
				row_errors = True

		# Nothing is written once any row has been refused; the whole change set
		# is rolled back by the caller either way (AUD-BUD-006).
		if row_errors or errors:
			continue

		if budget_line_key and budget_line_key in existing_versions:
			line_version = frappe.get_doc("Procurement Budget Line Version", existing_versions[budget_line_key].name)
			line_version.title = title
			line_version.owner_org_unit = owner_org_unit or None
			line_version.funding_source = funding_source
			line_version.approved_amount = approved_amount
			with budget_write():
				line_version.save(ignore_permissions=True)
		else:
			if not budget_line_key:
				line_ref = allocate_budget_line_reference()
				budget_line = frappe.get_doc(
					{"doctype": "Procurement Budget Line", "generated_reference": line_ref, "budget": budget.name}
				)
				with budget_write():
					budget_line.insert(ignore_permissions=True)
				budget_line_key = budget_line.name
			else:
				budget_line = frappe.get_doc("Procurement Budget Line", budget_line_key)
				if budget_line.budget != budget.name:
					errors[f"lines.{i}"] = _("Budget Line does not belong to this Budget")
					continue

			with budget_write():
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

	return errors, codes


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
			"approved_amount": as_float(money_stored(r.approved_amount)),
			"identity_locked": is_locked,
			"can_remove": may_edit and not is_locked,
		}
		if version.based_on_budget_version:
			active_amount = Decimal(0)
			if is_locked:
				active_amount = money_stored(
					frappe.db.get_value(
						"Procurement Budget Line Version",
						{"budget_version": version.based_on_budget_version, "budget_line": r.budget_line},
						"approved_amount",
					)
				)
			row_dto["active_amount"] = as_float(active_amount)
			row_dto["current_amount"] = as_float(active_amount)
			row_dto["change"] = as_float(money_stored(r.approved_amount) - active_amount)
			protected = _protected_amount(r.budget_line) if is_locked else Decimal(0)
			row_dto["protected_amount"] = as_float(protected)
			# §11.15 Omit from this update — only when nothing is reserved or committed.
			row_dto["can_omit"] = may_edit and is_locked and protected <= 0
		out.append(row_dto)

	omitted = []
	if version.based_on_budget_version:
		present = {r.budget_line for r in rows}
		for line_name, prior in locked.items():
			if line_name not in present:
				omitted.append({"budget_line": line_name, "title": prior.title, "current_amount": as_float(money_stored(frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version.based_on_budget_version, "budget_line": line_name}, "approved_amount")))})
	totals = _editor_totals(version, out)
	if omitted and "total_moved_out" in totals:
		moved_out = money_stored(totals["total_moved_out"]) + sum((money_stored(o["current_amount"]) for o in omitted), Decimal(0))
		totals["total_moved_out"] = as_float(moved_out)
		totals["transfer_balanced"] = moved_out == money_stored(totals["total_moved_in"])

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
	currency = doc.currency
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

	raw_totals = _planned_totals(planned_totals)

	as_at = now_datetime()
	budget_name = frappe.db.get_value("Procurement Budget", {"fiscal_year": fiscal_year}, "name")
	version = _active_version(budget_name) if budget_name else None
	totals = _exact_planned_totals(raw_totals, frappe.db.get_value("Procurement Budget", budget_name, "currency") if budget_name else None)
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
	currency = frappe.db.get_value("Procurement Budget", budget_name, "currency")
	lines = []
	failing = []
	seen = set()
	all_within_approved = True
	all_within_available = True
	for r in rows:
		seen.add(r.budget_line)
		pos = _line_position_exact(r.budget_line, r)
		planned = totals.get(r.budget_line, Decimal(0))
		# AUD-XC-116 — exact comparison, no epsilon (BUD §4.8).
		within_approved = planned <= pos["approved"]
		within_available = planned <= pos["available"]
		excess = max(Decimal(0), planned - pos["approved"])
		if not within_approved:
			all_within_approved = False
			failing.append({"budget_line": r.budget_line, "reference": references.get(r.budget_line, ""), "excess": as_float(excess)})
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
				"approved": as_float(pos["approved"]),
				"planned": as_float(planned),
				"reserved": as_float(pos["reserved"]),
				"committed": as_float(pos["committed"]),
				"available": as_float(pos["available"]),
				"within_approved": within_approved,
				"within_available": within_available,
				"excess_over_approved": as_float(excess),
			}
		)
	unknown = sorted(k for k in totals if k not in seen and totals[k] > 0)
	if unknown:
		all_within_approved = False
		all_within_available = False
		for key in unknown:
			failing.append({"budget_line": key, "reference": "", "excess": as_float(totals[key])})
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
# PLN-CHG-001 v1.18 §5.3.3 / §7.3 — the Budget contract Planning's Finance
# decision consumes: ceiling and affordability evidence only. The approved
# budget is never the 30% reservation denominator (BUD-CHG-001 v1.10
# BUD20-AC-001/002 — the old annual-basis contract was removed with no
# alias). Amounts are decimal strings in currency units (v1.18 §4.1);
# nothing here writes, reserves or produces a ledger event.
# --------------------------------------------------------------------------

import hashlib
import json

def money(value, *, currency: str | None = None) -> str:
	"""Exact decimal string in currency units (never a binary float, never a
	silent rounding: a stored value is read as exact text, and a value that
	has more places than the currency supports keeps them)."""
	amount = value if isinstance(value, Decimal) else money_stored(value, scale=scale_for(currency) if currency else 2)
	return f"{amount:f}"


def _planned_totals(planned_totals) -> dict[str, Any]:
	"""The caller's per-line planned totals, summed per line, with each amount
	left exactly as offered (parsed against the currency scale afterwards)."""
	if isinstance(planned_totals, str):
		planned_totals = frappe.parse_json(planned_totals)
	if isinstance(planned_totals, dict):
		return {str(k): v for k, v in planned_totals.items()}
	totals: dict[str, Any] = {}
	for row in planned_totals or []:
		key = str(row.get("budget_line") or row.get("id") or "")
		if key:
			amount = parse_money(row.get("planned") if "planned" in row else row.get("amount"), scale=_PLANNED_PARSE_SCALE, allow_zero=True)
			totals[key] = totals.get(key, Decimal(0)) + amount
	return totals


# The scale is only known once the Budget is resolved; rows are summed at the
# finest supported scale first and re-validated at the currency's scale below.
_PLANNED_PARSE_SCALE = 6


def _exact_planned_totals(raw: dict[str, Any], currency: str | None) -> dict[str, Decimal]:
	"""AUD-XC-117 — every planned total is an exact amount at the currency's
	scale (NaN/Infinity, exponent notation and excess scale fail typed)."""
	scale = scale_for(currency) if currency else 2
	return {key: parse_money(value, scale=scale, field=key, allow_zero=True) for key, value in raw.items()}


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
	raw_totals = _planned_totals(planned_totals)
	if isinstance(expected_revisions, str):
		expected_revisions = frappe.parse_json(expected_revisions or "{}")
	expected = dict(expected_revisions or {})
	expected_version = expected.pop("budget_version", "") or ""

	budget_name = frappe.db.get_value("Procurement Budget", {"fiscal_year": fiscal_year}, "name") if fiscal_year else None
	version = _active_version(budget_name) if budget_name else None
	if not version:
		frappe.throw(f"No Active Procurement Budget Version exists for {fiscal_year}.", title="BUD_BASIS_UNAVAILABLE")
	require_budget_version_read_scope(version)
	basis = currency_basis(frappe.db.get_value("Procurement Budget", budget_name, "currency"))
	totals = _exact_planned_totals(raw_totals, basis["currency"])

	# AUD-XC-104 / BUD §8.2A steps 2-3 — serialise the authoritative basis for
	# the rest of the caller's transaction with the lock order shared by
	# approve, close and reserve (Version rows, then line rows), and re-read the
	# Active Version, its line revisions and every position as locking reads: a
	# plain read would still show the basis this transaction saw before it
	# waited behind an approval.
	lock_budget(budget_name)
	locked_active = _active_version(budget_name, for_update=True)
	if not locked_active:
		frappe.throw("The Budget basis changed while the decision was being recorded.", title="BUD_BASIS_STALE")
	version = locked_active
	if expected_version and expected_version != version.name:
		frappe.throw(
			f"The reviewed Budget Version {expected_version} is no longer the Active one ({version.name}).",
			title="BUD_BASIS_STALE",
		)

	rows = [
		frappe._dict(r)
		for r in frappe.db.sql(
			"select name, budget_line, title, owner_org_unit, funding_source, approved_amount, modified "
			"from `tabProcurement Budget Line Version` where budget_version = %s order by title asc for update",
			(version.name,),
			as_dict=True,
		)
	]
	line_versions = {r.budget_line: r.name for r in rows}
	stale = sorted(line for line, reviewed in expected.items() if line_versions.get(line) != reviewed)
	if stale:
		frappe.throw(
			"The reviewed Budget Line revision has changed for: " + ", ".join(stale) + ".",
			title="BUD_BASIS_STALE",
		)

	as_at = now_datetime()
	references = _line_references([r.budget_line for r in rows])
	currency = basis["currency"]
	lines = []
	failing = []
	seen = set()
	all_within_approved = True
	all_within_available = True
	digest_rows = []
	for r in rows:
		seen.add(r.budget_line)
		pos = _line_position_exact(r.budget_line, r, for_update=True)
		planned = totals.get(r.budget_line, Decimal(0))
		# AUD-XC-116 — exact comparison, no epsilon (BUD §4.8).
		within_approved = planned <= pos["approved"]
		within_available = planned <= pos["available"]
		excess = max(Decimal(0), planned - pos["approved"])
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
	unknown = sorted(k for k in totals if k not in seen and totals[k] > 0)
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
		"currency_precision": basis["fraction_digits"],
		"currency_basis": basis,
		"line_versions": line_versions,
		"basis_digest": digest,
		"lines": lines,
		"unknown_lines": unknown,
		"within_approved": all_within_approved,
		"within_available": all_within_available,
		"failing_lines": failing,
	}
