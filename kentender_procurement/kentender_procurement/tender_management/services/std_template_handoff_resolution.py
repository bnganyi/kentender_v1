# Copyright (c) 2026, KenTender and contributors
"""STD Module POC retired stub — handoff resolution unavailable until production module."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

STD_MODULE_RETIRED = True
RETIRED_MESSAGE = _(
	"The STD Module POC has been archived. STD template handoff resolution is unavailable until the production STD Library Management module ships."
)


def resolve_std_template_for_handoff(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": "STD_MODULE_RETIRED",
		"message": RETIRED_MESSAGE,
		"retired": True,
	}


def format_ambiguous_std_message(*args: Any, **kwargs: Any) -> str:
	return str(RETIRED_MESSAGE)
