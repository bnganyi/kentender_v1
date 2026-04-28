# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""
I1–I2: idempotent dev/UAT seed: document types, categories, sample supplier + profile
(codes like SUP-KE-2026-00xx; align with seed doc §2 where applicable).
"""

import frappe


def ensure_document_types():
	"""I1: registration-required doc type (edge cases driven by I2 in tests/optional seeds)."""
	specs = [
		{
			"doctype": "KTSM Document Type",
			"document_type_code": "KTSM-REG-CR",
			"document_type_name": "Certificate of registration",
			"required_for_registration": 0,
			"expires": 0,
			"is_active": 1,
		},
	]
	for s in specs:
		if frappe.db.exists("KTSM Document Type", {"document_type_code": s["document_type_code"]}):
			continue
		d = frappe.get_doc(s)
		d.insert(ignore_permissions=True)


def ensure_categories():
	specs = [
		{
			"doctype": "KTSM Supplier Category",
			"category_name": "Medical consumables (seed)",
			"category_code": "CAT-MED-001",
			"is_active": 1,
		},
	]
	for s in specs:
		if frappe.db.exists("KTSM Supplier Category", {"category_code": s["category_code"]}):
			continue
		c = frappe.get_doc(s)
		c.insert(ignore_permissions=True)


def ensure_sample_supplier(yr: str = "2026", display_suffix: str = "Seed Demo"):
	"""Create Supplier + Profile in Draft; idempotent on fixed code."""
	if not frappe.db.has_column("Supplier", "kentender_supplier_code"):
		return
	code = f"SUP-KE-{yr}-0001"
	erpname = frappe.db.get_value("Supplier", {"kentender_supplier_code": code}, "name")
	if not erpname:
		sg = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or frappe.db.get_value(
			"Supplier Group", {}, "name"
		)
		erp = frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": f"KenTender {display_suffix} {code}",
				"supplier_type": "Company",
				"supplier_group": sg,
				"kentender_supplier_code": code,
			}
		)
		erp.insert(ignore_permissions=True)
		erpname = erp.name
	if frappe.db.exists("KTSM Supplier Profile", {"erpnext_supplier": erpname}):
		return
	p = frappe.get_doc(
		{
			"doctype": "KTSM Supplier Profile",
			"erpnext_supplier": erpname,
		}
	)
	p.insert(ignore_permissions=True)


def run(yr: str = "2026") -> None:
	ensure_document_types()
	ensure_categories()
	# After document types, compliance may be Incomplete for existing profiles; seed is best-effort.
	ensure_sample_supplier(yr=yr)
	frappe.db.commit()  # noqa: S608 — explicit seed finalization
	frappe.clear_cache()


def run_console():
	"""bench execute kentender_suppliers.seeds.seed_ktsm_mvp.run"""
	run()


if __name__ == "__main__":
	run()
