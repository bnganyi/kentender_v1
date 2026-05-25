# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Planning v2 — shared state constants and transition helpers."""

from __future__ import annotations

# --- Procurement Plan (PP2) ---
PLAN_DRAFT = "Draft"
PLAN_ACTIVE = "Active"
PLAN_CLOSED = "Closed"
PLAN_CANCELLED = "Cancelled"
PLAN_SUPERSEDED = "Superseded"

PLAN_VALID_STATUSES = frozenset(
	(PLAN_DRAFT, PLAN_ACTIVE, PLAN_CLOSED, PLAN_CANCELLED, PLAN_SUPERSEDED)
)
PLAN_READONLY_STATUSES = frozenset((PLAN_CLOSED, PLAN_CANCELLED, PLAN_SUPERSEDED))
PLAN_EDITABLE_STATUSES = frozenset((PLAN_DRAFT, PLAN_ACTIVE))

PLAN_ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
	PLAN_DRAFT: (PLAN_ACTIVE, PLAN_CANCELLED),
	PLAN_ACTIVE: (PLAN_CLOSED, PLAN_CANCELLED, PLAN_SUPERSEDED),
	PLAN_CLOSED: (),
	PLAN_CANCELLED: (),
	PLAN_SUPERSEDED: (),
}

PLAN_TRANSITIONS_REQUIRING_REASON = frozenset(
	(
		(PLAN_DRAFT, PLAN_CANCELLED),
		(PLAN_ACTIVE, PLAN_CANCELLED),
	)
)

# --- Procurement Package (PP2) ---
PKG_DRAFT = "Draft"
PKG_IN_REVIEW = "In Review"
PKG_RETURNED = "Returned for Correction"
PKG_APPROVED = "Approved"
PKG_READY_FOR_RELEASE = "Ready for Release"
PKG_RELEASED = "Released to Tender"
PKG_CONSUMED = "Consumed by Tender Management"
PKG_SUPERSEDED = "Superseded"
PKG_CANCELLED = "Cancelled"

PKG_VALID_STATUSES = frozenset(
	(
		PKG_DRAFT,
		PKG_IN_REVIEW,
		PKG_RETURNED,
		PKG_APPROVED,
		PKG_READY_FOR_RELEASE,
		PKG_RELEASED,
		PKG_CONSUMED,
		PKG_SUPERSEDED,
		PKG_CANCELLED,
	)
)

PKG_EDITABLE_STATUSES = frozenset((PKG_DRAFT, PKG_RETURNED))
PKG_LINE_EDITABLE_STATUSES = PKG_EDITABLE_STATUSES
PKG_READONLY_STATUSES = frozenset(
	(
		PKG_IN_REVIEW,
		PKG_APPROVED,
		PKG_READY_FOR_RELEASE,
		PKG_RELEASED,
		PKG_CONSUMED,
		PKG_SUPERSEDED,
		PKG_CANCELLED,
	)
)
PKG_LOCKED_STATUSES = frozenset((PKG_RELEASED, PKG_CONSUMED, PKG_SUPERSEDED))
PKG_TERMINAL_STATUSES = frozenset((PKG_SUPERSEDED, PKG_CANCELLED))
PKG_LIMITED_EDIT_STATUSES = frozenset((PKG_APPROVED,))

# Governance §4.3 — workbench grouping buckets
WB_IN_PREPARATION = "in_preparation"
WB_NEEDS_REVIEW = "needs_review"
WB_NEEDS_MY_ACTION = "needs_my_action"
WB_APPROVED = "approved"
WB_READY_FOR_HANDOFF = "ready_for_handoff"
WB_HANDED_OFF = "handed_off"
WB_CONSUMED = "consumed"
WB_HISTORICAL = "historical"

PKG_WORKBENCH_GROUP: dict[str, str] = {
	PKG_DRAFT: WB_IN_PREPARATION,
	PKG_IN_REVIEW: WB_NEEDS_REVIEW,
	PKG_RETURNED: WB_NEEDS_MY_ACTION,
	PKG_APPROVED: WB_APPROVED,
	PKG_READY_FOR_RELEASE: WB_READY_FOR_HANDOFF,
	PKG_RELEASED: WB_HANDED_OFF,
	PKG_CONSUMED: WB_CONSUMED,
	PKG_SUPERSEDED: WB_HISTORICAL,
	PKG_CANCELLED: WB_HISTORICAL,
}

# Authoritative ordered list (governance §4.1)
PKG_STATUS_ORDER: tuple[str, ...] = (
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PKG_RETURNED,
	PKG_APPROVED,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	PKG_CONSUMED,
	PKG_SUPERSEDED,
	PKG_CANCELLED,
)

