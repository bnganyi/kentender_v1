# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §4.7 / §5.3 — the immutable financial basis a Finance
review decides on (plan Phase 2d, PLN18-207).

A basis is the Fiscal Year, every operative Procurement Budget Line with its
exact Budget Version, currency, planned total and approved amount, plus the
eligibility result — captured through Budget's decision-time contract so the
line revisions it names can be validated again when Finance decides. Its
digest is technical, never a business field. The same content captured twice
yields the same digest, which is what lets an unchanged Plan reuse an earlier
affirmative decision (`Plan Finance Basis Reuse`).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import budget_gateway, money, readiness

DOCTYPE = "Plan Financial Basis"


def _rows_from_decision_statement(statement: dict[str, Any]) -> list[dict[str, Any]]:
	precision = int(statement.get("currency_precision") or 2)
	rows = []
	for line in statement.get("lines", []):
		rows.append(
			{
				"budget_line": cstr(line.get("budget_line")),
				"line_version": cstr(line.get("line_version")),
				"reference": cstr(line.get("reference")),
				"title": cstr(line.get("title")),
				"funding_source": cstr(line.get("funding_source")),
				"currency": cstr(line.get("currency") or statement.get("currency")),
				"approved": money.money_text(line.get("approved"), precision=precision),
				"planned": money.money_text(line.get("planned"), precision=precision),
				"eligible": bool(line.get("eligible", True)),
				"within_approved": bool(line.get("within_approved")),
			}
		)
	for key in statement.get("unknown_lines", []):
		rows.append({"budget_line": cstr(key), "line_version": "", "reference": "", "title": "", "funding_source": "", "currency": cstr(statement.get("currency")), "approved": money.money_text(0, precision=precision), "planned": "", "eligible": False, "within_approved": False})
	return sorted(rows, key=lambda r: r["budget_line"])


def digest(budget_version: str, rows: list[dict[str, Any]], *, operative_only: bool = True) -> str:
	"""Planning's comparison digest: the Budget Version plus, per operative
	line (planned > 0), identity, approved, planned, funding identity,
	currency and eligibility. Line revisions are validated separately at
	decision time, so the display read and the decision read agree."""
	material = [
		[r["budget_line"], r["approved"], r["planned"], r["funding_source"], r["currency"], r["eligible"]]
		for r in rows
		if not operative_only or flt(r["planned"]) > 0
	]
	material.sort()
	return hashlib.sha256(json.dumps({"budget_version": budget_version, "rows": material}, separators=(",", ":")).encode("utf-8")).hexdigest()


def capture(plan, version, *, correlation: str = "") -> tuple[Any, dict[str, Any]]:
	"""Capture (or reuse) the basis for the Version's current per-line totals
	through Budget's decision-time contract. Returns (basis doc, statement)."""
	totals = readiness.line_totals(version.name)
	try:
		statement = budget_gateway.validate_plan_affordability_for_decision(fiscal_year=plan.fiscal_year, planned_totals=totals, correlation=correlation or version.name)
	except budget_gateway.BudgetBasisStale as exc:
		fail("PLN_REFERENCE_UNAVAILABLE", f"The annual budget basis is not available: {exc}", {"budget_code": exc.code})
	rows = _rows_from_decision_statement(statement)
	basis_digest = digest(cstr(statement.get("budget_version")), rows)
	precision = int(statement.get("currency_precision") or 2)
	planned_total = money.sum_money((r["planned"] for r in rows if r["planned"]), precision=precision)
	approved_total = money.sum_money((r["approved"] for r in rows if flt(r["planned"]) > 0), precision=precision)
	existing = frappe.db.get_value(DOCTYPE, {"plan_version": version.name, "basis_digest": basis_digest}, "name")
	if existing:
		return frappe.get_doc(DOCTYPE, existing), statement
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"plan_version": version.name,
			"fiscal_year": plan.fiscal_year,
			"currency": cstr(statement.get("currency") or "KES"),
			"precision": precision,
			"lines": json.dumps(rows),
			"planned_total": float(planned_total),
			"approved_total": float(approved_total),
			"basis_digest": basis_digest,
			"budget_basis_digest": cstr(statement.get("basis_digest")),
			"captured_at": now_datetime(),
			"fixture_namespace": cstr(version.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	return doc, statement


def lines_of(basis) -> list[dict[str, Any]]:
	return json.loads(basis.lines or "[]") if basis else []


def expected_revisions(basis) -> dict[str, str]:
	"""The exact revisions Finance reviewed — what Budget must still hold."""
	out = {r["budget_line"]: r["line_version"] for r in lines_of(basis) if r.get("line_version") and flt(r.get("planned")) > 0}
	budget_version = _budget_version_of(basis)
	if budget_version:
		out["budget_version"] = budget_version
	return out


def _budget_version_of(basis) -> str:
	rows = lines_of(basis)
	if not rows:
		return ""
	name = rows[0].get("line_version")
	return cstr(frappe.db.get_value("Procurement Budget Line Version", name, "budget_version")) if name else ""


def current_digest(plan, version) -> str:
	"""The digest the Version's current totals would capture, from the
	non-locking display read (no basis row is written)."""
	totals = readiness.line_totals(version.name)
	statement = budget_gateway.check_plan_affordability(fiscal_year=plan.fiscal_year, planned_totals=totals)
	precision = 2
	rows = []
	for line in statement.get("lines", []):
		rows.append(
			{
				"budget_line": cstr(line.get("budget_line")), "approved": money.money_text(line.get("approved"), precision=precision),
				"planned": money.money_text(line.get("planned"), precision=precision), "funding_source": cstr(line.get("funding_source")),
				"currency": cstr(line.get("currency") or "KES"), "eligible": True,
			}
		)
	for key in statement.get("unknown_lines", []):
		rows.append({"budget_line": cstr(key), "approved": money.money_text(0), "planned": money.money_text(totals.get(key, 0)), "funding_source": "", "currency": "KES", "eligible": False})
	return digest(cstr(statement.get("active_version")), rows)


def basis_of_decision(decision) -> Any:
	"""The basis a Finance decision was made on (through its task)."""
	if not decision:
		return None
	name = frappe.db.get_value("Plan Finance Task", decision.task, "financial_basis")
	return frappe.get_doc(DOCTYPE, name) if name else None


def summary(basis) -> dict[str, Any]:
	if not basis:
		return {}
	return {
		"name": basis.name,
		"basis_digest": basis.basis_digest,
		"budget_basis_digest": cstr(basis.budget_basis_digest),
		"budget_version": _budget_version_of(basis),
		"currency": basis.currency,
		"planned_total": money.money_text(basis.planned_total, precision=int(basis.precision or 2)),
		"approved_total": money.money_text(basis.approved_total, precision=int(basis.precision or 2)),
		"captured_at": cstr(basis.captured_at),
		"lines": lines_of(basis),
	}
