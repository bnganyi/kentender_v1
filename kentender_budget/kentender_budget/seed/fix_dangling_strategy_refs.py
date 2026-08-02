"""W6-12 — Fix dangling strategy references (no-op after MVP-1 strategy teardown).

Strategy Link fields were removed from Budget / Budget Line. This script is kept
as a callable entry point for existing Makefile / docs commands.
"""
from __future__ import annotations


def run():
	"""No-op: strategy FK columns no longer exist on Budget / Budget Line."""
	return {
		"skipped": True,
		"reason": "strategy_link_fields_removed",
		"fixed_lines": 0,
		"fixed_budgets": 0,
	}
