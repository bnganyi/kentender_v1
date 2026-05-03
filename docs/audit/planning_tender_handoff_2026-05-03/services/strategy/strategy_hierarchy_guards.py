# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""Shared guards for Strategy Program / Objective / Target (v1 hierarchy)."""

from __future__ import annotations

import frappe
from frappe import _


def assert_plan_is_draft_for_mutation(strategic_plan: str) -> None:
	"""G2: Only Draft plans allow hierarchy mutations."""
	if not strategic_plan:
		return
	status = frappe.db.get_value("Strategic Plan", strategic_plan, "status")
	if status and status != "Draft":
		frappe.throw(
			_("Cannot change programs, objectives, or targets while the strategic plan is {0}. Set status to Draft to edit.").format(
				frappe.bold(status)
			)
		)
