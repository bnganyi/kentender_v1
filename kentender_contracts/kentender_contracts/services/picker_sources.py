# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract Management's sources for the shared record picker (AGENTS.md section 6.12; see `kentender_core.services.record_picker`).

Choosing one person or one record from a list that can grow is the picker, never a dropdown. Two sources cover every such choice on the contract screens:

* `contracts.person` -- the people who currently hold one registered responsibility (context `{"role": ...}`): the chair and members of an appointment, the entity signatory. The command that saves
  the choice makes the same check (`delivery.eligibility`), so what the picker lists and what the command accepts cannot differ.
* `contracts.native_record` -- one native record (context `{"kind": ...}`): the catalogue item a contract line is bought as, the supplier and the asset location, and the accounts, cost centre and tax
  template Finance chooses. It filters in the database; a kind not in `KINDS` is a masked not-found.

Whoever may not choose here (a person who is not preparing the contract, or not Finance) gets the masked not-found, so the picker confirms nothing."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_contracts.services import people
from kentender_core.services import business_role_registry as registry
from kentender_core.services import record_picker

PERSON = "contracts.person"
RECORD = "contracts.native_record"
FETCH = 300
#: the responsibilities a person can be picked for
ROLES = ("Contract inspection", "Technical certification", "Entity contract signing")
PREPARERS = ("Head of Procurement Function", "Contract preparation", "Accounting Officer")
FINANCE = ("Finance preparation",)
#: kind -> (who may choose, how it is read)
KINDS = {
	"item": PREPARERS, "supplier": PREPARERS, "location": PREPARERS,
	"account.payable": FINANCE, "account.expense": FINANCE, "account.bank": FINANCE, "cost_centre": FINANCE, "tax_template": FINANCE,
}


def sources() -> list[dict[str, Any]]:
	base = "kentender_contracts.services.picker_sources."
	return [
		{"key": PERSON, "noun": "person", "plural": "people", "match": "core", "provider": base + "people_holding"},
		{"key": RECORD, "noun": "record", "plural": "records", "rest_title": "Records", "match": "provider", "provider": base + "native_records", "resolver": base + "native_records_by_id"},
	]


def _gate(actor: str, roles: tuple[str, ...]) -> None:
	if not any(people.holds(actor, role) for role in roles) and not any(_holds_somewhere(actor, role) for role in roles):
		raise frappe.DoesNotExistError("Not found")


def _holds_somewhere(actor: str, role: str) -> bool:
	"""A unit-scoped responsibility held at any unit (the picker is asked before a contract is chosen)."""
	entry = registry.REGISTRY.get(role)
	if entry is None or not entry.requires_organisation_unit:
		return False
	return any(people.holds(actor, role, unit) for unit in frappe.get_all("User Responsibility Assignment", filters={"user": actor, "business_role": role, "status": "Enabled"}, pluck="organisation_unit") if unit)


def people_holding(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	"""Everyone who holds the responsibility in the context now."""
	role = cstr(context.get("role"))
	if role not in ROLES:
		raise frappe.DoesNotExistError("Not found")
	_gate(actor, PREPARERS)
	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, pluck="user", distinct=True)
	rows = []
	for user in sorted(set(users)):
		if people.holds(user, role):
			rows.append({"id": user, "label": people.full_name(user), "detail": user, "keywords": user})
	return rows


# -- native records ---------------------------------------------------------------------------------------------------------------------
def _company() -> str:
	return frappe.defaults.get_global_default("company") or frappe.db.get_value("Company", {}, "name")


def _query(kind: str) -> tuple[str, dict[str, Any], str, str]:
	"""doctype, filters, the field that names a row and the one that describes it."""
	company = _company()
	if kind == "item":
		return "Item", {"is_purchase_item": 1, "disabled": 0}, "item_name", "name"
	if kind == "supplier":
		return "Supplier", {"disabled": 0}, "supplier_name", "name"
	if kind == "location":
		return "Location", {}, "location_name", "name"
	if kind == "cost_centre":
		return "Cost Center", {"company": company, "is_group": 0, "disabled": 0}, "cost_center_name", "name"
	if kind == "tax_template":
		return "Purchase Taxes and Charges Template", {"company": company, "disabled": 0}, "title", "name"
	filters: dict[str, Any] = {"company": company, "is_group": 0, "disabled": 0}
	if kind == "account.payable":
		filters["account_type"] = "Payable"
	elif kind == "account.bank":
		filters["account_type"] = "Bank"
	else:
		filters["root_type"] = ["in", ["Expense", "Asset"]]
	return "Account", filters, "account_name", "name"


def _kind(context: dict, actor: str) -> str:
	kind = cstr(context.get("kind"))
	if kind not in KINDS:
		raise frappe.DoesNotExistError("Not found")
	_gate(actor, KINDS[kind])
	return kind


def _row(raw: Any, name_field: str) -> dict[str, Any]:
	return {"id": raw.name, "label": cstr(raw.get(name_field)) or raw.name, "detail": raw.name, "keywords": f"{raw.name} {cstr(raw.get(name_field))}"}


def native_records(*, query: str, context: dict, actor: str, limit: int) -> tuple[list[dict[str, Any]], int]:
	kind = _kind(context, actor)
	doctype, filters, name_field, _detail = _query(kind)
	fields = ["name"] if name_field == "name" else ["name", name_field]
	tokens = record_picker.words(query)
	if not tokens:
		rows = frappe.get_all(doctype, filters=filters, fields=fields, order_by="name asc", limit_page_length=limit)
		return [_row(r, name_field) for r in rows], frappe.db.count(doctype, filters)
	like = f"%{tokens[0]}%"
	or_filters = [["name", "like", like]] + ([[name_field, "like", like]] if name_field != "name" else [])
	fetched = frappe.get_all(doctype, filters=filters, or_filters=or_filters, fields=fields, order_by="name asc", limit_page_length=FETCH)
	kept = [row for row in (_row(r, name_field) for r in fetched) if record_picker.matches(row, query)]
	return kept[:limit], len(kept)


def native_records_by_id(*, ids: list[str], context: dict, actor: str) -> list[dict[str, Any]]:
	kind = _kind(context, actor)
	doctype, filters, name_field, _detail = _query(kind)
	fields = ["name"] if name_field == "name" else ["name", name_field]
	return [_row(r, name_field) for r in frappe.get_all(doctype, filters={**filters, "name": ["in", ids]}, fields=fields)]
