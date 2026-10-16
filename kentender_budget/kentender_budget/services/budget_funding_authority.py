# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who may act on a contract funding request or entry (BUD-CHG-001 v1.16 sections 4.12, 8.6, 8.8; AUTH-ADR-001 v1.16 section 4.4A).

The Budget Officer prepares and the Budget Approver decides: both live Site-wide responsibilities. The Approver must be a different actual person from the entry's preparer and from every Finance confirmer
whose confirmation supplies the submitted funding basis. The check reads **actual participation** (user identities recorded on the entry), so it cannot be avoided by holding several roles, by a changed
assignment or by a second confirmation. When attribution is unclear (nobody is shown to have confirmed the basis, or nobody to have prepared the entry) nobody can be shown to be independent, so the check fails
closed and approval is blocked until it is resolved."""

from __future__ import annotations

from typing import Any, Iterable

import frappe

from kentender_budget.services.budget_authorization import ROLE_BUDGET_APPROVER, ROLE_BUDGET_OFFICER
from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record
from kentender_core.services.responsibility_errors import fail


def _require(user: str, role: str) -> Any:
	decision = authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND)
	if not decision.allowed:
		fail(decision.reason_code or "AUTH_RESPONSIBILITY_REQUIRED")
	return decision


def require_officer(user: str) -> str:
	"""The live Budget Officer assignment exercised, for the record."""
	return str(_require(user, ROLE_BUDGET_OFFICER).assignment_id or "")


def require_approver(user: str) -> str:
	return str(_require(user, ROLE_BUDGET_APPROVER).assignment_id or "")


def _norm(user: Any) -> str:
	return str(user or "").strip().lower()


def participants(*, prepared_by: str, submitted_by: str, confirmers: Iterable[dict[str, Any]]) -> set[str]:
	"""Every person who prepared, submitted or confirmed the funding basis relied on."""
	found = {_norm(prepared_by), _norm(submitted_by)}
	found.update(_norm(c.get("user")) for c in confirmers or [])
	return found - {""}


def require_independent(approver: str, *, prepared_by: str, submitted_by: str, confirmers: Iterable[dict[str, Any]]) -> None:
	"""Refuse `AUTH_SEGREGATION_BLOCKED` unless `approver` is none of the participants, and unless both a preparer and at least one basis confirmer are shown."""
	confirmers = list(confirmers or [])
	if not _norm(prepared_by) or not any(_norm(c.get("user")) for c in confirmers):
		fail("AUTH_SEGREGATION_BLOCKED")
	if _norm(approver) in participants(prepared_by=prepared_by, submitted_by=submitted_by, confirmers=confirmers) or not _norm(approver):
		fail("AUTH_SEGREGATION_BLOCKED")


def session_user() -> str:
	return frappe.session.user
