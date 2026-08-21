"""Stable Departmental Needs states, actions and capability identifiers."""

STATE_DRAFT = "Draft"
STATE_SUBMITTED = "Submitted"
STATE_RETURNED = "Returned"
STATE_ACCEPTED = "Accepted for planning"
STATE_NOT_TAKEN_FORWARD = "Not taken forward"
STATE_WITHDRAWN = "Withdrawn"

CAP_CREATE = "departmental_needs.create"
CAP_EDIT_OWN = "departmental_needs.edit_own"
CAP_SUBMIT = "departmental_needs.submit"
CAP_VIEW_OWN = "departmental_needs.view_own"
CAP_VIEW_DEPARTMENT = "departmental_needs.view_department"
CAP_REVIEW = "departmental_needs.review"
CAP_READ_ACCEPTED_FOR_PLANNING = "departmental_needs.read_accepted_for_planning"
CAP_OVERSIGHT_READ = "departmental_needs.oversight_read"
CAP_ALLOCATE = "procurement_planning.need_allocate"

TASK_DEPARTMENT_REVIEW = "departmental_needs.department_review"
TASK_WITHDRAWAL_REVIEW = "departmental_needs.withdrawal_review"

USAGE_NOT_INCLUDED = "Not included"
USAGE_PARTIAL = "Partially included"
USAGE_FULL = "Fully included"

UNIT_CODES = ("Each", "Set", "Lot", "Person", "Staff", "Month", "Day", "Service", "Programme", "Other")
