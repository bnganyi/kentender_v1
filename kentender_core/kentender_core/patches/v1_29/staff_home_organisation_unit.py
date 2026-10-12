# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUTH-ADR-001 v1.12 §4.8, §11.2 — add the staff home organisation unit and
retire `kt_primary_department`.

The retired field's values name a Procurement Department, not an Organisation
Unit, so none is converted into a home unit: administrators record home units
through System setup. Idempotent."""

from __future__ import annotations

import frappe

NEW_FIELD = "kt_home_organisation_unit"
RETIRED_FIELD = "kt_primary_department"


def execute():
	from kentender_core.install import _ensure_user_kt_scope_fields

	_ensure_user_kt_scope_fields()
	retired = frappe.db.get_value("Custom Field", {"dt": "User", "fieldname": RETIRED_FIELD}, "name")
	if retired:
		frappe.delete_doc("Custom Field", retired, force=True, ignore_permissions=True)
	frappe.clear_cache(doctype="User")
