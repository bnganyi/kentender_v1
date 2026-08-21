# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared Budget seed helpers — neutralized by MVP-1 Budget preparatory teardown."""

from __future__ import annotations

from typing import Any

BUDGET_2026_NAME = "BUDGET-MOH-2026"
BUDGET_2027_NAME = "BUDGET-MOH-2027"


def clear_budget_data(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	return {"ok": True, "skipped": True, "reason": "mvp1-budget-teardown"}


def get_plan_name(*_args: Any, **_kwargs: Any) -> str | None:
	return None


def get_program_name(*_args: Any, **_kwargs: Any) -> str | None:
	return None


def upsert_budget(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	return {"ok": True, "skipped": True, "reason": "mvp1-budget-teardown"}


def upsert_budget_allocation(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	return {"ok": True, "skipped": True, "reason": "mvp1-budget-teardown"}
