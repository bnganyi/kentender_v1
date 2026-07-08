# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0003 — register std_config_ui_v2_enabled site config key (default off)."""

from __future__ import annotations

import frappe


def execute() -> None:
	# Default remains off until STD-CFG-0600 retirement gate passes.
	if frappe.conf.get("std_config_ui_v2_enabled") is not None:
		return
	# Idempotent: do not force-enable; operators enable via site_config.json when ready.
	frappe.cache.delete_value("bootinfo")
