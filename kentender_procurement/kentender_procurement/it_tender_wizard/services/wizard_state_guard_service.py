# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""State transition guards."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws


def assert_deletable(state: str) -> None:
	if (state or "").strip() not in ws.DELETABLE_STATES:
		frappe.throw(
			_("Only DRAFT configurations may be deleted."),
			title="ITW_STATE_CONFLICT",
			exc=frappe.ValidationError,
		)


def assert_std_version_immutable(existing_version: str, requested_version: str) -> None:
	if existing_version and requested_version and existing_version != requested_version:
		frappe.throw(
			_("STD version binding is immutable after creation."),
			title="ITW_IMMUTABLE_STD_VERSION",
			exc=frappe.ValidationError,
		)
