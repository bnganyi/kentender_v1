# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""New Tender package picker — PP2 Package path retired."""

from __future__ import annotations

from typing import Any


def list_packages_for_new_tender(*_args, **_kwargs) -> dict[str, Any]:
	return {
		"ok": True,
		"packages": [],
		"skipped": True,
		"reason": "PP2_PACKAGE_RETIRED",
		"message": "Procurement Package selection is retired. MVP-1 Plan Item take-up will restore New Tender entry.",
	}
