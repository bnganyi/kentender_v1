# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared DocType validators for STD Engine."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.constants import LIFECYCLE_STATES


def validate_lifecycle_state(value: str | None) -> None:
	state = (value or "").strip()
	if state not in LIFECYCLE_STATES:
		frappe.throw(
			_("Invalid lifecycle state: {0}").format(state or "(empty)"),
			title=_("STD Lifecycle"),
		)
