# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release package to tender — PP2 path retired (closed stub)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def release_procurement_package_to_tender(*_args, **_kwargs) -> dict[str, Any]:
	frappe.throw(
		_("Releasing a procurement package to tender is retired."),
		frappe.ValidationError,
		title="TM2_PACKAGE_RETIRED",
	)


def hook_release_procurement_package_to_tender(*_args, **_kwargs) -> None:
	return
