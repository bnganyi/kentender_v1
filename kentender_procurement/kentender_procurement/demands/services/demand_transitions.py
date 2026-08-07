# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-PERM-003 — Demands status/stage transition matrix (server authoritative)."""

from __future__ import annotations

from typing import NamedTuple

import frappe
from frappe import _

from kentender_procurement.demands.services.demand_permissions import (
	assert_business_approver_segregation,
	assert_can_perform_stage_action,
	assert_demand_scope,
	throw_demand_error,
)

ERR_INVALID_TRANSITION = "DEMAND_INVALID_TRANSITION"

STATUSES = (
	"Draft",
	"In Review",
	"Returned",
	"Approved",
	"Rejected",
	"Cancelled",
)

STAGES = (
	"Request Preparation",
	"Business Review",
	"Procurement Enrichment",
	"Budget Confirmation",
	"Final Approval",
	"Complete",
)


class TransitionResult(NamedTuple):
	status: str
	stage: str


# (status, stage, action) → (next_status, next_stage)
DEMAND_TRANSITIONS: dict[tuple[str, str, str], TransitionResult] = {
	("Draft", "Request Preparation", "Submit"): TransitionResult("In Review", "Business Review"),
	("Returned", "Request Preparation", "Submit"): TransitionResult(
		"In Review", "Business Review"
	),
	("Draft", "Request Preparation", "Cancel"): TransitionResult("Cancelled", "Complete"),
	("Returned", "Request Preparation", "Cancel"): TransitionResult("Cancelled", "Complete"),
	("In Review", "Business Review", "Support"): TransitionResult(
		"In Review", "Procurement Enrichment"
	),
	("In Review", "Business Review", "Return"): TransitionResult(
		"Returned", "Request Preparation"
	),
	("In Review", "Business Review", "Reject"): TransitionResult("Rejected", "Complete"),
	("In Review", "Procurement Enrichment", "Send for budget confirmation"): TransitionResult(
		"In Review", "Budget Confirmation"
	),
	("In Review", "Procurement Enrichment", "Return"): TransitionResult(
		"Returned", "Request Preparation"
	),
	("In Review", "Procurement Enrichment", "Reject"): TransitionResult("Rejected", "Complete"),
	("In Review", "Budget Confirmation", "Confirm funding"): TransitionResult(
		"In Review", "Final Approval"
	),
	("In Review", "Budget Confirmation", "Return"): TransitionResult(
		"Returned", "Procurement Enrichment"
	),
	("In Review", "Final Approval", "Approve"): TransitionResult("Approved", "Complete"),
	("In Review", "Final Approval", "Return"): TransitionResult(
		"Returned", "Budget Confirmation"
	),
	("In Review", "Final Approval", "Reject"): TransitionResult("Rejected", "Complete"),
	("In Review", "Final Approval", "Cancel"): TransitionResult("Cancelled", "Complete"),
}


def resolve_transition(status: str, stage: str, action: str) -> TransitionResult:
	key = (status, stage, action)
	if key not in DEMAND_TRANSITIONS:
		throw_demand_error(
			ERR_INVALID_TRANSITION,
			_("Invalid Demand transition: {0} / {1} / {2}").format(status, stage, action),
		)
	return DEMAND_TRANSITIONS[key]


def assert_valid_transition(status: str, stage: str, action: str) -> TransitionResult:
	return resolve_transition(status, stage, action)


def preview_transition(
	*,
	status: str,
	stage: str,
	action: str,
	procuring_entity: str | None = None,
	owner_org_unit: str | None = None,
	requester: str | None = None,
	user: str | None = None,
	small_entity_exception: bool = False,
	check_scope: bool = True,
) -> TransitionResult:
	"""Validate role, optional scope/segregation, and return next status/stage.

	Does not mutate documents — Wave 3 services apply the result.
	"""
	user = user or frappe.session.user
	assert_can_perform_stage_action(stage, action, user=user)
	if check_scope:
		assert_demand_scope(
			procuring_entity=procuring_entity,
			owner_org_unit=owner_org_unit,
			user=user,
			require_write=True,
		)
	if action in ("Support", "Return", "Reject") and stage == "Business Review":
		assert_business_approver_segregation(
			requester=requester,
			actor=user,
			small_entity_exception=small_entity_exception,
		)
	return resolve_transition(status, stage, action)
