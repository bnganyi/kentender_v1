# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0003 — feature flag for std config UI v2 (catalogue + configurator)."""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.services.std_config_roles import (
	STD_ADVANCED_CATALOGUE_ROLES,
	STD_CONFIGURATOR_WRITE_ROLES,
	STD_TECHNICAL_VIEW_ROLES,
	can_edit_technical_json_config,
	can_use_std_advanced_catalogue,
	can_view_technical_json,
)


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
	proc = bootinfo["kentender_procurement"]
	proc["std_config_ui_v2_enabled"] = is_std_config_ui_v2_enabled()
	proc["std_technical_view_roles"] = sorted(STD_TECHNICAL_VIEW_ROLES)
	proc["std_advanced_catalogue_roles"] = sorted(STD_ADVANCED_CATALOGUE_ROLES)
	proc["std_configurator_write_roles"] = sorted(STD_CONFIGURATOR_WRITE_ROLES)
	proc["can_use_std_advanced_catalogue"] = can_use_std_advanced_catalogue()
	proc["can_view_technical_json"] = can_view_technical_json()
	proc["can_edit_technical_json"] = can_edit_technical_json_config()
