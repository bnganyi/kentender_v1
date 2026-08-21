# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Prepare MOH fixtures for BUD-SUP-002 Playwright role matrix."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from kentender_budget.seeds.budget_role_users import upsert_budget_role_users
from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_core.seeds.moh_mvp_v1.constants import C


def prepare_budget_role_matrix_ui() -> dict:
	"""Reseed portfolio + role users; pin Draft budget Submitted for AC-018 dual-role UI."""
	upsert_budget_role_users()
	upsert_moh_mvp_v1_portfolio()
	name = frappe.db.get_value("Budget", {"generated_reference": C.BUD_DRAFT}, "name")
	if name:
		frappe.db.set_value(
			"Budget",
			name,
			{
				"status": "Submitted",
				"submitted_by": "moh.budget.officer.authority@example.test",
				"reviewed_by": "moh.budget.reviewer@example.test",
				"reviewed_at": now_datetime(),
				"return_reason": "",
			},
		)
	frappe.db.commit()
	return {"ok": True, "budget": name or ""}
