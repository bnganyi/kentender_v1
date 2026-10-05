"""ANL-CHG-001 v0.8 §7.1 — the provider contract for Procurement Analytics.

Core cannot import an owner module, so each owner registers a provider on the
`kt_analytics_providers` hook (a dotted path to a module). The module exposes:

* ``applies(*, user, at) -> set[str]`` — the fact kinds this actor may read
  from this owner, decided by the owner's own verdict and the OD-2 aggregate
  audience (site-wide readers get counts, values and instants, never
  documents). A cheap role check: no table scan. An owner that does not apply
  to the actor returns an empty set.
* ``facts(*, user, kind, at, **params) -> dict`` — one kind, as
  ``{"records": [...], ...}`` built by `record`/`line` below. It raises when
  the read fails: a failed provider is never a zero (ANL §8, plan D4). Records
  are limited to what the actor may know; a masked record contributes nothing.

Core then filters by Financial year and department, computes every band, month
bucket, median, percentage, label and page (ANL §7.1: "Core computes medians,
bands, month buckets and the coverage percentage from returned facts"), and
owner providers never format text for the figures. A provider creates, marks
and persists nothing (ANL §16).

Conventions (every provider):

* Instants are naive site-timezone ``datetime`` (``kentender_core.utils.instants``).
* Amounts are ``Decimal`` KES. Parse owner Data-string amounts with
  ``money()``; never ``float``.
* ``org_units`` are Organisation Unit ids, lead first, contributors after.
* ``fiscal_year`` is the native ERPNext ``Fiscal Year`` name, ``""`` when the
  owner records none.
* ``route`` is the owner's exact destination (``frappe.set_route`` segments);
  the owner builds it from its own routing, core never guesses a route.
* ``outstanding`` is ``None`` or ``outstanding(text, holder, since)``: the
  owner's required action in the owner's words *without* the instant, the
  holder as a person or role phrase ("Brian Wafula"; "" when none is named),
  and the raw ``since`` instant (ANL-M-02, `next_step.since`).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

HOOK = "kt_analytics_providers"

# Fact kinds, one per Analytics area, plus the funding position.
NEEDS = "needs"
DEPARTMENTAL_PLANS = "departmental_plans"
PLAN_ITEMS = "plan_items"
REQUISITIONS = "requisitions"
TENDERS = "tenders"
FUNDING = "funding"
KINDS = (NEEDS, DEPARTMENTAL_PLANS, PLAN_ITEMS, REQUISITIONS, TENDERS, FUNDING)

# Tender presentation buckets (ANL §5.2). Keys are stable; labels live in core.
PREPARATION, OPEN, OPENING, EVALUATION, AWARD, CONTRACT, CLOSED, UNAVAILABLE = (
	"preparation", "open", "opening", "evaluation", "award", "contract", "closed", "unavailable",
)
BUCKETS = (PREPARATION, OPEN, OPENING, EVALUATION, AWARD, CONTRACT, CLOSED, UNAVAILABLE)

# Requisition value kinds (ANL-M-08): requested for Awaiting Department Approval
# and Submitted to Procurement, authorised for Authorised, None otherwise.
REQUESTED, AUTHORISED = "requested", "authorised"

# Decision outcomes that count as an AO decision (ANL §4A.2).
OUTCOME_AWARD, OUTCOME_NO_AWARD = "Award", "No award"


def money(value: Any) -> Decimal:
	"""An owner amount (Decimal, int, or a Data string such as ``"7185000"`` or
	``"7,185,000.50"``) as an exact ``Decimal``. Raises ``ValueError`` on
	anything else, so a bad owner value fails the read instead of becoming 0."""
	if isinstance(value, Decimal):
		return value
	if isinstance(value, bool) or value is None:
		raise ValueError(f"not an amount: {value!r}")
	try:
		return Decimal(str(value).replace(",", "").strip())
	except InvalidOperation as error:
		raise ValueError(f"not an amount: {value!r}") from error


def line(org_unit: str, amount: Any) -> dict[str, Any]:
	"""One value line attributed to one department."""
	return {"org_unit": org_unit or "", "amount": money(amount)}


def outstanding(text: str, holder: str, since: datetime) -> dict[str, Any]:
	return {"text": text, "holder": holder or "", "since": since}


def record(kind: str, *, id: str, title: str, reference: str = "", fiscal_year: str = "", org_units: list[str] | None = None,
	route: list[str] | None = None, outstanding: dict[str, Any] | None = None, **fields: Any) -> dict[str, Any]:
	"""A record of ``kind`` with its kind-specific ``fields`` (below)."""
	out = {
		"kind": kind, "id": id, "title": title, "reference": reference, "fiscal_year": fiscal_year or "",
		"org_units": list(org_units or []), "route": list(route or []), "outstanding": outstanding, **fields,
	}
	validate(out)
	return out


# Kind-specific required fields, with the type each must have. ``None`` means
# the field is present and may be None.
#
#   needs               state (owner's disposition label), state_key, accepted_at (first acceptance, instant|None),
#                       pending_successor (bool)
#   departmental_plans  state ("Accepted"), accepted_at (instant|None)
#   plan_items          planned_value (Decimal, sum of allocations), allocations
#                       ([{org_unit, planned, covered}] Decimal), invitation_days (int|None: Planning's Baseline
#                       lateness for the invitation milestone; None = no date recorded), has_proceeding (bool),
#                       plan_title, plan_version (int)
#   requisitions        state, value_kind (REQUESTED|AUTHORISED|None), value_lines ([line]), submitted_at (the Version
#                       that was authorised, or the current submitted Version; instant|None), authorised_at,
#                       consumed_at, submission_events ([instant]: every Version entering Submitted to Procurement),
#                       authorisation_events ([instant]), tender_reference (str, "" = no Tender created)
#   tenders             bucket (BUCKETS), position (owner wording, "Evaluation — automatic checks complete; ..."),
#                       authorised_lines ([line]: authorised value of the Requisition Version the Tender consumed),
#                       started_at (that handoff's consumption instant), published_at, cancelled_at,
#                       opening_complete_at (nonempty openings only), report_sent_at (first Report sent),
#                       award_received_at, decision_at (first committed decision of cycle 1), decision_outcome
#                       (OUTCOME_AWARD|OUTCOME_NO_AWARD|None), decision_events ([instant]: every committed Award or
#                       No award decision version), award_amount (Decimal|None), award_amount_visible (bool: False
#                       when the owner's summary for this actor carries no amount), cancellation_events ([instant])
#   funding             (see `funding`)
_REQUIRED: dict[str, dict[str, Any]] = {
	NEEDS: {"state": str, "state_key": str, "accepted_at": (datetime, type(None)), "pending_successor": bool},
	DEPARTMENTAL_PLANS: {"state": str, "accepted_at": (datetime, type(None))},
	PLAN_ITEMS: {"planned_value": Decimal, "allocations": list, "invitation_days": (int, type(None)),
		"has_proceeding": bool, "plan_title": str, "plan_version": int},
	REQUISITIONS: {"state": str, "value_kind": (str, type(None)), "value_lines": list, "submitted_at": (datetime, type(None)),
		"authorised_at": (datetime, type(None)), "consumed_at": (datetime, type(None)), "submission_events": list,
		"authorisation_events": list, "tender_reference": str},
	TENDERS: {"bucket": str, "position": str, "authorised_lines": list, "started_at": (datetime, type(None)),
		"published_at": (datetime, type(None)), "cancelled_at": (datetime, type(None)),
		"opening_complete_at": (datetime, type(None)), "report_sent_at": (datetime, type(None)),
		"award_received_at": (datetime, type(None)), "decision_at": (datetime, type(None)),
		"decision_outcome": (str, type(None)), "decision_events": list, "award_amount": (Decimal, type(None)),
		"award_amount_visible": bool, "cancellation_events": list},
}


def validate(rec: dict[str, Any]) -> None:
	"""Raises ``ValueError`` naming the first thing wrong. Core calls this on
	every record, and an owner calls it through `record()`."""
	kind = rec.get("kind")
	if kind not in _REQUIRED:
		raise ValueError(f"unknown record kind {kind!r}")
	for key in ("id", "title"):
		if not isinstance(rec.get(key), str) or not rec[key]:
			raise ValueError(f"{kind}: {key} must be a non-empty string")
	if not isinstance(rec.get("org_units"), list) or not all(isinstance(x, str) for x in rec["org_units"]):
		raise ValueError(f"{kind} {rec['id']}: org_units must be a list of ids")
	for key, wanted in _REQUIRED[kind].items():
		if key not in rec:
			raise ValueError(f"{kind} {rec['id']}: missing {key}")
		if not isinstance(rec[key], wanted):
			raise ValueError(f"{kind} {rec['id']}: {key} has type {type(rec[key]).__name__}")
	if kind == TENDERS and rec["bucket"] not in BUCKETS:
		raise ValueError(f"tenders {rec['id']}: bucket {rec['bucket']!r} is not one of {BUCKETS}")
	if kind == REQUISITIONS and rec["value_kind"] not in (None, REQUESTED, AUTHORISED):
		raise ValueError(f"requisitions {rec['id']}: value_kind {rec['value_kind']!r}")
	for key in ("value_lines", "authorised_lines"):
		for item in rec.get(key, []):
			if not isinstance(item.get("amount"), Decimal):
				raise ValueError(f"{kind} {rec['id']}: {key} amount must be Decimal")
	if kind == PLAN_ITEMS:
		for item in rec["allocations"]:
			if not (isinstance(item.get("planned"), Decimal) and isinstance(item.get("covered"), Decimal)):
				raise ValueError(f"plan_items {rec['id']}: allocation planned/covered must be Decimal")
	out = rec.get("outstanding")
	if out is not None and not (isinstance(out.get("since"), datetime) and isinstance(out.get("text"), str) and out["text"]):
		raise ValueError(f"{kind} {rec['id']}: outstanding needs text and a since instant")


def facts_result(records: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
	"""A provider's answer for one kind. Every record is validated."""
	for rec in records:
		validate(rec)
	return {"records": records, **extra}


