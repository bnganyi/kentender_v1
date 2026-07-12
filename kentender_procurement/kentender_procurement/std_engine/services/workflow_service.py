# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Minimal STD Version lifecycle transitions for Step 1."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
	"DRAFT": ("LEGAL_REVIEW", "APPROVED", "ACTIVE"),
	"LEGAL_REVIEW": ("APPROVED", "DRAFT"),
	"APPROVED": ("ACTIVE", "DRAFT"),
	"ACTIVE": (),
}


def get_available_transitions(package_id: str) -> list[str]:
	state = _current_state(package_id)
	return list(ALLOWED_TRANSITIONS.get(state, ()))


def assert_transition_allowed(package_id: str, target_state: str) -> None:
	current = _current_state(package_id)
	allowed = ALLOWED_TRANSITIONS.get(current, ())
	target = (target_state or "").strip().upper()
	if target not in allowed:
		frappe.throw(
			_(f"Transition {current} -> {target} is not allowed."),
			title="STD_TRANSITION_NOT_ALLOWED",
		)


def execute_transition(package_id: str, target_state: str, *, reason: str | None = None) -> dict[str, Any]:
	assert_transition_allowed(package_id, target_state)
	target = target_state.strip().upper()
	frappe.db.set_value("STD Version", package_id, "lifecycle_state", target, update_modified=False)
	return {
		"package_id": package_id,
		"lifecycle_state": target,
		"reason": reason,
	}


def _current_state(package_id: str) -> str:
	return (frappe.db.get_value("STD Version", package_id, "lifecycle_state") or "DRAFT").strip().upper()
