# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5C-002 / P5C-003 / P5C-004 — Planning Home summary counts and queue APIs."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.planning_home_queues import (
	BLOCKED_VIEW_ALL_HREF,
	NEEDS_PLANNING_VIEW_ALL_HREF,
	NEEDS_REVIEW_VIEW_ALL_HREF,
	PLANNING_HOME_QUEUE_LIMIT,
	RELEASED_RECENTLY_VIEW_ALL_HREF,
	READY_RELEASE_VIEW_ALL_HREF,
	get_blocked_home_queue,
	get_needs_planning_home_queue,
	get_needs_review_home_queue,
	get_released_recently_home_queue,
	get_ready_to_release_home_queue,
)
from kentender_procurement.procurement_planning.services.planning_home_summary import (
	get_planning_home_summary,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"summary": {
			"needs_planning": 0,
			"needs_review": 0,
			"ready_to_release": 0,
			"released_recently": 0,
			"blocked": 0,
		},
	}


def _queue_fail(
	*,
	code: str,
	message: str,
	role_key: str = "auditor",
	queue_key: str = "needs_planning",
	view_all_href: str = NEEDS_PLANNING_VIEW_ALL_HREF,
) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"queue_key": queue_key,
		"total": 0,
		"limit": PLANNING_HOME_QUEUE_LIMIT,
		"items": [],
		"view_all_href": view_all_href,
	}


def _planning_queue_read_gate(
	queue_key: str,
	view_all_href: str,
) -> tuple[str | None, dict[str, Any] | None]:
	def fail(**kwargs: Any) -> dict[str, Any]:
		return _queue_fail(**kwargs, queue_key=queue_key, view_all_href=view_all_href)

	return pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to the Procurement Planning home queues."),
		fail=fail,
		installed_doctype="Procurement Plan",
	)


def _planning_read_gate() -> tuple[str | None, dict[str, Any] | None]:
	return pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to the Procurement Planning home summary."),
		fail=_fail,
		installed_doctype="Procurement Plan",
	)


@frappe.whitelist()
def get_pp_planning_home_summary() -> dict[str, Any]:
	"""Return Planning Home summary counts (reset addendum §7.2)."""
	role_key, denied = _planning_read_gate()
	if denied:
		return denied
	_ = role_key
	return get_planning_home_summary(frappe.session.user)


@frappe.whitelist()
def get_pp_planning_home_needs_planning_queue() -> dict[str, Any]:
	"""Return Needs Planning home queue slice (reset addendum §8.4)."""
	role_key, denied = _planning_queue_read_gate("needs_planning", NEEDS_PLANNING_VIEW_ALL_HREF)
	if denied:
		return denied
	_ = role_key
	return get_needs_planning_home_queue(frappe.session.user)


@frappe.whitelist()
def get_pp_planning_home_needs_review_queue() -> dict[str, Any]:
	"""Return Needs Review home queue slice (reset addendum §8.4)."""
	role_key, denied = _planning_queue_read_gate("needs_review", NEEDS_REVIEW_VIEW_ALL_HREF)
	if denied:
		return denied
	_ = role_key
	return get_needs_review_home_queue(frappe.session.user)


@frappe.whitelist()
def get_pp_planning_home_ready_to_release_queue() -> dict[str, Any]:
	"""Return Ready to Release home queue slice (reset addendum §8.4)."""
	role_key, denied = _planning_queue_read_gate("ready_to_release", READY_RELEASE_VIEW_ALL_HREF)
	if denied:
		return denied
	_ = role_key
	return get_ready_to_release_home_queue(frappe.session.user)


@frappe.whitelist()
def get_pp_planning_home_released_recently_queue() -> dict[str, Any]:
	"""Return Released Recently home queue slice (reset addendum §8.4)."""
	role_key, denied = _planning_queue_read_gate("released_recently", RELEASED_RECENTLY_VIEW_ALL_HREF)
	if denied:
		return denied
	_ = role_key
	return get_released_recently_home_queue(frappe.session.user)


@frappe.whitelist()
def get_pp_planning_home_blocked_queue() -> dict[str, Any]:
	"""Return Blocked home queue slice (reset addendum §8.4)."""
	role_key, denied = _planning_queue_read_gate("blocked", BLOCKED_VIEW_ALL_HREF)
	if denied:
		return denied
	_ = role_key
	return get_blocked_home_queue(frappe.session.user)
