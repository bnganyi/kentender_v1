# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP3 workbench demo scope — hide test/dev pollution from the ordinary workbench view."""

from __future__ import annotations

import re
from typing import Any

_WORKS_MASTER_CODE_PREFIXES = ("DEM-MOH-2026", "PKG-MOH-2026", "PLAN-MOH-2026")

_DEMO_POLLUTION_TITLE_PATTERNS = (
	re.compile(r"^pw\s+draft", re.I),
	re.compile(r"^test\b", re.I),
	re.compile(r"^incl\s+demand", re.I),
	re.compile(r"draft\s+\d+", re.I),
)


def _is_works_master_code(code: str) -> bool:
	value = (code or "").strip().upper()
	if not value:
		return False
	return any(value.startswith(prefix) for prefix in _WORKS_MASTER_CODE_PREFIXES)


def is_demo_pollution(*, title: str, code: str) -> bool:
	"""Return True when a workbench row looks like ad-hoc test/dev data."""
	if _is_works_master_code(code):
		return False
	text = (title or "").strip()
	if text.lower() in {"test", "testing"}:
		return True
	for pattern in _DEMO_POLLUTION_TITLE_PATTERNS:
		if pattern.search(text):
			return True
	return False


def filter_demo_workbench_items(
	items: list[dict[str, Any]],
	*,
	include_test_data: bool = False,
) -> list[dict[str, Any]]:
	"""Prefer clean WORKS master seed rows; hide obvious test pollution in demo view."""
	if include_test_data:
		return list(items or [])
	rows = list(items or [])
	master_rows = [
		row
		for row in rows
		if _is_works_master_code(str(row.get("underlying_object_code") or "").strip())
	]
	if master_rows:
		return master_rows
	return [
		row
		for row in rows
		if not is_demo_pollution(
			title=str(row.get("title") or ""),
			code=str(row.get("underlying_object_code") or ""),
		)
	]
