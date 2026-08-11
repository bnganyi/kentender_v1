# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Planning MVP-1 status and projection vocabularies (REQ §9)."""

from __future__ import annotations

# Logical Plan lifecycle (§9.1)
PLAN_OPEN = "Open"
PLAN_CLOSED = "Closed"
PLAN_CANCELLED = "Cancelled"
PLAN_LIFECYCLE_STATES = (PLAN_OPEN, PLAN_CLOSED, PLAN_CANCELLED)

# Plan Version status (§9.2)
VERSION_DRAFT = "Draft"
VERSION_IN_REVIEW = "In review"
VERSION_RETURNED = "Returned"
VERSION_APPROVED = "Approved"
VERSION_SUPERSEDED = "Superseded"
VERSION_CANCELLED = "Cancelled"
VERSION_STATUSES = (
	VERSION_DRAFT,
	VERSION_IN_REVIEW,
	VERSION_RETURNED,
	VERSION_APPROVED,
	VERSION_SUPERSEDED,
	VERSION_CANCELLED,
)
VERSION_IMMUTABLE_STATUSES = frozenset(
	(VERSION_APPROVED, VERSION_SUPERSEDED, VERSION_CANCELLED)
)
VERSION_EDITABLE_STATUSES = frozenset((VERSION_DRAFT, VERSION_RETURNED))
# Gate 05 — final approve only after submit_for_review + professional recommend.
VERSION_APPROVABLE_STATUSES = frozenset((VERSION_IN_REVIEW,))
VERSION_SUBMITTABLE_FOR_REVIEW = frozenset((VERSION_DRAFT, VERSION_RETURNED))

# Plan Decision.decision vocabulary (Gate 05)
DECISION_SUBMITTED_FOR_REVIEW = "Submitted for review"
DECISION_RECOMMENDED = "Recommended approval"
DECISION_RETURNED = "Returned"
DECISION_APPROVED = "Approved"

# Plan Item baseline (§9.3)
ITEM_PROPOSED = "Proposed"
ITEM_ACTIVE = "Active"
ITEM_REMOVED = "Removed"
ITEM_BASELINE_STATES = (ITEM_PROPOSED, ITEM_ACTIVE, ITEM_REMOVED)

# Plan Demand Allocation
ALLOC_DRAFT = "Draft"
ALLOC_EFFECTIVE = "Effective"
ALLOC_REVERSED = "Reversed"
ALLOCATION_STATUSES = (ALLOC_DRAFT, ALLOC_EFFECTIVE, ALLOC_REVERSED)

# Projections (§9.4) — not Plan statuses
VALIDATION_NOT_RUN = "Not run"
VALIDATION_READY = "Ready"
VALIDATION_NEEDS_ATTENTION = "Needs attention"
VALIDATION_BLOCKED = "Blocked"
VALIDATION_STALE = "Stale"
VALIDATION_PROJECTIONS = (
	VALIDATION_NOT_RUN,
	VALIDATION_READY,
	VALIDATION_NEEDS_ATTENTION,
	VALIDATION_BLOCKED,
	VALIDATION_STALE,
)

DEPT_PREPARING = "Preparing"
DEPT_SUBMITTED = "Submitted"
DEPT_RETURNED = "Returned"
DEPT_CONTRIBUTION_STATUSES = (DEPT_PREPARING, DEPT_SUBMITTED, DEPT_RETURNED)

PUB_NOT_SUBMITTED = "Not submitted"
PUB_QUEUED = "Queued"
PUB_PUBLISHED = "Published"
PUB_FAILED = "Failed"
PUB_NOT_APPLICABLE = "Not applicable"
PUBLICATION_STATUSES = (
	PUB_NOT_SUBMITTED,
	PUB_QUEUED,
	PUB_PUBLISHED,
	PUB_FAILED,
	PUB_NOT_APPLICABLE,
)

TAKEUP_NOT_TAKEN = "Not taken up"
TAKEUP_IN_PREP = "Tender in preparation"
TAKEUP_ACTIVE = "Tender active"
TAKEUP_CONTRACTED = "Contracted"
TAKEUP_CLOSED = "Closed downstream"
TENDER_TAKEUP_PROJECTIONS = (
	TAKEUP_NOT_TAKEN,
	TAKEUP_IN_PREP,
	TAKEUP_ACTIVE,
	TAKEUP_CONTRACTED,
	TAKEUP_CLOSED,
)

# Roles that may mutate draft plan content (Gate 02). Final approve is narrower —
# see planning_permissions.APPROVE_PLAN_ROLES (no Administrator / System Manager bypass).
PLANNING_OPERATIONAL_ROLES = frozenset(
	(
		"Planning Contributor",
		"Head of User Department",
		"Procurement Planner",
		"Planning Reviewer",
		"Planning Authority",
		"Accounting Officer",
		"Designated Approver",
	)
)

PLAN_TYPE_ANNUAL = "Annual"

DOCTYPE_PLAN = "Procurement Plan"
DOCTYPE_VERSION = "Procurement Plan Version"
DOCTYPE_ITEM = "Procurement Plan Item"
DOCTYPE_ITEM_VERSION = "Procurement Plan Item Version"
DOCTYPE_ALLOCATION = "Plan Demand Allocation"
DOCTYPE_DEPT_SUBMISSION = "Departmental Submission"
DOCTYPE_DECISION = "Plan Decision"
DOCTYPE_VALIDATION = "Plan Validation Result"
DOCTYPE_PUBLICATION = "Publication Event"
DOCTYPE_HANDOFF = "Planning Handoff Snapshot"

MVP1_DOCTYPES = (
	DOCTYPE_PLAN,
	DOCTYPE_VERSION,
	DOCTYPE_ITEM,
	DOCTYPE_ITEM_VERSION,
	DOCTYPE_ALLOCATION,
	DOCTYPE_DEPT_SUBMISSION,
	DOCTYPE_DECISION,
	DOCTYPE_VALIDATION,
	DOCTYPE_PUBLICATION,
	DOCTYPE_HANDOFF,
)
