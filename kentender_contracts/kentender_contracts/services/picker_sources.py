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
UNIT = "contracts.unit"
FETCH = 300
#: the responsibilities a person can be picked for
ROLES = ("Contract inspection", "Technical certification", "Entity contract signing")
PREPARERS = ("Head of Procurement Function", "Contract preparation", "Accounting Officer")
#: A person named to review a requested change holds one of these (the Accounting Officer, who decides, is deliberately not among them).
REVIEWER = "Change reviewer"
REVIEWER_ROLES = ("Contract inspection", "Technical certification", "Contract preparation", "Head of Procurement Function")
#: A person who owns surviving work a close-out correction keeps (a duty that outlives the closure) holds one of these contract responsibilities.
OWNER = "Surviving work owner"
OWNER_ROLES = ("Head of Procurement Function", "Contract coordination", "Contract preparation", "Contract inspection", "Technical certification", "Finance preparation")
FINANCE = ("Finance preparation",)
#: kind -> (who may choose, how it is read)
KINDS = {
	"item": PREPARERS, "supplier": PREPARERS, "location": PREPARERS,
	"account.payable": FINANCE, "account.expense": FINANCE, "account.bank": FINANCE, "cost_centre": FINANCE, "tax_template": FINANCE,
	"purchase_order": PREPARERS, "purchase_receipt": PREPARERS + FINANCE, "purchase_invoice": PREPARERS + FINANCE, "payment_entry": PREPARERS,  # Finance names the native return and credit when it reconciles a returned unit
}


def sources() -> list[dict[str, Any]]:
	base = "kentender_contracts.services.picker_sources."
	return [
		{"key": PERSON, "noun": "person", "plural": "people", "match": "core", "provider": base + "people_holding"},
		{"key": UNIT, "noun": "unit", "plural": "units", "match": "provider", "provider": base + "units_preparing", "resolver": base + "units_by_id"},
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
	if role not in ROLES and role not in (REVIEWER, OWNER):
		raise frappe.DoesNotExistError("Not found")
	_gate(actor, PREPARERS)
	wanted = REVIEWER_ROLES if role == REVIEWER else OWNER_ROLES if role == OWNER else (role,)
	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": ["in", list(wanted)], "status": "Enabled"}, pluck="user", distinct=True)
	rows = []
	for user in sorted(set(users)):
		if (eligible_reviewer(user) if role == REVIEWER else eligible_owner(user) if role == OWNER else people.holds(user, role)):
			rows.append({"id": user, "label": people.full_name(user), "detail": user, "keywords": user})
	return rows


def eligible_reviewer(user: str) -> bool:
	"""May this person be named to review a requested change: an enabled person who holds one of the contract responsibilities (a unit-scoped one at any unit)."""
	return any(people.holds(user, r) or _holds_somewhere(user, r) for r in REVIEWER_ROLES)


def eligible_owner(user: str) -> bool:
	"""May this person own surviving work: an enabled person who holds one of the contract responsibilities (a unit-scoped one at any unit)."""
	return any(people.holds(user, r) or _holds_somewhere(user, r) for r in OWNER_ROLES)


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
	if kind == "purchase_order":
		return "Purchase Order", {"company": company, "docstatus": 1}, "supplier_name", "name"
	if kind == "purchase_receipt":
		return "Purchase Receipt", {"company": company, "docstatus": 1}, "supplier_name", "name"
	if kind == "purchase_invoice":
		return "Purchase Invoice", {"company": company, "docstatus": 1}, "supplier_name", "name"
	if kind == "payment_entry":
		return "Payment Entry", {"company": company, "docstatus": 1, "payment_type": "Pay"}, "party_name", "name"
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


# -- organisation units ------------------------------------------------------------------------------------------------------------------
def preparing_units(actor: str) -> list[str]:
	"""Where this person prepares contracts: every unit for the head of procurement, otherwise the units of their Contract preparation assignments."""
	if people.holds(actor, "Head of Procurement Function"):
		return frappe.get_all("Organisation Unit", pluck="name", order_by="name asc")
	return sorted({u for u in frappe.get_all("User Responsibility Assignment", filters={"user": actor, "business_role": "Contract preparation", "status": "Enabled"}, pluck="organisation_unit") if u and people.holds(actor, "Contract preparation", u)})


def _unit_row(name: str) -> dict[str, Any]:
	label = frappe.db.get_value("Organisation Unit", name, "unit_name") if frappe.get_meta("Organisation Unit").has_field("unit_name") else name
	return {"id": name, "label": cstr(label) or name, "detail": name, "keywords": f"{name} {cstr(label)}"}


def units_preparing(*, query: str, context: dict, actor: str, limit: int) -> tuple[list[dict[str, Any]], int]:
	"""The organisation units where the person may prepare contracts (the unit that will manage the contract)."""
	allowed = preparing_units(actor)
	if not allowed:
		raise frappe.DoesNotExistError("Not found")
	kept = [row for row in (_unit_row(u) for u in allowed) if record_picker.matches(row, query)]
	return kept[:limit], len(kept)


def units_by_id(*, ids: list[str], context: dict, actor: str) -> list[dict[str, Any]]:
	allowed = set(preparing_units(actor))
	return [_unit_row(i) for i in ids if i in allowed]
