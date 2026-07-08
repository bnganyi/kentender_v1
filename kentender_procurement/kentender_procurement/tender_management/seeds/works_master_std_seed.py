# Copyright (c) 2026, KenTender and contributors
"""STD Module POC retired stub — WORKS master STD seed step is a no-op."""

from __future__ import annotations

from typing import Any

from frappe import _

RETIRED_MESSAGE = _(
	"The STD Module POC has been archived. WORKS STD master seed is unavailable until the production STD Library Management module ships."
)


def upsert_works_master_std(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": "STD_MODULE_RETIRED",
		"message": RETIRED_MESSAGE,
		"retired": True,
		"skipped": True,
	}
