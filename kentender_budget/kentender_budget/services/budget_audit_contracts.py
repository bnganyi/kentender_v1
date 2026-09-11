# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 §4.7/§14 — the append-only Funding Ledger (Budget Audit
Event doctype), plus the Funding Activity and History tab read models built
directly from it. There is exactly one ledger; Funding Activity and History
are two filtered projections of the same event stream, not two data sources.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, get_datetime, now_datetime

from kentender_budget.services.budget_authorization import require_budget_read_scope, require_budget_version_read_scope
from kentender_budget.services.budget_contracts import _display_datetime, _user_label

# Must match Budget Audit Event.event_type exactly (kentender_budget/doctype/
# budget_audit_event/budget_audit_event.json).
EVENT_VERSION_CREATED = "Budget version created"
EVENT_DRAFT_APPROVAL_SAVED = "Draft approval details saved"
EVENT_DRAFT_LINES_SAVED = "Draft lines saved"
EVENT_SUBMITTED = "Budget version submitted"
EVENT_RETURNED = "Budget version returned"
EVENT_APPROVED = "Budget version approved and activated"
EVENT_SUPERSEDED = "Budget version superseded"
EVENT_CLOSED = "Budget closed"
EVENT_CHECK_PERFORMED = "Check funding performed"
EVENT_RESERVED = "Funding reserved"
EVENT_REVALIDATED = "Reservation revalidated"
EVENT_RELEASED = "Reservation released"
EVENT_PARTIAL = "Reservation partially converted"
EVENT_COMMITMENT = "Contract commitment recorded"
EVENT_COMMITMENT_ADJUSTED = "Commitment adjusted"
EVENT_PERMISSION_DENIED = "Permission denied"
EVENT_CONCURRENCY_CONFLICT = "Concurrency conflict"

# §12.3 "History contains Budget Version lifecycle events only; it does not
# duplicate the funding ledger." — the two tabs are disjoint partitions.
LIFECYCLE_EVENT_TYPES = frozenset(
	{
		EVENT_VERSION_CREATED,
		EVENT_DRAFT_APPROVAL_SAVED,
		EVENT_DRAFT_LINES_SAVED,
		EVENT_SUBMITTED,
		EVENT_RETURNED,
		EVENT_APPROVED,
		EVENT_SUPERSEDED,
		EVENT_CLOSED,
	}
)

FUNDING_EVENT_TYPES = frozenset(
	{
		EVENT_RESERVED,
		EVENT_REVALIDATED,
		EVENT_RELEASED,
		EVENT_PARTIAL,
		EVENT_COMMITMENT,
		EVENT_COMMITMENT_ADJUSTED,
	}
)

# BUD-DES-11/13 History artboards show one "Draft saved" line regardless of
# which draft-save event actually fired; DRAFT_APPROVAL_SAVED / DRAFT_LINES_SAVED
# stay distinct in the ledger (precise audit) but collapse to one label here.
# EVENT_SUBMITTED / EVENT_RESERVED are remapped to the exact wording BUD-DES-07
# and BUD-DES-07A show ("Submitted for review" / "Reservation confirmed") —
# the stored event_type stays the precise audit value, only display changes.
_DISPLAY_LABEL = {
	EVENT_DRAFT_APPROVAL_SAVED: _("Draft saved"),
	EVENT_DRAFT_LINES_SAVED: _("Draft saved"),
	EVENT_SUBMITTED: _("Submitted for review"),
	EVENT_RESERVED: _("Reservation confirmed"),
}

_POSITION_KEYS = ("approved", "reserved", "committed", "available")

# Deterministic order for the Funding Activity "All funding events" filter —
# FUNDING_EVENT_TYPES is a frozenset and has no stable iteration order.
_FUNDING_EVENT_ORDER = (
	EVENT_RESERVED,
	EVENT_REVALIDATED,
	EVENT_PARTIAL,
	EVENT_RELEASED,
	EVENT_COMMITMENT,
	EVENT_COMMITMENT_ADJUSTED,
)


def record_event(
	*,
	budget: str,
	event_type: str,
	actor: str | None = None,
	actor_kind: str = "user",
	correlation_id: str,
	budget_version: str | None = None,
	budget_line: str | None = None,
	reservation: str | None = None,
	commitment: str | None = None,
	downstream_reference: str = "",
	amount: float | None = None,
	currency: str | None = None,
	calling_module: str = "",
	revalidation_failure_code: str = "",
	reason: str = "",
	before: dict[str, float] | None = None,
	after: dict[str, float] | None = None,
	event_at=None,
	fixture_namespace: str = "",
) -> str:
	"""Insert one immutable Budget Audit Event (the FundingLedgerEvent object).

	Unlike the pre-v1.2 shape, `correlation_id` is required — every event
	must be traceable to the command that produced it (§4.7, §14).
	"""
	if not (correlation_id or "").strip():
		frappe.throw(_("correlation_id is required to record a funding ledger event."))

	values: dict[str, Any] = {
		"doctype": "Budget Audit Event",
		"budget": budget,
		"budget_version": budget_version or None,
		"budget_line": budget_line or None,
		"event_type": event_type,
		"event_at": event_at or now_datetime(),
		"downstream_reference": downstream_reference or "",
		"reservation": reservation or None,
		"commitment": commitment or None,
		"amount": flt(amount) if amount is not None else None,
		"currency": currency or "KES",
		"actor": (actor or frappe.session.user or "System").strip(),
		"actor_kind": actor_kind if actor_kind in ("user", "system", "integration") else "user",
		"calling_module": calling_module or "",
		"correlation_id": correlation_id.strip(),
		"revalidation_failure_code": revalidation_failure_code or "",
		"reason": reason or "",
		"fixture_namespace": fixture_namespace or "",
	}
	for key in _POSITION_KEYS:
		values[f"before_{key}"] = flt((before or {}).get(key)) if before else None
		values[f"after_{key}"] = flt((after or {}).get(key)) if after else None

	doc = frappe.get_doc(values)
	doc.insert(ignore_permissions=True)
	return doc.name


