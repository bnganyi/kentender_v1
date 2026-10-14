# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The facts ERPNext does not hold, added through its documented extension point (plan D7, FU-CM-48).

`cm_operation_identity` marks every native document Contract Management creates, so a retry reads the owner by identity and
never posts twice. `cm_certified_amount` is the amount procurement certified on an invoice, the ceiling for payment.
`cm_unit_reference` is the contract's own reference for one fixed asset (the Asset record has no serial field). `no_copy`
stops an amendment or a duplicate from inheriting a stale value; the identity is indexed because it is looked up on every retry.
Installed idempotently on install and on every migrate."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

_IDENTITY = {"fieldname": "cm_operation_identity", "label": "Contract operation identity", "fieldtype": "Data", "read_only": 1, "no_copy": 1, "search_index": 1, "insert_after": "naming_series"}

CUSTOM_FIELDS: dict[str, list[dict]] = {
	"Purchase Order": [_IDENTITY],
	"Purchase Receipt": [_IDENTITY],
	"Payment Entry": [_IDENTITY],
	"Purchase Invoice": [_IDENTITY, {"fieldname": "cm_certified_amount", "label": "Contract certified amount", "fieldtype": "Currency", "read_only": 1, "no_copy": 1, "insert_after": "cm_operation_identity"}],
	"Asset": [{"fieldname": "cm_unit_reference", "label": "Contract unit reference", "fieldtype": "Data", "read_only": 1, "no_copy": 1, "search_index": 1, "insert_after": "asset_name"}],
}


def ensure() -> None:
	create_custom_fields(CUSTOM_FIELDS, update=True)
	frappe.clear_cache()


def missing() -> list[str]:
	"""`DocType.fieldname` for every field not yet installed."""
	return [f"{doctype}.{field['fieldname']}" for doctype, fields in CUSTOM_FIELDS.items() for field in fields if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]})]
