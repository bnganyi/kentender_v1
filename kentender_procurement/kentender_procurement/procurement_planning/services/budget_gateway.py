# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §7.3 — the Budget & Funding contracts, under the spec's
verbs (decision D6).

Planning calls only Budget's published API module and never reads Budget Line
tables directly (the pre-v1.2 module did — a boundary violation this file
closes). Name deltas the adapters carry:

	ListEligibleBudgetLines      → budget_api.list_eligible_budget_lines
	CheckAndReserveFunding       → budget_api.check_funding → 300 s token →
	                               budget_api.reserve_funding (all-or-none)
	ReleasePlanningReservations  → budget_api.release_reservation per
	                               reservation, one Planning correlation +
	                               idempotency key per batch, unconverted
	                               remainder only
	RevalidatePlanningReservations → budget_api.revalidate_reservations
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from contextlib import contextmanager

from kentender_procurement.procurement_planning.errors import fail


@contextmanager
def _system_principal():
	"""Temporarily evaluate one cross-module read as Administrator WITHOUT
	`frappe.set_user`.

	`frappe.set_user` is safe in patches/jobs but is destructive inside a web
	request: it overwrites `session.user`, sets `session.sid` to the USERNAME
	and empties `session.data` on the live session object — the request-end
	session save then persists that mangled state, and every later request on
	the same sid arrives as Guest ("User None not found" + a not-whitelisted
	refusal). Observed live in the Slice B browser run; a `finally:
	set_user(caller)` does NOT undo it (the sid/data stay mangled).

	This swap restores the exact session fields and clears the caches
	`set_user` would have cleared, so the web session survives intact."""
	local = frappe.local
	session = local.session
	saved = (session.user, session.sid, session.data)
	saved_form_dict = local.form_dict
	saved_user_obj = getattr(local, "user_obj", None)
	try:
		session.user = "Administrator"
		local.role_permissions = {}
		local.user_obj = None
		yield
	finally:
		session.user, session.sid, session.data = saved
		local.form_dict = saved_form_dict
		local.role_permissions = {}
		local.user_obj = saved_user_obj


def list_eligible_budget_lines(
	*, procuring_entity: str, financial_year: str, source_org_unit: str | None = None
) -> list[dict[str, Any]]:
	"""Runs as a system principal, deliberately: Budget's read scope admits only
	Budget-side roles (`require_budget_read_scope`), while §7.3/§12.3 requires
	the *departmental* author to see their department's eligible Active lines.
	Every Planning caller authorises its own actor for the exact PE/OU first,
	and the result is already narrowed to that department's eligible lines —
	the pre-v1.2 module handled the same mismatch by reading Budget tables
	directly, which is the boundary violation this gateway closes."""
	from kentender_budget.api.budget_api import list_eligible_budget_lines as contract

	with _system_principal():
		return contract(
			procuring_entity=procuring_entity,
			financial_year=financial_year,
			source_org_unit=source_org_unit,
		)


def eligible_line_ids(
	*, procuring_entity: str, financial_year: str, source_org_unit: str | None = None
) -> set[str]:
	return {
		cstr(row.get("id") or row.get("name"))
		for row in list_eligible_budget_lines(
			procuring_entity=procuring_entity,
			financial_year=financial_year,
			source_org_unit=source_org_unit,
		)
	}


def check_funding(
	*,
	plan_item: str,
	plan_version: str,
	finance_task: str,
	source_set_hash: str,
	allocations: list[dict[str, Any]],
	correlation_id: str,
) -> dict[str, Any]:
	from kentender_budget.api.budget_api import check_funding as contract

	return contract(
		plan_item=plan_item,
		plan_version=plan_version,
		finance_task=finance_task,
		source_set_hash=source_set_hash,
		allocations=allocations,
		correlation_id=correlation_id,
	)


def reserve_funding(
	*,
	check_token: str,
	finance_task: str,
	source_set_hash: str,
	idempotency_key: str,
) -> dict[str, Any]:
	from kentender_budget.api.budget_api import reserve_funding as contract

	return contract(
		token=check_token,
		finance_task=finance_task,
		source_set_hash=source_set_hash,
		idempotency_key=idempotency_key,
	)


def release_planning_reservations(
	*,
	reservation_refs: list[dict[str, Any]],
	correlation_id: str,
	event_type: str,
) -> list[dict[str, Any]]:
	"""Release the unconverted remainder of every reference under one Planning
	correlation. A failure rolls the calling transition back (§7.3): the
	ProcurementPlanningError below must propagate, never be swallowed."""
	from kentender_budget.api.budget_api import release_reservation as contract

	results = []
	for index, ref in enumerate(reservation_refs, start=1):
		try:
			results.append(
				contract(
					reservation=ref["reservation"],
					amount=None,  # unconverted remainder
					downstream_event_id=f"{correlation_id}:{index}",
					downstream_event_type=event_type,
					idempotency_key=f"{correlation_id}:{ref['reservation']}",
				)
			)
		except Exception:
			frappe.log_error(
				title="PLN_RESERVATION_RELEASE_FAILED",
				message=f"correlation={correlation_id} reservation={ref.get('reservation')}",
			)
			fail(
				"PLN_RESERVATION_RELEASE_FAILED",
				"Funding could not be released. The Planning change was not "
				f"completed. Try again or quote support reference {correlation_id}.",
			)
	return results


def revalidate_planning_reservations(
	*, reservations: list[str], correlation_id: str, event_type: str
) -> dict[str, Any]:
	from kentender_budget.api.budget_api import revalidate_reservations as contract

	return contract(
		reservations=reservations,
		downstream_event_id=correlation_id,
		downstream_event_type=event_type,
		idempotency_key=correlation_id,
	)


def reservation_states(reservations: list[str]) -> dict[str, str]:
	"""Read-only §4.11 derivation: Budget stays authoritative for status."""
	if not reservations:
		return {}
	rows = frappe.get_all(
		"Funding Reservation",
		filters={"name": ["in", reservations]},
		fields=["name", "status"],
		limit_page_length=0,
	)
	return {row.name: row.status for row in rows}
