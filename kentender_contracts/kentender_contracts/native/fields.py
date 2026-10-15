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
	ensure_indexes()
	frappe.clear_cache()


def ensure_indexes() -> None:
	"""A contract registered from outside has one case: its origin key (site, origin system, external contract identity) is unique. It is an index added here, not a UNIQUE column in the DocType, because a
	UNIQUE column cannot be added to a table that already exists on SQLite (the independence site). Idempotent on both databases."""
	if frappe.db.has_column("Contract Case", "origin_key"):
		frappe.db.add_unique("Contract Case", ["origin_key"], constraint_name="cm_origin_key_unique")


def missing() -> list[str]:
	"""`DocType.fieldname` for every field not yet installed."""
	return [f"{doctype}.{field['fieldname']}" for doctype, fields in CUSTOM_FIELDS.items() for field in fields if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]})]
