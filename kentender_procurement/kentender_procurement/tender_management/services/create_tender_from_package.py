# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Create tender from package — PP2 path retired (closed stub)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def create_tender_from_package(*_args, **_kwargs) -> dict[str, Any]:
	frappe.throw(
		_("Creating a tender from a procurement package is retired."),
		frappe.ValidationError,
		title="TM2_PACKAGE_RETIRED",
	)
