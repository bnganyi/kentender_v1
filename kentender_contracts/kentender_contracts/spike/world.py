"""Phase 2 spike S0 (CM plan, tracker CM8-201): the ERPNext world the spike needs on the TEST site.

Everything created here is named so `teardown()` can remove it; nothing touches the dev site.
Run: bench --site kentender-test.local execute kentender_contracts.spike.world.build
     bench --site kentender-test.local execute kentender_contracts.spike.world.teardown
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import add_days, today

COMPANY = "KenTender"
ABBR = "K"
SUPPLIER = "CM Spike Supplier"
ITEM_FA = "CM-SPIKE-LAPTOP-FA"  # serialised fixed asset
ITEM_STK = "CM-SPIKE-LAPTOP-STK"  # serialised stock item, inspection required
CATEGORY = "CM Spike Electronic Equipment"
WAREHOUSE = f"Stores - {ABBR}"
LOCATION = "CM Spike Store Room"
BANK_ACCOUNT = f"CM Spike Bank - {ABBR}"
USERS = {
	"maker": "cm.spike.maker@spike.example.test",
	"approver": "cm.spike.approver@spike.example.test",
	"other": "cm.spike.other@spike.example.test",
}
ROLES = {
	"maker": ["Accounts User", "Purchase User", "Stock User", "Item Manager"],
	"approver": ["Accounts Manager", "Purchase Manager", "Stock Manager"],
	"other": ["Accounts Manager", "Accounts User"],
}


def _account(name: str, parent_like: str, account_type: str, root_type: str = "Asset") -> str:
	full = f"{name} - {ABBR}"
	if frappe.db.exists("Account", full):
		return full
	parent = frappe.db.get_value("Account", {"company": COMPANY, "is_group": 1, "account_name": parent_like}, "name")
	if not parent:
		raise RuntimeError(f"no parent account {parent_like!r} in {COMPANY}")
	frappe.get_doc({"doctype": "Account", "account_name": name, "parent_account": parent, "company": COMPANY, "account_type": account_type,
		"root_type": root_type, "is_group": 0}).insert(ignore_permissions=True)
	return full


def _user(key: str) -> str:
	email = USERS[key]
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": f"CM Spike {key.title()}", "enabled": 1, "send_welcome_email": 0, "user_type": "System User",
			"roles": [{"role": r} for r in ROLES[key]]}).insert(ignore_permissions=True)
	return email


def build() -> dict:
	made: dict[str, str] = {}
	company = frappe.get_doc("Company", COMPANY)
	made["bank_account"] = _account("CM Spike Bank", "Bank Accounts", "Bank")
	if not frappe.db.exists("Mode of Payment Account", {"parent": "Wire Transfer", "company": COMPANY}):
		mop = frappe.get_doc("Mode of Payment", "Wire Transfer")
		mop.append("accounts", {"company": COMPANY, "default_account": made["bank_account"]})
		mop.save(ignore_permissions=True)
	if not frappe.db.exists("Supplier", SUPPLIER):
		frappe.get_doc({"doctype": "Supplier", "supplier_name": SUPPLIER, "supplier_group": "Hardware", "supplier_type": "Company", "default_currency": "KES"}).insert(ignore_permissions=True)
	made["supplier"] = SUPPLIER
	if not frappe.db.exists("Location", LOCATION):
		frappe.get_doc({"doctype": "Location", "location_name": LOCATION}).insert(ignore_permissions=True)
	if not frappe.db.exists("Asset Category", CATEGORY):
		frappe.get_doc({"doctype": "Asset Category", "asset_category_name": CATEGORY, "enable_cwip_accounting": 0,
			"finance_books": [{"depreciation_method": "Straight Line", "total_number_of_depreciations": 36, "frequency_of_depreciation": 1}],
			"accounts": [{"company_name": COMPANY, "fixed_asset_account": f"1720 - Electronic Equipment - {ABBR}",
				"accumulated_depreciation_account": f"1780 - Accumulated Depreciation - {ABBR}", "depreciation_expense_account": f"5203 - Depreciation - {ABBR}",
				"capital_work_in_progress_account": f"1790 - CWIP Account - {ABBR}"}]}).insert(ignore_permissions=True)
	made["asset_category"] = CATEGORY
	common = {"doctype": "Item", "item_group": "Products", "stock_uom": "Nos", "is_purchase_item": 1, "is_sales_item": 0, "valuation_rate": 100000, "standard_rate": 100000}
	if not frappe.db.exists("Item", ITEM_FA):
		frappe.get_doc({**common, "item_code": ITEM_FA, "item_name": "CM Spike Laptop (fixed asset)", "is_stock_item": 0, "is_fixed_asset": 1, "asset_category": CATEGORY,
			"auto_create_assets": 1, "asset_naming_series": "ACC-ASS-.YYYY.-"}).insert(ignore_permissions=True)
	if not frappe.db.exists("Item", ITEM_STK):
		frappe.get_doc({**common, "item_code": ITEM_STK, "item_name": "CM Spike Laptop (stock)", "is_stock_item": 1, "has_serial_no": 1, "serial_no_series": "CMSPK-.#####",
			"inspection_required_before_purchase": 1}).insert(ignore_permissions=True)
	made["items"] = f"{ITEM_FA}, {ITEM_STK}"
	for key in USERS:
		made[f"user_{key}"] = _user(key)
	frappe.db.commit()
	print(json.dumps(made, indent=1))
	return made


def teardown() -> dict:
	"""Cancel and delete every document the spike made, newest first, then the world itself."""
	removed: dict[str, int] = {}
	items = [ITEM_FA, ITEM_STK]

	def drop(doctype: str, names: list[str]) -> None:
		for name in names:
			try:
				doc = frappe.get_doc(doctype, name)
				if getattr(doc, "docstatus", 0) == 1:
					doc.cancel()
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
				removed[doctype] = removed.get(doctype, 0) + 1
			except Exception as exc:  # noqa: BLE001 - report, keep going
				removed[f"{doctype} FAILED {name}"] = str(exc)[:160]

	from kentender_core.services.command_write_guard import purge_doc

	for doctype in ("Contract Operation Intent", "Contract Command Journal", "Contract Case"):
		for name in frappe.get_all(doctype, filters={"fixture_namespace": "CM_SPIKE"}, pluck="name"):
			purge_doc(doctype, name)
	for wf in frappe.get_all("Workflow", filters={"name": ["like", "CM Spike%"]}, pluck="name"):
		frappe.delete_doc("Workflow", wf, force=True, ignore_permissions=True)
	if frappe.get_meta("Payment Entry").has_field("cm_operation_identity"):
		drop("Payment Entry", frappe.get_all("Payment Entry", filters={"cm_operation_identity": ["like", "SPIKE%"]}, pluck="name", order_by="creation desc"))
	drop("Payment Entry", frappe.get_all("Payment Entry", filters={"party": SUPPLIER}, pluck="name", order_by="creation desc"))
	drop("Journal Entry", frappe.get_all("Journal Entry", filters={"user_remark": ["like", "CM SPIKE%"]}, pluck="name", order_by="creation desc"))
	drop("Purchase Invoice", frappe.get_all("Purchase Invoice", filters={"supplier": SUPPLIER}, pluck="name", order_by="creation desc"))
	# submitted assets block their receipt; returns block the receipt they return; inspections block the receipt they inspect
	for asset in frappe.get_all("Asset", filters={"item_code": ["in", items], "docstatus": 1}, pluck="name"):
		try:
			frappe.get_doc("Asset", asset).cancel()
			removed["Asset cancelled"] = removed.get("Asset cancelled", 0) + 1
		except Exception as exc:  # noqa: BLE001
			removed[f"Asset FAILED {asset}"] = str(exc)[:160]
	receipts = frappe.get_all("Purchase Receipt", filters={"supplier": SUPPLIER}, fields=["name", "is_return"], order_by="creation desc")
	for pr in sorted(receipts, key=lambda r: not r.is_return):  # returns first, each group newest first
		frappe.db.set_value("Purchase Receipt Item", {"parent": pr.name}, "quality_inspection", None)
		for qi in frappe.get_all("Quality Inspection", filters={"reference_name": pr.name, "docstatus": 1}, pluck="name"):
			frappe.get_doc("Quality Inspection", qi).cancel()
		drop("Purchase Receipt", [pr.name])
	drop("Purchase Order", frappe.get_all("Purchase Order", filters={"supplier": SUPPLIER}, pluck="name", order_by="creation desc"))
	drop("Quality Inspection", frappe.get_all("Quality Inspection", filters={"item_code": ["in", items]}, pluck="name"))
	if frappe.db.exists("Quality Inspection Parameter", "CM-SPIKE criterion 1 screen size at least 14 inch"):
		frappe.delete_doc("Quality Inspection Parameter", "CM-SPIKE criterion 1 screen size at least 14 inch", force=True, ignore_permissions=True)
	for asset in frappe.get_all("Asset", filters={"item_code": ["in", items]}, pluck="name"):
		for mv in frappe.get_all("Asset Movement Item", filters={"asset": asset}, pluck="parent"):
			drop("Asset Movement", [mv])
	drop("Asset", frappe.get_all("Asset", filters={"item_code": ["in", items]}, pluck="name"))
	for sn in frappe.get_all("Serial No", filters={"item_code": ["in", items]}, pluck="name"):
		frappe.delete_doc("Serial No", sn, force=True, ignore_permissions=True)
		removed["Serial No"] = removed.get("Serial No", 0) + 1
	for dt, name in [("Item", ITEM_FA), ("Item", ITEM_STK), ("Asset Category", CATEGORY), ("Supplier", SUPPLIER), ("Location", LOCATION)]:
		if frappe.db.exists(dt, name):
			try:
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
				removed[dt] = removed.get(dt, 0) + 1
			except Exception as exc:  # noqa: BLE001
				removed[f"{dt} FAILED {name}"] = str(exc)[:160]
	if frappe.db.exists("Mode of Payment Account", {"parent": "Wire Transfer", "company": COMPANY}):
		mop = frappe.get_doc("Mode of Payment", "Wire Transfer")
		mop.accounts = [row for row in mop.accounts if row.company != COMPANY]
		mop.save(ignore_permissions=True)
		removed["Mode of Payment Account"] = 1
	for name in frappe.get_all("Bank Account", filters={"party": SUPPLIER}, pluck="name") + frappe.get_all("Bank Account", filters={"bank": "CM Spike Bank Ltd"}, pluck="name"):
		if frappe.db.exists("Bank Account", name):
			frappe.delete_doc("Bank Account", name, force=True, ignore_permissions=True)
	if frappe.db.exists("Bank", "CM Spike Bank Ltd"):
		frappe.delete_doc("Bank", "CM Spike Bank Ltd", force=True, ignore_permissions=True)
	if frappe.db.exists("Account", BANK_ACCOUNT):
		try:
			frappe.delete_doc("Account", BANK_ACCOUNT, force=True, ignore_permissions=True)
			removed["Account"] = 1
		except Exception as exc:  # noqa: BLE001 - cancelled ledger rows keep an account referenced
			removed[f"Account KEPT {BANK_ACCOUNT}"] = str(exc)[:120]
	for email in USERS.values():
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
			removed["User"] = removed.get("User", 0) + 1
	frappe.db.commit()
	print(json.dumps(removed, indent=1))
	return removed
