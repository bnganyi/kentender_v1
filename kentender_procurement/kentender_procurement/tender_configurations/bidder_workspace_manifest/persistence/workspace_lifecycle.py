# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Canonical BWMF workspace status model (Phase 2 lifecycle alignment)."""

from __future__ import annotations

from dataclasses import dataclass

# Canonical workspace status values (no Open).
WS_NOT_STARTED = "not_started"
WS_DRAFT = "draft"
WS_IN_PROGRESS = "in_progress"
WS_NEEDS_ATTENTION = "needs_attention"
WS_READY_TO_SUBMIT = "ready_to_submit"
WS_SUBMITTED = "submitted"
WS_WITHDRAWN = "withdrawn"
WS_CLOSED = "closed"

CANONICAL_WORKSPACE_STATUSES: frozenset[str] = frozenset(
	{
		WS_NOT_STARTED,
		WS_DRAFT,
		WS_IN_PROGRESS,
		WS_NEEDS_ATTENTION,
		WS_READY_TO_SUBMIT,
		WS_SUBMITTED,
		WS_WITHDRAWN,
		WS_CLOSED,
	}
)

# Derived from responses / blockers / confirmations / dependencies / readiness.
# Never set directly by bidder or a generic transition service.
PREPARATORY_WORKSPACE_STATUSES: frozenset[str] = frozenset(
	{
		WS_NOT_STARTED,
		WS_DRAFT,
		WS_IN_PROGRESS,
		WS_NEEDS_ATTENTION,
		WS_READY_TO_SUBMIT,
	}
)

TRANSACTIONAL_WORKSPACE_STATUSES: frozenset[str] = frozenset(
	{WS_SUBMITTED, WS_WITHDRAWN, WS_CLOSED}
)

# Controlled transaction transitions only.
WORKSPACE_TRANSACTION_TRANSITIONS: dict[str, frozenset[str]] = {
	WS_READY_TO_SUBMIT: frozenset({WS_SUBMITTED}),
	WS_SUBMITTED: frozenset({WS_WITHDRAWN, WS_CLOSED}),
	WS_WITHDRAWN: frozenset({WS_CLOSED}),
}

FORBIDDEN_WORKSPACE_STATUSES: frozenset[str] = frozenset({"Open", "Submitted", "Closed"})


@dataclass(frozen=True)
class WorkspaceReadinessSignals:
	"""Inputs for preparatory status derivation (boundary-tested, no persistence)."""

	response_count: int = 0
	has_incomplete_response: bool = False
	has_blockers: bool = False
	confirmations_complete: bool = False
	dependencies_ok: bool = True
	readiness_pass: bool = False


def derive_workspace_status(signals: WorkspaceReadinessSignals) -> str:
	"""Derive preparatory workspace status from readiness signals.

	Transactional statuses (submitted/withdrawn/closed) are never returned here.
	"""
	if signals.has_blockers:
		return WS_NEEDS_ATTENTION
	if signals.response_count <= 0:
		return WS_NOT_STARTED
	if (
		signals.readiness_pass
		and signals.confirmations_complete
		and signals.dependencies_ok
		and not signals.has_incomplete_response
	):
		return WS_READY_TO_SUBMIT
	if signals.response_count > 0 and not signals.has_incomplete_response:
		return WS_IN_PROGRESS
	return WS_DRAFT


def collect_workspace_readiness_signals(
	*,
	workspace: str,
	organization: str,
	bidder_party: str,
	response_doctype: str,
	confirmation_doctype: str,
) -> WorkspaceReadinessSignals:
	"""Collect persistence signals for derived status refresh."""
	import frappe

	responses = frappe.get_all(
		response_doctype,
		filters={"workspace": workspace, "organization": organization, "bidder_party": bidder_party},
		fields=["name", "values_json"],
	)
	confirmations = frappe.get_all(
		confirmation_doctype,
		filters={"workspace": workspace, "organization": organization, "bidder_party": bidder_party},
		pluck="name",
	)
	has_incomplete = False
	for row in responses:
		raw = row.get("values_json") or ""
		if not str(raw).strip() or str(raw).strip() in ("{}", "null"):
			has_incomplete = True
			break
	has_blockers = False
	confirmations_complete = bool(confirmations) if responses else False
	readiness_pass = (
		bool(responses) and not has_incomplete and confirmations_complete and not has_blockers
	)
	return WorkspaceReadinessSignals(
		response_count=len(responses),
		has_incomplete_response=has_incomplete,
		has_blockers=has_blockers,
		confirmations_complete=confirmations_complete,
		dependencies_ok=not has_blockers,
		readiness_pass=readiness_pass,
	)


def assert_canonical_workspace_status(status: str) -> None:
	import frappe
	from frappe import _

	if status in FORBIDDEN_WORKSPACE_STATUSES or status == "Open":
		frappe.throw(
			_("Workspace status {0} is forbidden; use canonical statuses.").format(status),
			title="BWMF_WORKSPACE_FORBIDDEN_STATUS",
		)
	if status not in CANONICAL_WORKSPACE_STATUSES:
		frappe.throw(
			_("Unknown workspace status {0}.").format(status),
			title="BWMF_WORKSPACE_UNKNOWN_STATUS",
		)
