# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deprecated shim — use kentender_mvp_v1_portfolio."""

from kentender_budget.seeds.kentender_mvp_v1_portfolio import (  # noqa: F401
	clear_moh_bl_0006_primary_for_e2e,
	set_budget_line_allocation_by_code,
	upsert_kentender_mvp_v1_portfolio as upsert_moh_mvp_v1_portfolio,
)
