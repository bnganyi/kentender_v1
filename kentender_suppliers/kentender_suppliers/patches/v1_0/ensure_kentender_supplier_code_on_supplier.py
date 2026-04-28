"""Add KenTender business supplier code on ERPNext Supplier (A1)."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	# Frappe has_table() expects a DocType name, not a physical table name.
	# (Passing "tabSupplier" would look for tabtabSupplier and no-op the patch.)
	if not frappe.db.has_table("Supplier"):
		return

	create_custom_fields(
		{
			"Supplier": [
				{
					"fieldname": "kentender_supplier_code",
					"fieldtype": "Data",
					"label": "KenTender Supplier Code",
					"insert_after": "supplier_name",
					"unique": 1,
					"description": "Public business id (e.g. SUP-KE-YYYY-####) for APIs and display.",
					"translatable": 0,
				}
			]
		},
		ignore_validate=True,
		update=True,
	)
	frappe.clear_cache(doctype="Supplier")
