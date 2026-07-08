# Copyright (c) 2026, KenTender and contributors
"""STD Module POC retired stub."""

from __future__ import annotations

from typing import Any

TEMPLATE_CODE = "KE-PPRA-WORKS-BLDG-2022-04-POC"


def upsert_std_template(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return {"ok": False, "error_code": "STD_MODULE_RETIRED", "retired": True}
