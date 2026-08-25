# Copyright (c) 2026, KenTender and contributors
"""Repair existing sites where the Budget Management Workspace was named
"Budget & Funding" (autoname derived from label instead of the canonical name).
"""

from __future__ import annotations

from kentender_budget.services.budget_workspace import ensure_budget_workspace


def execute() -> None:
	ensure_budget_workspace()
