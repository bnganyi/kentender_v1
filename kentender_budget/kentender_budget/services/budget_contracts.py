# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 — Budget/Budget Version identity, drafting and the
canonical position calculations (§5). BUD-UI-01 workspace, BUD-UI-02 version
editor Overview, BUD-UI-03 Overview tab.

Owns: `resolve_budget_context`, `list_available_fiscal_years`,
`save_budget_version_draft`, `create_budget_successor_version`, and the
shared position-calculation helpers every other contract module reuses.
Submit/Return/Approve/Close live in `budget_readiness_contracts.py`; Budget
Line drafting and eligible-line reads live in `budget_line_contracts.py`.

One site is one Procuring Entity (§4.1): every contract here is keyed by
Fiscal Year alone. There is no PE parameter, PE scope check or PE-aware
"working context" anywhere in this module.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate

from kentender_core.services.responsibility_errors import ResponsibilityError
from kentender_budget.services.budget_authorization import (
	CAP_APPROVE,
	CAP_EDIT,
	has_budget_version_capability,
	holds_any_budget_responsibility,
	holds_budget_approver_assignment,
	is_technical,
	require_budget_create_capability,
	require_budget_read_scope,
	require_budget_version_capability,
	require_budget_version_read_scope,
)
from kentender_budget.services.budget_idempotency import run_idempotent
from kentender_budget.services.budget_reference import (
	allocate_budget_line_version_reference,
	allocate_budget_reference,
	allocate_budget_version_reference,
)

_ACTIVE_RESERVATION_STATUSES = ("Active", "Partially Converted", "Needs Attention")


def format_kes_compact(amount: float | None, *, currency: str = "KES") -> str:
	val = flt(amount)
	if abs(val) >= 1_000_000:
		m = val / 1_000_000.0
		if abs(m - round(m)) < 0.05:
			return f"{currency} {int(round(m))}M"
		text = f"{m:.1f}".rstrip("0").rstrip(".")
		return f"{currency} {text}M"
	return f"{currency} {val:,.0f}"


def format_kes_full(amount: float | None, *, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.0f}"


def list_available_fiscal_years() -> list[str]:
	"""§9.1 — the Fiscal Year catalogue for a Budget-owned FY-only filter
	(BUD-CHG-001 v1.3 Phase 7 UI), mirroring
	`kentender_strategy.services.strategy_ui_contracts.list_available_fiscal_years`.
	`ignore_permissions` is safe here for the same reason: Fiscal Year rows
	carry only date ranges, and Budget has no create/write path onto the
	doctype regardless."""
	rows = frappe.get_all(
		"Fiscal Year", fields=["name"], order_by="year_start_date desc", limit_page_length=0, ignore_permissions=True
	)
	return [r.name for r in rows]


def _org_unit_label(org_unit: str | None) -> str:
	"""Empty owner_org_unit means every source department may draw on the
	line (BUD-CHG-001 v1.9 §4.9 label "All departments"; the stored value is
	unchanged) — that reads as a real label everywhere it's displayed, not a
	blank cell."""
	if not org_unit:
		return _("All departments")
	return frappe.db.get_value("Organisation Unit", org_unit, "unit_name") or org_unit


def _user_label(user: str | None) -> str:
	if not user:
		return ""
	return frappe.db.get_value("User", user, "full_name") or user


def _display_datetime(value) -> str:
	"""KT-STD-001 §8 fixture instants read "3 Oct 2026, 11:15 EAT" on every
	Budget artboard — the same rendering Procurement Planning's read models
	use, not the System Settings dd-mm-yyyy default. Budget Version lifecycle
	timestamps are stored by `now_datetime()` in the site timezone
	(Africa/Nairobi), so they are formatted as-is, without a UTC conversion."""
	from frappe.utils import format_datetime, get_datetime

	if not value:
		return ""
	return f"{format_datetime(get_datetime(value), 'd MMM yyyy, HH:mm')} EAT"


def _display_date(value) -> str:
	from frappe.utils import formatdate

	if not value:
		return ""
	return formatdate(value, "d MMM yyyy")


def _funding_source_label(funding_source: str | None) -> str:
	if not funding_source:
		return ""
	return frappe.db.get_value("Funding Source", funding_source, "label") or funding_source


