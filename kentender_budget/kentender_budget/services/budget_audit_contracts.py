# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §4.7/§14 — the append-only Funding Ledger (Budget Audit
Event doctype), plus the Funding Activity and History tab read models built
directly from it. There is exactly one ledger; Funding Activity and History
are two filtered projections of the same event stream, not two data sources.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, format_datetime, get_datetime, now_datetime

from kentender_budget.services.budget_permissions import (
	ROLE_AUDITOR,
	ROLE_APPROVER,
	ROLE_OFFICER,
	ROLE_VIEWER,
	require_any_role,
)

_READ_ROLES = (ROLE_OFFICER, ROLE_APPROVER, ROLE_VIEWER, ROLE_AUDITOR)

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
_DISPLAY_LABEL = {
	EVENT_DRAFT_APPROVAL_SAVED: _("Draft saved"),
	EVENT_DRAFT_LINES_SAVED: _("Draft saved"),
}

_POSITION_KEYS = ("approved", "reserved", "committed", "available")


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
		"event_at_display": format_datetime(ea) if ea else "—",
		"budget_line": r.get("budget_line") or "",
		"downstream_reference": r.get("downstream_reference") or "",
		"amount": flt(r.get("amount")) if r.get("amount") is not None else None,
		"currency": r.get("currency") or "",
		"actor": r.get("actor") or "",
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
	require_any_role(*_READ_ROLES)
	filters: dict[str, Any] = {"budget": budget, "event_type": ["in", list(FUNDING_EVENT_TYPES)]}
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
	out_rows = [_row_dto(r) for r in rows]
	return {
		"rows": out_rows,
		"row_count": len(out_rows),
		"summary_label": (
			_("Showing {0} funding event").format(len(out_rows))
			if len(out_rows) == 1
			else _("Showing {0} funding events").format(len(out_rows))
		),
	}


def get_budget_version_history(budget_version: str) -> dict[str, Any]:
	"""§9.3/§12.5 History tab — Budget Version lifecycle events only, for the
	exact submitted/active version, reverse chronological."""
	require_any_role(*_READ_ROLES)
	rows = frappe.get_all(
		"Budget Audit Event",
		filters={"budget_version": budget_version, "event_type": ["in", list(LIFECYCLE_EVENT_TYPES)]},
		fields=_ACTIVITY_FIELDS,
		order_by="event_at desc",
	)
	return {"rows": [_row_dto(r) for r in rows], "row_count": len(rows)}