PKG_ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
	PKG_DRAFT: (PKG_IN_REVIEW, PKG_CANCELLED),
	PKG_IN_REVIEW: (PKG_APPROVED, PKG_RETURNED, PKG_CANCELLED),
	PKG_RETURNED: (PKG_DRAFT, PKG_IN_REVIEW, PKG_CANCELLED),
	PKG_APPROVED: (PKG_READY_FOR_RELEASE, PKG_CANCELLED),
	PKG_READY_FOR_RELEASE: (PKG_RELEASED, PKG_APPROVED, PKG_CANCELLED),
	PKG_RELEASED: (PKG_CONSUMED, PKG_SUPERSEDED, PKG_RETURNED),
	PKG_CONSUMED: (PKG_SUPERSEDED, PKG_RETURNED),
	PKG_SUPERSEDED: (),
	PKG_CANCELLED: (),
}

PKG_TRANSITIONS_REQUIRING_REASON = frozenset(
	(
		(PKG_IN_REVIEW, PKG_RETURNED),
		(PKG_IN_REVIEW, PKG_CANCELLED),
		(PKG_READY_FOR_RELEASE, PKG_APPROVED),
		(PKG_RELEASED, PKG_RETURNED),
		(PKG_CONSUMED, PKG_RETURNED),
		(PKG_RELEASED, PKG_SUPERSEDED),
		(PKG_CONSUMED, PKG_SUPERSEDED),
	)
)

# Correction / supersession (P2-013)
CORRECTION_TYPE_POST_RELEASE = "Post-Release Correction"
CORRECTION_TYPE_SUPERSESSION = "Supersession"
CORRECTION_VALID_TYPES = frozenset((CORRECTION_TYPE_POST_RELEASE, CORRECTION_TYPE_SUPERSESSION))
CORRECTION_DECISION_APPLIED = "Applied"
CORRECTION_REPLACEMENT_VALID_STATUSES = frozenset(
	(PKG_DRAFT, PKG_RETURNED, PKG_IN_REVIEW, PKG_APPROVED)
)

READINESS_NOT_RUN = "Not Run"
READINESS_PASSED = "Passed"
READINESS_FAILED = "Failed"
READINESS_PASSED_WARNINGS = "Passed With Warnings"
READINESS_STALE = "Stale"

READINESS_VALID_STATUSES = frozenset(
	(
		READINESS_NOT_RUN,
		READINESS_PASSED,
		READINESS_FAILED,
		READINESS_PASSED_WARNINGS,
		READINESS_STALE,
	)
)

# Method decision
METHOD_BASIS_OPTIONS = frozenset(
	("Template", "Threshold", "Manual Confirmation", "Rule Profile")
)

VALID_PROCUREMENT_CATEGORIES = frozenset(("Works", "Goods", "Services", "Consultancy"))


def is_valid_pkg_status(status: str | None) -> bool:
	return bool(status and status.strip() in PKG_VALID_STATUSES)


def is_allowed_pkg_transition(old_status: str | None, new_status: str | None) -> bool:
	old = (old_status or "").strip()
	new = (new_status or "").strip()
	if not old or not new:
		return False
	allowed = PKG_ALLOWED_TRANSITIONS.get(old)
	return bool(allowed and new in allowed)


def pkg_transition_requires_reason(old_status: str | None, new_status: str | None) -> bool:
	return ((old_status or "").strip(), (new_status or "").strip()) in PKG_TRANSITIONS_REQUIRING_REASON


def pkg_workbench_group(status: str | None) -> str:
	st = (status or "").strip()
	if st not in PKG_WORKBENCH_GROUP:
		raise ValueError(f"Unknown procurement package status: {status!r}")
	return PKG_WORKBENCH_GROUP[st]


def pkg_is_terminal(status: str | None) -> bool:
	return (status or "").strip() in PKG_TERMINAL_STATUSES


def pkg_allows_ordinary_edit(status: str | None) -> bool:
	return (status or "").strip() in PKG_EDITABLE_STATUSES


# --- Post-release baseline lock (P2-012 / governance §11) ---
PKG_POST_RELEASE_LOCKED_FIELDS = frozenset(
	(
		"package_code",
		"package_name",
		"plan_id",
		"planning_inclusion_code",
		"demand_id",
		"budget_line_id",
		"template_id",
		"procurement_method",
		"contract_type",
		"method_override_flag",
		"method_override_reason",
		"procurement_category",
		"required_std_category",
		"required_std_type",
		"estimated_value",
		"currency",
		"schedule_start",
		"schedule_end",
	)
)

POST_RELEASE_LOCK_MESSAGE = (
	"This package has been released and cannot be edited directly. "
	"Create a governed correction or supersession request."
)

POST_RELEASE_WORKFLOW_EXEMPT_FIELDS = frozenset(
	(
		"status",
		"workflow_reason",
		"tender_code",
		"consumed_at",
		"release_code",
		"released_to_tender_at",
		"locked_after_release",
		"readiness_status",
		"latest_readiness_code",
		"latest_review_code",
		"approved_by",
		"approved_at",
		"rejected_by",
		"rejected_at",
		"journey_code",
	)
)

