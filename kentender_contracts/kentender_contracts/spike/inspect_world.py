"""Phase 2 spike (CM plan, tracker CM8-201): read-only description of the ERPNext world on the site.
Run: bench --site kentender-test.local execute kentender_contracts.spike.inspect_world.describe"""
import json

import frappe


def _count(dt, **filters):
	return frappe.db.count(dt, filters or None)


def _single(doctype, fields):
	meta = frappe.get_meta(doctype)
	return {f: (frappe.db.get_single_value(doctype, f) if meta.has_field(f) else "(no such field)") for f in fields}


def describe():
	company = frappe.get_all("Company", fields=["name", "abbr", "default_currency", "country", "stock_received_but_not_billed", "default_payable_account",
		"default_inventory_account", "stock_adjustment_account", "cost_center", "enable_perpetual_inventory", "asset_received_but_not_billed",
		"capital_work_in_progress_account", "default_bank_account", "default_cash_account", "round_off_account", "accumulated_depreciation_account",
		"depreciation_expense_account", "disposal_account", "default_expense_account", "default_income_account", "write_off_account"])
	out = {"frappe": frappe.__version__, "company": company}
	out["warehouses"] = frappe.get_all("Warehouse", fields=["name", "company", "is_group", "warehouse_type", "account"], limit_page_length=50)
	out["counts"] = {dt: _count(dt) for dt in ("Account", "Cost Center", "Item", "Item Group", "UOM", "Supplier", "Supplier Group", "Asset Category", "Asset", "Purchase Order",
		"Purchase Receipt", "Purchase Invoice", "Payment Entry", "Journal Entry", "Quality Inspection", "Quality Inspection Template", "Serial No", "Batch", "Stock Ledger Entry",
		"GL Entry", "Bank Account", "Mode of Payment", "Purchase Taxes and Charges Template", "Workflow", "Fiscal Year", "Price List", "Item Tax Template")}
	out["fiscal_years"] = frappe.get_all("Fiscal Year", fields=["name", "year_start_date", "year_end_date", "disabled"], filters={"name": ["not like", "_Test%"]})
	out["fiscal_year_companies"] = frappe.get_all("Fiscal Year Company", fields=["parent", "company"], limit_page_length=10)
	out["buying_settings"] = _single("Buying Settings", ("po_required", "pr_required", "maintain_same_rate", "allow_multiple_items", "bill_for_rejected_quantity_in_purchase_invoice"))
	out["stock_settings"] = _single("Stock Settings", ("allow_negative_stock", "auto_insert_price_list_rate_if_missing", "action_if_quality_inspection_is_not_submitted",
		"action_if_quality_inspection_is_rejected", "allow_partial_reservation", "over_delivery_receipt_allowance", "default_warehouse", "enable_stock_reservation", "use_serial_batch_fields"))
	out["accounts_settings"] = _single("Accounts Settings", ("unlink_payment_on_cancellation_of_invoice", "allow_stale", "check_supplier_invoice_uniqueness",
		"enable_common_party_accounting", "frozen_accounts_modifier", "acc_frozen_upto", "make_payment_via_journal_entry", "ignore_account_closing_balance"))
	out["uoms"] = frappe.get_all("UOM", filters={"name": ["in", ["Nos", "Unit", "Each", "Piece"]]}, pluck="name")
	out["user_roles_of_personas"] = {}
	for u in ("josphat.mwangi@moh.example.test", "beatrice.kamau@moh.example.test", "julia.njeri@moh.example.test", "charles.mutiso@moh.example.test"):
		out["user_roles_of_personas"][u] = sorted(r for r in frappe.get_roles(u) if r not in ("All", "Guest", "Desk User"))
	out["workflows"] = frappe.get_all("Workflow", fields=["name", "document_type", "is_active"])
	print(json.dumps(out, indent=1, default=str))
