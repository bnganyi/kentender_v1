"""Stable Departmental Needs states, actions and field bounds (NDS-CHG-001 v1.6)."""

# --- Root states (§4.2) ---------------------------------------------------
STATE_DRAFT = "Draft"
STATE_SUBMITTED = "Submitted"
STATE_RETURNED = "Returned"
STATE_ACCEPTED = "Accepted for planning"
STATE_NOT_TAKEN_FORWARD = "Not taken forward"
STATE_WITHDRAWN = "Withdrawn"

NEED_STATES = frozenset(
	{
		STATE_DRAFT,
		STATE_SUBMITTED,
		STATE_RETURNED,
		STATE_ACCEPTED,
		STATE_NOT_TAKEN_FORWARD,
		STATE_WITHDRAWN,
	}
)

# OU and FY are fixed at creation (§4.2). The site Procuring Entity is
# implicit (AUTH-ADR-001 v1.6 §1.1) and carries no field here.
IMMUTABLE_NEED_SCOPE_FIELDS = ("organisation_unit", "financial_year")

# --- Version statuses (§4.3) ----------------------------------------------
VERSION_DRAFT = "Draft"
VERSION_SUBMITTED = "Submitted"
VERSION_RETURNED = "Returned"
VERSION_ACCEPTED = "Accepted"
VERSION_NOT_TAKEN_FORWARD = "Not taken forward"
VERSION_WITHDRAWN = "Withdrawn"
VERSION_SUPERSEDED = "Superseded"

VERSION_STATUSES = frozenset(
	{
		VERSION_DRAFT,
		VERSION_SUBMITTED,
		VERSION_RETURNED,
		VERSION_ACCEPTED,
		VERSION_NOT_TAKEN_FORWARD,
		VERSION_WITHDRAWN,
		VERSION_SUPERSEDED,
	}
)

# Only a Draft may still have its requirement content edited (§4.3, §13).
MUTABLE_VERSION_STATUSES = frozenset({VERSION_DRAFT})

# A successor is "open" — and therefore blocks a second one (§5.2,
# NDS_OPEN_SUCCESSOR_EXISTS) — until it is accepted, declined or withdrawn.
OPEN_SUCCESSOR_STATUSES = frozenset({VERSION_DRAFT, VERSION_SUBMITTED, VERSION_RETURNED})

# The six requester-entered values (§2.2, §4.3).
VERSION_CONTENT_FIELDS = (
	"title",
	"description",
	"expected_operational_result",
	"indicative_quantity",
	"unit",
	"required_by_date",
)

# --- Field bounds (§4.3, §4.6, NDS-BR-011) --------------------------------
TITLE_MIN, TITLE_MAX = 5, 160
DESCRIPTION_MIN, DESCRIPTION_MAX = 10, 1000
REASON_MIN, REASON_MAX = 20, 1000
QUANTITY_DECIMALS = 3

# --- Withdrawal request statuses (§4.6, §5.3) -----------------------------
WITHDRAWAL_AWAITING_REVIEW = "Awaiting review"
WITHDRAWAL_AWAITING_CLEARANCE = "Awaiting planning clearance"
WITHDRAWAL_APPROVED = "Approved"
WITHDRAWAL_DECLINED = "Declined"

OPEN_WITHDRAWAL_STATUSES = frozenset({WITHDRAWAL_AWAITING_REVIEW, WITHDRAWAL_AWAITING_CLEARANCE})

# --- Needs-submission state (§4.1, NDS-AC-003, NDS-AC-055) ----------------
# Derived read-only from `Fiscal Year.kentender_needs_submission_open` (a
# plain Boolean) via `kentender_core.services.site_configuration` — never a
# module-owned window record. There is no `Scheduled` state under v1.6: the
# flag is a binary Open/Closed at the instant it is read, and reaching
# `kentender_needs_submission_closes_at` closes it with the same effect as a
# manual close (the hourly `close_due_needs_submissions` job, or an
# in-transaction recheck at command time, whichever runs first).
INTAKE_OPEN = "Open"
INTAKE_CLOSED = "Closed"

