# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The organisation facts of BDS-CHG-001 v0.8 §4.1 and their checks, shared by
registration and the bounded Account editor. Every value is self-declared;
nothing here claims external verification (BDS01-IMP-011)."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe.utils import cstr, validate_email_address

FIELDS = ("legal_name", "country", "registration_number", "tax_identifier", "registered_address", "official_email", "official_phone")
KENYA = "Kenya"
_PHONE = re.compile(r"^\+?[0-9 ()\-]{7,25}$")
_KRA_PIN = re.compile(r"^[AP][0-9]{9}[A-Z]$")
TEXT = {
	"legal_name": "Enter the registered name (3 to 200 characters).",
	"country": "Choose the country of registration.",
	"registration_number": "Enter the registration number.",
	"tax_identifier": "Enter a KRA PIN such as P051234567X.",
	"registered_address": "Enter the registered address.",
	"official_email": "Enter the organisation's official email.",
	"official_phone": "Enter a phone number using digits, spaces and an optional leading +.",
	"duplicate": "This organisation already has a supplier account. Ask its Authorised Signatory to add you.",
}
#: What an Account needs before a bid can start (BDS-CHG-001 §10.5 DES-04-ATTENTION).
MISSING = {"official_phone": "Enter the official phone number", "tax_identifier": "Enter the KRA PIN"}


def normalise(values: dict[str, Any]) -> dict[str, str]:
	out = {field: cstr(values.get(field) or "").strip() for field in FIELDS}
	out["official_email"] = out["official_email"].lower()
	out["tax_identifier"] = out["tax_identifier"].upper()
	return out


def errors_for(values: dict[str, str]) -> dict[str, str]:
	errors: dict[str, str] = {}
	if not 3 <= len(values["legal_name"]) <= 200:
		errors["legal_name"] = TEXT["legal_name"]
	if not values["country"] or not frappe.db.exists("Country", values["country"]):
		errors["country"] = TEXT["country"]
	if not values["registration_number"] or len(values["registration_number"]) > 60:
		errors["registration_number"] = TEXT["registration_number"]
	if values["country"] == KENYA and not _KRA_PIN.match(values["tax_identifier"]):
		errors["tax_identifier"] = TEXT["tax_identifier"]
	if not values["registered_address"] or len(values["registered_address"]) > 500:
		errors["registered_address"] = TEXT["registered_address"]
	if not values["official_email"] or not validate_email_address(values["official_email"], throw=False):
		errors["official_email"] = TEXT["official_email"]
	if not (_PHONE.match(values["official_phone"]) and sum(ch.isdigit() for ch in values["official_phone"]) >= 7):
		errors["official_phone"] = TEXT["official_phone"]
	return errors


def missing_items(org) -> list[dict[str, str]]:
	"""Required facts an existing Account lacks (e.g. a migrated record)."""
	out = []
	if not cstr(org.official_phone).strip():
		out.append({"field": "official_phone", "text": MISSING["official_phone"]})
	if org.country == KENYA and not cstr(org.tax_identifier).strip():
		out.append({"field": "tax_identifier", "text": MISSING["tax_identifier"]})
	return out


def same_identity(country: str, registration_number: str, *, exclude: str = "") -> str:
	"""An existing organisation with this country and registration number."""
	filters: dict[str, Any] = {"country": country, "registration_number": registration_number}
	if exclude:
		filters["name"] = ("!=", exclude)
	return cstr(frappe.db.get_value("Supplier Organisation", filters, "name"))
