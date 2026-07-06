# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0610 — enable std config UI v2 as primary experience."""

from __future__ import annotations

import frappe
from frappe.installer import update_site_config


def execute() -> None:
	update_site_config("std_config_ui_v2_enabled", True, validate=False)
	frappe.conf["std_config_ui_v2_enabled"] = True
	frappe.cache.delete_value("bootinfo")