# --- Decisions (§4.5) -----------------------------------------------------
ACTION_CREATE = "Create"
ACTION_SAVE_DRAFT = "Save draft"
ACTION_SUBMIT = "Submit"
ACTION_RESUBMIT = "Resubmit"
ACTION_RETURN = "Return for correction"
ACTION_ACCEPT = "Accept for planning"
ACTION_DECLINE = "Do not take forward"
ACTION_WITHDRAW = "Withdraw"

ACTION_CREATE_SUCCESSOR = "Create successor"
ACTION_SAVE_SUCCESSOR = "Save successor"
ACTION_CANCEL_SUCCESSOR = "Cancel successor"
ACTION_SUBMIT_SUCCESSOR = "Submit successor"
ACTION_RETURN_SUCCESSOR = "Return successor"
ACTION_ACCEPT_SUCCESSOR = "Accept successor"
ACTION_DECLINE_SUCCESSOR = "Decline successor"

ACTION_REQUEST_WITHDRAWAL = "Request withdrawal"
ACTION_EVALUATE_WITHDRAWAL = "Evaluate withdrawal"
ACTION_REEVALUATE_WITHDRAWAL = "Re-evaluate withdrawal"
ACTION_APPROVE_WITHDRAWAL = "Approve withdrawal"
ACTION_DECLINE_WITHDRAWAL = "Decline withdrawal"

# Reasons exist only for these actions; Accept collects none (NDS-BR-011, §4.5).
REASON_REQUIRED_ACTIONS = frozenset(
	{
		ACTION_RETURN,
		ACTION_DECLINE,
		ACTION_RETURN_SUCCESSOR,
		ACTION_DECLINE_SUCCESSOR,
		ACTION_REQUEST_WITHDRAWAL,
		ACTION_DECLINE_WITHDRAWAL,
	}
)

# --- Review tasks (§4.4) --------------------------------------------------
TASK_INITIAL_ACCEPTANCE = "Initial acceptance"
TASK_SUCCESSOR_ACCEPTANCE = "Successor acceptance"
TASK_WITHDRAWAL = "Withdrawal"

TASK_OPEN = "Open"
TASK_COMPLETED = "Completed"
TASK_CANCELLED = "Cancelled"

# --- Planning usage projection (§4.7) -------------------------------------
# `Partially included` is removed by §1.1 and forbidden by §17.
USAGE_NOT_INCLUDED = "Not included"
USAGE_FULL = "Fully included"
# PLN-CHG-001 v1.12 §4.4 / PLN-AC-092 — the department recorded, in its
# departmental procurement plan, that it is not proceeding with this accepted
# Need this financial year; Planning publishes the outcome back here.
USAGE_NOT_PROCEEDING = "Not proceeding"

USAGE_VALUES = frozenset({USAGE_NOT_INCLUDED, USAGE_FULL, USAGE_NOT_PROCEEDING})

# --- Business responsibilities (§6) ----------------------------------------
# These are also the projected Frappe Role names (AUTH-ADR-001 v1.6 §5.7) and
# the exact `business_role` strings registered in
# `kentender_core.services.business_role_registry`.
ROLE_DEPARTMENTAL_AUTHOR = "Departmental Author"
ROLE_HEAD_OF_USER_DEPARTMENT = "Head of User Department"
ROLE_PROCUREMENT_PLANNER = "Procurement Planner"
ROLE_AUDITOR = "Auditor"

# No capability identifiers are defined here. §6 requires the shared
# AUTH-ADR-001 v1.6 resolver (`kentender_core.services.authorization`) and its
# `User Responsibility Assignment` — see `services/permissions.py`. Do not
# reintroduce Frappe User Permission, a Capability Profile, an Operational
# Scope Assignment or any other parallel permission store as authority.
