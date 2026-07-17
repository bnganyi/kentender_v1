# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""API response envelope helpers."""

from __future__ import annotations

from typing import Any


def success_envelope(
	data: Any,
	*,
	warnings: list | None = None,
	audit_event_id: str | None = None,
) -> dict[str, Any]:
	return {
		"success": True,
		"data": data,
		"warnings": warnings or [],
		"errors": [],
		"audit_event_id": audit_event_id,
	}


def error_envelope(
	errors: list[dict[str, Any]],
	*,
	warnings: list | None = None,
) -> dict[str, Any]:
	return {
		"success": False,
		"data": None,
		"warnings": warnings or [],
		"errors": errors,
		"audit_event_id": None,
	}
