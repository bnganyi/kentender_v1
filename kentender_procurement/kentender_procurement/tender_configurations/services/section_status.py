# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared server-derived section status and issue-result interfaces (no section business rules)."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr

# Common Control §3.4 — canonical snake_case statuses.
STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
STATUS_NEEDS_ATTENTION = "needs_attention"
STATUS_COMPLETE = "complete"
STATUS_NOT_APPLICABLE = "not_applicable"

CANONICAL_SECTION_STATUSES = (
	STATUS_NOT_STARTED,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_COMPLETE,
	STATUS_NOT_APPLICABLE,
)

# A2 / Stitch Title Case display labels (checklist contract).
DISPLAY_STATUS_LABELS = {
	STATUS_NOT_STARTED: "Not Started",
	STATUS_IN_PROGRESS: "In Progress",
	STATUS_NEEDS_ATTENTION: "Needs Attention",
	STATUS_COMPLETE: "Complete",
	STATUS_NOT_APPLICABLE: "Not Applicable",
}

_DISPLAY_TO_CANONICAL = {v: k for k, v in DISPLAY_STATUS_LABELS.items()}
_DISPLAY_TO_CANONICAL["Locked"] = STATUS_NOT_STARTED  # workflow lock is display-only

# X100 issue severities (server-derived; client cannot author authoritative blockers).
SEVERITY_BLOCKER = "blocker"
SEVERITY_WARNING = "warning"
SEVERITY_INFORMATION = "information"
ISSUE_SEVERITIES = (SEVERITY_BLOCKER, SEVERITY_WARNING, SEVERITY_INFORMATION)


def issue_item(
	*,
	code: str,
	severity: str,
	message: str,
	correction_route: str = "",
	section_key: str = "",
	task_key: str = "",
	field_key: str = "",
	resolved: int | bool = 0,
) -> dict[str, Any]:
	"""Shared bidder-safe issue row for section validators and the Issues register."""
	sev = cstr(severity or SEVERITY_BLOCKER).strip().lower()
	if sev not in ISSUE_SEVERITIES:
		sev = SEVERITY_BLOCKER
	return {
		"code": cstr(code or "").strip() or "unspecified_issue",
		"severity": sev,
		"section_key": cstr(section_key or "").strip(),
		"task_key": cstr(task_key or "").strip(),
		"field_key": cstr(field_key or "").strip(),
		"message": cstr(message or "").strip(),
		"correction_route": cstr(correction_route or "").strip(),
		"resolved": 1 if resolved else 0,
	}


def to_display_status(canonical: str) -> str:
	"""Map canonical snake_case status to A2 Title Case label."""
	key = cstr(canonical or "").strip()
	if key in DISPLAY_STATUS_LABELS:
		return DISPLAY_STATUS_LABELS[key]
	# Already Title Case or unknown — pass through known display labels.
	if key in _DISPLAY_TO_CANONICAL or key == "Locked":
		return key
	return DISPLAY_STATUS_LABELS.get(STATUS_NOT_STARTED, "Not Started")


def to_canonical_status(label_or_key: str) -> str:
	text = cstr(label_or_key or "").strip()
	if text in CANONICAL_SECTION_STATUSES:
		return text
	return _DISPLAY_TO_CANONICAL.get(text, STATUS_NOT_STARTED)


def issue_result(
	*,
	ok: bool,
	issues: list[dict[str, Any]] | None = None,
	section_status: str,
	issue_count: int | None = None,
) -> dict[str, Any]:
	"""Shared IssueResult shape used by section validators and checklist helpers."""
	issues = list(issues or [])
	status = to_canonical_status(section_status)
	count = int(issue_count) if issue_count is not None else len(issues)
	return {
		"ok": bool(ok),
		"issues": issues,
		"section_status": status,
		"issue_count": count,
		"display_status": to_display_status(status),
	}


def derive_generic_section_status(
	*,
	required: bool = True,
	has_responses: bool = False,
	not_applicable: bool = False,
	has_validation_blockers: bool = False,
	is_partial: bool = False,
) -> dict[str, Any]:
	"""Generic status derivation without section-specific field rules.

	Returns an IssueResult-compatible dict with canonical ``section_status``.
	"""
	if not_applicable:
		status = STATUS_NOT_APPLICABLE
	elif has_validation_blockers:
		status = STATUS_NEEDS_ATTENTION
	elif not has_responses:
		status = STATUS_NOT_STARTED
	elif is_partial:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_COMPLETE

	# ``required`` reserved for future generic incomplete rules; unused in F0.
	_ = required
	issues: list[dict[str, Any]] = []
	if status == STATUS_NEEDS_ATTENTION:
		issues.append(
			{
				"code": "validation_blocker",
				"message": "Section has validation blockers.",
			}
		)
	return issue_result(
		ok=status in (STATUS_COMPLETE, STATUS_NOT_APPLICABLE, STATUS_NOT_STARTED)
		or (status == STATUS_IN_PROGRESS and not has_validation_blockers),
		issues=issues,
		section_status=status,
	)
