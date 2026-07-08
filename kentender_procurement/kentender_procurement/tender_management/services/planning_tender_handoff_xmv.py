# Copyright (c) 2026, KenTender and contributors
"""STD Module POC retired stub — planning→tender XMV handoff unavailable."""

from __future__ import annotations

from typing import Any

from frappe import _

from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	RETIRED_MESSAGE,
)


def validate_package_for_release_xmv(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": "STD_MODULE_RETIRED",
		"message": RETIRED_MESSAGE,
		"retired": True,
		"blockers": [str(RETIRED_MESSAGE)],
	}


def format_xmv_critical_message(*args: Any, **kwargs: Any) -> str:
	return str(RETIRED_MESSAGE)