def _resolve_budget(key: str) -> Any:
	"""Resolve Budget by generated_reference or document name."""
	key = (key or "").strip()
	if not key:
		frappe.throw(_("Budget is required"), frappe.ValidationError)
	name = frappe.db.get_value("Procurement Budget", {"generated_reference": key}, "name")
	if not name and frappe.db.exists("Procurement Budget", key):
		name = key
	if not name:
		frappe.throw(_("Budget {0} not found").format(key), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	return frappe.get_doc("Procurement Budget", name)


def _resolve_budget_version(key: str) -> Any:
	"""Resolve Budget Version by generated_reference or document name."""
	key = (key or "").strip()
	if not key:
		frappe.throw(_("Budget Version is required"), frappe.ValidationError)
	name = frappe.db.get_value("Procurement Budget Version", {"generated_reference": key}, "name")
	if not name and frappe.db.exists("Procurement Budget Version", key):
		name = key
	if not name:
		frappe.throw(_("Budget Version {0} not found").format(key), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	return frappe.get_doc("Procurement Budget Version", name)


def _resolve_budget_line(key: str) -> Any:
	"""Resolve Budget Line by generated_reference or document name — same
	dual-lookup pattern as _resolve_budget/_resolve_budget_version. Every URL
	that carries a Budget Line uses its code (line.code, e.g. via `go("line",
	line.code)`), never the raw hash docname."""
	key = (key or "").strip()
	if not key:
		frappe.throw(_("Budget Line is required"), frappe.ValidationError)
	name = frappe.db.get_value("Procurement Budget Line", {"generated_reference": key}, "name")
	if not name and frappe.db.exists("Procurement Budget Line", key):
		name = key
	if not name:
		frappe.throw(_("Budget Line {0} not found").format(key), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	return frappe.get_doc("Procurement Budget Line", name)


def _active_version(budget_name: str) -> Any | None:
	names = frappe.get_all("Procurement Budget Version", filters={"budget": budget_name, "status": "Active"}, pluck="name")
	if not names:
		return None
	if len(names) > 1:
		# BUD-BR-002 makes this unreachable in correctly-functioning code (the
		# database-level partial unique index is the real guard); kept as a
		# defensive check against a data-integrity bug, not a scope error.
		frappe.throw(_("Multiple Active Budget Versions found for this Budget"), frappe.ValidationError)
	return frappe.get_doc("Procurement Budget Version", names[0])


def _draft_version(budget_name: str) -> Any | None:
	"""At most one open (Draft or Submitted for approval) successor may exist (§6.2)."""
	names = frappe.get_all(
		"Procurement Budget Version",
		filters={"budget": budget_name, "status": ["in", ("Draft", "Submitted for approval")]},
		pluck="name",
		order_by="version_number desc",
	)
	return frappe.get_doc("Procurement Budget Version", names[0]) if names else None


def _line_position(budget_line_name: str, budget_line_version) -> dict[str, float]:
	"""§5 canonical calculation for one Budget Line at the current time.

	`budget_line_version` supplies `approved_amount`; Reserved/Committed are
	summed from the stable Budget Line identity's reservations/commitments,
	independent of which version is being displayed.
	"""
	approved = flt(budget_line_version.approved_amount) if budget_line_version else 0.0

	reserved = flt(
		frappe.db.sql(
			"select coalesce(sum(remaining_amount), 0) from `tabFunding Reservation` "
			"where budget_line = %s and status in %s",
			(budget_line_name, _ACTIVE_RESERVATION_STATUSES),
		)[0][0]
	)

	all_reservations = frappe.get_all("Funding Reservation", filters={"budget_line": budget_line_name}, pluck="name")
	committed = 0.0
	if all_reservations:
		committed = flt(
			frappe.db.sql(
				"select coalesce(sum(current_amount), 0) from `tabProcurement Commitment` "
				"where reservation in %s and status = 'Active'",
				(all_reservations,),
			)[0][0]
		)

	available = approved - reserved - committed
	return {"approved": approved, "reserved": reserved, "committed": committed, "available": available}


def _line_version_for(budget_version_name: str, budget_line_name: str):
	name = frappe.db.get_value(
		"Procurement Budget Line Version", {"budget_version": budget_version_name, "budget_line": budget_line_name}, "name"
	)
	return frappe.get_doc("Procurement Budget Line Version", name) if name else None


def _plan_item_label(plan_item: str | None) -> str:
	"""Budget Line detail's Active reservations table shows the Plan Item's
	human reference ("PPI-MOH-2027-001 · National digital health
	infrastructure upgrade"), not its raw docname. `Funding Reservation.plan_item`
	only stores kentender_procurement's own docname (a plain Data field, not a
	Link — no schema coupling), so this reads the Plan Item's own fields
	directly via frappe.db, the same cross-app read pattern already used for
	Organisation Unit/Fiscal Year/Funding Source. PLN-CHG-001 v1.2's
	rebuild replaced the Demand-era `Procurement Plan Item` (whose table was
	dropped outright) with `Annual Plan Item` — reading the retired name
	crashed every Budget position read that met a reservation, so this now
	reads the live model and degrades to the raw reference for any row a
	sibling test fixture wrote with a synthetic id."""
	if not plan_item:
		return ""
	if not frappe.db.exists("DocType", "Annual Plan Item"):
		return plan_item
	row = frappe.db.get_value(
		"Annual Plan Item", plan_item, ["plan_item_id", "title"], as_dict=True
	)
	if not row:
		return plan_item
	return f"{row.plan_item_id} · {row.title}" if row.title else cstr(row.plan_item_id)


def _plan_item_url(plan_item: str | None) -> str:
	if not plan_item or not frappe.db.exists("DocType", "Annual Plan Item"):
		return ""
	plan_item_id = frappe.db.get_value("Annual Plan Item", plan_item, "plan_item_id")
	return f"/app/procurement-plan-item/{plan_item_id}" if plan_item_id else ""


def _reservation_ledger_sums(reservation: str) -> dict[str, float]:
	"""Conservation (§4.6): original = remaining + converted + released, read
	from the reservation's own ledger rows."""
	rows = frappe.get_all(
		"Budget Audit Event",
		filters={"reservation": reservation, "event_type": ["in", ["Contract commitment recorded", "Reservation partially converted", "Reservation released"]]},
		fields=["event_type", "amount"],
	)
	converted = sum(flt(r.amount) for r in rows if r.event_type in ("Contract commitment recorded", "Reservation partially converted"))
	released = sum(flt(r.amount) for r in rows if r.event_type == "Reservation released")
	return {"converted": converted, "released": released}


_REVIEW_REASONS = {
	"BUDGET_LINE_FLOOR_BREACH": (
		"The budget line's registered allocation no longer covers this reservation after the last allocation update.",
		"The owning Requisition must be revalidated by its Procurement owner before it can progress.",
	),
}


def _requires_review_facts(reservation: str) -> dict[str, str] | None:
	"""§11.19 — the typed reason behind a Needs Attention hold, read from the
	latest `Reservation revalidated` ledger event (tracker D5)."""
	row = frappe.db.get_value(
		"Budget Audit Event",
		{"reservation": reservation, "event_type": "Reservation revalidated", "revalidation_failure_code": ["!=", ""]},
		["revalidation_failure_code", "downstream_reference", "event_at"],
		order_by="event_at desc",
		as_dict=True,
	)
	code = (row.revalidation_failure_code if row else "") or "BUDGET_LINE_FLOOR_BREACH"
	reason, owner_hint = _REVIEW_REASONS.get(code, ("This reservation requires review by its owner.", "The owning Requisition or Contract process must resolve it."))
	return {"code": code, "reason": reason, "owner_hint": owner_hint, "since_display": _display_datetime(row.event_at) if row else ""}


def _requisition_facts(caller_reference: str, calling_module: str) -> dict[str, str]:
	"""The owning Requisition, by its stable reference, with a route only when
	the record resolves and the caller may read it (§12.4: never a guessed
	route). Tracker D6: derived from `caller_reference`, no schema coupling."""
	ref = (caller_reference or "").strip()
	if not ref or not frappe.db.exists("DocType", "Procurement Requisition"):
		return {"requisition_reference": ref, "requisition_url": ""}
	name = frappe.db.get_value("Procurement Requisition", {"requisition_reference": ref}, "name")
	if not name:
		return {"requisition_reference": ref, "requisition_url": ""}
	try:
		readable = frappe.has_permission("Procurement Requisition", doc=name, user=frappe.session.user)
	except Exception:
		readable = False
	return {"requisition_reference": ref, "requisition_url": f"/app/procurement-requisitions/{ref}/authorised" if readable else ""}


def _source_department(plan_source_allocation: str | None) -> str:
	"""The exact source department of the drawn Planning allocation (§4.5) via
	Planning's own record, labelled through the Organisation Unit name."""
	if not plan_source_allocation or not frappe.db.exists("DocType", "Plan Source Allocation"):
		return ""
	unit = frappe.db.get_value("Plan Source Allocation", plan_source_allocation, "organisation_unit")
	if not unit:
		return ""
	return frappe.db.get_value("Organisation Unit", unit, "unit_name") or unit


def _line_active_reservations(budget_line: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Funding Reservation",
		filters={"budget_line": budget_line, "status": ["in", _ACTIVE_RESERVATION_STATUSES]},
		fields=["name", "generated_reference", "plan_item", "plan_source_allocation", "original_amount", "remaining_amount", "status", "caller_reference", "calling_module", "currency"],
		order_by="creation asc",
	)
	out = []
	for r in rows:
		sums = _reservation_ledger_sums(r.name)
		requires_review = r.status == "Needs Attention"
		source = _source_department(r.plan_source_allocation)
		req = _requisition_facts(r.caller_reference, r.calling_module)
		lead = req["requisition_reference"] or _plan_item_label(r.plan_item) or r.generated_reference
		out.append(
			{
				"id": r.name,
				"code": r.generated_reference,
				"title": f"{lead} · {source} source" if source else lead,
				"source_department": source,
				**req,
				"plan_item_label": _plan_item_label(r.plan_item),
				"plan_item_url": _plan_item_url(r.plan_item),
				"original_amount": flt(r.original_amount),
				"remaining_amount": flt(r.remaining_amount),
				"originally_reserved": flt(r.original_amount),
				"still_reserved": flt(r.remaining_amount),
				"converted": sums["converted"],
				"released": sums["released"],
				"status": r.status,
				"status_label": _("Requires review — funds remain reserved") if requires_review else (_("Partially converted") if r.status == "Partially Converted" else _("Active")),
				"requires_review": requires_review,
				"review": _requires_review_facts(r.name) if requires_review else None,
				"currency": r.currency or "KES",
			}
		)
	return out


def get_budget_line_position(budget_line: str, *, as_at_version: str | None = None) -> dict[str, Any]:
	"""§9.1 `get_budget_line_position` — authorised line identity, active-version
	amount and current positions. No mutation. BUD-UI-05 Budget Line detail."""
	verdict = forbidden_verdict()
	if verdict:
		return verdict
	try:
		line = _resolve_budget_line(budget_line)
	except frappe.DoesNotExistError:
		frappe.clear_last_message()
		return dict(NOT_FOUND)
	require_budget_read_scope("Procurement Budget Line", line.name)
	owning_version = _line_owning_version(line.name, as_at_version)
	budget = frappe.get_doc("Procurement Budget", line.budget)
	version_name = as_at_version or owning_version.name
	line_version = _line_version_for(version_name, line.name) if version_name else None
	position = _line_position(line.name, line_version)
	reservations = _line_active_reservations(line.name)
	converted_total = sum(r["converted"] for r in reservations)
	currency = line_version.currency if line_version else "KES"
	explanation = ""
	if position["committed"] > 0 and converted_total > 0:
		explanation = _("{0} of the reservation is now committed to a contract. The remaining reservation is {1}. No payment is recorded here.").format(
			format_kes_full(converted_total, currency=currency), format_kes_full(position["reserved"], currency=currency)
		)
	return {
		"id": line.name,
		"code": line.generated_reference,
		"as_at_display": _display_datetime(frappe.utils.now_datetime()),
		"explanation": explanation,
		"title": line_version.title if line_version else "",
		"owner_org_unit": _org_unit_label(line_version.owner_org_unit) if line_version else "",
		"funding_source": _funding_source_label(line_version.funding_source) if line_version else "",
		"currency": line_version.currency if line_version else "KES",
		"positions": position,
		"budget": {
			"id": budget.name,
			"code": budget.generated_reference,
			"fiscal_year": {"id": budget.fiscal_year, "label": budget.fiscal_year},
		},
		"version": {
			"id": owning_version.name,
			"version_number": owning_version.version_number,
			"status": owning_version.status,
		},
		"reservations": reservations,
	}


def _active_version_name_for_line(budget_line: str) -> str | None:
	budget_name = frappe.db.get_value("Procurement Budget Line", budget_line, "budget")
	version = _active_version(budget_name) if budget_name else None
	return version.name if version else None


def _line_owning_version(budget_line: str, as_at_version: str | None):
	version_name = as_at_version or _active_version_name_for_line(budget_line)
	if not version_name:
		frappe.throw(_("Budget Line has no resolvable version context"), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	return frappe.get_doc("Procurement Budget Version", version_name)


def _version_totals(budget_version_name: str) -> dict[str, float]:
	"""Budget totals are the sums of the Version's line positions (§5)."""
	line_versions = frappe.get_all(
		"Procurement Budget Line Version",
		filters={"budget_version": budget_version_name},
		fields=["budget_line", "approved_amount", "title", "owner_org_unit", "funding_source", "currency"],
		# Deterministic display order (BUD-DES-01/05 list lines by title) —
		# the same `title asc` every other Budget Lines read model uses;
		# without it MariaDB returned the rows in insertion-dependent order.
		order_by="title asc",
	)
	approved = reserved = committed = available = 0.0
	lines: list[dict[str, Any]] = []
	codes = (
		{
			r.name: r.generated_reference
			for r in frappe.get_all(
				"Procurement Budget Line", filters={"name": ["in", [lv.budget_line for lv in line_versions]]}, fields=["name", "generated_reference"]
			)
		}
		if line_versions
		else {}
	)
	for lv in line_versions:
		pos = _line_position(lv.budget_line, lv)
		approved += pos["approved"]
		reserved += pos["reserved"]
		committed += pos["committed"]
		available += pos["available"]
		lines.append(
			{
				**lv,
				"code": codes.get(lv.budget_line, ""),
				"owner_org_unit_label": _org_unit_label(lv.owner_org_unit),
				"funding_source_label": _funding_source_label(lv.funding_source),
				"positions": pos,
			}
		)
	return {
		"approved": approved,
		"reserved": reserved,
		"committed": committed,
		"available": available,
		"lines": lines,
	}


def resolve_budget_context(fiscal_year: str | None = None) -> dict[str, Any]:
	"""§9.1 `resolve_budget_context` — the Active Budget/Version summary for a
	Fiscal Year, or a typed not-found error. Never a first-record or
	Administrator fallback (BUD-BR-001)."""
	fy = (fiscal_year or "").strip()
	if not fy:
		frappe.throw(_("Fiscal Year is required"), frappe.ValidationError)
	if not frappe.db.exists("Fiscal Year", fy):
		frappe.throw(_("Fiscal Year {0} not found").format(fy), frappe.DoesNotExistError, title="BUDGET_CONFIG_MISSING")

	budget_name = frappe.db.get_value("Procurement Budget", {"fiscal_year": fy}, "name")
	if not budget_name:
		frappe.throw(
			_("No Budget is registered for this Fiscal Year"),
			frappe.DoesNotExistError,
			title="BUDGET_CONTEXT_NOT_FOUND",
		)
	budget = frappe.get_doc("Procurement Budget", budget_name)
	require_budget_read_scope("Procurement Budget", budget.name)
	version = _active_version(budget_name)
	if not version:
		return {"budget": _budget_summary(budget), "version": None}
	return {"budget": _budget_summary(budget), "version": _version_summary(version)}


def _budget_summary(budget) -> dict[str, Any]:
	return {
		"id": budget.name,
		"code": budget.generated_reference,
		"title": budget.title,
		"fiscal_year": {"id": budget.fiscal_year, "label": budget.fiscal_year},
		"currency": budget.currency,
	}


def _version_summary(version) -> dict[str, Any]:
	return {
		"id": version.name,
		"code": version.generated_reference,
		"version_number": version.version_number,
		"status": version.status,
		"approval_reference": version.approval_reference,
		# ISO (yyyy-mm-dd) — the version editor binds this straight into an
		# <input type=date>. approval_date_display is the read-only sibling
		# ("30 Sep 2026") for Workspace/Detail cards; keep both in sync here
		# rather than at each call site.
		"approval_date": str(version.approval_date) if version.approval_date else "",
		"approval_date_display": _display_date(version.approval_date),
		"authorised_total": flt(version.authorised_total),
		"budget": version.budget,
		"revision_type": version.revision_type or "",
		"based_on": version.based_on_budget_version or None,
		# The optimistic-lock stamp every command sends back as expected_modified.
		"modified": str(version.modified) if version.modified else "",
	}


def _closed_version(budget_name: str) -> Any | None:
	names = frappe.get_all(
		"Procurement Budget Version", filters={"budget": budget_name, "status": "Closed"}, order_by="version_number desc", limit=1, pluck="name"
	)
	return frappe.get_doc("Procurement Budget Version", names[0]) if names else None


def _current_or_closed_version(budget_name: str) -> Any | None:
	"""The version a read-only Budget workspace shows: the Active one, or the
	Closed one after year-end closure (BUD-CHG-001 v1.9 §11.1B/§11.18)."""
	return _active_version(budget_name) or _closed_version(budget_name)


def _closure_summary(version) -> dict[str, Any]:
	if not version or version.status != "Closed":
		return {"state": "open"}
	return {
		"state": "closed",
		"closed_by": _user_label(version.closed_by),
		"closed_at": str(version.closed_at) if version.closed_at else "",
		"closed_at_display": _display_datetime(version.closed_at),
	}


def _fy_end_display(fiscal_year: str) -> str:
	end = frappe.db.get_value("Fiscal Year", fiscal_year, "year_end_date")
	return _display_date(end) if end else ""



# KT-STD-001 v1.2 §3A.4 — resolved once here, never raised, so a page load
# with no matching responsibility renders the inline Forbidden panel instead
# of the framework's own permission-error modal.
FORBIDDEN = {
	"heading": "You do not have access to Budget & Funding",
	"text": (
		"This area needs one of these responsibilities: Budget Officer, Budget "
		"Approver, Finance Confirmation Officer or Auditor. Ask your KenTender "
		"administrator to assign one in System setup."
	),
}

# §12.5 — the approval task opens only for a Budget Approver; a read-only
# actor is denied rather than shown the task with its controls removed.
FORBIDDEN_TASK = {
	"heading": "You do not have access to this approval task",
	"text": (
		"Approval tasks open only for a Budget Approver. Ask your KenTender "
		"administrator to assign that responsibility in System setup."
	),
}

NOT_FOUND = {"outcome": "NOT_FOUND"}


def forbidden_verdict(user: str | None = None) -> dict[str, Any] | None:
	"""KT-STD-001 v1.2 §3A.2 — a page-load denial is never a modal. Every
	direct-route read (BUD-UI-02..05) resolves this first and returns it as
	data; raising `frappe.PermissionError` would answer HTTP 403, which
	Frappe's own request handler turns into a "Not permitted" dialog on top
	of the screen's inline Forbidden panel (confirmed live, 2026-09-06)."""
	if holds_any_budget_responsibility(user):
		return None
	return {"outcome": "FORBIDDEN", "forbidden": FORBIDDEN}


def forbidden_task_verdict(user: str | None = None) -> dict[str, Any] | None:
	if holds_budget_approver_assignment(user):
		return None
	return {"outcome": "FORBIDDEN", "forbidden": FORBIDDEN_TASK}


def get_budget_workspace(fiscal_year: str | None = None) -> dict[str, Any]:
	"""BUD-UI-01 — the selected Fiscal Year's existing Draft/submission,
	current Budget and operational position, with the §11.1B state matrix and
	the server-decided `available_actions` (BUD-CHG-001 v1.9 §12.1).

	One site is one Procuring Entity: the caller supplies a Fiscal Year
	directly; when it does not, this never guesses "today's" year — it
	returns selection_required with the full catalogue."""
	if not holds_any_budget_responsibility(frappe.session.user):
		return {"outcome": "FORBIDDEN", "forbidden": FORBIDDEN}
	fy = (fiscal_year or "").strip()
	if not fy:
		return {"selection_required": True, "fiscal_years": list_available_fiscal_years()}
	if not frappe.db.exists("Fiscal Year", fy):
		frappe.throw(_("Fiscal Year {0} not found").format(fy), frappe.DoesNotExistError, title="BUDGET_CONFIG_MISSING")

	result: dict[str, Any] = {
		"selection_required": False,
		"fiscal_year": {"id": fy, "label": fy},
		"has_budget": False,
		"can_register": False,
		"state": "no_record",
		"available_actions": [],
	}

	budget_name = frappe.db.get_value("Procurement Budget", {"fiscal_year": fy}, "name")
	if not budget_name:
		try:
			require_budget_create_capability(frappe.session.user)
			result["can_register"] = True
			result["available_actions"].append("record_allocation")
		except ResponsibilityError:
			# A reader with no Budget Officer assignment simply doesn't get the
			# register action, not an error (closed §10 vocabulary).
			pass
		return result

	budget = frappe.get_doc("Procurement Budget", budget_name)
	require_budget_read_scope("Procurement Budget", budget.name)
	active = _active_version(budget_name)
	closed = None if active else _closed_version(budget_name)
	result["has_budget"] = True
	result["budget"] = _budget_summary(budget)
	pending = _pending_version_summary(budget_name, frappe.session.user)
	if pending:
		result["pending_version"] = pending
		result["available_actions"].append(pending["action"])

	if not active and not closed:
		# A Budget row exists but nothing has been activated yet (§11.1B):
		# never a current position, never a zero, never a second Register.
		if pending:
			if pending["status"] == "Submitted for approval":
				result["state"] = "initial_submitted"
			elif pending["is_returned"]:
				result["state"] = "returned_draft"
			else:
				result["state"] = "initial_draft"
		else:
			result["state"] = "initial_pending_hidden"
		return result

	version = active or closed
	totals = _version_totals(version.name)
	result["version"] = _version_summary(version)
	result["positions"] = {
		"approved": totals["approved"],
		"reserved": totals["reserved"],
		"committed": totals["committed"],
		"available": totals["available"],
	}
	result["positions_as_at_display"] = _display_datetime(frappe.utils.now_datetime())
	result["lines_preview"] = [_line_preview_row(row) for row in totals["lines"][:5]]
	result["closure"] = _closure_summary(version)
	if closed:
		result["state"] = "closed"
		result["can_create_revision"] = False
		result["available_actions"].append("view_budget")
		return result

	result["can_create_revision"] = not pending and has_budget_version_capability(frappe.session.user, CAP_EDIT, version)
	result["available_actions"].append("view_budget")
	if result["can_create_revision"]:
		result["available_actions"].append("update_allocation")
	if pending:
		result["state"] = "current_with_submitted" if pending["status"] == "Submitted for approval" else "current_with_draft"
	else:
		result["state"] = "current"
	return result


def _pending_version_summary(budget_name: str, user: str) -> dict[str, Any] | None:
	"""The one open (Draft or Submitted for approval) version on this Budget
	— an unactivated baseline or a successor — with the action the caller may
	take on it, decided here (AGENTS.md §6.2), never from status client-side:

	- `continue_draft` / `continue_update` / `correct_and_resubmit`
	                    the Budget Officer continues an editable Draft;
	- `review`          the Budget Approver decides a Submitted version;
	- `view_submission` the submitting Officer (or an authorised reader) sees
	                    the read-only submitted version;
	- `view_draft`      an authorised reader inspects a Draft read-only;
	- `view_version_readonly`
	                    AUTH §8 technical readers (Administrator / System
	                    Manager) with no Budget business assignment — the
	                    §12.1 correction: a fourth outcome, never nothing.

	A reader who cannot read the version at all gets no disclosure that an
	open version exists (§12.1's no-disclosure principle)."""
	pending = _draft_version(budget_name)
	if not pending:
		return None
	is_successor = bool(pending.based_on_budget_version)
	is_returned = pending.status == "Draft" and bool((pending.return_reason or "").strip())
	action = None
	if pending.status == "Draft":
		if has_budget_version_capability(user, CAP_EDIT, pending):
			action = "correct_and_resubmit" if is_returned else ("continue_update" if is_successor else "continue_draft")
	elif pending.status == "Submitted for approval":
		if has_budget_version_capability(user, CAP_APPROVE, pending):
			action = "review"
		elif has_budget_version_capability(user, CAP_EDIT, pending):
			action = "view_submission"
	if not action:
		if is_technical(user):
			action = "view_version_readonly"
		elif frappe.has_permission("Procurement Budget Version", doc=pending.name, user=user):
			action = "view_submission" if pending.status == "Submitted for approval" else "view_draft"
	if not action:
		return None
	return {
		"id": pending.name,
		"code": pending.generated_reference,
		"version_number": pending.version_number,
		"status": pending.status,
		"is_successor": is_successor,
		"is_returned": is_returned,
		"revision_type": pending.revision_type or "",
		"action": action,
		"submitted_by": _user_label(pending.submitted_by),
		"submitted_at_display": _display_datetime(pending.submitted_at),
		"last_saved_display": _display_datetime(pending.modified),
		"return": (
			{"reason": pending.return_reason, "by": _user_label(pending.decided_by), "at_display": _display_datetime(pending.decided_at)}
			if is_returned
			else None
		),
	}


def _line_preview_row(row: dict[str, Any]) -> dict[str, Any]:
	pos = row["positions"]
	return {
		"id": row["budget_line"],
		"code": row.get("code", ""),
		"title": row["title"],
		"owner_org_unit": row.get("owner_org_unit_label", ""),
		"approved": pos["approved"],
		"reserved": pos["reserved"],
		"committed": pos["committed"],
		"available": pos["available"],
	}


def get_budget_version_draft(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-02 Overview tab — the Draft (or Submitted) version's own field
	values, for the version editor form."""
	verdict = forbidden_verdict()
	if verdict:
		return verdict
	try:
		version = _resolve_budget_version(budget_version)
	except frappe.DoesNotExistError:
		frappe.clear_last_message()
		return dict(NOT_FOUND)
	require_budget_version_read_scope(version)
	budget = frappe.get_doc("Procurement Budget", version.budget)
	return {
		"budget": _budget_summary(budget),
		"version": _version_summary(version),
		"based_on": _version_summary(frappe.get_doc("Procurement Budget Version", version.based_on_budget_version))
		if version.based_on_budget_version
		else None,
		"revision_type": version.revision_type or "",
		"approval_document": version.approval_document or "",
		"can_edit": version.status == "Draft" and has_budget_version_capability(frappe.session.user, CAP_EDIT, version),
		# §6 — a Return carries a required reason; the Officer correcting the
		# Draft needs to see it on the editor, not only in the History tab.
		# `submit_budget_version` clears it again on resubmission.
		"returned": (
			{
				"reason": version.return_reason,
				"by": _user_label(version.decided_by),
				"at": _display_datetime(version.decided_at),
			}
			if version.status == "Draft" and (version.return_reason or "").strip()
			else None
		),
	}


def get_budget_detail(budget: str) -> dict[str, Any]:
	"""BUD-UI-03 Overview tab — Active (or Closed) read-only funding position
	+ context, with the server-decided `available_actions` and the closure
	summary (BUD-CHG-001 v1.9 §11.4/§11.18)."""
	verdict = forbidden_verdict()
	if verdict:
		return verdict
	try:
		doc = _resolve_budget(budget)
	except frappe.DoesNotExistError:
		frappe.clear_last_message()
		return dict(NOT_FOUND)
	version = _current_or_closed_version(doc.name)
	if not version:
		return dict(NOT_FOUND)
	require_budget_version_read_scope(version)
	totals = _version_totals(version.name)
	pending = _pending_version_summary(doc.name, frappe.session.user)
	is_active = version.status == "Active"
	can_update = is_active and not pending and has_budget_version_capability(frappe.session.user, CAP_EDIT, version)
	can_close = is_active and has_budget_version_capability(frappe.session.user, CAP_APPROVE, version)
	actions = []
	if can_update:
		actions.append("update_allocation")
	if pending:
		actions.append(pending["action"])
	if can_close:
		actions.append("close_budget")
	return {
		"budget": _budget_summary(doc),
		"version": _version_summary(version),
		"positions": {
			"approved": totals["approved"],
			"reserved": totals["reserved"],
			"committed": totals["committed"],
			"available": totals["available"],
		},
		"positions_as_at_display": _display_datetime(frappe.utils.now_datetime()),
		"approval_document": version.approval_document,
		"document": {"name": (version.approval_document or "").split("/").pop() if version.approval_document else "", "url": version.approval_document or ""},
		"activation": {
			"submitted_by": _user_label(version.submitted_by),
			"submitted_at": _display_datetime(version.submitted_at),
			"decided_by": _user_label(version.decided_by),
			"decided_at": _display_datetime(version.decided_at),
		},
		"closure": {**_closure_summary(version), "fy_end_date_display": _fy_end_display(doc.fiscal_year)},
		"can_create_revision": can_update,
		"available_actions": actions,
		# §6: at most one open successor per Budget — when one exists the
		# header offers it (open/decide) instead of Update registered allocation.
		"pending_version": pending,
	}


def _validate_draft_payload(payload: dict) -> dict[str, str]:
	errors: dict[str, str] = {}
	approval_reference = (payload.get("approval_reference") or "").strip()
	approval_date = payload.get("approval_date")
	total = payload.get("authorised_total")

	if not approval_reference:
		errors["approval_reference"] = _("Approval reference is required")
	if not approval_date:
		errors["approval_date"] = _("Approval date is required")
	else:
		try:
			if getdate(approval_date) > getdate():
				errors["approval_date"] = _("Approval date cannot be in the future")
		except Exception:
			errors["approval_date"] = _("Enter a valid approval date")
	try:
		total_val = flt(total)
	except Exception:
		total_val = 0
	if not total or total_val <= 0:
		errors["authorised_total"] = _("Approved allocation must be greater than zero")
	return errors


def save_budget_version_draft(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `save_budget_version_draft` — create or update Draft approval
	details with optimistic concurrency. Creates the Budget on first save.
	Typed results, never a modal: BUDGET_ALREADY_EXISTS carries the existing
	authorised route; BUDGET_STALE_WRITE carries the current stamp (§9.3/§13)."""
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	payload = payload or {}
	return run_idempotent(payload=payload, fn=lambda: _save_budget_version_draft(payload), budget_for=lambda r: (r.get("budget") or {}).get("id") if isinstance(r.get("budget"), dict) else (r.get("version") or {}).get("budget"))


def _save_budget_version_draft(payload: dict[str, Any]) -> dict[str, Any]:
	budget_key = (payload.get("budget") or "").strip()
	version_key = (payload.get("budget_version") or "").strip()

	if not budget_key and not version_key:
		# One site is one Procuring Entity: the caller supplies the Fiscal
		# Year directly, not a PE+FY working-context id.
		fy = (payload.get("fiscal_year") or "").strip()
		if not fy:
			return {"ok": False, "errors": {"fiscal_year": _("A Fiscal Year is required")}}
		if not frappe.db.exists("Fiscal Year", fy):
			frappe.throw(_("Fiscal Year {0} not found").format(fy), frappe.DoesNotExistError, title="BUDGET_CONFIG_MISSING")
		require_budget_create_capability(frappe.session.user)
		existing_name = frappe.db.get_value("Procurement Budget", {"fiscal_year": fy}, "name")
		if existing_name:
			existing = frappe.get_doc("Procurement Budget", existing_name)
			pending = _pending_version_summary(existing.name, frappe.session.user)
			return {
				"ok": False,
				"code": "BUDGET_ALREADY_EXISTS",
				"errors": {"fiscal_year": _("An allocation record already exists for this financial year. Open it to continue.")},
				"budget": _budget_summary(existing),
				"pending_version": pending,
				"route": _pending_route(existing, pending),
			}
		errors = _validate_draft_payload(payload)
		if errors:
			return {"ok": False, "errors": errors}
		if not (payload.get("approval_document") or "").strip():
			# §9.3 — the four approval details, including one uploaded/linked
			# document, precede Save and add budget lines.
			return {"ok": False, "errors": {"approval_document": _("Attach the approval document before saving.")}}

		budget = frappe.get_doc(
			{
				"doctype": "Procurement Budget",
				"generated_reference": allocate_budget_reference(fy),
				"fiscal_year": fy,
				"currency": (payload.get("currency") or "KES").strip(),
			}
		)
		budget.insert(ignore_permissions=True)
		version = _create_draft_version(budget, payload, based_on=None)
		return {"ok": True, "saved_scope": "approval_details", "created": True, "budget": _budget_summary(budget), "version": _version_summary(version)}

	if version_key:
		version = _resolve_budget_version(version_key)
	else:
		budget = _resolve_budget(budget_key)
		version = _draft_version(budget.name)
		if not version:
			frappe.throw(_("No Draft Budget Version to update"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	require_budget_version_capability(frappe.session.user, CAP_EDIT, version)
	if version.status != "Draft":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}

	expected_version = payload.get("expected_modified")
	if expected_version and str(version.modified) != str(expected_version):
		return {
			"ok": False,
			"code": "BUDGET_STALE_WRITE",
			"errors": {"expected_modified": _("This budget has changed since you opened it. Refresh to see the current details.")},
			"version": _version_summary(version),
		}

	errors = _validate_draft_payload(payload)
	if errors:
		return {"ok": False, "errors": errors}

	version.approval_reference = (payload.get("approval_reference") or "").strip()
	version.approval_date = getdate(payload.get("approval_date"))
	version.authorised_total = flt(payload.get("authorised_total"))
	if payload.get("approval_document"):
		version.approval_document = payload["approval_document"]
	if version.based_on_budget_version and payload.get("revision_type"):
		version.revision_type = payload["revision_type"]
	version.save(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_DRAFT_APPROVAL_SAVED, safe_record_event

	safe_record_event(
		budget=version.budget,
		budget_version=version.name,
		event_type=EVENT_DRAFT_APPROVAL_SAVED,
		actor=frappe.session.user,
		correlation_id=frappe.generate_hash(length=12),
		calling_module="Budget & Funding",
	)
	version.reload()
	return {"ok": True, "saved_scope": "approval_details", "version": _version_summary(version)}


def _pending_route(budget, pending: dict[str, Any] | None) -> list[str]:
	"""The authorised route for an existing record (§13 BUDGET_ALREADY_EXISTS):
	the pending version's own editor/review route, else the Budget workspace."""
	if pending and pending["action"] == "review":
		return ["budget-funding", "review", pending["id"]]
	if pending:
		return ["budget-funding", budget.generated_reference, "version", str(pending["version_number"]), "edit"]
	return ["budget-funding", budget.generated_reference]


def _create_draft_version(budget, payload: dict, *, based_on) -> Any:
	next_number = (
		frappe.db.count("Procurement Budget Version", {"budget": budget.name}) + 1
		if not based_on
		else (based_on.version_number + 1)
	)
	version = frappe.get_doc(
		{
			"doctype": "Procurement Budget Version",
			"generated_reference": allocate_budget_version_reference(budget.generated_reference, next_number),
			"budget": budget.name,
			"version_number": next_number,
			"based_on_budget_version": based_on.name if based_on else None,
			"revision_type": payload.get("revision_type") if based_on else None,
			"status": "Draft",
			"approval_reference": (payload.get("approval_reference") or "").strip(),
			"approval_date": getdate(payload.get("approval_date")) if payload.get("approval_date") else None,
			"authorised_total": flt(payload.get("authorised_total")) if payload.get("authorised_total") else None,
			"approval_document": payload.get("approval_document") or None,
			"currency": budget.currency,
			"submitted_by": None,
		}
	)
	version.insert(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_VERSION_CREATED, safe_record_event

	safe_record_event(
		budget=budget.name,
		budget_version=version.name,
		event_type=EVENT_VERSION_CREATED,
		actor=frappe.session.user,
		correlation_id=frappe.generate_hash(length=12),
		calling_module="Budget & Funding",
	)

	if based_on:
		_copy_line_versions(based_on, version)
	return version


def _copy_line_versions(source_version, target_version) -> None:
	rows = frappe.get_all(
		"Procurement Budget Line Version",
		filters={"budget_version": source_version.name},
		fields=["budget_line", "title", "owner_org_unit", "funding_source", "approved_amount", "currency"],
	)
	for row in rows:
		line_code = frappe.db.get_value("Procurement Budget Line", row.budget_line, "generated_reference")
		frappe.get_doc(
			{
				"doctype": "Procurement Budget Line Version",
				"generated_reference": allocate_budget_line_version_reference(line_code, target_version.version_number),
				"budget_version": target_version.name,
				"budget_line": row.budget_line,
				"title": row.title,
				"owner_org_unit": row.owner_org_unit,
				"funding_source": row.funding_source,
				"approved_amount": row.approved_amount,
				"currency": row.currency,
			}
		).insert(ignore_permissions=True)


def create_budget_successor_version(budget: str, payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `create_budget_successor_version` — copy the current Active
	Version and line identities into one Draft successor. At most one open
	successor may exist (§6.2)."""
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	payload = payload or {}

	doc = _resolve_budget(budget)
	active = _active_version(doc.name)
	if not active:
		frappe.throw(_("No Active Budget Version to revise"), frappe.ValidationError, title="BUDGET_INVALID_STATE")
	require_budget_version_capability(frappe.session.user, CAP_EDIT, active)

	existing_draft = _draft_version(doc.name)
	if existing_draft:
		# §12.3 — a second open successor is rejected and the existing route returned.
		pending = _pending_version_summary(doc.name, frappe.session.user)
		return {
			"ok": False,
			"code": "BUDGET_INVALID_STATE",
			"errors": {"successor": _("An update is already in progress for this budget. Open it to continue.")},
			"existing": True,
			"version": _version_summary(existing_draft),
			"pending_version": pending,
			"route": _pending_route(doc, pending),
		}

	# approval_reference/date/authorised_total are DB-mandatory on Budget Version
	# from the first insert (approval_document is not — it is only required
	# before submission for review, see budget_readiness_contracts._evaluate_readiness).
	# A successor has no pre-creation form (BUD-DES-14/15 only exist
	# post-creation) — seed these from the prior Active version, matching how
	# _copy_line_versions seeds the line data; the Officer edits them in the
	# tabbed editor before Save/Submit.
	seeded = {
		"approval_reference": payload.get("approval_reference") or active.approval_reference,
		"approval_date": payload.get("approval_date") or str(active.approval_date),
		"authorised_total": payload.get("authorised_total") or active.authorised_total,
		"approval_document": payload.get("approval_document") or active.approval_document,
		"revision_type": payload.get("revision_type"),
	}
	version = _create_draft_version(doc, seeded, based_on=active)
	return {"ok": True, "version": _version_summary(version)}