def funding(*, fiscal_year: str, budget_title: str, version: int, as_at: datetime | None, lines: list[dict[str, Any]],
	reservations: list[dict[str, Any]], view: str) -> dict[str, Any]:
	"""The funding position for one Fiscal Year (ANL-M-11, §5.5 rule 5).

	``view`` is ``"whole"`` (the whole-Budget audience: Budget Officer, Budget Approver, Finance Confirmation Officer,
	Head of Procurement Function, Accounting Officer, Auditor, technical readers) or ``"department"`` (Head of User
	Department, limited to departments in their permitted scope). ``lines`` holds the Budget Lines the actor may read:
	``{"label", "owner_org_unit" ("" = available to all departments), "registered", "reserved", "committed",
	"available"}`` as Decimal. ``reservations`` holds ``{"source_org_unit", "line_owner_org_unit", "reserved",
	"committed"}`` as Decimal, one per reservation of that Fiscal Year the actor may read. Core derives the department
	view from these facts and never divides a shared line.
	"""
	if view not in ("whole", "department"):
		raise ValueError(f"funding view {view!r}")
	for item in lines:
		for key in ("registered", "reserved", "committed", "available"):
			if not isinstance(item.get(key), Decimal):
				raise ValueError(f"funding line {item.get('label')!r}: {key} must be Decimal")
	for item in reservations:
		for key in ("reserved", "committed"):
			if not isinstance(item.get(key), Decimal):
				raise ValueError(f"funding reservation: {key} must be Decimal")
	return {"fiscal_year": fiscal_year, "budget_title": budget_title, "version": version, "as_at": as_at,
		"lines": lines, "reservations": reservations, "view": view}
