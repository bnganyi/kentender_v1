"""Re-apply A1 if first patch was a no-op (wrong has_table("tabSupplier") check)."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	if not frappe.db.has_table("Supplier"):
		return
	if frappe.db.has_column("Supplier", "kentender_supplier_code"):
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
