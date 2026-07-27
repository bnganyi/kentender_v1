# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure BWMF DocTypes are loaded from filesystem (G1 Phase 2)."""

from __future__ import annotations

from pathlib import Path

import frappe


def execute() -> None:
	base = Path(frappe.get_app_path("kentender_procurement")) / "tender_configurations" / "doctype"
	if not base.is_dir():
		return
	for path in sorted(base.iterdir()):
		if not path.is_dir() or not path.name.startswith("bwmf_"):
			continue
		frappe.reload_doc("Tender Configurations", "doctype", path.name, force=True)
