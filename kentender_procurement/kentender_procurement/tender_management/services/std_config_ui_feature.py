# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0003 — feature flag for std config UI v2 (catalogue + configurator)."""

from __future__ import annotations

import frappe


def is_std_config_ui_v2_enabled() -> bool:
	"""Return True when the new STD Library / Configurator pages are primary."""
	value = frappe.conf.get("std_config_ui_v2_enabled")
	if value is None:
		try:
			from frappe.utils import get_site_config

			value = get_site_config().get("std_config_ui_v2_enabled")
		except Exception:
			value = None
	if value is None:
		return False
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "on"}
	return bool(value)


def expose_std_config_ui_boot(bootinfo: dict) -> None:
	bootinfo.setdefault("kentender_procurement", {})
	bootinfo["kentender_procurement"]["std_config_ui_v2_enabled"] = is_std_config_ui_v2_enabled()