def safe_record_event(**kwargs) -> str | None:
	"""Best-effort record; never break the calling mutation on a logging failure."""
	try:
		return record_event(**kwargs)
	except Exception:
		frappe.log_error(title="Budget audit record_event failed")
		return None


def _row_dto(r) -> dict[str, Any]:
	event_at = r.get("event_at")
	ea = get_datetime(event_at) if event_at else None
	event_type = r.get("event_type") or ""
	positions = None
	if any(r.get(f"after_{k}") is not None for k in _POSITION_KEYS):
		positions = {
			"before": {k: flt(r.get(f"before_{k}")) for k in _POSITION_KEYS},
			"after": {k: flt(r.get(f"after_{k}")) for k in _POSITION_KEYS},
		}
	return {
		"id": r.get("name") or "",
		"event_type": event_type,
		"event_type_label": _DISPLAY_LABEL.get(event_type, event_type),
		"event_at": str(event_at) if event_at else "",
		"event_at_display": _display_datetime(ea) if ea else "—",
		"budget_line": r.get("budget_line") or "",
		"downstream_reference": r.get("downstream_reference") or "",
		"amount": flt(r.get("amount")) if r.get("amount") is not None else None,
		"currency": r.get("currency") or "",
		"actor": _user_label(r.get("actor")),
		"actor_kind": r.get("actor_kind") or "user",
		"calling_module": r.get("calling_module") or "",
		"correlation_id": r.get("correlation_id") or "",
		"revalidation_failure_code": r.get("revalidation_failure_code") or "",
		"reason": r.get("reason") or "",
		"positions": positions,
	}


_ACTIVITY_FIELDS = [
	"name",
	"event_type",
	"event_at",
	"budget_line",
	"downstream_reference",
	"amount",
	"currency",
	"actor",
	"actor_kind",
	"calling_module",
	"correlation_id",
	"revalidation_failure_code",
	"reason",
	"before_approved",
	"before_reserved",
	"before_committed",
	"before_available",
	"after_approved",
	"after_reserved",
	"after_committed",
	"after_available",
]


def get_funding_activity(
	budget: str,
	*,
	budget_line: str | None = None,
	event_type: str | None = None,
) -> dict[str, Any]:
	"""BUD-UI-03 Funding Activity tab — §9.3: reverse chronological, server-filtered."""
	from kentender_budget.services.budget_contracts import _active_version, _resolve_budget, _version_totals

	doc = _resolve_budget(budget)
	require_budget_read_scope("Procurement Budget", doc.name)
	filters: dict[str, Any] = {"budget": doc.name, "event_type": ["in", list(FUNDING_EVENT_TYPES)]}
	if (budget_line or "").strip():
		filters["budget_line"] = budget_line.strip()
	if (event_type or "").strip() and event_type in FUNDING_EVENT_TYPES:
		filters["event_type"] = event_type.strip()

	rows = frappe.get_all(
		"Budget Audit Event",
		filters=filters,
		fields=_ACTIVITY_FIELDS,
		order_by="event_at desc",
	)
	# Ledger rows only store the Budget Line's own (hash) docname — the
	# artboard shows its human code (e.g. "MOH-BL-DHI-2027"), not the id.
	codes = (
		{
			r.name: r.generated_reference
			for r in frappe.get_all(
				"Procurement Budget Line",
				filters={"name": ["in", list({row.budget_line for row in rows if row.budget_line})]},
				fields=["name", "generated_reference"],
			)
		}
		if rows
		else {}
	)
	out_rows = []
	for row in rows:
		dto = _row_dto(row)
		dto["budget_line_code"] = codes.get(dto["budget_line"], "")
		out_rows.append(dto)

	active_version = _active_version(doc.name)
	budget_lines = (
		[
			{"id": ln["budget_line"], "code": ln.get("code", ""), "title": ln["title"]}
			for ln in _version_totals(active_version.name)["lines"]
		]
		if active_version
		else []
	)

	return {
		"rows": out_rows,
		"row_count": len(out_rows),
		"summary_label": (
			_("Showing {0} funding event").format(len(out_rows))
			if len(out_rows) == 1
			else _("Showing {0} funding events").format(len(out_rows))
		),
		"budget_lines": budget_lines,
		"event_type_options": [{"value": et, "label": _DISPLAY_LABEL.get(et, et)} for et in _FUNDING_EVENT_ORDER],
	}


def get_budget_version_history(budget_version: str) -> dict[str, Any]:
	"""§9.3/§12.5 History tab — Budget Version lifecycle events only, for the
	exact submitted/active version, reverse chronological."""
	from kentender_budget.services.budget_contracts import _resolve_budget_version

	version = _resolve_budget_version(budget_version)
	require_budget_version_read_scope(version)
	rows = frappe.get_all(
		"Budget Audit Event",
		filters={"budget_version": version.name, "event_type": ["in", list(LIFECYCLE_EVENT_TYPES)]},
		fields=_ACTIVITY_FIELDS,
		order_by="event_at desc",
	)
	return {"rows": [_row_dto(r) for r in rows], "row_count": len(rows)}
