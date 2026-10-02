# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The business profile: the standing facts a tender's business questionnaire
asks for (structure, owners, capital, trade licence, maximum business value,
state-owned status, year of registration), held once on the Account and copied
into each bid as a snapshot (release 1.4 plan, WP-2).

`UpdateSupplierBusinessProfile`: any active member may keep it, with a version
check, an idempotency key and an audit event that names the changed *fields*
only, never the values (owners' names, ages and shares are personal data).
A save may be partial; `missing_items` says what is still needed. Details that
do not belong to the chosen structure are dropped on save, so the profile
never says two things at once."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_core.utils import row_tables
from kentender_suppliers.supplier_accounts.services import audit, authz_state, records
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services.errors import field_errors

PROFILE = "Supplier Business Profile"
SOLE, PARTNERSHIP, COMPANY = "Sole proprietor", "Partnership", "Registered company"
STRUCTURES = (SOLE, PARTNERSHIP, COMPANY)
COMPANY_TYPES = ("Private company", "Public company")
YES_NO = ("Yes", "No")
SOLE_TEXT = ("sole_proprietor_name", "sole_proprietor_nationality", "sole_proprietor_country_of_origin", "sole_proprietor_citizenship")
MONEY = ("nominal_capital", "issued_capital", "maximum_business_value")
TABLES = ("partners", "directors")
SCALARS = ("business_structure", *SOLE_TEXT, "sole_proprietor_age", "company_type", *MONEY, "trade_licence_number", "trade_licence_expiry", "state_owned", "year_of_registration")
FIELDS = (*SCALARS, *TABLES)
#: Which details belong to which structure; the rest are cleared on save.
BELONGS = {
	SOLE: (*SOLE_TEXT, "sole_proprietor_age"),
	PARTNERSHIP: ("partners",),
	COMPANY: ("company_type", "nominal_capital", "issued_capital", "directors"),
}
PERSON_COLUMNS = [
	{"key": "name", "label": "the name", "type": "text", "max_length": 160},
	{"key": "nationality", "label": "the nationality", "type": "text", "max_length": 80},
	{"key": "citizenship", "label": "the citizenship", "type": "text", "max_length": 80},
	{"key": "shares", "label": "the percentage of shares", "type": "decimal", "scale": 2, "minimum": "0", "maximum": "100"},
]
SHARES_TOTAL = [{"column": "shares", "equals": "100"}]
LABELS = {
	"business_structure": "Business structure", "sole_proprietor_name": "Sole proprietor: name in full", "sole_proprietor_age": "Sole proprietor: age",
	"sole_proprietor_nationality": "Sole proprietor: nationality", "sole_proprietor_country_of_origin": "Sole proprietor: country of origin",
	"sole_proprietor_citizenship": "Sole proprietor: citizenship", "partners": "Partners", "company_type": "Company type", "nominal_capital": "Nominal capital",
	"issued_capital": "Issued capital", "directors": "Directors", "trade_licence_number": "Trade licence number", "trade_licence_expiry": "Trade licence expiry",
	"maximum_business_value": "Maximum value of business handled", "state_owned": "State-owned status", "year_of_registration": "Year of registration",
}
MISSING_TEXT = {
	"business_structure": "Choose the business structure", "sole_proprietor_name": "Enter the sole proprietor's name", "sole_proprietor_age": "Enter the sole proprietor's age",
	"sole_proprietor_nationality": "Enter the sole proprietor's nationality", "sole_proprietor_country_of_origin": "Enter the sole proprietor's country of origin",
	"sole_proprietor_citizenship": "Enter the sole proprietor's citizenship", "partners": "Enter the partners and their shares", "company_type": "Choose private or public company",
	"nominal_capital": "Enter the nominal capital", "issued_capital": "Enter the issued capital", "directors": "Enter the directors and their shares",
	"trade_licence_number": "Enter the trade licence number", "trade_licence_expiry": "Enter the trade licence expiry date",
	"maximum_business_value": "Enter the maximum value of business handled", "state_owned": "Say whether the business is state-owned", "year_of_registration": "Enter the year of registration",
}
ALWAYS = ("trade_licence_number", "trade_licence_expiry", "maximum_business_value", "state_owned", "year_of_registration")
UNKNOWN_TEXT = "This value cannot be changed here."


def _money(value: Any) -> tuple[str, str]:
	"""(canonical text, message); a blank is allowed and means "not given"."""
	text = cstr(value).strip().replace(",", "")
	if not text:
		return "", ""
	try:
		number = Decimal(text)
	except InvalidOperation:
		return "", "Enter an amount in figures."
	if not number.is_finite() or number < 0:
		return "", "Enter an amount of 0 or more."
	if number != number.quantize(Decimal("0.01")):
		return "", "Use at most 2 decimal places."
	return str(number.quantize(Decimal("0.01"))), ""


def _whole(value: Any, low: int, high: int) -> tuple[Any, str]:
	text = cstr(value).strip()
	if not text:
		return "", ""
	try:
		number = Decimal(text)
	except InvalidOperation:
		return "", f"Enter a whole number from {low} to {high}."
	if number != number.to_integral_value() or not low <= number <= high:
		return "", f"Enter a whole number from {low} to {high}."
	return int(number), ""


def _short(value: Any, limit: int) -> tuple[str, str]:
	text = " ".join(cstr(value).split())
	return (text, "") if len(text) <= limit else ("", f"Use at most {limit} characters.")


def _choice(value: Any, options: tuple[str, ...]) -> tuple[str, str]:
	text = cstr(value).strip()
	return (text, "") if text in options + ("",) else ("", "Choose one of the listed options.")


def _date(value: Any) -> tuple[str, str]:
	text = cstr(value).strip()
	if not text:
		return "", ""
	try:
		return str(getdate(text)), ""
	except Exception:
		return "", "Enter a date such as 2027-12-31."


def _clean(values: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
	"""Each value that was sent, checked and in its canonical form; the
	errors are keyed by field, and by `table.position.column` for a cell."""
	out: dict[str, Any] = {}
	errors: dict[str, str] = {}

	def put(field: str, checked: tuple[Any, str]) -> None:
		if checked[1]:
			errors[field] = checked[1]
		else:
			out[field] = checked[0]

	for field, value in values.items():
		if field in ("business_structure",):
			put(field, _choice(value, STRUCTURES))
		elif field == "company_type":
			put(field, _choice(value, COMPANY_TYPES))
		elif field == "state_owned":
			put(field, _choice(value, YES_NO))
		elif field in SOLE_TEXT:
			put(field, _short(value, 160 if field == "sole_proprietor_name" else 80))
		elif field == "trade_licence_number":
			put(field, _short(value, 80))
		elif field == "sole_proprietor_age":
			put(field, _whole(value, 18, 120))
		elif field == "year_of_registration":
			put(field, _whole(value, 1800, 2100))
		elif field in MONEY:
			put(field, _money(value))
		elif field == "trade_licence_expiry":
			put(field, _date(value))
		elif field in TABLES:
			result = row_tables.normalise(PERSON_COLUMNS, value, maximum_rows=row_tables.MAX_ROWS, totals=SHARES_TOTAL if value else ())
			if result.problems:
				if result.problems.get("table"):
					errors[field] = " ".join(result.problems["table"])
				for position, cells in (result.problems.get("rows") or {}).items():
					for column, message in cells.items():
						errors[f"{field}.{position}.{column}"] = message
			else:
				out[field] = result.rows
		else:
			errors[field] = UNKNOWN_TEXT
	return out, errors


def _blank(field: str) -> Any:
	return [] if field in TABLES else ""


def _read_row(doc, field: str) -> Any:
	if field in TABLES:
		return [{"name": cstr(r.person_name), "nationality": cstr(r.nationality), "citizenship": cstr(r.citizenship), "shares": f"{float(r.shares_percent or 0):.2f}"} for r in doc.get(field)]
	value = doc.get(field)
	if field in MONEY:  # a stored 0 reads as "not given": no real capital or business value is nil
		return f"{Decimal(str(value)):.2f}" if value not in (None, "") and Decimal(str(value)) else ""
	if field in ("sole_proprietor_age", "year_of_registration"):
		return int(value) if value else ""
	if field == "trade_licence_expiry":
		return cstr(value) if value else ""
	return cstr(value)


def values_of(organisation: str) -> tuple[dict[str, Any], int]:
	"""The stored facts (blank when none) and the profile's record version."""
	if not frappe.db.exists(PROFILE, organisation):
		return {field: _blank(field) for field in FIELDS}, 0
	doc = frappe.get_doc(PROFILE, organisation)
	return {field: _read_row(doc, field) for field in FIELDS}, int(doc.record_version or 0)


def missing_for(values: dict[str, Any]) -> list[dict[str, str]]:
	"""What the profile still needs, in the order a person would fill it."""
	structure = values.get("business_structure")
	if not structure:
		return [{"field": "business_structure", "text": MISSING_TEXT["business_structure"]}]
	needed = [*BELONGS[structure], *ALWAYS]
	order = [f for f in FIELDS if f in needed]
	return [{"field": f, "text": MISSING_TEXT[f]} for f in order if not values[f]]


def missing_items(organisation: str) -> list[dict[str, str]]:
	return missing_for(values_of(organisation)[0])


def get_business_profile(*, organisation: str, user: str | None = None) -> dict[str, Any]:
	principal = authz.require_signed_in(user)
	authz.require_member(organisation, principal)
	values, version = values_of(organisation)
	return {"organisation": organisation, "record_version": version, "values": values, "missing": missing_for(values), "labels": LABELS}


def _apply(doc, cleaned: dict[str, Any]) -> list[str]:
	"""Set the checked values; return the fields that changed."""
	changed: list[str] = []
	for field, value in cleaned.items():
		if field in TABLES:
			before = _read_row(doc, field)
			if before != value:
				changed.append(field)
			doc.set(field, [])
			for row in value:
				doc.append(field, {"person_name": row["name"], "nationality": row["nationality"], "citizenship": row["citizenship"], "shares_percent": float(row["shares"])})
		else:
			before = _read_row(doc, field)
			if before != value:
				changed.append(field)
			doc.set(field, None if value == "" and field in ("trade_licence_expiry",) else value)
	return changed


def update_business_profile(*, organisation: str, values: dict[str, Any], expected_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	principal = authz.require_signed_in(user)
	authz.require_member(organisation, principal)
	authz_state.require_not_suspended(organisation)
	sent = dict(values or {})

	def _do() -> dict[str, Any]:
		exists = frappe.db.exists(PROFILE, organisation)
		doc = frappe.get_doc(PROFILE, organisation) if exists else frappe.new_doc(PROFILE)
		records.check_version(doc if exists else frappe._dict(record_version=0), expected_version)
		cleaned, errors = _clean(sent)
		if errors:
			return field_errors(errors)
		structure = cleaned.get("business_structure") or (_read_row(doc, "business_structure") if exists else "")
		for other, fields in BELONGS.items():
			if structure in STRUCTURES and other != structure:
				cleaned.update({field: _blank(field) for field in fields})
		if not exists:
			doc.organisation = organisation
		changed = _apply(doc, cleaned)
		from kentender_suppliers.supplier_accounts.services import clock

		doc.updated_by, doc.updated_at = principal, clock.now()
		doc.record_version = int(doc.record_version or 0)
		if exists:
			records.bump(doc)
		else:
			doc.record_version = 1
			records.insert(doc)
		audit.record(doctype=PROFILE, name=organisation, action="update_business_profile", actor=principal, metadata={"changed_fields": sorted(changed), "record_version": int(doc.record_version)})
		return {"ok": True, "organisation": organisation, "record_version": int(doc.record_version), "missing": missing_for(values_of(organisation)[0])}

	payload = {"organisation": organisation, "values": sent, "expected_version": cstr(expected_version)}
	return records.idempotent(idempotency_key, "UpdateSupplierBusinessProfile", payload, _do, actor=principal, organisation=organisation)


def facts(organisation: str) -> dict[str, Any] | None:
	"""The profile as the provider answers it (and a bid copies it)."""
	if not organisation or not frappe.db.exists("Supplier Organisation", organisation):
		return None
	values, version = values_of(organisation)
	return {**values, "record_version": version, "complete": not missing_for(values)}
